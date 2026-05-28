---
name: fundamental-skill
description: A 股基本面研究报告 Skill。当前默认入口是已验收的 Research Report V1 single-stock offline CLI baseline：读取本地 accepted artifacts，复用或生成 Research Report V1 JSON / Markdown / HTML presentation output，返回 HTML / Markdown / JSON 路径、中文摘要、机会、风险、证据缺口和数据质量状态。默认不联网、不读 token、不调用 provider、不接 MCP，不输出交易建议、目标价、仓位或技术面交易信号。
trigger_keywords: ["分析股票", "个股分析", "股票研究", "基本面分析", "研究报告", "fundamental report"]
version: 3.0
last_updated: 2026-05-28
variant: offline-local-artifacts
---

# A 股基本面研究报告 Skill

## 当前身份

`fundamental_skill` 是一个 evidence-driven、artifact-driven 的 A 股基本面研究报告 Skill。当前已验收的用户入口是 Research Report V1 single-stock offline CLI baseline。

它的默认工作方式是读取本地 accepted artifacts，通过已验收的 offline orchestration 链路定位或复用 Research Report V1 JSON / Markdown / HTML artifacts，并返回：

- HTML / Markdown / JSON 路径；
- 中文摘要；
- 最大机会；
- 最大风险；
- 最大证据缺口；
- 数据质量状态；
- 基本面研究边界声明。

HTML 是 accepted renderer / presentation output，不是模型自由手写内容。Research Report V1 artifact chain 是当前正式报告路径：

```text
accepted local artifacts
-> Research Report V1 JSON
-> accepted Markdown presentation
-> accepted HTML renderer
-> HTML / Markdown / JSON paths + Chinese summary
```

## 当前默认调用方式

股票代码方式：

```bat
python -m src.fundamental_skill.research_report.generate_report --code 600406 --format html --data-mode offline_local_artifacts
```

公司名方式：

```bat
python -m src.fundamental_skill.research_report.generate_report --company-name 北方华创 --format html
```

当前已验收样本：

- `600406` 国电南瑞；
- `002371` 北方华创；
- `002050` 三花智控。

当前 baseline 已冻结为 single-stock offline CLI。默认路径是 `offline_local_artifacts` / `no_live_provider` / no token / no network / no MCP。

## 当前能力边界

本 Skill 可以：

- 通过已验收 CLI 返回单票 Research Report V1 artifacts；
- 展示基本面研究摘要、机会、风险、证据缺口和数据质量状态；
- 保留 evidence labels、data-quality caveats、rebuttal conditions 和 follow-up variables；
- 使用本地 artifact chain 复用 accepted HTML presentation output；
- 在缺少本地 artifacts 时 fail closed，并返回缺失清单；
- 帮助用户理解当前证据支持什么、不能支持什么、仍需复核什么。

本 Skill 当前不做：

- live provider 默认调用；
- Tushare / AkShare / provider runtime 调用；
- provider 自动 merge；
- Tushare primary 自动切换；
- token 读取，包括 `TUSHARE_TOKEN`；
- 网络访问；
- MCP 连接；
- 自由生成报告绕过 Research Report V1 artifact chain；
- AI 自由手写 HTML 最终报告；
- runtime output 提交；
- batch report 或 Dashboard 生成。

## 禁止输出和解释边界

本 Skill 不输出：

- 买入、卖出、持有、加仓、减仓、清仓等建议；
- 目标价；
- 仓位、组合权重或账户操作；
- 技术面交易信号；
- K 线、均线、量价、择时或执行建议；
- 承诺性收益表达。

本 Skill 也不得把证据边界写错：

- candidate fact 不能写成 `verified_fact`；
- 行业叙事不能写成公司兑现；
- policy / news / theme heat 不能写成经营事实；
- contract liabilities 只能是 partial proxy，不能写成真实 backlog；
- capex 只能是长期资产购建现金支出，不能写成产能释放或未来收入确定性；
- R&D expense ratio 只能表示研发强度，不能写成技术壁垒；
- data-quality caveat 不能隐藏。

## 当前已验收状态

- Research Report V1 JSON / Markdown / HTML chain accepted；
- professional analyst voice gate accepted；
- HTML renderer accepted；
- single-stock offline orchestration accepted；
- CLI implementation accepted；
- `600406` / `002371` / `002050` CLI runtime accepted；
- single-stock offline CLI baseline frozen；
- default path is offline local artifacts / no live provider / no token / no network / no MCP。

最近验收结果引用：

- targeted tests `163 passed`；
- full pytest `811 passed, 1 skipped`；
- regression `passed=47 failed=0 total=47`。

## 使用原则

当用户请求单票基本面研究报告时，优先使用当前 accepted CLI。返回结果应短而可操作：报告状态、HTML / Markdown / JSON 路径、中文摘要、最大机会、最大风险、最大证据缺口、数据质量状态和基本面研究边界声明。

除非进入新的已设计阶段，否则不要使用旧的 `stock_full_report.py` 三阶段流程，不要运行 AI 手写 HTML 流程，不要调用 `html_report_runner` 作为最终用户入口，不要主动请求 token、联网、调用 provider 或接 MCP。

## 后续方向

当前建议下一阶段是 batch / Dashboard design。Live provider report、official parser / CNInfo、MCP、Tushare token work、validator、fixture promotion、promote rules 和 Tushare primary switch 都属于 later work，必须另行设计、实现和验收。
