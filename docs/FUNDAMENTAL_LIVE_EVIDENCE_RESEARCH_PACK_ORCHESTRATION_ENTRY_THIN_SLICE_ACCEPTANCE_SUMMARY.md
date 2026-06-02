# Live Evidence Research Pack Orchestration Entry Thin Slice Acceptance Summary

## 1. 阶段名称

Live Evidence Research Pack Orchestration Entry Thin Slice

## 2. Baseline Commits

- implementation commit: `0e38c0c`
- previous completed stage: 600406 Live Evidence-aware Research Pack Vertical Slice acceptance summary commit `3ede9da`

## 3. 本阶段目标

本阶段为已有 validated components 提供稳定、可调用、可演示的 orchestration entry。

- 输入为 `live_evidence_research_pack_orchestration_request.v1`
- 输出为 `live_evidence_research_pack_orchestration_result.v1`
- result 包含 readiness、vertical_slice、markdown_preview、evidence_status_rollup、source_component_summary
- 本阶段不是完整 autonomous agent
- 不调用 live provider
- 不调用 live CNInfo
- 不下载或读取 PDF
- 不接 Report V1
- 不生成正式研报
- 不生成投资建议

## 4. 修改文件清单

- `src/fundamental_skill/research_planning/live_evidence_research_pack_orchestration_entry.py`
- `tests/test_live_evidence_research_pack_orchestration_entry.py`
- `tests/test_live_evidence_research_pack_orchestration_entry_safety.py`

## 5. 功能摘要

- 新增 `live_evidence_research_pack_orchestration_request.v1`
- 新增 `live_evidence_research_pack_orchestration_result.v1`
- 新增 `live_evidence_research_pack_orchestration_readiness.v1`
- `request.components` 必须是 dict
- components 至少必须包含 `evidence_aware_research_pack_scaffold`
- 可选接收 `ticker_research_context_skeleton`
- 可选接收 `provider_metric_official_anchor_map`
- 可选接收 `real_official_metadata_anchor_handoff_result`
- 可选接收 `official_disclosure_artifact_cache`
- 调用 existing `build_live_evidence_aware_research_pack_vertical_slice`
- 调用 existing `validate_live_evidence_aware_research_pack_vertical_slice`
- `markdown_preview` 只透传 `vertical_slice.user_readable_markdown_preview`
- 不重新生成自由长文
- 不自行构造上游组件
- 不读取本地文件
- 不调用 live modules

## 6. Readiness 行为摘要

- valid components 且 vertical slice / markdown preview 生成成功时 `readiness.status=ready`
- missing required component 时 `readiness.status=blocked`
- missing `evidence_aware_research_pack_scaffold` 时 blocked
- identity mismatch 时 blocked
- invalid schema / forbidden marker / raw inputs 走 fail-closed controlled error
- blocked result 不包含 `vertical_slice`
- blocked result 不包含 `markdown_preview`
- blocked result 不包含 `evidence_status_rollup`
- ready result 必须包含 `vertical_slice`、`markdown_preview`、`evidence_status_rollup`
- `has_formal_research_report=false`
- `has_trading_advice=false`

## 7. Input Contract / Safety 摘要

- request 必须是 dict
- `request.components` 必须是 dict
- `allow_network=true` rejected
- `requested_output` 只允许 `vertical_slice_and_markdown_preview`
- 拒绝 raw Tushare provider result
- 拒绝 raw provider queue
- 拒绝 raw HTTP response
- 拒绝 PDF bytes
- 拒绝 cache file content
- 拒绝 arbitrary URL
- 不接受 live provider / live Tushare / live CNInfo
- 不接受 output / fixture / manifest write intent
- 不接受 Report V1 / formal report intent
- 不接受 trading advice / target price / position / technical signal intent

## 8. Identity Consistency 摘要

- `request.stock_code` 与 `vertical_slice.stock_code` 不一致时 blocked
- `request.ts_code` 与 `vertical_slice.ts_code` 不一致时 blocked
- `company_name_hint` 非空明显冲突时 blocked
- 600406 只作为 sample
- production 逻辑保持 ticker-agnostic
- generic ticker sample 可通过

## 9. Tests 结果

- targeted tests: 72 passed
- related tests: 208 passed
- system python 不可用时使用 Codex bundled Python

## 10. Manual Orchestration Smoke 摘要

- manual orchestration smoke 已执行
- 不联网
- 不调用 live provider
- 不读取 output / fixtures / manifest
- 不读取 cache PDF
- `readiness.status=ready`
- vertical slice schema 为 `live_evidence_aware_research_pack_vertical_slice.v1`
- section count = 9
- evidence rollup 正常
- forbidden markers present=false
- 未输出 token
- 未写文件

## 11. 明确未触碰的禁区

- `live_evidence_aware_research_pack_vertical_slice.py`
- `evidence_aware_research_pack_scaffold.py`
- `ticker_research_context_skeleton.py`
- `official_artifact_cache_acquisition.py`
- `real_official_metadata_anchor_handoff.py`
- `provider_metric_official_anchor.py`
- `provider_candidate_verification_queue.py`
- Tushare provider module
- Research Report V1 generator
- HTML renderer
- Dashboard
- `schemas.py` / `validators.py`
- `__init__.py`
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

## 12. 当前剩余 Untracked 项

- `.local_experiments/`
- `output/`
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

## 13. 当前阶段结论

- implementation accepted
- no blocker
- summary doc is docs-only
- 项目已拥有稳定、可调用的 live evidence research pack orchestration entry 雏形
- 它仍然不是完整 autonomous agent
- 它仍然不是正式 Research Pack
- 它仍然不是 Report V1
- 它仍然没有 `official_metric_fact`
- 它仍然没有 provider-vs-official reconciliation
- 它仍然不包含交易建议
- 下一阶段应先 reassess
- 后续建议优先做 ticker-generalization smoke，验证不是 600406 专用
- 或做极小 official evidence extraction slice
- 不要继续无目的扩基础设施
- 不要直接进入 Report V1 或交易建议
