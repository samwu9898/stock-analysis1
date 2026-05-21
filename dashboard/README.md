# Fundamental Dashboard v3

Local Streamlit fundamental AI analysis report reader for viewing and auditing pre-generated Fundamental AI Analyst reports.

## Scope

Dashboard v3 is a Chinese-first AI fundamental report reader / auditor. It reads existing files:

- `output/ai_report_<code>.json`
- `output/ai_report_<code>.md`
- `output/evidence_pack_<code>.json`
- `output/fundamental_<code>.json`
- `output/raw_<code>.json`

It does not call an LLM, does not call OpenAI APIs, does not connect to accounts, does not output trading advice, does not add technical indicators, does not implement `technical_skill` or `trader_skill`, and does not change the deterministic fundamental pipeline.

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

- Chinese top conclusion area
- One-line conclusion
- Chinese `strategy_type` / `sub_type` explanations
- Evidence map
- Risk warnings and evidence gaps
- Must-track indicator table
- Confidence breakdown
- Data quality and missing-data summary
- Report stale / mismatch detection
- Schema / safety / garbled guard status
- Collapsed audit panels for Evidence Pack, Source Trace, Raw JSON, Prompt, and legacy compatibility fields

Raw JSON, prompt preview, source trace, Evidence Pack, and deprecated compatibility fields are audit material and are collapsed by default. Deprecated `trader_summary` / `action_hint_for_trader` fields are not shown in the main view.

## Current Limits

- No direct OpenAI API integration.
- No AI report generation inside the dashboard.
- AI reports must be generated before viewing.
- No trading advice, account actions, target prices, position sizing, or technical analysis.
- No trading-account connection.
- Raw JSON is shown only for audit/debug purposes.
