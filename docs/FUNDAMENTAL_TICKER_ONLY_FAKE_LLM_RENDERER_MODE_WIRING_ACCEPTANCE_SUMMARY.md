# Ticker-only Fake LLM Renderer Mode Wiring Thin Slice Acceptance Summary

## 1. 阶段名称

Ticker-only Fake LLM Renderer Mode Wiring Thin Slice

## 2. Baseline commits

- implementation commit: `ceffc932fd23b91d4cad5dfcc42914d6e54eea31`
- previous completed stage: Ticker-only Professional Brief E2E Quality Evaluation Harness acceptance summary commit `9105bf0`
- ticker-only wrapper acceptance summary commit `a13c78d`
- LLM Analyst Renderer Handoff acceptance summary commit `0e3d556`
- rulebook replacement commit `381b2ed`

## 3. 本阶段定位

本阶段是 ticker-only wrapper 到 fake LLM handoff 的 `renderer_mode` wiring。它让 ticker-only request 可以显式选择 `fake_llm` renderer route，同时保留 `deterministic` fallback。

本阶段不是 true LLM integration，不调用真实 LLM API，不读取 LLM key，不是 controlled real LLM smoke，不是 Report V1 integration，不是 HTML renderer，不是 official metric verification，不是 provider-vs-official reconciliation，也不生成任何 runtime artifact。

## 4. 修改文件清单

- `src/fundamental_skill/research_planning/a_share_fundamental_skill_wrapper.py`
- `src/fundamental_skill/research_planning/controlled_real_tushare_professional_compact_brief_pilot.py`
- `tests/test_a_share_fundamental_skill_wrapper.py`
- `tests/test_a_share_fundamental_skill_wrapper_safety.py`
- `tests/test_controlled_real_tushare_professional_compact_brief_pilot.py`
- `tests/test_controlled_real_tushare_professional_compact_brief_pilot_safety.py`

## 5. 功能摘要

- 新增 `renderer_mode` 白名单，允许值仅为 `deterministic` / `fake_llm`。
- wrapper ticker-only request 支持 `renderer_mode`。
- controlled pilot request 支持 `renderer_mode`。
- wrapper 和 controlled pilot 默认仍保持 `deterministic`。
- 显式 `renderer_mode=fake_llm` 可通过 wrapper 传到 controlled pilot。
- controlled pilot fake_llm route 调用 existing quality module 的 `analyst_renderer="fake_llm"`。
- fake_llm route 使用既有 LLM handoff，不重新实现 renderer。
- deterministic fallback 保持。
- quality evaluation baseline 未被静默改变。
- old `analysis_brief` / `orchestration_result` paths 不允许 `renderer_mode`。
- unsupported `renderer_mode` fail closed。
- no Report V1 / HTML / output artifact。

## 6. Ticker-only fake_llm 调用链摘要

`stock_code` / `ts_code`
-> wrapper `input_mode=ticker_only_professional_brief`
-> `renderer_mode=fake_llm`
-> `controlled_real_tushare_professional_compact_brief_pilot`
-> `professional_compact_brief_quality` `analyst_renderer="fake_llm"`
-> `llm_analyst_renderer_handoff`
-> `professional_compact_brief`
-> wrapper response

`request_summary` / `readiness` 可记录 `renderer_mode`；internal payload 可记录 `renderer_mode`。wrapper 默认不返回 `provider_candidate_bundle`、不默认返回 `candidate_items`、不默认返回 backend trace，也不在 user-facing professional brief 展示工程标签。

## 7. Renderer mode 边界

- 允许值只有 `deterministic` / `fake_llm`。
- 默认 `deterministic`，避免静默改变既有质量基线。
- `fake_llm` 必须显式请求。
- old paths 不允许 `renderer_mode`。
- `renderer_mode` 不能是 arbitrary string。
- `renderer_mode` 不能是 callable-like marker。
- `renderer_mode` 不能是 path-like/raw-like string。
- `renderer_mode` 不能是 token-like string。
- `renderer_mode` 不允许 `real_llm` / `custom` / URL / path。

