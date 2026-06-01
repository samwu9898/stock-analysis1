# Security Identity Contract Thin Slice / Implementation Readiness Gate

## 1. 阶段名称和当前 baseline

阶段名称：Security Identity Contract Thin Slice / Implementation Readiness Gate。

最近关键 commits：

- `550616c docs: add ticker company identity request reassessment plan`
- `8576a22 docs: accept synthetic official disclosure dry-run gate`
- `5dcc082 feat: add synthetic official disclosure dry-run gate`
- `9414519 docs: add synthetic official disclosure dry-run readiness plan`
- `d815e0c docs: accept official disclosure discovery candidate contract`

当前 baseline：

- Ticker / Company Identity + Official Disclosure Request Contract Reassessment Plan 已完成、commit、push。
- 当前推荐下一阶段是 Security Identity Contract Thin Slice / Implementation Readiness Gate。
- official verification data gate、official source registry + locator gate、official disclosure discovery candidate contract、synthetic-only / in-memory-only dry-run assembler 均已具备。
- 当前缺口是用户输入到 `security_identity.v1` 的 fail-closed 身份入口 contract。

本阶段性质：

- 只做 readiness gate。
- 只新增本 docs readiness gate 文件。
- 不写 production code。
- 不写 tests。
- 不做 implementation。
- 不 commit。
- 不 push。

## 2. 本阶段目标

本阶段为 future `security_identity.v1` 的 minimal implementation 锁定边界，明确以下事项：

- schema fields。
- normalization rules。
- no-IO constraints。
- exchange policy。
- company_name-only policy。
- stock_code-only policy。
- company alias policy。
- mismatch policy。
- identity confidence policy。
- fail-closed rules。
- safety markers。
- expected implementation files/tests。
- acceptance criteria。

核心边界：

- `security_identity.v1` 只负责证券身份归一化与 fail-closed validation。
- 本阶段和 future identity implementation 不负责 official disclosure request contract。
- 不做 live lookup。
- 不做 provider lookup。
- 不读本地 source file。
- 不读 token、`.env`、`tushare_token.txt`。
- 不调用 AkShare / Tushare / CNInfo / SSE live。
- 不下载。
- 不解析 PDF。
- 不生成 official metric fact。
- 不生成 trading advice。

## 3. `security_identity.v1` schema 草案

### Required fields

- `schema_version`
  - 固定值：`security_identity.v1`。
  - 必须存在。

- `raw_user_input`
  - 原始用户输入或 caller-provided raw string。
  - 必须存在，可以为空字符串但不能为非字符串。
  - 必须经过 recursive safety scan。

- `identity_confidence`
  - 枚举：`high`、`medium`、`low`、`blocked`。
  - 必须存在。

- `identity_status`
  - 枚举：`valid`、`partial`、`blocked`。
  - 必须存在。

- `identity_conflicts`
  - 结构化 conflict code 列表。
  - 必须存在；无冲突时为空列表。

- `caveats`
  - 限制说明列表。
  - 必须存在；无 caveat 时为空列表。

- `not_for_trading_advice`
  - 必须存在。
  - 必须为布尔值 `true`。
  - 缺失、`false`、字符串 `"true"`、数字 `1` 均 blocked。

### Conditional fields

- `stock_code`
  - 用户输入中的原始股票代码片段，例如 `600406`、`600406.SH`。
  - 如果输入包含股票代码则必须存在。
  - 如果 company_name-only 输入被处理为 partial 或 blocked，可为空。

- `normalized_stock_code`
  - 标准化后纯 6 位 A 股代码，例如 `600406`。
  - 当 `identity_status=valid` 且身份来自代码时必须存在。
  - invalid stock code 时为空并 blocked。

- `exchange`
  - 标准化交易所，例如 `SSE`、`SZSE`、`BSE`。
  - 当 `identity_status=valid` 且身份来自代码时必须存在。
  - unknown exchange、unsupported suffix、prefix/suffix mismatch 时 blocked。

