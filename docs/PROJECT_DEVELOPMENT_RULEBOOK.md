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
* 哪些判断边界需要说明；
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
* 通过专业语言表达的数据边界；
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

内部质量控制、模型 grounding、审计/debug/查看依据可以使用简单标签：

* `[较可靠]`
* `[待核验]`
* `[数据缺口]`
* `[推理]`
* `[不可判断]`

终端用户主视图不要默认展示这些标签，也不要默认展示 page / snippet / sha256 / source_url / cache_path / anchor map / provider queue。

### 4.4 专业分析师前台输出规则

前台默认输出必须像专业基本面分析师，而不是像后端系统状态汇报。

终端用户默认不应看到 `[待核验]`、`[数据缺口]`、`[推理]`、`provider candidate`、`pending verification`、`official verification`、`provider 与官方口径一致性` 等工程标签或验证状态。这些信息属于后台质量控制、模型 grounding、置信度、审计/debug/查看依据，不属于用户主视图。

用户主界面应展示专业分析观点，包括：

* 公司业务逻辑；
* 财务解读；
* 经营质量判断；
* 行业 / 宏观传导；
* 核心风险；
* 结论边界；
* 影响判断的关键变量。

前台输出必须给出模型自己的基本面判断，不能把判断责任抛给用户。禁止使用以下表达：

* 用户自行判断；
* 用户自行跟踪；
* 需要用户结合其他资料；
* 建议用户后续自行观察。

可以表达“影响判断的关键变量包括……”，但这应作为模型分析框架的一部分，而不是把判断责任转移给用户。

允许输出谨慎但明确的基本面主观判断，例如：

* 经营质量偏强 / 偏弱 / 中性观察；
* 财务表现改善 / 承压；
* 现金流匹配度改善 / 拖累；
* 行业传导顺畅 / 不明确；
* 主题逻辑强于基本面兑现。

仍然严格禁止输出：

* 买入 / 卖出 / 持有；
* 目标价；
* 仓位；
* 技术信号；
* 交易建议。

原则总结：

> 后台可以谨慎，前台必须专业。
> 后台可以处理验证状态，前台必须输出分析观点。
> 后台可以标记不确定性，前台不能把判断责任抛给用户。

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

默认用户报告不应展示 evidence locator 的页码、snippet、sha256 或验证状态。
如需表达数据来源或判断边界，应转化为专业分析语言，例如：

- 财务层面应重点观察收入、利润与现金流的匹配度，若利润增长无法转化为经营现金流，经营质量判断需要打折。
- 业务层面应关注主营构成、订单交付与回款节奏是否能共同支撑收入和利润表现。
- 行业与宏观变量不能直接等同于公司受益，必须落到订单、交付、回款和利润率等经营变量上。
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
* Public API / Skill Callable Wrapper Thin Slice；
* Controlled Real Tushare → Professional Analyst Compact Brief E2E Pilot；
* Professional Compact Brief Quality / Model Analysis Boundary Thin Slice；
* LLM Analyst Renderer Handoff Contract + Fake Renderer Integration Thin Slice；
* Ticker-only Professional Brief Wrapper Integration Thin Slice。

这些能力证明项目已经从后台证据链，推进到受控 ticker-only callable entry。

当前已经具备的前台 / wrapper 能力：

* 已有 `user_facing_analysis_brief.v1`；
* 已有 `analysis_brief_report_v1_compatibility_payload.v1`；
* 已有 `professional_analyst_context.v1`；
* 已有 `llm_analyst_handoff_context.v1`；
* 已有 fake LLM analyst renderer handoff；
* 已有最小 callable wrapper；
* wrapper 支持 `input_mode=analysis_brief`；
* wrapper 支持 `input_mode=orchestration_result`；
* wrapper 支持 `input_mode=ticker_only_professional_brief`；
* wrapper 支持 `output_mode=compact_brief`；
* wrapper 支持 `output_mode=compact_brief_and_report_v1_compatibility_payload`；
* wrapper 支持 `output_mode=professional_compact_brief`；
* wrapper 支持 `output_mode=professional_compact_brief_and_internal_payload`；
* ticker-only request 可以通过受控 wrapper 路径进入 professional compact brief 链路；
* ticker-only wrapper 默认不返回 provider_candidate_bundle、candidate_items 或 backend trace；
* env_live 仍只允许在 `input_mode=ticker_only_professional_brief`、`tushare_client_mode=env_live`、`allow_network=true` 的窄路径下使用。

