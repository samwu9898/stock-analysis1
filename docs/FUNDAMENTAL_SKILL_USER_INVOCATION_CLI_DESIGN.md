# Fundamental Skill User Invocation CLI / Command Wrapper Design

Date: 2026-05-28

Stage: Fundamental Skill User Invocation CLI / Command Wrapper Design and
Runtime Acceptance Sync.

Status: design accepted, CLI implementation accepted, three-sample CLI runtime
acceptance complete, single-stock offline CLI baseline frozen, CLI usage guide
recorded, accepted manifest module accepted, manifest-first locator hardening
accepted, retained runtime manifest review accepted, and manifest locator
runtime baseline frozen. This document remains the command argument, output
behavior, error behavior, and safety-boundary design source. The runtime acceptance
closeout is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`, and the CLI usage
guide is recorded in `docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`. This
documentation sync does not implement code, change tests, change fixtures,
generate runtime output, run smoke tests, read `TUSHARE_TOKEN`, use the
network, call Tushare or AkShare, connect MCP, change scoring / readiness,
change Research Intelligence P1.1, change regression expected files, or
provide trading advice.
Accepted artifact manifest / freshness design is recorded in
`docs/FUNDAMENTAL_ACCEPTED_ARTIFACT_MANIFEST_FRESHNESS_DESIGN.md`; it defines
the accepted CLI locator and freshness stdout behavior. Manifest locator
runtime acceptance closeout is recorded in
`docs/FUNDAMENTAL_ACCEPTED_MANIFEST_LOCATOR_RUNTIME_ACCEPTANCE_SUMMARY.md`.

Accepted upstream state:

- Single-stock offline orchestration implementation accepted.
- Chinese summary patch accepted.
- `600406`, `002371`, and `002050` one-sentence offline runtime invocations
  accepted.
- Offline local invocation baseline frozen.
- CLI implementation accepted.
- `600406`, `002371`, and `002050` CLI runtime invocations accepted.
- Single-stock offline CLI baseline frozen.
- CLI runtime acceptance summary recorded in
  `docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`.
- CLI usage guide recorded in `docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`.
- Default mode remains `offline_local_artifacts`, `no_live_provider`, no token,
  no network, no provider call, and no MCP.
- CLI locator behavior reads the accepted manifest first, exposes manifest and
  freshness status, and treats timestamp-latest lookup as a warned fallback.
  The retained runtime manifest baseline is frozen for `600406`, `002371`, and
  `002050`.

## 1. CLI Goal

The CLI should package the accepted single-stock offline orchestration behind a
stable command. The goal is operational simplicity, not new report logic.

Required product behavior:

- Codex can generate or locate a single-stock report by running one command.
- The user does not need to manually run candidate builders, report builders,
  Markdown renderers, or HTML renderers.
- The CLI calls the accepted orchestration path.
- The CLI does not reimplement report logic, reinterpret evidence, or create a
  parallel reporting pipeline.

The CLI is a command wrapper over the accepted orchestration functions. It is
not a provider runner, not a live-data connector, not a batch engine, and not a
new source of analytical truth.

## 2. Command Shape

Primary stock-code invocation:

```bash
python -m src.fundamental_skill.research_report.generate_report --code 600406 --format html --data-mode offline_local_artifacts
```

Company-name invocation:

```bash
python -m src.fundamental_skill.research_report.generate_report --company-name 北方华创 --format html
```

The command module name should be stable:

```text
src.fundamental_skill.research_report.generate_report
```

The command should resolve to the same accepted orchestration behavior that has
already passed offline runtime acceptance. It should not expose old runner
entry points as the user-facing path.

## 3. Parameter Design

| Parameter | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--code` | required unless `--company-name` is present | none | A-share stock code, such as `600406`. Code is primary when both code and company name are supplied. |
| `--company-name` | required unless `--code` is present | none | Company name or local alias, such as `北方华创`. Resolution must use local metadata / accepted artifacts only in offline modes. |
| `--format` | no | `html` | Output selection: `json`, `markdown`, `html`, or `all`. Even `html` should return JSON / Markdown paths when available or generated as intermediate artifacts. |
| `--data-mode` | no | `offline_local_artifacts` | Input mode: `offline_local_artifacts` or `local_provider_comparison`. No live provider mode is part of this CLI design. |
| `--provider-comparison-root` | no | none | Optional local root for already generated provider-comparison artifacts. Used only with `local_provider_comparison`; never triggers live provider calls. |
| `--output-root` | no | `output/research_reports` | Root for located or generated Research Report V1 outputs. Runtime outputs remain ignored artifacts and must not be submitted. |
| `--timestamp` | no | generated by orchestration when output is produced | Optional deterministic timestamp for local output routing. It must not imply fixture promotion or regression updates. |
| `--no-network` | no | `true` | Safety flag. Current CLI must fail closed if any path attempts network access. |
| `--no-token-read` | no | `true` | Safety flag. Current CLI must not read `TUSHARE_TOKEN` or any provider token. |
| `--not-for-trading-advice` | no | `true` | Required boundary flag for all user-facing outputs. |
| `--strict-evidence-boundary` | no | `true` | Required boundary flag. The CLI must not upgrade candidate, missing, or disputed evidence through wording. |

