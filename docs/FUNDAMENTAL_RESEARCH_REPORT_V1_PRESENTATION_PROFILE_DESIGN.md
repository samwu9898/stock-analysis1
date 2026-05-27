# Fundamental Research Report V1 Presentation Profile Design

Date: 2026-05-28

Stage: Fundamental Skill Research Report V1 Multi-Strategy Presentation
Profile Design and Acceptance.

Status: design accepted, presentation profile registry accepted, and
cross-industry Markdown profile validation accepted for `600406`, `002371`, and
`002050`. This document does not modify tests, fixtures, pipeline behavior,
scoring / readiness, Research Intelligence P1.1, regression expected files,
runtime output, HTML / Dashboard, provider behavior, or evidence labels. The
acceptance-summary stage did not run smoke tests, read `TUSHARE_TOKEN`, use the
network, call Tushare or AkShare, connect MCP, or provide buy / sell advice,
target prices, position sizing, portfolio weights, or technical trading
signals.

## 1. 设计目标

`presentation profile` 是 Research Report V1 的中文展示层配置。它服务于
Markdown 报告和未来 HTML 报告，决定行业语言、研究框架、机会表达、风险表达
和后续跟踪变量如何组织。

它不是新的数据层、评分层或事实提升层：

- 不改变 Research Report V1 JSON builder。
- 不改变 candidate generator。
- 不改变 review decisions。
- 不改变 scoring / readiness。
- 不改变 Research Intelligence P1.1。
- 不改变 provider precedence、provider merge、数据读取、字段口径或本地输出。
- 不把候选事实、行业叙事或 P1.1 问题提升为 verified fact。

profile 只决定中文报告如何组织行业逻辑、机会、风险、证据缺口和跟踪变量。当前
600406 refined Markdown、002371 Markdown 和 002050 refined Markdown 已通过
真实样本验收，确认 profile layer 能避免 600406 的电网设备语言污染半导体设备
和热管理 / 先进制造报告。

## 2. 通用报告骨架与 profile 分离

Research Report V1 presentation 应保持统一中文骨架：

- 重要声明
- 一句话结论
- 投研速读
- 研究员判断
- 数据质量说明
- 宏观与行业逻辑
- 公司基本面
- 机会分析
- 风险分析
- 证据缺口
- 反证条件
- 后续跟踪清单

通用骨架负责可读性、一致的信息层级和证据边界。profile 负责行业语言和行业
研究路径。以下内容必须由选中的 profile 决定：

- 行业关键词。
- 机会排序。
- 风险排序。
- 核心跟踪变量。
- 行业传导路径。
- 禁止误写的 unsupported claims。
- 证据缺口重点。

骨架不得内置单一行业表达。尤其是电网投资、国网 / 南网、特高压等 600406
专属语言不得进入通用 renderer 默认文案。

## 3. 第一批 profile

### 3.1 `stable_growth_grid_equipment`

适用对象：

- `600406 国电南瑞`

定位：

- `stable_growth` 下的电网设备 / 电力自动化 first-version presentation
  profile。
- 适合表达电网投资、招标、数字电网、特高压 / 配网、电力自动化和经营质量
  检验路径。

关键词：

- 电网投资
- 国网 / 南网
- 特高压
- 配网
- 数字电网
- 电力自动化
- 继电保护
- 调度系统
- 电力信息通信
- 应收账款
- 经营现金流
- 合同负债

机会路径，按默认排序：

1. 电网投资与招标
2. 数字电网 / 调度 / 信息通信
3. 特高压 / 配网
4. 电力自动化 / 继电保护
5. 经营质量候选支撑

风险路径，按默认排序：

1. 应收账款与经营现金流
2. 招标与订单兑现
3. 毛利率压力
4. 合同负债与订单可见度
5. 主营构成口径
6. 估值数据日期

禁止误写：

- 不能把电网投资直接写成公司订单或收入兑现。
- 不能把国网 / 南网招标节奏直接写成公司确定性增长。
- 不能把合同负债直接写成 backlog。
- 不能把单期经营现金流改善写成长周期现金流稳定。
- 不能把主营构成衍生提示写成官方主营业务事实。

