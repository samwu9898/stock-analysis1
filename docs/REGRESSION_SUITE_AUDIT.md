# Regression Suite Audit

## 1. 目的

Sample Regression Suite 用于固定 `fundamental_skill` 的关键行为，防止后续扩展规则时出现分类漂移、风险识别退化或输出边界被破坏。

回归集覆盖 A 股基本面 Skill 当前支持的主要策略类型：

- `resource_swing`
- `resource_core`
- `right_trend_growth`
- `semiconductor_cycle`
- `advanced_manufacturing_growth`
- `stable_growth`
- `theme_only`
- `unknown`

## 2. 为什么不做 full JSON snapshot

`FundamentalAnalysisResult` 中有很多解释性文本、证据摘要和跟踪项描述。完整 JSON 快照会让测试过于脆弱，文案轻微调整也会导致大量失败。

因此本套件只固定关键字段：

- `stock_code`
- `strategy_type`
- `status`
- `confidence`
- 关键 `risk_flags`
- `must_track_indicators` 关键词
- 禁止短语
- 禁止交易动作词

这能锁住业务边界，同时保留后续文案迭代空间。

## 3. 样本覆盖

当前回归样本：

- 兴业银锡：资源弹性股
- 洛阳钼业：资源弹性股
- 紫金矿业：资源核心底仓
- 中际旭创：高景气趋势成长股
- 胜宏科技：高景气趋势成长股
- 北方华创：半导体国产替代/周期股
- 澜起科技：半导体国产替代/周期股
- 三花智控：高端制造成长股
- 拓普集团：高端制造成长股
- 思源电气：稳健成长股
- 国电南瑞：稳健成长股
- 题材样本A：题材属性股
- 数据不足样本B：未知/数据不足

所有样本都是 mock raw JSON，不联网，不调用 AkShare。

## 4. 如何新增样本

1. 在 `tests/regression/fixtures/` 新增 mock raw JSON。
2. 在 `tests/regression/expected/` 新增同名 expected JSON。
3. expected 只填写关键字段，不要复制完整输出。
4. 运行：

```bash
python -m pytest tests/test_regression_suite.py
python scripts/run_regression_suite.py
```

## 5. 如何运行

单独运行回归套件：

```bash
python -m pytest tests/test_regression_suite.py
```

运行辅助脚本：

```bash
python scripts/run_regression_suite.py
```

全量测试：

```bash
python -m pytest tests
```

## 6. 当前限制

- 样本为 mock 数据，不代表真实财报。
- 风险识别仍基于规则和文本启发式。
- expected snapshot 不验证完整自然语言质量。
- 没有接入真实商品价格、客户收入占比、订单金额或同行估值分位。

## 7. 后续扩展到真实数据测试

后续可以新增一层真实数据回放测试：

- 保存历史 raw JSON，不实时联网。
- 固定数据时间戳和来源。
- 对比关键字段而非完整文本。
- 单独标记为慢速或集成测试，避免影响日常单元测试。

## 8. Growth & Semiconductor Structural Risk Regression

本轮 regression suite 增加结构性风险锁定，防止高景气成长股和半导体样本在数据完整时出现 `risk_flags=0`：

- 中际旭创：要求至少包含 AI资本开支依赖风险、订单与客户验证不足。
- 胜宏科技：要求至少包含 AI资本开支依赖风险。
- 北方华创：要求至少包含半导体周期波动风险、国产替代兑现验证风险。
- 澜起科技：要求至少包含半导体周期波动风险、国产替代兑现验证风险。
- 三花智控：继续锁定机器人业务兑现验证不足、大客户依赖验证不足，确保 advanced manufacturing guard 不退化。

测试仍只固定关键字段，不做完整 JSON snapshot；新增断言不改变交易边界，仍检查 forbidden trading terms 和 `assert_valid_result`。
## Real Data Calibration Regression

The regression suite remains mock-data based, but additional unit coverage now locks real-data calibration behavior:

- advanced manufacturing real-data gaps with sufficient basic info and financial metrics return `neutral`, not `insufficient_data`;
- semiconductor real-data gaps with missing inventory/business composition/valuation return `neutral`, not automatic `negative`;
- missing valuation alone does not force `insufficient_data`;
- missing business composition alone does not force `insufficient_data` when basic info and financial metrics are sufficient;
- `紫金矿业` is classified as `resource_core`;
- `兴业银锡` remains `resource_swing`.

These tests preserve existing boundaries: no LLM, no trading account, no HTML, no technical indicators, and no trading advice. The standard sample regression suite still verifies historical mock cases and forbidden trading terms.
