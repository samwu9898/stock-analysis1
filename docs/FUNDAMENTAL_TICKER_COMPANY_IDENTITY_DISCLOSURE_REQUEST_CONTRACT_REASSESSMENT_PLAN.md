# Ticker / Company Identity + Official Disclosure Request Contract Reassessment / Planning

## 1. 阶段名称和当前 baseline

阶段名称：Ticker / Company Identity + Official Disclosure Request Contract Reassessment / Planning。

最近关键 commits：

- `8576a22 docs: accept synthetic official disclosure dry-run gate`
- `5dcc082 feat: add synthetic official disclosure dry-run gate`
- `9414519 docs: add synthetic official disclosure dry-run readiness plan`
- `d815e0c docs: accept official disclosure discovery candidate contract`
- `54d9356 feat: add official disclosure discovery candidate contract`

当前 baseline：

- `official_disclosure_discovery_candidate.v1` 已具备，能够表达官方披露发现候选，不负责 live discovery。
- official source registry + locator gate 已具备，能够限定官方来源与定位结果的可信边界。
- official verification data gate 已具备，能够对官方验证链路做 fail-closed 校验。
- synthetic-only / in-memory-only dry-run assembler 已具备，能够在 no-IO、no-network、no-parser 边界内验证官方披露可信链路形状。
- 当前 discovery candidate、registry/locator、official verification、synthetic dry-run 都已完成。

本阶段性质：

- 只做 reassessment / planning。
- 只新增本 planning 文档。
- 不写 production code。
- 不写 tests。
- 不做 implementation。
- 不 commit。
- 不 push。

## 2. 当前能力地图

当前已经具备的 contract / gate / safety 能力：

- `official_disclosure_discovery_candidate.v1`：表达官方披露候选，承接 locator/registry 与后续 discovery handoff。
- `official_source_registry_entry.v1`：表达官方来源注册信息，明确 source type、authority、trust boundary。
- `official_disclosure_locator_result.v1`：表达官方来源定位结果，限定 registry 到 locator 的可接受输出。
- `synthetic_official_disclosure_pipeline_dry_run_result.v1`：表达 synthetic-only dry-run 输出，证明 pipeline 可以在内存内组合。
- official verification data gate：对官方数据路径做 schema 与 safety gate。
- recursive safety scan：对嵌套结构递归扫描，阻断 forbidden marker 与越界语义。
- provider/mirror/unknown/local cache fail-closed：对 provider、mirror、unknown、local cache 等不可信或非官方路径默认阻断。
- no-IO/no-network/no-parser boundary：当前 dry-run 不下载、不联网、不读写 output、不解析 PDF。
- synthetic-only dry-run pipeline：只使用 synthetic/in-memory 数据验证 contract continuity。

这些能力解决的是“官方披露可信链路内部是否可被安全拼接”的问题；尚未解决“用户输入如何变成可信主体身份与发现请求”的入口问题。

## 3. 当前缺口地图

当前尚未具备的入口链路能力：

- user input parsing contract。
- ticker / stock_code normalization。
- exchange inference or explicit exchange policy。
- company_name normalization。
- company alias policy。
- stock_code vs company_name mismatch policy。
- query_period normalization。
- requested_announcement_type normalization。
- `official_disclosure_discovery_request` schema。
- identity conflict blocked lane。
- discovery request -> discovery candidate handoff。
- live CNInfo/SSE discovery adapter。
- PDF parser。
- metric extraction。
- Research Pack / Evidence Panel integration。

关键缺口不是 live download 或 PDF parser，而是：在 no-IO 条件下，系统如何把用户自然语言输入 fail-closed 地转换为“主体身份 + 查询范围 + 公告类型 + 官方来源策略”。

## 4. 下一刀候选方案

### A. Security Identity Contract Thin Slice

目标：

- 定义 `security_identity.v1`。
- 处理 `stock_code`、`exchange`、`company_name`、`alias`、`market`。
- 明确 no IO、no provider、no live lookup。

价值：