证据缺口重点：

- 招标、订单、收入、毛利率、现金流之间的公司级传导证据。
- 主营构成 period、classification type、revenue ratio 和 denominator 口径。
- `main_business` 官方来源。
- 估值 `as_of_date` 与报告日期一致性。

核心跟踪变量：

- 国网 / 南网招标节奏。
- 特高压 / 配网项目进度。
- 数字电网、调度系统、信息通信相关披露。
- 应收账款、经营现金流、合同负债、毛利率、ROE、capex。
- 估值数据日期和业务构成口径变化。

### 3.2 `semiconductor_equipment_cycle`

适用对象：

- `002371 北方华创`

定位：

- `semiconductor_cycle` 下的半导体设备 first-version presentation profile。
- 适合表达晶圆厂资本开支、国产替代、设备导入、研发投入、订单 / 存货 /
  合同负债验证和周期波动。

关键词：

- 半导体设备
- 晶圆厂资本开支
- 国产替代
- 设备订单
- 存货
- 研发投入
- 毛利率
- 客户验证
- 产线扩张
- 周期波动

机会路径，按默认排序：

1. 国内晶圆厂 capex
2. 国产替代和设备导入
3. 研发投入转化
4. 订单 / 存货 / 合同负债验证
5. 产品结构和毛利率改善

风险路径，按默认排序：

1. 半导体周期下行
2. 订单兑现不及预期
3. 存货和收入错配
4. 研发投入无法转化
5. 毛利率压力
6. 客户验证不足
7. capex 节奏放缓

禁止误写：

- 不能把国产替代叙事直接写成收入兑现。
- 不能把研发投入直接写成技术壁垒。
- 不能把库存变化直接写成需求强弱。
- 不能把 capex 直接写成订单。
- 不能把客户验证、导入或认证直接写成批量收入。
- 不能把合同负债直接写成 backlog。

证据缺口重点：

- 设备订单、交付、验收、收入确认和回款之间的公司级证据。
- 研发投入对应产品进展、客户导入和商业化收入证据。
- 存货构成、周转、跌价风险和收入错配证据。
- 晶圆厂 capex 到公司订单的传导证据。

核心跟踪变量：

- 国内晶圆厂资本开支节奏。
- 设备订单、合同负债、存货、收入确认和回款。
- 研发投入、研发费用率、产品导入和客户验证进度。
- 毛利率、产品结构、capex、经营现金流。
- 半导体周期、产线扩张和客户扩产节奏。

### 3.3 `advanced_manufacturing_thermal_management`

适用对象：

- `002050 三花智控`

定位：

- `advanced_manufacturing_growth` 下的热管理 / 制冷控制 / 新能源车零部件
  first-version presentation profile。
- 适合表达制冷控制基本盘、新能源车热管理、客户和产品结构升级、机器人 /
  新业务可选项和经营质量验证。

关键词：

- 热管理
- 制冷控制
- 汽车零部件
- 新能源车
- 机器人 / 新业务
- 客户结构
- 毛利率
- 存货
- 应收账款
- 资本开支
- 新业务收入占比

机会路径，按默认排序：

1. 新能源车热管理
2. 制冷控制基本盘
3. 客户和产品结构升级
4. 新业务可选项
5. 毛利率和经营质量候选支撑

风险路径，按默认排序：

1. 汽车需求波动
2. 客户集中度
3. 新业务兑现不足
4. 毛利率压力
5. 存货 / 应收 / capex 扩张风险
6. 新业务收入占比证据不足

禁止误写：

- 不能把机器人概念直接写成已兑现收入。
- 不能把新业务叙事直接写成利润增长。
- 不能把客户传闻写成 verified fact。
- 不能把行业空间直接写成公司确定性。
- 不能把 design-win、定点、认证或客户导入直接写成批量收入。
- 不能把制冷控制和汽车热管理数据代理为机器人业务兑现。

证据缺口重点：

