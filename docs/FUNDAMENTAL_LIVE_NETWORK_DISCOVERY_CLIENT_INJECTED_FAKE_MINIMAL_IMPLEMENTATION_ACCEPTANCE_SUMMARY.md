# Live Network Discovery Client Injected-Fake Minimal Implementation Acceptance Summary

## 阶段名称

Live Network Discovery Client Injected-Fake Minimal Implementation

## Baseline Commits

- implementation commit: `58d6c5b`
- readiness gate commit: `021b85e`
- post metadata adapter reassessment commit: `05cfa02`
- official source discovery metadata adapter acceptance summary commit: `3a3ead4`
- official source discovery metadata adapter implementation commit: `f6461f8`

## 本阶段目标

本阶段实现 injected fake live discovery client gate，范围限定为 injected fake client interface 与 fake metadata response normalization。

本阶段支持：

- typed metadata query
- explicit fake responses
- domain allowlist policy
- redirect_chain metadata validation
- content-type policy
- structured error model
- handoff to existing `official_source_discovery_adapter`

本阶段不实现：

- real network client
- live CNInfo/SSE/SZSE/BSE query
- PDF download
- PDF parsing
- provider integration
- Report V1 integration
- output, fixtures, or accepted manifest writes

## 修改文件清单

- `src/fundamental_skill/data_verification/live_network_discovery_client.py`
- `tests/test_live_network_discovery_client.py`
- `tests/test_live_network_discovery_client_safety.py`

## 功能摘要

- 新增 `live_network_discovery_client_result.v1`
- `client_mode` 仅允许 `injected_fake`
- real network mode disabled by design
- 支持 `request -> typed_metadata_query`
- 支持 explicit fake responses
- 支持 normalized metadata records
- 支持 handoff to `official_source_discovery_adapter`
- 支持 `policy_decisions` / `errors` / `blocked_reasons` / `caveats`
- 支持 final result envelope recursive safety scan
- 合格 fake metadata 进入 adapter，不直接生成 registry / locator / fact / metric / report

## Policy 摘要

Exact-host allowlist:

- `www.cninfo.com.cn`
- `static.cninfo.com.cn`
- `www.sse.com.cn`
- `www.szse.cn`
- `www.bse.cn`

Domain and URL policy:

- apex hosts 默认 rejected
- no wildcard
- no substring matching
- path/query allowlist spoof rejected
- userinfo URL rejected
- malformed URL rejected
- mixed-case and trailing-dot hosts normalized

Redirect policy:

- `redirect_chain` 只校验显式 metadata
- `redirect_chain` max length 3
- every redirect hop must stay within the same source family allowlist

Content-type policy:

- only `application/json` and `text/html` are allowed
- PDF / binary / unknown content-type rejected
- real network mode blocked

## Focused Final Diff Review And Patch Summary

Initial implementation review: summary-level pass.

Project review found a final result validator gap: `validate_live_network_discovery_client_result()` needed a full recursive final envelope safety scan across accepted result fields.

Audit patch conclusion: PASS.

Patch content:

- `validate_live_network_discovery_client_result()` adds final result envelope recursive safety scan
- scan coverage includes `request`, `typed_metadata_query`, `input_fake_responses`, `normalized_metadata_records`, `discovery_adapter_result`, `blocked_reasons`, `policy_decisions`, `errors`, and `caveats`
- avoids scanning top-level `schema_version` so the literal word `network` inside the schema id is not falsely rejected
- URL fields continue to use dedicated secret-marker checks, so valid `https` / `http` official URLs are not falsely rejected
- URL values containing `token`, `.env`, or `tushare_token` are still rejected
- tests were added for `policy_decisions`, `blocked_reasons`, `discovery_adapter_result`, `typed_metadata_query`, URL secret markers, Chinese markers, and fact/conflict/report markers

Patch status:

- no blocker after patch
- no Gemini / DeepSeek / Kimi audit condition was triggered

## 测试结果

- targeted tests: 665 passed
- related regression subset: 228 passed
- extra subset: 249 passed
- system `python` was unavailable; Codex bundled Python was used

## 明确未触碰的禁区

Confirmed not touched:

- real live discovery
- network
- provider / AkShare / Tushare
- CNInfo / SSE / SZSE / BSE live
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

## 当前剩余 Untracked 项

Known existing untracked items remain untouched:

- `.local_experiments/`
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

## 当前阶段结论

- implementation accepted
- no blocker
- this summary doc is docs-only
- real network client remains unimplemented
- the next stage should begin with reassessment / planning
- do not directly proceed into real live discovery, PDF parser, download/cache acquisition, provider adapter, Report V1, Research Pack / Evidence Panel implementation, or output/fixture/manifest writes
