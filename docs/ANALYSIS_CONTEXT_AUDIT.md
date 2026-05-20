# Analysis Context Builder 审计

## 1. 上下文生成规则

`AnalysisContextBuilder` 读取：

- `NormalizedFundamentalInput`
- `StockClassificationResult`
- `FundamentalFramework`
- `DataReadinessPlan`

并生成 `AnalysisContext`。它不是基本面评分，不是基本面结论，不做交易判断。

核心流程：

1. 根据 `readiness_level` 和 `classification_confidence` 计算整体上下文质量与最高置信度。
2. 根据 `DataReadinessPlan.field_readiness` 中的 missing/partial 字段查找 `config/analysis_context_rules.yaml`。
3. 生成维度权限、必须风险、禁止结论、评分约束和 analyzer 指令。
4. 同类风险、禁止结论和评分约束合并去重。
5. 生成给后续 analyzer/scorer 的安全摘要。

## 2. 缺失字段映射

当前支持的关键缺失字段映射：

- `financial_metrics.deducted_net_profit`：限制财务质量和风险分析；禁止断言利润增长可持续。
- `financial_metrics.operating_cashflow`：限制财务质量；禁止断言现金流质量强。
- `financial_metrics.gross_margin`：限制财务质量和行业周期；禁止断言毛利率改善。
- `financial_metrics.inventory`：限制库存周期和风险分析；禁止断言库存周期健康。
- `financial_metrics.roe`：限制资本回报质量判断。
- `business_composition.segments`：限制业务摘要、行业周期和核心驱动判断。
- `external.commodity_prices`：限制资源股行业周期和催化判断。

## 3. strategy_type 专项限制

- `resource_swing`：核心字段缺失时，不允许断言商品价格上涨已经转化为持续业绩、利润增长可持续、资源暴露结构清晰。
- `right_trend_growth`：核心字段缺失时，不允许断言高景气已经充分兑现到业绩、估值可以被业绩消化、毛利率趋势改善。
- `semiconductor_cycle`：核心字段缺失时，不允许断言库存周期健康、国产替代已转化为订单和利润、半导体周期已经反转。
- `stable_growth`：核心字段缺失时，不允许断言现金流稳健、资本回报质量高、订单质量稳定。

## 4. 当前限制

- 规则仍是确定性的字段映射，不理解复杂语义。
- 上下文只限制后续分析，不生成分析正文。
- 评分约束只是上限提示，后续 scorer 需要显式执行。
- 当前只覆盖前几阶段已定义的 strategy_type 和关键字段。

## 5. 后续优化方向

- 给每条规则加入可追踪 rule id。
- 根据财报新鲜度和数据源质量调整上下文质量。
- 扩展金融、医药、公用事业等行业的专项缺失规则。
- 在后续 analyzer/scorer 中强制消费 `AnalysisContext`，把它作为置信度和评分上限。
