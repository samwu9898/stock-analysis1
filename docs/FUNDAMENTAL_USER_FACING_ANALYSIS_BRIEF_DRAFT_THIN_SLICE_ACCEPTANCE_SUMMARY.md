# User-facing Analysis Brief Draft Thin Slice Acceptance Summary

## 1. 阶段名称

User-facing Analysis Brief Draft Thin Slice

## 2. Baseline commits

- implementation commit: `be197e59ebc020999c7504a035f7714de7e68868`
- previous completed stage: Official Artifact Evidence Locator acceptance summary commit `0dd3a23`

## 3. 本阶段定位

本阶段是 **New Evidence Chain -> Analysis Brief Bridge Draft**。

本阶段不是 Research Report V1 替代品，不是 HTML presentation layer，不是 formal Research Pack，不重新实现旧 Report V1，也不重新实现 HTML renderer。后续仍需单独进行 Research Report V1 / HTML Reuse Audit 或 Bridge Integration Reassessment。

## 4. 本阶段目标

- 将 `live_evidence_research_pack_orchestration_result.v1` 转换为用户可读 analysis brief draft。
- 可选使用 `official_artifact_evidence_locator.v1`。
- 输出 `user_facing_analysis_brief.v1`。
- 把后台证据状态转成前台分析标签。
- 只展示用户关心的分析层内容。
- 不展示 page / snippet / source_url / sha256 / cache_path。
- `backend_grounding_summary` 默认不可见。
- 最高原则：证据在后台，分析在前台。

## 5. 修改文件清单

- `src/fundamental_skill/research_planning/user_facing_analysis_brief.py`
- `tests/test_user_facing_analysis_brief.py`
- `tests/test_user_facing_analysis_brief_safety.py`

## 6. 功能摘要

- 新增 `user_facing_analysis_brief.v1`。
- 新增 `user_facing_analysis_brief_section.v1`。
- 新增 `analysis_confidence_label.v1`。
- 新增 `backend_grounding_summary.v1`。
- 输入必须包含 `orchestration_result`。
- 可选 `locator_result`。
- 调用 existing `validate_live_evidence_research_pack_orchestration_result`。
- 调用 existing `validate_official_artifact_evidence_locator`。
- 拒绝 raw provider。
- 拒绝 raw HTTP。
- 拒绝 PDF bytes。
- 拒绝 arbitrary URL。
- 拒绝 `allow_network=true`。
- 不读取本地文件。
- 不调用 live modules。
- 不生成 upstream components。

## 7. User-visible section 摘要

固定 9 个 section：

- `subject_summary`
- `current_judgment_boundary`
- `business_logic`
- `financial_interpretation`
- `industry_macro_context`
- `risk_points`
- `data_gaps_that_matter`
- `tracking_indicators`
- `cannot_conclude_yet`

前台 section 只表达分析层内容，不展示 locator/page/snippet/source trace，不展示 sha256/source_url/cache_path，不展示 provider queue / anchor map raw detail。

- `current_judgment_boundary` 说明当前能形成基本面分析草稿，但官方指标核验尚未完成。
- `business_logic` 不推断主营业务。
- `financial_interpretation` 把 provider candidate 标成待核验。
- `industry_macro_context` 只保留框架和待判断问题。
- `risk_points` 只表达分析风险 / 数据风险 / 核验风险。
- `tracking_indicators` 只列名称，不给交易触发条件。
- `cannot_conclude_yet` 明确不能确认官方指标值、不能确认 provider-official 一致、不能生成正式报告或交易用途结论。

## 8. Analysis label 摘要

支持标签：

- 较可靠
- 待核验
- 数据缺口
- 推理
- 不可判断

标签规则：

- 较可靠只有 `official_verified_count > 0` 才可作为实际 section/point 标签。
- `provider_candidate` -> 待核验。
- `data_gap` -> 数据缺口。
- framework/question -> 推理。
- blocked/cannot_conclude -> 不可判断。
- `artifact_cached` / `locator_available` 不升级为 `official_verified`。

