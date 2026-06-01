# Official Disclosure Discovery Request Contract Thin Slice / Implementation Readiness Gate

## 1. 阶段名称和当前 baseline

阶段名称：Official Disclosure Discovery Request Contract Thin Slice / Implementation Readiness Gate。

最近关键 commits：

- `da5a57e docs: accept security identity contract`
- `65df22c feat: add security identity contract`
- `65704de docs: add security identity readiness gate`
- `550616c docs: add ticker company identity request reassessment plan`
- `8576a22 docs: accept synthetic official disclosure dry-run gate`

当前 baseline：

- `security_identity.v1` 已具备，可在 no-IO / no-network / no-provider 条件下归一化 A 股证券身份。
- `official_disclosure_discovery_candidate.v1` 已具备，用于表达官方披露发现候选。
- `official_source_registry_entry.v1` 已具备，用于表达官方来源注册项。
- `official_disclosure_locator_result.v1` 已具备，用于表达官方披露 locator 结果。
- synthetic official disclosure dry-run gate 已具备，用于 synthetic-only / in-memory-only 验证链路。
- official verification data gate 已具备，用于官方验证数据 fail-closed。

本阶段性质：

- 只做 readiness gate。
- 只新增本 docs readiness gate 文件。
- 不写 production code。
- 不写 tests。
- 不做 implementation。
- 不 commit。
- 不 push。

## 2. 本阶段目标

本阶段为 future `official_disclosure_discovery_request.v1` minimal implementation 锁定边界。

目标是定义：

- schema fields。
- request normalization rules。
- query_period policy。
- requested_announcement_type policy。
- security_identity handoff policy。
- allowed_source_types policy。
- source_priority policy。
- discovery_scope policy。
- fail-closed rules。
- safety markers。
- expected implementation files/tests。
- acceptance criteria。

核心边界：

- request 只表达“要找什么官方披露”。
- request 不表达“去哪里实时访问”。
- request 不下载。
- request 不解析 PDF。
- request 不抽取指标。
- request 不生成 report。
- request 不写 output / fixture / accepted manifest。
- request 不调用 live provider、CNInfo、SSE、AkShare、Tushare。

## 3. `official_disclosure_discovery_request.v1` schema 草案

### Required fields

- `schema_version`
  - 固定值：`official_disclosure_discovery_request.v1`。
  - 必须存在。

- `request_id`
  - 请求 ID。
  - 推荐由显式 metadata 提供，或由 pure deterministic serializer 从 request 内容派生。
  - 不得通过 provider/live/source lookup 生成。

- `security_identity`
  - 嵌入或引用 `security_identity.v1` object。
  - 必须通过 handoff policy。

- `stock_code`
  - 从 `security_identity.normalized_stock_code` 派生。
  - 不允许 request layer 覆盖为其他值。

- `exchange`
  - 从 `security_identity.exchange` 派生。
  - 不允许 request layer 通过 live lookup 修正。

- `market`
  - 从 `security_identity.market` 派生。
  - 当前 minimal implementation 只支持 `CN_A`。

- `query_period`
  - 标准化 period，例如 `2024`、`2024H1`、`2024Q1`、`2024Q2`、`2024Q3`。
  - 必须存在。

- `period_end_date`
  - 由 explicit `query_period` 纯规则派生。
  - 必须存在。

- `requested_announcement_type`
  - 标准化公告类型。
  - 必须存在。

- `allowed_source_types`
  - 只允许 official source 类型。
  - 必须非空。

- `source_priority`
  - 官方来源优先级策略。
  - 必须只表达策略，不触发访问。

- `discovery_scope`
  - 只允许 request 级别的 scope，例如 `metadata_only` 或 `official_disclosure_candidate_only`。
  - 必须存在。

- `blocked_reasons`
  - 结构化 blocked reason 列表。
  - 必须存在；未 blocked 时为空列表。

- `caveats`
  - 限制说明列表。
  - 必须存在；可以继承 security identity caveat，但不得覆盖或删除。

- `not_for_trading_advice`
  - 必须存在。
  - 必须为布尔值 `true`。

### Conditional fields

