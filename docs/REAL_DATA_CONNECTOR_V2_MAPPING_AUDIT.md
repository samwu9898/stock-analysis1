# RealDataConnector v2 Mapping Audit

## 1. Scope

This audit is based only on the real offline AkShare probe files currently present in `data/real_probe/`:

- `probe_002050.json`
- `probe_000426.json`
- `probe_300308.json`
- `probe_002371.json`
- `probe_601899.json`

All five files exist. This document does not modify connector code, does not call AkShare, does not run the pipeline, and does not produce trading advice.

Probe metadata:

- `akshare_version`: `1.18.60`
- generated around `2026-05-17 16:22-16:24`
- `limit_rows`: 5

Important limitation: the probe stores only `head` rows. For `stock_financial_abstract`, the returned table is a wide table with rows as indicators and columns as periods. Because only the first five rows were saved, this audit can confirm mappings for those first five indicators only.

## 2. Successful Functions By Stock

| code | basic_info | financial_indicator | valuation | business_composition | news |
|---|---|---|---|---|---|
| 002050 | `stock_individual_info_em`, `stock_profile_cninfo` | `stock_financial_analysis_indicator`, `stock_financial_abstract` | none | none | `stock_news_em` |
| 000426 | `stock_profile_cninfo` | `stock_financial_analysis_indicator`, `stock_financial_abstract` | none | none | `stock_news_em` |
| 300308 | `stock_profile_cninfo` | `stock_financial_analysis_indicator`, `stock_financial_abstract` | none | none | `stock_news_em` |
| 002371 | `stock_profile_cninfo` | `stock_financial_analysis_indicator`, `stock_financial_abstract` | none | none | `stock_news_em` |
| 601899 | `stock_profile_cninfo` | `stock_financial_analysis_indicator`, `stock_financial_abstract` | none | none | `stock_news_em` |

Observations:

- `stock_profile_cninfo` is the most stable `basic_info` source across all five stocks.
- `stock_individual_info_em` succeeded only for `002050`; it should be a secondary source, not the v2 primary source.
- `stock_financial_analysis_indicator` reported success but returned empty DataFrames: `columns=[]`, `shape=[0, 0]`. It should not be considered useful unless future probes show non-empty output.
- `stock_financial_abstract` returned non-empty wide financial tables for all five stocks.
- `stock_news_em` returned non-empty news tables for all five stocks.
- No valuation or business composition candidate succeeded in this probe set.

## 3. Financial Indicator Columns

### `stock_financial_analysis_indicator`

For all five stocks:

- `columns=[]`
- `shape=[0, 0]`
- `head=[]`

Although marked success by the probe, it provides no usable columns in these samples.

### `stock_financial_abstract`

For all five stocks, columns follow the same structure:

- `选项`
- `指标`
- many period columns such as `20260331`, `20251231`, `20250930`, `20250630`, `20250331`, `20241231`, ...

Observed shapes:

- `002050`: `[80, 92]`
- `000426`: `[80, 115]`
- `300308`: `[80, 66]`
- `002371`: `[80, 78]`
- `601899`: `[80, 80]`

The saved head rows show these first five `指标` values for all five stocks:

- `归母净利润`
- `营业总收入`
- `营业成本`
- `净利润`
- `扣非净利润`

This means v2 needs a parser that pivots or reads this wide table by indicator name and period. It should not treat each row as one reporting period.

## 4. Confirmed Financial Field Mapping

Based on columns/head rows actually present in the probe JSON:

