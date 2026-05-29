# Autonomous Ticker Research Planning & Readiness Gate Implementation Plan

日期：2026-05-29

阶段：Autonomous Ticker Research Planning & Readiness Gate Implementation
Planning。

状态：仅 implementation planning。本文件不实现 production code，不新增测试，不生成
runtime artifact，不 promote fixture，不更新 accepted manifest，不 commit，不 push。

设计输入：

- `docs/FUNDAMENTAL_AUTONOMOUS_TICKER_RESEARCH_PLANNING_READINESS_GATE_DESIGN.md`
- design commit: `cb1748a2d0d194de5346b2e3e4deb4647bb86ca6`

## 0. Product Shape: Codex Skill + Research Pack

最终产品形态是 Codex Skill + Research Pack，不是 dashboard-first，不是 standalone web app，
不是手工行业模板库，也不是纯 deterministic local artifact checker。

用户用一句话 prompt 输入一个 A 股标的后，Codex 以 `fundamental_skill` 方式调用本项目能力：
使用最新模型分析能力和本项目代码工具链，自动完成 identity resolution、本地证据发现、
研究规划、宏观 / 行业 / 公司推理、readiness gate，并在证据允许范围内生成专业基本面
Research Pack。

Research Pack 至少包括：

- Professional Research Report：给用户阅读的专业基本面报告。
- Evidence Panel：展示关键判断背后的 evidence refs、candidate / review status、confidence、
  caveats。
- Readiness Card：展示 accepted / experimental / fail-closed 判断。
- Data Gap Plan：展示缺什么数据、为什么缺、需要从哪里获取、是否阻断正式报告。
- Audit Manifest：展示生成过程、artifact lineage、安全边界和 `not_for_trading_advice`。

代码职责是 deterministic evidence scaffolding：schema、validators、local artifact index、
evidence inventory、safety checks、readiness gate、fail-closed。代码不应把所有投研判断
写死成 Python 规则或行业模板。

大模型职责是 bounded research reasoning：生成 industry / supply-chain / macro hypotheses。
每个 hypothesis 必须有 evidence_refs、confidence、caveats、required_follow_up_data 和
allowed_downstream_use。hypothesis 不能成为 verified fact，也不能直接进入 Research Report V1。

## 1. 总边界

本计划把 `autonomous_ticker_research_planning_gate.v1` 的后续实现拆成可回滚、
可审查的小阶段。该 gate 是 Research Report V1 之前的 planning / readiness 层：
它可以读取本地 artifact，形成证据盘点、研究假设、数据缺口和 readiness 决策，
但不能把 hypothesis 升级为 verified fact，也不能把内容直接写入 Research Report V1。

必须明确禁止：

- 不进入 Research Report V1 L1 Evidence Integration。
- 不做 fixture promotion。
- 不改 `output/research_reports/accepted_manifest.json`。
- 不接 live CNInfo。
- 不接 live Tushare。
- 不读 token，不读环境凭证。
- 不联网。
- 不接 MCP，不读本地 MCP 配置。
- 不做 Dashboard / Batch。
- 不做 PDF / DOCX / HTML / Excel parsing。
- 不输出买卖建议、目标价、仓位、组合权重、账户操作或交易信号。

## 2. 推荐模块拆分

### 2.1 Schema Module

职责：

- 定义 planning gate 输出的严格 Pydantic schema。
- 固定 schema version: `autonomous_ticker_research_planning_gate.v1`。
- 显式定义 identity status、source status、review status、hypothesis type、
  confidence、allowed downstream use、readiness level 等 enum。
- 强制 `not_for_trading_advice=true`。
- 禁止交易建议 key 和副作用 key。
- 对所有非 data-gap hypothesis 强制 evidence refs、caveats、required
  follow-up data 和 allowed downstream use。

推荐路径：

```text
src/fundamental_skill/research_planning/autonomous_ticker_research_schema.py
```

设计原则：schema module 只依赖 Pydantic 和轻量本地常量，不导入 provider runtime、
report writer、CLI、网络或 MCP 相关模块。

### 2.2 Local Artifact Index Module

职责：

