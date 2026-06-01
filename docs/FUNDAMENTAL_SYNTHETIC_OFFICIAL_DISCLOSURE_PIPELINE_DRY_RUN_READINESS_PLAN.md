# Synthetic Official Disclosure Pipeline Dry-Run Readiness / Planning

## 1. 阶段名称和当前 baseline

阶段名：Synthetic Official Disclosure Pipeline Dry-Run Readiness / Planning。

最近关键 commits：

- `d815e0c docs: accept official disclosure discovery candidate contract`
- `54d9356 feat: add official disclosure discovery candidate contract`
- `de64ae2 docs: add official disclosure discovery candidate readiness gate`
- `52f2322 docs: add official disclosure pipeline next-slice reassessment plan`
- `3d81527 docs: add official disclosure registry locator acceptance summary`

当前 baseline 判断：

- `official_disclosure_discovery_candidate.v1` contract 已完成、commit、push。
- Official Disclosure Source Registry + Locator Gate 已完成、commit、push。
- Official Verification Data Gate 已完成、commit、push。
- 当前阶段只做 readiness / planning，不做 implementation。
- 当前阶段不新增 production code，不新增 tests，不写 fixtures、output baseline 或 accepted manifest。
- 当前阶段不连接 Report V1、provider adapter、live disclosure source、PDF parser、metric extraction 或 Research Pack / Evidence Panel。

## 2. 当前能力地图

当前已经具备的能力边界：

- `official_disclosure_discovery_candidate.v1`。
- discovery candidate pure normalizer。
- discovery candidate validator。
- `source_domain` derivation。
- deterministic `discovery_candidate_id`。
- `can_handoff_to_registry` boundary。
- `official_source_registry_entry.v1`。
- `official_disclosure_locator_result.v1`。
- official verification data gate。
- recursive safety scan。
- provider / mirror / unknown / local cache fail-closed。
- no-IO / no-network / no-parser boundary。

这些能力已经足以支撑下一步规划一个 synthetic-only、in-memory-only 的 dry-run thin slice：dry-run 只在显式传入 payload 上进行 schema-level 串联、handoff 判断、blocked reason 聚合和 safety scan，不读取本地文件，不访问 URL，不下载，不解析 PDF，不抽取指标，不写任何输出。

## 3. 当前缺口地图

下一步 thin slice 尚未具备：

- synthetic dry-run assembler。
- discovery candidate -> registry entry handoff adapter。
- registry entry -> locator candidate composition。
- locator result -> verification readiness skeleton。
- pipeline-level `blocked_reasons` aggregation。
- pipeline-level `data_gap_plan`。
- pipeline-level safety scan final pass。
- dry-run result schema。
- dry-run tests。
- real live discovery。
- PDF parser。
- metric extraction。
- provider reconciliation。
- Research Pack / Evidence Panel integration。

其中，real live discovery、PDF parser、metric extraction、provider reconciliation、Research Pack / Evidence Panel integration 不应进入下一步 dry-run thin slice；它们属于后续独立 gate。

## 4. 推荐 future dry-run schema

推荐新增未来 dry-run result schema：

`synthetic_official_disclosure_pipeline_dry_run_result.v1`

字段建议：

| 字段 | 要求 | 说明 |
| --- | --- | --- |
| `schema_version` | required | 固定为 `synthetic_official_disclosure_pipeline_dry_run_result.v1`。 |
| `stock_code` | required | 由调用方显式传入；缺失必须 fail-closed。 |
| `company_name` | required | 由调用方显式传入；缺失必须 fail-closed。 |
| `query_period` | required | 由调用方显式传入，例如年度、季度或明确日期区间；缺失必须 fail-closed。 |
| `requested_announcement_type` | required | 由调用方显式传入，例如 annual_report / quarterly_report / interim_report；缺失必须 fail-closed。 |
| `input_discovery_candidates` | required | 原始 synthetic discovery candidate payload 列表；只允许来自内存参数。 |
| `normalized_discovery_candidates` | required | validator / normalizer 接受并标准化后的候选。为空时必须有 blocked result。 |
| `rejected_discovery_candidates` | required | 被拒绝候选及原因；mirror / provider / unknown / local cache / forbidden marker 必须进入拒绝或 blocked。 |
| `registry_entry_candidates` | required | 从 validated discovery candidate 显式转换出的 registry entry candidate；不得 silent promotion。 |
| `locator_result` | conditional | 仅当存在完整 official registry entry 且无 conflict 时可生成；否则应为空或 blocked locator result。 |
| `readiness_skeleton` | required | verification readiness / gate input skeleton；不得包含 verified fact、official metric fact 或 provider conflict。 |
| `blocked_reasons` | required | pipeline-level blocked reasons；失败或 review_required 时不能为空。 |
| `data_gap_plan` | required | pipeline-level data gap plan；缺口存在时必须列明下一步需要的显式数据，而不是自动获取。 |
| `caveats` | optional | 记录 dry-run 限制、未覆盖范围和后续 gate 依赖。 |
| `not_for_trading_advice` | required | 必须为布尔值 `true`；缺失、false 或非 bool 必须 fail-closed。 |

