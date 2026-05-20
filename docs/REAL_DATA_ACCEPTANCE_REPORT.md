# Real Data End-to-End Acceptance Report

Generated on: 2026-05-18

## Scope

This report freezes the current real-data end-to-end state of `fundamental_skill` before any later `technical_skill` or `trader_skill` work. It is based on the current files under `output/`:

- `fundamental_002050.json`
- `fundamental_000426.json`
- `fundamental_300308.json`
- `fundamental_002371.json`
- `fundamental_601899.json`
- `fundamental_603993.json`
- `raw_000426.json`
- `raw_601899.json`
- `raw_603993.json`

No core code changes are included in this report.

## Connector Versions

- RealDataConnector: `real_data_connector.v2.1`
- ExternalCommodityPriceConnector: `v1.1`

`real_data_connector.v2.1` currently provides public real-data blocks for basic information, financial indicators, valuation, business composition, news, and optional commodity prices for mapped resource stocks.

`ExternalCommodityPriceConnector v1.1` adds fresh domestic copper and tin sources while keeping foreign commodity data as reference-only. Cobalt and molybdenum remain unavailable until a stable domestic primary source is confirmed.

## Six-Stock Fundamental Output Summary

| stock_code | stock_name | strategy_type | status | confidence | fundamental_score | risk_flags | must_track_indicators | missing_fields | errors |
|---|---|---|---|---|---:|---:|---:|---|---:|
| 002050 | 三花智控 | advanced_manufacturing_growth | neutral | medium | 63 | 4 | 12 | `financial_metrics.accounts_receivable` | 0 |
| 000426 | 兴业银锡 | resource_swing | supportive | high | 76 | 0 | 7 | none | 0 |
| 300308 | 中际旭创 | right_trend_growth | supportive | medium | 72 | 3 | 10 | none | 0 |
| 002371 | 北方华创 | semiconductor_cycle | neutral | medium | 61 | 5 | 11 | `financial_metrics.inventory` | 0 |
| 601899 | 紫金矿业 | resource_core | supportive | medium | 79 | 0 | 7 | none | 0 |
| 603993 | 洛阳钼业 | resource_swing | supportive | low | 70 | 1 | 8 | `external.commodity_prices.cobalt`, `external.commodity_prices.molybdenum` | 0 |

## Data Coverage by Stock

| stock_code | basic_info | financial_indicator | valuation | business_composition | news | commodity_prices |
|---|---|---|---|---|---|---|
| 002050 | success | success, period `20260331` | success, period `2026-05-15` | success, period `2025-12-31` | success, period `2026-05-18 09:20:00` | not applicable |
| 000426 | success | success, period `20260331` | success, period `2026-05-18` | success, period `2025-12-31` | success, period `2026-05-18 16:56:00` | success, period `2026-05-18` |
| 300308 | success | success, period `20260331` | success, period `2026-05-15` | success, period `2025-12-31` | success, period `2026-05-17 15:06:02` | not applicable |
| 002371 | success | success, period `20260331` | success, period `2026-05-15` | success, period `2025-12-31` | success, period `2026-05-18 10:15:00` | not applicable |
| 601899 | success | success, period `20260331` | success, period `2026-05-18` | success, period `2025-12-31` | success, period `2026-05-18 16:56:00` | success, period `2026-05-18` |
| 603993 | success | success, period `20260331` | success, period `2026-05-18` | success, period `2025-12-31` | success, period `2026-05-18 16:56:00` | partial, copper fresh; cobalt and molybdenum missing |

## Commodity Price Acceptance

| stock_code | stock_name | required commodities | accepted coverage |
|---|---|---|---|
| 000426 | 兴业银锡 | silver, tin | silver fresh via `spot_silver_benchmark_sge`, date `2026-05-14`, freshness_days `4`; tin fresh via `futures_zh_realtime`, date `2026-05-18`, freshness_days `0` |
| 601899 | 紫金矿业 | copper, gold | copper fresh via `futures_zh_realtime`, date `2026-05-18`, freshness_days `0`; gold fresh via `spot_golden_benchmark_sge`, date `2026-05-14`, freshness_days `4` |
| 603993 | 洛阳钼业 | copper, cobalt, molybdenum | copper fresh via `futures_zh_realtime`, date `2026-05-18`, freshness_days `0`; cobalt missing; molybdenum missing |

Commodity acceptance rule:

- `freshness_days <= 7` is fresh.
- Stale data does not satisfy readiness.
- Foreign reference data does not satisfy domestic primary readiness.
- Partial resource coverage stays partial and keeps specific missing fields.

## Remaining Known Data Gaps

- `financial_metrics.accounts_receivable`: still missing for 002050.
- `financial_metrics.inventory`: still missing for 002371.
- `external.commodity_prices.cobalt`: still missing for 603993.
- `external.commodity_prices.molybdenum`: still missing for 603993.
- `valuation_metrics.dividend_yield`: still not mapped from the confirmed v2.1 valuation source.

These gaps are represented as missing fields or connector-level known limitations. They should lower confidence or keep risk/context constraints where relevant, not crash the pipeline.

## System Boundary

`fundamental_skill` is currently accepted as a deterministic fundamental-analysis component only.

It does not:

- connect to an LLM;
- connect to an account;
- generate HTML;
- introduce technical indicators;
- produce portfolio or order instructions;
- convert commodity prices into price-trend or action signals.

Commodity prices are external context variables for resource-stock fundamental analysis. They improve data readiness when fresh and domestic, but they are not standalone signals.

`status=supportive` means the fundamental layer is supportive for later evaluation. It is not a direct instruction and does not replace later technical or execution-stage checks.

## Verification

Full pytest:

```text
173 passed in 6.51s
```

Regression suite:

```text
summary: passed=13 failed=0 total=13
```

## Acceptance Decision

The real-data chain is accepted for current `fundamental_skill` scope:

- six real-stock fundamental outputs are generated;
- raw resource-stock commodity blocks are present where applicable;
- 000426 and 601899 have complete fresh commodity coverage for their configured exposure;
- 603993 has fresh copper coverage and explicit cobalt/molybdenum gaps;
- all tested outputs remain pipeline-consumable;
- pytest and regression suite pass.

## Next Stage Options

1. Start `technical_skill` as a separate skill with its own data boundary and no dependency on changing the fundamental outputs.
2. Start `trader_skill` only after defining its interface contract and ensuring it consumes, rather than mutates, `fundamental_skill` outputs.
3. Continue source expansion for cobalt and molybdenum before expanding the resource-stock coverage universe.
