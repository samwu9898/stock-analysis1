# Official Disclosure Pipeline Next-Slice Reassessment Plan

Date: 2026-06-01

Stage: Official Disclosure Pipeline Next-Slice Reassessment / Planning.

Status: documentation-only reassessment. This stage only evaluates the next
reasonable slice after the Official Disclosure Source Registry + Locator gate.
It does not write production code, tests, fixtures, outputs, accepted manifests,
provider adapters, Report V1 artifacts, token files, or runtime baselines. It
does not use network access, download files, parse PDFs, extract metrics, commit,
or push.

## 1. 阶段名称和当前 baseline

当前阶段名称：

```text
Official Disclosure Pipeline Next-Slice Reassessment / Planning
```

当前 baseline commits：

| Commit | Scope |
| --- | --- |
| `c687792402973d6dcf7621326d2371169fefee3a` | Official Verification Productionization Minimal Implementation |
| `5695135aa1c72bbe2391c8545746a540014bc3b7` | Official Verification acceptance summary |
| `ad95e14ae6b629ba6ef03b91c23110849922a22d` | Official Disclosure Source Registry + Locator Thin Slice Plan |
| `0699944c5ab7218614e973158c4a87c77ac48fef` | Official Disclosure Source Registry + Locator Thin Slice Minimal Implementation |
| `3d81527d22c9b740fc68e1fcc32ff6b5f0662ac6` | Official Disclosure Source Registry + Locator Thin Slice Implementation Acceptance Summary |

`git log --oneline -5` 当前显示：

```text
3d81527 docs: add official disclosure registry locator acceptance summary
0699944 feat: add official disclosure registry locator gate
ad95e14 docs: add official disclosure source registry locator plan
5695135 docs: accept official verification data gate
c687792 feat: add official verification data gate
```

当前 registry / locator gate 已完成并已完成 acceptance summary。现有
official verification data gate 与 source registry / locator gate 均为
fail-closed、显式输入、无联网、无 PDF 解析、无 provider adapter、无 Report V1
连接的最小生产基线。

当前剩余 untracked 项为：

```text
.local_experiments/
tushare_token.txt
unrelated mojibake HTML/Markdown/example files
```

这些 untracked 项不得读取、修改、删除、移动、stage、commit 或 push。本阶段不处理
`.local_experiments`、`tushare_token.txt`、`.env`、unrelated mojibake 文件、
examples 下的 unrelated 文件，且不得使用 `git add .` 或 `git add -A`。

## 2. 当前能力地图

### 2.1 Official verification data gate

系统已经具备 official verification data gate 的最小生产能力：

- `official_metric_fact.v1` schema / validator；
- `provider_official_conflict.v1` schema / validator；
- `official_source_candidate.v1` schema / validator；
- `official_verification_run_summary.v1` schema / validator；
- `blocked_until_review_item.v1` schema / validator；
- official source candidate 准入策略；
- provider / mirror / third-party source 不得自动 promotion；
- unresolved conflict、blocked item、低质量 extraction 不得 promotion；
- `not_for_trading_advice=true` 递归强制；
- forbidden marker 递归安全扫描；
- token、`.env`、provider live、network、Report V1、output write、trading
  advice markers 的 fail-closed 拦截。

该能力层解决的是“已存在的官方或候选事实能否进入 verified / candidate /
conflict / blocked lane”，而不是解决官方披露文件如何被发现、下载、解析或抽取。

### 2.2 Official source registry entry

系统已经具备 `official_source_registry_entry.v1` 的最小生产 gate：

- registry entry schema version；
- source id / stock code / company name / period / announcement type；
- source type、source status、refresh policy、registry version、source version；
- official URL、source title、disclosure date、optional local cache path；
- cached official file 所需的 `file_sha256`；
- `rejection_reason` / `caveats` / `not_for_trading_advice`；
- pure helper，用于 source type 分类、sha256 格式校验、source conflict
  reason 构造、official candidate / official cache lane eligibility 判定；