- 稳定主体身份，建立后续所有 official disclosure request 的前置条件。
- 把 `600406`、`600406.SH`、`国电南瑞`、`请分析 600406 国电南瑞` 等输入先归一到身份层。
- 对 stock code / company name mismatch、unknown exchange、unsupported market、alias conflict 做 fail-closed。

风险：

- 在 no-IO 条件下，公司名唯一性和别名归一能力有限。
- 若没有内置白名单或明确 policy，company_name-only 输入可能必须 blocked 或 degraded。

### B. Official Disclosure Discovery Request Contract Thin Slice

目标：

- 定义 `official_disclosure_discovery_request.v1`。
- 处理 stock identity + query_period + announcement_type + source_policy。
- 明确 no IO、no live discovery。

价值：

- 作为未来 CNInfo/SSE discovery adapter 的输入。
- 把“身份 + 期间 + 公告类型 + 官方来源优先级”固定为可验证 contract。
- 能直接衔接现有 `official_disclosure_discovery_candidate.v1`。

风险：

- 若 identity contract 尚不稳定，request contract 会被迫内嵌身份判断。
- query_period 与 announcement_type 的规则可独立定义，但 identity mismatch 的 blocked lane 仍依赖 A。

### C. Combined Identity + Request Contract Thin Slice

目标：

- 同时定义 `security_identity.v1` 和 `official_disclosure_discovery_request.v1`。
- 在一个入口 contract 中形成完整用户输入 -> identity -> request 的 no-IO 链路。

价值：

- 形成完整入口 contract。
- 与当前 synthetic dry-run 连续性最好，可直接规划 discovery request -> discovery candidate handoff。
- 能一次性覆盖用户输入样例。

风险：

- scope 可能偏大，容易把 parsing、identity policy、period normalization、announcement type normalization、source policy、handoff safety 混在一起。
- 若 future implementation 同时改 schemas、validators、identity、request，测试面会扩大。
- 对 fail-closed 来说，拆分后的身份层更容易审计。

### D. Live Discovery Adapter Readiness Gate

目标：

- 规划 CNInfo/SSE live discovery。
- 本阶段不得实现。

价值：

- 能提前识别 live adapter 需要的 request 输入字段。

风险：

- 风险高，依赖 identity/request contract。
- 容易误触 network、HTTP、fetch、download、CNInfo live、SSE live。
- 不适合作为当前下一刀 implementation。

### E. Evidence Panel / Research Pack Bridge Plan

目标：

- 规划用户可读证据展示。

价值：

- 能把官方披露证据链未来呈现给用户。

风险：

- 过早牵引 Report V1 / output shape。
- 可能误触 Research Pack implementation、Evidence Panel implementation、正式研报、输出基线、fixture。
- 当前入口 contract 未稳定前，不宜作为下一阶段。

## 5. 候选方案评分矩阵

评分：高 / 中 / 低。风险列中，“高”表示风险更高。

| 候选 | 用户价值 | 证据链价值 | 与 synthetic dry-run 连续性 | fail-closed 风险 | scope creep 风险 | 是否需要网络 | 是否需要 provider | 是否需要 PDF parser | 是否会误触 Report V1 / output / fixtures | 可测试性 | 是否适合作为下一阶段 implementation |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A. Security Identity Contract Thin Slice | 高 | 中 | 中 | 低 | 低 | 否 | 否 | 否 | 低 | 高 | 是，最安全 |
| B. Official Disclosure Discovery Request Contract Thin Slice | 高 | 高 | 高 | 中 | 中 | 否 | 否 | 否 | 低 | 高 | 是，但最好依赖 A |
| C. Combined Identity + Request Contract Thin Slice | 最高 | 最高 | 最高 | 中 | 中到高 | 否 | 否 | 否 | 中 | 中到高 | 可行，但建议拆分 |
| D. Live Discovery Adapter Readiness Gate | 中 | 高 | 中 | 高 | 高 | 是，未来需要 | 可能需要 | 否 | 中 | 中 | 否 |
| E. Evidence Panel / Research Pack Bridge Plan | 中 | 中 | 低到中 | 中 | 高 | 否 | 否 | 否 | 高 | 中 | 否 |

