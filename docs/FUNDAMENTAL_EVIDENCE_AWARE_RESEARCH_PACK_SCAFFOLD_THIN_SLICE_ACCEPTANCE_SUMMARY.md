# Evidence-aware Research Pack Scaffold Thin Slice Acceptance Summary

## 阶段名称

Evidence-aware Research Pack Scaffold Thin Slice

## Baseline commits

- implementation commit: `222ae11cd1715611a7f2d582b05767e348410a62`
- previous completed stage: Ticker-Agnostic Research Context Skeleton acceptance summary commit `2ebb1d3`

## 本阶段目标

- 将已验证的 `ticker_research_context_skeleton.v1` 装配为用户可读但证据约束的 research pack scaffold。
- 输入只能是 validated `ticker_research_context_skeleton.v1`。
- 输出 `evidence_aware_research_pack_scaffold.v1`。
- 只做结构化 scaffold / section assembly。
- 不做正式 Research Pack。
- 不接 Report V1。
- 不生成正式研报。
- 不生成投资结论。
- 不升级 evidence status。

## 修改文件清单

- `src/fundamental_skill/research_planning/evidence_aware_research_pack_scaffold.py`
- `tests/test_evidence_aware_research_pack_scaffold.py`
- `tests/test_evidence_aware_research_pack_scaffold_safety.py`

## 功能摘要

- 新增 `evidence_aware_research_pack_scaffold.v1`。
- 新增 `evidence_aware_research_pack_section.v1`。
- 新增 `evidence_status_legend.v1`。
- scaffold 顶层包含 `ts_code`、`stock_code`、`company_name_hint`、`source_context_schema_version`、`sections`、`evidence_status_legend`、`global_limitations`、`next_data_tasks`、`blocked_reasons`、`caveats`、`not_for_trading_advice`。
- 固定 8 个 section：
  - `research_subject`
  - `company_business_profile`
  - `financial_context`
  - `industry_context`
  - `macro_transmission`
  - `official_verification`
  - `data_gaps`
  - `research_questions`
- 每个 section 都是结构化 dict，不是自由长文。

## Evidence/status 边界摘要

- scaffold 只使用 context skeleton 中已组织好的字段。
- `provider_candidate` 不会升级为 `official_verified`。
- `pending_official_verification` 不会升级为 `official_verified`。
- `official_verified` 只允许作为显式 context status 或 legend label。
- `financial_context` section 禁止 claim `official_verified`。
- `evidence_status_legend` 可以解释全部 evidence status，但不升级任何 section。
- no new evidence status created by scaffold。

## Section 行为摘要

- `research_subject` 只展示主体信息和 evidence status summary。
- `company_business_profile` 展示业务字段和 data gap，不推断主营业务。
- `financial_context` 展示 provider candidate / pending verification / missing metrics，不做财务好坏判断。
- `industry_context` 展示 framework inputs / driver questions / data gaps，不写行业景气结论。
- `macro_transmission` 展示问题和所需证据，不写宏观利好/利空。
- `official_verification` 展示 pending count 和后续 official anchor/evidence extraction tasks，不生成 `official_metric_fact`。
- `data_gaps` 展示 high-priority gaps / next data tasks / blocked reasons。
- `research_questions` 保留 question categories，不改写成结论。

## Tests 结果

- targeted tests: 54 passed。
- related tests: 150 passed。
- 系统 `python` 不可用时使用 Codex bundled Python。

## 明确未触碰的禁区

- `ticker_research_context_skeleton.py`
- Tushare provider module
- `provider_candidate_verification_queue.py`
- official verification modules
- official source discovery modules
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
- 买入 / 卖出 / 持有
- 目标价
- 仓位
- 技术信号
- `official_metric_fact`
- `provider_official_conflict`

## 当前剩余 untracked 项

- `.local_experiments/`
- `output/`
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

## 当前阶段结论

- implementation accepted。
- no blocker。
- summary doc is docs-only。
- 项目已从 research context skeleton 进入 evidence-aware research pack scaffold。
- 这仍然不是正式 Research Pack。
- 下一阶段应先 reassess。
- 后续建议回到 Provider Queue -> Official Disclosure Anchor，补官方证据闭环。
- 不要直接进入 Report V1 或交易建议。
