# Financial Statement Field Mapping Audit v1

Date: 2026-05-19

Scope:

- Probe-only design for the next financial-statement field expansion.
- No `RealDataConnector` integration in this phase.
- No deterministic pipeline, dashboard, AI report, legacy analyzer, legacy renderer, or legacy data fetcher changes.
- No account integration, technical indicators, `technical_skill`, or `trader_skill` behavior.

New helpers:

- `scripts/probe_financial_statement_fields.py`
- `scripts/replay_financial_statement_probe.py`
- `tests/test_financial_statement_probe_replay.py`

## Why This Probe Exists

`docs/MUST_HAVE_INDICATOR_COVERAGE_AUDIT.md` found that the evidence pack has only 46.30% strict coverage and 52.78% effective coverage across audited must-have indicators. `semiconductor_cycle` is the weakest type, with only 27.78% effective coverage.

The best structured-data candidates for the next phase are financial-statement fields:

| target field | reason |
| --- | --- |
| `inventory` | Improves inventory-cycle and impairment-pressure analysis. |
| `accounts_receivable` | Improves revenue-quality and collection-pressure analysis. |
| `contract_liabilities` | Gives a structured partial proxy for order visibility. |
| `r_and_d_expense` | Supports technology-investment analysis. |
| `r_and_d_expense_ratio` | Makes R&D intensity comparable across stocks. |
| `capex` | Supports expansion-cycle and cash-flow-pressure analysis. |
| `capex_ratio` | Makes capex intensity comparable across stocks. |

The following fields are intentionally out of scope for this probe because they likely need announcement text, annual report text, research-note style curation, or manual input:

- `customer_concentration`
- `new_business_orders`
- `domestic_substitution_revenue`
- `production_or_unit_cost`
- cobalt and molybdenum commodity prices

## Candidate AkShare Functions

The probe defensively attempts the following functions with `hasattr` and `try/except`. Missing functions are recorded as `function_not_found`; parameter or runtime failures are recorded in the function result and do not stop the script.

### Balance Sheet Candidates

| function | target fields |
| --- | --- |
| `stock_balance_sheet_by_report_em` | `inventory`, `accounts_receivable`, `contract_liabilities` |
| `stock_balance_sheet_by_yearly_em` | `inventory`, `accounts_receivable`, `contract_liabilities` |
| `stock_balance_sheet_by_quarterly_em` | `inventory`, `accounts_receivable`, `contract_liabilities` |
| `stock_financial_report_sina` | fallback structure probe |

### Profit Sheet Candidates

| function | target fields |
| --- | --- |
| `stock_profit_sheet_by_report_em` | `r_and_d_expense`, revenue denominator |
| `stock_profit_sheet_by_yearly_em` | `r_and_d_expense`, revenue denominator |
| `stock_profit_sheet_by_quarterly_em` | `r_and_d_expense`, revenue denominator |
| `stock_financial_abstract` | fallback structure probe |

### Cash Flow Candidates

| function | target fields |
| --- | --- |
| `stock_cash_flow_sheet_by_report_em` | `capex`, possible revenue denominator if present |
| `stock_cash_flow_sheet_by_yearly_em` | `capex`, possible revenue denominator if present |
| `stock_cash_flow_sheet_by_quarterly_em` | `capex`, possible revenue denominator if present |
| `stock_financial_abstract` | fallback structure probe |

## Field Matching Rules

The probe looks for row names and column names. It supports wide statement tables with period columns such as `20260331`, and long tables with period columns such as `报告期`, `报告日期`, `日期`, or `截止日期`.

| target field | accepted Chinese labels |
| --- | --- |
| `inventory` | `存货`, `存货合计` |
| `accounts_receivable` | `应收账款`, `应收账款及应收票据`, `应收票据及应收账款`, `应收款项融资` |
| `contract_liabilities` | `合同负债`, `预收款项`, `预收账款` |
| `r_and_d_expense` | `研发费用`, `研究开发费用` |
| `capex` | `购建固定资产、无形资产和其他长期资产支付的现金`, `购建固定资产、无形资产和其他长期资产所支付的现金`, `购建固定资产、无形资产和其他长期资产支付现金` |
| revenue denominator | `营业总收入`, `营业收入` |

Derived fields:

- `r_and_d_expense_ratio = r_and_d_expense / 营业总收入 * 100`
- `capex_ratio = capex / 营业总收入 * 100`

If revenue is missing or not numeric, the ratio is not derived.

## Probe Output Contract

Each `data/financial_probe/probe_<code>.json` contains:

- `schema_version`
- `stock_code`
- `generated_at`
- `akshare_version`
- `functions_attempted`
- `target_fields`
- `function_results`

Each `function_result` contains:

- `statement_type`
- `function_name`
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

Each `target_field_matches.<field>` contains:

- `matched`
- `source_function`
- `source_column`
- `source_row_name`
- `source_period`
- `value`
- `unit`
- `confidence`
- `notes`

## Replay Output Contract

`scripts/replay_financial_statement_probe.py` reads a probe JSON and writes markdown with:

1. Successful Functions
2. Failed Functions
3. Target Field Mapping Summary
4. Per-target field detail:
   - whether found;
   - source function;
   - column or row;
   - latest report period;
   - current value;
   - scope note;
   - connector v2.2 suitability.
5. Derived Field Summary
6. Missing / Ambiguous Fields
7. v2.2 Connector Recommendation:
   - strongly recommended;
   - recommended with caution;
   - not ready.

## Local Commands

Probe six audited stocks:

```bash
python scripts/probe_financial_statement_fields.py --codes 002050 002371 300308 000426 601899 603993 --output-dir data/financial_probe --limit-rows 5
```

Replay one probe:

```bash
python scripts/replay_financial_statement_probe.py --input data/financial_probe/probe_002050.json --output data/financial_probe/replay_002050.md
```

The probe requires AkShare and network access to public data sources. Replay requires only the saved JSON file.

## v2.2 Readiness Criteria

Strongly recommended:

- direct row-name or column-name match;
- latest report period detected;
- numeric value present;
- stable source function across several audited stocks;
- no reliance on turnover-ratio proxy fields.

Recommended with caution:

- derived ratio fields;
- contract liabilities as a proxy for order visibility;
- fields that are found in only one source family;
- fields whose units require confirmation from AkShare output.

Not ready:

- missing in most audited stocks;
- ambiguous row names;
- non-numeric values;
- source function repeatedly unavailable;
- fields requiring text interpretation rather than structured statements.

## Expected Next Decision

After running six-stock probes and replay files locally, the next phase should decide whether connector v2.2 should add only:

- `inventory`
- `accounts_receivable`
- `contract_liabilities`
- `r_and_d_expense`
- `r_and_d_expense_ratio`
- `capex`
- optional `capex_ratio`

Fields outside this set should remain out of the connector until a separate text/curation design exists.