附加 schema 约束：

- result 不得包含 `official_metric_fact`。
- result 不得包含 `provider_official_conflict`。
- result 不得包含 Report V1 / output / fixture / accepted manifest 写入意图。
- result 不得包含 URL fetch、download、PDF parse、table extraction、metric extraction 或 provider call intent。
- `readiness_skeleton` 只表达后续 verification gate 需要什么，不表达任何已验证事实。

## 5. Future dry-run flow

未来 dry-run 的纯内存流程建议：

1. validate / normalize synthetic discovery candidates。
   - 只处理显式传入 payload。
   - 不读取文件，不访问 URL，不下载，不联网。
   - 不解析 PDF，不抽取指标。

2. filter handoff-eligible discovery candidates。
   - 只保留 validator 明确认可且 `can_handoff_to_registry` 为真或等价通过边界检查的候选。
   - mirror / provider / unknown / local cache intent 必须 fail-closed。

3. build registry entry candidate objects from explicit normalized metadata only。
   - registry entry candidate 必须由 validated discovery candidate 显式转换。
   - 不允许从 URL、文件名、缓存路径或外部服务补全缺失 metadata。

4. feed registry entry candidates into locator helper。
   - locator 只能消费完整 official registry entry candidate。
   - 不允许 locator 直接消费 rejected discovery candidate。

5. produce locator result。
   - 单一完整 official candidate 可形成 synthetic locator result。
   - 多个 official candidates、source conflict 或 metadata mismatch 必须 blocked / review_required。

6. derive verification readiness skeleton / readiness summary。
   - 只生成 readiness skeleton，不生成 verified fact。
   - 不生成 official metric fact。
   - 不生成 provider official conflict。

7. aggregate `blocked_reasons` and `data_gap_plan`。
   - pipeline-level blocked reason 必须覆盖 discovery、registry、locator、readiness 四层。
   - `data_gap_plan` 只能列出需要调用方后续显式提供或后续 gate 处理的数据，不得触发自动获取。

8. run final recursive safety scan。
   - 对 input、normalized、rejected、registry candidates、locator result、readiness skeleton 和 final result 做 nested scan。
   - forbidden marker、provider/mirror/unknown/local cache intent、IO/network/output/report intent 必须被拦截。

流程边界要求：

- 不读取文件。
- 不访问 URL。
- 不下载。
- 不联网。
- 不解析 PDF。
- 不抽取指标。
- 不写 output。
- 不写 fixtures。
- 不写 accepted manifest。
- 不接 Report V1。
- 不接 provider adapter。

## 6. Handoff rules

handoff 规则必须 fail-closed：

- discovery candidate 不能 silent promotion。
- registry entry candidate 必须由 validated discovery candidate 显式转换。
- locator 只能选择完整 official registry entry。
- mirror / provider / unknown / local cache 不能进入 official lane。
- missing source metadata 必须 blocked。
- multiple official candidates 必须 `review_required`。
- source conflict 必须 blocked / `review_required`。
- dry-run 结果不能生成 verified fact。
- dry-run 结果不能生成 `official_metric_fact`。
- dry-run 结果不能生成 `provider_official_conflict`。

## 7. Fail-closed rules

以下情况必须 fail-closed，且 final result 必须包含明确 `blocked_reasons` 和 `data_gap_plan`：

- input candidates 为空。
- 全部 candidates rejected。
- 多个 official candidates。
- source conflict。
- missing company / stock / period / announcement type。
- `source_url` / `source_domain` mismatch。
- forbidden marker。
- provider / mirror / unknown。
- local cache intent。
- readiness skeleton 不足。
- blocked reason 缺失。
- `data_gap_plan` 缺失。
- `not_for_trading_advice` missing / false / non-bool。

fail-closed 输出原则：

- blocked result 可以存在，但不得生成 verified fact。
- review_required result 可以存在，但不得自动选择一个 official lane。
- rejected candidate 的原因必须可追溯到输入 payload 或现有 validator / safety boundary。
- 任何自动补全 source metadata、自动读取本地缓存、自动访问 URL 的意图都应被视为 blocker。

## 8. Future implementation expected files

若 readiness plan 通过，未来 implementation 只能考虑以下文件。

Production：

- `src/fundamental_skill/data_verification/schemas.py`
- `src/fundamental_skill/data_verification/validators.py`
- `src/fundamental_skill/data_verification/synthetic_official_disclosure_pipeline_dry_run.py`
- `src/fundamental_skill/data_verification/__init__.py`，仅 public API 需要时可改。

Tests：

- `tests/test_synthetic_official_disclosure_pipeline_dry_run.py`
- `tests/test_synthetic_official_disclosure_pipeline_dry_run_safety.py`

