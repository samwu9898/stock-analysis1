# A股 Fundamental Skill 项目遵循手册

## 1. 项目最终目标

本项目的最终目标不是做一个公告检索器、证据展示器、PDF 解析器或数据管线 demo。

本项目的最终目标是：

> 用户输入一个 A 股标的，系统自动组织数据、证据状态和分析上下文，由大模型完成自下而上的基本面分析，并输出用户真正看得懂、用得上的分析结果。

用户真正关心的是：

* 这家公司是做什么的；
* 业务逻辑是否清楚；
* 财务变化怎么看；
* 行业与宏观如何传导；
* 核心风险在哪里；
* 哪些判断较可靠；
* 哪些仍待核验；
* 后续应该重点跟踪什么。

用户默认不关心：

* PDF 第几页命中什么关键词；
* sha256 是什么；
* source_domain 是什么；
* anchor status 是什么；
* provider queue 里有哪些 item；
* cache_path 是什么；
* official metadata 怎么来的；
* evidence locator 命中了哪些 snippet。

---

## 2. 项目最高原则

### 证据在后台，分析在前台

后台负责：

* 数据获取；
* 官方来源定位；
* PDF artifact cache；
* evidence locator；
* source lineage；
* sha256；
* confidence / caveat；
* provider candidate / official anchor / artifact cached 状态；
* debug / audit / 查看依据模式。

前台负责：

* 公司业务逻辑；
* 财务解读；
* 行业与宏观传导；
* 风险判断；
* 跟踪指标；
* 结论边界；
* 数据缺口；
* 用户可读的分析简报。

后台证据能力不等于用户价值。
后台证据能力的作用是约束模型、提高可信度、减少胡编、支持审计，而不是默认展示给用户。

---

## 3. Claude 批评必须长期牢记

Claude 曾经批评项目风险：

> 一直做 gate / schema / validator / dry-run / safety test，却迟迟不展示真实用户价值。

这个批评必须作为长期红线。

后续每一个阶段开始前都要问：

> 这一步是否直接提高用户看到的基本面分析价值？

如果答案是否，那么除非它是立即阻塞用户分析输出的必要能力，否则不应优先做。

禁止项目重新滑向：

* 无限 schema；
* 无限 validator；
* 无限 safety test；
* 无限 cache policy；
* 无限 manifest；
* 无限 dry-run；
* 无限 backend plumbing；
* 无限 evidence trace 展示。

---

## 4. 前台 / 后台分层规则

### 4.1 Backend Evidence Layer

这层可以包含：

* Tushare provider candidate；
* provider metric verification queue；
* official metadata discovery；
* official disclosure anchor；
* official artifact cache；
* official artifact evidence locator；
* PDF page / snippet / keyword hit；
* source lineage；
* sha256；
* caveats；
* data gaps；
* confidence signals。

这层默认不直接展示给用户。

只在以下场景展示：

* debug mode；
* audit mode；
* 用户点击“查看依据”；
* 内部验收；
* 模型需要解释为什么不能下结论；
* 后续机构版 source trace。

### 4.2 Model Context Layer

这层负责把后台证据转成模型可用上下文：

* 哪些数据较可靠；
* 哪些数据仍待核验；
* 哪些只有 provider candidate；
* 哪些有 official anchor；
* 哪些有 artifact cached；
* 哪些有 locator support；
* 哪些是 data gap；
* 哪些是推理问题。

这层服务大模型分析，不是最终用户主视图。

### 4.3 User-facing Analysis Layer

这层才是用户默认看到的内容。

必须聚焦：

* subject summary；
* business logic；
* financial interpretation；
* industry / macro context；
* risk points；
* data gaps that matter；
* tracking indicators；
* cannot conclude yet；
* conclusion boundary。

用户可见内容应使用简单标签：

* `[较可靠]`
* `[待核验]`
* `[数据缺口]`
* `[推理]`
* `[不可判断]`

不要默认展示 page / snippet / sha256 / source_url / cache_path / anchor map / provider queue。

---

## 5. 代码与模型职责边界

代码负责：

* 取数；
* 标的身份规范化；
* 数据结构化；
* 证据状态标记；
* 官方来源定位；
* PDF artifact cache；
* locator metadata；
* data gap 标记；
* 模型输入上下文组织；
* fail-closed safety；
* no trading advice boundary。

大模型负责：

* 业务判断；
* 财务解读；
* 行业分析；
* 宏观传导；
* 风险分析；
* 结论边界表达；
* 用户可读分析简报。

代码不得硬编码：

* 公司很好；
* 行业景气；
* 宏观利好；
* 公司受益；
* 核心投资逻辑成立；
* 龙头；
* 买入 / 卖出 / 持有；
* 目标价；
* 仓位；
* 技术信号。

---

## 6. Evidence Locator 的正确定位

`official_artifact_evidence_locator` 不是用户主界面功能。

它的正确作用是：

