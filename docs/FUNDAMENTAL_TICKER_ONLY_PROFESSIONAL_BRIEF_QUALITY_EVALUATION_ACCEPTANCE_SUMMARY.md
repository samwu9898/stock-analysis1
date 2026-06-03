# Ticker-only Professional Brief E2E Quality Evaluation Harness Thin Slice Acceptance Summary

## 1. 阶段名称

Ticker-only Professional Brief E2E Quality Evaluation Harness Thin Slice

## 2. Baseline commits

- implementation commit: `bbc53957cef299e1d83c9242f6deab8c9def70cc`
- previous completed stage: Ticker-only Professional Brief Wrapper Integration acceptance summary commit `a13c78d`
- LLM Analyst Renderer Handoff acceptance summary commit `0e3d556`
- Professional Compact Brief Quality acceptance summary commit `e1b63a6`
- rulebook update commit: `02dcc2a`

## 3. 本阶段定位

本阶段是 ticker-only professional brief 的可重复质量评估基线。评估对象是用户前台可见的 `professional_compact_brief`，不是后台 trace，也不是 provider candidate 原始数据。

本阶段不是人工一次性 sample review，不是 fake LLM renderer mode wiring，不是真实 LLM integration，不是 Report V1 integration，不是 HTML renderer，不是 official metric verification，也不是 provider-vs-official reconciliation。本阶段不生成任何 runtime artifact。

本阶段目标是用代码化 harness 评估 ticker-only 输出是否像专业分析师，并为后续 renderer / wrapper 升级提供可重复的前台质量基线。

## 4. 修改文件清单

- `src/fundamental_skill/research_planning/ticker_only_professional_brief_quality_evaluation.py`
- `tests/test_ticker_only_professional_brief_quality_evaluation.py`
- `tests/test_ticker_only_professional_brief_quality_evaluation_safety.py`

## 5. 功能摘要

- 新增 `ticker_only_professional_brief_quality_evaluation_request.v1`
- 新增 `ticker_only_professional_brief_quality_evaluation_result.v1`
- 新增 `ticker_only_professional_brief_quality_sample.v1`
- 新增 `ticker_only_professional_brief_quality_rubric.v1`
- 新增 `ticker_only_professional_brief_quality_scorecard.v1`
- 新增 `ticker_only_professional_brief_quality_issue.v1`
- 新增 `build_ticker_only_professional_brief_quality_evaluation`
- 新增 `build_quality_sample_requests`
- 新增 `evaluate_professional_compact_brief`
- 新增 `build_default_quality_rubric`
- harness 通过 wrapper 的 `input_mode=ticker_only_professional_brief` 路径生成 in-memory `professional_compact_brief`
- harness 使用 fake / injected client，不联网
- harness 不写文件
- harness 不生成 Report V1 / HTML / JSON artifact

## 6. Sample scenarios 摘要

覆盖样本：

- `baseline_600406_like`
- `non_600406_sample`
- `cashflow_supports_profit`
- `profit_stronger_than_cashflow`
- `high_receivables_pressure`
- `high_debt_pressure`
- `sparse_or_missing_metrics`

每个样本都走 wrapper ticker-only professional brief path。每个样本都只评估用户前台 `professional_compact_brief`。evaluation result 不输出 raw provider rows，不输出 `provider_candidate_bundle`，不输出 `candidate_items`，不输出 backend trace。

## 7. Rubric 摘要

rubric 维度：

- `has_overall_fundamental_view`
- `has_business_logic_view`
- `has_financial_interpretation`
- `has_operating_quality_judgment`
- `has_cashflow_profit_match_judgment`
- `has_receivables_or_working_capital_view`
- `has_margin_or_profitability_view`
- `has_balance_sheet_or_debt_view`
- `has_industry_macro_transmission_view`
- `has_core_risk_view`
- `has_conclusion_boundary`
- `has_key_variables`
- `no_engineering_labels`
- `no_backend_trace`
- `no_user_responsibility_shift`
- `no_trading_advice`
- `source_note_is_tushare`

## 8. Scorecard / issue 摘要

- scorecard 按维度给出 `pass` / `warning` / `fail`
- result 顶层包含 `overall_status`
- result 顶层包含 `pass_count` / `warning_count` / `fail_count`
- sample result 包含 `sample_id`、`scenario`、`readiness_status`、`brief_section_keys`、`source_note`、`scorecard`、`issues`
- issue 包含 `issue_id` / `severity` / `message` / `section_id`
- aggregate issues 聚合跨样本问题
- 压力样本出现 warning 是预期行为，不代表 implementation 失败

## 9. 质量评估结果摘要

- `baseline_600406_like`、`non_600406_sample`、`cashflow_supports_profit` 等基础样本通过
- `profit_stronger_than_cashflow` 会标记现金流利润质量压力
- `high_receivables_pressure` 会标记应收 / 营运资本压力
- `high_debt_pressure` 会标记资产负债压力
- `sparse_or_missing_metrics` 会生成 warning，但仍不得出现工程标签、推责表达或交易建议

## 10. Tests 结果

- targeted tests: `84 passed`
- related tests: `393 passed`
- system Python 不可用时使用 Codex bundled Python
- live smoke 未执行，原因是本阶段仅做 in-memory harness，不接真实 LLM / provider / token

## 11. Safety / boundary 摘要

- 未调用真实 LLM API
- 未调用 OpenAI / Claude / Gemini / DeepSeek / Kimi API
- 未读取任何 LLM API key
- 未读取 `tushare_token.txt` / `.env`
- 未输出 token
- 未调用 live provider
- 未写 `output` / `fixtures` / manifest
- 未生成 Report V1 artifact
- 未生成 HTML artifact
- 未生成 Markdown / JSON runtime artifact
- 未生成 `official_metric_fact`
- 未生成 `provider_official_conflict`
- 未做 provider-vs-official reconciliation
- evaluation result 不含 raw provider bundle
- evaluation result 不含 `candidate_items`
- evaluation result 不含 backend trace
- professional preview 无工程标签
- professional preview 无用户责任转移表达
- professional preview 无交易建议
- 英文交易短语和中文交易词继续阻断
- engineering labels 继续阻断

## 12. 明确未触碰的禁区

已确认未触碰：

- true LLM API
- OpenAI / Claude / Gemini / DeepSeek / Kimi API
- LLM key / API key
- Tushare live
- CNInfo live
- fake LLM renderer mode wiring
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
- `output` / `fixtures` / accepted manifest
- `.local_experiments`
- `tushare_token.txt`
- `.env`
- unrelated mojibake files
- unrelated examples file
- cache PDF
- token output
- trading advice output

## 13. 当前剩余 untracked 项

当前剩余 untracked 项为既存项，本阶段未处理：

- `.local_experiments/`
- unrelated mojibake files
- unrelated examples file

## 14. 当前阶段结论

- implementation accepted
- no blocker
- summary doc is docs-only
- 本阶段完成 ticker-only professional brief quality evaluation harness
- 本阶段建立了可重复的前台质量评估基线
- 本阶段让后续 renderer / wrapper 变更可以防止前台质量退化
- 这仍不是真实 LLM analyst
- 这仍不是 full autonomous agent
- 这仍不是 fake LLM renderer mode wiring
- 这仍不是 Report V1 / HTML
- 这仍不是 official metric verification
- 这仍不是 provider-vs-official reconciliation
- 这不包含交易建议

下一阶段应先 reassess。后续可评估 ticker-only fake LLM renderer mode wiring、controlled real LLM local/manual smoke planning、professional brief human review、Report V1 integration planning、official metric extraction / reconciliation。不要直接进入交易建议或无边界 full autonomous agent。