- `company_name`
  - 从 `security_identity.normalized_company_name` 或 `company_name` 派生。
  - 如果 identity 中没有公司名，可以为空。
  - 如果存在，只能作为 identity 的已有信息或 unverified hint 传递。
  - 不得在 request layer 声称 verified company match。

- `rejection_reason`
  - 当 request blocked 时必须存在。
  - 当 request valid 时应为空或 `None`。

### Optional fields

- `request_metadata`
  - Future optional。
  - 只能包含 caller-provided metadata。
  - 必须经过 safety scan。
  - 不得包含 live/download/provider/parser/output/write intent。

## 4. security_identity handoff policy

明确 policy：

- 只接受 `security_identity.v1`。
- 只接受 `identity_status=valid`。
- 只接受 `identity_confidence=high` 或 `medium`。
- `partial` identity 必须拒绝。
- `low` confidence identity 必须拒绝。
- `blocked` identity 必须拒绝。
- company_name-only blocked identity 不得进入 request。
- stock_code + company_name 的 unverified company hint 可以保留 caveat。
- request 不得声称 stock_code/company_name 已 verified match。
- request 不得生成 verified company identity。
- request 不得重新做 live lookup / provider lookup 验证身份。
- request 不得覆盖 security_identity 的 caveat。
- request 可以追加自己的 caveat，例如 no-IO、no-network、no-parser、request-only contract。

推荐 handoff 行为：

- 如果 `security_identity` 已经 valid + high：
  - request 可构造。
  - identity caveats 原样保留。
- 如果 `security_identity` valid + medium：
  - request 可构造。
  - caveats 必须保留，例如 deterministic prefix inference、company hint unverified。
- 如果 `security_identity` blocked：
  - request blocked。
  - `blocked_reasons` 包含 `invalid_security_identity` 或更具体 reason。
- 如果 request payload 试图覆盖 `stock_code` / `exchange` / `market`：
  - 与 identity 不一致则 blocked。
  - 与 identity 一致可忽略 caller copy，以 identity 为准。

## 5. query_period policy

推荐支持的 explicit formats：

- 年报：
  - `2024`
  - `2024A`
  - `2024FY`
- 半年报：
  - `2024H1`
- 季报：
  - `2024Q1`
  - `2024Q2`
  - `2024Q3`

不支持的 relative expressions：

- 最近年报。
- 最新年报。
- 上一期。
- 最近一期。
- last annual report。
- latest report。
- previous period。

裁决：

- 本阶段建议不支持相对表达，避免时间依赖。
- 如果出现相对表达，future implementation 必须 blocked，reason 为 `ambiguous_query_period` 或 `relative_query_period_unsupported`。
- query_period 缺失必须 blocked。
- ambiguous period 必须 blocked。
- unsupported query_period 必须 blocked。
- 不能联网查询最新报告期。
- 不能通过系统日期推断 latest period。

period_end_date 派生规则：

- `YYYY` / `YYYYA` / `YYYYFY` -> `YYYY-12-31`。
- `YYYYH1` -> `YYYY-06-30`。
- `YYYYQ1` -> `YYYY-03-31`。
- `YYYYQ2` -> `YYYY-06-30`。
- `YYYYQ3` -> `YYYY-09-30`。

关于 `YYYYQ4`：

- 推荐 blocked。
- reason：A 股 Q4 单独季度报告通常不作为独立标准披露入口；年度报告应使用 `YYYY` / `YYYYA` / `YYYYFY`。
- 如果未来要把 `YYYYQ4` 映射到 annual_report，必须由单独 readiness gate 或 implementation review 明确批准。

## 6. requested_announcement_type policy

支持范围：

- `annual_report`
- `semiannual_report`
- `quarterly_report`
- `correction`
- `exchange_announcement`

推荐 minimal implementation 裁决：

- `annual_report`、`semiannual_report`、`quarterly_report` 作为 first implementation allowlist。
- `correction` 和 `exchange_announcement` 先保留 schema 枚举讨论，但 minimal implementation 默认 blocked，除非 request payload 明确只做 metadata-only 且另有 readiness approval。
- 本阶段建议 future minimal implementation 不启用 `correction` / `exchange_announcement`，避免 scope creep 到公告类型检索策略。