- 不读文件、不计算真实文件 hash、不下载、不联网、不调用 provider、不写输出。

### 2.3 Official disclosure locator result

系统已经具备 `official_disclosure_locator_result.v1` 的最小生产 gate：

- locator result schema version；
- request stock / company / period / announcement type 对齐；
- structured candidates / rejected candidates / source conflicts；
- `selected_official_source_id` 仅在唯一 selectable official candidate 且无冲突时可填充；
- 多候选默认 review required；
- rejected / blocked / conflict 状态结构化返回；
- locator 不生成 `official_metric_fact.v1`，不做 provider-vs-official
  reconciliation，不触发 Report V1。

### 2.4 Source type / source status / locator status

系统已具备官方披露 source lane 的有限枚举和 fail-closed 策略：

- official source types: CNInfo official PDF、SSE / exchange official
  announcement、exchange official PDF、local official cache；
- discovery-only / rejected source types: mirror source candidate、provider
  source candidate、unknown source candidate；
- source status: `official_candidate`、`official_cached`、
  `rejected_mirror`、`rejected_provider_endpoint`、`missing_sha256`、
  `missing_required_metadata`、`source_conflict`、`blocked_until_review`；
- locator status: `found_single_official_candidate`、
  `found_multiple_candidates_review_required`、`no_official_source_found`、
  `rejected_all_candidates`、`blocked_until_review`。

### 2.5 SHA256 / cache / versioning policy

系统已经具备 cache 与 versioning 的边界：

- cached official file 必须同时具备 original official URL、local cache path、
  valid `file_sha256`；
- `file_sha256` 必须是 64 位十六进制 digest；
- missing sha256 不能进入 `official_cached`；
- same URL / different sha256 必须产生 conflict 或 review item，不能 silent overwrite；
- `registry_version`、`source_version`、`source_refresh_policy` 必须存在；
- `.local_experiments` cache 不得自动进入 production registry；
- 第一版仍为 explicit metadata only，不执行 live download。

### 2.6 Recursive safety scan

系统已经复用并扩展 recursive safety scan，可在嵌套 dict/list/value 中阻断：

- token / `.env` / `tushare_token.txt`；
- provider live / network / CNInfo/SSE live intent；
- Report V1 / accepted manifest write / output baseline write / fixture write；
- PDF parser / PDF table extractor / metric extraction；
- trading advice、target price、position、technical signal 及中文等价 marker。

### 2.7 Fail-closed source lane

source lane 的 fail-closed 行为已经具备：

- mirror / provider / unknown source 不得进入 official candidate 或 cache lane；
- local cache without official URL blocked；
- missing metadata blocked；
- missing or invalid sha256 blocked；
- source conflict blocks downstream readiness；
- `not_for_trading_advice=false` rejected；
- forbidden markers rejected。

### 2.8 Fail-closed locator lane

locator lane 的 fail-closed 行为已经具备：

- exactly one selectable official candidate 才能 single-select；
- multiple official candidates 必须 review required；
- selected source 必须是完整 registry entry；
- selected source 不能指向 mirror / provider / unknown / blocked candidate；
- no official source found、rejected all、blocked until review 均可结构化返回；
- locator 不下载、不读取文件、不解析 PDF、不生成 metric fact、不调用 provider。

## 3. 当前缺口地图

当前系统仍未具备以下能力：

