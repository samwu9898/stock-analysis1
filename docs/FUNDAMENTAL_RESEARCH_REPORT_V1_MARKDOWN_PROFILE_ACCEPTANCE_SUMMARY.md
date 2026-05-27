# Fundamental Research Report V1 Markdown Profile Acceptance Summary

Date: 2026-05-28

Stage: Fundamental Skill Research Report V1 Cross-Industry Markdown Profile
Acceptance Summary.

Status: documentation-only acceptance summary. This stage read the three local
Markdown runtime artifacts listed below and synchronized documentation only. It
did not modify code, tests, fixtures, pipeline behavior, scoring / readiness,
Research Intelligence P1.1, HTML / Dashboard, regression expected files, or
runtime output. It did not run smoke tests, read `TUSHARE_TOKEN`, use the
network, call Tushare or AkShare, connect MCP, or provide buy / sell advice,
target prices, position sizing, portfolio weights, or technical trading
signals.

Accepted runtime artifacts reviewed:

- `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md`
- `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md`
- `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md`

Latest verification results are quoted from the current acceptance input and
were not rerun in this documentation-only stage:

- targeted tests `86 passed`
- full pytest `734 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

## 1. Final status

- `600406` Markdown accepted.
- `002371` Markdown accepted.
- `002050` Markdown accepted.
- Presentation profile registry accepted.
- Professional analyst voice gate accepted.
- Cross-industry Markdown validation passed.

This confirms that the first three Research Report V1 presentation profiles
have passed real-sample Markdown validation:

- `stable_growth_grid_equipment`
- `semiconductor_equipment_cycle`
- `advanced_manufacturing_thermal_management`

## 2. 三个 profile 验收表

| code | company | profile | industry focus | product readability score | cross-contamination result | evidence boundary result | accepted runtime artifact path | known limitations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | `stable_growth_grid_equipment` | 电网设备 / 数字电网 / 电力自动化 | 8/10 | Passed: 未混入半导体、晶圆厂、国产替代、机器人或热管理新业务语言。 | Passed: 保留候选字段、需复核字段、证据缺口和行业到公司兑现的 caveat；未输出交易建议。 | `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md` | 主营构成、主营业务官方来源和估值日期仍需后续证据增强；仍是投资经理版初稿，不是最终正式研报。 |
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | 半导体设备 / 国产替代 / 晶圆厂 capex | 7.5/10 | Passed: 未混入电网、国网 / 南网、特高压、热管理、制冷或新能源车语言。 | Passed: profile 只改变表达顺序和行业语言，不改变 evidence label；capex、国产替代、研发投入、客户验证均未写成公司已兑现事实。 | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md` | 内容厚度仍偏 V1 初稿；后续应把 `capex` 统一中文为“资本开支”，并补强订单、交付、验收、收入确认和回款证据。 |
| `002050` | 三花智控 | `advanced_manufacturing_thermal_management` | 热管理 / 制冷控制 / 新能源车 / 新业务可选项 | 8/10 | Passed: 未混入电网、国网 / 南网、特高压、半导体设备、晶圆厂或国产替代语言。 | Passed: 新能源车热管理和机器人 / 新业务均保留为待验证路径或可选项；未把行业空间写成公司确定性收入或利润。 | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` | 内容厚度仍偏 V1 初稿；`capex` 后续建议统一中文为“资本开支”；新业务收入占比、客户结构、订单和回款证据仍需补足。 |

## 3. Cross-contamination summary

- `600406` 未混入半导体 / 机器人新业务语言。
- `002371` 未混入电网 / 热管理语言。
- `002050` 未混入电网 / 半导体设备语言。
- 当前 V1 hard-fail 防串味策略有效：profile-specific terms 没有从一个
  profile 泄漏到另一个 profile 的最终 Markdown 正文。
- 若未来要允许跨行业词，必须另行设计 evidence-label-aware allowlist。
  允许条件应至少包含明确输入证据、证据标签、来源说明、profile 不扩写和
  caveat 保留，不能只靠关键词命中放行。

## 4. Product readability summary

- Markdown 已明显优于 JSON：它把数据质量、行业逻辑、公司基本面、机会、
  风险、证据缺口、反证条件和后续跟踪变量组织成可读研究底稿。
- 三份报告都可以作为投资经理版初稿：阅读顺序清楚，行业语言与样本匹配，
  证据边界可见。
- 三份报告仍不是最终正式研报：内容厚度、证据密度、官方披露引用和展示层
  体验仍有空间。
- 还需要 HTML / Dashboard 展示层，让同一套 Research Report V1 输出能以更
  强的信息层级、视觉结构和审阅入口呈现。
- 还需要未来 live provider / official parser / evidence enrichment 提升内容
  厚度，尤其是官方公告、CNInfo、订单、客户、分部收入、收入确认和回款证据。

## 5. Known limitations

- `002371` 和 `002050` 内容厚度仍偏 V1 初稿。
- `002050` 中 `capex` 后续建议统一中文为“资本开支”。
- `002371` 中 `capex` 后续也建议统一中文为“资本开支”，以保持中文报告口径。
- 证据等级文字后续可进一步柔化，避免报告读感过于工程化。
- 当前只验证 3 个真实样本。
- 尚未做 HTML presentation。
- 尚未做 live provider report。
- 尚未做 official parser / CNInfo。
- 尚未做 fixture promotion / validator / primary switch。
- 尚未把 promote rules、validator、fixture promotion 或 Tushare primary 纳入
  当前阶段。

## 6. Next recommended stage

下一步建议进入 HTML presentation layer design / implementation。

HTML presentation layer 必须遵守以下边界：

- HTML 必须消费 Markdown / presentation-layer output 或 Research Report V1
  structured payload。
- HTML 不得重新分析、不改结论、不隐藏 caveat。
- HTML 不得调用 provider、不联网、不读 token。
- HTML 不得把候选字段、行业叙事、P1.1 问题或 profile language 升级为
  verified fact。
- HTML 应保留免责声明、证据等级、数据质量说明、证据缺口、反证条件和后续
  跟踪变量。
- promote rules / validator / fixture promotion / Tushare primary 仍后置。

## 7. Safety

本阶段确认：

- 不读 token。
- 不联网。
- 不调用 provider。
- 不接 MCP。
- 不写 `output`。
- 不提交 runtime artifacts。
- 不输出投资建议。

Documentation-only 结论：三套 presentation profiles 已通过真实样本 Markdown
验证，可以作为进入 HTML presentation layer 的前置结论。
