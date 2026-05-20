# Real Data Connector Audit

## 1. 定位

`RealDataConnector` 是 `fundamental_skill` 的真实公开数据入口。它接收 A 股 6 位股票代码，通过 AkShare 尝试获取公开数据，并转换成 `FundamentalDataAdapter` 可以消费的 raw JSON。

它只负责数据获取、字段映射、错误记录和缓存，不负责分析、不负责评分、不负责交易判断。

边界：
- 不接 LLM。
- 不接交易账户。
- 不生成 HTML。
- 不输出交易建议。
- 不引入技术指标。
- 不修改旧的 `src/analyzer.py`、`src/html_renderer.py`、`src/data_fetcher.py`。
- 不实现 `trader_skill`。

## 2. 与 Data Adapter / Pipeline 的关系

当前链路为：

```text
stock_code
  -> RealDataConnector
  -> raw JSON
  -> FundamentalSkillPipeline
  -> FundamentalAnalysisResult
```

`RealDataConnector.fetch_to_raw_json()` 输出的 raw JSON 包含：
- `meta`
- `blocks.basic_info`
- `blocks.financial_indicator`
- `blocks.valuation`
- `blocks.business_composition`
- `blocks.news`
- `fetch_status`
- `errors`

`FundamentalDataAdapter` 继续负责把 raw JSON 标准化为 `NormalizedFundamentalInput`。后续 classifier、readiness、context、scoring 和 assembler 的职责不变。

## 3. AkShare 接口不稳定性

AkShare 是公开数据聚合库，接口名称、字段名、返回列、限频和可用性都可能变化。因此 connector 对每个数据块单独 try/except：

- 某个接口失败不会让整体流程崩溃。
- 失败写入 `errors`。
- 每个 block 的成功、错误、缺失字段写入 `fetch_status`。
- 尽量返回可用 raw JSON，让 pipeline 用现有数据继续给出低置信度或带缺口的结果。

## 4. 数据缺失处理

connector 不硬猜字段。无法稳定取得的字段保留为空，并写入该 block 的 `missing_fields`。

当前目标字段包括：
- `basic_info`：股票代码、股票名称、行业、主营业务、上市日期。
- `financial_indicator`：收入增速、净利润增速、扣非净利润、毛利率、净利率、ROE、经营现金流、资产负债率、存货、应收账款。
- `valuation`：PE TTM、PB、PS、市值、股息率。
- `business_composition`：业务名称、收入、收入占比、毛利率。
- `news`：标题、发布时间、来源、链接、摘要。

## 5. 缓存机制

缓存路径：

```text
cache/real_data/<code>.json
```

规则：
- 默认 24 小时内已有缓存时优先使用缓存。
- CLI 支持 `--force-refresh` 强制重新获取。
- 如果新抓取失败但旧缓存存在，connector 会返回旧缓存，并在 `meta.cache_fallback_reason` 写入 `fresh_fetch_failed`。
- `meta.cache_created_at`、`meta.cache_hit` 和 `meta.cache_path` 用于审计缓存状态。

## 6. CLI 示例

```bash
python -m src.fundamental_skill.real_stock_runner --code 002050 --output output/fundamental_002050.json
```

流程：
1. 通过 `RealDataConnector` 获取 raw JSON。
2. 保存 `output/raw_002050.json`。
3. 调用 `FundamentalSkillPipeline.analyze_from_dict(raw_json)`。
4. 保存 `output/fundamental_002050.json`。
5. 控制台打印基本字段、风险数量、跟踪项数量、缺失字段和错误数量。

## 7. 当前限制

- AkShare 字段覆盖无法保证，部分字段可能长期缺失。
- 第一版只做保守字段映射，不做复杂表间拼接。
- 不做真实行业资本开支、客户收入占比、订单金额、库存周期或估值分位增强。
- 新闻只作为公开文本材料进入 raw JSON，不做语义理解。
- 测试使用 mock connector，不依赖真实网络。

## 8. 为什么 v1 不追求完美字段覆盖

真实公开数据接口变化频繁，第一版目标是先打通可审计的数据入口和 pipeline 闭环。相比追求字段全覆盖，更重要的是：

- 任一接口失败时系统仍可运行。
- 数据缺失被显式记录。
- pipeline 可以稳定消费 raw JSON。
- regression suite 不受真实网络影响。
- 后续可以逐步替换或增强单个数据块，而不改变 fundamental_skill 主链路。
## RealDataConnector v2 Update

`RealDataConnector` has moved to `real_data_connector.v2`. The connector is still only a public-data adapter: it does not call LLMs, trading accounts, technical indicators, HTML renderers, or `trader_skill`.

v2 confirmed sources:

