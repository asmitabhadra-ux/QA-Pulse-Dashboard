# QA Pulse Dashboard

> A GenAI-powered test intelligence dashboard that transforms raw Playwright/Pytest results
> into executive-ready quality reports — with trend analysis, flakiness detection, and
> AI-generated release narratives powered by Claude.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Playwright](https://img.shields.io/badge/Playwright-E2E-green)
![Claude API](https://img.shields.io/badge/Claude-AI%20Summaries-purple)
![CI](https://img.shields.io/badge/GitHub%20Actions-Automated-orange)

---

## Why I Built This

In 20+ years leading QA teams, the hardest part was never finding bugs — it was
**communicating quality** to stakeholders who don't read test logs. Executives want a
single, clear signal: *can we ship?*

QA Pulse bridges that gap. It takes raw JSON test output, computes the metrics that
actually matter (pass rate, flakiness, trends), and uses the Claude API to generate
a plain-English release assessment — the same kind of narrative I'd write manually
before a Go/No-Go review.

---

## Architecture

```
Pytest / Playwright runs
        │
        ▼
  parser.py  ──────────────────────►  metrics.py
  (normalise JSON)                    (pass rate, flakiness, trend)
                                             │
                                             ▼
                                       ai_engine.py
                                    (Claude API → narrative)
                                             │
                                             ▼
                              report_builder.py
                         ┌──────────┴──────────┐
                   dashboard.html        quality_report.md
               (Chart.js, tables)      (shareable exec report)
```

---

## Project Structure

```
qa-pulse-dashboard/
├── data/                    # Historical test runs (JSON) for trend analysis
├── src/
│   ├── parser.py            # Reads & normalises pytest-json-report output
│   ├── metrics.py           # Pass rate, flakiness score, trend, delta
│   ├── ai_engine.py         # Calls Claude API → plain-English narrative
│   └── report_builder.py   # Assembles HTML dashboard + Markdown report
├── tests/
│   ├── conftest.py          # Fixtures: base URL, credentials
│   ├── test_login.py        # 6 login flow tests
│   ├── test_inventory.py    # 7 product listing / sort tests
│   └── test_cart.py         # 5 shopping cart tests
├── output/                  # Generated reports (gitignored except samples)
├── .github/workflows/
│   └── qa_pulse.yml         # CI: runs tests → generates report → uploads artifact
├── pytest.ini
└── requirements.txt
```

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/YOUR_USERNAME/qa-pulse-dashboard.git
cd qa-pulse-dashboard
pip install -r requirements.txt
playwright install chromium

# 2. Run the test suite (generates output/test_results.json)
pytest --browser chromium

# 3. Generate the dashboard
python src/report_builder.py

# 4. Open the dashboard
open output/dashboard.html
```

### Enable AI Summaries

```bash
export ANTHROPIC_API_KEY=your_key_here
python src/report_builder.py
```

Get a free API key at [console.anthropic.com](https://console.anthropic.com).
Without a key, the AI section shows a clearly-labelled stub so the rest of the
dashboard still works.

---

## GitHub Actions CI

Every push to `main` automatically:
1. Runs all Playwright tests against SauceDemo
2. Generates the QA Pulse report (with AI summary if `ANTHROPIC_API_KEY` secret is set)
3. Uploads `dashboard.html`, `quality_report.md`, and `test_results.json` as a build artifact
4. Commits the run JSON to `data/` to grow the historical trend

**Setup:** Add `ANTHROPIC_API_KEY` under *Settings → Secrets → Actions* in your repo.

---

## Test Coverage

| Module | Tests | What's covered |
|--------|-------|----------------|
| `test_login.py` | 6 | Valid login, locked user, empty fields, invalid creds, logout |
| `test_inventory.py` | 7 | Page load, product count, all 3 sort modes, detail nav, back button |
| `test_cart.py` | 5 | Add item, add multiple, remove, cart page validation, empty cart |

All tests run against the publicly available [SauceDemo](https://www.saucedemo.com)
demo application — no account or setup required.

---

## Key Design Decisions

**Why pytest-json-report?** It produces structured output that's trivially parseable,
making the pipeline tool-agnostic. Swap in any test runner that emits JSON.

**Why a flakiness score?** A binary "flaky / not flaky" label isn't actionable.
The score (`flips / appearances`) lets teams prioritise which tests to stabilise first.

**Why stub the AI?** The dashboard is fully functional without an API key. The AI layer
is an enhancement, not a dependency — the same philosophy as shift-left testing.

---

## Author

**Asmita Bhadra** — Principal QA Engineer | 20+ years in CCaaS & video platforms  
[LinkedIn](https://www.linkedin.com/in/asmita-bhadra/) · [asmitabhadra@gmail.com](mailto:asmitabhadra@gmail.com)