Effective internal options:

| Internal option | Effective value | Boundary |
| --- | --- | --- |
| `provider_mode` | `no_live_provider` | No live provider can be selected by default or by fallback. |
| `provider_transport` | `none` | No SDK, HTTP, MCP, or provider transport is available in this CLI stage. |

If future implementation exposes `--provider-mode` or `--provider-transport`
for diagnostics, the only accepted current values are
`--provider-mode no_live_provider` and `--provider-transport none`. Any other
value must fail closed until a separately accepted live-provider design exists.

## 4. Defaults

Current V1 CLI defaults:

- `--format html`
- `--data-mode offline_local_artifacts`
- `--provider-mode no_live_provider`
- `--provider-transport none`
- `--no-network true`
- `--no-token-read true`
- `--not-for-trading-advice true`
- `--strict-evidence-boundary true`

Default behavior must remain local-only. The command must not silently upgrade
from `offline_local_artifacts` to `local_provider_comparison`, and it must not
silently upgrade from either offline mode to any live-provider path.

## 5. Output Behavior

The CLI should print a short Chinese operational result. It should not dump the
full report body unless a future explicit flag is designed for that purpose.

Required success fields:

- `status`
- `HTML path`
- `Markdown path`
- `JSON path`
- `中文摘要`
- `最大机会`
- `最大风险`
- `最大证据缺口`
- `数据质量状态`
- `重要声明`

Recommended shape:

```text
status: 已定位
HTML path: output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.html
Markdown path: output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.md
JSON path: output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.json

中文摘要: ...
最大机会: ...
最大风险: ...
最大证据缺口: ...
数据质量状态: ...
重要声明: 本报告仅用于基本面研究讨论，不构成买卖建议，不包含目标价、仓位或技术面交易信号。
```

Allowed status values should be small and operational:

- `已定位`: accepted local artifacts were found and returned.
- `已生成`: missing presentation artifacts were generated offline from accepted
  local upstream artifacts.
- `未生成_missing_local_artifacts`: required local artifacts were missing.
- `失败_invalid_request`: target stock was not provided or request parameters
  were invalid.
- `失败_safety_boundary`: a forbidden network, token, provider, MCP, fixture,
  scoring, P1.1, regression, or trading-advice path was requested or detected.

Path fields should be printed even when some paths are unavailable; unavailable
paths should be explicit, for example `未生成` or `缺失`, instead of omitted.

Accepted manifest/freshness output behavior:

- The CLI prefers `output/research_reports/accepted_manifest.json` for
  accepted artifact selection.
- The CLI displays manifest status, freshness status, freshness warnings,
  `accepted_at`, `valuation_as_of_date`, and `source_data_period` when
  available.
- `freshness_status=current` can be returned without a freshness warning.
- `freshness_status=unknown` or `stale` must be returned with a visible warning.
- `freshness_status=superseded` or `invalidated` must not be returned as the
  accepted baseline.
- Missing manifest can fall back to timestamp lookup only with
  `manifest_missing_warning`.
