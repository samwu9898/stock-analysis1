# fundamental_skill 输出规范

## Neutral Naming Compatibility v1

`FundamentalAnalysisResult` now includes neutral aliases while preserving the existing public schema contract:

- `analyst_summary` is the recommended neutral fundamental-analysis summary.
- `downstream_review_hint` is the recommended neutral follow-up review hint inside `invalidation_conditions`.
- `trader_summary` is deprecated but retained for backward compatibility with historical JSON.
- `action_hint_for_trader` is deprecated but retained for backward compatibility with historical JSON.

New v1 outputs mirror `analyst_summary` to `trader_summary`, and `downstream_review_hint` to `action_hint_for_trader`, using neutral user-visible wording. AI layer and Dashboard display should prefer the new fields and use old fields only as fallback for legacy files.

Current project boundaries remain unchanged: this project does not implement `trader_skill`, does not implement `technical_skill`, does not connect to trading accounts, and does not output trading advice.

Research Intelligence P0 is an upper AI analyst artifact above the deterministic `fundamental_skill` pipeline. It reads the existing evidence pack and writes independent research-question artifacts:

- `output/research_intelligence_<code>.json`
- `output/research_questions_<code>.json`
- `output/research_questions_<code>.md`

It does not modify `FundamentalAnalysisResult`, deterministic pipeline behavior, classifier output, connector mappings, scoring, readiness, result assembly, or HTML rendering. It is a rule-triggered, evidence-gated research question discovery layer, not a trading system, not a technical-analysis module, and not a report renderer.

## 1. 定位

`fundamental_skill` 是 A 股基本面分析 Skill。它只负责判断公司基本面、行业景气、财务质量、估值、风险、催化和后续跟踪指标。

它不判断买卖点，不输出交易指令，不给仓位建议，不给目标价，不负责最终交易纪律。它的输出对象是后续综合评估层；当前项目不实现 `trader_skill`，也不引入技术面继续评估。

HTML report generator 属于 AI analyst layer 的上层展示能力，不属于 deterministic `fundamental_skill` pipeline。它把 evidence pack 和模型生成的结构化 `FundamentalHtmlReport` JSON 渲染为纯基本面中文 HTML 研报，不改变 deterministic pipeline，不修改 connector / classifier / scoring / readiness，不输出交易建议，不做技术面。HTML report 和 visual audit 产物写入 `output/`，包括 `output/reports/` 和 `output/visual_audit/`，不进入 git。
Research Intelligence P0 也属于 AI analyst layer 的上层 artifact，但它不接 HTML Report 主链路；它只把 evidence pack 转成 research intelligence pack 和 research question set，用于发现业务-财务交叉验证问题、规则触发矛盾和 IR / manual review 问题清单。

`fundamental_skill` 只能表达基本面状态：

- `supportive`：基本面支持继续跟踪或进入后续综合评估。
- `neutral`：基本面没有明显否定，但支持力度不足。
- `negative`：基本面不支持。
- `insufficient_data`：数据不足，不能下判断。

## 2. 三 Agent 架构

- `fundamental_skill`：基本面分析员，输出结构化 JSON，覆盖公司基本面、行业、财务、估值、风险、催化和跟踪项。
- `technical_skill`：不在当前项目实现；不得在当前阶段引入趋势、量价、形态、波动或技术风险分析。
- `trader_skill`：不在当前项目实现；未来若单独设计，必须另行定义边界和接口。

本规范只覆盖 `fundamental_skill`。

## 3. 输出字段解释

- `schema_version`：固定为 `fundamental.v1`。
- `stock_code`：股票代码。
- `stock_name`：股票名称，可为空。
- `analysis_date`：分析日期。
- `strategy_type`：基本面适配的策略类型。
- `status`：基本面是否支持后续模块评估。
- `confidence`：结论置信度。
- `confidence_reason`：置信度理由。
- `fundamental_score`：基本面评分，0-100。
- `business_summary`：公司业务摘要。
- `key_drivers`：核心驱动因素。
- `financial_quality`：财务质量，包括收入、利润、毛利率、现金流、债务压力和一次性损益风险。
- `valuation_view`：估值观察，包括估值水平、方法、同业比较和历史分位。
- `industry_cycle`：行业周期位置、趋势和外部变量。
- `risk_flags`：风险项，每项包含严重程度、证据和跟踪方法。
- `catalysts`：催化因素，每项包含类型、证据、预期时间和不确定性。
- `must_track_indicators`：后续综合评估应持续跟踪的基本面指标。
- `invalidation_conditions`：基本面判断失效条件，只能提示重新评估、暂停支持判断或更新分析。
- `thesis_check`：对用户假设的验证情况。
- `suitable_strategy_type`：适配的策略描述，不是交易指令。
- `analyst_summary`：推荐字段，中性的简短基本面摘要，不得包含交易动作。
- `trader_summary`：deprecated，保留用于 backward compatibility；新展示层不应优先使用。
- `data_sources`：数据来源、抓取时间、周期、成功状态和错误。
- `data_timestamp`：本次结构化输出对应的数据时间戳。
- `missing_fields`：缺失字段列表。
- `valid_until`：结论有效期，可为空。
- `refresh_triggers`：需要刷新基本面分析的触发条件。
- `raw_data_path`：原始数据路径，可为空。

## 4. confidence 含义

- `high`：关键数据较完整，证据一致性强，缺失字段不影响核心判断。
- `medium`：数据基本可用，但存在部分缺失、滞后或证据冲突。
- `low`：关键数据不足或证据冲突明显，只能给低置信度判断。

## 5. strategy_type 含义

