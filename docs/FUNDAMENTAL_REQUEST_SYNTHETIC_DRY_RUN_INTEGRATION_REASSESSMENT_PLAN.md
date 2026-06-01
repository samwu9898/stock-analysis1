# Request + Synthetic Dry-Run Integration Planning

本文件仅用于规划 `official_disclosure_discovery_request.v1` 如何以纯内存、synthetic-only、explicit-payload-only 的方式接入现有 synthetic official disclosure dry-run。本文档不实现 production code，不新增 tests，不修改 output / fixtures / accepted manifest，不接 provider，不接 Report V1，不读取 token / `.env` / `tushare_token.txt`，不联网，不下载，不解析 PDF。

## 1. 阶段名称和当前 baseline

阶段名称：Request + Synthetic Dry-Run Integration Planning

当前最近命令检查：

```text
git status --short
?? .local_experiments/
?? "HTML\342\225\251\342\225\223\342\225\250\342\224\244\342\226\223\342\225\254\342\224\220\342\225\235.md"
?? "HTML\342\226\222\302\277\342\225\225\302\265\342\225\224\316\246\342\225\235\342\225\236\342\225\243\302\265\342\225\226\342\225\242v1.0.md"
?? "examples/\342\225\225\303\267\342\225\243\342\225\224\342\225\244\342\225\250\342\225\233\342\224\220-\342\225\223\342\225\250\342\225\243\302\267\342\224\202\303\261\342\224\202\342\225\237.html"
?? tushare_token.txt
?? "\342\225\226\342\225\223\342\225\254\303\267\342\224\220\342\211\245\342\225\235\342\226\204.md"
```

```text
git log --oneline -8
0a64ea2 docs: accept official disclosure request contract
cc86447 feat: add official disclosure request contract
e56cf4e docs: add official disclosure request readiness gate
da5a57e docs: accept security identity contract
65df22c feat: add security identity contract
65704de docs: add security identity readiness gate
550616c docs: add ticker company identity request reassessment plan
8576a22 docs: accept synthetic official disclosure dry-run gate
```

本阶段关注的最近关键 commits：

- `0a64ea2 docs: accept official disclosure request contract`
- `cc86447 feat: add official disclosure request contract`
- `e56cf4e docs: add official disclosure request readiness gate`
- `da5a57e docs: accept security identity contract`
- `65df22c feat: add security identity contract`
- `8576a22 docs: accept synthetic official disclosure dry-run gate`
- `5dcc082 feat: add synthetic official disclosure dry-run gate`

本阶段只做 planning，不做 implementation。当前下一步不是 live discovery，不是 PDF parser，不是 provider，不是 Report V1，而是重新评估 request contract 如何以安全边界接入 synthetic dry-run。

## 2. 当前能力地图

当前已经具备的能力和边界：

- `security_identity.v1`：可以表达证券身份输入、身份置信度和相关 caveats，但不应被 synthetic candidate 反向提升。
- `official_disclosure_discovery_request.v1`：可以表达“要找什么官方披露”，包括 `stock_code`、`exchange`、`query_period`、`period_end_date`、`requested_announcement_type`、`allowed_source_types`、`discovery_scope`、`blocked_reasons`、`caveats` 和 `not_for_trading_advice` 等约束，但它本身不执行查找。
- `official_disclosure_discovery_candidate.v1`：可以承载 discovery candidate 的结构化候选结果，供后续 normalizer / locator / dry-run 使用。
- `official_source_registry_entry.v1`：可以表达官方来源 registry entry 候选，但本阶段不得写 registry、不得落盘、不得接 live source。
- `official_disclosure_locator_result.v1`：可以表达 locator 层结果，但本阶段只规划未来 handoff，不做 URL 访问、下载、缓存或解析。
- `synthetic_official_disclosure_pipeline_dry_run_result.v1`：可以表达 synthetic dry-run 的 readiness、blocked reasons、data gap plan、safety caveats 和 fail-closed 状态。
- official verification data gate：可以作为 future dry-run 的最终数据门，但不得在本阶段或 future synthetic-only implementation 中生成真实官方指标事实。
- recursive safety scan：已有安全扫描概念，需要在 future request-driven flow 最后一层继续执行，并递归检查嵌套 payload 中的 forbidden markers。
- no-IO / no-network / no-parser boundary：现有方向应保持不读文件、不写 output、不联网、不下载、不解析 PDF、不抽取指标。
- provider / mirror / unknown / local cache fail-closed：候选来源如果显示 provider、mirror、unknown 或 local cache，应在 request-driven integration 层 fail closed。
- request contract 已能表达“要找什么官方披露”，但不执行查找；它只能驱动显式传入的 synthetic candidates 进行兼容性过滤和 dry-run 评估。