- `market`
  - 标准化市场，例如 `CN_A`。
  - 当 `identity_status=valid` 且身份来自代码时必须存在。
  - unsupported market 时 blocked。

- `company_name`
  - 用户输入中的公司名片段。
  - 如果输入包含公司名则保留为 raw company name。
  - 必须经过 safety scan。

- `normalized_company_name`
  - 纯 normalization 后的公司名。
  - 只有在显式输入公司名，或 future approved static identity map 提供公司名时才可存在。
  - no-IO 条件下不得通过 provider/live/source lookup 推导。

### Optional fields

- `company_aliases`
  - 公司别名列表。
  - 当前 minimal implementation 默认空列表。
  - 只能来自显式输入或 future approved static identity map。
  - 不得通过 live lookup、provider lookup、CNInfo/SSE lookup、local file read 推导。

- `rejection_reason`
  - 当 `identity_status=blocked` 时必须存在。
  - 当非 blocked 时应为空或不存在，建议实现中固定为空字符串或 `None`，保持 schema 可预测。

### Recommended status semantics

- `valid`
  - stock code、exchange、market 已按 deterministic/no-IO policy 归一化。
  - safety scan 通过。
  - `not_for_trading_advice=true`。
  - 可以进入 future request contract 的身份输入，但 request contract 仍必须执行自己的 no-live/no-provider/no-parser gate。

- `partial`
  - 有用户提供的公司名或未验证字段，但缺少可验证的 code/exchange/market 身份。
  - 当前推荐不允许进入 request contract。
  - 可用于给用户解释需要更明确的股票代码或交易所。

- `blocked`
  - 任何关键字段非法、冲突、低置信度、forbidden marker、交易建议意图、live/provider/parser/output write 意图均进入 blocked。
  - 不允许进入 request contract。

## 4. 必须裁决的 policy

### A. stock_code-only policy

裁决：

- 推荐允许 `600406` 在 no-IO 条件下通过 A 股代码前缀 deterministic policy 推断为 `SSE`。
- `600406` 应归一为：
  - `normalized_stock_code=600406`
  - `exchange=SSE`
  - `market=CN_A`
  - `identity_status=valid`
  - `identity_confidence=medium`
  - `normalized_company_name` 为空
  - caveat 包含 `exchange inferred by deterministic CN A-share prefix policy; company identity not verified`

推荐 deterministic policy：

- `600` / `601` / `603` / `605` / `688` -> `SSE`
- `000` / `001` / `002` / `003` / `300` / `301` -> `SZSE`
- `8` / `4` 开头 -> `BSE`

允许该 policy 的理由：

- 这是纯字符串规则，不需要 IO、network、provider、local file read。
- 它只推断交易所和市场，不声称验证公司名称。
- 对用户输入 `600406` 这类常见 A 股代码，能形成可审计的 security identity。

必须列出的 caveat：

- deterministic prefix inference is not live verification。
- company identity is not verified。
- symbol existence is not verified。
- future request/discovery adapter must still fail closed before any live lookup。

若未来 implementation 不采用该 policy：

- `600406` 必须 blocked 为 `missing_exchange` 或 `ambiguous_exchange`。
- 但本 readiness gate 推荐采用 deterministic prefix inference，因为它在 no-IO 边界内提供更高用户价值，且不会引入 provider/live 风险。

### B. explicit exchange policy

裁决：

- 支持以下 suffix normalization：
  - `.SH` -> `SSE`
  - `.SS` -> `SSE`
  - `.SSE` -> `SSE`
  - `.SZ` -> `SZSE`
  - `.SZSE` -> `SZSE`
  - `.BJ` -> `BSE`
  - `.BSE` -> `BSE`

样例：