- `resource_swing`：资源弹性股，基本面主要受商品价格、供需周期和成本弹性影响。
- `resource_core`：资源核心底仓，强调资源禀赋、成本曲线、现金流和分红能力。
- `right_trend_growth`：高景气趋势成长股，强调行业趋势、收入增长和利润兑现。
- `semiconductor_cycle`：半导体国产替代/周期股，强调库存周期、国产替代、订单和资本开支。
- `stable_growth`：稳健成长，强调稳定收入、现金流、ROE 和治理质量。
- `satellite_communication_infrastructure`：卫星通信基础设施，强调在轨卫星、轨位/频段、转发器/带宽资源、容量利用率、客户合同、资产寿命、折旧和现金流稳定性。
- `theme_only`：题材属性强但基本面支撑弱。
- `unknown`：无法分类。

## 6. 禁止输出内容

`fundamental_skill` 的 JSON、Markdown 或任何最终输出不得包含以下交易指令或承诺性表述：

- 买入
- 卖出
- 满仓
- 梭哈
- 加仓
- 减仓
- 清仓
- 止损
- 止盈
- 目标价
- 保证收益
- 必涨
- 必跌

## 7. Mock JSON 示例：兴业银锡 resource_swing

以下示例为 mock 数据，仅用于说明结构，不调用实时数据，不代表真实研究结论。

```json
{
  "schema_version": "fundamental.v1",
  "stock_code": "000426",
  "stock_name": "兴业银锡",
  "analysis_date": "2026-05-15",
  "strategy_type": "resource_swing",
  "status": "supportive",
  "confidence": "medium",
  "confidence_reason": "资源品价格、主营结构和财务质量数据基本可用，但部分同业比较和最新产量数据缺失。",
  "fundamental_score": 72,
  "business_summary": "公司业务对银、锡等资源品价格较敏感，基本面弹性主要来自商品价格周期和矿山经营效率。",
  "key_drivers": ["资源品价格周期", "矿山产量释放", "单位成本控制"],
  "financial_quality": {
    "revenue_trend": "收入受资源品价格影响较大",
    "profit_trend": "利润弹性高于收入",
    "margin_trend": "毛利率随金属价格波动",
    "cashflow_quality": "经营现金流需结合价格周期跟踪",
    "debt_pressure": "需要继续观察有息负债变化",
    "one_off_profit_risk": "暂未纳入一次性损益明细",
    "score": 68,
    "evidence": [
      {
        "source": "mock_financial_statement",
        "metric_name": "gross_margin",
        "value": "mock",
        "period": "2025",
        "interpretation": "资源品价格上行时利润率具备弹性。"
      }
    ]
  },
  "valuation_view": {
    "valuation_level": "reasonable",
    "valuation_method": "资源股周期估值框架",
    "peer_comparison": "同业比较数据为 mock",
    "historical_percentile": "unknown",
    "score": 62,
    "evidence": []
  },
  "industry_cycle": {
    "cycle_position": "upcycle",
    "industry_trend": "资源品价格处于偏强阶段的 mock 假设",
    "key_external_variables": ["银价", "锡价", "美元指数", "矿山供给扰动"],
    "score": 75,
    "evidence": []
  },
  "risk_flags": [
    {
      "name": "商品价格回落风险",
      "severity": "high",
      "evidence": [],
      "monitor_method": "跟踪银、锡价格与库存变化"
    }
  ],
  "catalysts": [
    {
      "name": "资源品价格偏强",
      "catalyst_type": "commodity_price",
      "evidence": [],
      "expected_timeframe": "未来1-2个季度",
      "uncertainty": "medium"
    }
  ],
  "must_track_indicators": [
    {
      "name": "银价",
      "current_value": null,
      "importance": "high",
      "monitor_frequency": "weekly",
      "reason": "直接影响利润弹性"
    }
  ],
  "invalidation_conditions": [
    {
      "condition": "资源品价格持续弱于基本面假设",
      "evidence_needed": "连续多个观察周期价格与库存数据恶化",
      "downstream_review_hint": "需要后续分析层复核",
      "action_hint_for_trader": "需要后续分析层复核"
    }
  ],
  "thesis_check": {
    "user_thesis": "资源价格上行带动利润弹性",
    "thesis_support": "partially_supported",
    "supporting_evidence": [],
    "opposing_evidence": [],
    "missing_evidence": ["最新产量数据", "完整同业估值数据"]
  },
  "suitable_strategy_type": "资源弹性基本面观察",
  "trader_summary": "基本面对进一步评估形成支持，但存在高风险，需要重新评估商品价格和产量数据变化。",
  "data_sources": [
    {
      "name": "mock_sample",
      "source_type": "derived",
      "fetched_at": "2026-05-15T00:00:00",
      "period": "mock",
      "success": true,
      "error_message": null
    }
  ],
  "data_timestamp": "2026-05-15T00:00:00",
  "missing_fields": ["latest_output_volume", "peer_valuation"],
  "valid_until": null,
  "refresh_triggers": ["商品价格大幅波动", "季度报告发布", "矿山产量披露"],
  "raw_data_path": null
}
```

## 8. Data Adapter

### 8.1 流程

`fundamental_skill` 的数据链路分为三层：

```text
raw data JSON -> NormalizedFundamentalInput -> FundamentalAnalysisResult
```

- `raw data JSON`：现有项目由 AkShare 采集后保存的原始 `blocks` 数据。
- `NormalizedFundamentalInput`：Data Adapter 标准化后的输入对象，只做字段整理、来源记录和缺失记录。
- `FundamentalAnalysisResult`：后续阶段的最终基本面结论对象，本阶段不生成。

### 8.2 NormalizedFundamentalInput 字段

- `schema_version`：固定为 `fundamental_input.v1`。
- `stock_code`：股票代码；缺失时使用 `UNKNOWN` 并记录缺失。
- `stock_name`：股票名称，可为空。
- `generated_at`：标准化对象生成时间或 raw meta 生成时间。
- `data_cutoff`：数据截止日，可为空。
- `basic_info`：基础公司信息。
- `financial_metrics`：财务指标列表。
- `valuation_metrics`：估值指标。
- `business_composition`：主营构成，segments 保留为宽松 dict。
- `latest_news`：新闻或公告条目。
- `raw_blocks`：完整原始 blocks，便于追溯。
- `block_status`：每个 block 的行数、状态、最新期间、错误信息。
- `data_sources`：数据来源列表。
- `missing_fields`：标准化后仍缺失的重要字段。
- `adapter_warnings`：适配过程中的结构告警。
- `raw_data_path`：原始 JSON 路径。