## 3. 当前缺口地图

尚未具备、需要 future implementation 解决的缺口：

- request -> synthetic discovery candidate handoff：尚未定义 request 如何接收显式 synthetic candidates 并进入候选 normalizer。
- request constraints 对 synthetic candidates 的过滤 / 验证：尚未定义字段级兼容规则和拒绝原因。
- request caveats 向 dry-run result 的传递：尚未定义 caveats 的保留、合并和不可覆盖规则。
- request-level `blocked_reasons` 与 dry-run `blocked_reasons` 的聚合：尚未定义 request blocked 时是否完全阻断 pipeline，以及最终 merged blocked reasons 的形状。
- request-driven dry-run result schema：尚未决定新增 request envelope schema，还是复用现有 synthetic dry-run result 并外包一层。
- request-driven integration tests：尚未建立覆盖 request + candidate compatibility、fail-closed 和安全标记的测试集。
- live discovery adapter：不属于当前阶段，未来也应在 synthetic-only request integration 稳定后另行审批。
- source download / cache acquisition：不属于当前阶段，也不属于 synthetic-only implementation。
- PDF parser / table extractor：不属于当前阶段。
- metric extraction：不属于当前阶段。
- provider reconciliation：不属于当前阶段。
- Research Pack / Evidence Panel integration：不属于当前阶段。

## 4. 本阶段要回答的核心问题

本阶段规划需要回答：

- valid request 如何驱动 synthetic candidates：只接受函数参数或测试 payload 中显式传入的 synthetic candidates，不从文件、URL、cache、provider 或网络发现候选。
- synthetic candidate 必须如何匹配 request：必须匹配 `stock_code`、`exchange`、`query_period` / `period_end_date`、`requested_announcement_type`、`allowed_source_types` 和 `discovery_scope` 的禁止动作边界。
- request 的 caveats 如何进入 final dry-run result：request caveats 必须原样保留，并与 candidate caveats、dry-run caveats 合并为 `final_caveats`；candidate 不得覆盖或删除 request caveats。
- request 的 `blocked_reasons` 如何阻止 pipeline 继续：只要 request 自身 blocked，后续 normalizer / dry-run 不得继续处理 candidates，最终返回 blocked readiness result。
- request 与 discovery candidate 不一致时如何 fail-closed：字段不一致的 candidate 进入 `request_rejected_candidates`，附 machine-readable rejection reasons；如果全部不兼容，最终 blocked。
- candidate 中出现 provider / mirror / unknown / local cache 如何处理：无条件 rejected，并保留拒绝原因，不进入 synthetic dry-run。
- request 的 `discovery_scope` 如何约束 dry-run：不得允许 download、parse_pdf、metric_extraction、provider lookup、output write、fixture write 或 manifest write 等动作暗示。
- 是否需要新增 request-driven dry-run result：建议新增 request envelope schema，而不是直接修改现有 synthetic dry-run result 的核心语义。

## 5. Future Integration Flow 草案

未来实现应采用纯内存流程：

1. Validate `official_disclosure_discovery_request.v1`
   - request 必须存在、schema valid、`not_for_trading_advice` 必须为布尔值 `true`。
   - request 中不得包含 forbidden markers 或任何 IO / network / parser / output intent。

2. Accept explicit synthetic discovery candidates as input
   - candidates 必须由调用方显式传入。
   - 不读取文件，不访问 URL，不下载，不联网，不查本地 cache，不调用 provider。

3. Check every synthetic candidate against request constraints
   - `stock_code`
   - `company_name` / company hint caveat
   - `exchange`
   - `query_period`
   - `period_end_date`
   - `requested_announcement_type`
   - `allowed_source_types`
   - `discovery_scope`

4. Reject mismatched candidates with machine-readable reasons
   - 每个 rejected candidate 应包含 `rejection_reasons`，例如 `stock_code_mismatch`、`period_mismatch`、`announcement_type_mismatch`、`source_type_not_allowed`、`forbidden_scope_intent`、`provider_source_forbidden`。

5. Pass only request-compatible candidates into existing discovery candidate normalizer
   - 只传递兼容候选。
   - normalizer 不得读取文件、联网、下载或解析 PDF。