| Gap | Current State | Why It Matters |
| --- | --- | --- |
| company / ticker identification integration | 尚未将用户输入、ticker、公司名、交易所、证券代码规范化接入 official disclosure lane | 没有稳定 subject identity，后续 discovery request 容易错配公司 |
| official disclosure discovery input contract | 尚未定义 discovery adapter 未来输出到 registry / locator 前的 candidate contract | 当前只能显式传入 registry candidates，缺少 discovery output 的准入接口 |
| CNInfo / SSE / Exchange source discovery adapter | 尚未实现官方入口 discovery adapter | 不能自动发现官方披露 URL，也不应在 contract 前进入 live adapter |
| source download / cache acquisition | 尚未实现 controlled downloader 或 cache acquisition | 当前只允许 explicit metadata，不允许 live download |
| PDF parser / table extractor | 尚未实现官方 PDF 解析或表格抽取 | 当前无法从官方 PDF 自动抽取指标 |
| official metric extraction | 尚未从官方披露文件生成 `official_metric_fact.v1` | data gate 有 schema，但没有真实官方披露抽取生产路径 |
| provider-vs-official reconciliation at real pipeline level | 尚未在真实 pipeline 中把 official facts 与 provider facts 对账 | 当前只有 data gate / conflict gate，未串入真实运行流 |
| Research Pack integration | 尚未将 verified / candidate / conflict / blocked evidence 集成到 research pack | 用户可见研究包仍不能消费这一官方披露 evidence lane |
| user-facing Evidence Panel integration | 尚未形成用户可读 Evidence Panel | 用户无法直接看到来源、缺口、blocked reason、review required reason |

这些缺口存在优先级差异。最靠近当前 gate 的缺口不是 live download 或 PDF
extraction，而是 official disclosure discovery output 在进入 registry / locator
前的 contract。

## 4. 下一刀候选方案

### A. Official Disclosure Discovery Candidate Contract Thin Slice

目标：定义 future discovery output 的 schema / validator / pure normalization
contract。

输入：显式传入的 synthetic discovery candidates。

输出：可进入 registry / locator 的 normalized candidate object。

边界：

- 不做 IO；
- 不联网；
- 不下载；
- 不解析；
- 不读取 token 或 `.env`；
- 不生成 metric fact；
- 不连接 provider adapter 或 Report V1。

价值：

- 为未来 CNInfo / SSE / exchange discovery adapter 留出稳定接口；
- 把“发现结果是什么”与“如何联网发现”拆开；
- 可用纯内存 payload 做 validator 和 safety tests；
- 与当前 registry / locator gate 连续性最高；
- 是后续 synthetic pipeline dry-run 的前置契约。

主要风险：

- 如果字段过早过宽，可能把 live discovery / download concern 泄漏进 contract；
- 如果直接把 contract 与 dry-run 合并，容易在同一阶段扩大到 orchestration。

### B. Synthetic Official Disclosure Pipeline Dry-Run Thin Slice

目标：使用内存 synthetic candidates 串起 discovery candidate -> registry entry
-> locator result -> verification input readiness skeleton。

边界：

- 不写 fixture；
- 不写 output baseline；
- 不接 Report V1；
- 不生成 `official_metric_fact.v1`；
- 不生成 `provider_official_conflict.v1`；
- 不联网、不下载、不解析。

价值：

- 验证 registry / locator gate 能否被 pipeline 组合使用；
- 能较早暴露 contract 到 registry / locator 的字段缺口；
- 为未来 research pack readiness 提供骨架。

主要风险：

- 如果 discovery candidate contract 尚未稳定，dry-run 容易把 schema 争议和
  pipeline 组合争议混在一起；
- 容易误触 output / fixture / Report V1 / provider integration 边界；
- 测试面比 A 更宽，stage review 成本更高。

### C. Official PDF Extraction Boundary Plan

目标：只规划 PDF parser / table extractor 的边界、输入输出、review queue 和失败路径。

边界：

- 不实现 parser；
- 不下载 PDF；
- 不解析 PDF；
- 不生成 official metric fact；
- 不连接 provider 或 Report V1。

价值：

- 为未来官方指标抽取建立安全边界；
- 提前定义 review queue、quality hint、traceability、blocked reason。

主要风险：

- 与当前 registry / locator gate 的连续性较弱；
- 容易让下一阶段误以为可以直接实现 parser；
- 仍缺 discovery candidate contract，PDF extraction 的输入来源未稳定。

### D. Research Pack Evidence Panel Bridge Plan

