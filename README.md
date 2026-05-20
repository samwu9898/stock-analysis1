# A 股 Fundamental Skill AI Analyst System

> 面向 A 股基本面研究的 deterministic pipeline + AI analyst layer。
>
> 本项目已经从早期的 AkShare 个股 HTML 报告生成器，重构为 `fundamental_skill` 基本面 AI 分析系统。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 项目定位

`fundamental_skill` 是 A 股基本面分析 Skill。它负责把公开数据整理为可审计的基本面判断、证据包和 AI 分析提示词，用于研究公司基本面、行业框架、财务质量、估值上下文、风险、催化因素和后续跟踪指标。

它不是交易系统，不是技术面系统，不连接交易账户，也不输出交易建议。系统输出的 `confidence` 表示对当前 `fundamental_view` 的证据置信度，不代表正向强度、上涨概率或投资吸引力。

## 当前核心能力

- `RealDataConnector v2.3a`：从公开数据源获取 A 股基础信息、财务指标、估值、主营构成、资产负债表字段、研发费用和 capex 等，并保留 source trace。
- `ExternalCommodityPriceConnector v1.1`：为资源股补充配置化商品价格上下文，区分 domestic primary、fallback、stale、foreign reference 和 readiness eligibility。
- `FundamentalSkillPipeline`：串联 data adapter、classifier、framework selector、readiness planner、analysis context、scoring engine 和 result assembler。
- Evidence Pack：把 deterministic pipeline 输出和 raw blocks 压缩成 AI 可消费、可审计的证据包。
- AI Prompt / AI Report：生成模型可用的基本面分析提示词；当前以 `prompt_only` 工作流为主。
- Dashboard v2：本地 Streamlit viewer / auditor，用于查看 AI report、prompt、evidence pack、source trace、fundamental JSON 和 raw JSON。
- Industry Framework Workflow：用标准流程扩展行业框架，避免把单只股票、主题热度或 proxy 当成基本面事实。

## strategy_type

当前支持的 `strategy_type`：

- `resource_swing`
- `resource_core`
- `right_trend_growth`
- `semiconductor_cycle`
- `stable_growth`
- `advanced_manufacturing_growth`
- `satellite_communication_infrastructure`
- `low_altitude_economy_infrastructure`
- `life_science_cxo_services`
- `theme_only`
- `unknown`

## 当前数据覆盖

当前 raw / normalized / evidence 层覆盖或可暴露的主要字段包括：

- `basic_info`
- `financial_indicator`
- `valuation`
- `business_composition`
- `commodity_prices`
- `inventory`
- `accounts_receivable`
- `contract_liabilities`
- `r_and_d_expense`
- `r_and_d_expense_ratio`
- `capex`

部分字段依赖公开数据源可用性。缺失字段会进入 missing fields、warnings、data limitations 或 source trace，而不是被系统硬猜。

## 使用方式

### 1. 创建环境

```bash
conda create -n fundamental-skill python=3.10
conda activate fundamental-skill
pip install -r requirements.txt
```

### 2. 运行测试

```bash
python -m pytest tests
```

### 3. 运行 regression suite

```bash
python scripts/run_regression_suite.py
```

### 4. 运行真实股票 pipeline

```bash
python -m src.fundamental_skill.real_stock_runner --code 601698 --output output/fundamental_601698.json --force-refresh
```

该命令会通过 `RealDataConnector` 生成 raw JSON，并通过 `FundamentalSkillPipeline` 输出结构化基本面结果。

### 5. 生成 AI analyst prompt

```bash
python -m src.fundamental_skill.ai_analyst.runner --code 601698 --mode prompt_only
```

`prompt_only` 会读取 `output/fundamental_<code>.json` 和 `output/raw_<code>.json`，生成：

- `output/evidence_pack_<code>.json`
- `output/ai_prompt_<code>.md`

### 6. 打开 Dashboard v2

```bash
streamlit run dashboard/fundamental_dashboard.py
```

Dashboard v2 是本地查看和审计工具，不调用模型 API，不连接账户，不生成交易动作。

## 示例命令

```bash
python -m src.fundamental_skill.real_stock_runner --code 601698 --output output/fundamental_601698.json --force-refresh
python -m src.fundamental_skill.ai_analyst.runner --code 601698 --mode prompt_only
streamlit run dashboard/fundamental_dashboard.py
```

## 安全边界

系统输出必须遵守以下边界：