query_period 到 announcement_type 的默认映射：

- `2024` / `2024A` / `2024FY` -> `annual_report`。
- `2024H1` -> `semiannual_report`。
- `2024Q1` / `2024Q2` / `2024Q3` -> `quarterly_report`。
- `2024Q4` -> blocked，reason `unsupported_query_period` 或 `q4_period_requires_annual_report_period`。

requested_announcement_type 显式输入规则：

- 如果显式 type 与 query_period 推导 type 一致，允许。
- 如果显式 type 与 query_period 推导 type 不一致，blocked。
  - 例：`query_period=2024H1` 且 `requested_announcement_type=annual_report` 必须 blocked。
- unsupported announcement_type 必须 blocked。
- ambiguous announcement_type 必须 blocked。
- 缺失 requested_announcement_type 时，future implementation 可以由 explicit query_period 推导；若无法推导则 blocked。

## 7. allowed_source_types / source_priority / discovery_scope policy

### allowed_source_types

只允许 official source 类型：

- `cninfo_official_pdf`
- `sse_exchange_announcement`
- `exchange_official_pdf`

必须禁止：

- `provider_source_candidate`
- `mirror_source_candidate`
- `unknown_source_candidate`
- `local_official_cache`

关于 local cache：

- `local_official_cache` 不应在 request layer 启用。
- 如果 future registry / locator layer 管控 local cache，也必须在 registry/locator readiness gate 中单独批准。
- request layer 默认 blocked local cache。

### source_priority

source_priority 只能表达策略，不触发访问：

- 可以表达 official source order，例如 `["cninfo_official_pdf", "sse_exchange_announcement"]`。
- 可以表达 exchange-aware official priority。
- 不得包含 provider、mirror、unknown、local cache。
- 不得包含 URL fetch、download、parser、cache acquisition 指令。

### discovery_scope

建议只允许：

- `metadata_only`
- `official_disclosure_candidate_only`

必须禁止：

- `download`
- `parse_pdf`
- `metric_extraction`
- `provider_lookup`
- `report_generation`
- `output_write`

裁决：

- minimal implementation 默认 `discovery_scope=official_disclosure_candidate_only` 或要求 caller 显式传入 allowlisted scope。
- scope 不得触发 side effect。
- scope 只定义 future adapter 可接收的 request shape。

## 8. Normalization rules

Pure normalization rules：

- trim strings。
- normalize query_period。
- normalize requested_announcement_type。
- normalize allowed_source_types。
- normalize source_priority。
- normalize discovery_scope。
- derive `period_end_date` from explicit `query_period` only。
- derive `request_id` from explicit metadata only，或由 pure deterministic content hash 派生。
- inherit security_identity caveats without deletion。
- append request caveats，例如 no IO、no network、request-only contract。

Hard boundaries：

- no live lookup。
- no provider lookup。
- no CNInfo/SSE lookup。
- no local file read。
- no token read。
- no PDF parser。
- no output write。
- no fixture write。
- no accepted manifest write。
- no Report V1。

## 9. Fail-closed rules

未来 implementation 必须覆盖：

- missing security_identity：blocked。
- invalid security_identity schema：blocked。
- `identity_status` 非 `valid`：blocked。
- `identity_confidence` 非 `high` / `medium`：blocked。
- partial identity：blocked。
- blocked identity：blocked。
- missing stock_code：blocked。
- missing exchange：blocked。
- missing market：blocked。
- missing query_period：blocked。
- ambiguous query_period：blocked。
- unsupported query_period：blocked。
- missing requested_announcement_type 且无法由 query_period 推导：blocked。
- unsupported requested_announcement_type：blocked。
- requested_announcement_type 与 query_period 推导不一致：blocked。
- allowed_source_types 为空：blocked。
- allowed_source_types 包含 provider/mirror/unknown/local cache：blocked。
- discovery_scope 包含 download / parse / metric extraction / output write：blocked。
- source_priority 包含 provider：blocked。
- request attempts to trigger live lookup：blocked。
- request attempts to trigger provider lookup：blocked。
- request attempts to trigger PDF parser：blocked。
- request attempts to write output / fixture / manifest：blocked。
- request attempts to produce trading advice：blocked。
- `not_for_trading_advice` missing / false / non-bool：blocked。
- forbidden marker nested：blocked。