### 8.3 Adapter 边界

Data Adapter 不做分析、不做评分、不做交易判断。它不会生成 `supportive / neutral / negative`，不会生成 `fundamental_score`，也不会输出买卖、仓位、目标价、止损等交易建议。

### 8.4 missing_fields 与 adapter_warnings

- `missing_fields` 表示下游基本面分析可能需要但当前无法稳定获得的字段。
- `adapter_warnings` 表示 raw JSON 结构本身存在问题，例如缺少 `meta`、没有识别到 `blocks`、需要从文件名推断股票代码等。

### 8.5 CLI 示例

```bash
python -m src.fundamental_skill.data_adapter \
  --input tests/fixtures/raw_with_meta_blocks.json \
  --output output/normalized_input_000426.json
```

CLI 会打印股票代码、股票名称、缺失字段、适配告警和 block 状态摘要。该命令不调用 AkShare，不调用 LLM，不生成 HTML。

## 9. 股票分类器和分析框架选择器

### 9.1 职责边界

`stock_classifier` 只做股票基本面类型分类，不做评分，不输出 `supportive / neutral / negative`，不输出 `FundamentalAnalysisResult`。

`framework_selector` 只根据分类结果返回分析框架模板，不做结论，不做交易判断。

二者均为 deterministic rule-based 模块，不调用 LLM，不调用实时 AkShare。

### 9.2 为什么不能用同一套基本面框架

不同股票的基本面驱动不同：

- 资源弹性股重点看商品价格、产量、成本曲线和周期风险。
- 高景气成长股重点看订单、收入增速、客户资本开支和估值消化。
- 半导体周期股重点看国产替代、资本开支周期、存货和研发商业化。
- 稳健成长股重点看订单稳定性、现金流、ROE 和资产负债率。
- 题材属性股要先验证题材和主营业务是否相关，不能把新闻热度当成基本面。

因此分类器先决定“应该用哪套基本面问题清单”，后续 analyzer/scorer 再基于该框架展开。

### 9.3 strategy_type 业务含义

- `resource_swing`：资源弹性股，利润对商品价格和周期波动高度敏感。
- `resource_core`：资源核心底仓，多矿种、大储量、现金流和分红属性更强。
- `right_trend_growth`：高景气趋势成长股，例如 AI 算力、光模块、PCB、服务器、液冷等方向。
- `semiconductor_cycle`：半导体国产替代/周期股，受订单、资本开支、研发和库存周期影响。
- `stable_growth`：稳健成长股，强调订单稳定、现金流、ROE 和政策投资周期。
- `theme_only`：题材属性较强但基本面支撑弱，需验证利润兑现路径。
- `unknown`：数据不足或无法稳定分类。

### 9.4 分类置信度

分类结果包含 `confidence_score` 和 `confidence`：

- `confidence_score >= 75`：`high`
- `50 <= confidence_score < 75`：`medium`
- `confidence_score < 50`：`low`

如果只有新闻命中，置信度最高只能到 `medium`。`unknown` 通常为 `low`。

### 9.5 alternative_types

`alternative_types` 记录其他有明显命中的类型。它用于提示后续分析可能存在框架冲突，例如：

- 资源股同时命中 `resource_swing` 和 `resource_core`。
- AI 产业链股票同时命中 `right_trend_growth` 和 `semiconductor_cycle`。
- 电力设备公司同时命中 `stable_growth` 和 `right_trend_growth`。

后续 analyzer 可以根据 `alternative_types` 做交叉检查，但不能直接把它当作交易判断。

### 9.6 CLI 示例

```bash
python -m src.fundamental_skill.stock_classifier \
  --input tests/fixtures/classifier_resource_swing.json
```

CLI 会先调用 `FundamentalDataAdapter`，再调用 `StockClassifier` 和 `FrameworkSelector`，输出股票代码、股票名称、分类、置信度、理由、备选类型、缺失字段和框架重点。

该命令不输出交易建议，不输出技术指标，不生成 HTML。

## 10. Data Readiness Planner

### 10.1 定位

`DataReadinessPlanner` 用于判断当前数据是否足够支撑后续基本面分析。它读取：

- `NormalizedFundamentalInput`
- `StockClassificationResult`
- `FundamentalFramework`

并输出 `DataReadinessPlan`。

它不是基本面评分器，不输出 `FundamentalAnalysisResult`，不输出 `supportive / neutral / negative`，不做交易判断。

### 10.2 与其他模块的关系

```text
raw data
  -> FundamentalDataAdapter
  -> NormalizedFundamentalInput
  -> StockClassifier
  -> FrameworkSelector
  -> DataReadinessPlanner
  -> 后续 scorer/analyzer
```

`stock_classifier` 决定股票适合哪类基本面框架，`framework_selector` 给出该框架的关注重点，`data_readiness_planner` 检查该框架所需字段是否可用。

### 10.3 readiness_score 和 fundamental_score 的区别

AI datacenter boundary samples make this distinction explicit: the boundary cap applies to `readiness_score` only. If a sample lacks structured real order, customer, delivery, or sub-type revenue validation, `readiness_score` can be capped at `<= 39` and `readiness_level` can become `insufficient`. That does not mean final `fundamental_score` must also be `<= 39`; final `fundamental_score` is produced later by weighted scoring and result assembly.

`readiness_score` 衡量数据准备度，只回答“数据够不够”。它不评价公司好坏，不代表投资价值。

`fundamental_score` 是后续阶段才会实现的基本面评分，用来评价基本面质量。二者不能混用。

分类置信度和数据准备度也是两个概念。分类器可能高置信度判断一家公司属于资源弹性股，但如果缺少扣非净利润、经营现金流或商品价格，`readiness_level` 仍然可能是 `weak`。

### 10.4 readiness_level

