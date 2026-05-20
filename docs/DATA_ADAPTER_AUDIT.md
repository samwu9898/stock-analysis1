# Data Adapter 审计

## 1. 现有 raw JSON 可能结构

当前项目的主要数据产物来自 `stock_full_report.py` 和 `src/data_fetcher.py`。

已观察到的真实输出：

```json
{
  "blocks": {
    "basic_info": [],
    "spot": [],
    "share_structure": [],
    "zygc": [],
    "kline_daily": [],
    "kline_minute": [],
    "fund_flow": [],
    "fin_abstract": [],
    "fin_indicator_ths": [],
    "balance_sheet": [],
    "income_statement": [],
    "cashflow": [],
    "news": [],
    "research": []
  }
}
```

`stock_full_report.py` 内部的 `StockReportData` 有 `code / prefixed / market / generated_at / ak_version / errors` 字段，但最终保存 JSON 时目前只写入 `{"blocks": data.blocks}`。因此下游不能稳定获得元信息。

未来也可能出现更完整结构：

```json
{
  "meta": {
    "code": "000426",
    "market": "sz",
    "generated_at": "2026-05-15T10:00:00",
    "data_cutoff": "2026-05-14"
  },
  "fetch_status": {},
  "errors": [],
  "blocks": {}
}
```

Data Adapter 需要兼容这两种结构，并对未知结构尽量返回可检查对象。

## 2. 可映射到基本面输入的 block

- `basic_info / company_info / stock_info / 个股信息 / 公司资料`：映射到 `BasicInfoInput`。
- `spot / valuation / market_data / quote / 估值`：映射到 `ValuationMetricInput`。
- `fin_indicator_ths / fin_abstract / financial_indicator / financial_abstract / finance`：映射到 `FinancialMetricInput`。
- `balance_sheet / income_statement / cashflow`：可作为财务补充数据，但字段形态差异较大，目前仅宽松抽取能识别的字段。
- `zygc / business_composition / main_business / 主营构成 / 业务构成`：映射到 `BusinessCompositionInput`。
- `news / latest_news / notice / 公告 / 新闻`：映射到 `NewsItemInput`。
- `research`：目前不直接映射到新闻，后续可单独建研报输入结构。

## 3. 缺失的元信息

现有真实 `output/data_000426.json` 顶层只有 `blocks`，缺少：

- `meta.code`
- `meta.market`
- `meta.generated_at`
- `meta.data_cutoff`
- `akshare_version`
- 每个 block 的 `fetched_at`
- 每个 block 的原始 source 名称
- 每个 block 的错误信息

Adapter 会尝试从文件名、`spot`、`basic_info` 或业务构成中推断股票代码，但推断不能视为强保证。

## 4. 无法稳定获得的字段

以下字段当前无法保证稳定映射：

- `industry`：部分 AkShare 来源为空，或字段名随接口变化。
- `main_business`：`basic_info` 为空时无法获得，只能依赖主营构成。
- `listing_date`：不同来源字段名和格式不稳定。
- `gross_margin / net_margin / roe`：不同财务 block 的字段命名差异大。
- `operating_cashflow / debt_to_asset / inventory / accounts_receivable`：可能分散在三大报表中，当前只做宽松字段命中。
- `pe_ttm / pb / ps / dividend_yield / market_cap`：需要依赖行情快照或估值 block，真实接口字段可能缺失。
- `business_composition.segments`：主营构成字段可稳定保留 raw，但标准字段只做 best-effort 映射。

## 5. Data Adapter 最小兼容设计

Data Adapter 的目标是“结构标准化”，不是分析判断。

最小设计：

1. 输入 `meta + blocks`、纯 `blocks` 或未知 dict。
2. 输出 `NormalizedFundamentalInput`。
3. 保留完整 `raw_blocks`。
4. 尽量抽取基础信息、财务指标、估值、主营构成和新闻。
5. 为每个 block 生成 `RawBlockStatus`。
6. 为每个 block 生成 `DataSource`。
7. 解析不到的重要字段写入 `missing_fields`。
8. 结构异常或元信息缺失写入 `adapter_warnings`。
9. 不输出 `supportive / neutral / negative`。
10. 不输出任何交易建议。