推荐 rejection reasons：

- `missing_security_identity`
- `invalid_security_identity_schema`
- `security_identity_not_valid`
- `security_identity_confidence_not_allowed`
- `missing_stock_code`
- `missing_exchange`
- `missing_market`
- `missing_query_period`
- `ambiguous_query_period`
- `unsupported_query_period`
- `missing_requested_announcement_type`
- `unsupported_requested_announcement_type`
- `announcement_type_period_mismatch`
- `invalid_allowed_source_types`
- `forbidden_source_type`
- `invalid_source_priority`
- `forbidden_discovery_scope`
- `forbidden_marker_detected`
- `not_for_trading_advice_required`
- `live_lookup_forbidden`
- `provider_lookup_forbidden`
- `pdf_parser_forbidden`
- `output_fixture_manifest_write_forbidden`
- `trading_advice_forbidden`

## 10. Safety markers

未来 request validator 必须覆盖英文和中文 marker，并执行 recursive safety scan。

英文 / mixed markers：

- token / `.env` / `tushare_token`
- provider live / AkShare / Tushare
- network / HTTP / fetch / download
- CNInfo live / SSE live
- PDF parser / table extractor / parse PDF
- metric extraction
- `official_metric_fact`
- `provider_official_conflict`
- Report V1
- accepted manifest write
- output baseline write
- fixture write
- buy / sell / hold
- target price
- portfolio / position
- technical signal
- trading advice / investment advice

中文 markers：

- 买入
- 卖出
- 持有
- 目标价
- 仓位
- 组合
- 技术信号
- 投资建议
- 下载
- 网络
- 联网
- 解析PDF
- PDF解析
- 表格抽取
- 指标抽取
- 正式研报
- 输出基线
- 写入fixture
- 写入accepted manifest

Safety marker 命中后的处理：

- 不尝试自动改写为安全 request。
- 不执行 live lookup。
- 不执行 provider lookup。
- 不触发 PDF parser。
- 不写 output / fixture / manifest。
- 返回 blocked request。

## 11. Future implementation expected files

建议优先保持 request 独立。

Production：

- `src/fundamental_skill/data_verification/official_disclosure_request.py`
- `src/fundamental_skill/data_verification/__init__.py` 仅 public API 需要时可改

Allowed only if necessary and must justify：

- `src/fundamental_skill/data_verification/schemas.py`
- `src/fundamental_skill/data_verification/validators.py`

Tests：

- `tests/test_official_disclosure_request.py`
- `tests/test_official_disclosure_request_safety.py`

默认不要修改：

- `security_identity.py`，除非发现 handoff contract bug，必须先说明。
- synthetic dry-run。
- discovery candidate。
- registry / locator。
- official verification。
- Report V1。
- provider adapter。

## 12. Future implementation forbidden files

未来 implementation 必须禁止修改或生成：

- Report V1 generator。
- provider adapter。
- accepted manifest。
- output baseline。
- fixtures。
- examples。
- `.local_experiments`。
- `tushare_token.txt`。
- `.env`。
- unrelated mojibake files。
- source download/cache acquisition。
- PDF parser。
- PDF table extractor。
- metric extraction。
- Research Pack implementation。
- Evidence Panel implementation。
- live CNInfo/SSE/AkShare/Tushare/provider calls。

## 13. Future tests

未来 implementation 至少覆盖：

- valid annual report request from high confidence identity。
- valid annual report request from medium confidence identity with caveat。
- valid semiannual report request。
- valid quarterly report request。
- unsupported Q4 policy blocked or mapped according to chosen policy。
- missing query_period blocked。
- ambiguous query_period blocked。
- unsupported announcement_type blocked。
- partial identity rejected。
- blocked identity rejected。
- company_name-only identity rejected。
- allowed_source_types with provider/mirror/unknown/local cache rejected。
- discovery_scope with download/parse/metric extraction rejected。
- source_priority with provider rejected。
- request cannot trigger live discovery。
- request cannot trigger provider lookup。
- request cannot trigger PDF parser。
- request cannot write output / fixture / manifest。
- not_for_trading_advice required。
- not_for_trading_advice=false blocked。
- not_for_trading_advice non-bool blocked。
- nested forbidden markers rejected。
- no IO / no network / no file read。

