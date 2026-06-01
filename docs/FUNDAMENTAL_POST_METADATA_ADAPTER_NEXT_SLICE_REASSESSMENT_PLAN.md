# Post Metadata Adapter Reassessment / Next-Slice Planning

## 1. 阶段名称和当前 baseline

阶段名称：Post Metadata Adapter Reassessment / Next-Slice Planning

本阶段性质：docs-only reassessment / planning。当前阶段只判断 metadata-only fake / injected adapter 完成后的下一刀，不进入 implementation，不写 production code，不写 tests，不联网，不读取 token / `.env` / `tushare_token.txt`，不生成 output / fixtures / accepted manifest，不 commit，不 push。

当前观察到的最近提交：

- `3a3ead4 docs: accept official source discovery metadata adapter`
- `f6461f8 feat: add official source discovery metadata adapter`
- `227e069 docs: add official source discovery metadata readiness gate`
- `625f1ac docs: accept request synthetic dry-run integration`
- `caef73b feat: add request synthetic dry-run integration`
- `f0f5b6c docs: add request synthetic dry-run integration plan`
- `0a64ea2 docs: accept official disclosure request contract`
- `cc86447 feat: add official disclosure request contract`

当前关键 baseline：

- Official Source Discovery Adapter Metadata-Only Minimal Implementation 已完成，commit `f6461f8`。
- Official Source Discovery Adapter Metadata-Only Acceptance Summary 已完成，commit `3a3ead4`。
- 当前 metadata adapter 仍然是 fake / injected metadata-only。
- 当前没有真实 live discovery。
- 当前没有 network client。
- 当前没有 provider adapter。
- 当前没有 PDF parser / table extraction。
- 当前没有 metric extraction。
- 当前没有 Report V1。
- 当前没有 output / fixtures / accepted manifest。
- 当前没有 token 使用。

## 2. 当前能力地图

当前已经具备的链路能力：

- `security_identity.v1`
- `official_disclosure_discovery_request.v1`
- `request_synthetic_dry_run_integration`
- `official_source_discovery_adapter` metadata-only
- `official_disclosure_discovery_candidate.v1`
- registry / locator
- synthetic dry-run
- official verification data gate
- recursive safety scan
- no-IO / no-network fake metadata pipeline

这些能力已经足够证明：请求对象、安全身份、metadata-only discovery candidate、注册定位、synthetic dry-run、以及 verification gate 可以在无网络、无下载、无解析、无指标抽取的条件下闭环。

## 3. 当前缺口地图

当前尚未具备：

- real live official metadata discovery client
- CNInfo / SSE / SZSE / BSE live query
- network client abstraction
- domain allowlist enforcement against real responses
- redirect handling against real responses
- timeout / retry / rate limit handling
- malformed live response handling
- source freshness policy in real discovery
- download/cache acquisition
- PDF parser / table extraction
- official metric extraction
- provider reconciliation
- Evidence Panel / Research Pack integration

缺口的核心不是 PDF、metric 或 Report V1，而是：系统还没有定义真实官方源 metadata discovery 的网络边界、失败模型、allowlist、redirect、timeout、rate limit、以及 metadata-only handoff 规则。直接实现 live client 会把网络、下载、解析、输出形态和 provider reconciliation 过早耦合在一起。

## 4. 下一刀候选方案

### A. Live Network Discovery Client Readiness Gate

目标：规划真实 CNInfo / SSE / SZSE / BSE metadata discovery client 的安全边界。

本阶段只做 readiness，不做实现。重点锁定：

- network client abstraction
- domain allowlist
- redirect policy
- timeout policy
- retry policy
- rate limit policy
- no download
- no parser
- metadata-only response shape
- fail-closed error model

初步判断：最适合作为下一阶段，因为它直接承接 metadata-only adapter 的缺口，同时避免过早进入 PDF、metric、provider、Report V1 和 output。

### B. Metadata Adapter + Request-Driven Dry-Run Scenario Matrix

目标：继续扩展 fake metadata / request-driven integration 的 scenario tests。

价值：可以补充更多 synthetic 场景，增强现有 adapter 在无网络条件下的覆盖度。

风险：边际收益下降，容易继续在 synthetic 层重复打磨，却没有推进真实官方源 metadata discovery 所必需的网络边界决策。

初步判断：适合作为后续补强，不适合作为下一刀主线。

### C. Download / Cache Acquisition Readiness Gate

目标：规划 PDF 下载、sha256、cache policy。

价值：为后续 official source artifact acquisition 铺路。

风险：当前真实 metadata discovery client 尚未规划完成。没有稳定 metadata discovery 边界时，先规划下载/cache 会过早触碰文件获取、持久化、hash、cache invalidation 和 artifact lifecycle。