- 只从白名单本地路径构建 in-memory artifact index。
- 记录 artifact family、artifact path、stock code、company name、schema version、
  period、source status、review status、caveats、可选 SHA-256。
- 只读 accepted manifest，不能调用 `write_accepted_manifest`。
- 把历史 `output/*` 视为 artifact-state evidence，不视为新的 accepted fact。
- 保留 provider candidate、official disclosure candidate、bridge review signal 的
  candidate / review 状态。

推荐路径：

```text
src/fundamental_skill/research_planning/local_artifact_index.py
```

建议 V1 允许发现的本地根路径：

```text
output/fundamental_<code>.json
output/evidence_pack_<code>.json
output/research_questions_p1_<code>.json
output/ai_report_<code>.json
output/ground_truth_candidates/<timestamp>/<code>/fact_candidates.json
output/ground_truth_candidate_reviews/<timestamp>/<code>/candidate_review_decisions.json
output/official_disclosures/<timestamp>/<code>/*.json
output/candidate_source_bridges/<timestamp>/<code>/candidate_source_bridge_review.json
output/candidate_review_decisions_bridge_reviews/<timestamp>/<code>/candidate_review_decisions_bridge_review.json
output/provider_comparison/<timestamp>/<code>/*.json
output/research_reports/accepted_manifest.json
output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.{json,md,html}
```

未知、格式错误、越界、含 secret-like 内容的 artifact 应 fail closed 或标为 blocked，
不能 opportunistic parsing。

### 2.3 Bounded Hypothesis Generator

职责：

- 从 evidence inventory 生成公司、行业、供应链位置、宏观传导、数据缺口 hypothesis。
- Phase 4 先保持 deterministic / rule-bounded / offline，不调用 LLM，不读 token，不联网。
- 未来如需 AI hypothesis，必须另做 prompt / token / safety design。
- 正向 hypothesis 必须有 evidence refs。
- 弱证据只允许 `planning_only`、`data_collection_prioritization` 或
  `experimental_report_context_candidate`，不能变成 accepted-report fact。

推荐路径：

```text
src/fundamental_skill/research_planning/hypothesis_generator.py
```

建议只维护轻量通用 driver taxonomy：demand、price、volume、cost、inventory、
capacity、customer concentration、supplier concentration、policy、technology migration、
working capital、financing、FX、commodity input exposure。不要演变成手工维护的全行业模板库。

### 2.4 Gate Orchestrator

职责：

- 协调 identity resolution、artifact index、现有 deterministic pipeline signal、
  evidence inventory、hypothesis generator、readiness decision、fail-closed safety。
- 复用现有模块，不改现有 pipeline 行为。
- 默认返回 in-memory planning model。
- runtime output 只能在后续 wrapper phase 经批准后加入。

推荐路径：

```text
src/fundamental_skill/research_planning/autonomous_ticker_research_gate.py
```

推荐依赖：

- `FundamentalDataAdapter`
- `StockClassifier`
- `FrameworkSelector`
- `DataReadinessPlanner`
- `AnalysisContextBuilder`
- `FundamentalScoringEngine`
- `FundamentalResultAssembler` 只作为既有 artifact / deterministic signal 的读取线索，不能调用 writer。
- accepted manifest read helpers。
- candidate source bridge validator。
- bridge-aware review decision validator。

### 2.5 Validation / Safety Helpers

职责：

- 集中 no-trading-advice 校验。
- 集中 secret-like payload 检测。
- 禁止副作用 key，例如 `accepted_manifest_update`、`fixture_write_allowed`、
  `provider_primary_switch`、`research_report_v1_update`、`verified_fact`。
- 校验本地路径边界和 allowed artifact roots。
- 校验 readiness boolean 与 readiness level 的 fail-closed 关系。

推荐路径：

```text
src/fundamental_skill/research_planning/safety.py
```

应复用或对齐现有安全模式：

```text
src/fundamental_skill/validators.py
src/fundamental_skill/ai_analyst/safety.py
src/fundamental_skill/data_providers/token_leak_scanner.py
src/fundamental_skill/research_report/accepted_manifest.py
src/fundamental_skill/research_report/candidate_source_bridge.py
src/fundamental_skill/research_report/candidate_review_decisions_bridge.py
```