- `basic_info`: primary source is `stock_profile_cninfo`.
  - `stock_code` <- `A股代码`
  - `stock_name` <- `A股简称`, fallback `公司名称`
  - `industry` <- `所属行业`
  - `main_business` <- `主营业务`, fallback `经营范围`
  - `listing_date` <- `上市日期`
- `news`: primary source is `stock_news_em`.
  - `title` <- `新闻标题`
  - `publish_time` <- `发布时间`
  - `source` <- `文章来源`
  - `url` <- `新闻链接`
  - `summary` <- `新闻内容`
- `financial_indicator`: primary source is `stock_financial_abstract`.
  - The connector parses the wide table by `指标` rows and date-like period columns such as `20260331`.
  - The latest period is selected lexicographically from period columns.
  - `revenue_yoy` prefers `营业总收入增长率`; fallback derives YoY from `营业总收入` latest period and same period last year.
  - `net_profit_yoy` prefers `归属母公司净利润增长率` / `归母净利润增长率`; fallback derives YoY from `归母净利润`, then `净利润`.
  - `deducted_net_profit` maps from `扣非净利润`.
  - `gross_margin` prefers `毛利率`; fallback derives `(营业总收入 - 营业成本) / 营业总收入 * 100`.
  - `net_margin` prefers `销售净利率` / `净利率`; fallback derives `净利润 / 营业总收入 * 100`.
  - `roe` maps from `净资产收益率(ROE)`, fallback `净资产收益率_平均` or `摊薄净资产收益率`.
  - `operating_cashflow` maps from `经营现金流量净额`.
  - `debt_to_asset` maps from `资产负债率`.

Still missing in v2:

- `valuation`: no stable successful source has been confirmed, so the block remains empty and its fields remain missing.
- `business_composition`: no stable successful source has been confirmed, so the block remains empty and its fields remain missing.
- `inventory`: not mapped from `存货周转率` or `存货周转天数`. It is mapped only when a clear `存货` amount row exists.
- `accounts_receivable`: not mapped from `应收账款周转率` or `应收账款周转天数`. It is mapped only when a clear `应收账款` amount row exists.

Source trace:

Each successful mapped field records `source_trace` under `fetch_status.<block_name>.source_trace`, with:

- `block_name`
- `field_name`
- `function_name`
- `source_indicator`
- `source_period`
- `value`
- `derived`
- `derivation_method`

Warnings are recorded under `fetch_status.<block_name>.warnings`. If only turnover proxy indicators exist for inventory or accounts receivable, v2 records a warning and leaves the amount field missing.
## Real Data Calibration Patch

Connector v2 can now provide enough real data for a conservative fundamental read even when public sources still lack valuation or business composition. The downstream rules have been calibrated accordingly:

- `valuation` remains empty until a stable source is confirmed.
- `business_composition` remains empty until a stable source is confirmed.
- These gaps are common in real public data and should lower confidence, not automatically force `insufficient_data`.
- `business_composition` missing still forbids revenue-share claims and must create a business composition risk.
- `valuation_metrics` missing still forbids valuation-level claims and must create valuation-data tracking needs.
- `accounts_receivable` missing still creates a collection-quality risk and keeps financial/risk dimensions constrained.

The connector itself remains fail-soft and deterministic. It does not generate HTML, call LLMs, call trading accounts, introduce technical indicators, or output trading advice.

## RealDataConnector v2.1 Update

`RealDataConnector` has moved to `real_data_connector.v2.1` for two additional public-data blocks. It remains a data-layer adapter only: no LLM, no trading account, no HTML generation, no technical indicator, no trading advice, and no `trader_skill`.

v2.1 added:

- `valuation`: primary source is `stock_value_em`.
- `business_composition`: primary source is `stock_zygc_em`.

Valuation mapping from `stock_value_em`:

| target field | source column | notes |
|---|---|---|
| `pe_ttm` | `PE(TTM)` | TTM field only; PEG and forecast PE are not used. |
| `pb` | `市净率` | Direct numeric mapping. |
| `ps` | `市销率` | Direct numeric mapping. |
| `market_cap` | `总市值` | Direct numeric mapping. |
| `dividend_yield` | none | Still missing in v2.1. |

The connector selects the latest row by sortable `数据日期`. If sorting fails, it falls back to the first available row and records a warning. Each mapped field records `source_trace` with `block_name=valuation`, `function_name=stock_value_em`, `source_column`, `source_period`, `value`, and `derived=false`.

Business composition mapping from `stock_zygc_em`:

- latest `报告日期` is selected;
- all valid rows from that latest reporting period are kept;
- rows with empty `主营构成` are filtered out;
- `segment_name` comes only from `主营构成`, not `分类类型`;
- `classification_type` is preserved so later analysis can distinguish product, industry, or region rows.

Segment fields:

- `period` <- `报告日期`
- `segment_name` <- `主营构成`
- `classification_type` <- `分类类型`
- `revenue` <- `主营收入`
- `revenue_ratio` <- `收入比例`
- `gross_margin` <- `毛利率`
- `cost` <- `主营成本`
- `cost_ratio` <- `成本比例`
- `profit` <- `主营利润`
- `profit_ratio` <- `利润比例`

Business-composition `source_trace` records `function_name=stock_zygc_em`, latest `source_period`, selected `row_count`, and source `columns`.

Fail-soft behavior remains unchanged. Empty or malformed valuation/business-composition data does not crash the raw JSON generation; it produces missing fields and warnings.

`commodity_prices` is intentionally not connected in v2.1. Although the source expansion probe found successful commodity candidates, replay still marks `connector_ready=false`. Commodity data requires a separate External Commodity Price Connector design for product mapping, units, contract selection, and spot/futures distinctions.

## External Commodity Price Connector v1

`RealDataConnector` now performs a minimal optional integration with `ExternalCommodityPriceConnector`. If the stock code appears in `config/commodity_exposure_map.yaml`, raw JSON includes `blocks.commodity_prices` and `fetch_status.commodity_prices`.

The connector supports `000426` (`silver`, `tin`), `601899` (`copper`, `gold`), and partial `603993` (`copper`; `cobalt` and `molybdenum` remain missing in v1). Non-mapped stocks do not receive a commodity block and are not affected.

Primary data comes from `futures_spot_price`, with `futures_spot_price_daily` as fallback. Stale primary rows are kept as candidates but do not stop fallback selection and do not satisfy readiness. SGE benchmark functions are fallbacks for silver and gold. Foreign commodity realtime data is reference-only and does not satisfy readiness.

Failures are fail-soft: unavailable functions, empty frames, stale observations, and probe-only commodities enter `warnings`, `missing_fields`, `stale_commodities`, `missing_commodities`, and `source_trace` rather than stopping raw JSON generation. Missing fields are reported at commodity or freshness level when a commodity block exists.

## External Commodity Price Connector v1.1 Integration Note

The RealDataConnector integration point is unchanged: mapped resource stocks still receive `blocks.commodity_prices` and `fetch_status.commodity_prices` from `ExternalCommodityPriceConnector`.

Connector v1.1 expands the connector-side source chain for copper and tin:

- copper uses `futures_zh_realtime(symbol="沪铜")`, then `futures_zh_daily_sina(symbol="CU0")`, then `futures_main_sina(symbol="CU0")`;
- tin uses `futures_zh_realtime(symbol="沪锡")`, then `futures_zh_daily_sina(symbol="SN0")`, then `futures_main_sina(symbol="SN0")`.

Fresh domestic rows from these sources can clear the commodity freshness gap. Stale rows remain trace-only, and foreign realtime data remains reference-only. `cobalt` and `molybdenum` are still not connected because no stable domestic primary source has been promoted.

## RealDataConnector v2.2a Update

`RealDataConnector` has moved to `real_data_connector.v2.2a` for a narrow Financial Statement Period Binding integration. v2.2a only adds three balance-sheet amount fields to `blocks.financial_indicator`:

- `inventory` <- `stock_financial_report_sina(indicator="资产负债表")` column `存货`
- `accounts_receivable` <- `stock_financial_report_sina(indicator="资产负债表")` column `应收账款`
- `contract_liabilities` <- `stock_financial_report_sina(indicator="资产负债表")` column `合同负债`

The source period is bound from `报告日`. If `报告日` is an 8-digit report date such as `20260331`, `period_confidence=high`; otherwise the connector writes `source_period="unknown"`, `period_confidence=low`, records a warning, and continues without crashing.

Field-level `source_trace` now records `field_name`, `value`, `source_function`, `source_column_or_row`, `source_period`, `period_confidence`, `value_confidence`, `statement_type=balance_sheet`, and `scope_note`. `value_confidence` remains conservative (`medium`) because `stock_financial_report_sina` is a public aggregation source and is not treated as unconditional high-confidence truth.

`contract_liabilities` is only an order-visibility proxy. Its scope note is: `合同负债可作为订单可见度 proxy，但不等同于真实订单或 backlog。`

v2.2a still does not connect R&D expense, R&D expense ratio, capex, capex ratio, customer concentration, new-business orders, domestic-substitution revenue, production/unit cost, cobalt price, or molybdenum price. R&D and Capex require a separate Source Expansion Probe before connector integration.