Optional / requires approval：

- 其他 production 文件：仅当现有 public API、schema export 或 safety scan ownership 无法通过上述文件完成时可考虑；必须先单独说明原因并获得 approval。
- 其他 tests 文件：仅当需要补充已有 regression ownership 且无法在新增 dry-run tests 中覆盖时可考虑；必须先单独说明原因并获得 approval。
- docs follow-up：仅当 implementation acceptance 需要新增 acceptance summary 时可考虑；必须作为独立 docs-only step approval。

## 9. Future implementation forbidden files

未来 implementation 明确禁止触碰：

- Report V1 generator。
- provider adapter。
- accepted manifest。
- output baseline。
- fixtures。
- examples。
- `.local_experiments`。
- `tushare_token.txt`。
- `.env`。
- unrelated mojibake files。
- source download / cache acquisition。
- PDF parser。
- PDF table extractor。
- metric extraction。
- Research Pack implementation。
- Evidence Panel implementation。
- live CNInfo / SSE / AkShare / Tushare / provider calls。

## 10. Future tests

未来 implementation 至少应覆盖：

- valid single CNInfo synthetic candidate dry-run。
- valid SSE / exchange synthetic candidate dry-run。
- mirror / provider / unknown rejected。
- local cache intent inert / rejected。
- all candidates rejected -> blocked result。
- no candidates -> blocked result。
- multiple official candidates -> review required。
- source conflict -> blocked / review required。
- missing metadata -> blocked。
- forbidden markers nested -> rejected。
- `not_for_trading_advice` required。
- dry-run result cannot include `official_metric_fact`。
- dry-run result cannot include `provider_official_conflict`。
- dry-run result cannot include Report V1 / output / fixture / manifest intent。
- no IO / no network / no file read。
- no URL fetch。
- no PDF parser。
- final safety scan covers nested result。

测试边界：

- tests 必须 synthetic-only、in-memory-only。
- tests 不得读取 disclosure source file、token、`.env`、`tushare_token.txt` 或 local cache。
- tests 不得下载或访问 URL。
- tests 不得写 output / fixtures / accepted manifest。

## 11. Regression subset

未来 implementation 后至少运行：

- `tests/test_synthetic_official_disclosure_pipeline_dry_run.py`
- `tests/test_synthetic_official_disclosure_pipeline_dry_run_safety.py`
- `tests/test_official_disclosure_discovery_candidate.py`
- `tests/test_official_disclosure_discovery_candidate_safety.py`
- `tests/test_official_disclosure_source_registry.py`
- `tests/test_official_disclosure_locator.py`
- `tests/test_official_disclosure_registry_locator_safety.py`
- `tests/test_official_verification_safety.py`

如果修改 `schemas.py` / `validators.py`，还应运行 official verification schema / validator subset。

## 12. Acceptance criteria

Readiness plan acceptance：

- 只新增 docs readiness / planning 文件。
- no production code。
- no tests。
- no output / fixtures / accepted manifest。
- no token / `.env` / `tushare_token.txt` read。
- no `.local_experiments` / mojibake handling。
- future dry-run result schema clear。
- flow clear。
- handoff rules clear。
- fail-closed rules clear。
- expected files / tests clear。
- forbidden scope clear。
- implementation entry can be approved or rejected。

Future implementation acceptance：

- only expected production / test files changed。
- synthetic-only。
- in-memory-only。
- no IO。
- no network。
- no download。
- no PDF parser。
- no metric extraction。
- no provider。
- no Report V1。
- no output / fixture / manifest write。
- safety tests pass。
- registry / locator / discovery regressions pass。
- no blocker remains open。

## 13. 是否需要三方审计

本 docs-only readiness / planning 阶段不需要 Gemini / DeepSeek / Kimi 三方审计。

future implementation 的审计建议按风险分级：

- 若 implementation 只新增 standalone dry-run assembler，且不修改 `schemas.py` / `validators.py` 的既有行为，可以先走本地 tests + readiness acceptance review，不默认要求三方审计。
- 若 implementation 修改 `schemas.py` / `validators.py`，或新增 pipeline assembly gate 并改变 discovery / registry / locator / verification handoff 边界，建议进行 Gemini / DeepSeek / Kimi 三方审计，重点审计 fail-closed、safety scan 覆盖、schema required 字段、forbidden intent 阻断和 no-IO/no-network 保证。
- 若 implementation 触及 provider adapter、Report V1、live source、PDF parser、metric extraction、fixtures/output/accepted manifest，则应拒绝本 thin slice scope；在重新拆分 gate 前不建议进入实现。

## Recommendation

建议下一步先进行 planning acceptance review。若本 readiness plan 被接受，可进入 future implementation thin slice；implementation 仍应保持 synthetic-only、in-memory-only、no IO、no network、no output write，并以新增 dry-run assembler + focused tests 为主。
