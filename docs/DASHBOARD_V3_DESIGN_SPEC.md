# Dashboard v3 与 AI Report Markdown v2 展示规格

日期：2026-05-21

## 1. 阶段定位

本阶段只定义 Dashboard v3 和 AI Report Markdown v2 的展示规格，不实现代码，不修改 AI report schema，不修改 deterministic pipeline，不修改 classifier、connector、scoring、readiness，不新增 `strategy_type`。

Dashboard v3 的定位是：

- A 股基本面 AI 分析报告阅读器。
- 同时保留审计能力。
- 主视图服务于快速理解结论、证据、风险、缺口。
- 原始 JSON、数据来源追踪、prompt 预览只作为默认折叠的审计材料。
- 不做交易终端，不输出交易建议，不展示技术面图表。

中文主标题：

```text
A股基本面 AI 分析看板
```

## 2. 设计边界

Dashboard v3 不应实现：

- 交易账户连接。
- 买卖建议、目标价、仓位、买卖动作。
- 技术面图表、技术指标、交易终端 UI。
- `technical_skill`、`trader_skill`。
- 自动调用 API 生成报告。
- raw JSON 主视图。
- 任何会让用户以为系统在给交易动作的设计。

展示层必须反复表达：本系统只做基本面研究展示与审计，不做交易动作输出。

## 3. 中文化规则

Dashboard v3 和 AI Report Markdown v2 的所有用户可见主内容必须使用中文。

必须中文化的内容包括：

- 主视图标题、模块标题、按钮、标签、badge、提示语、warning、表格列名。
- AI Report Markdown v2 的全部标题。
- `strategy_type`、`sub_type`、`confidence`、`fundamental_view`、`status` 等英文内部字段的展示解释。

允许保留英文原始字段名的区域：

- 数据来源追踪。
- 原始 JSON。
- Debug audit。
- Prompt 预览。

这些区域必须默认折叠。

主视图不得出现未翻译的英文模块标题，例如 `One-line View`、`Evidence Map`、`Supporting Evidence`、`Limiting Evidence`、`Missing Evidence`、`Risk Flags`、`Must-Track Indicators`、`Data Quality`、`Report stale`、`Source Trace`、`Raw JSON`。

`confidence` 必须展示固定解释：

```text
置信度表示对当前基本面结论的证据置信度，不等于看好程度。
```

deprecated 字段不得在主视图展示：

- `trader_summary`
- `action_hint_for_trader`

主视图应使用：

- `analyst_summary`
- `downstream_review_hint`

历史 JSON fallback 可以存在，但 UI 不应把 deprecated 字段名作为主语义展示。审计折叠区展示 raw JSON 时可以出现这些字段。

## 4. 术语映射

### 4.1 strategy_type 中文解释

| 原值 | 中文展示 |
| --- | --- |
| `satellite_communication_infrastructure` | 卫星通信基础设施 |
| `low_altitude_economy_infrastructure` | 低空经济基础设施 / 运营服务 |
| `life_science_cxo_services` | CXO 医药外包服务 |
| `advanced_manufacturing_growth` | 高端制造成长 |
| `semiconductor_cycle` | 半导体周期 |
| `resource_swing` | 资源弹性 |
| `resource_core` | 资源核心 |
| `right_trend_growth` | 高景气成长 |
| `stable_growth` | 稳健成长 |
| `theme_only` | 题材型 |
| `unknown` | 未知 / 暂无法归类 |

展示格式建议：

```text
satellite_communication_infrastructure（卫星通信基础设施）
```

### 4.2 sub_type 中文解释

| 原值 | 中文展示 |
| --- | --- |
| `aviation_operations_service` | 通航 / 低空飞行运营服务 |
| `airspace_platform_system` | 空域平台 / 调度系统 |
| `integrated_cxo_platform` | 综合 CXO 平台 |
| `cdmo_manufacturing_services` | CDMO 生产制造服务 |
| `clinical_cro_services` | 临床 CRO 服务 |
| 空值 | N/A / 不适用 |

### 4.3 status 与 fundamental_view 中文解释

| 原值 | 中文展示 |
| --- | --- |
| `supportive` | 基本面支持进一步研究 |
| `neutral` | 中性，需要更多证据 |
| `negative` | 基本面不支持 |
| `insufficient_data` | 数据不足，无法可靠判断 |
| `supportive_for_further_evaluation` | AI 观点：支持进一步研究 |
| `neutral_requires_more_evidence` | AI 观点：中性，需要更多证据 |
| `not_supportive` | AI 观点：不支持 |
| `insufficient_data` | AI 观点：数据不足 |