### 2.6 Optional CLI Or Runtime Wrapper

建议延后。

理由：CLI / runtime wrapper 天然涉及 output 写入，容易扩大副作用面。应先完成 schema、
artifact index、evidence inventory、hypothesis generator、orchestrator 的 in-memory
实现与测试，再决定是否加入 writer。

延后路径：

```text
src/fundamental_skill/research_planning/runtime_wrapper.py
scripts/run_autonomous_ticker_research_gate.py
```

若后续获批，唯一允许的 runtime output：

```text
output/autonomous_ticker_research_plans/<timestamp>/<code>/autonomous_ticker_research_planning_gate.json
```

该 wrapper 不能写 Research Report V1、fixtures、accepted manifest、provider comparison、
candidate bridges、review decisions、dashboard state、HTML / Markdown report。

## 3. 推荐文件路径

### 3.1 Production Module Paths

按阶段逐步新增：

```text
src/fundamental_skill/research_planning/__init__.py
src/fundamental_skill/research_planning/autonomous_ticker_research_schema.py
src/fundamental_skill/research_planning/safety.py
src/fundamental_skill/research_planning/local_artifact_index.py
src/fundamental_skill/research_planning/hypothesis_generator.py
src/fundamental_skill/research_planning/autonomous_ticker_research_gate.py
```

延后：

```text
src/fundamental_skill/research_planning/runtime_wrapper.py
scripts/run_autonomous_ticker_research_gate.py
```

### 3.2 Test File Paths

后续建议测试路径：

```text
tests/test_autonomous_ticker_research_schema.py
tests/test_autonomous_ticker_research_safety.py
tests/test_autonomous_ticker_research_local_artifact_index.py
tests/test_autonomous_ticker_research_evidence_inventory.py
tests/test_autonomous_ticker_research_hypotheses.py
tests/test_autonomous_ticker_research_readiness_levels.py
tests/test_autonomous_ticker_research_planning_gate.py
tests/test_autonomous_ticker_research_300475_review.py
```

测试只能使用 `tmp_path` 或经批准的 ignored `.pytest_tmp_*` 目录，不能写仓库真实
`output/`、fixtures、accepted manifest 或 report artifacts。

### 3.3 Runtime Output Paths

后续获批 wrapper 后才允许：

```text
output/autonomous_ticker_research_plans/<timestamp>/<code>/autonomous_ticker_research_planning_gate.json
```

300475 runtime review 文档可在实际 review 后新增：

```text
docs/FUNDAMENTAL_AUTONOMOUS_TICKER_RESEARCH_PLANNING_READINESS_GATE_300475_RUNTIME_REVIEW.md
```

最终 acceptance summary 文档：

```text
docs/FUNDAMENTAL_AUTONOMOUS_TICKER_RESEARCH_PLANNING_READINESS_GATE_ACCEPTANCE_SUMMARY.md
```

### 3.4 Future Fixture Paths

本阶段不得创建 fixture。后续也只有在单独 fixture promotion design 获批后才可创建：

```text
tests/fixtures/autonomous_ticker_research/300475_minimal_offline.json
tests/fixtures/autonomous_ticker_research/300475_with_official_candidates.json
tests/fixtures/autonomous_ticker_research/300475_conflict_review_required.json
tests/fixtures/autonomous_ticker_research/manifest_current_reuse_only.json
tests/fixtures/autonomous_ticker_research/provider_official_conflict.json
```

## 4. 分阶段实现顺序

### Phase 1: schema + validators

目标：建立输出契约和 safety rails，不接 artifact discovery，不接 pipeline。
Phase 1 只能实现 schema + validators，严禁引入任何运行时、模型调用、artifact scanning
或报告生成能力。

Phase 1 明确禁止：

- 无 LLM / model call。
- 无 prompt orchestration。
- 无 artifact scanning。
- 无 accepted manifest read。
- 无 provider fetch。
- 无 live CNInfo。
- 无 live Tushare。
- 无 token read。
- 无 network。
- 无 MCP。
- 无 runtime / output / report artifact generation。
- 无 fixture promotion。
- 无 Dashboard / Batch。
- 无 PDF / DOCX / HTML / Excel parsing。
- 无买卖建议、目标价、仓位、交易信号。

