# Data Readiness Planner 审计

## 1. 字段要求设计

`DataReadinessPlanner` 基于 `NormalizedFundamentalInput`、`StockClassificationResult` 和 `FundamentalFramework` 生成 `DataReadinessPlan`。它只检查数据准备度，不做基本面评分，不输出基本面结论。

字段要求来自 `config/data_requirements.yaml`，按 `strategy_type` 分组。每个字段要求包含：

- 字段路径；
- 展示名称；
- 字段类别；
- 重要性；
- 缺失原因；
- 预期位置；
- 影响的后续分析维度。

## 2. 扣分规则

`readiness_score` 是数据准备度，不是基本面评分。

从 100 分开始扣分：

- `critical missing`：每个扣 18 分；
- `high missing`：每个扣 10 分；
- `medium missing`：每个扣 5 分；
- `low missing`：每个扣 2 分；
- `critical partial`：每个扣 9 分；
- `high partial`：每个扣 5 分；
- `medium partial`：每个扣 3 分；
- `low partial`：每个扣 1 分；
- `strategy_type=unknown` 额外扣 20 分；
- `classification_confidence=low` 额外扣 10 分。
- `classification_confidence=medium` 额外扣 5 分。
- `raw data unknown structure` 额外扣 10 分。
- `financial_metrics` 为空额外扣 20 分。
- critical 主营构成缺失额外扣 10 分。

`readiness_level`：

- `sufficient`：分数不低于 80 且没有 critical 缺失；
- `usable_with_warnings`：分数不低于 60；
- `weak`：分数不低于 40；
- `insufficient`：分数低于 40。

如果 critical 缺失不少于 3 个，最高只能是 `weak`。如果 `strategy_type=unknown`，最高只能是 `weak`。

更严格的等级封顶规则：

- 任意 critical 缺失：最高 `usable_with_warnings`。
- critical 缺失不少于 2 个：最高 `weak`。
- critical 缺失不少于 3 个：最高 `insufficient`。
- high 缺失不少于 2 个：最高 `usable_with_warnings`。
- `classification_confidence=low`：最高 `weak`。
- `financial_metrics` 为空：最高 `weak`。
- critical 主营构成缺失：最高 `usable_with_warnings`；若同时存在 critical 财务缺失，最高 `weak`。
- `resource_swing` 缺扣非净利润或经营现金流：最高 `usable_with_warnings`；二者同时缺失：最高 `weak`；若主营构成也缺失：最高 `insufficient`。
- `right_trend_growth` 缺毛利率：最高 `usable_with_warnings`；缺营收增速或净利润增速：最高 `weak`。
- `semiconductor_cycle` 缺存货：最高 `usable_with_warnings`；若存货和毛利率同时缺失：最高 `weak`。
- `stable_growth` 缺经营现金流或 ROE：最高 `usable_with_warnings`；二者同时缺失：最高 `weak`。

## 3. 各 strategy_type 关键字段

- `resource_swing`：扣非净利润、毛利率、经营现金流、主营构成、商品价格。
- `resource_core`：经营现金流、资产负债率、ROE、主营构成、商品价格和股息率。
- `right_trend_growth`：营收增速、净利润增速、毛利率、估值、市值、主营构成。
- `semiconductor_cycle`：营收增速、毛利率、存货、经营现金流、主营构成。
- `stable_growth`：经营现金流、ROE、毛利率、资产负债率、应收账款、主营构成。
- `theme_only`：扣非净利润、经营现金流、主营构成和公告新闻。
- `unknown`：行业、主营业务、财务指标和主营构成。

## 4. 当前限制

- 当前没有外部变量标准字段，因此 `external.commodity_prices` 默认缺失。
- 字段存在性检查不判断数据质量，只判断是否可用或部分可用。
- `partial` 的判定目前较保守：有财务对象但对应字段为空即为 partial。
- 对财务字段，最近一期缺失但历史期存在才记为 `partial`；任一期都没有则记为 `missing`。
- 不计算行业横向比较，也不判断财务指标是否异常。
- 不接实时数据，不自动补数据。

## 5. 后续优化方向

- 为外部变量建立标准输入结构，例如商品价格、行业资本开支、库存周期。
- 引入字段新鲜度检查，例如财报是否过旧。
- 根据不同字段的数据周期设置更精细的惩罚。
- 与后续 scorer 联动，将 readiness 作为置信度上限，而不是基本面分数。
