"""
report_builder.py — Generates the HTML dashboard and Markdown summary report.

Outputs:
  output/dashboard.html  — Visual dashboard with Chart.js charts
  output/report.md       — Shareable plain-text executive report
"""
from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from src.metrics import QualityMetrics


def _trend_color(delta: float) -> str:
    if delta > 0:
        return "#22c55e"
    if delta < 0:
        return "#ef4444"
    return "#94a3b8"


def _go_badge(verdict: str) -> str:
    colors = {
        "GO": ("GO", "#22c55e", "#052e16"),
        "CONDITIONAL GO": ("CONDITIONAL", "#f59e0b", "#1c1005"),
        "NO GO": ("NO GO", "#ef4444", "#1c0505"),
    }
    label, bg, fg = colors.get(verdict, ("?", "#94a3b8", "#fff"))
    return f'<span class="badge" style="background:{bg};color:{fg}">{label}</span>'


def build_html_dashboard(metrics: QualityMetrics, ai_summary: str, output_path: str = "output/dashboard.html") -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    labels_json = json.dumps(metrics.run_labels)
    pass_rates_json = json.dumps(metrics.pass_rates)
    failed_json = json.dumps(metrics.failed_counts)
    class_labels = json.dumps(list(metrics.class_breakdown.keys()))
    class_rates = json.dumps([v["pass_rate"] for v in metrics.class_breakdown.values()])

    flaky_rows = ""
    if metrics.flaky_tests:
        for f in metrics.flaky_tests:
            score_pct = int(f.flakiness_score * 100)
            bar_color = "#f59e0b" if f.flakiness_score < 0.6 else "#ef4444"
            flaky_rows += f"""
            <tr>
              <td>{f.short_name}</td>
              <td><span class="tag">{f.class_name}</span></td>
              <td>{f.pass_count}</td>
              <td>{f.fail_count}</td>
              <td>
                <div class="score-bar-wrap">
                  <div class="score-bar" style="width:{score_pct}%;background:{bar_color}"></div>
                  <span>{f.flakiness_score}</span>
                </div>
              </td>
            </tr>"""
    else:
        flaky_rows = '<tr><td colspan="5" class="empty">No flaky tests detected ✓</td></tr>'

    failure_rows = ""
    if metrics.top_failures:
        for t in metrics.top_failures:
            failure_rows += f"""
            <tr>
              <td>{t.short_name}</td>
              <td><span class="tag">{t.class_name}</span></td>
              <td class="error-msg">{t.error_message[:100] or "—"}</td>
            </tr>"""
    else:
        failure_rows = '<tr><td colspan="3" class="empty">No failures in latest run ✓</td></tr>'

    delta_str = f"+{metrics.pass_rate_delta}%" if metrics.pass_rate_delta >= 0 else f"{metrics.pass_rate_delta}%"
    delta_color = _trend_color(metrics.pass_rate_delta)
    go_badge = _go_badge(metrics.go_no_go)
    ai_html = _md_to_html(ai_summary)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>QA Pulse Dashboard</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0f172a; --surface: #1e293b; --surface2: #273348;
      --border: #334155; --text: #e2e8f0; --muted: #94a3b8;
      --accent: #6366f1; --pass: #22c55e; --fail: #ef4444; --warn: #f59e0b;
      --radius: 12px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }}
    header {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 20px 32px; display: flex; justify-content: space-between; align-items: center; }}
    header h1 {{ font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em; }}
    header h1 span {{ color: var(--accent); }}
    .meta {{ font-size: 0.8rem; color: var(--muted); }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; display: grid; gap: 24px; }}
    .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
    .kpi {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px 24px; }}
    .kpi .label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }}
    .kpi .value {{ font-size: 2rem; font-weight: 700; line-height: 1; }}
    .kpi .sub {{ font-size: 0.8rem; color: var(--muted); margin-top: 6px; }}
    .kpi .delta {{ font-weight: 600; }}
    .chart-row {{ display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }}
    .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; }}
    .card h2 {{ font-size: 0.9rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 16px; }}
    .chart-wrap {{ position: relative; height: 220px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
    thead th {{ text-align: left; font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; padding: 0 12px 10px 0; border-bottom: 1px solid var(--border); }}
    tbody tr {{ border-bottom: 1px solid var(--border); }}
    tbody tr:last-child {{ border-bottom: none; }}
    td {{ padding: 10px 12px 10px 0; vertical-align: middle; }}
    .tag {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 4px; padding: 2px 8px; font-size: 0.75rem; color: var(--muted); white-space: nowrap; }}
    .error-msg {{ color: var(--muted); font-size: 0.8rem; font-family: monospace; max-width: 380px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .empty {{ color: var(--muted); padding: 16px 0; font-style: italic; }}
    .score-bar-wrap {{ display: flex; align-items: center; gap: 8px; }}
    .score-bar {{ height: 6px; border-radius: 3px; min-width: 4px; }}
    .score-bar-wrap span {{ font-size: 0.8rem; color: var(--muted); white-space: nowrap; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; letter-spacing: 0.04em; }}
    .ai-summary {{ background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: var(--radius); padding: 24px 28px; }}
    .ai-summary h2 {{ margin-bottom: 16px; }}
    .ai-content h2, .ai-content h3 {{ font-size: 1rem; font-weight: 600; color: var(--text); margin: 16px 0 8px; }}
    .ai-content p {{ color: var(--muted); line-height: 1.65; margin-bottom: 10px; font-size: 0.9rem; }}
    .ai-content ul {{ color: var(--muted); font-size: 0.9rem; padding-left: 20px; margin-bottom: 10px; }}
    .ai-content li {{ margin-bottom: 4px; line-height: 1.55; }}
    .ai-content strong {{ color: var(--text); }}
    .ai-content blockquote {{ border-left: 3px solid var(--warn); padding-left: 12px; color: var(--warn); font-size: 0.85rem; margin-bottom: 12px; }}
    .ai-content code {{ background: var(--surface2); padding: 1px 5px; border-radius: 4px; font-size: 0.8rem; }}
    .ai-content hr {{ border: none; border-top: 1px solid var(--border); margin: 16px 0; }}
    footer {{ text-align: center; padding: 32px; color: var(--muted); font-size: 0.8rem; }}
    @media (max-width: 768px) {{
      .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
      .chart-row {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<header>
  <h1>QA <span>Pulse</span> Dashboard</h1>
  <span class="meta">SauceDemo · {metrics.latest_date} · {metrics.latest_total} tests</span>
</header>
<main>
  <div class="kpi-row">
    <div class="kpi">
      <div class="label">Pass Rate</div>
      <div class="value" style="color:{'var(--pass)' if metrics.latest_pass_rate >= 90 else 'var(--warn)' if metrics.latest_pass_rate >= 75 else 'var(--fail)'}">{metrics.latest_pass_rate}%</div>
      <div class="sub"><span class="delta" style="color:{delta_color}">{delta_str}</span> vs previous run</div>
    </div>
    <div class="kpi">
      <div class="label">Tests Passed</div>
      <div class="value" style="color:var(--pass)">{metrics.latest_passed}</div>
      <div class="sub">of {metrics.latest_total} total</div>
    </div>
    <div class="kpi">
      <div class="label">Tests Failed</div>
      <div class="value" style="color:{'var(--fail)' if metrics.latest_failed > 0 else 'var(--pass)'}">{metrics.latest_failed}</div>
      <div class="sub">Trend: {metrics.overall_trend}</div>
    </div>
    <div class="kpi">
      <div class="label">Release Verdict</div>
      <div class="value" style="font-size:1.1rem;padding-top:4px">{go_badge}</div>
      <div class="sub">{metrics.latest_duration}s total run time</div>
    </div>
  </div>
  <div class="chart-row">
    <div class="card">
      <h2>Pass rate trend</h2>
      <div class="chart-wrap"><canvas id="trendChart"></canvas></div>
    </div>
    <div class="card">
      <h2>Pass rate by feature</h2>
      <div class="chart-wrap"><canvas id="classChart"></canvas></div>
    </div>
  </div>
  <div class="card">
    <h2>Flaky test tracker</h2>
    <table>
      <thead><tr><th>Test</th><th>Class</th><th>Passes</th><th>Failures</th><th>Flakiness score</th></tr></thead>
      <tbody>{flaky_rows}</tbody>
    </table>
  </div>
  <div class="card">
    <h2>Current failures — latest run</h2>
    <table>
      <thead><tr><th>Test</th><th>Class</th><th>Error</th></tr></thead>
      <tbody>{failure_rows}</tbody>
    </table>
  </div>
  <div class="ai-summary">
    <h2>🤖 AI Quality Analysis</h2>
    <div class="ai-content">{ai_html}</div>
  </div>
</main>
<footer>Generated by QA Pulse · {datetime.now().strftime("%Y-%m-%d %H:%M")}</footer>
<script>
const cd = {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}, y: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8', font: {{ size: 11 }} }} }} }} }};
new Chart(document.getElementById('trendChart'), {{ type: 'line', data: {{ labels: {labels_json}, datasets: [{{ label: 'Pass Rate %', data: {pass_rates_json}, borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.12)', fill: true, tension: 0.4, pointBackgroundColor: '#6366f1', pointRadius: 5 }}] }}, options: {{ ...cd, scales: {{ ...cd.scales, y: {{ ...cd.scales.y, min: 0, max: 100, ticks: {{ ...cd.scales.y.ticks, callback: v => v + '%' }} }} }} }} }});
new Chart(document.getElementById('classChart'), {{ type: 'bar', data: {{ labels: {class_labels}, datasets: [{{ data: {class_rates}, backgroundColor: ['#6366f1','#22c55e','#f59e0b','#ef4444'], borderRadius: 6 }}] }}, options: {{ ...cd, indexAxis: 'y', scales: {{ x: {{ ...cd.scales.x, min: 0, max: 100, ticks: {{ ...cd.scales.x.ticks, callback: v => v + '%' }} }}, y: {{ ...cd.scales.y }} }} }} }});
</script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"[report] Dashboard written → {output_path}")
    return str(Path(output_path).resolve())


def build_markdown_report(metrics: QualityMetrics, ai_summary: str, output_path: str = "output/report.md") -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    delta_str = f"+{metrics.pass_rate_delta}%" if metrics.pass_rate_delta >= 0 else f"{metrics.pass_rate_delta}%"
    class_rows = "\n".join(f"| {cls} | {data['pass_rate']}% | {data['passed']}/{data['total']} |" for cls, data in metrics.class_breakdown.items())
    flaky_rows = "\n".join(f"| {f.short_name} | {f.class_name} | {f.flakiness_score} | {f.pass_count}/{f.fail_count} |" for f in metrics.flaky_tests) or "| — | — | — | — |"
    failure_rows = "\n".join(f"| {t.short_name} | {t.class_name} | `{t.error_message[:80] or '—'}` |" for t in metrics.top_failures) or "| — | — | — |"
    trend_str = " → ".join(f"{r}%" for r in metrics.pass_rates)

    md = f"""# QA Pulse — Release Quality Report
**Date:** {metrics.latest_date}
**Suite:** SauceDemo E2E (Playwright + Pytest)
**Verdict:** {metrics.go_no_go}

---

## Summary

| Metric | Value |
|--------|-------|
| Pass Rate | **{metrics.latest_pass_rate}%** ({delta_str} vs prev) |
| Tests Passed | {metrics.latest_passed} / {metrics.latest_total} |
| Tests Failed | {metrics.latest_failed} |
| Run Duration | {metrics.latest_duration}s |
| Trend | {metrics.overall_trend.upper()} |
| Pass Rate Trend | {trend_str} |

---

## Feature Breakdown

| Feature Class | Pass Rate | Result |
|---------------|-----------|--------|
{class_rows}

---

## Flaky Tests

| Test | Class | Flakiness Score | Pass / Fail |
|------|-------|-----------------|-------------|
{flaky_rows}

---

## Current Failures

| Test | Class | Error |
|------|-------|-------|
{failure_rows}

---

## AI Quality Analysis

{ai_summary}

---
*Generated by QA Pulse · {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""
    Path(output_path).write_text(md, encoding="utf-8")
    print(f"[report] Markdown report written → {output_path}")
    return str(Path(output_path).resolve())


def _md_to_html(md: str) -> str:
    lines = md.split("\n")
    html_lines = []
    in_ul = False
    in_blockquote = False

    for line in lines:
        stripped = line.strip()
        if in_ul and not (stripped.startswith("- ") or stripped.startswith("* ")):
            html_lines.append("</ul>")
            in_ul = False
        if in_blockquote and not stripped.startswith(">"):
            html_lines.append("</blockquote>")
            in_blockquote = False
        if not stripped:
            html_lines.append("")
            continue
        if stripped.startswith("### "):
            html_lines.append(f"<h3>{_inline(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{_inline(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            html_lines.append(f"<h2>{_inline(stripped[2:])}</h2>")
        elif stripped.startswith(">"):
            if not in_blockquote:
                html_lines.append("<blockquote>")
                in_blockquote = True
            html_lines.append(f"<p>{_inline(stripped[1:].strip())}</p>")
        elif stripped in ("---", "***", "___"):
            html_lines.append("<hr>")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{_inline(stripped[2:])}</li>")
        else:
            html_lines.append(f"<p>{_inline(stripped)}</p>")

    if in_ul:
        html_lines.append("</ul>")
    if in_blockquote:
        html_lines.append("</blockquote>")
    return "\n".join(html_lines)


def _inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text