Expected files:

```text
src/fundamental_skill/research_planning/__init__.py
src/fundamental_skill/research_planning/autonomous_ticker_research_schema.py
src/fundamental_skill/research_planning/safety.py
tests/test_autonomous_ticker_research_schema.py
tests/test_autonomous_ticker_research_safety.py
```

Prohibited files:

```text
src/fundamental_skill/pipeline.py
src/fundamental_skill/data_adapter.py
src/fundamental_skill/stock_classifier.py
src/fundamental_skill/framework_selector.py
src/fundamental_skill/data_readiness_planner.py
src/fundamental_skill/analysis_context_builder.py
src/fundamental_skill/scoring_engine.py
src/fundamental_skill/result_assembler.py
src/fundamental_skill/research_report/*
output/*
tests/fixtures/*
output/research_reports/accepted_manifest.json
```

Tests to run:

```text
pytest tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py
pytest tests/test_token_safety.py tests/test_ai_report_safety.py tests/test_accepted_artifact_manifest.py
```

Acceptance checklist:

- schema version 固定为 `autonomous_ticker_research_planning_gate.v1`。
- 所有模型 `extra="forbid"`。
- `not_for_trading_advice` 必须为 true。
- 非 blocked data-gap hypothesis 必须有 evidence refs。
- `allowed_downstream_use` 禁止 accepted-report fact 用法。
- 禁止交易建议 key、目标价、仓位、组合权重、账户操作。
- 禁止副作用 key：manifest update、fixture write、provider primary switch、report update。
- secret-like 字符串、`.env`、credential path、remote-control URL 被拦截或 masked。
- readiness level 与 `can_generate_accepted_report` / `can_generate_experimental_report`
  的关系 fail closed。

Rollback conditions:

- schema 接受交易建议或副作用 key。
- validator 导入 provider runtime、读取 env、触达网络或 MCP 能力。
- 既有 safety / manifest 测试回归。

### Phase 2: local artifact index

目标：实现本地-only artifact discovery 和 accepted manifest read-only indexing。

Expected files:

```text
src/fundamental_skill/research_planning/local_artifact_index.py
tests/test_autonomous_ticker_research_local_artifact_index.py
```

Prohibited files:

```text
output/*
tests/fixtures/*
src/fundamental_skill/research_report/accepted_manifest.py
src/fundamental_skill/data_providers/*
scripts/*
dashboard/*
```

Tests to run:

```text
pytest tests/test_autonomous_ticker_research_local_artifact_index.py
pytest tests/test_accepted_artifact_manifest.py tests/test_candidate_source_bridge.py tests/test_candidate_review_decisions_bridge.py
```

Acceptance checklist:

- 只读 approved local roots。
- accepted manifest 只能通过 `read_accepted_manifest` 读取。
- 没有任何调用 `write_accepted_manifest` 的路径。
- manifest entry 只作为 artifact-state evidence。
- `output/*` 不被提升为 verified operating fact。
- unknown / malformed artifact 被忽略、标 partial 或 blocked。
- path traversal、absolute escape、非白名单根路径被拒绝。
- SHA-256 只对本地存在文件可选计算，不作为事实验证替代。

Rollback conditions:

- indexer 写入任何 output。
- indexer 把 manifest freshness 当成新经营事实。
- indexer 读取 live provider config、token、MCP config 或网络相关模块。

### Phase 3: deterministic evidence inventory + readiness skeleton

目标：把 artifact index 与 deterministic pipeline signal 转为 evidence inventory、
business description evidence、available / missing data artifacts 和初始 readiness skeleton。

Expected files:

```text
src/fundamental_skill/research_planning/autonomous_ticker_research_gate.py
tests/test_autonomous_ticker_research_evidence_inventory.py
tests/test_autonomous_ticker_research_readiness_levels.py
```

Prohibited files:

```text
src/fundamental_skill/research_report/research_report_v1.py
src/fundamental_skill/research_report/orchestration.py
src/fundamental_skill/research_report/generate_report.py
output/*
tests/fixtures/*
```

Tests to run:

```text
pytest tests/test_autonomous_ticker_research_evidence_inventory.py tests/test_autonomous_ticker_research_readiness_levels.py
pytest tests/test_data_adapter.py tests/test_stock_classifier.py tests/test_framework_selector.py tests/test_data_readiness_planner.py tests/test_analysis_context_builder.py
```

Acceptance checklist:

- identity resolution 保守：本地 artifact 一致才可 `resolved`。
- code-derived exchange inference 必须带 caveat。
- evidence inventory 保留 source family、schema version、path、period、review status、
  confidence、caveats、source status。
- official disclosure candidates 仍是 candidates。
- provider candidates 仍是 candidates。
- bridge artifact 仍是 source index。
- review decision 仍是 workflow signal。
- missing local artifacts 生成 data-plan rows 或 fail-closed reasons。
- 在 hypothesis phase 前，readiness 只能保守落到 `data_collection_required`、
  `classification_review_required`、`evidence_conflict_review_required` 或 `blocked`。

Rollback conditions:

- evidence inventory 把 output artifact 当 verified fact。
- official candidates 被当成 report-ready facts。
- skeleton 生成 Research Report V1 output 或调用 report writer。

### Phase 4: bounded hypothesis generator

目标：加入离线、确定性、证据约束的 hypothesis generator。

Expected files:

```text
src/fundamental_skill/research_planning/hypothesis_generator.py
tests/test_autonomous_ticker_research_hypotheses.py
```

Prohibited files:

```text
src/fundamental_skill/ai_analyst/prompt_builder.py
src/fundamental_skill/ai_analyst/runner.py
src/fundamental_skill/data_providers/*
config/industry_frameworks.yaml
output/*
tests/fixtures/*
```

Tests to run:

```text
pytest tests/test_autonomous_ticker_research_hypotheses.py
pytest tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py
```

Acceptance checklist:

- 每个正向 hypothesis 至少一个 evidence ref。
- 无证据时只输出 blocked data-gap hypothesis。
- confidence 受 evidence status 和 review status 限制。
- `accepted_for_report_candidate` 不能升级为 verified fact。
- `allowed_downstream_use` 不能强于 `experimental_report_context_candidate`。
- macro hypotheses 只描述机制和 monitoring variables，不做市场预测。
- 不存在 prompt、token、model call、network、MCP 路径。

Rollback conditions:

- hypothesis 硬套 002371 profile，且没有 target-specific evidence。
- hypothesis 含目标价、买卖、仓位、交易时点。
- generator 导入 AI runner、provider client 或 live fetch module。

### Phase 5: orchestrator

目标：把 schema、safety、artifact index、deterministic signal、hypothesis generator、
readiness decision 串成 in-memory gate。

Expected files:

```text
src/fundamental_skill/research_planning/autonomous_ticker_research_gate.py
tests/test_autonomous_ticker_research_planning_gate.py
```

Prohibited files:

```text
src/fundamental_skill/pipeline.py
src/fundamental_skill/research_report/orchestration.py
src/fundamental_skill/research_report/generate_report.py
scripts/*
output/*
tests/fixtures/*
output/research_reports/accepted_manifest.json
```

Tests to run:

```text
pytest tests/test_autonomous_ticker_research_planning_gate.py
pytest tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py tests/test_autonomous_ticker_research_local_artifact_index.py tests/test_autonomous_ticker_research_hypotheses.py tests/test_autonomous_ticker_research_readiness_levels.py
pytest tests/test_pipeline.py tests/test_research_report_v1.py tests/test_research_report_orchestration.py
```

Acceptance checklist:

- gate 默认返回 in-memory model。
- `data_adapter` 只处理本地 raw / normalized artifacts。
- `StockClassifier` 提供 deterministic baseline classification。
- `FrameworkSelector` 在 classification usable 时提供 guardrails。
- `DataReadinessPlanner` 提供 deterministic field readiness。
- `AnalysisContextBuilder` 提供 downstream safety caps、prohibited claims、blocked dimensions。
- `FundamentalScoringEngine` 只作为 deterministic quality signal。
- `FundamentalResultAssembler` 不创建、不写 Research Report V1 artifact。
- accepted manifest read-only。
- candidate source bridge 与 bridge-aware review decisions 只作为 source / workflow signals。
- deterministic classification 与 hypothesis material disagreement 时返回
  `classification_review_required`，除非本地证据支持保守选择。
