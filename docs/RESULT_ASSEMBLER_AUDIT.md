# Result Assembler Audit

## Neutral Naming Compatibility v1

`FundamentalResultAssembler` now fills neutral alias fields while preserving old public fields:

- `analyst_summary` is recommended for new readers and user-facing display.
- `downstream_review_hint` is recommended for invalidation-condition follow-up review.
- `trader_summary` is deprecated but retained for backward compatibility.
- `action_hint_for_trader` is deprecated but retained for backward compatibility.

During v1, the assembler writes both summary fields with the same neutral text, and writes both review-hint fields with the same neutral value. Newly assembled user-visible text must use neutral wording such as "进入后续综合评估", "需要后续分析层复核", "后续模块评估", or "后续基本面复核". This does not change scoring, status, confidence, invalidation logic, regression expectations, or safety boundaries. The project still does not implement `trader_skill`, does not implement `technical_skill`, does not connect to trading accounts, and does not output trading advice.

## 1. 定位

`FundamentalResultAssembler` 是 `fundamental_skill` 的最终结构化输出层，负责把前序 deterministic pipeline 的中间产物装配为 `FundamentalAnalysisResult`。

输入包括：

- `NormalizedFundamentalInput`
- `StockClassificationResult`
- `FundamentalFramework`
- `DataReadinessPlan`
- `AnalysisContext`
- `FundamentalScoringResult`

输出是给后续 `trader_skill` 使用的基本面结构化输入，不是交易建议。

## 2. status 决策规则

决策顺序为严格优先级：

1. `insufficient_data`
   - 数据准备度为 `insufficient`。
   - 上下文质量为 `insufficient`。
   - 评分置信度为 `low`，且数据准备度为 `weak/insufficient`，并且规则总分低于 55。
   - 股票类型为 `unknown`。
   - 原始数据结构未知。

2. `negative`
   - 规则总分低于 45。
   - `risk_control` 维度受约束后低于 40。
   - `financial_quality` 低于 40 且 `data_quality` 不低。
   - 高严重度必带风险达到 3 个及以上。
   - 财务质量和业务质量同时受到严重限制。

3. `supportive`
   - 规则总分不低于 70。
   - 评分置信度不低。
   - 数据准备度至少为 `usable_with_warnings`。
   - 上下文最高置信度不低。
   - 高严重度风险不超过 1 个。
   - 数据质量不低。
   - 财务质量较好，或成长/半导体框架下业务质量和行业周期较强。

4. `neutral`
   - 不满足以上条件时使用。

这些状态只表达基本面 Skill 对后续评估的支持程度。

## 2.1 保守性补丁：confidence 封顶

`status=supportive` 不等于交易建议，也不代表高置信度。最终置信度会被关键数据缺失封顶：

- 资源弹性股和资源核心底仓缺少 `external.commodity_prices` 时，周期判断不能高置信度，`confidence` 最高为 `medium`；如果数据准备度不是 `sufficient`，最高为 `low`。
- 高景气趋势成长股缺少毛利率，或存在 `margin_improvement_confirmed` 禁止结论时，盈利能力判断不能高置信度，`confidence` 最高为 `medium`。
- 半导体周期股缺少存货，或存在 `inventory_cycle_healthy` 禁止结论时，周期判断不能高置信度，`confidence` 最高为 `medium`。
- 稳健成长股缺少经营现金流或 ROE 时，稳健性判断不能高置信度，`confidence` 最高为 `medium`；如果 readiness 为 `weak`，则为 `low`。
- 任意 high severity 的数据缺失风险存在时，`confidence` 不允许为 `high`。

资源股缺商品价格时，`trader_summary` 必须提示“资源股周期判断受商品价格数据缺失限制”或外部价格变量未验证。

## 2.2 supportive 的保守限制

