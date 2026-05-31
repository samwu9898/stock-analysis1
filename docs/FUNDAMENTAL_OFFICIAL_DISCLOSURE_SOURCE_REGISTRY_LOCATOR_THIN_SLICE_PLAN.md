# Official Disclosure Source Registry + Locator Thin Slice Plan

Date: 2026-05-31

Stage: Official Disclosure Source Registry + Locator thin slice planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not download
PDFs, does not parse PDFs, does not call CNInfo/SSE/AkShare/Tushare/provider
endpoints, does not read tokens or `.env`, does not write accepted manifests,
does not write output baselines or fixtures, does not connect Report V1, does
not create formal research reports, does not commit, and does not push.

Reference baseline:

- Official Verification Productionization Minimal Implementation:
  `c687792402973d6dcf7621326d2371169fefee3a`.
- Official Verification Productionization Minimal Implementation Acceptance
  Summary: `5695135aa1c72bbe2391c8545746a540014bc3b7`.

## 1. 阶段目标

本阶段只规划 `official disclosure source registry + locator` 的最小生产切片。

目标是定义未来系统如何从：

```text
stock_code + period + announcement_type
```

得到：

```text
official source candidate
-> official source registry entry
-> optional local official cache metadata
-> file_sha256
-> source_status
-> source_refresh_policy
-> downstream official verification input
```

本阶段关注官方披露文件的定位、登记、缓存元数据、`file_sha256` 和刷新策略。它是已完成 official verification data gate 的上游入口，不是指标抽取层。

本阶段明确不做：

- 不抽取 metric。
- 不解析 PDF 表格。
- 不接 Report V1。
- 不接 provider adapter。
- 不写 accepted manifest、output baseline 或 fixture。
- 不生成正式研报。
- 不下载或解析 CNInfo/SSE/exchange PDF。
- 不读取 token、`.env` 或 `tushare_token.txt`。
- 不把 mirror、provider endpoint 或 source candidate 当成 official fact。

## 2. 输入边界

未来最小生产切片只允许以下输入：

- `stock_code`。
- `company_name`。
- `period_key` / `period_end_date`。
- `announcement_type`。
- `source_url` candidate。
- optional local official file path。
- `not_for_trading_advice=true`。

这些输入只描述官方披露来源定位和登记状态。它们不能携带投资结论、价格目标、交易动作、Report V1 payload 或 provider metric。

明确拒绝以下输入：

- raw provider metric value。
- Report V1 payload。
- accepted manifest。
- output scan result。
- investor prompt。
- trading prompt。
- target price prompt。
- token。
- `.env`。
- unverified mirror URL as official fact。
- `not_for_trading_advice=false`。

`source_url` 在进入 official lane 前必须被分类。不能因为 URL 能打开、标题看似正确、或第三方页面展示了公告链接，就自动接受为官方来源。

## 3. Source Type Policy

本 thin slice 规划以下 source types。它们是 locator/registry 层的来源类型，不等同于已完成 data gate 中的 `official_metric_fact.v1`。

| source_type | lane | policy |
| --- | --- | --- |
| `cninfo_official_pdf` | official candidate | 仅当 URL 与元数据确认来自 CNInfo 官方披露入口时可进入 official source candidate；缓存或下游 extraction 仍需要 `file_sha256`。 |
| `sse_exchange_announcement` | official candidate | 上交所官方公告页面或官方披露文件可进入 official source candidate；需要 title、date、period、announcement_type。 |
| `exchange_official_pdf` | official candidate | 交易所官方 PDF 或官方披露文件可进入 official source candidate；具体交易所域名必须被显式 allowlist。 |
| `local_official_cache` | official cache lane | 只有同时具备 original official URL、local cache path、`file_sha256` 和完整元数据时才可进入 official cache lane。 |
| `mirror_source_candidate` | discovery only | 只能帮助发现 official URL，不能 `accepted_as_official`，不能产生 official fact。 |
| `provider_source_candidate` | provider/discovery only | AkShare/Tushare/provider endpoint 只能作为 provider candidate 或发现线索，不能成为 official fact。 |
| `unknown_source_candidate` | blocked/discovery only | 必须 blocked until review，不能进入 official lane。 |