- provider / official / bridge material conflict 返回 `evidence_conflict_review_required`。
- identity、official evidence、critical financials、conflict review 缺失时，accepted-report
  readiness fail closed。

Rollback conditions:

- gate 默认写 runtime output。
- gate 修改现有 deterministic pipeline modules。
- gate 调用 report generation、manifest writing、provider fetching、token reading、network、
  MCP、dashboard 或 batch flow。

### Phase 6: 300475 runtime review

目标：实现完成且用户批准 runtime 执行后，对 `300475` / 香农芯创做本地-only runtime review。

Expected files，仅在 runtime wrapper 获批后：

```text
output/autonomous_ticker_research_plans/<timestamp>/300475/autonomous_ticker_research_planning_gate.json
docs/FUNDAMENTAL_AUTONOMOUS_TICKER_RESEARCH_PLANNING_READINESS_GATE_300475_RUNTIME_REVIEW.md
```

Prohibited files:

```text
output/research_reports/*
output/research_reports/accepted_manifest.json
tests/fixtures/*
src/fundamental_skill/research_report/*
dashboard/*
```

Tests to run before runtime review:

```text
pytest tests/test_autonomous_ticker_research_300475_review.py
pytest tests/test_autonomous_ticker_research_planning_gate.py
```

输入来源：

- user query: `300475`，可带 company-name hint `香农芯创`。
- local artifact index 发现的既有本地 artifacts。
- accepted manifest read-only state。
- provider candidate artifacts，如果存在。
- official disclosure candidate artifacts，如果存在。
- candidate source bridge artifacts，如果存在。
- bridge-aware review decision artifacts，如果存在。
- deterministic pipeline output，仅当本地 normalized / raw artifact 存在。

需要发现的 local artifacts，如果存在：

```text
output/fundamental_300475.json
output/evidence_pack_300475.json
output/research_questions_p1_300475.json
output/ai_report_300475.json
output/provider_comparison/<timestamp>/300475/{akshare_fundamental.json,tushare_fundamental.json,diff_report.json,score_confidence_explainability.json}
output/ground_truth_candidates/<timestamp>/300475/fact_candidates.json
output/ground_truth_candidate_reviews/<timestamp>/300475/candidate_review_decisions.json
output/official_disclosures/<timestamp>/300475/*.json
output/candidate_source_bridges/<timestamp>/300475/candidate_source_bridge_review.json
output/candidate_review_decisions_bridge_reviews/<timestamp>/300475/candidate_review_decisions_bridge_review.json
```

避免硬套 `002371` 北方华创半导体设备 profile：

- 002371 accepted report 与 `presentation_profile=semiconductor_equipment_cycle`
  只对 002371 自身有效，不能作为 300475 默认模板。
- 300475 只有在 target-specific business evidence 支持时，才可进入半导体设备制造 frame。
- 如果证据指向电子元器件分销、存储 / 芯片供应链服务、代理或渠道业务，只能形成 caveated
  hypotheses，不能强行套设备制造逻辑。
- chip、storage、AI 等关键词不能单独证明业务兑现；缺少收入、客户、产品、库存、订单或毛利证据时，
  confidence 应 capped at low，并生成 follow-up data requirements。

Expected readiness level：

- 当前只读扫描未发现设计文档之外的明确 300475 本地 artifact。
- 在这种状态下，预期 readiness 是 `data_collection_required` 或 `blocked`。
- `identity_resolution_status` 应为 `not_found`、`ambiguous` 或 `blocked`，除非本地 artifact 支持 identity。
- `can_generate_accepted_report=false`。
- `can_generate_experimental_report=false`，除非后续存在足够 local evidence 且 safety gates 全部通过。

Expected hypotheses，如果证据支持：

- 电子元器件分销 / 代理 / 供应链服务位置。
- 存储或芯片供应链 exposure。
- AI computing demand transmission 作为 candidate driver，不作为 verified benefit。
- 库存周期与产品价格周期。
- 客户和供应商集中度。
- 毛利率波动。
- 应收账款与经营现金流质量。
- 营运资金压力。
- required follow-up data：official business-composition table、segment revenue、
  segment gross margin、major customer / supplier concentration、inventory trend、
  receivable aging、cash-flow reconciliation、official business-model text。

