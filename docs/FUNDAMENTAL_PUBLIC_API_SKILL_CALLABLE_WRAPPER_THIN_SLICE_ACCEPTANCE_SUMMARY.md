# Public API / Skill Callable Wrapper Thin Slice Acceptance Summary

## 1. 阶段名称

Public API / Skill Callable Wrapper Thin Slice

## 2. Baseline commits

- implementation commit: `24c7607`
- previous completed stage: Analysis Brief -> Report V1 Compatibility Adapter acceptance summary commit `e218e76`

## 3. 本阶段定位

本阶段是 A股 fundamental skill 的最小 callable wrapper 雏形。它让后续 Codex / skill 可以稳定调用既有 Analysis Brief 链路，但它不是完整 autonomous agent，不是 live provider orchestrator，不是 Report V1 builder，也不是 HTML renderer。

本阶段不生成任何 runtime artifact，只接受 explicit validated inputs。当前 ticker-only request 会 blocked，live ticker orchestration 是后续阶段。

## 4. 修改文件清单

- `src/fundamental_skill/research_planning/a_share_fundamental_skill_wrapper.py`
- `tests/test_a_share_fundamental_skill_wrapper.py`
- `tests/test_a_share_fundamental_skill_wrapper_safety.py`

## 5. 功能摘要

- 新增 `a_share_fundamental_skill_request.v1`
- 新增 `a_share_fundamental_skill_response.v1`
- 新增 `a_share_fundamental_skill_readiness.v1`
- 新增 `a_share_fundamental_compact_response.v1`
- 支持 `input_mode=analysis_brief`
- 支持 `input_mode=orchestration_result`
- 支持 `output_mode=compact_brief`
- 支持 `output_mode=compact_brief_and_report_v1_compatibility_payload`
- 当 `input_mode=analysis_brief` 时，要求 `user_facing_analysis_brief.v1`
- 当 `input_mode=orchestration_result` 时，要求 `live_evidence_research_pack_orchestration_result.v1`，并可选 `locator_result`
- 可调用 existing `build_user_facing_analysis_brief`
- 可调用 existing `build_analysis_brief_report_v1_compatibility_payload`
- 只做内存对象组装
- 不调用 live provider
- 不调用 Report V1
- 不调用 HTML
- 不写任何 artifact

## 6. Readiness / blocked behavior 摘要

- valid analysis_brief request returns ready
- valid orchestration_result request builds analysis brief and returns ready
- ticker-only request returns blocked
- blocked reason: `validated_analysis_input_required`
- blocked message: `current wrapper requires validated analysis inputs; live ticker orchestration is later stage`
- `allow_network=true` rejected
- `allow_file_writes=true` rejected
- unsupported `input_mode` rejected
- unsupported `output_mode` rejected
- `readiness.has_report_v1_artifact=false`
- `readiness.has_html_artifact=false`
- `readiness.has_trading_advice=false`

## 7. Compact response 摘要

`compact_response` 只从 `user_visible_sections` 和 existing `markdown_preview` 组装。

它包含：

- subject summary
- section summaries
- `labels_used`
- tracking indicators
- `cannot_conclude_yet`

它不包含：

- `backend_grounding_summary`
- `page_number`
- `snippet`
- `source_url`
- `sha256`
- `cache_path`
- provider queue / anchor map / locator hits / official metadata
- Report V1 artifact path / HTML artifact path

## 8. Compatibility payload 摘要

- `output_mode=compact_brief_and_report_v1_compatibility_payload` 时，可返回 `analysis_brief_report_v1_compatibility_payload.v1`
- `output_mode=compact_brief` 时不返回 compatibility payload
- compatibility payload 仍是 in-memory context
- 它不是 Report V1 artifact
- 不调用 Report V1 builder
- 不生成 Markdown / HTML / JSON report

## 9. Tests 结果

- targeted tests: 97 passed
- related tests: 178 passed
- system python 不可用时使用 Codex bundled Python

## 10. Manual smoke 摘要

- manual smoke 已执行
- `readiness.status=ready`
- `input_mode=analysis_brief`
- `output_mode=compact_brief_and_report_v1_compatibility_payload`
- compact_response section count=9
- compatibility payload present=true
- backend_trace_leaked=false
- forbidden markers present=false
- 未输出 token
- 未写文件

## 11. 明确未触碰的禁区

已确认未触碰：

- Research Report V1 builder
- HTML renderer
- Tushare provider
- CNInfo live
- `user_facing_analysis_brief.py`
- `analysis_brief_report_v1_adapter.py`
- official artifact evidence locator
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
- Report V1 artifact
- HTML artifact
- Markdown artifact
- JSON report artifact
- 买入 / 卖出 / 持有
- 目标价
- 仓位
- 技术信号

## 12. 当前剩余 untracked 项

当前工作区仍有既存 untracked 项，本阶段不处理：

- `.local_experiments/`
- `docs/PROJECT_DEVELOPMENT_RULEBOOK.md`
- `output/`
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

## 13. 当前阶段结论

- implementation accepted
- no blocker
- summary doc is docs-only
- 项目已拥有最小 callable wrapper 雏形
- 这更接近“一句话调用基本面 skill”的最终目标
- 当前 wrapper 仍要求 explicit validated inputs
- ticker-only live orchestration 仍是后续阶段
- 这不是 full autonomous agent
- 这不是 live data orchestrator
- 这不是 Report V1 integration
- 这不是 HTML rendering
- 这没有 `official_metric_fact`
- 这没有 provider-vs-official reconciliation
- 这不包含交易建议
- 下一阶段应先 reassess
- 后续可以评估 Controlled Real Tushare -> Analysis Brief E2E Pilot
- 后续可以评估 rulebook docs-only commit
- 后续可以评估 Report V1 integration planning
- 后续可以评估 Very Small Metric Evidence Extraction
- 不要直接进入 Report V1 artifact generation
- 不要直接进入 HTML rendering
- 不要直接进入交易建议
- 不要继续无目的扩后台基础设施
