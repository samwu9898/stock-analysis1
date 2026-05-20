# Pipeline Facade Audit

## Neutral Naming Compatibility v1

The pipeline continues to orchestrate the same deterministic fundamental modules, but the public `FundamentalAnalysisResult` now includes neutral aliases:

- `analyst_summary` is preferred by AI and Dashboard layers.
- `downstream_review_hint` is preferred by AI and Dashboard layers.
- `trader_summary` is deprecated but retained for backward compatibility.
- `action_hint_for_trader` is deprecated but retained for backward compatibility.

This compatibility migration mirrors values, preserves historical JSON readers, and avoids new user-visible "交易员 Agent" style wording in freshly assembled results. It does not change classification, readiness, scoring, status, confidence, or regression logic except for added neutral-field checks. The project still does not implement `trader_skill`, does not implement `technical_skill`, does not connect to trading accounts, and does not output trading advice.

## 1. 作用

`FundamentalSkillPipeline` 是 `fundamental_skill` 的统一入口，用于把 raw JSON 一次性转换为最终 `FundamentalAnalysisResult`。

它面向两类调用方：

- 后续 `trader_skill`：直接消费结构化基本面结果。
- 人工测试和调试：通过 CLI 或 Python 类调用完整链路。

Pipeline 只是编排器，不改变任何评分、分类、readiness、context 或 assembler 规则。

## 2. 完整链路

执行顺序固定为：

1. `FundamentalDataAdapter`
2. `StockClassifier`
3. `FrameworkSelector`
4. `DataReadinessPlanner`
5. `AnalysisContextBuilder`
6. `FundamentalScoringEngine`
7. `FundamentalResultAssembler`
8. `assert_valid_result`

任何步骤失败都会抛出带阶段名称的 `RuntimeError`，不会静默吞掉异常。

## 3. 输入输出

输入：

- `analyze_from_file(raw_data_path, user_thesis=None, output_path=None)`
- `analyze_from_dict(raw_data, user_thesis=None, output_path=None)`

输出：

- `FundamentalAnalysisResult`

如果传入 `output_path`，会额外保存最终 JSON。

## 4. CLI 用法

```bash
python -m src.fundamental_skill.pipeline \
  --input tests/fixtures/pipeline_sanhua_mock.json \
  --output output/fundamental_sanhua.json
```

控制台会打印：

- stock_code
- stock_name
- strategy_type
- status
- confidence
- fundamental_score
- readiness_level
- context_quality
- score_confidence
- risk_flags count
- must_track_indicators count

## 5. pipeline_trace 字段

最近一次运行的 trace 保存在 `pipeline.last_trace`：

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

Trace 用于调试和审计，不写入最终 `FundamentalAnalysisResult`。

## 6. 当前限制

- 不接 LLM。
- 不调用 AkShare。
- 不生成 HTML。
- 不做技术面分析。
- 不实现 `trader_skill`。
- 不联网做真实股票验证。
- 分类准确性仍受规则关键词覆盖范围影响。

## 7. 为什么它仍然不是交易系统

Pipeline 只输出基本面结构化结果，且最终 `status` 只表示基本面对后续交易员 Agent 评估的支持程度。它不会输出仓位、价格、止盈止损或任何交易动作，也不会根据技术面或交易纪律做最终决策。

## 8. advanced_manufacturing_growth 示例

第九阶段后，`pipeline_sanhua_mock.json` 会被识别为 `advanced_manufacturing_growth`。该类型用于高端制造成长股，重点关注汽车热管理、机器人执行器、工业自动化、精密制造零部件、新能源车供应链等。

三花智控 mock 的 pipeline 输出会继续提示机器人相关业务仍需订单和收入验证，避免把新闻或布局直接写成确定性收入贡献。

第九阶段补丁后，三花智控 mock 还会触发 Advanced Manufacturing Risk Guard：

- 机器人业务兑现验证不足：机器人执行器相关业务为布局/待验证，未提供明确订单和收入贡献。
- 大客户依赖验证不足：出现特斯拉供应链和大客户逻辑，但缺少客户收入占比和订单持续性数据。
- 估值预期消化风险：PE TTM 较高时，需要后续业绩增长消化。

这些风险会进入最终 `risk_flags`，并影响 scoring constraints 和最终 confidence。