与现有 `src/fundamental_skill/data_verification/schemas.py` 的关系：

- 现有 data gate 已有 `SourceType`、`OFFICIAL_SOURCE_TYPES`、`DISCOVERY_ONLY_SOURCE_TYPES` 和 `PROVIDER_SOURCE_TYPES`。
- 未来实现应显式映射 registry/locator source types 到现有 official verification source types。
- 不应静默把 `mirror_source_candidate`、`provider_source_candidate` 或 `unknown_source_candidate` 映射为 official source type。
- 如果保留现有 `sse_exchange_official_announcement` 命名，应在 schema 文档和 validator 中明确它与 locator 层 `sse_exchange_announcement` 的兼容关系。

## 4. Source Registry Schema 草案

规划 schema:

```text
official_source_registry_entry.v1
```

最低字段：

| field | required | policy |
| --- | --- | --- |
| `schema_version` | yes | 必须等于 `official_source_registry_entry.v1`。 |
| `source_id` | yes | 稳定 ID，建议由 `stock_code`、`period_key`、`announcement_type`、`source_type`、`source_url`、`source_version` 生成。 |
| `stock_code` | yes | 6 位 A 股代码；不做模糊 ticker 推断。 |
| `company_name` | yes | 来自显式输入或官方元数据，不从 provider metric 推断。 |
| `period_key` | yes | 查询期，例如 `2025FY`、`2025H1`、`2025Q3`。 |
| `period_end_date` | yes | 披露覆盖期末日期。 |
| `announcement_type` | yes | 必须是有限枚举；未知类型 blocked。 |
| `source_type` | yes | 必须是本计划定义的 source type。 |
| `source_url` | conditional | official URL 或 source candidate URL；local cache lane 必须有 original official URL。 |
| `source_title` | yes for official lanes | 官方披露标题；缺失时 blocked。 |
| `disclosure_date` | yes for official lanes | 官方披露日期；缺失时 blocked。 |
| `local_cache_path` | optional | 仅作为缓存元数据，不是 output baseline。 |
| `file_sha256` | conditional | cached official file 必须有 64 位 sha256；缺失时不能进入 official cache lane。 |
| `retrieved_at_utc` | conditional | 缓存或人工登记时间；必须是 UTC。 |
| `source_status` | yes | 使用第 6 节有限枚举。 |
| `source_refresh_policy` | yes | 使用第 9 节刷新策略，不允许空值。 |
| `registry_version` | yes | registry entry 版本；同一 source 更新时递增或产生新版本。 |
| `source_version` | yes | 官方来源本身版本，例如 original、corrected、updated、manual_reviewed。 |
| `rejection_reason` | conditional | rejected/blocked/conflict 时必填。 |
| `caveats` | yes | list，记录限制、人工复核需求和不确定性。 |
| `not_for_trading_advice` | yes | 必须为 `true`。 |

schema 行为要求：

- official URL 可以先成为 `official_candidate`，但没有 `file_sha256` 的本地文件不能成为 `official_cached`。
- `local_official_cache` 不是独立官方来源。它必须回指 original official URL。
- `file_sha256` 不匹配时必须产生 `source_conflict`，不能覆盖旧 hash。
- `registry_version` 和 `source_refresh_policy` 是 registry entry 的准入字段，不允许省略。

## 5. Locator Output Schema 草案

规划 schema:

```text
official_disclosure_locator_result.v1
```

最低字段：