- `sufficient`：数据基本足够，且没有 critical 缺失。
- `usable_with_warnings`：数据可用，但存在重要缺失或部分字段缺失。
- `weak`：数据较弱，后续分析必须显著降低置信度。
- `insufficient`：数据不足，不应做高置信度基本面分析。

严格封顶规则：

- 存在任意 critical 缺失时，最高只能是 `usable_with_warnings`。
- critical 缺失不少于 2 个时，最高只能是 `weak`。
- critical 缺失不少于 3 个时，最高只能是 `insufficient`。
- `strategy_type=unknown` 或分类置信度为 `low` 时，最高只能是 `weak`。
- 财务指标整体为空时，最高只能是 `weak`。
- critical 主营构成缺失时，最高只能是 `usable_with_warnings`；若同时有 critical 财务字段缺失，最高只能是 `weak`。

特殊框架规则：

- `resource_swing`：缺扣非净利润或经营现金流时，最高 `usable_with_warnings`；二者同时缺失时，最高 `weak`。
- `right_trend_growth`：缺毛利率时，最高 `usable_with_warnings`；缺营收增速或净利润增速时，最高 `weak`。
- `semiconductor_cycle`：缺存货时，最高 `usable_with_warnings`；存货和毛利率同时缺失时，最高 `weak`。
- `stable_growth`：缺经营现金流或 ROE 时，最高 `usable_with_warnings`；二者同时缺失时，最高 `weak`。

### 10.5 critical_missing_fields

`critical_missing_fields` 表示当前框架中最关键的数据缺口。例如资源弹性股缺少扣非净利润、经营现金流或主营构成，会直接影响利润质量和业务暴露判断。

### 10.6 analysis_blockers

`analysis_blockers` 用自然语言说明哪些分析暂时不能做。例如：

- 缺少经营现金流：无法判断利润质量。
- 缺少主营构成：无法判断核心业务暴露。
- 缺少商品价格：资源股周期判断不完整。

### 10.7 CLI 示例

```bash
python -m src.fundamental_skill.data_readiness_planner \
  --input tests/fixtures/readiness_resource_swing_missing_cashflow.json \
  --output output/readiness_plan_000426.json
```

该命令会读取 mock/raw JSON，经 Adapter、Classifier、FrameworkSelector 后生成 Data Readiness Plan。它不调用 AkShare，不调用 LLM，不生成 HTML，不输出交易建议。

## 11. Analysis Context Builder

### 11.1 定位

`AnalysisContextBuilder` 将前序结构合成为后续 analyzer/scorer 的安全上下文：

```text
NormalizedFundamentalInput
+ StockClassificationResult
+ FundamentalFramework
+ DataReadinessPlan
  -> AnalysisContext
```

它不是基本面结论，不评价公司好坏，不输出最终分析结果，也不做交易判断。

### 11.2 与 readiness/scorer/analyzer 的关系

`DataReadinessPlan` 告诉系统“数据够不够”。`AnalysisContext` 进一步把数据缺口转成可执行约束：

- 哪些分析维度允许；
- 哪些分析维度必须降低置信度；
- 哪些结论禁止生成；
- 哪些风险必须写入；
- 哪些评分维度不能给高分。

后续 analyzer/scorer 应消费 `AnalysisContext`，避免在数据缺失时给出过度确定的判断。

### 11.3 overall_context_quality

- `strong`：上下文质量强，数据准备度和分类置信度都较好。
- `usable`：上下文可用，但必须带限制使用。
- `weak`：上下文较弱，只能做低置信度分析。
- `insufficient`：上下文不足，不应做完整基本面分析。

### 11.4 max_overall_confidence

`max_overall_confidence` 是后续 analyzer/scorer 的整体置信度上限：

- `readiness_level=insufficient` 时只能是 `low`。
- `readiness_level=weak` 时不能高于 `low`。
- `readiness_level=usable_with_warnings` 时不能高于 `medium`。
- `strategy_type=unknown` 时不能高于 `low`。

### 11.5 required_risks、prohibited_claims、scoring_constraints

- `required_risks`：后续风险模块必须包含的风险。
- `prohibited_claims`：后续 analyzer 禁止生成的结论类型。
- `scoring_constraints`：后续 scorer 的维度分数上限，多个约束合并时取更低上限。

### 11.6 防止过度自信

当缺少扣非净利润、经营现金流、毛利率、存货、主营构成或商品价格等核心字段时，`AnalysisContext` 会限制对应维度。例如缺少经营现金流时，财务质量维度会被限制，且禁止断言现金流质量强。

### 11.7 CLI 示例

```bash
python -m src.fundamental_skill.analysis_context_builder \
  --input tests/fixtures/context_resource_swing_weak.json \
  --output output/analysis_context_000426.json
```

该命令会依次执行 Adapter、Classifier、FrameworkSelector、DataReadinessPlanner 和 AnalysisContextBuilder。它不调用 AkShare，不调用 LLM，不生成 HTML，不输出交易建议。

## 12. Rule-based Fundamental Scoring Engine

### 12.1 定位

`FundamentalScoringEngine` 是规则型基本面评分材料生成器。它读取：

- `NormalizedFundamentalInput`
- `StockClassificationResult`
- `FundamentalFramework`
- `DataReadinessPlan`
- `AnalysisContext`

并输出 `FundamentalScoringResult`。

它不是最终基本面结论，不输出最终分析结果，不做交易判断。

### 12.2 weighted_total_score 与 final fundamental_score 的区别

`weighted_total_score` 是规则型中间分，用于给后续 analyzer/scorer 提供结构化评分材料。它不是最终 `fundamental_score`，不能直接解释为基本面支持或不支持。

最终 `fundamental_score` 只能在后续最终 analyzer 阶段生成，并且必须消费本阶段输出的约束、风险和证据。

### 12.3 为什么必须受 AnalysisContext 约束

如果缺少经营现金流、扣非净利润、毛利率、存货、主营构成或商品价格等核心字段，评分引擎不能因为其他指标好看就给相关维度高分。