* 给模型提供 grounded context；
* 防止模型胡编；
* 标记哪些分析点有官方文本支撑；
* 为后续 official evidence extraction 做基础；
* 为 audit / debug / 查看依据模式提供 trace；
* 支持 confidence / caveat 系统。

它不应该默认变成：

* 用户报告主 section；
* PDF 页码展示；
* snippet 展示；
* 证据检索页面；
* source trace 页面。

默认用户报告不应写：

* “第 7 页命中管理层讨论与分析”；
* “第 12 页命中财务报表”；
* “sha256=xxxx”；
* “source_domain=static.cninfo.com.cn”。

默认用户报告应该写：

* `[待核验] 已有官方公告和 PDF artifact 支撑，但尚未完成官方指标核验。`
* `[数据缺口] 当前还缺少正式业务分部抽取，不能判断主营结构变化。`
* `[推理] 行业/宏观传导需要结合订单、招标、投资节奏进一步确认。`

---

## 7. 后续阶段选择规则

每次选择下一阶段，必须先进行 reassessment，而不是机械沿着工程链路往下做。

优先级判断：

1. 是否能提高用户分析价值？
2. 是否能让最终 skill 更接近“一句话分析标的”？
3. 是否避免把后台机制暴露为前台内容？
4. 是否避免过早进入 Report V1？
5. 是否避免再次陷入基础设施扩张？

---

## 8. 当前项目已完成能力

当前项目已经完成：

* Tushare provider candidate 财务数据；
* provider metric verification queue；
* real CNInfo official metadata discovery；
* provider metric → official disclosure anchor map；
* official PDF artifact download/cache；
* official artifact evidence locator；
* ticker research context skeleton；
* evidence-aware research pack scaffold；
* live evidence-aware vertical slice；
* live evidence research pack orchestration entry；
* ticker-generalization smoke；
* non-600406 shaped samples 验证；
* User-facing Analysis Brief Draft Thin Slice；
* Research Report V1 / HTML Reuse Audit + Bridge Integration Reassessment；
* Analysis Brief → Report V1 Compatibility Adapter Planning；
* Analysis Brief → Report V1 Compatibility Adapter Minimal Implementation；
* Public API / Skill Callable Wrapper Thin Slice。

这些能力证明项目已不是纯空转。

当前已经具备的前台 / wrapper 能力：

* 已有 `user_facing_analysis_brief.v1`；
* 已有 `analysis_brief_report_v1_compatibility_payload.v1`；
* 已有最小 callable wrapper；
* wrapper 支持 `input_mode=analysis_brief`；
* wrapper 支持 `input_mode=orchestration_result`；
* wrapper 支持 `output_mode=compact_brief`；
* wrapper 支持 `output_mode=compact_brief_and_report_v1_compatibility_payload`；
* ticker-only request 目前会 blocked，reason 是 `validated_analysis_input_required`。

---

## 9. 当前仍未完成

当前状态应明确区分“前台 analysis brief bridge draft 已完成”和“真实 ticker 自动分析尚未完成”。

已经完成：

* 用户前台 analysis brief bridge draft；
* 最小 callable wrapper。

仍未完成：

* ticker-only live orchestration；
* Controlled Real Tushare → Compact Brief E2E Pilot；
* official_metric_fact；
* official metric verification；
* provider-vs-official reconciliation；
* formal Report V1 integration；
* HTML / formal report rendering with new evidence chain；
* one-command fully autonomous skill。

---

## 10. Callable Wrapper 当前边界

当前 wrapper 是最小 callable entry，不是 full autonomous agent。

它只接受 explicit validated inputs：

* `input_mode=analysis_brief`
* `input_mode=orchestration_result`

它支持的输出边界是：

* `compact_response`
* 可选的 Report V1 compatibility payload

它当前不会：

* live 拉数据；
* 读取 token；
* 写 output；
* 生成 Report V1；
* 生成 HTML；
* 把 ticker-only request 自动升级成真实数据编排。

ticker-only request 当前必须 blocked，并明确 reason：

* `validated_analysis_input_required`

真实 ticker 自动分析属于后续 Controlled Real Tushare → Compact Brief E2E Pilot，不应在 wrapper 阶段暗中扩展。

---

## 11. Controlled Real Tushare Pilot Token / Network Rules

测试默认必须使用 fake client，不走真实网络。

真实 Tushare 只允许 manual/local smoke，并且必须满足：

* 显式 `allow_network=true` 或等价显式开关；
* 只允许从本机环境变量 `TUSHARE_TOKEN` 读取 token；
* 不允许读取 `tushare_token.txt`；
* 不允许读取 `.env`；
* 不允许在代码、测试、日志、docs、output、commit 中写入或输出 token；
* 不允许把 token 放进 fixtures / manifest / output。

真实 Tushare 返回的数据必须保持候选状态：