| field | required | policy |
| --- | --- | --- |
| `schema_version` | yes | 必须等于 `official_disclosure_locator_result.v1`。 |
| `stock_code` | yes | 与 request 一致。 |
| `company_name` | yes | 与 request/official metadata 一致；不做模糊推断。 |
| `query_period` | yes | 包含 `period_key` 和/或 `period_end_date`。 |
| `requested_announcement_type` | yes | 必须是受支持公告类型。 |
| `candidates` | yes | 所有 source candidates 的结构化列表。 |
| `selected_official_source_id` | conditional | 仅在单一官方候选可选且无冲突时填充。 |
| `rejected_candidates` | yes | mirror/provider/unknown/missing metadata 等拒绝项。 |
| `source_conflicts` | yes | sha mismatch、多官方候选、period/type 冲突等。 |
| `locator_status` | yes | 使用第 6 节有限枚举。 |
| `blocked_reason` | conditional | blocked/review required 时必填。 |
| `caveats` | yes | list，说明边界和人工复核事项。 |
| `not_for_trading_advice` | yes | 必须为 `true`。 |

locator 行为要求：

- locator 只选择 official source registry entry 或 review-required 状态。
- locator 不产生 `official_metric_fact.v1`。
- locator 不做 provider/official conflict 判断。
- locator 不读取 accepted manifest、output、fixture、Report V1 artifact。
- locator 不调用 provider，不联网，不读取 token。

## 6. Status 枚举

`source_status` 有限枚举：

- `official_candidate`。
- `official_cached`。
- `rejected_mirror`。
- `rejected_provider_endpoint`。
- `missing_sha256`。
- `missing_required_metadata`。
- `source_conflict`。
- `blocked_until_review`。

`locator_status` 有限枚举：

- `found_single_official_candidate`。
- `found_multiple_candidates_review_required`。
- `no_official_source_found`。
- `rejected_all_candidates`。
- `blocked_until_review`。

状态转换规则：

- `official_candidate` 可以在 metadata 完整时作为官方来源候选进入人工或后续验证流程。
- `official_cached` 只能由 official URL + local cache path + valid `file_sha256` 形成。
- `missing_sha256` 不能被 promotion 为 cached official source。
- `source_conflict` 必须阻断 downstream official verification input。
- 多个同 period/announcement_type 官方候选默认进入 `found_multiple_candidates_review_required`。

## 7. Cache / SHA256 Policy

local official cache 不是 output baseline，也不是 accepted manifest。它只是官方披露文件的本地缓存元数据。

强制规则：

- cache file 必须有 original official source URL。
- cache file 必须有 `file_sha256`。
- `file_sha256` 必须是 64 位十六进制 sha256。
- sha256 mismatch 必须生成 `source_conflict`。
- 同一 source URL 但 sha256 不同，必须创建新的 `registry_version` 或 `source_version`，不得静默覆盖旧 hash。
- 缺 `file_sha256` 不得进入 `official_cached` lane。
- 不得把 `.local_experiments` cache 自动写入 production registry。
- 第一版 production 只支持 explicit local file + explicit sha256 metadata，不做 live download。
- local file without official URL 必须 blocked。
- local path 必须被当作元数据，不触发 output scan 或 artifact parser。

建议第一版实现只接受调用方显式传入的：

```text
source_url + local_cache_path + file_sha256 + source_title + disclosure_date + period + announcement_type
```

如果只传入 local file path 而没有 official URL，则只能产生 `blocked_until_review`，不能产生 official registry entry。

## 8. Live Access Boundary

本 planning 阶段不联网。

第一版 official source locator production implementation 默认不应 live 下载 CNInfo/SSE/exchange PDF。建议先支持 explicit `source_url` + local official file + sha256 registry entry。

原因：

- live downloader 会引入网络可用性、重定向、镜像页面、反爬、速率限制、文件更新、存储路径和 hash 稳定性问题。
- live downloader 容易把 discovery 行为、official URL 判定、缓存写入和 registry promotion 混在一个阶段里。
- 当前更紧缺的是 source registry schema、locator result schema、fail-closed policy 和 downstream data gate 的入口契约。
- 在没有 controlled downloader 边界前，不应让 locator 拥有下载、缓存写入或自动接受 official source 的能力。

controlled official downloader 应作为单独阶段规划。若未来启用，必须至少具备：