目标：规划将 verified / candidate / conflict / blocked 映射到用户可读
Evidence Panel。

边界：

- 不生成正式报告；
- 不接 Report V1；
- 不写 output baseline；
- 不写 accepted manifest；
- 不连接 provider。

价值：

- 直接回应用户对可读性、趋势、缺口说明和证据链解释的需求；
- 可以提前定义 evidence lane 的展示语义；
- 有助于避免未来把 blocked / conflict 隐藏在内部日志里。

主要风险：

- 当前 official disclosure pipeline 尚未形成 discovery -> registry -> locator
  -> verification readiness 的稳定链路；
- 过早做 UI / research pack bridge 可能倒逼 Report V1 或 output shape；
- 对当前 registry / locator gate 的技术连续性中等。

### E. Live Source Download Readiness Gate

目标：只评估什么时候才允许进入 live download。

边界：

- 本阶段不得实现 downloader；
- 不联网；
- 不下载 PDF；
- 不接 CNInfo / SSE / exchange live；
- 不读取 token 或 `.env`。

价值：

- 提前定义 live acquisition 的 blocker checklist；
- 可把 official domain allowlist、redirect policy、content-type、file size、
  sha256、cache write policy、安全审计要求写清楚。

主要风险：

- 当前 contract 尚未定义，readiness gate 容易过早围绕 downloader 设计；
- live download 是高风险能力，可能引入网络、存储、hash、重定向和 source
  promotion 的复杂性；
- 不适合作为 registry / locator gate 之后的第一刀 implementation。

## 5. 候选方案评分矩阵

评分说明：5 = 强 / 高 / 很适合；1 = 弱 / 低 / 不适合。风险项中 5 表示风险高，
1 表示风险低。

| Candidate | 用户价值 | 证据链价值 | fail-closed 风险 | scope creep 风险 | 与 registry/locator 连续性 | 需要网络 | 需要 PDF parser | 误触 Report V1/provider/output/fixtures 风险 | 可测试性 | 适合作为下一阶段 implementation |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| A. Discovery Candidate Contract | 4 | 5 | 1 | 2 | 5 | 否 | 否 | 1 | 5 | 是，但建议先过 readiness gate |
| B. Synthetic Pipeline Dry-Run | 4 | 5 | 2 | 4 | 4 | 否 | 否 | 3 | 4 | 可作为 A 之后的第二阶段 |
| C. PDF Extraction Boundary Plan | 3 | 4 | 3 | 3 | 2 | 否 | 否，本方案只规划 | 2 | 3 | 不建议作为下一阶段 implementation |
| D. Evidence Panel Bridge Plan | 5 | 4 | 2 | 4 | 3 | 否 | 否 | 4 | 3 | 不建议现在 implementation |
| E. Live Download Readiness Gate | 3 | 4 | 5 | 5 | 3 | 当前否，未来是 | 否 | 4 | 2 | 不建议作为下一阶段 implementation |

判断：

- A 是最小、最连续、最 fail-closed 的下一刀。
- B 有价值，但应该依赖 A 的 contract；若与 A 合并，scope creep 风险明显升高。
- C 应继续停留在 boundary planning，不应进入 parser implementation。
- D 用户价值高，但当前证据链还缺 pipeline contract，过早 bridge 会牵引 Report V1
  和 output shape。
- E 重要但高风险；在 contract、dry-run、review gate 稳定前不应进入 live source
  acquisition。

## 6. 推荐下一阶段

推荐阶段名称：

```text
Official Disclosure Discovery Candidate Contract Implementation Readiness Gate
```

推荐结论：建议把默认倾向中的 “Official Disclosure Discovery Candidate Contract
+ Synthetic Pipeline Dry-Run” 拆成两个阶段。第一阶段只做 Discovery Candidate
Contract 的 implementation readiness gate；第二阶段在 contract accepted 之后，
再单独规划 Synthetic Official Disclosure Pipeline Dry-Run。

