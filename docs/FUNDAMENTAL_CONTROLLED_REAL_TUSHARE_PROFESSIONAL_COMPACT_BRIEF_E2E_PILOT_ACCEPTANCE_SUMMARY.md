# Controlled Real Tushare to Professional Analyst Compact Brief E2E Pilot Acceptance Summary

## 1. 阶段名称

Controlled Real Tushare -> Professional Analyst Compact Brief E2E Pilot

## 2. Baseline commits

- implementation commit: `d7f6cdf8585e771e1930490615c16f66b11b2e3f`
- previous completed stage: Public API / Skill Callable Wrapper acceptance summary commit `4de7f33`
- rulebook update commit: `02dcc2a`

## 3. 本阶段定位

本阶段是受控真实 Tushare 到专业分析师 compact brief 的 E2E pilot。它证明真实 Tushare provider candidate 可以安全进入 professional compact brief，并且前台输出是 `professional_analyst_compact_brief`，不是工程状态列表。

本阶段不是 full autonomous agent，不是 Report V1 integration，不是 HTML renderer，不是 official metric verification，也不是 provider-vs-official reconciliation。它不生成任何 runtime artifact，不接正式 Report V1，不输出 HTML，不产出 official metric fact，也不做 provider 与 official 口径的一致性结论。

## 4. 修改文件清单

implementation commit 只提交了以下 3 个 expected files：

- `src/fundamental_skill/research_planning/controlled_real_tushare_professional_compact_brief_pilot.py`
- `tests/test_controlled_real_tushare_professional_compact_brief_pilot.py`
- `tests/test_controlled_real_tushare_professional_compact_brief_pilot_safety.py`

## 5. 功能摘要

本阶段新增并验证以下 schema / 数据结构：

- `controlled_real_tushare_professional_compact_brief_request.v1`
- `controlled_real_tushare_professional_compact_brief_result.v1`
- `controlled_real_tushare_provider_candidate_bundle.v1`
- `professional_analyst_compact_brief.v1`
- `controlled_real_tushare_professional_e2e_readiness.v1`

实现支持 `fake` / `injected` / `env_live` client mode。测试默认使用 fake 或 injected client，不走真实网络。`env_live` 只允许在 `allow_network=true` 时使用，并且只从 `TUSHARE_TOKEN` 环境变量读取凭证；它不读取 `tushare_token.txt`，也不读取 `.env`。

真实 Tushare rows 只进入内部 `provider_candidate_bundle`。内部证据状态保持为 `provider_candidate` / `pending_official_verification`，`official_verified_count=0`。随后数据通过 existing internal analysis chain 和 wrapper，生成 `professional_analyst_compact_brief`。本阶段不写文件，不生成 Report V1 / HTML / JSON artifact。

## 6. Professional front-end output 摘要

前台 `professional_compact_brief` 默认不展示工程标签，不展示“待核验 / 数据缺口 / 推理”，不展示 `provider_candidate` / `pending_official_verification` / `official verification`，也不展示 provider 与官方口径一致性。

前台输出不把判断责任抛给用户，不写“用户自行判断 / 自行跟踪 / 需要用户结合 / 建议用户”。输出保持 professional analyst view，包括：

- `overall_view`
- `business_view`
- `financial_view`
- `operating_quality_view`
- `industry_macro_view`
- `risk_view`
- `key_variables`
- `conclusion_boundary`
- `source_note`

`source_note=数据来源：Tushare。`

本阶段不写“及公开披露信息”，因为本阶段未接入 official disclosure。

## 7. Token / network / live smoke 摘要

manual live smoke 使用指定 Python：

- `D:\anaconda\envs\ashare-copilot\python.exe`
- `TUSHARE_TOKEN=set`
- `tushare=installed`
- `yaml=installed`
- provider import OK

manual live smoke 已执行，真实网络 smoke success：

- `readiness.status=ready`
- `provider_candidate_count=19`
- `official_verified_count=0`
- `professional_compact_brief` 9 个 section 全部生成
- `source_note=数据来源：Tushare。`
- `forbidden_user_visible_engineering_labels_present=false`
- `trading_advice_present=false`
- `backend_trace_present=false`
- `token_present_in_output=false`
- `files_written=false`

本阶段确认未输出 token，未输出原始 Tushare rows，未写 `output` / `fixtures` / manifest。

## 8. Tests 结果

- targeted tests: 122 passed
- related tests: 176 passed
- system python 不可用时使用 Codex bundled Python
- manual live smoke 使用指定 Anaconda Python

## 9. Safety / boundary 摘要

`professional_compact_brief` 不展示 backend trace，不展示 `page_number` / `snippet` / `source_url` / `sha256` / `cache_path`，不展示 official verification / reconciliation。

本阶段不生成：

- `official_metric_fact`
- `provider_official_conflict`
- provider-vs-official reconciliation
- Report V1 artifact
- HTML artifact
- Markdown / JSON runtime artifact
- 交易建议
- 买入 / 卖出 / 持有
- 目标价
- 仓位
- 技术信号

英文交易短语 `buy recommendation` / `sell signal` / `hold position` 等已被阻断；`threshold` / `shareholder` / `withholding` 不误杀。

## 10. 明确未触碰的禁区

本阶段明确未触碰：

- Report V1 builder
- HTML renderer
- official artifact evidence locator
- CNInfo live
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

## 11. 当前剩余 untracked 项

当前工作区仍有既存 untracked 项，本阶段不处理：

- `.local_experiments/`
- unrelated mojibake files
- unrelated examples file

## 12. 当前阶段结论

implementation accepted，no blocker。本文档是 docs-only acceptance summary。

本阶段首次证明真实 Tushare provider candidate 可以安全进入 professional analyst compact brief；用户前台输出是 professional analyst view，而不是工程状态汇报。

这仍不是 full autonomous agent，仍不是 Report V1 / HTML，仍不是 official metric verification，仍不是 provider-vs-official reconciliation，也不包含交易建议。

下一阶段应先 reassess。后续可评估：

- professional compact brief quality iteration
- ticker-only wrapper integration planning
- Report V1 integration planning
- official metric extraction / reconciliation

不要直接进入交易建议或无边界 full autonomous agent。