注意：

* 当前 ticker-only wrapper 已经接通，但仍是受控 thin slice；
* 当前仍不是 full autonomous agent；
* 当前仍不是 true LLM analyst；
* 当前仍不是 Report V1 / HTML；
* 当前仍不是 official metric verification；
* 当前仍不是 provider-vs-official reconciliation；
* 当前仍不包含交易建议。

---

## 9. 当前仍未完成

当前状态应明确区分“ticker-only callable entry 已完成”和“最终完整自动分析产品尚未完成”。

已经完成：

* 用户前台 analysis brief bridge draft；
* 最小 callable wrapper；
* Controlled Real Tushare → Professional Analyst Compact Brief E2E Pilot；
* Professional Compact Brief Quality / Model Analysis Boundary；
* LLM Analyst Renderer Handoff Contract + Fake Renderer Integration；
* ticker-only professional brief wrapper integration。

仍未完成：

* ticker-only professional brief 的可重复质量评估基线；
* ticker-only fake LLM renderer mode wiring；
* controlled real LLM local/manual smoke；
* true LLM analyst integration；
* official_metric_fact；
* official metric verification；
* provider-vs-official reconciliation；
* formal Report V1 integration；
* HTML / formal report rendering with new evidence chain；
* one-command fully autonomous skill；
* production-grade multi-ticker batch / UI / dashboard。

当前最真实的产品缺口不是“没有入口”，而是：

> ticker-only wrapper 已能生成 professional brief，但还没有系统性证明这些 brief 在不同样本场景下足够专业、稳定、可回归。

---

## 10. Callable Wrapper 当前边界

当前 wrapper 是受控 callable entry，不是 full autonomous agent。

它支持的输入模式：

* `input_mode=analysis_brief`
* `input_mode=orchestration_result`
* `input_mode=ticker_only_professional_brief`

它支持的输出边界：

* `compact_response`
* 可选的 Report V1 compatibility payload；
* `professional_compact_brief`
* 可选的 sanitized `professional_internal_payload`

`ticker_only_professional_brief` 的边界：

* 可以接收 `stock_code` / `ts_code`；
* 必须显式声明 `tushare_client_mode`；
* tests 默认 fake / injected，不走真实网络；
* `env_live` 只允许在 `allow_network=true` 下使用；
* 不读取 `tushare_token.txt`；
* 不读取 `.env`；
* 不输出 token；
* 不写 output / fixtures / manifest；
* 不生成 Report V1；
* 不生成 HTML；
* 不生成 official_metric_fact；
* 不做 provider-vs-official reconciliation；
* 不输出买入 / 卖出 / 持有、目标价、仓位或技术信号；
* 不默认返回 provider_candidate_bundle、candidate_items、backend trace 或 evidence locator 细节。

当前 wrapper 仍不应被描述为 full autonomous agent。它只是让 ticker-only 请求进入受控 professional brief 链路。

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

当前已经完成：

* Controlled Real Tushare → Professional Analyst Compact Brief E2E Pilot；
* Professional Compact Brief Quality / Model Analysis Boundary；
* LLM Analyst Renderer Handoff Contract + Fake Renderer Integration；
* Ticker-only Professional Brief Wrapper Integration。

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
* trading advice；
* unbounded full autonomous agent；
* true LLM API integration without prior planning and smoke boundary。

下一阶段应优先做：

> Ticker-only Professional Brief E2E Quality Evaluation Harness Thin Slice

目标是建立可重复的前台质量评估基线，评估 wrapper ticker-only 路径生成的 `professional_compact_brief` 是否真的满足专业分析师前台输出要求。

该阶段应：

