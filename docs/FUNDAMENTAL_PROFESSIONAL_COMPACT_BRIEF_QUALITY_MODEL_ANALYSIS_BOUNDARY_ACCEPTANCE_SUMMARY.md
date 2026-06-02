# Professional Compact Brief Quality / Model Analysis Boundary Thin Slice Acceptance Summary

## 1. 阶段名称

Professional Compact Brief Quality / Model Analysis Boundary Thin Slice

## 2. Baseline commits

- implementation commit: `802983a07e89c41e466ffbe1c4fb8ebe7366fbe9`
- previous completed stage: Controlled Real Tushare -> Professional Analyst Compact Brief E2E Pilot acceptance summary commit `d592c72`
- rulebook update commit: `02dcc2a`

## 3. 本阶段定位

本阶段是 professional compact brief 分析质量升级，核心是建立 analyst context / analyst renderer boundary，让 professional compact brief 不再只是模板句式，而是由 structured analyst context 驱动。

本阶段明确不是 full autonomous agent，不是真实 LLM integration，不是 Report V1 integration，不是 HTML renderer，不是 official metric verification，也不是 provider-vs-official reconciliation。本阶段不生成任何 runtime artifact。

## 4. 修改文件清单

- `src/fundamental_skill/research_planning/professional_compact_brief_quality.py`
- `src/fundamental_skill/research_planning/controlled_real_tushare_professional_compact_brief_pilot.py`
- `tests/test_professional_compact_brief_quality.py`
- `tests/test_professional_compact_brief_quality_safety.py`
- `tests/test_controlled_real_tushare_professional_compact_brief_pilot.py`

## 5. 功能摘要

本阶段新增 `professional_analyst_context.v1`、`professional_analyst_financial_signal.v1`、`professional_analyst_quality_signal.v1`、`professional_analyst_industry_macro_signal.v1`、`professional_analyst_renderer_output.v1`。

本阶段新增 deterministic analyst renderer，并支持 injected `analyst_renderer`。renderer 只接收 sanitized `professional_analyst_context`，renderer output 再转换成 `professional_analyst_compact_brief.v1`。existing controlled Tushare pilot 只通过最小 wiring 调用 quality module。

本阶段不接真实 LLM API，不写文件，不生成 Report V1 / HTML / JSON artifact。

## 6. Analyst context 摘要

`professional_analyst_context.v1` 整理了以下分析变量：

- `revenue_present` / `revenue_direction_hint`
- `profit_present` / `profit_direction_hint`
- `revenue_profit_consistency`
- `operating_cashflow_present`
- `profit_cashflow_match`
- `receivables_present`
- `receivables_pressure_hint`
- `margin_present`
- `margin_quality_hint`
- `debt_ratio_present`
- `balance_sheet_pressure_hint`
- `roe_present`
- `capital_efficiency_hint`
- `inventory_present`
- `turnover_or_working_capital_hint`
- `key_variables`
- `risk_flags`
- `conclusion_boundary`

## 7. 分析质量提升摘要

Professional compact brief 不再只拼模板。财务侧判断收入利润同步性、利润率、资产负债、ROE；经营侧判断现金流利润匹配、应收压力、存货和周转效率；行业宏观侧强调行业变量必须传导到订单、交付、回款和利润率。

当现金流支撑利润时，brief 输出更正面的经营质量判断；当利润强于现金流时，brief 输出经营质量需要打折；当应收扩张时，brief 输出利润质量削弱风险。整体输出更明确的经营质量、财务表现、风险边界和关键变量。

## 8. Renderer boundary 摘要

核心边界函数是 `render_professional_compact_brief_from_context(context, analyst_renderer=None)`。默认使用 deterministic renderer，也支持 injected renderer。

Injected renderer 只接收 sanitized context。renderer 不允许输出工程标签，不允许输出 token/backend trace，不允许输出买卖持、目标价、仓位、技术信号。当前不接真实 LLM，后续可作为大模型 analyst renderer 接入边界。

## 9. User-facing output 边界

Professional output 不展示 `provider_candidate` / pending verification / official verification，不展示“待核验 / 数据缺口 / 推理”，不展示 page/snippet/source_url/sha256/cache_path。

Professional output 不写“用户自行判断 / 自行跟踪 / 需要用户 / 建议用户”，只输出专业分析观点。仍不输出买入/卖出/持有，仍不输出目标价/仓位/技术信号，仍不输出交易建议。

## 10. Tests 结果

- targeted tests: 200 passed
- related tests: 176 passed
- system python 不可用时使用 Codex bundled Python
- live smoke 未执行，原因：本阶段只改内存 context / renderer boundary，不影响 live path，且要求不读取 token

## 11. Safety / boundary 摘要

本阶段未读取 `tushare_token.txt` / `.env`，未输出 token，未调用 live provider，未调用真实 LLM API，未写 output / fixtures / manifest，未生成 Report V1 artifact，未生成 HTML artifact，未生成 Markdown/JSON runtime artifact。

本阶段未生成 `official_metric_fact`，未生成 `provider_official_conflict`，未做 provider-vs-official reconciliation，未输出交易建议。英文交易短语和中文交易词继续阻断，engineering labels 继续阻断，user responsibility-shifting phrases 继续阻断。

## 12. 明确未触碰的禁区

已确认未触碰：

- true LLM API
- OpenAI / Claude / Gemini / DeepSeek / Kimi API
- Report V1 builder
- HTML renderer
- CNInfo live
- PDF download/read/parse
- table extraction
- metric extraction as official fact
- `official_metric_fact`
- `provider_official_conflict`
- provider-vs-official reconciliation
- output / fixtures / accepted manifest
- `.local_experiments`
- `tushare_token.txt`
- `.env`
- unrelated mojibake files
- unrelated examples file
- cache PDF
- token output
- trading advice output

## 13. 当前剩余 untracked 项

当前剩余 untracked 项为既存项，本阶段不得处理：

- `.local_experiments/`
- unrelated mojibake files
- unrelated examples file

## 14. 当前阶段结论

Implementation accepted。No blocker。Summary doc is docs-only。

本阶段完成 professional compact brief quality boundary，把 brief 从模板表达升级为 analyst context + renderer boundary。这仍不是 true LLM analyst，仍不是 full autonomous agent，仍不是 Report V1 / HTML，仍不是 official metric verification，仍不是 provider-vs-official reconciliation，也不包含交易建议。

下一阶段应先 reassess。后续可评估 ticker-only wrapper integration planning、real LLM analyst renderer planning、professional brief quality human review、Report V1 integration planning、official metric extraction / reconciliation。不要直接进入交易建议或无边界 full autonomous agent。