### 4.4 confidence 中文解释

| 原值 | 中文展示 |
| --- | --- |
| `high` | 高证据置信度 |
| `medium` | 中等证据置信度 |
| `low` | 低证据置信度 |

必须同时展示固定说明：置信度表示对当前基本面结论的证据置信度，不等于看好程度。

## 5. Dashboard v3 信息架构

### 5.1 顶部结论区

顶部 Hero 卡片是主视图第一屏核心，不再把 schema / safety 状态放在最显眼位置。

必须展示：

- 股票代码。
- 公司名称。
- 分析框架：`strategy_type` 原值 + 中文解释。
- 子类型：`sub_type` 原值 + 中文解释；为空时显示 `N/A / 不适用`。
- 规则基本面状态：来自 deterministic `status`。
- AI基本面观点：来自 AI report `fundamental_view`。
- 证据置信度：来自 deterministic `confidence`，带固定解释。
- 基本面评分：来自 `fundamental_score`。
- 报告质量状态：正常 / 自由文本损坏 / 报告过期 / 报告不一致 / 结构或安全校验未通过。
- 结构校验 / 安全校验 / 乱码检测：简洁 badge，不抢主视觉。

### 5.2 一句话结论

优先展示：

1. deterministic `analyst_summary`。
2. AI `executive_summary`，仅当报告质量正常且未 stale/mismatch。

如果 AI report 过期或不一致，主视图不得把旧 AI `executive_summary` 当作可信主报告展示，应显示 warning，并提示重新生成 AI report。

### 5.3 为什么是这个结论？

用 3 到 5 条中文 bullet 解释：

- 为什么是当前规则基本面状态。
- 为什么是当前证据置信度。
- 哪些证据支持当前结论。
- 哪些证据限制当前结论。
- 哪些关键缺口阻止高证据置信度。

该区应从 `confidence_basis`、`supporting_evidence`、`limiting_evidence`、`unknown_or_missing_evidence`、`risk_flags`、`missing_fields` 组合生成，不应展示大段原始 JSON。

### 5.4 证据地图

三列卡片展示，不默认使用大 dataframe：

- 支持证据。
- 限制因素。
- 缺失证据。

每张卡片建议字段：

- 证据名称。
- 当前值。
- 为什么重要。
- 影响维度。
- 来源。
- 对置信度的影响。

### 5.5 风险提示与证据缺口

风险提示必须比 v2 更突出。

展示规则：

- `high` severity risk flags 以卡片优先展示。
- `medium` 和 `low` 可在同区下方折叠或列表展示。
- 如果 `risk_flags` 为空，但 high-priority missing evidence 很多，必须展示“关键证据缺口”。
- 不允许让用户误以为 `risk_count=0` 就是没有风险。

推荐 warning 文案：

```text
当前结构化风险项为 0，但仍存在高优先级证据缺口；这表示风险尚未被充分识别或量化，不表示没有风险。
```

### 5.6 必须跟踪指标

用简洁表格，按优先级排序：

- 默认展示 `high` / `medium`。
- `low` 默认折叠。

列名必须中文：

| 列名 | 来源字段 |
| --- | --- |
| 指标 | `indicator_name` |
| 状态 | `current_status` |
| 优先级 | `priority` |
| 当前值 | `current_value` |
| 为什么重要 | `why_it_matters` |
| 下一步需要验证的证据 | `follow_up_question` |

### 5.7 置信度拆解

展示五维 confidence basis，并用中文维度名：

| 原维度 | 中文展示 |
| --- | --- |
| `data_coverage` | 数据覆盖 |
| `financial_quality` | 财务质量 |
| `valuation_interpretability` | 估值可解释性 |
| `growth_validation` | 成长 / 框架验证 |
| `risk_identifiability` | 风险可识别性 |

### 5.8 数据质量与缺口

展示：

- 缺失字段数量。
- `latest_news` 抓取失败或缺失。
- source gaps。
- stale / mismatch warnings。
- fetch_status 摘要。

该区仍是主视图，但应是中文摘要，不是 raw JSON。

### 5.9 报告新鲜度 / 一致性

必须比较 AI report 与 fundamental/evidence 的关键字段：

- `stock_code`。
- `strategy_type`。
- `sub_type`。
- `status` / `fundamental_view`。
- `generated_at` / `analysis_date` / `data_timestamp` / 文件修改时间。

如果不一致，显示：

```text
报告过期 / 报告不一致
```

处理规则：

- stale report 不应作为可信主报告展示。
- 可展示 deterministic 结论、evidence pack、缺口和审计材料。
- AI report 正文默认隐藏或降级为“旧报告审计材料”。
- 优先提示重新生成 AI report。