Fail-closed 条件：

- 没有 local artifact 支持 identity。
- ticker 与 company name 冲突。
- 只有设计文档引用 300475。
- accepted-report readiness 缺少 official disclosure evidence。
- provider / official / bridge sources 在 business、period、unit、denominator、source lineage
  上有 material conflict。
- critical financial fields 缺失。
- hypotheses 缺少 evidence refs。
- 输出含交易建议、目标价、仓位、token、secret-like strings、`.env`、credential path、
  remote-control URL、live-provider requirement 或 verified-fact marker。

### Phase 7: acceptance summary

目标：记录已实现内容、未实现内容、测试结果、runtime review 结果和仍然关闭的边界。

Expected files:

```text
docs/FUNDAMENTAL_AUTONOMOUS_TICKER_RESEARCH_PLANNING_READINESS_GATE_ACCEPTANCE_SUMMARY.md
```

Prohibited files:

```text
output/research_reports/accepted_manifest.json
tests/fixtures/*
config/industry_frameworks.yaml
dashboard/*
```

Tests to run:

```text
pytest tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py tests/test_autonomous_ticker_research_local_artifact_index.py tests/test_autonomous_ticker_research_evidence_inventory.py tests/test_autonomous_ticker_research_hypotheses.py tests/test_autonomous_ticker_research_readiness_levels.py tests/test_autonomous_ticker_research_planning_gate.py tests/test_autonomous_ticker_research_300475_review.py
pytest tests/test_pipeline.py tests/test_research_report_v1.py tests/test_research_report_orchestration.py tests/test_accepted_artifact_manifest.py tests/test_candidate_source_bridge.py tests/test_candidate_review_decisions_bridge.py
```

Acceptance checklist:

- phase-specific tests 通过。
- existing deterministic pipeline tests 通过。
- Research Report V1 tests 无 baseline drift。
- accepted manifest 未变。
- 无 fixture promotion。
- 无 live provider、token、network、MCP 路径。
- 如有 runtime output，只在 approved planning path。
- 300475 在 local evidence 缺失时 fail closed。

Rollback conditions:

- accepted manifest 有任何变更。
- fixture promotion 发生。
- live provider、token、network、MCP 行为出现。
- 未获批的 Research Report V1 output 或 baseline drift 出现。

## 5. 与现有 pipeline 的接入方式

### 5.1 `data_adapter`

使用 `FundamentalDataAdapter` 仅处理既有本地 raw / provider fundamental artifacts。
缺失输入转为 `missing_data_artifacts` 和 `required_data_plan`，不要在 adapter 中新增 provider fetching。

### 5.2 `StockClassifier`

使用 `StockClassifier` 作为 deterministic baseline。AI / bounded hypotheses 可补充或挑战 baseline，
但不能 silent override。material disagreement 返回 `classification_review_required`，除非本地证据支持保守选择。

### 5.3 `FrameworkSelector`

仅当 deterministic classification usable 时使用 `FrameworkSelector` 取得 guardrails。不要扩展
`config/industry_frameworks.yaml` 去维护全行业模板或强行安置 300475。

### 5.4 `DataReadinessPlanner`

使用 `DataReadinessPlanner` 计算 baseline framework 下的 deterministic field readiness。gate 在此基础上增加
source-readiness checks：official evidence presence、candidate-only status、bridge conflict status、
accepted manifest freshness、artifact availability、offline-boundary availability。

### 5.5 `AnalysisContextBuilder`

使用 `AnalysisContextBuilder` 的 blocked dimensions、confidence caps、prohibited claims、
required risks 和 safe downstream permission 概念，映射为 caveats、required data rows、fail-closed reasons。

### 5.6 `FundamentalScoringEngine`

仅在 normalized inputs、classification、framework、readiness、context 都可用时，把
`FundamentalScoringEngine` 作为 deterministic data-quality / confidence signal。它不是交易信号，
也不能单独决定 accepted-report readiness。