结论：

- A 是最小、最 fail-closed 的下一步。
- B 是 A 稳定后的自然下一步。
- C 适合作为总体方向，但不建议一次性 implementation。
- D 和 E 都应等待 identity/request contract 稳定后再进入 readiness。

## 6. 推荐下一阶段

推荐阶段名称：

- Security Identity Contract Thin Slice / Implementation Readiness Gate。

为什么选它：

- 用户输入入口的第一不变量是主体身份，不是下载、解析或报告。
- `600406`、`600406.SH`、`国电南瑞`、`国电南瑞 2025 年报`、`请分析 600406 国电南瑞` 都必须先经过 identity normalization 与 conflict policy。
- 一旦 identity 层 fail-closed，request 层可以更干净地处理 query period、announcement type、source policy。
- A 的 allowed files 和 tests 面最窄，最容易证明 no-IO/no-network/no-parser。

为什么不选其他方案：

- 不直接选 B：request contract 依赖 stable `security_identity.v1`，否则 request 会重复承担 identity validation。
- 不直接选 C：Combined 作为目标正确，但 implementation scope 容易偏大；若身份冲突策略与 request safety scan 同时变更，审计成本升高。
- 不选 D：live discovery adapter 依赖 identity/request contract，且未来会触及网络边界。
- 不选 E：Evidence Panel / Research Pack 会过早牵引 Report V1、output shape 和用户可读展示。

是否建议拆成两个阶段：

- 是。建议拆成：
  1. `Security Identity Contract Thin Slice / Implementation Readiness Gate`
  2. `Official Disclosure Discovery Request Contract Thin Slice / Implementation Readiness Gate`

是否需要先做 Implementation Readiness Gate：

- 是。建议先做 identity 的 readiness gate，明确：
  - no-IO 条件下是否允许 company_name-only。
  - stock_code-only 是否允许构造 partial identity。
  - `600406` 的 exchange inference 是 blocked、explicit-only，还是通过 deterministic suffix policy。
  - alias conflict 与 company mismatch 的 blocked lane。
  - safety marker 是否复用 existing recursive safety scan。

是否允许直接 implementation：

- 不建议直接做 Combined implementation。
- 若 planning acceptance review 明确批准，可直接进入更小的 `Security Identity Contract Thin Slice` implementation。
- request contract implementation 建议在 identity acceptance 后进入。

future allowed files：

- Production:
  - `src/fundamental_skill/data_verification/schemas.py`
  - `src/fundamental_skill/data_verification/validators.py`
  - `src/fundamental_skill/data_verification/security_identity.py`
  - `src/fundamental_skill/data_verification/official_disclosure_request.py`
  - `src/fundamental_skill/data_verification/__init__.py` 仅 public API 需要时可改
- Tests:
  - `tests/test_security_identity.py`
  - `tests/test_official_disclosure_request.py`
  - `tests/test_official_disclosure_request_safety.py`

future forbidden files：

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

expected tests：

- identity schema 与 validator unit tests。
- stock_code / exchange / market / company_name conflict tests。
- recursive safety marker tests。
- request schema 与 validator unit tests。
- query_period 与 announcement_type normalization tests。
- request no-live/no-provider/no-parser/no-output safety tests。
- regression subset：synthetic dry-run、discovery candidate、registry/locator、official verification safety。

acceptance criteria：

- identity/request validators fail closed。
- no IO。
- no network。
- no provider。
- no PDF parser。
- no output / fixture / manifest write。
- no Report V1。
- nested forbidden markers rejected。
- synthetic dry-run/discovery/registry/locator regressions pass。
- no blocker remains open。

blocker checklist：

- 是否明确 company_name-only 在 no-IO 条件下的状态：allow partial / block / require known static map。
- 是否明确 stock_code-only 的 exchange policy：explicit-only / deterministic suffix / blocked until exchange supplied。
- 是否明确 stock_code / company_name mismatch 的 rejection reason。
- 是否明确 query_period 缺失是否 blocked，或者由 announcement_type 推导。
- 是否明确 requested_announcement_type 支持范围。
- 是否明确 request 不能触发 live discovery。
- 是否明确 `not_for_trading_advice=true` 是强制字段。
- 是否明确 forbidden marker 递归扫描覆盖中英文。