初步判断：现在过早，应在 live metadata discovery readiness gate 之后再评估。

### D. PDF Extraction Boundary Plan

目标：规划 PDF parser / table extraction。

价值：为 official metric extraction 和 table evidence 做前置边界设计。

风险：比 download/cache 更早触碰解析层。必须等 discovery 与 acquisition 边界稳定后再进入，否则 parser 设计会反向污染 source discovery 和 cache policy。

初步判断：不适合作为下一刀。

### E. Evidence Panel / Research Pack Bridge Planning

目标：规划用户可读证据展示。

价值：最终用户价值清晰，可以帮助 Report V1 或 Research Pack 更可解释。

风险：当前还没有真实官方 metadata、下载、解析、metric fact。此时规划展示层容易过早牵引 Report V1、output shape、fixtures 和 accepted manifest。

初步判断：应推迟到 official evidence artifact 和 metric fact 边界更稳定后。

## 5. 候选方案评分矩阵

| 维度 | A. Live Network Discovery Client Readiness Gate | B. Scenario Matrix | C. Download / Cache Gate | D. PDF Extraction Plan | E. Evidence Panel / Research Pack |
| --- | --- | --- | --- | --- | --- |
| 用户价值 | 高：解锁真实官方源 metadata 的前置边界 | 中：提升 synthetic 覆盖 | 中：为后续获取 PDF 铺路 | 中：为后续抽取铺路 | 高但过早：面向最终解释性 |
| 证据链价值 | 高：定义 official metadata 入口可信边界 | 中：仍停留 fake metadata | 中高：定义 artifact 获取可信边界 | 高但依赖前序 artifact | 高但依赖事实和 artifact |
| 与当前 metadata adapter 连续性 | 最高：直接承接 metadata-only adapter | 高：继续扩展当前 synthetic 链路 | 中：依赖 discovery 输出 | 低中：依赖 download/cache | 低中：依赖 extraction / fact |
| fail-closed 风险 | 可控：readiness 先定义失败模型 | 可控但收益有限 | 中：涉及文件获取和 cache | 高：解析失败形态复杂 | 中高：容易展示不完整证据 |
| scope creep 风险 | 中：需明确 no download / no parser | 中：可能扩成大量测试矩阵 | 高：可能触发 output/cache artifact | 高：可能触发 metric extraction | 高：可能触发 Report V1/output |
| 是否需要 network | readiness 不需要；未来实现需要 | 不需要 | readiness 不需要；未来获取需要 | 不需要 network，但依赖已获取 PDF | 不需要 network，但依赖前序数据 |
| 是否需要 PDF parser | 不需要 | 不需要 | 不需要 | 需要规划 parser | 不直接需要，但容易牵引 parser |
| 是否会误触 provider / Report V1 / output / fixtures | 低，只要禁止下载和输出 | 低中，若扩测试可能写 fixtures | 高，cache/output 边界易被触发 | 高，抽取 fixtures 易被触发 | 高，展示层易触发 Report V1/output |
| 可测试性 | 高：可用 injected fake client 测 allowlist/redirect/error | 高：synthetic tests 直接可写 | 中：需 mock artifact/cache | 中：需 PDF samples/fixtures | 中：需 evidence fixtures |
| 是否适合作为下一阶段 readiness gate | 是，最适合 | 否，偏补强 | 暂否，等待 discovery gate | 否，过早 | 否，过早 |
| 是否适合作为下一阶段 implementation | 否，先 readiness | 可实现但不推荐作为主线 | 否 | 否 | 否 |

## 6. 推荐下一阶段

推荐阶段名称：Live Network Discovery Client Readiness Gate

推荐理由：

- 它是从 fake / injected metadata-only adapter 走向真实官方 metadata discovery 的最小必要下一刀。
- 它仍然可以保持 docs-only 或 readiness-gate 形态，不要求直接联网、不要求下载、不要求解析 PDF、不要求生成 official metric fact。
- 它能先锁定 network client abstraction、domain allowlist、redirect、timeout、retry、rate limit、content-type、metadata-only response shape 和 fail-closed model。
- 它可以防止后续 implementation 把 discovery、download、PDF parser、metric extraction、provider reconciliation 和 Report V1 混成一个过大的切片。

为什么不选其他方案：

- B 继续打磨 synthetic scenario，但不能解决真实官方源 discovery 的核心风险。
- C 依赖稳定 metadata discovery，当前进入下载/cache 太早。
- D 依赖 discovery 与 acquisition，当前进入 PDF parser/table extraction 太早。
- E 依赖 official evidence artifact 和 metric fact，当前进入 Evidence Panel / Research Pack 会过早牵引 Report V1、output 和 fixtures。

是否建议先做 readiness gate：是。