- `600406.SH` -> `normalized_stock_code=600406`、`exchange=SSE`、`market=CN_A`。
- `600406.SS` -> `normalized_stock_code=600406`、`exchange=SSE`、`market=CN_A`。
- `000001.SZ` -> `normalized_stock_code=000001`、`exchange=SZSE`、`market=CN_A`。

unsupported suffix：

- 例如 `.US`、`.HK`、`.NYSE`、`.NASDAQ`、`.L`，当前 CN_A-only minimal implementation 必须 blocked。
- `rejection_reason=unsupported_exchange_suffix` 或 `unsupported_market`。

exchange 与 code prefix mismatch：

- `600406.SZ` 必须 blocked，原因 `code_prefix_exchange_mismatch`。
- `000001.SH` 必须 blocked，原因 `code_prefix_exchange_mismatch`。
- `688001.SZ` 必须 blocked，原因 `code_prefix_exchange_mismatch`。
- `430000.SH` 必须 blocked，原因 `code_prefix_exchange_mismatch` 或 `unknown_exchange_for_prefix`，具体取决于 prefix policy。

### C. company_name-only policy

裁决：

- no-IO 条件下，不允许 company_name-only 进入 `valid` identity。
- 如果没有 approved static identity map，company_name-only 必须是 `partial` 或 `blocked`；本 readiness gate 推荐 future minimal implementation 直接 blocked。
- `国电南瑞` 作为 company_name-only 输入，在没有 approved static identity map 时应 blocked：
  - `identity_status=blocked`
  - `identity_confidence=blocked`
  - `rejection_reason=company_name_only_requires_approved_static_identity_map`
  - `identity_conflicts=[]`
  - `normalized_company_name=国电南瑞`
  - caveat 包含 `no IO; no provider lookup; no live exchange lookup; company name cannot be verified`

为什么推荐 blocked 而不是 partial：

- partial identity 很容易被误用为 request input。
- company name-only 在 A 股中存在简称、曾用名、集团名、子公司名、同名简称等歧义。
- 没有 approved static identity map 时，系统无法 fail-closed 地确认唯一证券主体。

partial identity 是否能进入 request：

- 推荐不能。
- future request contract 只接受 `identity_status=valid` 的 `security_identity.v1`。
- 如果未来要允许 partial 进入 request，必须由另一个 Official Disclosure Discovery Request readiness gate 明确批准，并增加 request-level blocked lane。

### D. stock_code + company_name policy

裁决：

- 如果没有 approved static identity map，future minimal implementation 不能验证 stock_code 和 company_name 是否匹配。
- 推荐以 stock_code/exchange/market 构造 `valid` security identity，同时把 company_name 标记为 unverified user-provided company hint，并加入 caveat。
- 不应因为无法验证公司名而阻断有效 stock_code 身份，除非出现可检测冲突或 forbidden marker。

样例：

- `请分析 600406 国电南瑞`
  - 若 `600406` 通过 deterministic prefix 推断为 `SSE`：
    - `normalized_stock_code=600406`
    - `exchange=SSE`
    - `market=CN_A`
    - `normalized_company_name=国电南瑞`
    - `identity_status=valid`
    - `identity_confidence=medium`
    - `identity_conflicts=[]`
    - caveat 包含 `company name supplied by user but not verified against stock code`
  - 同时必须拒绝“分析”被解释为交易建议；只要 raw input 未要求买入/卖出/目标价/仓位/技术信号，可以保留为 identity parsing 语境。

什么时候 blocked：

- company_name 或 raw input 命中 forbidden marker。
- stock_code invalid。
- exchange suffix unsupported。
- code prefix / explicit exchange mismatch。
- future approved static identity map 存在且能确认 stock_code / company_name mismatch。
- alias conflict 可检测。
- 用户要求 live lookup、provider lookup、PDF parser、output write、fixture write、manifest write、trading advice。

mismatch 如何表达：

