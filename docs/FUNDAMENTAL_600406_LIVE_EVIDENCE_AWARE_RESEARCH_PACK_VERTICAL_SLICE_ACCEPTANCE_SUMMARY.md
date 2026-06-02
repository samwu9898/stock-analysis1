# 600406 Live Evidence-aware Research Pack Vertical Slice Acceptance Summary

## 1. 阶段名称

600406 Live Evidence-aware Research Pack Vertical Slice

## 2. Baseline commits

- implementation commit: `d9fd5c9d828332d7962f4941fea9f0dc0e55c66b`
- previous completed stage: Official Artifact Download / Cache Acquisition acceptance summary commit `4c267d5`

## 3. 本阶段目标

- 将现有真实链路结果组装成用户可读的 research pack vertical slice。
- 输入是显式传入的 validated components。
- 输出 `live_evidence_aware_research_pack_vertical_slice.v1`。
- 这是产品价值验证。
- 不是正式 Research Pack。
- 不是 Report V1。
- 不生成投资建议。
- 不生成买入 / 卖出 / 持有。
- 不生成目标价。
- 不生成仓位。
- 不生成技术信号。
- 不把 candidate / anchor / artifact cached 状态升级为 `official_verified`。

## 4. 修改文件清单

- `src/fundamental_skill/research_planning/live_evidence_aware_research_pack_vertical_slice.py`
- `tests/test_live_evidence_aware_research_pack_vertical_slice.py`
- `tests/test_live_evidence_aware_research_pack_vertical_slice_safety.py`

## 5. 功能摘要

- 新增 `live_evidence_aware_research_pack_vertical_slice.v1`。
- 新增 `live_evidence_research_pack_section.v1`。
- 新增 `live_evidence_status_rollup.v1`。
- 输入 `components` 必须包含 `evidence_aware_research_pack_scaffold`。
- 可选接收 `ticker_research_context_skeleton`、`provider_metric_official_anchor_map`、`real_official_metadata_anchor_handoff_result`、`official_disclosure_artifact_cache`。
- 对输入组件调用 existing validators。
- 拒绝 raw Tushare provider result。
- 拒绝 raw provider queue。
- 拒绝 raw HTTP response。
- 拒绝 PDF bytes。
- 拒绝 cache file content。
- 不读取本地文件。
- 不调用 live network/provider。

## 6. Section 摘要

固定 9 个 section:

- `subject`
- `evidence_status_summary`
- `financial_candidate_summary`
- `official_anchor_and_artifact_status`
- `company_business_profile`
- `industry_and_macro_context`
- `data_gaps_and_next_tasks`
- `research_questions`
- `cannot_conclude_yet`

Section 行为摘要:

- `subject` 展示标的身份和 vertical slice 定位。
- `evidence_status_summary` 展示 `provider_candidate` / `pending_official_verification` / `official_anchor_matched` / `artifact_cached` / `data_gap` / `not_assessable` / `blocked`。
- `financial_candidate_summary` 展示 provider candidate 财务信息与 pending verification，不做财务好坏判断。
- `official_anchor_and_artifact_status` 展示 anchor matched / artifact cached / `sha256_prefix` / `file_size_bytes` / `cache_filename`，不展示完整 `cache_path`。
- `company_business_profile` 展示业务证据缺口，不推断主营业务。
- `industry_and_macro_context` 展示 framework hints / questions，不写行业景气 / 宏观利好 / 公司受益。
- `data_gaps_and_next_tasks` 展示 high-priority gaps 和 next tasks。
- `research_questions` 保留问题类别。
- `cannot_conclude_yet` 明确列出当前不能确认官方指标值、不能确认 provider-official 一致性、不能生成正式报告、不能生成方向性建议、不能生成估值目标、不能生成仓位相关内容。

## 7. Evidence/status rollup 摘要

Rollup 字段:

- `provider_candidate_present`
- `pending_official_verification_count`
- `official_anchor_matched_count`
- `official_artifact_cached_count`
- `official_verified_count`
- `data_gap_count`
- `not_assessable_count`
- `blocked_count`
- `has_formal_research_report=false`
- `has_trading_advice=false`
- `not_for_trading_advice=true`

## 8. Smoke 摘要

- manual vertical slice smoke 已执行。
- smoke 不联网。
- 不调用 live provider。
- 不读取 output / fixtures / manifest。
- 不读取 cache PDF。
- 使用 inline sample components / previous-stage-shaped payload。
- section ids 为固定 9 个。
- rollup 包含:
  - provider candidate present。
  - pending count 2。
  - anchor matched 2。
  - artifact cached 1。
  - official verified 0。
  - data gap 38。
  - blocked 2。
- markdown preview 前几行包含 subject 和 rollup。
- forbidden markers present=false。
- 未输出 token。
- 未写文件。

## 9. Tests 结果

- targeted tests: 68 passed。
- related tests: 194 passed。
- system python 不可用时使用 Codex bundled Python。

## 10. 明确未触碰的禁区

已确认未触碰:

- `official_artifact_cache_acquisition.py`
- `real_official_metadata_anchor_handoff.py`
- `provider_metric_official_anchor.py`
- `ticker_research_context_skeleton.py`
- `evidence_aware_research_pack_scaffold.py`
- `provider_candidate_verification_queue.py`
- Tushare provider module
- Research Report V1 generator
- HTML renderer
- Dashboard
- `schemas.py` / `validators.py`
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

## 11. 当前剩余 untracked 项

按当前工作区裁定继续保留且不处理:

- `.local_experiments/`
- `output/`
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

## 12. 当前阶段结论

- implementation accepted。
- no blocker。
- summary doc is docs-only。
- 项目已经第一次把真实链路状态组装成用户可读研究包雏形。
- 这仍然不是正式 Research Pack。
- 这仍然不是 Report V1。
- 这仍然没有 `official_metric_fact`。
- 这仍然没有 provider-vs-official reconciliation。
- 这仍然不包含交易建议。
- 下一阶段应先 reassess。
- 建议下一步围绕 vertical slice 暴露出的最大缺口选择:
  - 极小 official evidence extraction slice。
  - 或 public API / orchestration cleanup。
  - 或 ticker-generalization smoke。
- 不要继续无目的扩基础设施。
- 不要直接进入 Report V1 或交易建议。