* 调用 wrapper 的 `input_mode=ticker_only_professional_brief`；
* 使用 fake / injected client，不联网；
* 生成 in-memory professional brief 样本；
* 对用户前台 `professional_compact_brief` 做 rubric-based quality evaluation；
* 覆盖 baseline、非 600406、现金流支撑利润、利润强于现金流、应收压力、资产负债压力、指标缺失等场景；
* 生成 in-memory evaluation result；
* 不写 output / fixtures / manifest；
* 不输出 raw provider bundle / candidate_items / backend trace；
* 不输出交易建议。

只有在质量评估基线建立后，才应继续评估：

1. ticker-only fake LLM renderer mode wiring；
2. controlled real LLM local/manual smoke planning；
3. professional brief human review；
4. Report V1 integration planning；
5. official metric extraction / reconciliation。

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
* 用户主视图默认不展示工程标签或置信度标签；置信度、证据状态和分析边界应通过专业分析语言体现。标签只用于内部、审计/debug 或查看依据模式。

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

* 分析层内部标签；
* 明确结论边界；
* 受控推理；
* 通过专业语言表达的数据边界；
* 影响判断的关键变量；
* 对财务候选趋势做谨慎解读；
* 对行业/宏观传导提出分析框架，但不能硬下结论。

---

## 14. 推荐的后续路线

新的推荐路线顺序为：

1. `Ticker-only Professional Brief E2E Quality Evaluation Harness Thin Slice`
2. `Ticker-only Fake LLM Renderer Mode Wiring Thin Slice`
3. `Controlled Real LLM Local/Manual Smoke Planning`
4. `Controlled Real LLM Local/Manual Smoke`
5. `Professional Brief Human Review / Sample Output Evaluation`
6. `Report V1 Integration Planning`
7. `Very Small Metric Evidence Extraction`
8. `Provider-vs-Official Reconciliation`
9. `Full Evidence-aware Research Pack / Report V1 Integration`
10. `HTML / Formal Report Rendering`

不应直接跳到 Report V1。
不应直接进入 Report V1 artifact generation。
不应直接进入 HTML rendering。
不应直接进入交易建议。
不应先继续做更多 locator / cache / manifest / validator。
不应把 evidence locator 接入用户主视图。
不应继续无目的扩后台基础设施。
不应在未建立 ticker-only quality evaluation baseline 前，急于扩大 renderer / LLM / report 能力。

下一主开发建议是：

> Ticker-only Professional Brief E2E Quality Evaluation Harness Thin Slice

一句话原则：

> 入口已经接通，下一步先建立“好简报”的可重复工程评估标准，再升级 renderer 或进入真实 LLM。

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
* 这一步是否显式区分 fake tests 和 real local smoke？
* 这一步是否遵守 `TUSHARE_TOKEN` 环境变量规则？
* 这一步是否避免把 provider candidate 当 official fact？
* 这一步是否避免把 wrapper 扩成 full autonomous agent？
* 这一步是否避免直接进入 Report V1？
* 这一步是否默认隐藏 provider_candidate / pending verification / evidence trace / backend trace？
* 这一步是否保持 professional front-end output，而不是工程状态汇报？
* 这一步是否避免“用户自行判断 / 自行跟踪 / 需要用户结合”等责任转移表达？
* 若是质量评估阶段：是否评估的是用户前台 `professional_compact_brief`，而不是后台数据结构？
* 若是质量评估阶段：是否形成可重复 harness，而不是一次性人工 summary？
* 若是 renderer 阶段：是否已有质量基线说明为什么要切换或升级 renderer？
* 若是 LLM 阶段：是否已有 model-facing context sanitizer、prompt/output contract、token/key 边界和 no-output-write 边界？

若任何一项不通过，必须 reassess，不得推进。

---

## 16. 给 Codex 的长期提醒

后续 Codex 任务必须牢记：

> 我们做的是 A 股基本面分析 skill，不是官方公告证据展示系统。

后台证据越强，前台应该越简洁。
用户默认看到的是分析，不是证据工程。
证据能力服务模型，不打扰用户。

最终产品应该像一个专业基本面分析师，而不是一个 PDF 检索控制台。