## 7. Proposed schema 草案

以下为 schema planning，不实现。

### A. `security_identity.v1`

建议字段：

- `schema_version`：固定为 `security_identity.v1`。
- `raw_user_input`：原始用户输入，仅用于审计与错误解释；必须经过 safety scan。
- `stock_code`：用户输入中的原始股票代码片段，例如 `600406` 或 `600406.SH`。
- `normalized_stock_code`：标准化后纯代码，例如 `600406`。
- `exchange`：交易所，例如 `SSE`、`SZSE`、`BSE`；未知必须 blocked。
- `market`：市场，例如 `CN_A`；unsupported market 必须 blocked。
- `company_name`：用户输入中的公司名片段。
- `normalized_company_name`：标准化公司名。
- `company_aliases`：允许的别名列表；no-IO 条件下只能来自显式输入或 future static allowlist。
- `identity_confidence`：`high` / `medium` / `low` / `blocked`，低于阈值必须 blocked。
- `identity_status`：`valid` / `partial` / `blocked`。
- `identity_conflicts`：结构化冲突列表，例如 `stock_code_company_name_mismatch`、`alias_conflict`、`ambiguous_stock_code`。
- `rejection_reason`：blocked 时的机器可读原因。
- `caveats`：限制说明，例如 no-live lookup、no-provider lookup。
- `not_for_trading_advice`：必须为布尔值 `true`。

建议状态语义：

- `valid`：身份字段满足 no-IO validation，可进入 request 构造。
- `partial`：只允许在明确 policy 下存在，例如 stock_code-only 且 exchange explicit；默认不得进入 live discovery。
- `blocked`：任何关键身份冲突、不支持市场、未知交易所、低置信度、forbidden marker 均进入 blocked lane。

### B. `official_disclosure_discovery_request.v1`

建议字段：

- `schema_version`：固定为 `official_disclosure_discovery_request.v1`。
- `request_id`：deterministic 或 caller-provided ID；不得由 live provider 生成。
- `security_identity`：嵌入 `security_identity.v1`，必须为 valid 或明确允许的 partial。
- `stock_code`：从 `security_identity` 派生的 normalized stock code。
- `exchange`：从 `security_identity` 派生的 exchange。
- `company_name`：从 `security_identity` 派生的 normalized company name。
- `query_period`：标准化查询期间，例如 `2025`、`2025Q1`、`2025H1`。
- `period_end_date`：期间结束日，例如 `2025-12-31`、`2025-03-31`。
- `requested_announcement_type`：标准化公告类型，例如 `annual_report`、`quarterly_report`、`semiannual_report`。
- `allowed_source_types`：允许来源类型，例如 `official_exchange`、`official_disclosure_site`；不得包含 provider、mirror、unknown、local cache。
- `source_priority`：官方来源优先级，例如 `SSE` before registry fallback；只能表达策略，不触发 IO。
- `discovery_scope`：`metadata_only` / `official_disclosure_candidate_only`；不得包含 download、parse、metric extraction。
- `blocked_reasons`：blocked request 的机器可读原因。
- `caveats`：no-IO、no-network、no-parser、not investment advice 等限制。
- `not_for_trading_advice`：必须为布尔值 `true`。

建议 handoff 语义：

- request 只表达“要找什么”，不执行“去哪里下载”。
- request -> discovery candidate handoff 必须经过 adapter gate。
- 在 adapter 未实现前，只能用 synthetic/in-memory candidate 做 dry-run。
- live CNInfo/SSE discovery adapter 是 future stage，不属于当前 planning 或下一步 identity implementation。

## 8. Fail-closed rules

必须覆盖并默认 blocked 的规则：