6. Feed accepted normalized candidates into existing synthetic official disclosure pipeline dry-run
   - synthetic dry-run 只接收内存 payload。
   - 不生成 official metric facts，不生成 provider conflict，不写 output。

7. Merge request caveats / request blocked reasons / candidate blocked reasons / dry-run blocked reasons
   - request caveats 不可被覆盖。
   - request blocked reasons 优先级最高。
   - candidate 和 dry-run blocked reasons 合并后必须去重并保留来源。

8. Produce final request-driven dry-run readiness result
   - final result 必须表达 compatible / rejected candidates、merged blocked reasons、merged data gap plan、final caveats 和 `not_for_trading_advice=true`。

9. Run final recursive safety scan
   - 递归扫描 request、candidate、dry-run result、merged result。
   - 一旦发现 forbidden marker 或 forbidden intent，最终 result 必须 fail closed。

整个 flow 只处理显式传入 payload，不读文件，不访问 URL，不下载，不联网，不解析 PDF，不抽取指标，不生成 `official_metric_fact`，不生成 `provider_official_conflict`，不写 output，不写 fixtures，不写 accepted manifest，不接 Report V1，不接 provider adapter。

## 6. Future Schema / Result Shape 草案

建议新增独立 request-driven result schema：

```text
official_disclosure_request_synthetic_dry_run_result.v1
```

推荐字段：

- `schema_version`: 固定为 `official_disclosure_request_synthetic_dry_run_result.v1`。
- `request`: validated request snapshot。
- `security_identity`: request 中关联的 `security_identity.v1` snapshot；不得由 candidate 提升 confidence。
- `input_synthetic_candidates`: 原始显式传入 candidates 的安全摘要或结构化副本。
- `request_compatible_candidates`: 通过 request compatibility checks 的候选。
- `request_rejected_candidates`: 未通过 request compatibility checks 的候选及 machine-readable reasons。
- `synthetic_dry_run_result`: 现有 synthetic dry-run result 的嵌套结果；如果 request blocked 或无 compatible candidates，可为空或为 blocked skeleton。
- `merged_blocked_reasons`: request、candidate、dry-run 和 safety scan 的聚合 blocked reasons。
- `merged_data_gap_plan`: request-driven 层和 dry-run 层合并后的 data gap plan。
- `request_caveats`: request 原始 caveats。
- `dry_run_caveats`: dry-run 层 caveats。
- `final_caveats`: request、candidate、dry-run 和 safety caveats 的最终合并结果。
- `not_for_trading_advice`: 必须为 `true`。

推荐理由：

- 新增 request envelope 可以保留现有 `synthetic_official_disclosure_pipeline_dry_run_result.v1` 的职责，不把 request-specific compatibility / rejection / merge semantics 塞进现有 schema。
- request-driven result 需要表达 `input_synthetic_candidates`、`request_compatible_candidates`、`request_rejected_candidates`、`merged_blocked_reasons` 等 envelope 语义，这些不是原 synthetic dry-run 的核心职责。
- 未来如需变更 request-candidate compatibility rules，可以在 envelope 层迭代，不破坏 synthetic dry-run result。

备选方案：

- 复用现有 `synthetic_official_disclosure_pipeline_dry_run_result.v1` 并增加 request envelope 字段。
- 不推荐作为第一选择，因为容易模糊 synthetic dry-run 与 request-driven integration 的边界，也会增加回归风险。

## 7. Request-Candidate Compatibility Rules

未来实现必须采用 fail-closed compatibility rules：

- candidate `stock_code` 与 request `stock_code` 不一致 -> rejected: `stock_code_mismatch`。
- candidate `exchange` 与 request `exchange` 不一致 -> rejected: `exchange_mismatch`。
- candidate period 与 request `query_period` / `period_end_date` 不一致 -> rejected: `period_mismatch`。
- candidate `announcement_type` 与 request `requested_announcement_type` 不一致 -> rejected: `announcement_type_mismatch`。
- candidate `source_type` 不在 request `allowed_source_types` -> rejected: `source_type_not_allowed`。
- candidate `discovery_scope` 或 metadata 暗示 download / parse / metric extraction -> rejected: `forbidden_scope_intent`。
- candidate 来源显示 provider / mirror / unknown / local cache -> rejected: `forbidden_source_kind`。
- request blocked -> pipeline 不得继续，所有 candidates 不进入 normalizer / dry-run。
- request caveat 不得被 candidate 覆盖、删除或降级。
- candidate 不得提升 request 的 identity confidence。
- company hint 不得变成 verified company match。
- candidate 不得补充 request 中缺失的强身份验证结论。
- candidate 不得绕过 request `allowed_source_types`，即使 candidate 看起来是官方来源。
- candidate 不得引入 URL fetch、file read、cache read、output write 或 manifest write 意图。

