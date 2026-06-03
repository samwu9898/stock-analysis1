# Fake LLM Frontstage Quality Comparison Thin Slice Acceptance Summary

## 1. 阶段名称

Fake LLM Frontstage Quality Comparison Thin Slice

## 2. Baseline commits

- implementation commit: `c42c03c225aeb51d0f753db6e4c560a339ebbc70`
- previous completed stage: Ticker-only Fake LLM Renderer Mode Wiring acceptance summary commit `86bc104`
- ticker-only professional brief quality evaluation acceptance summary commit `9105bf0`
- ticker-only wrapper acceptance summary commit `a13c78d`
- rulebook replacement commit `381b2ed`

## 3. 本阶段定位

本阶段是 deterministic vs fake_llm 的前台 `professional_compact_brief`
质量对比，目标是判断 fake_llm 前台输出是否与 deterministic 有差异，
并确认没有发现质量或安全退化。

本阶段明确不是以下事项：

- 不是新一轮质量评估系统扩张。
- 不是 true LLM integration。
- 不调用真实 LLM API。
- 不读取 LLM key。
- 不是 controlled real LLM smoke。
- 不是 Report V1 integration。
- 不是 HTML renderer。
- 不是 official metric verification。
- 不是 provider-vs-official reconciliation。
- 不生成任何 runtime artifact。

## 4. 修改文件清单

本阶段 implementation 只修改了以下 3 个 expected files：

- `src/fundamental_skill/research_planning/ticker_only_professional_brief_quality_evaluation.py`
- `tests/test_ticker_only_professional_brief_quality_evaluation.py`
- `tests/test_ticker_only_professional_brief_quality_evaluation_safety.py`

## 5. 功能摘要

- quality evaluation request 新增 `renderer_mode`。
- `renderer_mode` 允许值为 `deterministic` / `fake_llm`。
- 默认 `renderer_mode=deterministic`，deterministic baseline 保持。
- 显式 `renderer_mode=fake_llm` 会传入 wrapper `ticker_only_professional_brief` path。
- sample request / sample result / evaluation result 记录 `renderer_mode`。
- 新增 `build_fake_llm_frontstage_quality_comparison`。
- comparison 用同一批 `sample_ids` 分别运行 deterministic 和 fake_llm。
- comparison 只比较 `professional_compact_brief` 前台 preview。
- comparison 不看 backend trace。
- comparison 不输出 raw provider bundle / candidate_items。
- 没有 Report V1 / HTML / output artifact。

## 6. Comparison 摘要

- deterministic: `warning=4`, `fail=0`
- fake_llm: `warning=4`, `fail=0`
- `changed_count=42`
- `regression=false`
- `conclusion=fake_llm differs and no regression detected`

本阶段不试图证明 fake_llm 全面优于 deterministic。它只证明 fake_llm
与 deterministic 的前台输出有差异，并且未发现质量或安全退化。warning
分布不变，说明 fake_llm 没有静默降低质量基线。

## 7. Safety / boundary 摘要

comparison summary 与 fake_llm evaluation 结果确认不包含以下内容：

- token。
- `.env` / `tushare_token`。
- backend trace。
- raw provider bundle。
- raw provider rows。
- candidate_items。
- `source_url` / `page_number` / `snippet` / `sha256` / `cache_path`。
- `provider_candidate` / `pending_official_verification`。
- 待核验 / 数据缺口 / 推理。
- 用户自行判断 / 自行跟踪 / 需要用户 / 建议用户。
- buy / sell / hold。
- 目标价 / 仓位 / 技术信号。
- Report V1 / HTML artifact。

## 8. Tests 结果

- targeted tests: `119 passed`
- related tests: `432 passed`
- system python 不可用时使用 Codex bundled Python。
- live smoke 未执行，原因：本阶段只比较 in-memory deterministic/fake_llm
  frontstage quality，不接真实 LLM、不改变 live provider connector、不读取 token。

## 9. 明确未触碰的禁区

本阶段确认未触碰以下禁区：

- true LLM API。
- OpenAI / Claude / Gemini / DeepSeek / Kimi API。
- LLM key / API key。
- Tushare live。
- CNInfo live。
- wrapper / controlled pilot / renderer 主逻辑。
- Report V1 builder。
- HTML renderer。
- PDF download / read / parse。
- table extraction。
- metric extraction as official fact。
- official_metric_fact。
- provider_official_conflict。
- provider-vs-official reconciliation。
- output / fixtures / accepted manifest。
- `.local_experiments`。
- `tushare_token.txt`。
- `.env`。
- unrelated mojibake files。
- unrelated examples file。
- cache PDF。
- token output。
- trading advice output。

## 10. 当前剩余 untracked 项

当前剩余 untracked 项为既存项目，不属于本阶段处理范围：

- `.local_experiments/`
- unrelated mojibake files
- unrelated examples file

## 11. 当前阶段结论

- implementation accepted。
- no blocker。
- summary doc is docs-only。
- 本阶段完成 fake LLM frontstage quality comparison。
- 本阶段没有扩展成新质量评估大系统。
- 本阶段确认 fake_llm frontstage output differs from deterministic。
- 本阶段确认 no regression detected。
- 这仍不是 true LLM analyst。
- 这仍不是 controlled real LLM smoke。
- 这仍不是 Report V1 / HTML。
- 这仍不是 official metric verification。
- 这仍不是 provider-vs-official reconciliation。
- 这不包含交易建议。
- 下一阶段应先 reassess。

后续可评估：

- Controlled Real LLM Local Manual Smoke Minimal Harness Thin Slice。
- professional brief human review。
- Report V1 integration planning。
- official metric extraction / reconciliation。

后续不应直接进入交易建议或无边界 full autonomous agent。
