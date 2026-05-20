# Real Data Smoke Test

## 1. 测试环境

- Date: 2026-05-17
- Workspace: `C:\Users\wujia\a_share_copilot\stock-analysis1`
- Python executable: `C:\Users\wujia\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- Python version: `3.12.13`
- AkShare version: `1.18.60`
- Command pattern:

```bash
python -m src.fundamental_skill.real_stock_runner --code <code> --output output/fundamental_<code>.json --force-refresh
```

当前 shell 中 `python`、`py` 和项目 `.venv` 不可用，因此实际使用 bundled Python 绝对路径运行。

## 2. AkShare 可用性

初始检查时，bundled Python 未安装 `akshare`。随后安装 `akshare==1.18.60`，import 检查通过。

真实接口访问阶段，AkShare 目标域访问被当前环境的 socket 权限阻断。典型错误：

- `WinError 10013`: An attempt was made to access a socket in a way forbidden by its access permissions.
- `curl: (7) Failed to connect to search-api-web.eastmoney.com port 443`

因此本次 smoke test 验证到：RealDataConnector 和 pipeline 不崩溃，能够记录 block 级失败并输出 `FundamentalAnalysisResult`；但当前环境未能取得真实数据字段。

## 3. 股票运行结果

| code | stock_name | strategy_type | status | confidence | score | risks | failed_blocks | output |
|---|---|---|---|---|---:|---:|---|---|
| 002050 | null | unknown | insufficient_data | low | 29 | 4 | basic_info, financial_indicator, valuation, business_composition, news | `output/fundamental_002050.json` |
| 000426 | null | unknown | insufficient_data | low | 29 | 4 | basic_info, financial_indicator, valuation, business_composition, news | `output/fundamental_000426.json` |
| 300308 | null | unknown | insufficient_data | low | 29 | 4 | basic_info, financial_indicator, valuation, business_composition, news | `output/fundamental_300308.json` |
| 002371 | null | unknown | insufficient_data | low | 29 | 4 | basic_info, financial_indicator, valuation, business_composition, news | `output/fundamental_002371.json` |
| 601899 | null | unknown | insufficient_data | low | 29 | 4 | basic_info, financial_indicator, valuation, business_composition, news | `output/fundamental_601899.json` |

对应 raw JSON 文件：

- `output/raw_002050.json`
- `output/raw_000426.json`
- `output/raw_300308.json`
- `output/raw_002371.json`
- `output/raw_601899.json`

## 4. 最容易失败的数据块

本轮所有数据块均失败，原因是外部连接被当前环境阻断，而不是单个 AkShare 接口字段不匹配。

失败目标包括：

- `push2.eastmoney.com`: basic info
- `money.finance.sina.com.cn`: financial indicator
- `82.push2.eastmoney.com`: valuation
- `emweb.securities.eastmoney.com`: business composition
- `search-api-web.eastmoney.com`: news

## 5. 缺失严重字段

五只股票最终共同缺失：

- `basic_info.stock_name`
- `basic_info.industry`
- `basic_info.main_business`
- `basic_info.listing_date`
- `financial_metrics`
- `valuation_metrics`
- `business_composition`
- `business_composition.segments`
- `latest_news`
- `data_cutoff`

由于核心字段缺失，分类全部为 `unknown`，最终状态为 `insufficient_data`，这是符合 pipeline 保守边界的结果。

## 6. 是否需要 Real Data Connector v2

需要，但不应在本轮 smoke test 中大改。v1 已验证：

- AkShare 缺失或失败不会使 CLI 崩溃。
- 每个 block 的失败被写入 `fetch_status`。
- 错误信息被写入 `errors`.
- raw JSON 可以交给 `FundamentalSkillPipeline`。
- 最终输出仍通过 validator，不输出交易建议。

v2 应重点解决真实环境可用性和数据源 fallback，而不是改变 pipeline。

## 7. 下一步建议

1. 在允许外部网络访问的本机环境重新运行相同命令，确认 AkShare 接口真实返回结构。
2. 为 `basic_info` 增加 fallback 接口，优先保证 `stock_name`、`industry`、`main_business` 可用。
3. 为 `valuation` 避免全市场行情一次性拉取失败，增加单股行情 fallback。
4. 为财务指标增加东方财富/新浪/财报摘要多接口 fallback。
5. 增加字段级 source trace，记录每个字段来自哪个 AkShare 接口和原始列名。
6. 保留当前 fail-soft 行为：真实数据不完整时降级输出，而不是中断。

## 8. 测试回归

- `python -m pytest tests/test_regression_suite.py`: 13 passed.
- `python scripts/run_regression_suite.py`: passed=13 failed=0 total=13.
- `python -m pytest tests`: 121 passed.
