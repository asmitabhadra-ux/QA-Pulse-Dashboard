"""
main.py — QA Pulse entry point.

Wires together the full pipeline:
  1. Load all test run JSON files from data/
  2. Compute quality metrics
  3. Generate AI narrative (Claude API or placeholder)
  4. Build HTML dashboard + Markdown report in output/

Usage:
    python main.py                    # uses data/ and writes to output/
    python main.py --data my_runs/    # custom data directory
    python main.py --open             # open dashboard in browser after generation
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

# Ensure src/ is importable when running from project root
sys.path.insert(0, str(Path(__file__).parent))

from src.parser import load_all_runs
from src.metrics import compute_metrics
from src.ai_engine import generate_summary
from src.report_builder import build_html_dashboard, build_markdown_report


def main(data_dir: str = "data", open_browser: bool = False) -> None:
    print("\n🔍 QA Pulse — starting pipeline\n")

    # Step 1: Load runs
    print(f"  [1/4] Loading test runs from '{data_dir}/'...")
    try:
        runs = load_all_runs(data_dir)
    except FileNotFoundError as e:
        print(f"\n  ✗ {e}")
        print("  Run your Playwright tests first:")
        print("    pytest tests/ --json-report --json-report-file=data/run_latest.json\n")
        sys.exit(1)
    print(f"         Loaded {len(runs)} run(s): {', '.join(r.label for r in runs)}")

    # Step 2: Compute metrics
    print("  [2/4] Computing quality metrics...")
    metrics = compute_metrics(runs)
    print(f"         Pass rate: {metrics.latest_pass_rate}%  |  "
          f"Flaky: {len(metrics.flaky_tests)}  |  Verdict: {metrics.go_no_go}")

    # Step 3: Generate AI summary
    print("  [3/4] Generating AI quality narrative...")
    ai_summary = generate_summary(metrics)
    ai_source = "Claude API" if "placeholder" not in ai_summary.lower() else "placeholder (no API key)"
    print(f"         Source: {ai_source}")

    # Step 4: Build outputs
    print("  [4/4] Building reports...")
    html_path = build_html_dashboard(metrics, ai_summary)
    md_path = build_markdown_report(metrics, ai_summary)

    print(f"\n  ✓ Done!\n")
    print(f"  📊 Dashboard : {html_path}")
    print(f"  📄 Report    : {md_path}")

    if open_browser:
        webbrowser.open(f"file://{html_path}")

    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QA Pulse Dashboard Generator")
    parser.add_argument("--data", default="data", help="Directory containing run_*.json files")
    parser.add_argument("--open", action="store_true", dest="open_browser", help="Open dashboard in browser")
    args = parser.parse_args()
    main(data_dir=args.data, open_browser=args.open_browser)