### 6.1 为什么选它

选择 A 的 readiness gate，是因为它是当前 registry / locator gate 之后最靠近、
最小、最容易 fail-closed 的缺口：

- registry / locator 只能处理显式 candidates；下一步需要定义 discovery adapter
  未来输出的候选对象长什么样；
- contract 可通过纯 schema / validator / normalization rules 定义，不需要 IO、
  network、download、PDF parser、provider adapter 或 Report V1；
- contract 稳定后，B 的 synthetic dry-run 才有清晰输入；
- contract 可以把 mirror/provider/unknown/live/download/parser intent 继续阻断在
  official lane 外；
- 可测试性高，可完全使用内存 payload。

### 6.2 为什么不选其他方案

- 不优先选 B：B 是正确的后续方向，但应依赖 A。若把 A+B 合并为一个 implementation
  slice，会同时引入 schema、normalization、pipeline assembly、readiness skeleton
  和 regression scope，review 面过大。
- 不优先选 C：PDF extraction 仍缺稳定 source discovery candidate contract，且
  容易误导下一阶段进入 parser/table extractor。
- 不优先选 D：Evidence Panel 用户价值高，但当前 evidence lane 尚未形成从 discovery
  candidate 到 locator readiness 的完整 contract，过早 bridge 容易触碰 Report V1
  / output / user-facing report。
- 不优先选 E：live download 是高风险能力，必须等 contract、dry-run 和 downloader
  readiness blockers 全部明确后再进入。

### 6.3 是否需要先做 Implementation Readiness Gate

需要。下一阶段应仍是 readiness gate，而不是直接 implementation。

readiness gate 应明确：

- discovery candidate schema；
- allowed source types and statuses；
- normalization input / output；
- strict forbidden markers；
- promotion boundary into registry / locator；
- expected production files；
- expected tests；
- no IO / no network / no download / no parser / no provider / no output /
  no fixture / no Report V1 safety requirements。

### 6.4 是否允许 implementation

当前阶段不允许 implementation。

下一阶段如果仅是 `Official Disclosure Discovery Candidate Contract
Implementation Readiness Gate`，也不应写 production code 或 tests，只写 planning /
readiness doc。只有该 readiness gate 被 acceptance review 接受后，才建议进入一个
窄范围 implementation slice。

### 6.5 未来 implementation allowed files

若 readiness gate 被接受，未来 implementation slice 可考虑仅允许：

```text
src/fundamental_skill/data_verification/schemas.py
src/fundamental_skill/data_verification/validators.py
src/fundamental_skill/data_verification/official_disclosure_discovery_candidate.py
src/fundamental_skill/data_verification/__init__.py
tests/test_official_disclosure_discovery_candidate.py
tests/test_official_disclosure_discovery_candidate_safety.py
```

`__init__.py` 仅在需要暴露稳定 public API 时可改。

### 6.6 未来 implementation forbidden files

未来 implementation slice 仍应禁止修改：

```text
src/fundamental_skill/reporting/
src/fundamental_skill/providers/
src/fundamental_skill/provider_adapter*
src/fundamental_skill/research_report*
src/fundamental_skill/report_v1*
examples/
fixtures/
output/
docs/accepted_manifest*
.local_experiments/
tushare_token.txt
.env
```

同时禁止处理 unrelated mojibake files，禁止写 accepted manifest、output baseline、
fixtures、Report V1 generator、provider adapter、token 文件。

### 6.7 Expected tests

未来 implementation tests 应使用纯内存 payload，覆盖：

- valid CNInfo / SSE / exchange discovery candidate normalization；
- mirror candidate remains discovery-only and cannot become official；
- provider candidate rejected from official lane；
- unknown source blocked；
- missing stock code / company / period / announcement type / title /
  disclosure date blocked；
- missing official URL blocked for official candidate；
- local cache intent rejected at discovery candidate layer unless explicitly
  represented as metadata-only and not promoted to cache lane；
