# Real Data Probe & Offline Replay Audit

## 1. 为什么需要 Probe 阶段

Real Data Smoke Test 已证明 `RealDataConnector v1` 的 fail-soft 行为有效：AkShare 失败时不会导致 CLI 或 pipeline 崩溃，错误会进入 `fetch_status` 和 `errors`。

但当前 Codex 运行环境对 AkShare 目标域的 socket 访问被阻断，因此不能在这里直接确认真实 DataFrame 的列名、shape、字段含义和接口稳定性。贸然实现 v2 字段映射容易变成猜测。

Probe 阶段用于在本地可联网电脑上采集真实 AkShare 返回结构，保存为离线 JSON。之后 Codex 可以基于这些 JSON 做 RealDataConnector v2，而不是凭空写映射。

## 2. 当前环境限制

Codex 当前环境已能 import AkShare，但真实请求目标域失败，典型错误包括：

- `WinError 10013`
- `curl: (7) Failed to connect`

因此本阶段新增脚本，但不要求在 Codex 环境跑出真实 probe 数据。

## 3. 本地安装 AkShare

在你的可联网本地环境运行：

```bash
py -m pip install akshare
```

如果使用项目虚拟环境，也可以运行：

```bash
.venv\Scripts\python.exe -m pip install akshare
```

## 4. 运行 Probe

推荐命令：

```bash
py scripts/probe_akshare_real_data.py --codes 002050 000426 300308 002371 601899 --output-dir data/real_probe --limit-rows 5
```

如果 `python` 可用，也可以：

```bash
python scripts/probe_akshare_real_data.py --codes 002050 000426 300308 002371 601899 --output-dir data/real_probe --limit-rows 5
```

输出文件：

- `data/real_probe/probe_<code>.json`
- `data/real_probe/probe_<code>.md`

Probe 脚本只探测数据结构，不跑 pipeline，不做基本面分析，不输出交易建议。

## 5. Probe 记录内容

每个候选 AkShare 函数都会独立 try/except，并记录：

- `function_name`
- `success`
- `error`
- DataFrame columns
- DataFrame shape
- head rows，最多 `limit_rows`
- dtypes
- payload type

如果函数不存在，记录：

```json
{"success": false, "error": "function_not_found"}
```

## 6. 如何交回给 Codex

把生成的 `data/real_probe/probe_*.json` 放回项目同名目录，或直接发给 Codex。不要提交超大的真实数据文件；默认只保留 `head` 小样本即可。

目录结构已保留：

```text
data/real_probe/.gitkeep
```

## 7. 运行 Offline Replay

Replay 不联网，只读取 probe JSON：

```bash
py scripts/replay_real_data_probe.py --input data/real_probe/probe_002050.json
```

也可以指定 markdown 输出：

```bash
py scripts/replay_real_data_probe.py --input data/real_probe/probe_002050.json --output data/real_probe/replay_002050.md
```

默认会生成：

```text
data/real_probe/replay_002050.md
```

Replay 输出每个 block 哪些函数成功、哪些失败，以及可能用于 v2 的字段映射建议。

## 8. 下一步如何做 RealDataConnector v2

拿到真实 probe 后，v2 应按以下顺序推进：

1. 先选每个 block 最稳定的 AkShare 函数。
2. 基于真实 columns 建立字段映射，而不是猜列名。
3. 给 `basic_info` 和 `valuation` 增加 fallback，优先保障分类所需字段。
4. 为每个字段记录 source function 和 source column。
5. 用离线 probe JSON 新增 replay fixture 测试。
6. 再回到真实网络环境做 smoke test。

## 9. 当前限制

- Probe 只保存小样本结构，不判断数据质量。
- Replay 只给映射建议，不改 connector 代码。
- 候选函数覆盖不保证完整，可根据真实 probe 继续补充。
- 不接 LLM、不接交易账户、不生成 HTML、不输出交易建议、不引入技术指标。
## 10. Real Data Probe Enhancement

The probe now keeps the old compact fields and adds richer DataFrame metadata for offline mapping audits:

- `columns_full`: complete DataFrame column list. `columns` is still kept for backward compatibility.
- `shape`: DataFrame shape.
- `row_count`: number of rows in the returned DataFrame.
- `dtypes`: DataFrame dtypes by column.
- `head_rows`: head rows limited by `--limit-rows`. `head` is still kept for backward compatibility.
- `indicator_names_full`: complete values from a column named `指标`, when present.
- `option_names_full`: complete values from a column named `选项`, when present.
- `period_columns`: date-like period columns such as `20260331` and `20251231`.
- `sample_rows_by_keywords`: compact rows whose `指标` or `选项` text matches key financial mapping terms.

For `stock_financial_abstract`, the important new fields are `indicator_names_full`, `period_columns`, `row_count`, and `sample_rows_by_keywords`. The keyword sample is intentionally small: it records the non-period columns and the first several period columns for matched rows, rather than storing the entire wide table.