`supportive` 仍可在个别关键外部变量缺失时出现，但必须满足规则分、数据准备度、上下文置信度和风险数量要求。若 high severity 风险达到 2 个及以上，除非 readiness 为 `sufficient` 且 scoring confidence 为 `high`，否则不得输出 `supportive`。

当 `status=supportive` 但 `confidence=medium` 时，`trader_summary` 必须说明仍存在关键验证项或数据限制。

## 3. 字段装配规则

- `business_summary`：来自行业、主营、主营构成、分类结果和框架说明。主营构成缺失时不断言收入来源。
- `key_drivers`：来自评分正面证据、框架关注点、分类理由和可用财务数据。若上下文禁止某类断言，则改用待验证描述。
- `financial_quality`：使用最近一期财务指标和 `financial_quality` 受约束后分数。现金流、扣非净利润或毛利率缺失时必须提示数据缺口。
- `valuation_view`：使用估值指标和估值维度分数。缺估值数据时为 `unknown`；成长和半导体框架不简单按低 PE 解释。
- `industry_cycle`：使用行业周期维度分数和策略类型。资源股缺商品价格时不写成上行周期，半导体缺存货时不写成库存健康。
- `risk_flags`：合并 `AnalysisContext.required_risks`、`FundamentalScoringResult.required_risks` 和 readiness blockers，并去重。
- `catalysts`：只保守描述财报改善、行业景气、商品价格、订单或政策等因素；相关数据缺失时不确定性提高。
- `must_track_indicators`：来自框架、readiness 推荐补充数据、上下文风险和评分警告。
- `invalidation_conditions`：生成基本面证伪条件，`action_hint_for_trader` 只使用 schema 允许值。
- `trader_summary`：说明 status、confidence、数据准备度和主要风险，不输出交易动作。
- `key_drivers`：若上下文禁止商品价格收益确认、毛利率改善确认或库存周期健康等结论，只能写为“需要进一步验证”或“关键跟踪项”，不得写成确定性驱动。

## 4. validator 强制生效

Assembler 在返回前必须调用 `assert_valid_result(result)`。

当前 validator 会检查：

- 输出 JSON 不包含禁止交易动作词。
- `trader_summary` 不包含交易动作。
- `invalidation_conditions.action_hint_for_trader` 不包含交易动作，且 schema 限定为允许值。
- `insufficient_data` 状态下 `fundamental_score` 不高于 50。
- 低置信度必须给出缺失字段或置信度原因。
- 存在 high severity 风险时，摘要必须提示高风险或需要重新评估。

## 5. 当前限制

- 本阶段仍是规则型装配，不接 LLM，不做自然语言深度归因。
- 新闻和公告不做语义级验证。
- 商品价格、行业周期和同行比较依赖后续数据源增强。
- `fundamental_score` 仍是基本面规则分，不是交易评分。

## 6. 后续优化方向

- 引入可审计的证据溯源路径。
- 增加行业横向比较和历史分位信息。
- 为不同 strategy_type 增加更细的证伪条件模板。
- 在保持 validator 边界的前提下，后续接入 LLM 生成更自然但受约束的解释文本。

## 7. advanced_manufacturing_growth 装配规则

第九阶段新增 `advanced_manufacturing_growth` 后，Result Assembler 增加：

- `must_track_indicators` 必须包含营收增速、净利润增速、毛利率、经营现金流、应收账款、业务构成、机器人相关业务收入或订单、汽车热管理业务收入或订单。
- `invalidation_conditions` 包含营收或利润增速放缓、毛利率下滑、经营现金流与利润背离、机器人或新业务收入/订单无法验证、大客户需求低于预期、估值无法被业绩增长消化。
- `key_drivers` 不得把机器人概念写成确定性收入贡献。即使分类为高端制造成长股，机器人业务仍需订单和收入验证。
- `trader_summary` 对高端制造成长股会提示机器人相关业务仍需订单和收入验证。

该策略类型仍然不是交易建议，只是更精确的基本面分析框架。

