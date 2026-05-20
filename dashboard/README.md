# Fundamental Dashboard v2

Local Streamlit dashboard for viewing and auditing pre-generated Fundamental AI Analyst reports.

## Scope

Dashboard v2 is an AI Report Viewer / Auditor. It reads existing files:

- `output/ai_report_<code>.json`
- `output/ai_report_<code>.md`
- `output/evidence_pack_<code>.json`
- `output/fundamental_<code>.json`
- `output/raw_<code>.json`

It does not call an LLM, does not call OpenAI APIs, does not connect to accounts, does not add technical indicators, does not implement `technical_skill` or `trader_skill`, and does not change the deterministic fundamental pipeline.

## Generate Inputs First

Run the prompt-only AI Analyst layer:

```bash
python -m src.fundamental_skill.ai_analyst.runner --code 002050 --mode prompt_only
```

Then use Codex / GPT-5.5 with `output/ai_prompt_002050.md` and `output/evidence_pack_002050.json` to generate:

```text
output/ai_report_002050.json
output/ai_report_002050.md
```

If an AI report is missing, the dashboard shows prompt-only instructions and a prompt preview when available.

## Run

```bash
streamlit run dashboard/fundamental_dashboard.py
```

## Main Views

- AI Executive Summary
- Fundamental View
- Confidence Breakdown
- Evidence Classification
- AI Analysis Report
- Must Track Indicators
- Safety / Schema Status
- Evidence Pack Viewer
- Evidence / Raw Data audit panels

Raw JSON and legacy tables are audit material and are collapsed by default.

## Current Limits

- No direct OpenAI API integration.
- No AI report generation inside the dashboard.
- AI reports must be generated before viewing.
- No trading advice, account actions, target prices, position sizing, or technical analysis.
- Raw JSON is shown only for audit/debug purposes.