因此每个维度先生成 `raw_score`，再应用 `AnalysisContext.scoring_constraints`、维度权限和整体置信度上限，得到 `constrained_score`。

### 12.4 strategy_type 权重

权重来自 `config/fundamental_scoring.yaml`：

- `resource_swing`：更重视行业周期和财务质量。
- `resource_core`：更重视业务质量、财务质量、行业周期和风险可控度。
- `right_trend_growth`：更重视业务质量、财务质量、行业周期和催化强度。
- `semiconductor_cycle`：维度较均衡，但重点关注财务、周期和业务质量。
- `stable_growth`：更重视财务质量、风险可控度和数据质量。
- `theme_only`：更重视风险可控度和数据质量。
- `unknown`：更重视数据质量。

### 12.5 维度含义

- `business_quality`：业务清晰度、主营构成和分类匹配度。
- `financial_quality`：增长、盈利能力、ROE、现金流和扣非利润。
- `industry_cycle`：行业景气和策略类型关键变量。
- `valuation_reasonableness`：估值合理性，但不会简单认为低 PE 就好。
- `catalyst_strength`：催化材料强度，当前只做保守规则。
- `risk_control`：风险可控度，分数越高表示风险越可控。
- `data_quality`：数据准备度转化而来的数据质量分。

### 12.6 CLI 示例

```bash
python -m src.fundamental_skill.scoring_engine \
  --input tests/fixtures/scoring_resource_swing_weak.json \
  --output output/scoring_000426.json
```

该命令会依次执行 Adapter、Classifier、FrameworkSelector、DataReadinessPlanner、AnalysisContextBuilder 和 ScoringEngine。它不调用 AkShare，不调用 LLM，不生成 HTML，不输出交易建议。

### 12.7 当前限制

- 不做最终结论。
- 不做行业横向比较。
- 不接实时外部变量。
- 新闻不做语义理解。
- 评分规则仍需后续结合真实样本迭代。

## 13. Final Fundamental Result Assembler

### 13.1 定位

`FundamentalResultAssembler` 是 `fundamental_skill` 的最终结构化输出装配层。它消费 `NormalizedFundamentalInput`、`StockClassificationResult`、`FundamentalFramework`、`DataReadinessPlan`、`AnalysisContext` 和 `FundamentalScoringResult`，并输出第一阶段定义的 `FundamentalAnalysisResult`。

该结果供后续综合评估层使用，但仍然不是交易建议，也不包含技术面判断。当前项目不实现 `trader_skill`。

### 13.2 FundamentalAnalysisResult 的用途

`FundamentalAnalysisResult` 回答的是“基本面材料是否支持进入后续综合评估”。它包含公司业务摘要、财务质量、估值视角、行业周期、风险、催化、跟踪指标、证伪条件、数据来源、缺失字段和置信度。

### 13.3 status 含义

- `supportive`：基本面支持进入后续综合评估。
- `neutral`：基本面没有明显否定，但支持力度不足。
- `negative`：基本面不支持继续评估，或风险明显高于逻辑。
- `insufficient_data`：数据不足，不能可靠判断。

这些状态只表达基本面 Skill 对后续评估的支持程度，不代表任何交易动作。

`supportive` 不等于交易建议，也不自动代表高置信度。若仍存在关键验证项，结果可以是 `supportive` 但 `confidence` 只能是 `medium` 或 `low`。

### 13.4 confidence 生成规则

`confidence` 由 `AnalysisContext.max_overall_confidence`、`FundamentalScoringResult.score_confidence` 和 `DataReadinessPlan.readiness_level` 共同决定。只要上下文或评分置信度为 `low`，结果置信度为 `low`；`readiness_level=weak/insufficient` 时结果置信度为 `low`；只有上下文、评分和数据准备度都达到高标准时，才允许 `high`。

此外，关键数据缺失会对 `confidence` 做保守封顶：

- 资源股缺少商品价格数据时，周期判断不能高置信度。
- 高景气成长股缺少毛利率时，盈利能力判断不能高置信度。
- 半导体缺少存货时，周期判断不能高置信度。
- 稳健成长缺少经营现金流或 ROE 时，稳健性判断不能高置信度。
- high severity 的数据缺失风险存在时，最终置信度不得为 `high`。

### 13.5 fundamental_score 与交易评分的区别

For final result semantics, do not confuse a readiness cap with a final-score cap. `status=insufficient_data` caps final `fundamental_score` at `<= 50`; it does not inherit every lower upstream `readiness_score` cap. In particular, AI datacenter boundary cases with `readiness_score <= 39` can still have final `fundamental_score` above 39, as long as the final result remains `status=insufficient_data`, `confidence=low`, and `fundamental_score <= 50`.

本阶段的 `fundamental_score` 来自规则型 `weighted_total_score`，表示基本面结构化材料的规则评分。它不是交易评分，不是收益预测，也不是任何交易动作依据。若数据不足、置信度低或分类未知，会进一步封顶。

### 13.6 Neutral Summary 边界

`analyst_summary` 是推荐的中性基本面摘要字段，必须说明 status、confidence、主要风险和数据缺口。`trader_summary` 已 deprecated，但为了 historical JSON backward compatibility 仍保留并镜像同一段中性文本。当前项目不实现 `trader_skill`，不连接交易账户，也不输出交易建议。

如果置信度被关键数据缺失封顶，`analyst_summary` / `trader_summary` 必须说明封顶原因。例如资源股缺商品价格时，需要提示外部价格变量未验证；`supportive + medium` 时，需要提示仍存在关键验证项或数据限制。

### 13.7 CLI 示例

```bash
python -m src.fundamental_skill.result_assembler \
  --input tests/fixtures/result_resource_swing_good.json \
  --output output/fundamental_000426.json
```

该命令会依次执行 Adapter、Classifier、FrameworkSelector、DataReadinessPlanner、AnalysisContextBuilder、ScoringEngine 和 ResultAssembler。它不调用 AkShare，不调用 LLM，不生成 HTML。