Recommended concrete examples：

- valid high confidence identity + `2024` -> annual_report request。
- valid medium confidence identity + `2024FY` -> annual_report request with inherited caveat。
- valid identity + `2024H1` -> semiannual_report request。
- valid identity + `2024Q1` -> quarterly_report request。
- valid identity + `2024Q4` -> blocked。
- valid identity + relative period `最新年报` -> blocked。
- blocked identity + `2024` -> blocked request。
- valid identity + `allowed_source_types=["provider_source_candidate"]` -> blocked。
- valid identity + `discovery_scope="download"` -> blocked。

## 14. Regression subset

未来 implementation 后建议至少运行：

- `tests/test_official_disclosure_request.py`
- `tests/test_official_disclosure_request_safety.py`
- `tests/test_security_identity.py`
- `tests/test_security_identity_safety.py`
- `tests/test_synthetic_official_disclosure_pipeline_dry_run.py`
- `tests/test_synthetic_official_disclosure_pipeline_dry_run_safety.py`
- `tests/test_official_disclosure_discovery_candidate.py`
- `tests/test_official_disclosure_discovery_candidate_safety.py`
- `tests/test_official_verification_safety.py`

如果修改 `schemas.py` / `validators.py`，还要运行 official verification schema/validator subset。

## 15. 是否需要三方审计

当前 docs-only readiness gate：

- 不需要 Gemini / DeepSeek / Kimi 三方审计。

future implementation：

- 如果只新增 isolated `official_disclosure_request.py` + tests，不改 `schemas.py` / `validators.py` / shared safety scan，可以先不默认三方审计。
- 如果修改 `schemas.py` / `validators.py`、shared safety scan、security_identity handoff boundary、query_period/announcement_type policy 的 shared behavior，建议 Gemini / DeepSeek / Kimi 三方审计。
- 如果 future implementation 触碰 live adapter handoff、registry/locator shared contracts、discovery candidate shared schema，也建议三方审计。

## 16. Acceptance criteria

Readiness gate acceptance：

- 只新增 docs readiness gate 文件。
- no production code。
- no tests。
- no output / fixtures / accepted manifest。
- no token / `.env` / `tushare_token` read。
- no mojibake handling。
- security_identity handoff policy 明确。
- query_period policy 明确。
- announcement_type policy 明确。
- allowed_source_types / discovery_scope policy 明确。
- expected files/tests 明确。
- forbidden scope 明确。
- implementation entry can be approved or rejected。

Future implementation acceptance：

- only expected production/test files changed。
- no IO。
- no network。
- no provider。
- no PDF parser。
- no output / fixture / manifest write。
- no Report V1。
- request validator fail closed。
- safety tests pass。
- security identity / synthetic dry-run / discovery regressions pass。
- no blocker remains open。

## Readiness decision summary

Recommended next implementation：

- Official Disclosure Discovery Request Contract Minimal Implementation。

Recommended implementation scope：

- Implement `official_disclosure_discovery_request.v1` only。
- Do not implement live discovery adapter。
- Do not modify `security_identity.py` unless a true handoff bug is found and reported first。
- Do not modify shared `schemas.py` / `validators.py` unless separately approved.

Policy decisions：

- security_identity handoff：only valid + high/medium accepted。
- query_period：explicit only; relative periods blocked。
- `YYYYQ4`：blocked; annual report should use `YYYY` / `YYYYA` / `YYYYFY`。
- requested_announcement_type：minimal allowlist annual/semiannual/quarterly; correction/exchange_announcement reserved unless separately approved。
- allowed_source_types：official-only。
- discovery_scope：metadata_only or official_disclosure_candidate_only only。

Known blockers：

- No blocker for readiness acceptance。
- Future implementation must still decide exact public function names and request_id deterministic derivation details。