- 新能源车热管理收入、订单、客户、毛利率和回款证据。
- 制冷控制基本盘的收入稳定性、毛利率和现金流证据。
- 机器人 / 新业务的收入占比、订单、客户、量产、交付和收款证据。
- 客户集中度、客户结构升级和产品结构改善证据。
- 存货、应收、capex 扩张是否与收入和现金流匹配。

核心跟踪变量：

- 新能源车销量和热管理单车价值量相关披露。
- 制冷控制业务收入、毛利率和现金流。
- 客户结构、产品结构、新业务收入占比。
- 存货、应收账款、capex、经营现金流、ROE。
- 机器人 / 新业务订单、客户、量产、交付和收入确认。

## 4. Profile selection 规则

profile selection 必须可审计，且不能只因为关键词命中就强行切 profile。关键词
只能作为人工检查或输出隔离的辅助信号，不是 routing 的主规则。

选择顺序：

1. 优先使用 `strategy_type_expected` / classifier result。
2. 其次使用 `code` 白名单。
3. 再看 evidence_pack / P1.1 strategy。
4. 若无法识别，使用 `generic_fundamental_report`。
5. 不能因为关键词命中就强行切 profile。
6. profile selection 必须可审计，并在 Markdown 或 metadata 中记录。

建议的审计记录字段：

- `presentation_profile_id`
- `presentation_profile_selected_by`
- `strategy_type_expected`
- `classifier_strategy_type`
- `code_whitelist_match`
- `evidence_pack_strategy_type`
- `p1_strategy_type`
- `fallback_reason`
- `profile_term_isolation_version`

首批明确映射：

| code | company | expected strategy | profile |
| --- | --- | --- | --- |
| `600406` | 国电南瑞 | `stable_growth` | `stable_growth_grid_equipment` |
| `002371` | 北方华创 | `semiconductor_cycle` | `semiconductor_equipment_cycle` |
| `002050` | 三花智控 | `advanced_manufacturing_growth` | `advanced_manufacturing_thermal_management` |

如果 classifier result 与 code 白名单冲突，renderer 不应静默套用 profile。V1
建议记录 `profile_selection_warning`，并在无法确认时退回
`generic_fundamental_report`。presentation profile 只影响展示语言，不应反向修改
classifier、P1.1、scoring 或 evidence label。

## 5. Generic fallback

`generic_fundamental_report` 是无法可靠识别 profile 时的保守 fallback。

fallback 规则：

- 不写行业专属强判断。
- 只保留财务质量、估值、主营构成、数据质量、风险、证据缺口。
- 不写特高压、国网 / 南网、半导体设备、晶圆厂 capex、国产替代、热管理、
  机器人 / 新业务等专属词。
- 不把主题词或新闻词写成行业框架。
- 不为了显得具体而套用错误行业语言。
- 避免错配比空泛更重要。

fallback 应该优先输出：

- 数据质量说明。
- 公司基本面和字段可信度。
- 估值数据日期和口径说明。
- 主营构成缺口。
- 通用财务风险。
- 证据缺口和后续需要验证的变量。

## 6. Cross-contamination 防护

防串味规则适用于最终 Markdown / HTML 报告正文和 presentation metadata，不针对
本设计文档本身。

硬性隔离规则：

- 002371 报告不得出现国网 / 南网 / 特高压，除非输入证据明确。
- 002050 报告不得自动出现国网 / 南网 / 半导体设备。
- 600406 报告不得出现晶圆厂 capex / 国产替代 / 机器人新业务。
- profile-specific terms 只能来自选中的 profile。
- 非选中 profile 的专属词即使被通用 renderer 模板包含，也必须被过滤。
- 若输入证据明确包含跨行业词，报告必须说明证据来源和证据标签，不能按默认
  profile 语言扩写。

建议的 future tests：

- 覆盖 `600406` / `002371` / `002050` fake reports。
- 覆盖每个 profile 的 allowed terms。
- 覆盖非选中 profile 的 forbidden terms。
- 覆盖 fallback 不输出行业专属词。
- 覆盖 profile selection audit metadata。
- 覆盖 evidence boundary：专属词出现不等于 verified fact。

本阶段不新增 tests。测试只作为后续 implementation acceptance 的要求。

## 7. 与 evidence boundary 的关系

