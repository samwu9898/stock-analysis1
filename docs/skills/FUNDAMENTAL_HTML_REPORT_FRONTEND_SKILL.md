# Fundamental HTML Report Frontend Skill

Date: 2026-05-21

Purpose: define the project-specific frontend design skill for future `Fundamental HTML Report Generator` work. This document only governs HTML report frontend presentation, visual hierarchy, report structure, language quality, and safety boundaries. It does not change code, renderer logic, prompt builder, schema, pipeline, or tests.

## 1. Skill Positioning

This skill is dedicated to A-share fundamental HTML research reports.

It is used to guide future Codex work on the HTML report renderer, visual optimization, and report-structure upgrades for `Fundamental HTML Report Generator`.

This is not a generic web design skill. It is not a trading terminal skill. It must not produce trading advice, position-management advice, technical-analysis conclusions, or execution-oriented UI.

The expected output style is a professional Chinese fundamental research report: evidence-grounded, visually clear, dense enough for serious analysis, and explicit about uncertainty.

## 2. Reference Object

Primary reference:

- `examples/个股研究-中国长城.html`

Learn from the reference page's presentational strengths:

- strong first-screen visual hierarchy;
- sticky navigation and clear anchor rhythm;
- Hero area with an immediate company and report identity;
- prominent core conclusion block;
- company profile card;
- recent fundamental updates;
- modular cards for business, macro, industry, chain, quality, valuation, risk, and tracking;
- risk cards and risk-level badges;
- score bars and quality-diagnosis visuals;
- industry-chain map;
- scenario cards;
- tracking plan and review conditions.

Do not copy or inherit the reference page's trading or technical-analysis content. Any K-line, target price, buy/sell language, position sizing, stop-loss/take-profit, return-risk ratio, trading timing, or technical-analysis pattern in the reference page is explicitly out of scope.

## 3. Required Report Modules

Future Fundamental HTML Report frontend work must preserve or strengthen the following modules when the underlying data supports them:

1. 顶部 Hero
2. 核心结论高亮卡
3. 公司画像
4. 近期基本面动态
5. 主营业务构成
6. 关键财务指标
7. 财务质量诊断
8. 核心命题与基本面矛盾
9. 宏观与行业周期
10. 产业链与商业模式
11. 六维质量评分
12. 基本面弹性公式
13. 估值解释
14. 风险分析
15. 必须跟踪指标
16. 后续基本面复核条件
17. 数据质量与无法判断事项
18. 安全边界说明

The first screen should let a Chinese fundamental-research reader understand the company identity, current core thesis, evidence confidence, main contradiction, and missing-data boundary without scrolling deeply.

## 4. Forbidden Content And Boundaries

The renderer, report copy, navigation, cards, badges, charts, and tables must not introduce:

- K线;
- 技术指标;
- 技术面分析;
- 买入 / 卖出;
- 加仓 / 减仓 / 清仓;
- 仓位;
- 止损 / 止盈;
- 目标价;
- 盈亏比;
- 买卖时机;
- 交易终端 UI;
- `trader_skill`;
- `technical_skill`;
- 账户接入.

Must-track indicators are monitoring variables for fundamental review, not action triggers. Risk and invalidation language must be framed as "基本面复核条件", "逻辑削弱条件", or "需要继续观察的证据", not as stop-loss, entry, exit, or trade timing.

Valuation explanation is allowed only as fundamental context, such as valuation method, valuation comparability, valuation assumptions, historical range interpretation, and data limitations. It must not become a target-price module or an action recommendation.

## 5. Visual Specification

The preferred visual direction is a polished dark-theme Chinese research workspace, with optional light-theme switching.

Required visual patterns:

- dark theme as the default or primary design direction;
- light theme toggle support when feasible;
- sticky nav for major report anchors;
- Hero section with a strong visual anchor and compact report identity;
- prominent core conclusion area with high information density;
- card-based report modules;
- consistent table styling;
- badge labels for status, evidence quality, data coverage, and classification;
- risk-level badges;
- score bars for quality dimensions;
- scenario cards for fundamental cases, without target prices or trading actions;
- industry-chain map for upstream, company position, downstream, customers, and value capture;
- responsive mobile layout with no horizontal page overflow;
- tables must scroll inside their containers on small screens;
- all Chinese user-visible report layer text must be localized in Chinese.

Avoid decorative excess. The report should feel serious, structured, and research-oriented rather than like a marketing landing page or trading dashboard.

## 6. Research Language Specification

Report language must not merely repeat field values.

Every important metric or data point should explain:

- what the data says;
- why it matters;
- how it affects the fundamental conclusion;
- whether it is a fact, proxy, or inference.

Core conclusions must read like analyst judgment, not raw data assembly. They should synthesize business quality, financial quality, cycle position, valuation interpretability, risk, and evidence gaps.

Facts, proxies, and inferences must be clearly separated:

- Fact: directly supported by reported data or source material.
- Proxy: indirect indicator used because direct data is unavailable.
- Inference: reasoned judgment derived from facts and proxies.

If data is missing, insufficient, stale, or not comparable, the report must say "无法判断" or an equivalent Chinese limitation statement. Missing data must not be silently converted into a confident conclusion.

Do not fabricate orders, customers, market share, industry ranking, peer percentile, policy impact, or competitive position. If these are not in available evidence, mark them as unknown or requiring follow-up.

## 7. Frontend Acceptance Checklist

For any future Fundamental HTML Report frontend optimization, Codex must check:

- 是否像专业中文基本面研报；
- 是否第一屏能看懂公司核心命题；
- 是否核心结论有判断密度；
- 是否模块清晰；
- 是否视觉层级强；
- 是否无交易/技术越界；
- 是否移动端可读；
- 是否没有横向溢出；
- 是否表格在容器内滚动；
- 是否没有英文模块标题残留；
- 是否明确展示数据质量、缺失数据与无法判断事项；
- 是否保留安全边界说明。

If any item fails, frontend work is not complete.

## 8. Future Usage

以后凡是优化 Fundamental HTML Report 前端，Codex 必须先阅读：

- `docs/skills/FUNDAMENTAL_HTML_REPORT_FRONTEND_SKILL.md`

Codex must strictly follow this document's visual rules, module requirements, research-language requirements, and safety boundaries before changing any renderer, prompt, schema, pipeline, or test related to Fundamental HTML Report frontend presentation.
