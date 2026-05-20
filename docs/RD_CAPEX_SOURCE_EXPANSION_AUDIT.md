# R&D / Capex Source Expansion Audit v1

Date: 2026-05-20

Scope:

- Probe-only source expansion based on the current v2.2a baseline.
- No RealDataConnector integration in this phase.
- No deterministic pipeline, dashboard, AI report, legacy analyzer, renderer, or data-fetcher change.
- No account connection, technical indicators, `technical_skill`, or `trader_skill` behavior.

New helpers:

- `scripts/probe_rd_capex_fields.py`
- `scripts/replay_rd_capex_probe.py`
- `tests/test_rd_capex_probe_replay.py`

## Target Fields

| target field | source rule |
| --- | --- |
| `r_and_d_expense` | Profit-statement expense amount row only. |
| `r_and_d_expense_ratio` | Derived from `r_and_d_expense / revenue * 100` only when both fields share the same `source_period`. |
| `capex` | Cash-flow statement cash paid for fixed, intangible, and other long-term assets. |
| `capex_ratio` | Derived from `capex / revenue * 100` only when both fields share the same `source_period`. |
| `depreciation_amortization` | Optional observation only; multiple component rows may exist, so do not promote without stability evidence. |

## Candidate AkShare Functions

The probe uses `hasattr` and `try/except` for every candidate. A missing or failing function is recorded and never stops the full probe.

Profit-statement candidates:

- `stock_profit_sheet_by_report_em`
- `stock_profit_sheet_by_yearly_em`
- `stock_profit_sheet_by_quarterly_em`
- `stock_financial_report_sina`
- `stock_financial_abstract`

Cash-flow statement candidates:

- `stock_cash_flow_sheet_by_report_em`
- `stock_cash_flow_sheet_by_yearly_em`
- `stock_cash_flow_sheet_by_quarterly_em`
- `stock_financial_report_sina`
- `stock_financial_abstract`

Financial-summary candidates:

- `stock_financial_abstract`
- `stock_financial_analysis_indicator`

Call variants include `symbol=<code>`, positional `<code>`, `stock=sz/sh<code>`, and for Sina statement reports `symbol="利润表"` or `symbol="现金流量表"`.

## Field Matching Rules

Accepted labels:

- `r_and_d_expense`: `研发费用`, `研究开发费用`, `研发支出`, `研发投入`, `研发费用合计`
- `capex`: `购建固定资产、无形资产和其他长期资产支付的现金`, `购建固定资产、无形资产和其他长期资产所支付的现金`, `购建固定资产、无形资产和其他长期资产支付现金`
- `depreciation_amortization`: `固定资产折旧、油气资产折耗、生产性生物资产折旧`, `无形资产摊销`, `长期待摊费用摊销`, `折旧与摊销`
- revenue denominator: `营业总收入`, `营业收入`

Guardrails:

- Amount fields and ratio fields are kept separate.
- R&D ratio and capex ratio require same-period revenue.
- Capex must come from the cash paid for long-term assets line, not balance-sheet assets or project narrative.
- R&D must come from profit-statement expense rows, not staffing, project, or narrative evidence.
- If cumulative versus single-quarter scope is unclear, the probe writes `unknown`.
- If unit context is absent, the probe writes `unit_confidence=low`.

## Probe Output Contract

Each `data/rd_capex_probe/probe_<code>.json` contains:

- `stock_code`
- `generated_at`
- `akshare_version`
- `functions_attempted`
- `function_results`

Each `function_result` contains:

- `function_name`
- `statement_type`
- `success`
- `error`
- `shape`
- `columns_full`
- `dtypes`
- `head_rows`
- `detected_report_periods`
- `detected_field_candidates`
- `target_field_matches`
- `sample_rows_by_keywords`

Each target match records:

- `matched`
- `source_function`
- `source_column`
- `source_row_name`
- `source_period`
- `value`
- `unit`
- `period_confidence`
- `value_confidence`
- `unit_confidence`
- `cumulative_or_single_quarter`
- `derivation_method`
- `notes`

## Replay Output Contract

`scripts/replay_rd_capex_probe.py` writes markdown with:

1. Successful Functions
2. Failed Functions
3. Target Field Mapping Summary
4. Per-field detail and v2.3 suitability
5. Derived Field Summary
6. Ambiguity / Risk Summary
7. v2.3 Recommendation

Recommendation buckets:

- `strongly recommended`
- `recommended with caution`
- `not ready`

## Local Commands

Probe six audited stocks:

```bash
python scripts/probe_rd_capex_fields.py --codes 002050 002371 300308 000426 601899 603993 --output-dir data/rd_capex_probe --limit-rows 5
```

Replay one probe:

```bash
python scripts/replay_rd_capex_probe.py --input data/rd_capex_probe/probe_002050.json --output data/rd_capex_probe/replay_002050.md
```

Replay is offline-only. Probe requires AkShare and network access to public data sources.

## v2.3 Readiness Criteria

Strongly recommended:

- direct row-name or column-name match;
- recognizable source period;
- numeric value;
- unit context is at least medium confidence;
- stable source family across multiple audited stocks.

Recommended with caution:

- derived ratio fields;
- clear source field but unit context requires confirmation;
- source appears stable in only one family.

Not ready:

- missing or inconsistent across audited stocks;
- ambiguous row names;
- non-numeric values;
- period mismatch for derived ratios;
- optional depreciation/amortization rows before component stability is proven.

## Expected Next Decision

After running six-stock real probes, decide whether v2.3 should promote:

- `r_and_d_expense`
- `r_and_d_expense_ratio`
- `capex`
- `capex_ratio`

`depreciation_amortization` should remain trace-only unless replay confirms a stable row family and aggregation policy.