- missing stock_code and company_name：缺少股票代码且缺少公司名，blocked。
- ambiguous stock code：股票代码长度、市场或交易所无法唯一确定，blocked。
- stock_code / company_name mismatch：代码与公司名不匹配，blocked。
- unknown exchange：交易所未知或不可推断，blocked。
- unsupported market：市场不在支持范围内，blocked。
- missing query_period：构造 disclosure request 时缺少期间，blocked。
- ambiguous period：期间表达模糊，例如“最近年报”但没有当前 date policy，blocked。
- unsupported announcement_type：公告类型不在 allowlist，blocked。
- company alias conflict：多个别名指向不同主体或置信度不足，blocked。
- identity_confidence too low：低于阈值，blocked。
- forbidden marker：任意字段或嵌套字段命中 forbidden marker，blocked。
- `not_for_trading_advice` missing / false / non-bool：缺失、为 false、非布尔值均 blocked。
- request attempts to trigger live download：任何下载意图 blocked。
- request attempts to trigger provider lookup：任何 provider 查询意图 blocked。
- request attempts to trigger PDF parser：任何 PDF parser 意图 blocked。
- request attempts to write output / fixture / manifest：任何 output、fixture、manifest 写入意图 blocked。
- request attempts to produce trading advice：任何交易建议、投资建议、目标价、仓位、技术信号意图 blocked。

对用户样例的 planning 期望：

- `600406`：若 future policy 允许 deterministic exchange inference，可形成 stock_code-only identity；否则 blocked 为 `missing_exchange` 或 `ambiguous_exchange`。
- `600406.SH`：可解析 stock_code + explicit exchange；company_name 可为空或 partial，取决于 identity policy。
- `国电南瑞`：no-IO 条件下如果没有 approved static identity map，应 blocked 为 `company_name_only_requires_verified_identity_source`。
- `国电南瑞 2025 年报`：可解析 company_name + query_period + announcement_type，但 identity 仍需 verified mapping；no-IO 无法确认则 blocked。
- `请分析 600406 国电南瑞`：可解析 stock_code + company_name；必须校验 mismatch policy；不得输出 trading advice。

## 9. Safety markers

未来 identity/request validator 必须继续覆盖英文和中文 marker，并支持 recursive safety scan。

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

- 不尝试纠正为可执行请求。
- 不执行 live lookup。
- 不降级为 provider 或 mirror。
- 返回 blocked status 与 machine-readable `rejection_reason`。

## 10. Future implementation expected files

如果本 planning 被接受，未来 implementation 可考虑以下文件。

Production：

- `src/fundamental_skill/data_verification/schemas.py`
- `src/fundamental_skill/data_verification/validators.py`
- `src/fundamental_skill/data_verification/security_identity.py`
- `src/fundamental_skill/data_verification/official_disclosure_request.py`
- `src/fundamental_skill/data_verification/__init__.py` 仅 public API 需要时可改

Tests：

- `tests/test_security_identity.py`
- `tests/test_official_disclosure_request.py`
- `tests/test_official_disclosure_request_safety.py`

放置位置建议：

- 首选 `data_verification`，因为 identity/request 是官方披露可信链路的输入验证 contract，核心职责是 fail-closed validation 与 safety boundary。
- 不首选 `research_planning`，因为当前不生成研究计划、不生成 Research Pack、不决定展示形态；过早放入 `research_planning` 会模糊 verification 与 narrative planning 的边界。
- 仅当 future design 把用户自然语言意图解析作为独立研究规划层时，才考虑在 `research_planning` 放 orchestration wrapper；schema 与 validator 仍建议留在 `data_verification`。

## 11. Future implementation forbidden files

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

禁止行为：

- 不读取 token。
- 不读取 `.env`。
- 不读取 `tushare_token.txt`。
- 不联网。
- 不下载。
- 不调用 AkShare / Tushare。
- 不调用 CNInfo / SSE live。
- 不解析 PDF。
- 不生成 official_metric_fact。
- 不生成 provider_official_conflict。
- 不接 Report V1。
- 不写 accepted manifest。
- 不写 output baseline。
- 不写 fixtures。
- 不输出买入/卖出/持有。
- 不输出目标价。
- 不输出仓位。
- 不输出技术面交易信号。

