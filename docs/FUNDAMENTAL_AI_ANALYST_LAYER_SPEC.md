# Fundamental AI Analyst Layer v1

## 1. Why Dashboard v1 Is Not the Final Shape

Dashboard v1 is a local Streamlit viewer for existing `fundamental_skill` outputs. It can run `real_stock_runner`, show `fundamental_<code>.json`, show selected raw data blocks, summarize data quality, and expose source traces.

That is useful for acceptance and debugging, but it is still a data display surface. It does not build a compact evidence pack, does not generate a model-ready analyst prompt, and does not produce an AI-written fundamental research report.

## 2. Positioning

The Fundamental AI Analyst Layer is a separate layer above the deterministic `fundamental_skill` pipeline.

It consumes:

- `output/fundamental_<code>.json`
- `output/raw_<code>.json`

It produces:

- `output/evidence_pack_<code>.json`
- `output/ai_prompt_<code>.md`

It does not mutate the deterministic pipeline, call AkShare directly, connect to accounts, introduce technical indicators, implement `technical_skill`, or implement `trader_skill`.

## 3. Evidence Pack

The evidence pack compresses pipeline output and raw public-data blocks into a model-friendly JSON object. It intentionally avoids passing full raw JSON to the model.

The v1 evidence pack includes:

- stock identity and deterministic fundamental status;
- confidence basis;
- basic information;
- financial metrics;
- valuation metrics;
- business composition;
- commodity price context when present;
- risk flags;
- enhanced must-track indicators;
- invalidation conditions;
- missing-field explanations;
- data limitations;
- source trace summary;
- forbidden-term safety summary.

`source_trace_summary` records block-level counts, functions, fields, and latest periods. It does not include full source trace rows.

### 3.1 Quality Patch v1: Unit Normalization

Ratio-like fields are represented with both raw and display values:

```json
{
  "name": "gross_margin",
  "raw_value": 27.796688,
  "display_value": "27.80%",
  "unit": "%",
  "unit_confidence": "medium"
}
```

For values between 0 and 1, the display value is converted to percentage form. For values that already look like percentage-point values, the display value preserves that interpretation. YoY fields such as `revenue_yoy` and `net_profit_yoy` also include `unit_assumption`; because public data sources can be inconsistent, their `unit_confidence` is conservative unless the source unit is explicitly confirmed.

### 3.2 Quality Patch v1: Confidence Breakdown

`confidence_basis` includes a five-part breakdown:

- `data_coverage`
- `financial_quality`
- `valuation_interpretability`
- `growth_validation`
- `risk_identifiability`

The AI report must explain these dimensions instead of only repeating the overall confidence level.

### 3.3 Quality Patch v1: Evidence Classification

The evidence pack classifies evidence into:

- `supporting_evidence`
- `limiting_evidence`
- `unknown_or_missing_evidence`

Each item records the evidence name, value, why it matters, affected dimension, source, and confidence effect. This is meant to make the AI report more audit-friendly and less template-like.

### 3.4 Neutral Naming Compatibility v1

The evidence pack and prompt use neutral handoff names:

- `analyst_summary` is the recommended summary field.
- `downstream_review_hint` is the recommended invalidation-condition review hint.
- `trader_summary` is deprecated but retained in the source schema for backward compatibility.
- `action_hint_for_trader` is deprecated but retained in the source schema for backward compatibility.

When reading historical JSON that only has legacy fields, the builder falls back from `trader_summary` to `analyst_summary` and from `action_hint_for_trader` to `downstream_review_hint`. Prompt construction must not primarily expose the deprecated field names. This remains a fundamental-analysis layer only: no `trader_skill`, no `technical_skill`, no trading-account connection, and no trading advice.

## 4. Enhanced Must-Track Indicators

The v1 layer adds `enhanced_must_track_indicators` because the dashboard-era indicators are not enough for AI analysis.

Each enhanced indicator contains:

- `indicator_name`
- `why_it_matters`
- `current_value`
- `current_status`
- `source`
- `source_date`
- `related_risk`
- `affects_dimension`
- `follow_up_question`
- `priority`

Strategy-specific indicator templates are used for resource stocks, advanced manufacturing growth, semiconductor cycle, right-trend growth stocks, and satellite communication infrastructure. Missing data is explicitly marked with `current_status = "missing"` rather than filled with invented values.