- `identity_conflicts` 包含 `stock_code_company_name_mismatch`。
- `rejection_reason=stock_code_company_name_mismatch`。
- `identity_status=blocked`。
- caveat 包含匹配依据，例如 `mismatch detected by approved static identity map`，不得引用 live/provider。

caveat 如何表达：

- 没有 approved static map 时：
  - `company name supplied by user but not verified against stock code`
  - `security identity derived from stock code and exchange only`
- 有 approved static map 且匹配时：
  - `company name matched by approved static identity map`
- 有 approved static map 且不匹配时：
  - blocked，不进入 request。

### E. identity_confidence policy

裁决：

- `high`
  - explicit stock code + explicit supported exchange。
  - prefix 与 exchange 一致。
  - market supported。
  - safety scan 通过。
  - 若 company name 存在，则必须来自 approved static map 或经 approved static map 验证匹配；否则不得为 high。

- `medium`
  - stock_code-only 通过 deterministic prefix 推断 exchange。
  - stock_code + user-provided company_name，但没有 approved static map 可验证匹配。
  - explicit stock code + exchange 有效，但 company_name 是 unverified user hint。
  - medium 可进入 future request contract，但 request contract 必须保留 caveat 并禁止 live side effect。

- `low`
  - company_name-only。
  - alias-only。
  - code-like fragment 不完整。
  - exchange 不明确但可能可猜。
  - low 必须 blocked，不得进入 request。

- `blocked`
  - invalid stock code。
  - unsupported market。
  - unknown exchange。
  - unsupported suffix。
  - code prefix / exchange mismatch。
  - verifiable stock_code / company_name mismatch。
  - alias conflict。
  - forbidden marker。
  - `not_for_trading_advice` invalid。
  - live/provider/parser/output/trading advice intent。

什么状态可进入 request contract：

- 推荐仅 `identity_status=valid` 可进入 future request contract。
- `identity_confidence=high` 和 `medium` 可进入 request contract。
- `identity_confidence=low` 和 `blocked` 不可进入 request contract。

partial identity 是否可进入 request：

- 推荐不允许。
- `partial` 仅用于解释缺口，不作为 request input。

## 5. Normalization rules

Pure normalization rules：

- trim strings。
- collapse leading/trailing whitespace。
- 保留中文公司名原文，不做繁简转换、不做别名猜测。
- normalize stock code：
  - 接受 6 位数字。
  - 接受 6 位数字加 supported suffix。
  - 拒绝非 6 位数字、含字母主体代码、含路径/URL/token-like fragment 的代码。
- normalize exchange suffix：
  - 大小写不敏感。
  - `.SH` / `.SS` / `.SSE` -> `SSE`。
  - `.SZ` / `.SZSE` -> `SZSE`。
  - `.BJ` / `.BSE` -> `BSE`。
- normalize market：
  - 当前 minimal implementation 只支持 `CN_A`。
  - `SSE` / `SZSE` / `BSE` 均映射到 `CN_A`。
- normalize company name：
  - trim。
  - 去除输入解析产生的明显空白。
  - 不通过 live/provider/source lookup 补全公司全称。
  - 不通过本地 source file 读取别名。
- normalize aliases：
  - 只允许来自显式输入或 future approved static identity map。
  - 当前 minimal implementation 默认 `company_aliases=[]`。

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

## 6. Fail-closed rules

未来 implementation 必须覆盖并默认 fail closed：

- missing stock_code and company_name：
  - blocked。
  - `rejection_reason=missing_stock_code_and_company_name`。

- invalid stock_code：
  - blocked。
  - `rejection_reason=invalid_stock_code`。

- unsupported market：
  - blocked。
  - `rejection_reason=unsupported_market`。

- unknown exchange：
  - blocked。
  - `rejection_reason=unknown_exchange`。

- unsupported exchange suffix：
  - blocked。
  - `rejection_reason=unsupported_exchange_suffix`。

- code prefix / exchange mismatch：
  - blocked。
  - `rejection_reason=code_prefix_exchange_mismatch`。

