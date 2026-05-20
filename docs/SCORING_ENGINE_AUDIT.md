# Scoring Engine 审计

## 1. 评分规则

`FundamentalScoringEngine` 是确定性的规则型评分引擎。它不调用 LLM，不调用 AkShare，不生成最终基本面结论。

输入：

- `NormalizedFundamentalInput`
- `StockClassificationResult`
- `FundamentalFramework`
- `DataReadinessPlan`
- `AnalysisContext`

输出：

- `FundamentalScoringResult`

评分维度：

- `business_quality`
- `financial_quality`
- `industry_cycle`
- `valuation_reasonableness`
- `catalyst_strength`
- `risk_control`
- `data_quality`

`risk_control` 分数越高代表风险越可控，分数越低代表风险越大。

## 2. 权重设计

权重来自 `config/fundamental_scoring.yaml`，按 `strategy_type` 区分。

- `resource_swing` 更重视 `industry_cycle` 和 `financial_quality`。
- `resource_core` 更重视 `business_quality`、`financial_quality`、`industry_cycle` 和 `risk_control`。
- `right_trend_growth` 更重视业务质量、财务质量、行业周期和催化强度。
- `semiconductor_cycle` 对业务、财务、周期、风险和数据质量保持较均衡权重。
- `stable_growth` 更重视财务质量、风险可控度和数据质量。
- `theme_only` 更重视风险可控度和数据质量。
- `unknown` 更重视数据质量。

如果权重和不等于 1.0，代码会 normalize 并记录 warning。

## 3. Context Constraint 应用方式

评分先生成 `raw_score`，再应用 `AnalysisContext`：

- 如果 `scoring_constraints` 有维度上限，`constrained_score` 不能超过该上限。
- 如果维度被 `blocked`，最高 40。
- 如果维度被 `restricted`，最高 60。
- 如果维度为 `allowed_with_low_confidence`，最高 75。
- 如果 `max_overall_confidence=low`，所有维度最高 75。
- 如果 `readiness_level=insufficient`，所有维度最高 60。

每个被应用的限制都会写入 `applied_constraints`。

## 4. 整体封顶规则

`weighted_total_score` 是规则评分，不是最终基本面评分。

整体封顶：

- `max_overall_confidence=low`：最高 70。
- `readiness_level=weak`：最高 70。
- `readiness_level=insufficient`：最高 50。
- `strategy_type=unknown`：最高 50。
- `context_quality=insufficient`：最高 50。

## 5. 当前限制

- 规则评分只使用已标准化字段，不做行业横向比较。
- 新闻只做保守关键词判断，不做语义分析。
- 未接外部商品价格、行业库存、订单等数据源。
- 不判断最终基本面好坏。
- 不生成最终分析报告。

## 6. 后续优化方向

- 引入行业专属阈值。
- 加入数据新鲜度和来源质量权重。
- 扩展外部变量输入，例如商品价格、行业资本开支、库存周期。
- 在最终 analyzer 中强制引用 `required_risks` 和 `applied_constraints`。
# advanced_manufacturing_growth 评分补充

第九阶段新增 `advanced_manufacturing_growth` 权重：

- `business_quality`: 0.20
- `financial_quality`: 0.22
- `industry_cycle`: 0.15
- `valuation_reasonableness`: 0.10
- `catalyst_strength`: 0.13
- `risk_control`: 0.10
- `data_quality`: 0.10

补充规则：

- 主营构成中出现汽车热管理、机器人执行器、工业自动化、精密制造等有效业务名称时，`business_quality` 加分。
- `revenue_yoy`、`net_profit_yoy`、`gross_margin` 用于验证成长是否兑现到收入、利润和盈利能力。
- `operating_cashflow` 为正有助于 `risk_control`。
- `accounts_receivable` 缺失会降低 `risk_control`，因为无法验证回款和收入质量。
- 新闻中出现机器人、汽车热管理、订单、客户等关键词只做小幅催化加分，不能单独形成高置信度结论。

当前限制：

- 暂不区分机器人业务真实收入、订单、产能和纯概念曝光。
- 仍需要后续增加研发费用率、大客户收入占比、海外收入和汇率影响等字段。

## Advanced Manufacturing Risk Guard

高端制造成长股新增三类 guard：

- `机器人业务兑现验证不足`：限制 `catalyst_strength <= 70`，`business_quality <= 80`，并加入 scoring warning“机器人业务仍需订单和收入验证”。
- `大客户依赖验证不足`：限制 `risk_control <= 75`，`catalyst_strength <= 70`，并加入 scoring warning“大客户收入占比和订单持续性需要验证”。
- `估值预期消化风险`：限制 `valuation_reasonableness <= 70`，并加入 scoring warning“估值可能已经反映部分成长预期”。

这些 guard 防止系统把机器人、特斯拉供应链或高端制造预期直接当作已经兑现的基本面质量。

## Growth & Semiconductor Structural Risk Guard

新增结构性风险 guard 后，Scoring Engine 继续只消费 `AnalysisContext`，不直接做外部数据判断。新增风险通过 `context.required_risks` 和 `context.scoring_constraints` 进入评分：

- `right_trend_growth`：AI资本开支依赖风险限制 `industry_cycle <= 75`、`catalyst_strength <= 70`、`risk_control <= 75`；订单与客户验证不足限制 `catalyst_strength <= 70`、`risk_control <= 75`；估值预期消化风险限制 `valuation_reasonableness <= 70`。
- `semiconductor_cycle`：半导体周期波动风险限制 `industry_cycle <= 75`、`risk_control <= 75`；国产替代兑现验证风险限制 `catalyst_strength <= 70`、`industry_cycle <= 75`、`risk_control <= 75`；半导体估值波动风险限制 `valuation_reasonableness <= 70`、`risk_control <= 75`。
- `stable_growth`：订单节奏验证风险限制 `industry_cycle <= 75`、`catalyst_strength <= 70`；应收账款与现金流跟踪风险限制 `risk_control <= 75`、`financial_quality <= 80`。

Scoring warnings 增加对应提示，用于 pipeline trace 审计；这不会引入交易建议、技术指标、LLM 或 AkShare 调用。
