# Official Disclosure Discovery Request Contract Minimal Implementation Acceptance Summary

## 1. 阶段名称

Official Disclosure Discovery Request Contract Minimal Implementation

## 2. Baseline Commits

- implementation commit: `cc86447`
- readiness gate commit: `e56cf4e`
- security identity acceptance summary commit: `da5a57e`
- security identity implementation commit: `65df22c`

## 3. 本阶段目标

本阶段实现 `official_disclosure_discovery_request.v1`，仅作为 no-IO、no-network、no-provider 的官方披露查询请求 contract。

该 contract 从已经验证过的 `security_identity.v1`，加上显式 `query_period`、`requested_announcement_type` 和 source policy，构造“要找什么官方披露”的 request。

本阶段不做 live discovery、provider lookup、CNInfo/SSE lookup、PDF parser、Report V1，也不写 output、fixtures 或 accepted manifest。

## 4. 修改文件清单

- `src/fundamental_skill/data_verification/official_disclosure_request.py`
- `tests/test_official_disclosure_request.py`
- `tests/test_official_disclosure_request_safety.py`

## 5. 功能摘要

- 新增 `official_disclosure_discovery_request.v1`。
- 支持从 `security_identity.v1` handoff。
- 只接受 `identity_status=valid` 且 `identity_confidence` 为 `high` 或 `medium`。
- 支持显式 `query_period` 格式。
- 支持 `annual_report`、`semiannual_report`、`quarterly_report`。
- 支持 official-only `allowed_source_types`。
- 支持 `metadata_only`、`official_disclosure_candidate_only` discovery scope。
- 支持 deterministic `request_id`。
- 支持 `can_enter_discovery_candidate_generation` readiness check。
- request 只表达“要找什么”，不执行 live discovery。

## 6. Policy 摘要

- `2024` / `2024A` / `2024FY` -> `annual_report`，`period_end_date=2024-12-31`。
- `2024H1` -> `semiannual_report`，`period_end_date=2024-06-30`。
- `2024Q1` / `2024Q2` / `2024Q3` -> `quarterly_report`。
- `2024Q4` blocked。
- `最近年报` / `最新年报` / `上一期` / `latest` / `recent` blocked。
- `correction` / `exchange_announcement` 默认不启用。
- 显式 `requested_announcement_type` 必须与 `query_period` 推导类型一致。
- `allowed_source_types` 只允许 `cninfo_official_pdf` / `sse_exchange_announcement` / `exchange_official_pdf`。
- `provider_source_candidate` / `mirror_source_candidate` / `unknown_source_candidate` / `local_official_cache` blocked。
- `discovery_scope` 只允许 `metadata_only` / `official_disclosure_candidate_only`。
- `download` / `parse_pdf` / `metric_extraction` / `provider_lookup` / `report_generation` / `output_write` blocked。

## 7. Security Identity Handoff 摘要

- 只接受 `security_identity.v1`。
- `partial` / `low` / `blocked` identity 拒绝。
- company_name-only blocked identity 拒绝。
- request 保留 `security_identity` caveats。
- request 不覆盖 `security_identity` caveats。
- request 不声称 `company_name` 已 verified match。
- request 不做 live lookup / provider lookup 验证身份。

## 8. Focused Final Diff Review 和 Patch 摘要

focused final diff review 初始结论为 `PASS_WITH_PATCH_NEEDED`。

最小 patch 内容：

- direct validator 对缺失 `requested_announcement_type` fail-closed。
- direct validator 对缺失 / 非 list `source_priority` fail-closed。
- direct validator 对缺失 `discovery_scope` fail-closed。
- 补充 direct validation 和 `can_enter_discovery_candidate_generation` 阻断测试。

patch 后无 blocker。未修改 `security_identity.py`、`schemas.py`、`validators.py` 或 shared safety scan。未触发 Gemini / DeepSeek / Kimi 三方审计条件。

## 9. 测试结果

- targeted tests: `506 passed`
- related regression subset: `228 passed`
- extra subset: `249 passed`
- official verification schema/validator subset 未运行，原因是未修改 `schemas.py` / `validators.py`。
- 系统 `python` 不可用时，使用 Codex bundled Python，并设置 `PYTHONPATH=src`。

## 10. 明确未触碰的禁区

确认本阶段未触碰：

- live discovery
- network
- provider / AkShare / Tushare
- CNInfo / SSE live
- PDF parser / table extractor
- metric extraction
- Report V1
- accepted manifest
- output baseline
- fixtures
- token / `.env` / `tushare_token`
- `.local_experiments`
- unrelated mojibake files
- unrelated examples file
- trading advice / target price / position / technical signal

## 11. 当前剩余 Untracked 项

当前工作区仍有以下既存 untracked 项，均未处理：

- `.local_experiments/`
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

## 12. 当前阶段结论

- implementation accepted。
- no blocker。
- summary doc is docs-only。
- 下一阶段应先 reassess / planning。
- 不要直接进入 live discovery、PDF parser、provider adapter、Report V1、Research Pack / Evidence Panel implementation 或 output/fixture/manifest 写入。