- network / download / parser / provider / token / `.env` / Report V1 /
  accepted manifest / output / fixture markers rejected；
- `not_for_trading_advice=true` required；
- `not_for_trading_advice=false` rejected；
- no file existence checks；
- no real path reads；
- no live adapter invocation；
- normalized candidate can be consumed by existing registry / locator helpers
  only through explicit handoff, not implicit side effects。

### 6.8 Acceptance criteria

未来 implementation readiness gate acceptance criteria：

- only approved docs file changed during readiness gate；
- explicit candidate contract fields listed；
- field-level required / optional / conditional policy listed；
- normalization behavior defined without IO；
- source type mapping into registry / locator listed；
- fail-closed behavior listed；
- expected files and tests listed；
- forbidden files and actions listed；
- no network, no download, no parser, no provider, no Report V1, no output,
  no fixture, no accepted manifest, no token read；
- acceptance reviewer can decide whether implementation may begin。

未来 implementation acceptance criteria：

- only expected production / test files changed；
- no output / fixture / accepted manifest / token / `.env` / untracked file
  changes；
- discovery candidate validator and normalizer pass focused tests；
- safety tests prove forbidden markers fail closed；
- registry / locator regression subset passes；
- no live source discovery adapter exists；
- no downloader / parser / metric extraction exists；
- no Report V1 / provider integration exists。

### 6.9 Blocker checklist

进入未来 implementation 前必须全部确认：

- readiness gate accepted；
- candidate schema version named；
- required fields finalized；
- source type mapping finalized；
- forbidden marker list finalized；
- no IO policy accepted；
- no network policy accepted；
- no local file read policy accepted；
- no output / fixture / accepted manifest write policy accepted；
- tests can run without tokens, `.env` or provider configuration；
- no dependency on `.local_experiments`；
- no dependency on unrelated mojibake files；
- rollback path is limited to candidate contract files。

## 7. 下一阶段边界草案

推荐进入的下一阶段：

```text
Official Disclosure Discovery Candidate Contract Implementation Readiness Gate
```

### 7.1 Allowed scope

- 新增一个 readiness / implementation plan doc；
- 定义 discovery candidate contract；
- 定义 candidate normalization rules；
- 定义 registry / locator handoff rules；
- 定义 source type / status / rejection policy；
- 定义 safety markers；
- 定义 expected implementation files and tests；
- 定义 acceptance review checklist。

### 7.2 Forbidden scope

- 不写 production code；
- 不写 tests；
- 不联网；
- 不下载；
- 不读取本地 source file；
- 不读取 token、`.env`、`tushare_token.txt`；
- 不解析 PDF；
- 不实现 PDF parser；
- 不实现 PDF table extractor；
- 不做 metric extraction；
- 不生成 `official_metric_fact.v1`；
- 不生成 `provider_official_conflict.v1`；
- 不连接 provider adapter；
- 不连接 AkShare / Tushare / CNInfo / SSE live；
- 不写 accepted manifest；
- 不写 output baseline；
- 不写 fixtures；
- 不接 Report V1；
- 不生成正式研报；
- 不输出 trading advice、target price、position、technical signal；
- 不处理 `.local_experiments` 或 unrelated mojibake files；
- 不 commit；
- 不 push。

### 7.3 Expected files