### 13.8 当前限制

- 结果仍然是规则型装配，不做自然语言深度推理。
- 新闻和公告只作为保守材料，不做语义级验证。
- 行业横向比较、真实商品价格和外部变量仍需后续数据源增强。
- `supportive/neutral/negative/insufficient_data` 仅是基本面支持程度，不是交易结论。

## 14. Pipeline Facade

### 14.1 定位

`FundamentalSkillPipeline` 是 `fundamental_skill` 的统一调用入口。调用方只需要提供 raw JSON 文件或 dict，就可以得到最终 `FundamentalAnalysisResult`。

它只做 deterministic pipeline 编排，不接 LLM，不调用 AkShare，不生成 HTML，也不实现 `trader_skill`。

### 14.2 调用流程

执行顺序固定为：

```text
raw JSON
  -> FundamentalDataAdapter
  -> StockClassifier
  -> FrameworkSelector
  -> DataReadinessPlanner
  -> AnalysisContextBuilder
  -> FundamentalScoringEngine
  -> FundamentalResultAssembler
  -> assert_valid_result
  -> FundamentalAnalysisResult
```

### 14.3 Python 用法

```python
from src.fundamental_skill.pipeline import FundamentalSkillPipeline

pipeline = FundamentalSkillPipeline()
result = pipeline.analyze_from_file("tests/fixtures/pipeline_sanhua_mock.json")
trace = pipeline.last_trace
```

也可以使用 `analyze_from_dict(raw_data)`。

### 14.4 CLI 示例

```bash
python -m src.fundamental_skill.pipeline \
  --input tests/fixtures/pipeline_sanhua_mock.json \
  --output output/fundamental_sanhua.json
```

### 14.5 pipeline_trace

`pipeline.last_trace` 保存最近一次运行的调试摘要，包括分类、readiness、context、scoring 和最终结果字段：

- `stock_code`
- `stock_name`
- `strategy_type`
- `classification_confidence`
- `readiness_score`
- `readiness_level`
- `context_quality`
- `max_overall_confidence`
- `weighted_total_score`
- `score_confidence`
- `final_status`
- `final_confidence`
- `final_score`
- `warnings`

Trace 用于审计和调试，不进入最终结果。

### 14.6 边界

Pipeline 不是交易系统。它不输出交易动作，不判断技术面，不生成仓位或价格建议，只把基本面 Skill 的结构化输出稳定地交给后续模块。

## 15. advanced_manufacturing_growth

`advanced_manufacturing_growth` 表示高端制造成长股，适用于汽车热管理、机器人执行器、工业自动化、精密制造核心零部件、新能源车供应链和机器人产业链公司。

适用标的示例包括三花智控、拓普集团、汇川技术、双环传动、中大力德、鸣志电器、绿的谐波、埃斯顿、禾川科技、柯力传感、汉威科技等。

它与 `right_trend_growth` 的区别是：后者更偏 AI 算力、光模块、PCB、服务器、液冷、数据中心等高景气科技链；前者更偏汽车零部件、机器人零部件、工业自动化和精密制造。它与 `stable_growth` 的区别是：后者更偏电网设备、输配电、订单稳定和现金流稳健；前者更强调新业务兑现、客户验证、毛利率和估值预期。

对于三花智控，mock 数据中主营包含汽车热管理、制冷控制元器件、机器人执行器相关零部件，因此更适合归入 `advanced_manufacturing_growth`。但机器人相关业务如果只是新闻、布局或预期，不能写成已经确定兑现的主营收入，必须继续验证订单和收入。

### 15.1 Advanced Manufacturing Risk Guard

高端制造成长股即使财务数据完整，也必须额外识别新业务验证风险：

- 机器人业务不能因为新闻、布局或预期就当作确定收入贡献，必须验证订单、收入和收入占比。
- 大客户供应链逻辑需要客户收入占比和订单持续性验证。
- 高估值成长股需要后续业绩增长消化，不能只依赖机器人、新能源车或高端制造预期。
- 传统主业、新能源车业务和机器人业务占比需要拆分验证。

三花智控 mock 中机器人执行器相关业务被标记为布局/待验证，同时新闻包含特斯拉供应链和大客户逻辑，且 PE TTM 较高，因此 pipeline 会加入机器人业务兑现验证不足、大客户依赖验证不足和估值预期消化风险。

## 16. Regression Suite

Sample Regression Suite 用于防止后续规则扩展造成分类漂移或风险识别退化。它使用 mock raw JSON 样本，通过 `FundamentalSkillPipeline` 跑完整链路，并校验关键字段。

回归样本覆盖：

- 资源弹性股：兴业银锡、洛阳钼业
- 资源核心底仓：紫金矿业
- 高景气趋势成长股：中际旭创、胜宏科技
- 半导体国产替代/周期股：北方华创、澜起科技
- 高端制造成长股：三花智控、拓普集团
- 稳健成长股：思源电气、国电南瑞
- 题材属性股：题材样本A
- 数据不足：数据不足样本B

回归测试不做完整 JSON snapshot，只固定 `strategy_type`、允许的 `status`、最高 `confidence`、关键 `risk_flags`、关键跟踪项和禁止短语。

运行方式：

```bash
python -m pytest tests/test_regression_suite.py
python scripts/run_regression_suite.py
```

该套件不联网，不调用 AkShare，不接 LLM，也不输出交易建议。

## 17. Growth & Semiconductor Structural Risk Guard

`fundamental_skill` 在数据缺失风险之外，增加行业固有结构性风险识别。该补丁仍然是 deterministic rule-based，不接 LLM、不调用 AkShare、不生成 HTML、不输出交易建议。

适用范围：
- `right_trend_growth`：识别 AI资本开支依赖风险、订单与客户验证不足、估值预期消化风险。
- `semiconductor_cycle`：识别半导体周期波动风险、国产替代兑现验证风险、半导体估值波动风险。
- `stable_growth`：在订单、政策投资、项目交付、应收账款、回款或现金流触发时识别订单节奏验证风险、应收账款与现金流跟踪风险。