## 8. User-facing professional output 摘要

无论 `deterministic` 还是 `fake_llm`，`professional_compact_brief` 都不展示 `provider_candidate`，不展示 `pending_official_verification`，不展示 official verification，不展示待核验 / 数据缺口 / 推理，不展示 `page` / `snippet` / `source_url` / `sha256` / `cache_path`。

前台输出不写“用户自行判断 / 自行跟踪 / 需要用户 / 建议用户”。它应输出专业分析观点，不输出买入 / 卖出 / 持有，不输出目标价 / 仓位 / 技术信号。`source_note=数据来源：Tushare。`

## 9. Tests 结果

- targeted tests：拆分执行全部通过。
- wrapper 两文件：147 passed。
- pilot：28 passed。
- pilot safety：113 passed。
- targeted 合计：288 passed。
- related tests：228 passed。
- 完整四文件同进程 targeted 命令触发一次 Windows/Python access violation。
- 拆分执行已全部通过。
- 该 access violation 作为环境/runner 备注记录，不作为 implementation blocker。
- system python 不可用时使用 Codex bundled Python。
- live smoke 未执行，原因：本阶段只做 fake_llm renderer mode wiring，不接真实 LLM、不改变 live provider connector。

## 10. Safety / boundary 摘要

- 未调用真实 LLM API。
- 未调用 OpenAI / Claude / Gemini / DeepSeek / Kimi API。
- 未读取任何 LLM API key。
- 未读取 `tushare_token.txt` / `.env`。
- 未输出 token。
- 未调用 live provider。
- 未写 `output` / `fixtures` / manifest。
- 未生成 Report V1 artifact。
- 未生成 HTML artifact。
- 未生成运行时 Markdown / JSON report artifact。
- 未生成 `official_metric_fact`。
- 未生成 `provider_official_conflict`。
- 未做 provider-vs-official reconciliation。
- fake_llm route 无 backend trace。
- fake_llm route 无工程标签。
- fake_llm route 无用户责任转移表达。
- fake_llm route 无交易建议。
- 英文交易短语和中文交易词继续阻断。
- engineering labels 继续阻断。

## 11. 明确未触碰的禁区

- true LLM API
- OpenAI / Claude / Gemini / DeepSeek / Kimi API
- LLM key / API key
- Tushare live
- CNInfo live
- Report V1 builder
- HTML renderer
- PDF download/read/parse
- table extraction
- metric extraction as official fact
- `official_metric_fact`
- `provider_official_conflict`
- provider-vs-official reconciliation
- `output` / `fixtures` / accepted manifest
- `.local_experiments`
- `tushare_token.txt`
- `.env`
- unrelated mojibake files
- unrelated examples file
- cache PDF
- token output
- trading advice output

## 12. 当前剩余 untracked 项

- `.local_experiments/`
- unrelated mojibake files
- unrelated examples file

## 13. 当前阶段结论

- implementation accepted。
- no blocker。
- summary doc is docs-only。
- 本阶段完成 ticker-only fake LLM renderer mode wiring。
- 本阶段让 wrapper ticker-only request 可显式选择 fake_llm route。
- 本阶段保持 deterministic fallback。
- 本阶段没有静默改变 quality evaluation baseline。
- 这仍不是 true LLM analyst。
- 这仍不是 controlled real LLM smoke。
- 这仍不是 Report V1 / HTML。
- 这仍不是 official metric verification。
- 这仍不是 provider-vs-official reconciliation。
- 这不包含交易建议。
- 下一阶段应先 reassess。

后续可评估：

- controlled real LLM local/manual smoke planning
- professional brief human review
- Report V1 integration planning
- official metric extraction / reconciliation

不要直接进入交易建议或无边界 full autonomous agent。