### 5.7 `FundamentalResultAssembler`

不使用 `FundamentalResultAssembler` 生成新的 Research Report V1 artifact。如发现既有 assembled result，
只能读取 status、missing fields、data source metadata 作为 artifact-state evidence。

### 5.8 Accepted Manifest

只读使用：

```text
output/research_reports/accepted_manifest.json
```

允许 helper：

```text
read_accepted_manifest
validate_accepted_manifest
get_manifest_entry
get_freshness_status
is_manifest_entry_usable_by_default
build_freshness_warning
verify_manifest_entry_hashes
```

禁止：

```text
write_accepted_manifest
build_accepted_manifest for runtime mutation
adding 300475 to the manifest
changing accepted paths
changing artifact hashes
using freshness as operating fact evidence
```

### 5.9 Candidate Source Bridge

使用 `candidate_source_bridge.v1` 作为 source index。它可以告诉 gate provider / official
candidate artifacts 是否存在、有哪些 review priorities、是否有 conflicts。它不是 merge layer，
也不是 verified fact store。

### 5.10 Bridge-Aware Review Decisions

使用 `candidate_review_decisions_bridge.v1` 作为 workflow state：

- `manual_review_required` 限制 readiness。
- `blocked_by_caveat` 对 material fields 可 fail closed。
- `needs_more_evidence` 生成 data-plan rows。
- `conflict_requires_review` 触发 conflict-review readiness。
- `accepted_for_report_candidate` 仍是 candidate status，仍需未来 Research Report V1 L1 Evidence
  Integration 后才可进入 report。

## 6. 风险点与控制

### 6.1 AI Hypothesis 过度自信

风险：hypothesis 看起来像 verified fact。

控制：

- evidence refs 必填。
- confidence 受 source status / review status 限制。
- 禁止 `accepted_report_fact`。
- validator 拦截 verified-fact marker。

### 6.2 Artifact Index 误把 Output 当 Accepted Fact

风险：历史 `output/*` artifact 被当成事实。

控制：

- 每条 evidence 记录 source family、source status、review status、caveats。
- accepted manifest 只证明 artifact lineage / freshness state，不证明新经营事实。

### 6.3 Accepted Manifest 被误写

风险：gate 更新 accepted report inventory。

控制：

- index / orchestrator 不导入 writer。
- tests monkeypatch `write_accepted_manifest`，一旦调用即失败。
- acceptance 前检查 git diff，manifest 必须无变更。

### 6.4 Official Candidates 被误当 Verified Facts

风险：`auto_candidate` 或 `accepted_for_report_candidate` 被升级。

控制：

- evidence refs 保留 candidate status。
- `accepted_for_report_candidate` 自动带 caveat：
  `requires_later_report_v1_l1_evidence_design`。
- accepted-report readiness 仍需 formal readiness 条件。

### 6.5 Local Artifact 不完整导致假通过

风险：缺失 artifact 被忽略，readiness 误通过。

控制：

- 缺失 artifact family 必须进入 `missing_data_artifacts` 和 `required_data_plan`。
- accepted-report readiness 必须同时满足 identity、official evidence 或 usable accepted artifact、
  critical financials、conflict closure、offline boundary safety。

### 6.6 Prompt / Token / Secret 泄露

风险：未来 AI 或 artifact ingestion 泄露 secret。

控制：

- Phase 4 先 deterministic offline。
- safety module 复用 token-leak scanner pattern。
- 测试覆盖 secret-like string、`.env`、credential path、bearer token、remote-control URL。

### 6.7 Future Live Provider 边界被提前打开

风险：CNInfo、Tushare、network、MCP、token access 提前进入。

控制：

- research planning modules 不导入 provider runtime。
- live-only data 缺失时返回 `data_collection_required` 或 `blocked`。
- 测试断言 planning modules 不含 live provider / token / MCP import path。

## 7. 下一阶段建议

建议下一步进入 Phase 1: schema + validators implementation。

原因：Phase 1 只建立 contract 和 safety rails，范围小、可回滚、不会接 artifact discovery、
pipeline orchestration 或 runtime writer。Phase 1 完成并通过测试后，再进入 Phase 2 local artifact index。
