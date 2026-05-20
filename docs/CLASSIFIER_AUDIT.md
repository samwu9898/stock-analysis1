# 股票分类器审计

## 1. 分类规则

`StockClassifier` 是确定性规则分类器，不调用 LLM，不调用 AkShare，不做评分引擎。

输入为 `NormalizedFundamentalInput`，分类器从以下字段收集文本：

- `stock_name`
- `basic_info.industry`
- `basic_info.main_business`
- `business_composition.segments`
- `latest_news.title / summary`
- `raw_blocks` 的安全截断文本

分类规则来自 `config/strategy_classification.yaml`。当前支持：

- `resource_swing`
- `resource_core`
- `right_trend_growth`
- `semiconductor_cycle`
- `stable_growth`
- `theme_only`
- `unknown`

加权规则：

- 股票名称命中核心样例：高权重。
- 行业命中：高权重。
- 主营业务命中：高权重。
- 主营构成命中：中高权重。
- 新闻命中：低权重。
- 原始 blocks 文本命中：低权重。

如果仅新闻或原始文本命中，置信度不会提升到 `high`。

## 2. 冲突处理逻辑

当多个类型同时命中时，分类器选择最高分，并将其他命中类型写入 `alternative_types`。

特殊冲突：

- `resource_swing` vs `resource_core`：如果出现“紫金矿业、多矿种、全球矿业、资源龙头、大型矿企”，优先 `resource_core`；如果出现“银、锡、稀土、单一商品、弹性”，偏向 `resource_swing`。
- `right_trend_growth` vs `semiconductor_cycle`：半导体设备、芯片、晶圆、存储、国产替代优先 `semiconductor_cycle`；光模块、PCB、AI服务器、液冷、数据中心优先 `right_trend_growth`。
- `stable_growth` vs `right_trend_growth`：电网、变压器、特高压、输配电、电网自动化优先 `stable_growth`；液冷、AI 数据中心等温控扩散链可进入 `right_trend_growth`。

## 3. 当前限制

- 关键词规则不能理解复杂上下文，例如否定句或反讽。
- `raw_blocks` 文本仅截断抽样，可能漏掉很靠后的信息。
- 行业字段来自上游数据，缺失时分类置信度会受影响。
- 财务指标只参与缺失字段传递，不参与分类打分。
- 当前分类器不会识别所有 A 股行业，只覆盖本阶段定义的几类框架。
- 分类不是结论，不能替代后续基本面分析。

## 4. 后续优化方向

- 引入更细的行业词典和同义词表。
- 将股票名称白名单和关键词权重拆成更细粒度规则。
- 引入 explainable rule id，方便审计每条命中的来源。
- 在后续 scorer 阶段结合数据完整性，对框架置信度做惩罚。
- 为金融、医药、公用事业、高股息等类型扩展新框架。
# advanced_manufacturing_growth 补充

第九阶段新增 `advanced_manufacturing_growth`，用于识别高端制造成长股。

适用方向：

- 汽车热管理
- 机器人执行器
- 工业自动化
- 精密制造核心零部件
- 新能源车供应链
- 机器人产业链
- 高端制造核心零部件

典型标的包括三花智控、拓普集团、汇川技术、双环传动、绿的谐波、中大力德、鸣志电器、埃斯顿等。

冲突处理：

- 同时命中 `right_trend_growth` 和 `advanced_manufacturing_growth` 时，光模块、PCB、AI 服务器、CPO、数据中心优先 `right_trend_growth`；汽车热管理、机器人、执行器、工业自动化、精密制造优先 `advanced_manufacturing_growth`。
- 同时命中 `stable_growth` 和 `advanced_manufacturing_growth` 时，电网、变压器、特高压、输配电优先 `stable_growth`；汽车零部件、机器人零部件、工业自动化优先 `advanced_manufacturing_growth`。

当前限制：

- 机器人业务如果只出现在新闻或业务布局中，分类可以识别方向，但后续 analyzer 不能直接断言收入已经兑现。
- 汽车热管理和机器人零部件仍需要订单、收入占比、毛利率和现金流验证。
