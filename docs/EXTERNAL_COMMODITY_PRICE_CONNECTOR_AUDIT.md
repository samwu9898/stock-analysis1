# External Commodity Price Connector v1 Audit

## Scope

`ExternalCommodityPriceConnector` supplies external commodity price observations for the deterministic `fundamental_skill` pipeline. It is limited to public AkShare data, raw JSON enrichment, readiness checks, context constraints, and risk-flag data quality handling.

It does not call LLMs, connect to accounts, render HTML, create price-trend analysis, or create action instructions.

## Supported Stock Exposure Map

The static exposure map lives in `config/commodity_exposure_map.yaml`.

- `000426`: `silver`, `tin`
- `601899`: `copper`, `gold`
- `603993`: `copper`, `cobalt`, `molybdenum`

`cobalt` and `molybdenum` are `probe_only` in v1 because no stable domestic primary price source has been promoted from probe evidence.

## Source Priority

1. `futures_spot_price` is the primary source and uses `spot_price`.
2. `futures_spot_price_daily` is the domestic fallback.
3. `spot_silver_benchmark_sge` is the silver fallback.
4. `spot_golden_benchmark_sge` is the gold fallback.
5. `futures_foreign_commodity_realtime` is saved as reference only and is not readiness eligible.

`spot_price_table_qh` remains a coverage/discovery table and is not treated as a price source.

Stale primary data no longer terminates source selection. If `futures_spot_price` returns a stale row, the connector records it as a candidate, continues to `futures_spot_price_daily`, and then tries the SGE fallback for silver or gold. If no fresh eligible source is found, the best stale row is returned as `source_priority=stale_reference` with `readiness_eligible=false`.

## Raw JSON Shape

Resource stocks with configured exposure add `blocks.commodity_prices` plus `fetch_status.commodity_prices`. Each normalized commodity row includes `commodity_name`, `commodity_name_cn`, `symbol`, `price`, `date`, `market`, `source_function`, `source_priority`, contract context fields, `freshness_days`, `is_stale`, `readiness_eligible`, and row-level warnings.

Partial coverage records specific fields such as `external.commodity_prices.cobalt`. Stale observations record freshness-specific gaps.

`fetch_status.commodity_prices` includes `success`, `missing_fields`, `missing_commodities`, `stale_commodities`, `partial_commodities`, `warnings`, and per-attempt `source_trace`. Success is true only when every required commodity has a fresh readiness-eligible source.

## Readiness and Context Behavior

Full, fresh domestic primary coverage satisfies `external.commodity_prices`. Partial coverage, stale data, and foreign-reference-only data keep the external field constrained. Existing missing-field rules continue to constrain `industry_cycle`, catalysts, confidence, and risk flags.

Freshness uses a seven-calendar-day threshold. Rows older than seven days, rows with unparseable dates, and foreign references do not satisfy readiness. Missing fields are reported at the most specific level available, for example `external.commodity_prices.copper.freshness` or `external.commodity_prices.cobalt`.

Commodity price observations are external context variables. They do not create price-trend analysis, technical indicators, HTML, account actions, or deterministic action instructions.

## Limits

- No cobalt or molybdenum primary source is enabled in v1.
- Units and currency are preserved only when the source clearly provides them.
- Contract fields are context variables, not replacements for domestic spot price.
- Price presence alone is not a fundamental conclusion.

## Copper/Tin Freshness Follow-up

Real raw-output diagnosis confirmed that the connector fallback logic is working, but domestic copper and tin remain stale with the current promoted sources. The probe layer has therefore been expanded before any connector v1.1 work.

The new probe-only candidates search for fresher domestic copper and tin evidence across `futures_zh_spot`, `futures_zh_daily_sina`, `futures_main_sina`, `futures_hist_em`, `futures_hist_daily_em`, `futures_hist_daily_sina`, `futures_shfe_daily`, `get_shfe_daily`, `futures_spot_price_previous`, `futures_spot_stock`, and `futures_spot_sys`.

This is intentionally not connected to `ExternalCommodityPriceConnector v1`. A source can only be promoted later if replay evidence shows:

- domestic source identity is clear;
- latest date is within the seven-calendar-day freshness window;
- a usable price column is present;
- symbol handling is stable for both `CU` and `SN`;
- foreign reference data is not mixed into domestic primary readiness.

## External Commodity Price Connector v1.1

v1.1 promotes fresh domestic copper and tin sources confirmed by replay. The raw JSON shape, fail-soft behavior, and readiness policy remain unchanged.

Copper source order:

1. `futures_zh_realtime(symbol="沪铜")`: `price <- trade`, `market=domestic_futures_realtime`, `source_priority=domestic_realtime_primary`.
2. `futures_zh_daily_sina(symbol="CU0")`: `price <- close`, `market=domestic_futures_daily`, `source_priority=domestic_daily_fallback`.
3. `futures_main_sina(symbol="CU0")`: `price <- 收盘价`, `market=domestic_futures_main`, `source_priority=domestic_main_fallback`.

Tin source order:

1. `futures_zh_realtime(symbol="沪锡")`: `price <- trade`, `market=domestic_futures_realtime`, `source_priority=domestic_realtime_primary`.
2. `futures_zh_daily_sina(symbol="SN0")`: `price <- close`, `market=domestic_futures_daily`, `source_priority=domestic_daily_fallback`.
3. `futures_main_sina(symbol="SN0")`: `price <- 收盘价`, `market=domestic_futures_main`, `source_priority=domestic_main_fallback`.

The older `futures_spot_price` and `futures_spot_price_daily` sources remain in the candidate chain. Stale rows from those sources are retained for traceability, but they do not terminate fallback selection and do not satisfy readiness.

Fresh rows from `domestic_realtime_primary`, `domestic_daily_fallback`, or `domestic_main_fallback` are readiness eligible. Foreign realtime rows remain `foreign_reference` only. `cobalt` and `molybdenum` remain missing until a stable domestic primary source is confirmed.

The connector preserves realtime/daily raw fields such as settlement, presettlement, open, high, low, close, volume, and hold when the source provides them. These are carried as raw context fields only; no trend calculation or action instruction is produced.