### 5.10 审计材料

以下内容默认折叠：

- 完整 evidence pack。
- 数据来源追踪。
- 原始 JSON。
- fundamental JSON。
- prompt 预览。
- fetch_status。
- legacy / deprecated fields。

折叠区标题也必须中文，例如：

- 完整证据包。
- 数据来源追踪。
- 原始 JSON。
- 规则结果 JSON。
- Prompt 预览。
- 抓取状态。
- 历史兼容字段。

## 6. 报告 stale / mismatch 检测设计

### 6.1 对比对象

Dashboard helper 应生成一个只供展示层使用的 `report_consistency_status`，不改 schema。

建议输入：

- `ai_report_<code>.json`
- `ai_report_<code>.md`
- `evidence_pack_<code>.json`
- `fundamental_<code>.json`
- 文件修改时间

### 6.2 字段对比

| 检查项 | 规则 |
| --- | --- |
| 股票代码 | AI report `stock_code` 必须等于 evidence/fundamental stock code |
| 分析框架 | AI report 可无 `strategy_type` 字段；若正文或 markdown 明确出现旧框架，应与 evidence/fundamental 对比 |
| 子类型 | evidence/fundamental 有 `sub_type` 时，AI report 正文或 markdown 不应仍描述为旧框架或 unknown |
| 状态 / 观点 | deterministic `status` 与 AI `fundamental_view` 应语义一致 |
| 生成时间 | AI report 文件修改时间不应早于 evidence/fundamental 文件修改时间 |
| 质量状态 | schema/safety/garbled 失败时，报告不能作为可信主报告 |

### 6.3 状态分类

| 状态 | 中文展示 | 主视图行为 |
| --- | --- | --- |
| `ok` | 报告正常 | 展示 AI report 主体 |
| `missing` | 尚无 AI 报告 | 展示 prompt 生成指引和 evidence/fundamental |
| `stale` | 报告过期 | 隐藏 AI 正文，提示重新生成 |
| `mismatch` | 报告不一致 | 隐藏 AI 正文，展示不一致字段 |
| `schema_failed` | 结构校验未通过 | 隐藏 AI 正文 |
| `safety_failed` | 安全校验未通过 | 隐藏 AI 正文 |
| `garbled` | 自由文本损坏 | 使用结构化 evidence fallback，提示重新生成 |

### 6.4 603259 示例

603259 当前应触发 `mismatch`：

- fundamental/evidence：`life_science_cxo_services`。
- fundamental/evidence：`integrated_cxo_platform`。
- 旧 AI report：仍描述为 `unknown` / framework gap。

主视图应显示：

```text
报告不一致：规则结果和证据包已识别为 CXO 医药外包服务 / 综合 CXO 平台，但当前 AI report 仍使用旧的 unknown 结论。请重新生成 AI report。
```

## 7. AI Report Markdown v2 模板

所有标题必须中文。

```markdown
# <股票代码> <公司名称> AI基本面分析报告

## 一句话结论

> 置信度表示对当前基本面结论的证据置信度，不等于看好程度。

## 公司身份与分析框架

- 股票代码：
- 公司名称：
- 分析框架：
- 子类型：
- 规则基本面状态：
- AI基本面观点：
- 证据置信度：
- 基本面评分：

## 结论速览

- 为什么是当前结论：
- 主要支持证据：
- 主要限制因素：
- 关键证据缺口：

## 状态与置信度解释

## 证据地图

### 支持证据

### 限制因素

### 缺失证据

## 行业框架检查

- strategy_type：
- 中文解释：
- sub_type：
- 中文解释：
- 框架适用边界：
- 不能过度解释的 proxy：

## 必须跟踪指标

| 指标 | 状态 | 优先级 | 当前值 | 为什么重要 | 下一步需要验证的证据 |
| --- | --- | --- | --- | --- | --- |

## 风险提示

### 风险一

- 严重程度：
- 风险说明：
- 证据依据：
- 仍缺失的验证材料：

## 后续复核条件

## 数据质量与来源限制

## 安全边界说明

本报告仅用于 A 股基本面研究展示与审计，不提供交易建议，不提供目标价，不提供仓位建议，不使用技术面图表，不连接交易账户。
```

Markdown v2 要求：

- 必须写明：置信度不是看好程度，而是证据置信度。
- Must-track 表格要精简，默认只放 high / medium。
- Risk 用结构化卡片式字段。
- Data limitations 单独成区。
- 行业框架检查必须显示 `strategy_type` / `sub_type` 并给中文解释。
- fallback warning 必须区分 AI 自由文本损坏、report stale / mismatch、schema/safety 不通过、garbled guard 命中。