- 不输出买入、卖出、加仓、减仓、清仓、止损、止盈、目标价、满仓、梭哈等交易动作或承诺性表达。
- 不做交易执行。
- 不做技术面分析，不引入技术指标。
- 不连接交易账户。
- `confidence` 不是正向强度，而是对当前 `fundamental_view` 的证据置信度。
- proxy 不能当事实，例如合同负债只能作为订单可见度 proxy，不能等同真实订单或 backlog。
- capex 只能表示长期资产购建现金支出，不能直接证明产能释放或未来增长确定性。
- 研发费用率只能表示研发强度，不能直接证明技术壁垒。

## Neutral Naming Compatibility v1

`fundamental.v1` 当前已完成中性命名迁移，同时保留历史 JSON 的兼容字段：

- `analyst_summary` 是推荐的基本面分析摘要字段。
- `downstream_review_hint` 是推荐的后续复核提示字段。
- `trader_summary` 已 deprecated，仅为 backward compatibility 保留。
- `action_hint_for_trader` 已 deprecated，仅为 backward compatibility 保留。

AI layer 和 Dashboard 优先使用 `analyst_summary` / `downstream_review_hint`，仅在读取旧文件时回退到 legacy 字段。当前项目仍不实现 `trader_skill`，不连接交易账户，不输出交易建议。

## 开发流程

新增或扩展行业框架时，遵循 `docs/INDUSTRY_FRAMEWORK_DEVELOPMENT_WORKFLOW.md`：

```text
Out-of-Sample Audit
-> Design Audit
-> Optional External Review
-> Design Revision
-> Implementation
-> Acceptance
-> Commit
```

核心原则：

- 先观察 out-of-sample 框架缺口，再设计边界。
- 按商业模式扩展，不按单只股票或热门主题扩展。
- 实现前明确 required / preferred / optional data、confidence caps、risk guards、must-track indicators 和 regression samples。
- proxy 必须标注为 proxy，不能被 AI report 当成事实。
- 文档规划阶段不要求跑测试；代码或行为变更阶段需要跑 `pytest` 和 regression suite。

## 当前限制

- 新闻源仍可能失败，且新闻只能作为公开文本材料或低权重上下文。
- 部分行业专属数据仍缺失，例如客户结构、项目验收、容量利用率、卫星剩余寿命、运营小时、飞行架次等。
- AI report 当前以 `prompt_only` 为主；API 模式在 v1 中未实现。
- 行业框架仍需逐步扩展，现有框架不应被当成所有 A 股公司的完整行业分类体系。
- `output/`、`data/`、`cache/` 等运行产物和缓存不应提交。

## 文档入口

- `docs/FUNDAMENTAL_SKILL_SPEC.md`：`fundamental_skill` 输出契约、模块边界和 pipeline 说明。
- `docs/FUNDAMENTAL_AI_ANALYST_LAYER_SPEC.md`：Evidence Pack、AI Prompt、AI Report 和 Dashboard v2 说明。
- `docs/REAL_DATA_CONNECTOR_AUDIT.md`：真实公开数据连接器版本、字段映射、source trace 和限制。
- `docs/INDUSTRY_FRAMEWORK_DEVELOPMENT_WORKFLOW.md`：新增行业框架的标准流程。
- `docs/INDUSTRY_FRAMEWORK_TEMPLATE.md`：行业框架设计模板。
- `docs/SATELLITE_COMMUNICATION_FRAMEWORK_DESIGN_AUDIT.md`：卫星通信基础设施框架设计审计。
- `docs/LOW_ALTITUDE_ECONOMY_INFRASTRUCTURE_DESIGN_AUDIT.md`：低空经济基础设施框架设计审计。
- `docs/LIFE_SCIENCE_CXO_SERVICES_DESIGN_AUDIT.md`：生命科学 CXO 服务框架设计审计。

## 项目来源

本仓库来源于原始 `stock-analysis` 项目，早期目标是基于 AkShare 生成个股 HTML 深度报告。当前项目已经重构为 A 股 `fundamental_skill` AI analyst system，旧的 HTML 报告生成器、K 线展示和交易式表达不再是项目首页所描述的主线能力。

## 许可证

[MIT License](LICENSE)

## 致谢

- [AkShare](https://github.com/akfamily/akshare)：公开数据聚合来源。
- 原始 `stock-analysis` 项目：提供了早期项目基础。