是否允许 direct implementation：否。下一阶段不应直接实现 live network client。应先完成 Live Network Discovery Client Readiness Gate，并由 acceptance review 决定是否进入受限 implementation。

future allowed files：

- 对下一阶段 readiness gate：仅允许新增/修改明确命名的 docs planning/readiness 文件。
- 对未来受限 implementation：只有在 readiness gate 被接受后，才允许新增最小 network client abstraction、injected fake client tests、allowlist/redirect/error model tests；实际文件名应由后续实施计划根据 repo 结构单独列出并批准。

future forbidden files：

- `output/`
- fixtures
- accepted manifest
- Report V1 generator
- provider adapter
- PDF parser / table extractor
- metric extraction module
- token / `.env` / `tushare_token.txt`
- `.local_experiments`
- unrelated mojibake files

expected tests：

- 当前 docs-only reassessment：无 tests。
- 下一阶段 docs-only readiness gate：无 tests。
- 未来受限 implementation 若获批准：只允许 no-network injected-client tests，覆盖 allowlist、redirect rejection、timeout/retry/rate-limit policy、malformed metadata response、content-type rejection、metadata-only handoff、fail-closed errors。

acceptance criteria：

- next slice recommendation clear
- allowed / forbidden scope clear
- no direct implementation
- no production code
- no tests in planning stage
- no network
- no token / `.env` / `tushare_token.txt` read
- no output / fixtures / accepted manifest
- no PDF download / parser / table extraction
- no provider / Report V1 coupling
- third-party audit trigger conditions clear

blocker checklist before implementation:

- Exact official source domain allowlist is approved.
- Redirect policy is approved.
- Timeout, retry, rate-limit defaults are approved.
- Metadata-only response shape is approved.
- Fail-closed error taxonomy is approved.
- No-download and no-parser boundaries are accepted.
- Handoff to `official_source_discovery_adapter` is accepted.
- Tests are confirmed to use injected fake client only unless real network is explicitly approved.
- Third-party audit decision is recorded if real network client is introduced.

## 7. Live Network Discovery Client Readiness Gate 草案

阶段名称：Live Network Discovery Client Readiness Gate

allowed scope：

- Define the live official metadata discovery boundary.
- Define network client abstraction without implementing live calls in the readiness stage.
- Define exact future source domain allowlist policy.
- Define injected client vs real client policy.
- Define no-token policy.
- Define timeout / retry / rate limit policy.
- Define redirect policy.
- Define content-type policy.
- Define no-download policy.
- Define metadata-only response shape.
- Define result-to-adapter handoff into `official_source_discovery_adapter`.
- Define fail-closed error model.
- Define expected future tests for a later implementation slice.

forbidden scope：

- No live network implementation.
- No PDF download.
- No cache acquisition.
- No PDF parser.
- No PDF table extractor.
- No metric extraction.
- No provider fallback.
- No Report V1.
- No accepted manifest write.
- No output baseline write.
- No fixture write.
- No token read.
- No `.env` read.
- No `tushare_token.txt` read.
- No AkShare / Tushare.
- No trading advice, target price, position, or technical signal.

future source domains：

- Candidate official domain families to validate in the readiness gate: CNInfo, SSE, SZSE, BSE.
- Candidate domain families should be treated as unapproved until reviewed and reduced to exact concrete hostnames.
- No wildcard domain acceptance.
- No redirect promotion from an allowed domain to an unlisted domain.
- Attachment/CDN/download hosts remain forbidden until a separate Download / Cache Acquisition Readiness Gate is accepted.

network client abstraction：

- The abstraction should accept a typed metadata discovery request, not arbitrary URLs.
- The abstraction should validate domain allowlist before request execution.
- The abstraction should expose normalized response metadata without returning downloadable binary content.
- The abstraction should separate transport errors, policy rejections, malformed responses, stale responses, and empty results.
- The abstraction should be deterministic under injected fake clients.

injected client vs real client policy：

- Readiness stage: docs only, no client implementation.
- Future implementation stage: tests must default to injected fake client.
- Real client must be disabled by default and require explicit approval.
- Real client must not read tokens or environment secrets.
- Real client must not call provider libraries such as AkShare or Tushare.

no-token policy：

- Official metadata discovery must not require tokens.
- No `.env` read.
- No `tushare_token.txt` read.
- No provider credential fallback.

timeout / retry / rate limit policy：

- Timeouts must be finite and conservative.
- Retries must be bounded and only apply to retry-safe transient failures.
- Rate limits must be explicit and conservative.
- Exhausted retry or rate limit must fail closed with structured error metadata.

redirect policy：