* 标记为 `provider_candidate`；
* 标记为 `pending_official_verification`；
* 不得把 Tushare provider candidate 当 official fact；
* 不得生成 official_metric_fact；
* 不得做 provider-vs-official reconciliation；
* 不得生成买入 / 卖出 / 持有、目标价、仓位或技术信号。

---

## 12. 下一阶段重新裁定

下一阶段不应做：

* locator result user-facing display；
* more cache / manifest / validator；
* more evidence trace UI；
* full PDF parser；
* table extraction；
* official_metric_fact；
* provider-vs-official reconciliation；
* Report V1；
* HTML rendering；
* trading advice。

下一阶段应做：

> Controlled Real Tushare → Compact Brief E2E Pilot

也可命名为：

> Controlled Real Tushare → Compact Brief Pilot

目标是让 ticker-only request 从 blocked 进入可控真实数据 pilot，同时继续保持 provider candidate / pending official verification 边界。

---

## 13. Analysis Brief / Report V1 Bridge 使用边界

User-facing Analysis Brief Draft Thin Slice 已完成。它的定位仍然是把后台状态转成用户真正关心的分析层结构，而不是展示证据工程。

输入：

* `live_evidence_research_pack_orchestration_result.v1`
* optional `official_artifact_evidence_locator.v1`

输出：

* `user_facing_analysis_brief.v1`
  或
* `analysis_layer_research_brief.v1`

建议 section：

1. `subject_summary`
2. `current_judgment_boundary`
3. `business_logic`
4. `financial_interpretation`
5. `industry_macro_context`
6. `risk_points`
7. `data_gaps_that_matter`
8. `tracking_indicators`
9. `cannot_conclude_yet`
10. `backend_grounding_summary`

注意：

* `backend_grounding_summary` 默认不是用户主 section；
* 可以作为模型用字段；
* 可以作为 audit/debug/查看依据字段；
* 用户主视图只展示必要的可信度标签。

Analysis Brief / Report V1 bridge 仍禁止：

* 买入 / 卖出 / 持有；
* 目标价；
* 仓位；
* 技术信号；
* official_metric_fact；
* provider_official_conflict；
* provider-vs-official reconciliation；
* 把 provider candidate 当官方事实；
* 把 artifact cached 当 official verified；
* 把 locator hit 当 official verified；
* 把 page/snippet/source_url/sha256 作为用户主内容；
* 硬编码公司受益、行业景气、宏观利好等结论。

允许：

* 分析层标签；
* 明确结论边界；
* 受控推理；
* 数据缺口；
* 后续跟踪清单；
* 对财务候选趋势做谨慎解读；
* 对行业/宏观传导提出分析框架，但不能硬下结论。

---

## 14. 推荐的后续路线

新的路线顺序为：

1. `Controlled Real Tushare → Compact Brief E2E Pilot`
2. `Report V1 Integration Planning`
3. `Very Small Metric Evidence Extraction`
4. `Provider-vs-Official Reconciliation`
5. `Full Evidence-aware Research Pack / Report V1 Integration`
6. `HTML / Formal Report Rendering`

不应直接跳到 Report V1。
不应直接进入 Report V1 artifact generation。
不应直接进入 HTML rendering。
不应直接进入交易建议。
不应先继续做更多 locator / cache / manifest / validator。
不应把 evidence locator 接入用户主视图。
不应继续无目的扩后台基础设施。

rulebook commit 后，下一主开发建议是 Controlled Real Tushare → Compact Brief E2E Pilot。

---

## 15. 主策划决策检查清单

每次给 Codex 发下一阶段任务前，必须检查：

* 这一步是不是更接近用户的一句话基本面分析？
* 这一步是不是提高前台分析价值？
* 这一步是不是只是后台工程痕迹？
* 这一步会不会让用户看到不必要的证据细节？
* 这一步会不会让项目重新陷入 schema / validator / safety / dry-run 循环？
* 这一步是否仍然遵守 no trading advice？
* 这一步是否避免硬编码 600406？
* 这一步是否避免把 provider candidate / anchor / artifact / locator 升级为 official_verified？
* 这一步是否会让 ticker-only request 从 blocked 变成可控真实数据 pilot？
* 这一步是否显式区分 fake tests 和 real local smoke？
* 这一步是否遵守 `TUSHARE_TOKEN` 环境变量规则？
* 这一步是否避免把 provider candidate 当 official fact？
* 这一步是否避免把 wrapper 扩成 full autonomous agent？
* 这一步是否避免直接进入 Report V1？

若任何一项不通过，必须 reassess，不得推进。

---

## 16. 给 Codex 的长期提醒

后续 Codex 任务必须牢记：

> 我们做的是 A 股基本面分析 skill，不是官方公告证据展示系统。

后台证据越强，前台应该越简洁。
用户默认看到的是分析，不是证据工程。
证据能力服务模型，不打扰用户。

最终产品应该像一个专业基本面分析师，而不是一个 PDF 检索控制台。