## 12. Future tests

未来 implementation 至少应覆盖：

- valid stock_code only identity。
- valid stock_code + company_name identity。
- valid company_name only identity，如果 no-IO 条件下允许。
- ambiguous company_name blocked。
- stock_code / company_name mismatch blocked。
- unknown exchange blocked。
- unsupported market blocked。
- missing query_period blocked。
- ambiguous query_period blocked。
- annual / quarterly / semiannual announcement_type normalization。
- unsupported announcement_type blocked。
- valid discovery request。
- request cannot trigger live discovery。
- request cannot trigger provider lookup。
- request cannot trigger PDF parser。
- request cannot write output / fixture / manifest。
- not_for_trading_advice required。
- nested forbidden markers rejected。

建议额外覆盖：

- `not_for_trading_advice=false` blocked。
- `not_for_trading_advice="true"` blocked。
- `allowed_source_types` 包含 provider/mirror/unknown/local cache blocked。
- `discovery_scope` 包含 download、parse、metric extraction blocked。
- raw_user_input 中含 trading advice marker blocked。

## 13. Regression subset

未来 implementation 后建议至少运行：

- 新增 identity/request tests。
- synthetic dry-run tests。
- discovery candidate tests。
- registry / locator tests。
- official verification safety tests。
- 如果改 `schemas.py` / `validators.py`，运行 official verification schema/validator subset。

建议原则：

- 如果只新增 `security_identity.py`，运行新增 identity tests + official verification safety subset。
- 如果触碰 shared `schemas.py` / `validators.py`，必须扩大到 discovery candidate、registry/locator、synthetic dry-run regression。
- 不需要运行 live provider、PDF parser、Report V1、output baseline 相关测试。

## 14. 是否需要三方审计

docs-only planning：

- 当前阶段只是 docs-only planning，不需要 Gemini / DeepSeek / Kimi 三方审计。

future implementation：

- 如果 future implementation 修改 `schemas.py` / `validators.py`，建议进行 Gemini / DeepSeek / Kimi 三方审计，因为这些文件可能影响既有 official verification、discovery candidate、registry/locator gate。
- 如果涉及 identity mismatch policy / request safety scan / handoff 边界，建议进行三方审计，重点审查 fail-closed、nested forbidden marker、no-IO/no-network/no-parser 边界。
- 如果只新增 isolated `security_identity.py` 且不触碰 shared validators，可先用内部 review + regression subset；但一旦 public API 或 shared safety scan 变更，仍建议三方审计。

## 15. Acceptance criteria

Readiness / planning acceptance：

- 只新增 docs planning 文件。
- no production code。
- no tests。
- no output / fixtures / accepted manifest。
- no token / `.env` / `tushare_token` read。
- no mojibake handling。
- schema 草案清楚。
- fail-closed rules 清楚。
- expected files/tests 清楚。
- forbidden scope 清楚。
- implementation entry can be approved or rejected。

Future implementation acceptance：

- only expected production/test files changed。
- no IO。
- no network。
- no provider。
- no PDF parser。
- no output / fixture / manifest write。
- no Report V1。
- identity/request validators fail closed。
- safety tests pass。
- synthetic dry-run/discovery/registry/locator regressions pass。
- no blocker remains open。

## 推荐摘要

推荐下一阶段：

- `Security Identity Contract Thin Slice / Implementation Readiness Gate`。

建议拆分：

- 是，先 identity，后 request。

是否进入 implementation readiness gate：

- 是。

是否直接 implementation：

- 不建议直接 Combined implementation。
- 可在 planning acceptance review 后，批准更小的 Security Identity Contract implementation。

是否建议三方审计：

- 当前 docs-only planning 不需要。
- future implementation 若改 shared schemas/validators、安全扫描、handoff 边界或 identity mismatch policy，建议 Gemini / DeepSeek / Kimi 三方审计。

当前未解决 blocker：

- company_name-only 在 no-IO 条件下的允许策略。
- stock_code-only exchange inference policy。
- identity_confidence 阈值与 blocked lane 细节。
- request contract 是否接受 partial identity。
