# Fundamental HTML Report Generation Skill

Date: 2026-05-22

Purpose: 固化“生成单只 A 股正式 HTML 基本面研报”的项目内执行流程，让用户以后只需要说“用 Fundamental HTML Report Generation Skill 生成 <股票代码> 的正式 HTML 基本面研报”，Codex 就能按标准流程准备证据、生成正式 JSON、渲染 HTML 并完成视觉审计。

本 skill 只编排现有正式研报生成流程；不得修改 deterministic pipeline、classifier、connector、scoring、readiness。

## 1. 触发方式

当用户提出以下任一需求时，Codex 必须使用本 skill：

- “用 Fundamental HTML Report Generation Skill 生成 002837 的正式 HTML 基本面研报”
- “生成 <股票代码> 的正式基本面 HTML 研报”
- “生成单只股票正式 HTML 基本面研报”

Codex 应先读取本文件，再执行 `scripts/generate_fundamental_html_report.py`。

## 2. 工作流总览

标准流程分三段：

1. Prepare：运行真实数据和 prompt 准备。
   - `real_stock_runner`
   - `ai_analyst runner` 的 `prompt_only`
   - `html_report_runner` 的 `prompt_only`
   - 输出下一步给 Codex/GPT 生成正式 JSON 的短任务说明

2. Formal JSON：由 Codex/GPT 基于 HTML report prompt 生成正式 `fundamental_html_report.v1` JSON。
   - 必须保存到 `output/reports/fundamental_report_<code>.json`
   - 不得调用 OpenAI API
   - 不得生成 skeleton 冒充正式报告

3. Render and visual audit：渲染正式 HTML，并做视觉审计。
   - `render_existing` 只接受正式 JSON
   - 输出 `output/reports/fundamental_report_<code>.html`
   - `visual_audit` 输出桌面首屏、移动首屏、全页截图和 manifest 到 `output/visual_audit/<code>/`

## 3. CLI 标准命令

Prepare：

```bash
python scripts/generate_fundamental_html_report.py --code <code>
```

渲染已保存的正式 JSON：

```bash
python scripts/generate_fundamental_html_report.py --code <code> --mode render_existing
```

渲染并截图审计：

```bash
python scripts/generate_fundamental_html_report.py --code <code> --mode render_existing --visual-audit
```

只对已存在正式 HTML 做视觉审计：

```bash
python scripts/generate_fundamental_html_report.py --code <code> --mode visual_audit
```

## 4. Formal JSON 要求

正式 JSON 必须满足：

- 顶层为单个 JSON object，不要 Markdown fence，不要解释性前后缀。
- `report_version` 必须为 `fundamental_html_report.v1`。
- 必须严格匹配 `src/fundamental_skill/ai_analyst/html_report_schema.py` 的 schema。
- 必须基于 `output/reports/fundamental_report_prompt_<code>.md` 中的 evidence pack、source trace、derived observation 和 missing evidence。
- 必须解释数据含义、基本面影响和证据置信边界，不能只复述字段。
- 必须区分事实、proxy 和推断。
- 缺失、过期、不完整或不可比的数据必须明确写“无法判断”“缺少数据，不足以判断”或等价限制。
- `confidence` 只能表示证据置信度，不能当成看好程度。
- `financial_ratio_caveats` 必须说明应收/收入、存货/收入、合同负债/收入等 stock-flow mixed ratio 的口径限制。
- `quality_score_breakdown` 是基本面质量维度评分，不是交易评级。
- `fundamental_scenario_analysis` 只能写基本面情景，不得写股价、目标价或交易动作。
- `valuation_explanation` 只能解释估值方法、可比性、假设、历史区间和限制，不得输出目标价。
- `must_track_indicators` 和 `tracking_plan_groups` 是基本面复核变量，不是交易触发器。

正式 JSON 必须保存到：

```text
output/reports/fundamental_report_<code>.json
```

## 5. 禁止内容和安全边界

全流程禁止输出：

- 交易建议
- 买入、卖出、加仓、减仓、清仓
- 仓位或账户动作
- 目标价
- 止损、止盈、盈亏比
- 技术面分析
- K线、均线、成交量、技术指标
- 买卖时机或价格执行依据
- `trader_skill`
- `technical_skill`
- 交易终端 UI 或账户接入

禁止编造：

- 订单、backlog、客户、份额、行业排名
- 产能释放
- 同业分位
- 未在 evidence pack 中出现的政策影响、竞争壁垒或业务进展

不得把合同负债直接等同为订单或 backlog；不得把 capex 直接等同为产能释放。

## 6. Skeleton 禁令

本 skill 生成的是正式 HTML 基本面研报。Codex 不得：

- 运行 `html_report_runner --mode skeleton` 来冒充正式报告。
- 把 skeleton JSON 放到 `output/reports/fundamental_report_<code>.json`。
- 把 skeleton HTML 放到正式报告路径。
- 在缺少正式 JSON 时伪造空壳报告。

如果正式 JSON 不存在，应停止渲染并要求先完成 Formal JSON 阶段。

## 7. Visual Audit 要求

正式 HTML 生成后必须运行 visual audit，除非用户明确要求只准备 prompt 或只渲染。

审计命令：

```bash
python scripts/generate_fundamental_html_report.py --code <code> --mode render_existing --visual-audit
```

审计产物：

- `output/visual_audit/<code>/desktop_first_screen.png`
- `output/visual_audit/<code>/mobile_first_screen.png`
- `output/visual_audit/<code>/full_page.png`
- `output/visual_audit/<code>/visual_audit_manifest.json`
- `output/visual_audit/<code>/visual_audit_notes.md`

Codex 必须检查：

- 桌面首屏是否能看清公司身份、研究主线、核心结论和证据边界。
- 移动首屏是否无重叠、无横向溢出、无被截断的关键文字。
- 全页是否没有大面积空白、错位、遮挡、断裂或表格溢出。
- 报告是否没有交易建议、目标价、仓位、技术面、K线等越界内容。
- 安全边界说明是否保留。

如果 visual audit 失败或截图不可用，不能宣布正式报告完成。

## 8. Git 边界

`output/reports` 和 `output/visual_audit` 属于生成产物，必须继续不入 git。当前项目通过忽略 `output/` 覆盖这些目录；本 skill 不得改变该边界。

## 9. Codex 执行清单

当用户要求生成某代码正式 HTML 基本面研报时：

1. 运行 prepare 命令。
2. 阅读 wrapper 输出的 `next_task` 和 `output/reports/fundamental_report_prompt_<code>.md`。
3. 生成正式 JSON，保存到 `output/reports/fundamental_report_<code>.json`。
4. 运行 `--mode render_existing --visual-audit`。
5. 检查 visual audit manifest 和截图。
6. 最终回复中列出 JSON、HTML、visual audit 产物和测试/审计状态。
