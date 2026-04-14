"""
parser.py — Reads and normalizes pytest-json-report output files.

Supports single-run analysis and multi-run trend loading.
All downstream modules consume the data structures returned here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# ── Data models ──────────────────────────────────────────────────────────────

@dataclass
class TestResult:
    """Normalized result for a single test case."""
    node_id: str
    class_name: str
    test_name: str
    outcome: str          # "passed" | "failed" | "error"
    duration: float       # seconds
    error_message: str = ""

    @property
    def short_name(self) -> str:
        return self.test_name.replace("test_", "").replace("_", " ").title()


@dataclass
class RunSummary:
    """Aggregated data for one test run."""
    run_date: datetime
    total: int
    passed: int
    failed: int
    errors: int
    duration: float
    tests: list[TestResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return round((self.passed / self.total * 100), 1) if self.total else 0.0

    @property
    def label(self) -> str:
        return self.run_date.strftime("%b %d")


# ── Parsing logic ─────────────────────────────────────────────────────────────

def _parse_node_id(node_id: str) -> tuple[str, str]:
    """Extract class name and test name from a pytest node ID."""
    parts = node_id.split("::")
    class_name = parts[-2] if len(parts) >= 3 else "General"
    test_name = parts[-1] if parts else node_id
    return class_name, test_name


def _extract_error(test: dict) -> str:
    """Safely extract a short error message from a test entry."""
    call = test.get("call") or {}
    longrepr = call.get("longrepr", "")
    if not longrepr:
        return ""
    # Return just the first meaningful line
    first_line = longrepr.strip().split("\n")[0]
    return first_line[:200]


def parse_run(filepath: str | Path) -> RunSummary:
    """
    Parse a single pytest-json-report JSON file into a RunSummary.

    Args:
        filepath: Path to the JSON report file.

    Returns:
        A RunSummary with all tests normalized.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If the file is missing required fields.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {path}")

    with path.open() as f:
        raw = json.load(f)

    summary = raw.get("summary", {})
    created = raw.get("created", "")

    # Parse timestamp — support ISO format with or without microseconds
    try:
        if isinstance(created, (int, float)):
            run_date = datetime.fromtimestamp(created)
        else:
            run_date = datetime.fromisoformat(str(created))
    except (ValueError, TypeError, OSError):
        run_date = datetime.now()

    tests: list[TestResult] = []
    for t in raw.get("tests", []):
        class_name, test_name = _parse_node_id(t.get("nodeid", ""))
        tests.append(TestResult(
            node_id=t.get("nodeid", ""),
            class_name=class_name,
            test_name=test_name,
            outcome=t.get("outcome", "unknown"),
            duration=round(t.get("duration", 0.0), 2),
            error_message=_extract_error(t),
        ))

    return RunSummary(
        run_date=run_date,
        total=summary.get("total", len(tests)),
        passed=summary.get("passed", 0),
        failed=summary.get("failed", 0),
        errors=summary.get("error", 0),
        duration=round(raw.get("duration", 0.0), 1),
        tests=tests,
    )


def load_all_runs(data_dir: str | Path = "data") -> list[RunSummary]:
    """
    Load every JSON report in data_dir, sorted chronologically.

    Args:
        data_dir: Directory containing run_*.json files.

    Returns:
        List of RunSummary objects, oldest first.
    """
    data_path = Path(data_dir)
    json_files = sorted(data_path.glob("run_*.json"))

    if not json_files:
        raise FileNotFoundError(f"No run_*.json files found in '{data_dir}'")

    runs = []
    for f in json_files:
        try:
            runs.append(parse_run(f))
        except (KeyError, json.JSONDecodeError) as e:
            print(f"[parser] Skipping {f.name}: {e}")

    # Sort by run date ascending
    return sorted(runs, key=lambda r: r.run_date)


# ── CLI helper ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "data"
    runs = load_all_runs(target)
    for r in runs:
        print(f"{r.label} | Pass rate: {r.pass_rate}% | {r.passed}/{r.total} passed | {r.failed} failed")