## 9. Backend grounding summary 摘要

- `backend_grounding_summary.default_visible=false`。
- 只包含 availability/count/status summary。
- 可以包含 `audit_trace_available`、`official_anchor_available`、`artifact_cached_available`、`locator_available`、`provider_candidate_present`、`pending_verification_count`、`official_verified_count`、`data_gap_count`。
- 不包含 `page_number`。
- 不包含 `snippet`。
- 不包含 `source_url`。
- 不包含 `sha256`。
- 不包含 `cache_path`。
- 不包含 full locator hits。
- 不包含 full provider queue。
- 不包含 full anchor map。
- 不包含 full official metadata。

## 10. Markdown preview 摘要

- `markdown_preview` 只从 `user_visible_sections` 生成。
- 包含分析标签。
- 包含 `current_judgment_boundary`。
- 包含 `data_gaps_that_matter`。
- 包含 `tracking_indicators`。
- 包含 `cannot_conclude_yet`。
- 不包含 `backend_grounding_summary`。
- 不包含 page_number / snippet / source_url / sha256 / cache_path。
- 不包含 Report V1 / formal report。
- 不包含买卖持 / 目标价 / 仓位 / 技术信号。

## 11. Tests 结果

- targeted tests: 79 passed。
- related tests: 241 passed。
- system python 不可用时使用 Codex bundled Python。

## 12. Manual smoke 摘要

- manual smoke 已执行。
- section ids 全部固定。
- labels used: 待核验 / 推理 / 不可判断 / 数据缺口。
- `backend_grounding_summary.default_visible=false`。
- locator details leaked=false。
- forbidden markers present=false。
- 未输出 token。
- 未写文件。

## 13. 明确未触碰的禁区

已确认未触碰：

- Research Report V1 generator
- HTML renderer
- `official_artifact_evidence_locator.py`
- `live_evidence_research_pack_orchestration_entry.py`
- `live_evidence_aware_research_pack_vertical_slice.py`
- `evidence_aware_research_pack_scaffold.py`
- `ticker_research_context_skeleton.py`
- `official_artifact_cache_acquisition.py`
- `real_official_metadata_anchor_handoff.py`
- `provider_metric_official_anchor.py`
- `provider_candidate_verification_queue.py`
- Tushare provider module
- `schemas.py` / `validators.py`
- `__init__.py`
- `docs/PROJECT_DEVELOPMENT_RULEBOOK.md`
- accepted manifest
- output baseline
- fixtures
- output 读取/写入
- token / `.env` / `tushare_token` 文件读取
- `.local_experiments`
- unrelated mojibake files
- unrelated examples file
- cache PDF file read
- PDF bytes read
- PDF parser
- text extraction
- table extraction
- metric extraction
- `official_metric_fact`
- `provider_official_conflict`
- provider-vs-official reconciliation
- 买入 / 卖出 / 持有
- 目标价
- 仓位
- 技术信号

## 14. 当前剩余 untracked 项

- `.local_experiments/`
- `docs/PROJECT_DEVELOPMENT_RULEBOOK.md`
- `output/`
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

这些剩余项不是本阶段 acceptance summary 的一部分，本阶段未处理。

## 15. 当前阶段结论

- implementation accepted。
- no blocker。
- summary doc is docs-only。
- 项目已完成 New Evidence Chain -> Analysis Brief Bridge Draft。
- 这增强了用户前台分析价值。
- 这不是旧 Research Report V1 / HTML 替代品。
- 这仍然不是完整 autonomous agent。
- 这仍然不是 formal Research Pack。
- 这仍然不是 Report V1。
- 这仍然没有 `official_metric_fact`。
- 这仍然没有 provider-vs-official reconciliation。
- 这仍然不包含交易建议。
- 下一阶段应先 reassess。
- 建议下一步做 Research Report V1 / HTML Reuse Audit + Bridge Integration Reassessment。
- 或 Public API / Skill Callable Wrapper，但不得绕过复用审查。
- 不要直接进入 Report V1 或交易建议。
- 不要继续无目的扩后台基础设施。