触发原则：
- 高景气成长股不无条件塞满风险；AI资本开支依赖风险需要命中 AI、算力、光模块、PCB、AI服务器、数据中心、云厂商、液冷等关键词。
- 订单与客户验证不足需要命中大客户、海外客户、云厂商、订单、供应链等关键词，并且缺少客户收入占比或订单验证字段。
- 成长股估值预期消化风险由 `pe_ttm > 40`，或估值缺失但存在强成长叙事触发。
- 半导体周期波动风险对 `semiconductor_cycle` 默认提示；国产替代兑现验证风险和半导体估值波动风险按关键词与估值阈值触发。
- 稳健成长股不强制 risk_flags 非空，只在订单节奏、政策投资、项目交付、应收账款、回款、现金流等文本或数据条件触发。

这些风险进入 `AnalysisContext.required_risks`，并通过 scoring constraints 影响 `catalyst_strength`、`industry_cycle`、`valuation_reasonableness`、`risk_control` 等维度，最终由 Result Assembler 合并到 `risk_flags`、`analyst_summary` 和兼容字段 `trader_summary`。

## 18. Real Data Connector v1

`RealDataConnector` 是 `fundamental_skill` 的真实公开数据入口，用于把 A 股股票代码转换为 pipeline 可消费的 raw JSON。它仍然只属于数据层，不负责分析、不负责评分、不负责交易判断。

调用链路：

```text
stock_code
  -> RealDataConnector
  -> raw JSON
  -> FundamentalSkillPipeline
  -> FundamentalAnalysisResult
```

输出 raw JSON 必须包含：
- `meta`
- `blocks.basic_info`
- `blocks.financial_indicator`
- `blocks.valuation`
- `blocks.business_composition`
- `blocks.news`
- `fetch_status`
- `errors`

每个 AkShare 数据块独立抓取和记录状态。任一接口失败时，不允许整个程序崩溃；失败信息写入 `errors`，缺失字段写入 `fetch_status`。如果 24 小时内存在 `cache/real_data/<code>.json`，默认使用缓存；`--force-refresh` 可强制刷新。如果刷新失败但旧缓存存在，可回退旧缓存并记录原因。

CLI 示例：

```bash
python -m src.fundamental_skill.real_stock_runner --code 002050 --output output/fundamental_002050.json
```

该命令会保存 `output/raw_002050.json` 和 `output/fundamental_002050.json`，控制台只打印结构化基本面摘要、缺失字段和错误数量，不输出交易建议、目标价、仓位或技术分析。
## RealDataConnector v2 Boundary

`RealDataConnector v2` remains a data-layer component for `fundamental_skill`. It converts confirmed public AkShare tables into raw JSON blocks consumed by `FundamentalDataAdapter`. It does not call LLMs, trading accounts, technical indicators, HTML renderers, or `trader_skill`, and it does not produce trading advice.

v2 confirmed sources:

- `stock_profile_cninfo` for `basic_info`.
- `stock_news_em` for `news`.
- `stock_financial_abstract` for `financial_indicator`.

`stock_financial_abstract` is parsed as a wide table:

- `指标` identifies metric rows.
- Date-like columns such as `20260331` identify reporting periods.
- The latest period is selected for current values.
- YoY and margin fields may be derived only from explicit financial rows, and such fields are marked in source trace as `derived=true`.

The connector writes source trace to `fetch_status.<block_name>.source_trace`, including source block, AkShare function, source indicator, source period, value, whether the value is derived, and the derivation method.

Current v2 limitations:

- `valuation` remains missing until a stable source is confirmed.
- `business_composition` remains missing until a stable source is confirmed.
- `inventory` is not mapped from `存货周转率` or `存货周转天数`; those are proxy turnover indicators, not amount fields.
- `accounts_receivable` is not mapped from `应收账款周转率` or `应收账款周转天数`; those are proxy turnover indicators, not amount fields.
## Real Data Calibration

Real public data often has stable `basic_info`, news, and financial indicator tables while valuation and business composition remain unavailable. Missing valuation or business composition does not automatically mean the stock cannot be analyzed at all. It means confidence must be lowered and prohibited claims must remain active.

Calibration rules:

- `insufficient_data` is for severely missing basic identity, business description, or financial metrics, not for every missing advanced field.
- For `advanced_manufacturing_growth`, when `basic_info.main_business` and at least five core financial fields are available, missing `business_composition`, `valuation_metrics`, or `accounts_receivable` can still allow `neutral` with low confidence.
- For `semiconductor_cycle`, when basic info and core financial metrics are available, missing `inventory`, `business_composition`, or `valuation_metrics` should express uncertainty through `neutral`, capped confidence, and risk flags rather than automatic `negative`.
- Missing `business_composition` means the result must not claim revenue mix, business exposure, robot business contribution, or auto thermal management revenue share is confirmed.
- Missing `valuation_metrics` means the result must not claim valuation is cheap, reasonable, or fully digested by growth.
- Missing `accounts_receivable` means the result must not claim collection quality or revenue quality is good.

## RealDataConnector v2.1 Boundary

`RealDataConnector v2.1` adds two confirmed public-data mappings while keeping the same fundamental-skill boundaries. It does not call LLMs, trading accounts, technical indicators, HTML renderers, or `trader_skill`, and it does not produce trading advice.

New confirmed sources:

- `valuation`: `stock_value_em`.
- `business_composition`: `stock_zygc_em`.

`valuation` maps:

- `pe_ttm` <- `PE(TTM)`
- `pb` <- `市净率`
- `ps` <- `市销率`
- `market_cap` <- `总市值`
- `dividend_yield` remains missing.

The valuation block selects the latest row by `数据日期`, records field-level source trace, and remains fail-soft when a column is missing or cannot be converted. It does not map PEG to PE and does not use forecast PE as the primary TTM PE.

`business_composition` maps latest-period segments from `stock_zygc_em`:

- `period` <- `报告日期`
- `segment_name` <- `主营构成`
- `classification_type` <- `分类类型`
- `revenue` <- `主营收入`
- `revenue_ratio` <- `收入比例`
- `gross_margin` <- `毛利率`
- `cost` <- `主营成本`
- `cost_ratio` <- `成本比例`
- `profit` <- `主营利润`
- `profit_ratio` <- `利润比例`

The connector keeps all valid rows from the latest report period and preserves `classification_type` for later analysis. It does not treat `分类类型` as the segment name.

`source_trace` records valuation field provenance and business-composition table provenance. Any block failure is recorded in `fetch_status` and `errors` rather than crashing the raw JSON generation.

`commodity_prices` remains outside v2.1. Although probe/replay can discover commodity-price candidates, external commodity data needs a separate `External Commodity Price Connector v1` design for品种 mapping, units, spot/futures distinctions, and contract selection.

Risk flags, prohibited claims, analyzer instructions, and must-track indicators must preserve these limits even when the final status is `neutral`.

### External Commodity Price Connector v1

`ExternalCommodityPriceConnector` adds `blocks.commodity_prices` for configured resource stocks. The first static exposure map covers `000426` (`silver`, `tin`), `601899` (`copper`, `gold`), and `603993` (`copper`, with `cobalt` and `molybdenum` remaining partial or missing until stable domestic sources are confirmed).

The v1 source priority is `futures_spot_price`, then `futures_spot_price_daily`, then SGE benchmark fallbacks for silver and gold. Stale primary data does not stop fallback selection; it is retained as a candidate while the connector searches for fresh daily or SGE data. `futures_foreign_commodity_realtime` is saved only as `foreign_reference` and is not readiness eligible because market, unit, currency, and contract meaning differ from the domestic primary source.

The raw block records `commodity_name`, `symbol`, `price`, `date`, `market`, `source_function`, contract context fields, `freshness_days`, `is_stale`, `readiness_eligible`, warnings, and source trace. `DataReadinessPlanner` treats full, fresh domestic primary coverage as satisfying `external.commodity_prices`; partial or stale coverage reports commodity-specific gaps such as `external.commodity_prices.copper.freshness` or `external.commodity_prices.cobalt`.

Commodity price observations are external context variables. They do not create price-trend analysis, technical indicators, account actions, HTML, or deterministic action instructions.

### External Commodity Price Connector v1.1

`ExternalCommodityPriceConnector v1.1` adds fresh domestic source promotion for copper and tin after replay confirmed that the older `futures_spot_price` and `futures_spot_price_daily` rows were stale.

For copper, the promoted source order is:

- `futures_zh_realtime(symbol="沪铜")`, with `trade` as price and `source_priority=domestic_realtime_primary`.
- `futures_zh_daily_sina(symbol="CU0")`, with `close` as price and `source_priority=domestic_daily_fallback`.
- `futures_main_sina(symbol="CU0")`, with `收盘价` as price and `source_priority=domestic_main_fallback`.

For tin, the promoted source order is:

- `futures_zh_realtime(symbol="沪锡")`, with `trade` as price and `source_priority=domestic_realtime_primary`.
- `futures_zh_daily_sina(symbol="SN0")`, with `close` as price and `source_priority=domestic_daily_fallback`.
- `futures_main_sina(symbol="SN0")`, with `收盘价` as price and `source_priority=domestic_main_fallback`.

Fresh rows from these domestic sources may satisfy `external.commodity_prices.<commodity>.freshness`. Stale rows and foreign references remain non-eligible. `cobalt` and `molybdenum` remain unavailable in connector v1.1.

Realtime and daily fields such as settlement, presettlement, open, high, low, close, volume, and hold are preserved as raw data context only. They are not converted into technical indicators or price-trend conclusions.

## RealDataConnector v2.2a Boundary

`RealDataConnector v2.2a` adds only three confirmed balance-sheet fields to the existing financial block:

- `financial_metrics.inventory`
- `financial_metrics.accounts_receivable`
- `financial_metrics.contract_liabilities`

All three come from `stock_financial_report_sina(indicator="资产负债表")`; `source_period` is the `报告日` field. A recognizable report date receives `period_confidence=high`; an unrecognizable or missing period is retained as `source_period="unknown"` with `period_confidence=low`.

`contract_liabilities` may improve order-visibility discussion only as a proxy. It must not be described as real orders, order backlog, or confirmed future revenue.

The connector still does not add R&D expense, R&D expense ratio, capex, capex ratio, customer concentration, new-business orders, domestic-substitution revenue, production/unit cost, cobalt price, or molybdenum price. R&D and Capex need a separate Source Expansion Probe before any deterministic integration.

## RealDataConnector v2.3a Boundary

`RealDataConnector v2.3a` adds only three source-traced statement fields to `financial_metrics`:

- `r_and_d_expense`
- `r_and_d_expense_ratio`
- `capex`

The source is `stock_financial_report_sina`:

- `r_and_d_expense` maps from the profit-statement `研发费用` amount.
- `r_and_d_expense_ratio` is derived only from same-report-period `r_and_d_expense` and revenue.
- `capex` maps from the cash-flow statement long-term-asset purchase/construction cash-paid line.

`capex_ratio` and `depreciation_amortization` remain unconnected. Customer concentration, new-business orders, domestic-substitution revenue, production or unit cost, technical indicators, `technical_skill`, and `trader_skill` also remain outside this connector version.

Trace fields preserve `period_confidence`, `value_confidence`, `unit`, `unit_confidence`, `cumulative_or_single_quarter`, `statement_type`, `derived`, `derivation_method`, and `scope_note`. Amount fields keep `unit_confidence=low`; the R&D ratio keeps `unit_confidence=high`; all three fields are treated as cumulative as reported.

Interpretation guardrails:

- R&D expense ratio represents R&D intensity only; it does not confirm a technology barrier.
- Capex represents cash paid for long-term assets only; it does not confirm capacity release or future growth certainty.