| target field | mapping status | source function | source row/columns | notes |
|---|---|---|---|---|
| `revenue_yoy` | derivable, not direct | `stock_financial_abstract` | row `营业总收入`, period columns | Can derive YoY by comparing latest period to same quarter previous year, e.g. `20260331` vs `20250331`, or annual `20251231` vs `20241231`. Must label as derived. |
| `net_profit_yoy` | derivable, not direct | `stock_financial_abstract` | row `归母净利润` or `净利润`, period columns | Prefer `归母净利润` for shareholder profit trend; can derive YoY from matching period columns. |
| `deducted_net_profit` | direct | `stock_financial_abstract` | row `扣非净利润`, selected period column | Direct value is visible in head rows. |
| `gross_margin` | derivable, not direct | `stock_financial_abstract` | rows `营业总收入`, `营业成本` | Can derive `(营业总收入 - 营业成本) / 营业总收入 * 100`. Must label as derived. |
| `net_margin` | derivable, not direct | `stock_financial_abstract` | rows `净利润`, `营业总收入` | Can derive `净利润 / 营业总收入 * 100`. Must label as derived. |
| `roe` | unconfirmed | none in saved head rows | unknown | May exist later in the 80-row table, but current probe head does not prove it. |
| `operating_cashflow` | unconfirmed | none in saved head rows | unknown | May exist later in the 80-row table, but current probe head does not prove it. |
| `debt_to_asset` | unconfirmed | none in saved head rows | unknown | May exist later in the 80-row table, but current probe head does not prove it. |
| `inventory` | unconfirmed | none in saved head rows | unknown | May exist later in the 80-row table, but current probe head does not prove it. |
| `accounts_receivable` | unconfirmed | none in saved head rows | unknown | May exist later in the 80-row table, but current probe head does not prove it. |

Minimum v2 financial parser from current evidence:

1. Use `stock_financial_abstract`.
2. Ignore `stock_financial_analysis_indicator` when empty.
3. Select recent period columns.
4. Extract direct rows: `营业总收入`, `营业成本`, `归母净利润`, `净利润`, `扣非净利润`.
5. Derive `revenue_yoy`, `net_profit_yoy`, `gross_margin`, `net_margin`.
6. Keep `roe`, `operating_cashflow`, `debt_to_asset`, `inventory`, and `accounts_receivable` in `missing_fields` until a full-row probe confirms source rows.

## 5. Basic Info Mapping

### Stable primary source: `stock_profile_cninfo`

Successful for all five stocks with stable columns:

- `公司名称`
- `A股代码`
- `A股简称`
- `所属市场`
- `所属行业`
- `成立日期`
- `上市日期`
- `主营业务`
- `经营范围`
- `机构简介`

Recommended v2 mapping:

| target field | source column | confidence |
|---|---|---|
| `stock_code` | `A股代码` | high |
| `stock_name` | `A股简称` | high |
| `industry` | `所属行业` | high |
| `main_business` | `主营业务`; fallback `经营范围` | high |
| `listing_date` | `上市日期` | high |
| `market` | derive from `所属市场` or code prefix | medium |

### Secondary source: `stock_individual_info_em`

Succeeded only for `002050`. It returned item/value rows:

- `股票代码`
- `股票简称`
- market snapshot fields such as `最新`, `总股本`, `流通股`

Recommended use:

- Secondary fallback for `stock_code` and `stock_name`.
- Do not rely on it for `industry`, `main_business`, or `listing_date` based on current probe.

## 6. News Mapping

Stable source: `stock_news_em`, successful for all five stocks.

Observed columns:

- `关键词`
- `新闻标题`
- `新闻内容`
- `发布时间`
- `文章来源`
- `新闻链接`

Recommended v2 mapping:

| target field | source column | confidence |
|---|---|---|
| `title` | `新闻标题` | high |
| `publish_time` | `发布时间` | high |
| `source` | `文章来源` | high |
| `url` | `新闻链接` | high |
| `summary` | `新闻内容` | high |

Notes:

- Keep only a small recent sample, as v1 already does.
- News should remain auxiliary material, not a basis for high-confidence fundamental conclusions by itself.

## 7. Valuation Failure Diagnosis

No valuation candidate succeeded.

Observed failures:

- `stock_zh_a_spot_em`: `ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))`
- `stock_individual_spot_xq`: `KeyError: 'data'`
- `stock_bid_ask_em`: `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`

Interpretation:

- `stock_zh_a_spot_em` may be blocked, rate-limited, or unstable because it queries a large market-wide table.
- `stock_individual_spot_xq` did not return the expected JSON shape for the tested symbol format.
- `stock_bid_ask_em` did not return valid JSON in this probe.