profile 只决定表达框架，不改变 evidence label。

必须保持的边界：

- profile 不能把 `unsupported_assumption` 变成事实。
- profile 不能把 candidate 写成 `verified_fact`。
- profile 不能隐藏 data-quality caveats。
- profile 不能把行业叙事写成公司兑现。
- profile 不能把 P1.1 research questions 写成 operating facts。
- profile 不能把 capex 写成订单、产能释放、收入或增长兑现。
- profile 不能把合同负债写成 backlog。
- profile 不能把研发投入写成技术壁垒。
- profile 不能把存货变化写成需求强弱。
- profile 不能输出买卖建议、目标价、仓位、组合权重或技术面交易信号。

每一条关键判断仍应携带 Research Report V1 既有 evidence label，例如
`verified_fact`、`auto_accepted_candidate`、`manual_review_required`、
`unsupported_assumption`、`coverage_caveat` 或 `forward_tracking_variable`。

## 8. Implementation acceptance notes

已接受的实现方向以小而可审计的 registry 为主：

- `ResearchReportPresentationProfile` 或 dict-based profile registry。
- `_select_presentation_profile(report)`。
- renderer 根据 profile 输出行业逻辑、机会、风险、证据缺口和 follow-up
  variables。
- renderer 在 Markdown 或 metadata 中记录 profile selection。
- renderer 将通用骨架与 profile-owned 文案分离。
- tests 覆盖 600406 / 002371 / 002050 fake reports。
- tests 覆盖 no cross-contamination。
- tests 覆盖 fallback 不输出行业专属词。

建议 profile 字段：

- `profile_id`
- `display_name`
- `applicable_codes`
- `strategy_types`
- `keywords`
- `opportunity_paths`
- `risk_paths`
- `industry_transmission_paths`
- `follow_up_variables`
- `unsupported_claims`
- `evidence_gap_focus`
- `forbidden_terms_when_not_selected`

实现顺序已经验证为先 registry 和 selection，再改 renderer。不要直接把
600406 renderer 套到 002371 / 002050。

## 9. Roadmap

已完成路线：

1. 本设计文档。
2. profile registry implementation。
3. 生成 002371 Markdown。
4. 生成 002050 Markdown。
5. 做跨行业可读性验收。
6. 记录 cross-industry Markdown profile acceptance summary。

下一步建议进入 HTML presentation layer design / implementation。

HTML presentation layer 必须消费 Markdown / presentation-layer output 或
Research Report V1 structured payload；不得重新分析，不得改结论，不得隐藏
caveat，不得调用 provider，不得联网，不得读 token，不得接 MCP。promote rules /
validator / fixture promotion / Tushare primary 仍后置。

## 10. Cross-industry Markdown acceptance

验收结论记录在
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_MARKDOWN_PROFILE_ACCEPTANCE_SUMMARY.md`。

最终状态：

- `600406` Markdown accepted。
- `002371` Markdown accepted。
- `002050` Markdown accepted。
- presentation profile registry accepted。
- professional analyst voice gate accepted。
- cross-industry Markdown validation passed。

三个 accepted runtime artifacts：

| code | company | profile | product readability score | accepted runtime artifact |
| --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | `stable_growth_grid_equipment` | 8/10 | `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md` |
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | 7.5/10 | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md` |
| `002050` | 三花智控 | `advanced_manufacturing_thermal_management` | 8/10 | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` |

Cross-contamination result:

- `600406` 未混入半导体 / 机器人新业务语言。
- `002371` 未混入电网 / 热管理语言。
- `002050` 未混入电网 / 半导体设备语言。
- 当前 V1 hard-fail 防串味策略有效。
- 若未来要允许跨行业词，必须另行设计 evidence-label-aware allowlist。

Known limitations:

- `002371` 和 `002050` 内容厚度仍偏 V1 初稿。
- `002050` 中 `capex` 后续建议统一中文为“资本开支”。
- 证据等级文字后续可进一步柔化。
- 当前只验证 3 个样本。
- 尚未做 HTML presentation、live provider report、official parser / CNInfo、
  fixture promotion、validator 或 primary switch。