- A missing manifest artifact path or hash mismatch must fail closed.
- CLI must not network-check freshness, read tokens, call providers, connect
  MCP, or auto-upgrade to live provider mode.

Runtime acceptance confirmed that `600406`, `002371`, and `002050` all return
exit code `0`, `Manifest 状态：used`, and `Freshness 状态：current` from the
retained ignored manifest. No `manifest_missing_warning`, timestamp fallback
warning, English JSON summary leak, full body dump, profile cross-contamination,
or positive trading advice was observed.

## 6. Error Behavior

The CLI must fail closed.

Required error behavior:

- If neither `--code` nor `--company-name` is provided, stop with
  `失败_invalid_request`.
- If required local artifacts are missing, return
  `未生成_missing_local_artifacts` plus a missing checklist.
- Do not automatically use the network to resolve a company name or find data.
- Do not actively suggest live provider access when local artifacts are
  missing.
- Do not read `TUSHARE_TOKEN` or any provider token.
- Do not call Tushare, AkShare, or any other provider.
- Do not connect MCP or read local MCP config.
- Do not generate a free-written model report outside the accepted artifact
  chain.
- Do not hide freshness status when the future accepted manifest reports
  `unknown`, `stale`, `superseded`, or `invalidated`.
- Do not regenerate automatically only because an accepted artifact is stale.

Missing checklist should name local requirements, such as:

- local Research Report V1 JSON artifact;
- local Markdown presentation artifact;
- local HTML presentation artifact;
- `fact_candidates.json`;
- `candidate_review_decisions.json`;
- local provider comparison artifact root for the stock, when
  `local_provider_comparison` is explicitly selected;
- provider-separated local fundamentals / evidence packs, when required by the
  selected offline path.

Suggested exit-code design:

- `0`: success, report located or generated.
- `2`: invalid request, such as missing `--code` and `--company-name`.
- `3`: missing local artifacts.
- `4`: safety boundary violation.
- `5`: unsupported mode or unsupported argument combination.
- Future `6`: accepted manifest integrity failure, such as missing manifest
  target file or hash mismatch.

## 7. Safety / Non-Goals

The CLI must not:

- read `TUSHARE_TOKEN`;
- use the network;
- call Tushare;
- call AkShare;
- call any provider runtime;
- connect MCP;
- read local MCP config;
- write fixtures;
- change scoring;
- change Research Intelligence P1.1;
- change regression expected files;
- submit runtime output;
- output buy / sell recommendations;
- output target prices;
- output position sizing, portfolio weights, or account actions;
- output technical trading signals;
- hide data-quality caveats;
- upgrade missing, candidate, or disputed evidence into verified facts.

Explicit negative boundary language is allowed. For example, the CLI may say
the report is not trading advice and contains no target price or position
sizing. It must not translate that disclaimer into positive investment-action
language.

## 8. Implementation Boundary

The accepted implementation exposes one command module:

```text
src/fundamental_skill/research_report/generate_report.py
```

The command module should be thin. Internally it should only call the accepted
orchestration surface:

- `normalize_report_request`
- `run_single_stock_report_orchestration`
- `format_orchestration_response`

Implementation boundaries:

- Do not import the old runner as the CLI entry path.
- Do not import provider runtime modules.
- Do not call `real_stock_runner`, `ai_analyst.runner`, `html_report_runner`,
  `scripts/generate_fundamental_html_report.py`, early AkShare HTML report
  scripts, or Tushare transport modules from the CLI.
- Legacy entry points may be used only as historical implementation references;
  they must not become the user-facing CLI path.
- Do not duplicate report-building logic in the CLI.
- Do not bypass the accepted Research Report V1 JSON -> Markdown -> HTML
  artifact chain.
- Keep request parsing, default safety flags, and response formatting small and
  explicit.
- Keep `offline_local_artifacts` as the default and keep
  `local_provider_comparison` local-artifact-only.

Accepted implementation-stage test and review coverage included:

- no environment token read;
- no network access;
- no provider import or provider call;
- no MCP connection or MCP config read;
- missing target fails closed;
- missing local artifacts returns a checklist;
- default invocation uses `offline_local_artifacts`, `no_live_provider`, and
  `provider_transport=none`;