No v2 mapping should be implemented from these failed samples.

Potential future probe candidates, not yet validated:

- A single-stock Eastmoney quote endpoint if AkShare exposes one with stable columns.
- Historical valuation interfaces, if available, for PE/PB/PS.
- Retry `stock_zh_a_spot_em` with throttling or outside peak time.
- Add a probe candidate that records raw shape for alternative symbol formats where available.

Until a valuation source succeeds, keep:

- `valuation_metrics`
- `pe_ttm`
- `pb`
- `ps`
- `market_cap`
- `dividend_yield`

as missing.

## 8. Business Composition Failure Diagnosis

No business composition candidate succeeded.

Observed failures:

- `stock_zygc_em`: `KeyError: 'zygcfx'`
- `stock_zygc_ym`: `function_not_found`
- `stock_main_business_cninfo`: `function_not_found`

Interpretation:

- `stock_zygc_em` exists but current response shape does not contain the expected `zygcfx` key for these samples or this AkShare version.
- The other two candidates are not available in `akshare==1.18.60`.

No v2 mapping should be implemented from these failed samples.

Potential future probe candidates:

- Additional CNInfo business composition interfaces if present in local AkShare.
- Annual report main-business composition interfaces by report period.
- A lower-level fallback that uses `stock_profile_cninfo` `主营业务` only for narrative classification, while keeping `business_composition.segments` missing.

Until a business composition source succeeds, keep:

- `business_composition`
- `business_composition.segments`
- `segment_name`
- `revenue`
- `revenue_ratio`
- `gross_margin` by segment

as missing.

## 9. RealDataConnector v2 Minimum Scope

Based on current real probe evidence, the smallest defensible v2 is:

1. Use `stock_profile_cninfo` as primary `basic_info`.
2. Use `stock_individual_info_em` only as fallback for `stock_code` and `stock_name` when it succeeds.
3. Use `stock_news_em` for news.
4. Use `stock_financial_abstract` as the primary financial source.
5. Implement a wide-table financial parser:
   - period columns are date strings such as `20260331`, `20251231`.
   - rows are selected by `指标`.
   - direct extraction: `deducted_net_profit` from `扣非净利润`.
   - derived values: `revenue_yoy`, `net_profit_yoy`, `gross_margin`, `net_margin`.
6. Treat empty successful DataFrames as unusable, especially `stock_financial_analysis_indicator`.
7. Keep valuation and business composition missing until new probes identify successful sources.

This would likely allow real-data pipeline classification to improve materially because `stock_name`, `industry`, `main_business`, `financial_metrics`, and `news` would become available.

## 10. Fields That Must Continue To Enter `missing_fields`

From current probe evidence:

- `valuation_metrics`
- `valuation_metrics.pe_ttm`
- `valuation_metrics.pb`
- `valuation_metrics.ps`
- `valuation_metrics.market_cap`
- `valuation_metrics.dividend_yield`
- `business_composition`
- `business_composition.segments`
- `financial_metrics.roe`
- `financial_metrics.operating_cashflow`
- `financial_metrics.debt_to_asset`
- `financial_metrics.inventory`
- `financial_metrics.accounts_receivable`

Conditional:

- `financial_metrics.gross_margin` and `financial_metrics.net_margin` should not be missing if v2 derives them from `营业总收入` and `营业成本` / `净利润`.
- `financial_metrics.revenue_yoy` and `financial_metrics.net_profit_yoy` should not be missing if v2 derives them from matching period columns.

## 11. Required Follow-Up Probe

Because the current probe only stored head 5 rows, a more useful financial probe should store:

- full `指标` list for `stock_financial_abstract`, without all period values;
- or at least rows whose `指标` matches cash flow, ROE, asset-liability ratio, inventory, accounts receivable, and margin keywords.

Suggested next probe enhancement:

- keep `limit_rows` for raw head,
- additionally save `indicator_values` for columns named `指标`,
- save only indicator names, not full large data.

That would let v2 map the remaining financial fields without collecting huge data files.

## 12. Boundary