## 8. 三个样本展示设计

### 8.1 601698 中国卫通

顶部结论区：

- 分析框架：`satellite_communication_infrastructure`（卫星通信基础设施）。
- 子类型：N/A / 不适用。
- 规则基本面状态：中性，需要更多证据。
- 证据置信度：低证据置信度。
- 基本面评分：展示 deterministic score。

主视图应突出：

- 容量利用率 / 出租率缺失。
- 客户结构 / 客户集中度缺失。
- 卫星剩余寿命缺失。
- 折旧摊销缺失。
- 转发器 / 带宽容量缺失。
- 合同负债只能作为订单可见度 proxy，不等于真实 backlog。
- capex 只代表长期资产购建现金支出，不等于新增容量确定释放。

展示重点：即使有基础财务、估值和业务构成，卫星通信基础设施框架的核心运营证据不足，因此 low confidence 合理。

### 8.2 000099 中信海直

顶部结论区：

- 分析框架：`low_altitude_economy_infrastructure`（低空经济基础设施 / 运营服务）。
- 子类型：`aviation_operations_service`（通航 / 低空飞行运营服务）。
- 规则基本面状态：中性，需要更多证据。
- 证据置信度：低证据置信度。

主视图应突出：

- 运营小时缺失。
- 飞行架次缺失。
- 机队规模缺失。
- 单飞行小时收入缺失。
- 安全监管事件缺失。
- 客户结构、合同金额、项目验收、政府项目依赖等缺口。

特殊提示：

- 如果 `risk_flags` 为 0，但高优先级 missing evidence 很多，必须显示“关键证据缺口”。
- 不能让用户理解为风险很少，只能理解为风险尚未被充分结构化识别。

### 8.3 603259 药明康德

顶部结论区：

- 分析框架：`life_science_cxo_services`（CXO 医药外包服务）。
- 子类型：`integrated_cxo_platform`（综合 CXO 平台）。
- 当前 AI report 应触发“报告过期 / 报告不一致” warning。

主视图应突出：

- backlog / 在手订单缺失。
- 新签订单缺失。
- 客户集中度缺失。
- 海外收入、美国收入、北美收入敞口缺失。
- 监管风险、地缘风险、Biosecure Act / 制裁风险需要显式跟踪。
- CDMO 产能利用率、临床项目数量、项目取消或延期、收款周期等缺口。
- 合同负债只能作为 partial proxy，不能等同 backlog。

旧 AI report 不应作为可信主报告展示，应放入折叠审计材料或显示为不一致报告。

## 9. 视觉设计方向

Streamlit 最小视觉改造即可：

- 顶部 Hero 卡片。
- status badge。
- confidence badge。
- report quality badge。
- risk severity badge。
- evidence cards。
- must-track priority badges。
- collapsible audit sections。
- 简洁表格，而不是全量 JSON-like dataframe。

不要求 CSS 大改，不要求复杂前端框架，不引入重型前端依赖。

## 10. 最小实现范围

v3 implementation 只应改：

- `dashboard/fundamental_dashboard.py`
- `src/fundamental_skill/dashboard_helpers.py`
- `src/fundamental_skill/ai_analyst/markdown_renderer.py`
- `tests/test_dashboard_helpers.py`
- `tests/test_ai_markdown_renderer.py`
- `docs`

不应改：

- pipeline。
- classifier。
- connector。
- scoring。
- readiness。
- schema。
- industry framework logic。
- regression expected，除非只是 dashboard helper 测试 fixture。

## 11. 验收标准

Dashboard v3 acceptance 应检查：

1. 601698 / 000099 / 603259 三个样本展示合理。
2. 顶部结论区完整。
3. `analyst_summary` 主展示。
4. `sub_type` 主展示。
5. confidence meaning 明确。
6. report stale / mismatch 可检测。
7. `risk_flags` 为 0 但 missing evidence 高时仍提示。
8. deprecated 字段不在主视图展示。
9. raw/source trace 默认折叠。
10. schema / safety / garbled guard 可见但不抢主视觉。
11. 用户可见主视图不得出现未翻译英文模块标题。
12. pytest 通过。
13. regression suite 通过。

## 12. 建议进入下一阶段

建议进入 Dashboard v3 Implementation，但实施时必须保持本规格的边界：

- 只做展示层和 helper 层改造。
- 不改 schema 和 deterministic pipeline。
- 不扩大行业框架。
- 不把 Dashboard 做成交易终端。