- `--format html` still reports HTML / Markdown / JSON paths when available;
- forbidden output checks reject buy / sell advice, target price, position
  sizing, and technical trading signals.

The current CLI runtime acceptance summary quotes the latest accepted results;
this documentation sync does not add or modify tests.

## 9. Relation To Existing Orchestration

The CLI should be the stable command wrapper around the accepted single-stock
offline orchestration. The ownership split is:

- CLI: parse command arguments, enforce defaults, call orchestration, print a
  concise Chinese result.
- Orchestration: normalize the report request, locate or generate accepted local
  artifacts, enforce evidence boundaries, and prepare the response payload.
- Research Report V1 builders / renderers: produce JSON, Markdown, and HTML
  artifacts from accepted local inputs.

The CLI must not become a hidden second implementation of:

- candidate fact generation;
- review decision handling;
- Research Report V1 JSON construction;
- Markdown rendering;
- HTML rendering;
- provider comparison;
- evidence scoring;
- report summarization beyond `format_orchestration_response`.

## 10. Accepted CLI Implementation Criteria

The CLI implementation acceptance criteria are:

- Codex can run one stable command to locate or generate a single-stock report.
- The command supports `--code` and `--company-name` entry paths.
- Defaults remain offline local artifacts, no live provider, no provider
  transport, no network, no token read, strict evidence boundary, and
  not-for-trading-advice.
- CLI output includes status, HTML path, Markdown path, JSON path, Chinese
  summary, maximum opportunity, maximum risk, maximum evidence gap, data-quality
  status, and important statement.
- CLI output exposes manifest status, freshness status, freshness warning,
  `accepted_at`, `valuation_as_of_date`, and `source_data_period` when the
  accepted manifest provides them.
- Missing target and missing local artifacts fail closed.
- No provider, network, token, MCP, fixture, scoring, P1.1, regression, or
  runtime-output submission side effect is introduced.
- No buy / sell advice, target price, position sizing, portfolio weight,
  account action, or technical trading signal is emitted.

## 11. CLI Runtime Acceptance Sync

The CLI command wrapper has now passed three-sample runtime acceptance. The
accepted runtime closeout is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`.

Accepted commands:

```bash
python -m src.fundamental_skill.research_report.generate_report --code 600406 --format html --data-mode offline_local_artifacts
python -m src.fundamental_skill.research_report.generate_report --company-name 北方华创 --format html
python -m src.fundamental_skill.research_report.generate_report --company-name 三花智控 --format html
```

Acceptance result:

- CLI implementation accepted.
- `600406`, `002371`, and `002050` CLI runtime accepted.
- Manifest-first locator hardening accepted.
- Retained runtime manifest review accepted.
- Manifest locator runtime baseline frozen.
- Exit code `0` for all three accepted CLI runtime runs.
- Stdout Chinese and operational.
- Selected HTML / Markdown / JSON artifacts correct.
- All retained-manifest CLI runs showed `Manifest 状态：used`.
- All retained-manifest CLI runs showed `Freshness 状态：current`.
- No `manifest_missing_warning`.
- No timestamp fallback warning.
- No English JSON summary leaked.
- No full report body dumped.
- No cross-profile contamination.
- Artifact boundary passed.
- Token / secret / provider scan passed.
- Forbidden output check passed.
- Latest quoted verification: targeted tests with retained manifest
  `251 passed`, full pytest with retained manifest `899 passed, 1 skipped`,
  and regression `passed=47 failed=0 total=47`.

## 12. Next Recommended Step

After manifest locator runtime acceptance, the next recommended sequence is:

1. Submit the manifest locator runtime acceptance summary documentation patch.
2. Enter Minimal CNInfo / official disclosure parser design, or A-share
   specific risk framework design.
3. Start batch / Dashboard design after manifest closeout, and make it depend
   on manifest-located artifacts.
4. Keep live provider, Tushare token, MCP, validator, fixture promotion,
   primary-provider switch, and live smoke work for later separately accepted
   stages.

The operational usage guide for Codex and developers is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_USAGE_GUIDE.md`. It should be the first reference
for the accepted commands, Codex invocation behavior, parameters, stdout
fields, error handling, and safety guardrails.