- 显式 allowlist 官方域名。
- 禁止 provider、mirror、搜索引擎和第三方下载源。
- 禁止 token 和 `.env` 读取。
- 明确 redirect policy，redirect 到非官方域名时拒绝。
- content type、文件大小、扩展名和 sha256 校验。
- 下载前后记录 `retrieved_at_utc`、source URL、final URL、sha256 和 source version。
- 下载成功不等于 accepted official；仍需 registry validator 通过。
- 不写 accepted manifest，不写 output baseline，不触发 Report V1。

## 9. Source Refresh / Versioning

`source_refresh_policy` 必须显式存在。建议第一版有限策略：

- `manual_review_only`: 需要人工确认，不自动刷新。
- `explicit_metadata_refresh`: 只允许显式输入更新 metadata。
- `explicit_file_rehash`: 只允许显式本地文件重新计算或传入 sha256。
- `corrected_filing_review_required`: 修订公告或更新披露必须人工复核。
- `immutable_cache_record`: 已登记 hash 保留，不覆盖。

版本字段职责：

- `registry_version`: registry entry 的版本。登记策略、metadata 或 hash 变化时更新。
- `source_version`: 官方披露文件的版本。可表达 original、corrected、updated 或 manual-review variant。
- `source_id`: 应包含或引用版本信息，避免同一 URL 不同 sha256 覆盖。

关键场景：

- same source URL but different sha256: 生成 `source_conflict`，保留旧 entry，新增版本或 blocked review item。
- same period / announcement_type multiple official candidates: locator 返回 `found_multiple_candidates_review_required`，不得自动选最新或最大文件。
- announcement correction / updated filing: 新旧来源都保留；新来源需要 `source_version` 标注和 review policy。
- older source retained: 旧 entry 继续可追溯，不能被 silent overwrite。
- metadata update without file change: 更新 `registry_version`，保留相同 `file_sha256`。

## 10. Fail-closed Rules

必须 fail closed 的情况：

- mirror source cannot become official。
- provider endpoint cannot become official。
- missing title / disclosure_date / period / announcement_type blocked。
- missing sha256 blocked for cached file。
- ambiguous multiple candidates -> review_required。
- unknown announcement_type -> blocked。
- source_url domain not official -> source_candidate only。
- local file without official URL -> blocked。
- sha256 mismatch -> source_conflict。
- `not_for_trading_advice=false` -> reject。
- trading / target price markers -> reject。
- token、`.env`、`tushare_token.txt`、provider live call、network intent -> reject。
- Report V1 trigger、accepted manifest write、output baseline write、fixture write -> reject。
- PDF parse、PDF table extractor、official metric extraction intent -> reject。

在 fail-closed 状态下，locator 可以返回 structured rejected candidate 或 blocked result，但不得生成 downstream official verification input。

## 11. 与已完成 Data Verification Gate 的关系

official source registry / locator 是 official verification data gate 的上游。

它只产出：

- official source metadata。
- official source registry entry。
- locator result。
- optional local official cache metadata。
- `file_sha256` 和版本信息。
- blocked/rejected/conflict 状态。

它不产出：

- `official_metric_fact.v1`。
- `provider_official_conflict.v1`。
- metric extraction result。
- provider comparison result。
- Report V1 payload。
- accepted manifest。
- output baseline。

后续 `official_metric_fact.v1` 必须由 official verification layer 在 source metadata 稳定后生成。provider/official conflict 也必须由已完成 data gate 的 promotion/conflict policy 处理，不能在 locator 层提前做。

Report V1 必须等 verified/candidate/conflict/blocked lanes 稳定后再接入。source locator 只能解决“官方披露文件在哪里、是否可登记、是否有 sha256 和版本”的问题。

## 12. Tests 策略

未来 tests 应覆盖：