The keyword set covers:

- `营业总收入`
- `营业成本`
- `归母净利润`
- `净利润`
- `扣非净利润`
- `毛利率`
- `净利率`
- `ROE`
- `净资产收益率`
- `经营现金流`
- `经营活动现金流`
- `资产负债率`
- `存货`
- `应收账款`

Replay now reads these enhanced fields and reports which target financial fields have indicator evidence and which remain missing. This remains an offline audit tool only: it does not modify `RealDataConnector`, does not run the pipeline, does not call trading accounts, does not use LLMs, does not generate HTML, and does not produce trading advice.

## 11. Real Data Source Expansion Probe

The probe has been expanded for the next evidence-gathering round before any `RealDataConnector v2.1` work. This stage still only records AkShare interface shapes and replay diagnostics. It does not connect the discovered data to the pipeline.

Expanded categories:

- `valuation`: adds more market snapshot and valuation candidates for `pe_ttm`, `pb`, `ps`, `market_cap`, and `dividend_yield`.
- `business_composition`: retries main-business composition candidates with multiple symbol formats, including plain code, prefixed code, exchange-prefixed code, and known stock name when available.
- `commodity_prices`: probes external resource-price tables for silver, tin, copper, gold, aluminum, molybdenum, cobalt, and rare earth data where available.

All candidates remain defensive:

- every function is checked with `hasattr`;
- every function call is wrapped in `try/except`;
- function-not-found, argument errors, empty tables, and successful tables are all recorded;
- successful payload summaries keep `columns_full`, `head_rows`, `dtypes`, `shape`, and `row_count` where possible;
- list and dict payloads also keep `columns_full`, `head_rows`, and `row_count`.

Replay now adds:

- valuation candidate summary: successful functions, possible PE/PB/PS/market-cap/dividend-yield columns, and still-missing fields;
- business-composition candidate summary: successful functions, candidate segment/revenue/revenue-ratio/gross-margin/period columns, empty table markers, and sample rows;
- commodity-prices summary: successful functions, covered commodities, resource strategy types that could use the data later, and a `connector_ready=false` note.

Recommended local commands:

```bash
python scripts/probe_akshare_real_data.py --codes 002050 000426 300308 002371 601899 --output-dir data/real_probe --limit-rows 5
python scripts/replay_real_data_probe.py --input data/real_probe/probe_601899.json --output data/real_probe/replay_601899.md
```

Boundary: this expansion does not authorize mapping any new valuation, business-composition, or commodity-price field into `RealDataConnector`. Fresh probe JSON should be reviewed first and only then used to design a separate connector patch.

## 12. Copper/Tin Fresh Source Expansion Probe

`ExternalCommodityPriceConnector v1` correctly writes commodity prices to raw JSON and readiness now reports detailed commodity gaps. Real resource-stock diagnostics showed that the current domestic tin and copper sources are stale:

- `futures_spot_price`: latest observed `2024-04-30`
- `futures_spot_price_daily`: latest observed `2021-02-01`

The probe now includes a copper/tin source-expansion matrix for domestic AkShare candidates only. It tries multiple symbol forms for both commodities:

- copper: `CU`, `cu`, `沪铜`, `铜`, `CU0`, `cu0`, `SHFE_CU`
- tin: `SN`, `sn`, `沪锡`, `锡`, `SN0`, `sn0`, `SHFE_SN`

Additional candidate functions include:

- `futures_zh_spot`
- `futures_zh_daily_sina`
- `futures_main_sina`
- `futures_hist_em`
- `futures_hist_daily_em`
- `futures_hist_daily_sina`
- `futures_shfe_daily`
- `get_shfe_daily`
- `futures_spot_price_previous`
- `futures_spot_stock`
- `futures_spot_sys`

Each commodity candidate records `commodity`, `symbol_used`, `symbol_formatter`, `detected_date_columns`, `detected_price_columns`, `latest_date_detected`, `freshness_days`, and `is_fresh_candidate`. Functions that do not exist still record `function_not_found`; argument mismatches are recorded as errors and do not stop the probe.

Replay adds `Copper/Tin Freshness Candidate Summary`. It reports successful copper/tin candidates, latest detected dates, freshness days, candidate price columns, and the best evidence-only candidate for a future connector v1.1 review. If no fresh domestic source is found, keeping the detailed freshness gap is the correct behavior.

Recommended local commands:

```bash
python scripts/probe_akshare_real_data.py --codes 000426 601899 603993 --output-dir data/real_probe --limit-rows 5
python scripts/replay_real_data_probe.py --input data/real_probe/probe_601899.json --output data/real_probe/replay_601899.md
```

Boundary: this stage does not modify `ExternalCommodityPriceConnector`, `RealDataConnector`, readiness, context, or the pipeline. Foreign reference data remains reference-only and is not promoted to domestic primary readiness.
