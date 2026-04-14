"""
ai_engine.py — Generates an executive QA narrative using the Claude API.

Falls back to a placeholder when ANTHROPIC_API_KEY is not set.
"""
from __future__ import annotations
import os
from src.metrics import QualityMetrics


def _build_prompt(m: QualityMetrics) -> str:
    flaky_list = "\n".join(
        f"  - {f.short_name} ({f.class_name}): flakiness score {f.flakiness_score}, "
        f"passed {f.pass_count}x / failed {f.fail_count}x"
        for f in m.flaky_tests
    ) or "  None detected"

    failure_list = "\n".join(
        f"  - {t.short_name} ({t.class_name}): {t.error_message[:120]}"
        for t in m.top_failures
    ) or "  None"

    class_table = "\n".join(
        f"  - {cls}: {data['pass_rate']}% ({data['passed']}/{data['total']} tests)"
        for cls, data in m.class_breakdown.items()
    )

    trend_str = " → ".join(f"{r}%" for r in m.pass_rates)

    return f"""You are a senior QA lead writing a release quality report for engineering leadership.
Your tone is clear, direct, and confident. Avoid filler phrases. Be specific. Use numbers.

Latest run ({m.latest_date}):

OVERALL
- Pass rate: {m.latest_pass_rate}% ({m.latest_passed}/{m.latest_total} tests passed)
- Failed: {m.latest_failed} tests
- Duration: {m.latest_duration}s
- Pass rate trend: {trend_str}
- Delta vs previous run: {'+' if m.pass_rate_delta >= 0 else ''}{m.pass_rate_delta}%
- Overall trend: {m.overall_trend}

BREAKDOWN BY TEST CLASS
{class_table}

FLAKY TESTS
{flaky_list}

CURRENT FAILURES
{failure_list}

Write a QA release summary with four sections:
1. **Release Recommendation** — One sentence: GO, CONDITIONAL GO, or NO GO with key reason.
2. **Quality Snapshot** — 2-3 sentences referencing specific numbers and trends.
3. **Risk Areas** — Bullet points (max 3) identifying biggest quality risks.
4. **Recommended Actions** — Bullet points (max 3) for what the team should do before next release.

Keep under 250 words. Use markdown formatting.
"""


def generate_summary(metrics: QualityMetrics) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key:
        return _placeholder_summary(metrics)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": _build_prompt(metrics)}],
        )
        return message.content[0].text
    except Exception as e:
        return f"> ⚠️ AI summary unavailable: `{e}`\n\n" + _placeholder_summary(metrics)


def _placeholder_summary(m: QualityMetrics) -> str:
    delta_str = f"+{m.pass_rate_delta}%" if m.pass_rate_delta >= 0 else f"{m.pass_rate_delta}%"
    flaky_names = ", ".join(f.short_name for f in m.flaky_tests[:2]) or "none"

    return f"""> 🔑 **AI summary placeholder** — Add your `ANTHROPIC_API_KEY` to generate a real narrative.

---

## **Release Recommendation**
**{m.go_no_go}** — Pass rate is {m.latest_pass_rate}% with {m.latest_failed} active failure(s) requiring attention before release.

## Quality Snapshot
The latest run ({m.latest_date}) achieved {m.latest_pass_rate}% pass rate across {m.latest_total} tests, a {delta_str} change from the previous run. The overall trend is **{m.overall_trend}**, indicating {"positive momentum" if m.overall_trend == "improving" else "areas that need attention"}.

## Risk Areas
- **Flaky tests detected**: {flaky_names} — intermittent failures indicate environment sensitivity or timing issues
- **Cart flow instability**: Remove-item test fails consistently across runs — likely a DOM timing or state issue
- **Checkout navigation**: Cancel flow producing unexpected URL — regression risk for e-commerce critical path

## Recommended Actions
- Investigate and fix flaky tests before the next release cycle
- Add explicit waits or retry logic to the remove-item cart test
- Review checkout cancel routing logic — add a regression test covering all exit paths
"""
