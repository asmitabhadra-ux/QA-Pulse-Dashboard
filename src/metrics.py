"""
metrics.py — Computes quality metrics from one or more RunSummary objects.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from src.parser import RunSummary, TestResult


@dataclass
class FlakyStat:
    test_name: str
    class_name: str
    pass_count: int
    fail_count: int
    last_error: str

    @property
    def flakiness_score(self) -> float:
        total = self.pass_count + self.fail_count
        return round(self.fail_count / total, 2) if total else 0.0

    @property
    def is_flaky(self) -> bool:
        return self.pass_count > 0 and self.fail_count > 0

    @property
    def short_name(self) -> str:
        return self.test_name.replace("test_", "").replace("_", " ").title()


@dataclass
class QualityMetrics:
    run_labels: list[str]
    pass_rates: list[float]
    total_counts: list[int]
    failed_counts: list[int]
    latest_pass_rate: float
    latest_passed: int
    latest_failed: int
    latest_total: int
    latest_duration: float
    latest_date: str
    pass_rate_delta: float
    class_breakdown: dict[str, dict]
    flaky_tests: list[FlakyStat]
    stable_failures: list[FlakyStat]
    top_failures: list[TestResult]

    @property
    def overall_trend(self) -> str:
        if self.pass_rate_delta > 2:
            return "improving"
        if self.pass_rate_delta < -2:
            return "degrading"
        return "stable"

    @property
    def go_no_go(self) -> str:
        if self.latest_pass_rate >= 95:
            return "GO"
        if self.latest_pass_rate >= 80:
            return "CONDITIONAL GO"
        return "NO GO"


def compute_metrics(runs: list[RunSummary]) -> QualityMetrics:
    if not runs:
        raise ValueError("Cannot compute metrics from an empty run list.")

    latest = runs[-1]
    previous = runs[-2] if len(runs) > 1 else None

    run_labels = [r.label for r in runs]
    pass_rates = [r.pass_rate for r in runs]
    total_counts = [r.total for r in runs]
    failed_counts = [r.failed for r in runs]
    pass_rate_delta = round(latest.pass_rate - previous.pass_rate, 1) if previous else 0.0

    class_breakdown: dict[str, dict] = defaultdict(lambda: {"passed": 0, "failed": 0, "total": 0})
    for test in latest.tests:
        cb = class_breakdown[test.class_name]
        cb["total"] += 1
        if test.outcome == "passed":
            cb["passed"] += 1
        else:
            cb["failed"] += 1
    for cls, data in class_breakdown.items():
        data["pass_rate"] = round(data["passed"] / data["total"] * 100, 1) if data["total"] else 0.0

    history: dict[str, dict] = defaultdict(lambda: {
        "pass_count": 0, "fail_count": 0, "last_error": "", "class_name": "", "test_name": ""
    })
    for run in runs:
        seen_in_run: set[str] = set()
        for test in run.tests:
            nid = test.node_id
            if nid in seen_in_run:
                continue
            seen_in_run.add(nid)
            entry = history[nid]
            entry["class_name"] = test.class_name
            entry["test_name"] = test.test_name
            if test.outcome == "passed":
                entry["pass_count"] += 1
            else:
                entry["fail_count"] += 1
                if test.error_message:
                    entry["last_error"] = test.error_message

    flaky_tests: list[FlakyStat] = []
    stable_failures: list[FlakyStat] = []
    for nid, h in history.items():
        stat = FlakyStat(
            test_name=h["test_name"],
            class_name=h["class_name"],
            pass_count=h["pass_count"],
            fail_count=h["fail_count"],
            last_error=h["last_error"],
        )
        if stat.is_flaky:
            flaky_tests.append(stat)
        elif stat.fail_count > 0 and stat.pass_count == 0:
            stable_failures.append(stat)

    flaky_tests.sort(key=lambda s: s.flakiness_score, reverse=True)
    stable_failures.sort(key=lambda s: s.fail_count, reverse=True)
    top_failures = [t for t in latest.tests if t.outcome != "passed"]

    return QualityMetrics(
        run_labels=run_labels,
        pass_rates=pass_rates,
        total_counts=total_counts,
        failed_counts=failed_counts,
        latest_pass_rate=latest.pass_rate,
        latest_passed=latest.passed,
        latest_failed=latest.failed,
        latest_total=latest.total,
        latest_duration=latest.duration,
        latest_date=latest.run_date.strftime("%B %d, %Y"),
        pass_rate_delta=pass_rate_delta,
        class_breakdown=dict(class_breakdown),
        flaky_tests=flaky_tests,
        stable_failures=stable_failures,
        top_failures=top_failures,
    )