Readiness gate 阶段只应新增一个 docs 文件，例如：

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_DISCOVERY_CANDIDATE_CONTRACT_IMPLEMENTATION_READINESS_GATE.md
```

该 readiness gate 不应修改 production code 或 tests。

若后续 implementation 被批准，expected files 才可限定为第 6.5 节所列 production
和 test 文件。

### 7.4 Expected tests

Readiness gate 阶段不运行或新增 tests，除非审查方明确要求只运行现有只读测试。

未来 implementation 阶段 expected tests：

```text
tests/test_official_disclosure_discovery_candidate.py
tests/test_official_disclosure_discovery_candidate_safety.py
tests/test_official_disclosure_source_registry.py
tests/test_official_disclosure_locator.py
tests/test_official_disclosure_registry_locator_safety.py
```

测试必须不依赖 network、token、`.env`、fixtures、output baseline、accepted manifest、
`.local_experiments` 或真实 PDF。

### 7.5 Fail-closed rules

下一阶段必须保留以下 fail-closed rules：

- missing identity / period / announcement type / title / disclosure date blocked；
- unknown source type blocked；
- provider endpoint cannot become official；
- mirror source cannot become official；
- network / download / parser intent rejected；
- token / `.env` / `tushare_token.txt` marker rejected；
- Report V1 / accepted manifest / output / fixture write marker rejected；
- metric extraction / official metric fact / provider official conflict marker rejected；
- trading advice / target price / position / technical signal marker rejected；
- local file path is inert metadata only and cannot trigger file read；
- normalized candidate cannot silently promote itself to verified fact。

### 7.6 Safety markers

Safety markers must continue to include English and Chinese equivalents for:

- network / live download / fetch / HTTP / CNInfo live / SSE live；
- PDF parser / PDF table extractor / parse PDF；
- provider live / AkShare / Tushare；
- token / `.env` / `tushare_token.txt`；
- accepted manifest write / output baseline write / fixture write；
- Report V1 / formal report generation；
- buy / sell / hold / target price / portfolio / position / technical signal；
- metric extraction / `official_metric_fact` / `provider_official_conflict`。

### 7.7 Regression subset

未来 implementation 后建议至少运行：

```text
tests/test_official_disclosure_discovery_candidate.py
tests/test_official_disclosure_discovery_candidate_safety.py
tests/test_official_disclosure_source_registry.py
tests/test_official_disclosure_locator.py
tests/test_official_disclosure_registry_locator_safety.py
tests/test_official_verification_safety.py
```

如修改 `schemas.py` 或 `validators.py`，还应运行 existing official verification
schema / validator subset。

### 7.8 Acceptance review checklist

下一阶段 readiness gate acceptance review 应确认：

- 只新增/修改 approved docs planning 文件；
- no production code changed；
- no tests changed；
- no output / fixtures / accepted manifest changed；
- no token / `.env` / `tushare_token.txt` read；
- no `.local_experiments` or mojibake untracked files handled；
- candidate contract fields are complete enough for A implementation；
- B synthetic dry-run remains separate；
- live download remains blocked；
- PDF parser / table extractor remains blocked；
- provider adapter and Report V1 remain blocked；
- acceptance reviewer can explicitly approve or reject implementation entry。

## 8. 明确禁止事项

下一阶段仍不得默认进入：

- live download；
- network；
- PDF parser；
- PDF table extractor；
- metric extraction；
- provider adapter；
- Report V1；
- accepted manifest write；
- output baseline write；
- fixture write；
- token read；
- `.env` read；
- `tushare_token.txt` read；
- `.local_experiments` handling；
- unrelated mojibake files handling；
- AkShare / Tushare / CNInfo / SSE live；
- formal research report generation；
- trading advice / target price / position / technical signal。

这些事项必须继续作为 blocker，而不是作为默认实现路径或隐式 side effect。

## 9. Final recommendation

推荐下一阶段：

```text
Official Disclosure Discovery Candidate Contract Implementation Readiness Gate
```

建议拆成两个阶段：

1. Discovery Candidate Contract Implementation Readiness Gate；
2. Synthetic Official Disclosure Pipeline Dry-Run Thin Slice。

第一阶段的目标是把 future discovery adapter 的输出 contract 固定下来。第二阶段再用
纯内存 synthetic candidates 验证 contract -> registry entry -> locator result ->
verification input readiness skeleton 的组合路径。

当前不建议进入 live source download、PDF parser、PDF table extractor、metric
extraction、provider adapter、Report V1、accepted manifest write、output baseline
write、fixture write、Research Pack / Evidence Panel bridge implementation。