推荐摘要：request 是硬约束，candidate 只能被 request 接受或拒绝，不能扩大 request scope、不能提升 request 身份置信度、不能引入任何执行性动作。

## 8. Fail-Closed Rules

未来实现必须覆盖以下 fail-closed 情况：

- missing request。
- invalid request。
- request blocked。
- request `not_for_trading_advice` missing / false / non-bool。
- no synthetic candidates。
- all synthetic candidates incompatible。
- partial candidate compatibility，需要最终结果明确 blocked / caveat / rejected candidates，不得静默忽略 rejected candidates。
- mixed compatible and incompatible candidates，需要保留完整 rejection summary。
- multiple official candidates，需要 blocked 或明确 disambiguation gap，不得自动任选一个。
- source conflict。
- request-candidate stock_code mismatch。
- request-candidate period mismatch。
- request-candidate announcement_type mismatch。
- request-candidate source_type mismatch。
- forbidden marker。
- request / dry-run caveat missing。
- merged blocked_reasons missing。
- merged data_gap_plan missing。
- output / write / report / provider / parser / download intent。
- final result 出现 `official_metric_fact`。
- final result 出现 `provider_official_conflict`。
- final result 暗示 Report V1、output baseline、fixture 或 accepted manifest 写入。

## 9. Safety Markers

未来 implementation 的 recursive safety scan 必须覆盖英文和中文 markers，并在嵌套 payload 中发现后 fail closed。

英文 markers：

- `token`
- `.env`
- `tushare_token`
- `provider live`
- `AkShare`
- `Tushare`
- `network`
- `HTTP`
- `fetch`
- `download`
- `CNInfo live`
- `SSE live`
- `PDF parser`
- `table extractor`
- `parse PDF`
- `metric extraction`
- `official_metric_fact`
- `provider_official_conflict`
- `Report V1`
- `accepted manifest write`
- `output baseline write`
- `fixture write`
- `buy`
- `sell`
- `hold`
- `target price`
- `portfolio`
- `position`
- `technical signal`
- `trading advice`
- `investment advice`

中文 markers：

- `买入`
- `卖出`
- `持有`
- `目标价`
- `仓位`
- `组合`
- `技术信号`
- `投资建议`
- `下载`
- `网络`
- `联网`
- `解析PDF`
- `PDF解析`
- `表格抽取`
- `指标抽取`
- `正式研报`
- `输出基线`
- `写入fixture`
- `写入accepted manifest`
- `读取token`
- `读取.env`
- `读取tushare_token`
- `调用AkShare`
- `调用Tushare`
- `调用CNInfo live`
- `调用SSE live`
- `调用provider`

注意：planning doc 可以列出安全 markers；future implementation 不得把这些 markers 当作执行意图，也不得因为测试需要而进行真实 IO / network / provider / parser 行为。

## 10. Future Implementation Expected Files

未来 implementation 推荐优先新增 standalone integration module：

Production:

- `src/fundamental_skill/data_verification/request_synthetic_dry_run_integration.py`
- `src/fundamental_skill/data_verification/__init__.py`，仅当 public API 需要导出时可改。

Tests:

- `tests/test_request_synthetic_dry_run_integration.py`
- `tests/test_request_synthetic_dry_run_integration_safety.py`

默认不修改：

- `official_disclosure_request.py`
- `security_identity.py`
- `synthetic_official_disclosure_pipeline_dry_run.py`
- `official_disclosure_discovery_candidate.py`
- registry / locator
- `schemas.py`
- `validators.py`

如果 future implementation 必须修改 existing modules，需要明确说明原因并标注 `requires approval`。可能需要审批的场景包括：

- existing module 不暴露纯内存 API，standalone integration 无法复用。
- existing safety scan 不能递归扫描 request-driven envelope。
- existing dry-run result schema 无法被 envelope 安全嵌套。
- existing normalizer 会隐式 IO / network / parser，需要先隔离出 pure function。

## 11. Future Implementation Forbidden Files

未来 implementation 禁止修改或触碰：

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

本阶段也不得处理上述文件或范围。

## 12. Future Tests

未来 implementation 至少需要覆盖：