- company_name-only without approved static map：
  - blocked。
  - `rejection_reason=company_name_only_requires_approved_static_identity_map`。

- stock_code / company_name mismatch when verifiable：
  - blocked。
  - `rejection_reason=stock_code_company_name_mismatch`。

- alias conflict：
  - blocked。
  - `rejection_reason=company_alias_conflict`。

- identity_confidence too low：
  - blocked。
  - `rejection_reason=identity_confidence_too_low`。

- forbidden marker：
  - blocked。
  - `rejection_reason=forbidden_marker_detected`。

- `not_for_trading_advice` missing / false / non-bool：
  - blocked。
  - `rejection_reason=not_for_trading_advice_required`。

- attempts to trigger live lookup：
  - blocked。
  - `rejection_reason=live_lookup_forbidden`。

- attempts to trigger provider lookup：
  - blocked。
  - `rejection_reason=provider_lookup_forbidden`。

- attempts to trigger PDF parser：
  - blocked。
  - `rejection_reason=pdf_parser_forbidden`。

- attempts to write output / fixture / manifest：
  - blocked。
  - `rejection_reason=output_fixture_manifest_write_forbidden`。

- attempts to produce trading advice：
  - blocked。
  - `rejection_reason=trading_advice_forbidden`。

## 7. Safety markers

未来 identity validator 必须覆盖英文和中文 marker，并执行 recursive safety scan。

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

- 不尝试自动改写成安全请求。
- 不执行 live lookup。
- 不执行 provider lookup。
- 不触发 parser。
- 不写 output / fixture / manifest。
- 返回 `identity_status=blocked`。

## 8. Future implementation expected files

建议优先保持 identity 独立，不做 request contract。

Production：

- `src/fundamental_skill/data_verification/security_identity.py`
- `src/fundamental_skill/data_verification/__init__.py` 仅 public API 需要时可改

Allowed only if necessary and must justify：

- `src/fundamental_skill/data_verification/schemas.py`
- `src/fundamental_skill/data_verification/validators.py`

Tests：

- `tests/test_security_identity.py`
- `tests/test_security_identity_safety.py`

不建议本阶段实现：

- `src/fundamental_skill/data_verification/official_disclosure_request.py`
- `tests/test_official_disclosure_request.py`
- `tests/test_official_disclosure_request_safety.py`

Implementation shape 建议：

- 独立 dataclass 或 typed dict schema。
- 独立 parser/normalizer/validator 函数。
- 复用 shared safety scan 只有在无需扩大 shared surface 时才考虑。
- 如果复用 shared validators 需要修改 `validators.py`，必须在 commit message 或 docs 中说明理由。

## 9. Future implementation forbidden files

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
- `official_disclosure_request.py`，除非另一个 readiness gate 批准。

禁止行为：

- 不读取 token。
- 不读取 `.env`。
- 不读取 `tushare_token.txt`。
- 不联网。
- 不下载。
- 不读取本地 source file 来做身份映射。
- 不调用 AkShare / Tushare。
- 不调用 CNInfo / SSE live。
- 不解析 PDF。
- 不写 accepted manifest。
- 不写 output baseline。
- 不写 fixtures。
- 不生成正式研报。
- 不输出买入/卖出/持有。
- 不输出目标价。
- 不输出仓位。
- 不输出技术面交易信号。

## 10. Future tests

未来 implementation 至少覆盖：

- valid explicit stock_code + exchange。
- valid stock_code-only if deterministic inference is allowed。
- invalid stock_code blocked。
- unsupported exchange suffix blocked。
- code prefix / exchange mismatch blocked。
- company_name-only blocked or partial according to chosen policy。
- stock_code + company_name partial / caveat according to chosen policy。
- alias conflict blocked。
- missing stock_code and company_name blocked。
- not_for_trading_advice required。
- not_for_trading_advice=false blocked。
- not_for_trading_advice non-bool blocked。
- nested forbidden markers rejected。
- live lookup / provider lookup / PDF parser / output write intent rejected。
- no IO / no network / no file read。