- CNInfo official PDF candidate accepted as official candidate。
- SSE exchange announcement accepted as official candidate。
- exchange official PDF accepted as official candidate。
- mirror rejected as official。
- provider endpoint rejected as official。
- unknown source candidate blocked。
- local cache without sha256 rejected。
- local cache with sha256 + official URL accepted。
- missing disclosure_date/title/period/announcement_type rejected。
- multiple candidates review_required。
- sha256 mismatch source_conflict。
- registry_version required。
- source_version required。
- source_refresh_policy required。
- `not_for_trading_advice=true` required。
- `not_for_trading_advice=false` rejected。
- no token read。
- no `.env` read。
- no provider live call。
- no CNInfo/SSE live download in first production slice。
- no accepted manifest write。
- no output baseline write。
- no fixture write。
- no Report V1 trigger。
- no PDF parser or table extractor trigger。
- no trading advice / target price。

测试形态建议：

- 使用 in-memory dict/list payload。
- 使用临时 inert path strings，不检查真实 artifact 存在性。
- 不读真实 `output/`。
- 不读真实 accepted manifest。
- 不访问网络。
- 不读取 token 或 provider 配置。

## 13. Expected Files 规划

根据当前 `src/fundamental_skill/data_verification` 结构，未来最小 implementation 建议优先使用现有 package，而不是引入新顶层模块。

当前已存在：

- `src/fundamental_skill/data_verification/schemas.py`
- `src/fundamental_skill/data_verification/validators.py`
- `src/fundamental_skill/data_verification/source_registry.py`
- `src/fundamental_skill/data_verification/official_verification.py`

建议未来 implementation expected files：

- `src/fundamental_skill/data_verification/schemas.py`
  - 增加 `OFFICIAL_SOURCE_REGISTRY_ENTRY_VERSION`。
  - 增加 `OFFICIAL_DISCLOSURE_LOCATOR_RESULT_VERSION`。
  - 增加 registry/locator status 和 required-key constants。
- `src/fundamental_skill/data_verification/validators.py`
  - 增加 registry entry validator。
  - 增加 locator result validator。
  - 复用现有 safety marker 和 `not_for_trading_advice` 递归检查。
- `src/fundamental_skill/data_verification/official_disclosure_source_registry.py`
  - 新增纯 policy helper，负责 registry entry eligibility、cache/sha256/versioning policy。
  - 避免改名或扩大现有 `source_registry.py` 的 official verification data gate 语义。
- `src/fundamental_skill/data_verification/official_disclosure_locator.py`
  - 新增纯 locator helper，只处理显式输入 candidates，不联网、不下载、不读文件。
- `src/fundamental_skill/data_verification/official_verification.py`
  - 可选：在 validators 稳定后暴露 facade。
- `src/fundamental_skill/data_verification/__init__.py`
  - 可选：只暴露稳定 public API。
- `tests/test_official_disclosure_source_registry.py`
- `tests/test_official_disclosure_locator.py`
- `tests/test_official_disclosure_registry_locator_safety.py`

默认不修改：

- Report V1 generator。
- provider adapter。
- accepted manifest。
- output baseline。
- fixtures。
- token files。
- unrelated mojibake files。
- `.local_experiments`。

如果必须复用现有 `source_registry.py`，应只添加 registry/locator 上游辅助函数，不能改变已经完成的 `official_source_candidate.v1` data gate 行为。

## 14. Acceptance Checklist

未来 implementation acceptance checklist：

- only expected files changed。
- no Report V1。
- no provider adapter。
- no PDF parser。
- no PDF table extractor。
- no live download unless explicitly approved in a separate stage。
- no token read。
- no `.env` read。
- no accepted manifest/output/fixture writes。
- source registry schemas validate。
- locator output schema validates。
- mirror/provider cannot become official。
- unknown source cannot become official。
- sha256 required for cached official source。
- source_refresh_policy / registry_version / source_version enforced。
- same URL different sha256 produces source_conflict and retains old entry。
- multiple official candidates require review。
- targeted tests pass。
- regression subset pass。
- git status clean except unrelated untracked files.

Current planning-stage acceptance checklist:

- Only this planning document is added.
- No production code is written.
- No tests are written.
- No runtime artifact is generated.
- No network, provider, token, PDF parser, output scan, accepted manifest, fixture, Report V1, commit, or push action is performed.