- valid request + compatible single CNInfo synthetic candidate。
- valid request + compatible SSE / exchange synthetic candidate。
- request blocked -> no dry-run。
- no candidates -> blocked result。
- all candidates incompatible -> blocked result。
- mixed compatible / incompatible candidates。
- stock_code mismatch rejected。
- query_period / period_end_date mismatch rejected。
- announcement_type mismatch rejected。
- source_type not allowed rejected。
- provider / mirror / unknown / local cache rejected。
- request caveats preserved。
- company hint remains unverified。
- candidate cannot raise identity confidence。
- candidate cannot generate verified company match。
- nested forbidden markers rejected。
- request / dry-run merged blocked_reasons required。
- merged data_gap_plan required。
- final result cannot contain `official_metric_fact`。
- final result cannot contain `provider_official_conflict`。
- final result cannot contain Report V1 / output / fixture / manifest intent。
- no IO / no network / no URL fetch / no file read。

测试策略：

- 使用显式内存 payload。
- 使用 monkeypatch / sentinel guard 阻断 file open、network client、provider adapter、download、PDF parser 等入口。
- safety tests 递归扫描嵌套 dict / list / string。
- compatibility tests 校验每个 rejected candidate 的 machine-readable reason。

## 13. Regression Subset

未来 implementation 后建议至少运行：

- `tests/test_request_synthetic_dry_run_integration.py`
- `tests/test_request_synthetic_dry_run_integration_safety.py`
- `tests/test_official_disclosure_request.py`
- `tests/test_official_disclosure_request_safety.py`
- `tests/test_security_identity.py`
- `tests/test_security_identity_safety.py`
- `tests/test_synthetic_official_disclosure_pipeline_dry_run.py`
- `tests/test_synthetic_official_disclosure_pipeline_dry_run_safety.py`
- `tests/test_official_disclosure_discovery_candidate.py`
- `tests/test_official_disclosure_discovery_candidate_safety.py`
- `tests/test_official_verification_safety.py`

如果修改 `schemas.py` / `validators.py`，还需要运行 official verification schema / validator subset。默认建议避免修改 shared schemas / validators，除非 request-driven envelope schema 必须进入统一 schema registry，且获得明确 approval。

## 14. 是否需要三方审计

当前 docs-only planning 不需要三方审计。

future implementation 如果只新增 isolated integration module + tests，不改 existing modules，可以先不默认要求 Gemini / DeepSeek / Kimi 三方审计，但建议在 acceptance review 中保留人工复核。

future implementation 如果修改以下边界，建议进行 Gemini / DeepSeek / Kimi 三方审计：

- request contract。
- `security_identity`。
- synthetic dry-run。
- discovery candidate normalizer。
- shared validators / schemas。
- recursive safety scan。
- request-candidate handoff boundary。
- 任何可能引入 IO / network / provider / parser / output write 的代码路径。

## 15. Acceptance Criteria

Planning acceptance：

- 只新增 docs planning 文件。
- no production code。
- no tests。
- no output / fixtures / accepted manifest。
- no token / `.env` / `tushare_token.txt` read。
- no mojibake handling。
- request-candidate compatibility rules 清晰。
- future result shape 清晰。
- fail-closed rules 清晰。
- expected files / tests 清晰。
- forbidden scope 清晰。
- implementation entry can be approved or rejected。

Future implementation acceptance：

- only expected production / test files changed。
- no IO。
- no network。
- no provider。
- no PDF parser。
- no output / fixture / manifest write。
- no Report V1。
- request-driven integration fail closed。
- safety tests pass。
- request / security identity / synthetic dry-run / discovery regressions pass。
- no blocker remains open。

## Recommendation Summary

建议新增 standalone integration module：是。优先新增 `request_synthetic_dry_run_integration.py`，把 request-candidate compatibility、caveat merge、blocked reason merge 和 request-driven envelope result 放在独立层，避免污染 request contract、security identity、candidate normalizer 和 existing dry-run。

建议新增 request-driven result schema：是。推荐 `official_disclosure_request_synthetic_dry_run_result.v1`，并将现有 `synthetic_official_disclosure_pipeline_dry_run_result.v1` 作为嵌套结果复用，而不是直接扩展其核心职责。

是否建议进入 future implementation：可以进入，但前提是 implementation scope 被批准为 synthetic-only、in-memory-only、explicit-payload-only、no IO、no network、no provider、no parser、no output write。

是否建议三方审计：当前 planning 不需要；future implementation 如只新增 isolated module + tests，可先不默认要求；若触碰 shared validators / schemas / safety scan / existing modules，则建议三方审计。