This audit does not connect to LLMs, trading accounts, technical indicators, HTML generation, or `trader_skill`. It does not modify legacy modules.
## 13. Probe Enhancement Status

The next step before `RealDataConnector v2` is the enhanced offline probe, not connector implementation. The enhanced probe records `indicator_names_full`, `period_columns`, `row_count`, and `sample_rows_by_keywords` for DataFrames with a column named `指标`, especially `stock_financial_abstract`.

Once fresh real probes are regenerated locally, this audit should be updated from the new JSON evidence:

- If `indicator_names_full` confirms `ROE` or `净资产收益率`, v2 can map `financial_metrics.roe`.
- If it confirms `经营现金流` or `经营活动现金流`, v2 can map `financial_metrics.operating_cashflow`.
- If it confirms `资产负债率`, v2 can map `financial_metrics.debt_to_asset`.
- If it confirms `存货`, v2 can map `financial_metrics.inventory`.
- If it confirms `应收账款`, v2 can map `financial_metrics.accounts_receivable`.

Until those fresh enhanced probe files are present and reviewed, these fields must remain in `missing_fields`. This document still does not authorize implementing `RealDataConnector v2`, changing the legacy modules, adding technical indicators, generating HTML, calling LLMs, calling trading accounts, or producing trading advice.
## 14. Implemented v2 Mapping

`RealDataConnector v2` is now implemented from enhanced probe evidence. It keeps the existing raw JSON contract and writes mapping provenance into `fetch_status`, avoiding a broad schema migration.

Implemented source selection:

- `stock_profile_cninfo` for `basic_info`.
- `stock_news_em` for `news`.
- `stock_financial_abstract` for `financial_indicator`.
- No valuation source yet.
- No business composition source yet.

Implemented financial mappings from `stock_financial_abstract`:

| target field | primary mapping | fallback / derivation |
|---|---|---|
| `revenue_yoy` | `营业总收入增长率` | derive from `营业总收入` latest period vs same period last year |
| `net_profit_yoy` | `归属母公司净利润增长率`, `归母净利润增长率` | derive from `归母净利润`, fallback `净利润` |
| `deducted_net_profit` | `扣非净利润` | none |
| `gross_margin` | `毛利率` | `(营业总收入 - 营业成本) / 营业总收入 * 100` |
| `net_margin` | `销售净利率`, `净利率` | `净利润 / 营业总收入 * 100` |
| `roe` | `净资产收益率(ROE)` | `净资产收益率_平均`, `摊薄净资产收益率` |
| `operating_cashflow` | `经营现金流量净额` | none |
| `debt_to_asset` | `资产负债率` | none |
| `inventory` | exact `存货` amount row only | turnover rows are not mapped |
| `accounts_receivable` | exact `应收账款` amount row only | turnover rows are not mapped |

Important protection:

- `存货周转率` and `存货周转天数` are not inventory amount fields.
- `应收账款周转率` and `应收账款周转天数` are not accounts receivable amount fields.
- If only proxy turnover indicators are found, v2 leaves the amount field missing and records a warning in `fetch_status.financial_indicator.warnings`.

Derived values:

- `yoy_from_same_period` for YoY fallback.
- `margin_from_revenue_cost` for gross margin fallback.
- `margin_from_revenue_profit` for net margin fallback.

The connector remains fail-soft. Any block or field parsing failure is recorded as missing or warning rather than crashing the whole raw JSON generation.

## 15. Source Expansion Probe Status

The next step is now explicitly an expanded probe/replay evidence pass, not a `RealDataConnector v2.1` implementation.

Probe-only additions:

- `valuation` candidates now include broader A-share spot tables, PE/PB/dividend-yield tables, single-stock value analysis, Baidu valuation endpoints, and Eastmoney valuation comparison candidates.
- `business_composition` candidates now retry known main-business composition functions with plain code, lowercase prefixed code, exchange-prefixed code, and known stock-name symbols.
- `commodity_prices` is a new probe category for external resource variables, including candidate spot, Shanghai Gold Exchange, domestic futures spot, and foreign commodity realtime functions.

Replay-only additions:

- valuation summary reports possible mappings for `pe_ttm`, `pb`, `ps`, `market_cap`, and `dividend_yield`;
- business-composition summary reports possible mappings for `segment_name`, `revenue`, `revenue_ratio`, `gross_margin`, and `period`, and marks empty successful tables;
- commodity-price summary reports successful functions, commodity coverage, and whether the evidence may later support `resource_swing` or `resource_core` frameworks.

Current connector status remains unchanged:

- no new valuation source is mapped into `RealDataConnector v2`;
- no new business-composition source is mapped into `RealDataConnector v2`;
- no commodity-price source is mapped into `RealDataConnector v2`;
- `external.commodity_prices` remains a missing external-variable gap for resource strategies until a separate connector design is reviewed.

Fresh probe files should be generated locally with:

```bash
python scripts/probe_akshare_real_data.py --codes 002050 000426 300308 002371 601899 --output-dir data/real_probe --limit-rows 5
python scripts/replay_real_data_probe.py --input data/real_probe/probe_601899.json --output data/real_probe/replay_601899.md
```

Only after reviewing the new offline evidence should a future `RealDataConnector v2.1` mapping be considered.

## 16. Implemented v2.1 Mapping

Fresh probe/replay evidence from `probe_002050.json`, `probe_000426.json`, `probe_601899.json`, and their replay reports confirmed stable sources for valuation and business composition.

Implemented in `real_data_connector.v2.1`:

- `valuation` is now mapped from `stock_value_em`.
- `business_composition` is now mapped from `stock_zygc_em`.
- `commodity_prices` remains probe/replay only and is not mapped.

### Valuation

Primary source: `stock_value_em`.

Observed stable columns:

- `数据日期`
- `PE(TTM)`
- `市净率`
- `市销率`
- `总市值`
- `流通市值`

Implemented fields:

| target field | source column |
|---|---|
| `pe_ttm` | `PE(TTM)` |
| `pb` | `市净率` |
| `ps` | `市销率` |
| `market_cap` | `总市值` |
| `dividend_yield` | not mapped |

Protections:

- latest row is selected by sortable `数据日期`;
- if date sorting fails, the first available row is used and a warning is recorded;
- numeric conversion is best-effort and field-level failures do not crash the block;
- `PEG值` is not used as `pe_ttm`;
- forecast PE columns from `stock_zh_valuation_comparison_em`, such as `市盈率-25E`, `市盈率-26E`, and `市盈率-27E`, are not used as primary TTM PE;
- `dividend_yield` remains missing until a stable source is confirmed.

### Business Composition

Primary source: `stock_zygc_em`.

Observed stable columns:

- `股票代码`
- `报告日期`
- `分类类型`
- `主营构成`
- `主营收入`
- `收入比例`
- `主营成本`
- `成本比例`
- `主营利润`
- `利润比例`
- `毛利率`

Implemented segment mapping:

| target field | source column |
|---|---|
| `period` | `报告日期` |
| `segment_name` | `主营构成` |
| `classification_type` | `分类类型` |
| `revenue` | `主营收入` |
| `revenue_ratio` | `收入比例` |
| `gross_margin` | `毛利率` |
| `cost` | `主营成本` |
| `cost_ratio` | `成本比例` |
| `profit` | `主营利润` |
| `profit_ratio` | `利润比例` |

Protections:

- latest `报告日期` is selected;
- all valid rows from that reporting period are retained;
- rows with empty `主营构成` are filtered out;
- `分类类型` is preserved but never used as `segment_name`;
- empty tables remain fail-soft and produce `business_composition.segments` as missing.

### Source Trace

v2.1 extends trace entries where needed:

- valuation field traces include `source_column`, `source_period`, `function_name=stock_value_em`, `value`, and `derived=false`;
- business-composition trace includes `function_name=stock_zygc_em`, latest `source_period`, selected `row_count`, and source `columns`.

### Commodity Prices

Commodity prices are not part of v2.1. The probe showed successful candidates, but replay explicitly marks commodity data as not connector-ready. A future `External Commodity Price Connector v1` should separately handle commodity-to-company exposure mapping, units, spot/futures differences, and contract selection.