- Redirects must not be silently followed across domains.
- Same-domain redirects require explicit policy handling and normalized final URL recording.
- Cross-domain redirects must fail closed unless the final hostname is explicitly allowlisted.
- Redirect chains must have a small fixed maximum length.

content-type policy：

- Metadata discovery may accept only approved metadata-oriented content types, such as JSON or HTML, after future review.
- PDF, binary, archive, image, and unknown content types must not be downloaded or parsed in the discovery stage.
- Content type mismatch must fail closed.

no download policy：

- The discovery client may record metadata about a PDF or disclosure artifact.
- It must not download artifact bytes.
- It must not calculate sha256.
- It must not write cache files.
- It must not create fixtures or output baselines.

metadata-only response shape：

- `security_identity`
- `request_id`
- `ticker`
- `exchange`
- `source_family`
- `source_domain`
- `source_url`
- `normalized_url`
- `disclosure_id`
- `title`
- `announcement_type`
- `published_at`
- `content_type`
- `artifact_kind`
- `is_downloaded: false`
- `fetch_policy`
- `freshness_status`
- `discovery_status`
- `policy_decisions`
- `error_code`
- `error_message`

result -> `official_source_discovery_adapter` handoff：

- Live discovery results must remain metadata-only.
- The handoff should produce `official_disclosure_discovery_candidate.v1` only after policy checks pass.
- Rejected responses should not be promoted into discovery candidates.
- Candidate provenance should record source family, source domain, normalized URL, policy decisions, and no-download status.

fail-closed error model：

- Unknown domain: reject.
- Cross-domain redirect: reject unless explicitly allowlisted.
- Unknown content type: reject.
- PDF/body download attempt: reject.
- Malformed live response: reject with structured error.
- Missing publish date or title: reject or quarantine according to approved freshness policy.
- Ambiguous ticker/exchange mapping: reject.
- Stale source beyond freshness policy: reject or quarantine.
- Provider fallback request: reject.

expected files：

- For the readiness stage itself: one docs readiness file only.
- For future implementation after acceptance: minimal source files and tests must be listed in a separate implementation plan before editing.

expected tests：

- Readiness stage: none.
- Future implementation after acceptance:
  - injected fake client success path
  - domain allowlist rejection
  - cross-domain redirect rejection
  - same-domain redirect normalization
  - timeout error classification
  - retry exhaustion classification
  - rate-limit classification
  - malformed metadata response rejection
  - content-type rejection
  - no-download invariant
  - metadata-only handoff to discovery candidate

三方审计触发条件：

- A real network client is introduced.
- Redirect handling is implemented against live responses.
- Domain allowlist enforcement is implemented against live responses.
- Source promotion from live response to official candidate is implemented.
- Persistent cache, artifact acquisition, or output baseline is introduced.
- Any boundary can affect official evidence trust, user-facing research, or future Report V1.

## 8. 明确禁止事项

下一阶段仍不得默认进入：

- PDF download
- PDF parser
- PDF table extraction
- metric extraction
- provider fallback
- Report V1
- accepted manifest write
- output baseline write
- fixture write
- token read
- `.env` read
- `tushare_token.txt` read
- trading advice
- target price
- position
- technical signal

这些事项必须由单独 planning / readiness / acceptance 流程显式批准，不能由 live metadata discovery readiness gate 顺带引入。

## 9. 三方审计建议

当前 docs-only reassessment 不需要三方审计，因为本阶段只新增 planning 文档，不联网、不实现 client、不读 token、不写 output、不写 tests。

如果 future readiness gate 仍然是 docs-only，也不需要三方审计。

如果 future implementation 引入真实 network client、redirect handling、domain allowlist enforcement、source promotion boundary，建议触发 Gemini / DeepSeek / Kimi 三方审计，重点审计：

- domain allowlist 是否过宽
- redirect policy 是否会被绕过
- live response 是否可能被错误提升为 official candidate
- no-download / no-parser 边界是否被破坏
- fail-closed error model 是否完整
- 是否存在 provider/token fallback

如果仅做 injected fake client interface，且不接真实网络，可先不默认三方审计；但仍应在 acceptance summary 中记录未触发三方审计的理由。

## 10. Acceptance criteria

Planning acceptance：

- 只新增 docs planning 文件。
- no production code。
- no tests。
- no network。
- no token / `.env` / `tushare_token.txt` read。
- no mojibake handling。
- next slice recommendation clear。
- allowed / forbidden scope clear。
- future files/tests clear。
- implementation entry can be approved or rejected。
- 不 commit。
- 不 push。

当前 reassessment 结论：

- 推荐下一阶段：Live Network Discovery Client Readiness Gate。
- 不建议 direct implementation。
- 不建议当前引入真实 network client。
- 当前不需要三方审计。
- 若后续真实 network client 进入 implementation，应触发三方审计。