Recommended concrete examples：

- `600406` -> valid, `SSE`, `CN_A`, medium confidence, company unverified caveat。
- `600406.SH` -> valid, `SSE`, `CN_A`, high confidence if no unverified company name。
- `600406.SS` -> valid, `SSE`, `CN_A`。
- `000001.SZ` -> valid, `SZSE`, `CN_A`。
- `600406.SZ` -> blocked, `code_prefix_exchange_mismatch`。
- `600406.US` -> blocked, `unsupported_exchange_suffix`。
- `国电南瑞` -> blocked, `company_name_only_requires_approved_static_identity_map`。
- `请分析 600406 国电南瑞` -> valid security identity from code, medium confidence, company name unverified caveat, no trading advice output。
- nested `{"note": "download PDF"}` -> blocked。
- nested `{"x": {"y": "目标价"}}` -> blocked。

## 11. Regression subset

未来 implementation 后建议至少运行：

- `tests/test_security_identity.py`
- `tests/test_security_identity_safety.py`
- `tests/test_synthetic_official_disclosure_pipeline_dry_run.py`
- `tests/test_synthetic_official_disclosure_pipeline_dry_run_safety.py`
- `tests/test_official_disclosure_discovery_candidate.py`
- `tests/test_official_disclosure_discovery_candidate_safety.py`
- `tests/test_official_verification_safety.py`

如果修改 `schemas.py` / `validators.py`，还要运行 official verification schema/validator subset。

建议原则：

- 如果只新增 isolated `security_identity.py` + tests，回归范围可保持上述 minimal subset。
- 如果改 shared safety scan 或 shared validators，必须扩大回归范围。
- 不需要运行 provider、PDF parser、Report V1、output baseline、fixtures 相关测试。

## 12. 是否需要三方审计

当前 docs-only readiness gate：

- 不需要 Gemini / DeepSeek / Kimi 三方审计。

future implementation：

- 如果只新增 isolated `security_identity.py` + `tests/test_security_identity.py` + `tests/test_security_identity_safety.py`，且不改 `schemas.py` / `validators.py` / shared safety scan，可以先不默认三方审计。
- 如果修改 `schemas.py` / `validators.py`、shared safety scan、identity mismatch policy 影响 handoff 边界，建议 Gemini / DeepSeek / Kimi 三方审计。
- 如果 future implementation 引入 approved static identity map，也建议三方审计，重点审查 map 来源、更新流程、mismatch policy、company_name-only 进入 valid 的边界。

## 13. Acceptance criteria

Readiness gate acceptance：

- 只新增 docs readiness gate 文件。
- no production code。
- no tests。
- no output / fixtures / accepted manifest。
- no token / `.env` / `tushare_token` read。
- no mojibake handling。
- stock_code-only policy 明确。
- company_name-only policy 明确。
- explicit exchange policy 明确。
- identity_confidence policy 明确。
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
- identity validator fail closed。
- safety tests pass。
- synthetic dry-run/discovery regressions pass。
- no blocker remains open。

## Readiness decision summary

Recommended next implementation：

- Security Identity Contract Thin Slice Minimal Implementation。

Recommended implementation scope：

- Implement `security_identity.v1` only。
- Do not implement `official_disclosure_discovery_request.v1` yet。

Policy decisions：

- stock_code-only deterministic exchange inference：allow for CN_A using prefix policy。
- company_name-only no-IO identity：blocked without approved static identity map。
- stock_code + company_name without static map：valid security identity from code, company name retained only as unverified user hint with caveat。
- partial identity into request：not allowed。
- low confidence identity：blocked。

Known blockers:

- No blocker for readiness acceptance.
- Future implementation must still decide exact public function names and whether to keep all logic inside isolated `security_identity.py`.