## 8. Advanced Manufacturing Risk Guard

当 `advanced_manufacturing_growth` 出现机器人业务、特斯拉/大客户供应链或高估值预期但缺少充分验证时，Result Assembler 必须保留对应风险：

- 机器人业务兑现验证不足
- 大客户依赖验证不足
- 估值预期消化风险

`key_drivers` 不得出现“机器人业务已经兑现”“机器人业务成为主要增长来源”“人形机器人收入确定放量”“特斯拉订单确定增长”等确定性表述。

`trader_summary` 必须提示机器人相关业务仍需订单和收入验证；若存在大客户风险，需要提示大客户收入占比和订单持续性需要跟踪；若存在估值风险，需要提示估值需要业绩增长消化。

如果两个及以上 medium severity guard 风险存在，最终 `confidence` 最高为 `medium`。

## 9. Growth & Semiconductor Structural Risk Guard

Result Assembler 不直接重新判断结构性风险来源，而是合并 `AnalysisContext.required_risks` 和 `FundamentalScoringResult.required_risks`。新增 guard 后：

- `right_trend_growth` 的 `risk_flags` 可包含 AI资本开支依赖风险、订单与客户验证不足、估值预期消化风险。
- `semiconductor_cycle` 的 `risk_flags` 可包含半导体周期波动风险、国产替代兑现验证风险、半导体估值波动风险。
- `stable_growth` 的 `risk_flags` 可在触发条件满足时包含订单节奏验证风险、应收账款与现金流跟踪风险，但不强制非空。

当 `right_trend_growth` 或 `semiconductor_cycle` 的中等结构性风险达到 2 个及以上时，最终 `confidence` 最高为 `medium`。`trader_summary` 会提示订单、客户资本开支、估值消化、半导体周期、库存、国产替代兑现、回款和现金流等限制因素，但仍不输出任何交易动作、仓位、价格或技术面判断。
## Real Data Calibration Patch

`FundamentalResultAssembler` now distinguishes severe data absence from real-data verification gaps.

For `advanced_manufacturing_growth`, if classification confidence is at least medium, basic identity/business text exists, at least five core financial metrics are available, readiness is `weak`, and the remaining gaps are mainly `business_composition`, `valuation_metrics`, or `accounts_receivable`, the assembler may return `neutral` instead of `insufficient_data`. Confidence remains capped and supportive status is still blocked by the normal scoring/confidence gates.

For `semiconductor_cycle`, if basic info and core financial metrics are available but `inventory`, `business_composition`, and `valuation_metrics` are missing, data uncertainty should produce `neutral` rather than `negative`, unless financial quality, risk control, or weighted score are genuinely poor beyond the calibrated data-gap case.

The patch does not relax prohibited conclusions:

- missing business composition still blocks claims about business revenue mix or confirmed segment exposure;
- missing valuation still blocks claims that valuation is cheap or reasonable;
- missing accounts receivable still blocks claims about collection quality;
- robot/new business and customer-demand claims remain unverified without order or revenue evidence.

`insufficient_data` remains appropriate for unknown strategy, severe basic-info gaps, unknown raw structure, empty financial metrics, or truly insufficient readiness/context quality.

## External Commodity Price Connector v1 Impact

When `blocks.commodity_prices` contains full, fresh domestic primary coverage for a configured resource stock, `DataReadinessPlanner` no longer reports the broad `external.commodity_prices` gap. This lets the result assembler avoid the commodity-data-missing risk path for that specific gap.

Partial coverage still flows through readiness as commodity-specific missing fields, such as `external.commodity_prices.cobalt` or freshness-specific gaps. The existing context rules continue to constrain `industry_cycle`, catalysts, confidence, and risk flags when coverage is partial, stale, or reference-only.

Commodity prices remain external evidence only. The result assembler must not convert price availability into price-trend claims, technical indicators, HTML, account actions, or deterministic action instructions.
