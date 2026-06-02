# LLM Analyst Renderer Handoff Contract + Fake Renderer Integration Thin Slice Acceptance Summary

## 1. 阶段名称

LLM Analyst Renderer Handoff Contract + Fake Renderer Integration Thin Slice

## 2. Baseline commits

- implementation commit: `a59ba4af0b9e76dd66986d00dd9d0bcc6108f854`
- previous completed stage: Professional Compact Brief Quality / Model Analysis Boundary acceptance summary commit `e1b63a6`
- rulebook update commit: `02dcc2a`

## 3. 本阶段定位

本阶段是 LLM analyst renderer 的 model-facing handoff contract，也是 fake renderer integration thin slice。它不是 true LLM integration，不调用 OpenAI / Claude / Gemini / DeepSeek / Kimi，不是 ticker-only wrapper integration，不是 full autonomous agent，不是 Report V1 integration，不是 HTML renderer，不是 official metric verification，也不是 provider-vs-official reconciliation。

本阶段不生成任何 runtime artifact。核心目标是把未来真实 LLM 分析师能看到什么、必须输出什么、禁止输出什么，用代码和测试锁住。

## 4. 修改文件清单

- `src/fundamental_skill/research_planning/llm_analyst_renderer_handoff.py`
- `src/fundamental_skill/research_planning/professional_compact_brief_quality.py`
- `tests/test_llm_analyst_renderer_handoff.py`
- `tests/test_llm_analyst_renderer_handoff_safety.py`
- `tests/test_professional_compact_brief_quality.py`

## 5. 功能摘要

- 新增 `llm_analyst_handoff_context.v1`
- 新增 `llm_analyst_prompt_contract.v1`
- 新增 `llm_analyst_renderer_output.v1`
- 新增 `fake_llm_analyst_renderer_result.v1`
- 新增 model-facing context sanitizer
- 新增 fake LLM analyst renderer
- 新增 LLM renderer output validator
- 新增 `fake_llm_professional_analyst_renderer` adapter
- 新增 `render_professional_brief_with_fake_llm`
- `professional_compact_brief_quality.py` 最小 wiring 支持 `analyst_renderer="fake_llm"`
- 保持 deterministic renderer path
- 保持 existing injected renderer path
- 不接真实 LLM API
- 不写文件
- 不生成 Report V1 / HTML / JSON artifact

## 6. Model-facing context 摘要

model-facing context 包含：

- `stock_code`
- `ts_code`
- `company_name_hint`
- `periods`
- `latest_period`
- `derived_signals`
- revenue / profit / cashflow / receivables / margin / debt / roe 等 derived signals
- `key_variables`
- `risk_flags`
- `conclusion_boundary`
- `data_source_note=Tushare`
- `model_data_boundary`
- `evidence_confidence_hint`
- `not_for_trading_advice=true`

model-facing context 明确剔除：

- token / `.env` / `tushare_token`
- `source_url` / `page_number` / `snippet` / `sha256` / `cache_path`
- raw provider rows
- raw provider queue
- raw HTTP
- full locator hits
- artifact path
- output path
- fixture path
- accepted manifest path
- `provider_candidate` 原始标签
- `pending_official_verification` 原始标签
- `official_verified_count` 原始调试字段
- provider-vs-official 原始状态
- Report V1 / HTML artifact 字段

## 7. Prompt contract 摘要

prompt contract 规定模型必须输出：

- `overall_view`
- `business_view`
- `financial_view`
- `operating_quality_view`
- `industry_macro_view`
- `risk_view`
- `key_variables`
- `conclusion_boundary`
- `source_note`
- `not_for_trading_advice=true`

prompt contract 明确禁止：

- 买入 / 卖出 / 持有
- 目标价
- 仓位
- 技术信号
- 交易建议
- 用户自行判断 / 用户自行跟踪 / 需要用户结合 / 建议用户
- 待核验 / 数据缺口 / 推理
- provider candidate / pending verification / official verification
- page / snippet / source_url / sha256 / cache_path
- Report V1 artifact / HTML artifact

## 8. Fake LLM renderer 摘要

`fake_llm_analyst_renderer` 是 deterministic，不调用外部 API，不读任何 key，不写文件。它输出 `llm_analyst_renderer_output.v1`，模拟 LLM 风格的专业分析观点。

fake renderer 输出包括总体判断、业务逻辑、财务表现、经营质量、行业/宏观传导、核心风险、关键变量、结论边界。fake output 可转换为 `professional_compact_brief`；fake LLM route 与 deterministic route 输出不同，但满足同一 professional brief contract。

## 9. 与 professional_compact_brief_quality 集成摘要

- `professional_compact_brief_quality` 支持 `analyst_renderer="fake_llm"`
- 新增/支持 `render_professional_compact_brief_with_llm_handoff(context, renderer="fake")`
- 保持 deterministic renderer path
- 保持 callable injected renderer path
- 不破坏 existing quality module
- 不改 wrapper
- 不改 controlled Tushare pilot
- 不做 ticker-only wrapper integration

## 10. Tests 结果

- targeted tests: 144 passed
- related tests: 220 passed
- system python 不可用时使用 Codex bundled Python
- live smoke 未执行，原因：本阶段不接 live provider、不接真实 LLM、不读取 token

## 11. Safety / boundary 摘要

- 未调用真实 LLM API
- 未调用 OpenAI / Claude / Gemini / DeepSeek / Kimi API
- 未读取任何 LLM API key
- 未读取 `tushare_token.txt` / `.env`
- 未输出 token
- 未调用 live provider
- 未写 output / fixtures / manifest
- 未生成 Report V1 artifact
- 未生成 HTML artifact
- 未生成 Markdown / JSON runtime artifact
- 未生成 `official_metric_fact`
- 未生成 `provider_official_conflict`
- 未做 provider-vs-official reconciliation
- 未做 ticker-only wrapper integration
- model-facing context 无 backend trace
- fake renderer 输出无工程标签
- fake renderer 输出无用户责任转移表达
- fake renderer 输出无交易建议
- 英文交易短语和中文交易词继续阻断
- engineering labels 继续阻断

## 12. 明确未触碰的禁区

- true LLM API
- OpenAI / Claude / Gemini / DeepSeek / Kimi API
- LLM key / API key
- Tushare live
- CNInfo live
- ticker-only wrapper integration
- wrapper
- controlled Tushare pilot
- Report V1 builder
- HTML renderer
- PDF download / read / parse
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

- `.local_experiments/`
- unrelated mojibake files
- unrelated examples file

These remaining untracked items are pre-existing and were not handled by this stage.

## 14. 当前阶段结论

- implementation accepted
- no blocker
- summary doc is docs-only
- 本阶段完成 LLM analyst renderer handoff contract
- 本阶段完成 fake renderer integration
- 本阶段把未来真实 LLM 分析师的输入输出边界变成可测试代码
- 这仍不是 true LLM analyst
- 这仍不是 full autonomous agent
- 这仍不是 ticker-only wrapper
- 这仍不是 Report V1 / HTML
- 这仍不是 official metric verification
- 这仍不是 provider-vs-official reconciliation
- 这不包含交易建议
- 下一阶段应先 reassess

后续可评估：

- ticker-only professional brief wrapper integration
- controlled real LLM local/manual smoke planning
- professional brief human review
- Report V1 integration planning
- official metric extraction / reconciliation

不要直接进入交易建议或无边界 full autonomous agent。