For `satellite_communication_infrastructure`, v1 must-track indicators include satellite resources, transponder / bandwidth capacity, utilization / lease rate, unit bandwidth price, satellite remaining life, contract duration, customer concentration, contract liabilities, accounts receivable, capex, depreciation / amortization, operating cash flow, gross margin, commercial-aerospace new-business revenue, major satellite launch / failure / insurance events, EV/EBITDA, EBITDA margin, free cash flow, and debt / EBITDA. EV/EBITDA, EBITDA margin, and debt / EBITDA are data limitations only in v1 and must not enter scoring.

AI-facing prompts require these indicators to be rendered as a Markdown table with current status, value, priority, reason, and follow-up question.

## 5. Prompt-Only Workflow

Run:

```bash
python -m src.fundamental_skill.ai_analyst.runner --code 002050 --mode prompt_only
```

The runner reads existing output files, builds the evidence pack, generates the prompt, and writes both files under `output/`.

If `fundamental_<code>.json` or `raw_<code>.json` is missing, the runner asks the user to run `src.fundamental_skill.real_stock_runner` first.

## 6. Why v1 Does Not Call an API

v1 is prompt-only by design. This keeps the deterministic pipeline stable and avoids making tests depend on network access, API keys, model availability, or provider-specific behavior.

The `--mode api` flag is reserved but intentionally not implemented in v1. It prints:

```text
API mode not implemented in v1; use prompt_only
```

## 7. Safety Boundary

The AI analyst layer is limited to fundamental analysis. It must not output trading advice, account actions, target prices, position sizing, technical indicators, or `technical_skill` / `trader_skill` behavior.

The prompt includes a prohibition list for policy context. Final AI reports should not contain those restricted terms as substantive recommendations. The safety module records detections and separates allowed policy context from blocked report-body usage.

The layer does not delete original evidence. It records safety findings separately.

## 8. Dashboard v2 Next Step

Dashboard v2 should consume the files generated by this layer:

- show the AI prompt or AI report as the primary analyst view;
- keep evidence pack, source summary, and raw JSON as audit panels;
- preserve the existing dashboard v1 result inspection tools;
- run safety checks before displaying any AI report as an accepted analysis.

Dashboard v2 should remain separate from the deterministic pipeline and should not introduce trading-account or technical-analysis behavior.

## 9. Dashboard v2 Viewer / Auditor

Dashboard v2 is implemented as a local Streamlit AI report viewer. It reads existing `ai_report`, `evidence_pack`, `fundamental`, and `raw` files from `output/`.

It does not call model APIs and does not generate new AI reports. If `ai_report_<code>.json` is missing, it shows the prompt-only command and a prompt preview when `ai_prompt_<code>.md` exists.

The default view is the AI report:

- executive summary;
- fundamental view;
- confidence breakdown;
- supporting / limiting / unknown evidence;
- analysis sections;
- must-track table;
- schema and safety status.

Evidence pack summaries, source traces, deterministic fundamental JSON, and raw JSON are kept in collapsed audit sections.

## 10. Evidence Pack v2.2a Field Note

After `RealDataConnector v2.2a`, the evidence pack can surface these additional `financial_metrics` fields when present in raw JSON:

- `inventory`
- `accounts_receivable`
- `contract_liabilities`

The fields are sourced from `stock_financial_report_sina(indicator="资产负债表")`, with period binding from `报告日`. `inventory` and `accounts_receivable` can clear working-capital missing indicators when their values are present. `contract_liabilities` can only be shown as an order-visibility proxy and must keep the scope note that it is not real orders or backlog.

The AI analyst layer must continue marking capex ratio, customer concentration, new-business orders, domestic-substitution revenue, production/unit cost, cobalt price, and molybdenum price as missing or outside scope until separate source-expansion work is completed.

## 11. Evidence Pack v2.3a Field Note

After `RealDataConnector v2.3a`, the evidence pack can surface three additional `financial_metrics` fields when present in raw JSON:

- `r_and_d_expense`
- `r_and_d_expense_ratio`
- `capex`

The fields are sourced from `stock_financial_report_sina`. Amount fields keep `unit="raw_statement_unit"` and `unit_confidence=low`; `r_and_d_expense_ratio` keeps `unit="%"` and `unit_confidence=high`. All three are cumulative as reported.

The AI analyst layer must not over-interpret these fields:

- R&D expense ratio can improve the current status of R&D-intensity indicators, but it represents R&D intensity only and does not confirm a technology barrier.
- Capex can improve capital-expenditure observation items, but it represents long-term-asset purchase/construction cash outflow only and does not confirm capacity release.

The layer still does not surface or infer `capex_ratio`, `depreciation_amortization`, customer concentration, new-business orders, domestic-substitution revenue, production/unit cost, technical indicators, `technical_skill`, or `trader_skill`.
