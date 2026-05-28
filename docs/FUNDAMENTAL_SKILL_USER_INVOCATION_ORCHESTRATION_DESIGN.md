# Fundamental Skill User Invocation / Report Orchestration Design

Date: 2026-05-28

Stage: Fundamental Skill User Invocation / Report Orchestration Design and
Three-Sample Offline Orchestration Acceptance Sync.

Status: design accepted, single-stock offline orchestration implementation
accepted, Chinese summary patch accepted, three-sample offline runtime
acceptance complete, CLI / command wrapper implementation accepted, three-sample
CLI runtime acceptance complete, and single-stock offline CLI baseline frozen.
The orchestration acceptance closeout is recorded in
`docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`, the CLI
design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`, and the CLI runtime
acceptance closeout is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`. This documentation
sync does not change tests, change fixtures, change pipeline behavior, change
scoring / readiness, change Research Intelligence P1.1, change regression
expected files, generate output, run smoke tests, read `TUSHARE_TOKEN`, use the
network, call Tushare or AkShare, connect MCP, or produce trading advice.
Accepted artifact manifest / freshness design is recorded in
`docs/FUNDAMENTAL_ACCEPTED_ARTIFACT_MANIFEST_FRESHNESS_DESIGN.md`; it is a
future locator hardening design only and does not change the current runtime.

Current accepted upstream state:

- Research Report V1 JSON builder accepted.
- Markdown presentation accepted.
- Presentation profiles accepted.
- Professional analyst voice gate accepted.
- HTML renderer accepted.
- `600406`, `002371`, and `002050` HTML reports accepted.
- HTML presentation baseline frozen.
- HTML is a display layer: it must not re-analyze, change conclusions, or hide
  caveats.
- Single-stock offline orchestration implementation accepted.
- Chinese summary patch accepted.
- `600406`, `002371`, and `002050` one-sentence offline runtime invocations
  accepted.
- One-sentence local report invocation baseline frozen.
- User invocation CLI / command wrapper design recorded.
- CLI implementation accepted.
- `600406`, `002371`, and `002050` CLI runtime accepted.
- Single-stock offline CLI baseline frozen.
- CLI runtime acceptance summary recorded.
- Older `002371` Markdown / HTML runtime artifacts were superseded by the
  `20260528T125518` professional-voice regenerated artifacts; user-facing
  orchestration baseline should use the `20260528T125518` Markdown / HTML
  artifacts.
- Accepted manifest / freshness design is recorded. Future orchestration should
  prefer the manifest over timestamp-latest artifact selection and surface
  freshness warnings, while remaining offline and local-only.

## 1. Product Goal

The final product experience should let an end user ask Codex / GPT-5.5 for a
fundamental research report in ordinary Chinese, for example: "帮我生成 600406
国电南瑞的基本面投研报告。"

The user should not need to know the internal artifact chain. In particular,
the user should not need to understand or manually locate
`fact_candidates.json`, `candidate_review_decisions.json`,
`fundamental_research_report_v1.json`, Markdown, HTML, provider comparison
artifacts, evidence packs, or review queues.

The user also should not need to manually find data, run multiple builders, or
choose between JSON / Markdown / HTML generation steps. The skill should:

- parse the user request;
- resolve the stock code, company name, or stock pool;
- read approved local artifacts under the selected data mode;
- assess data quality and evidence sufficiency;
- run or locate the deterministic Research Report V1 artifact chain;
- render Markdown and HTML presentation outputs when requested;
- preserve data caveats and evidence labels;
- return a readable HTML report plus a short Chinese summary.

The default user-facing output should be:

- HTML report path;
- Markdown path when available or generated;
- JSON path when available or generated;
- short Chinese summary;
- data-quality caveat;
- explicit statement that the report is not trading advice.

The skill must not output buy / sell recommendations, target prices, position
sizing, portfolio weights, account actions, or technical trading signals.

## 2. User Invocation Examples

Natural-language prompts are converted into a structured request before any
artifact work begins. Examples:

| User prompt | Parsed intent | Structured request sketch |
| --- | --- | --- |
| "帮我生成 600406 国电南瑞的基本面投研报告。" | Single-stock Research Report V1, default HTML output, offline local artifacts. | `code=600406`, `company_name=国电南瑞`, `report_type=fundamental_research_report_v1`, `output_format=html`, `data_mode=offline_local_artifacts`, `allow_network=false`, `allow_token_read=false` |
| "分析一下北方华创的基本面，输出 HTML 报告。" | Resolve company name to stock code, generate or locate HTML report. | `code=002371`, `company_name=北方华创`, `output_format=html`, `data_mode=offline_local_artifacts` unless user explicitly authorizes another mode |
| "用当前本地数据给我生成三花智控的研究报告。" | Use local-only data, no live provider, produce the default HTML report. | `code=002050`, `company_name=三花智控`, `output_format=html`, `data_mode=offline_local_artifacts`, `provider_mode=no_live_provider` |
| "对这个股票池生成基本面报告，先不要联网。" | Batch-style request over a provided stock pool, but each stock uses the same single-stock orchestration pipeline. | `stock_pool=[...]`, `output_format=html`, `data_mode=offline_local_artifacts`, `allow_network=false` |
| "只用本地 artifacts，不要调用实时接口，帮我生成 600406 国电南瑞的基本面投研报告。" | Explicit offline single-stock Research Report V1 request, no live providers. | `code=600406`, `company_name=国电南瑞`, `output_format=html`, `data_mode=offline_local_artifacts`, `provider_mode=no_live_provider`, `allow_network=false`, `allow_token_read=false` |

Resolution notes:

- If both code and company name are present, code is primary and company name is
  used as a consistency hint.
- If only company name is present, the orchestration layer may resolve it from
  local metadata, accepted artifacts, or a local alias table. It must not use
  the network in offline modes.
- If a stock pool is provided, orchestration creates one normalized request per
  stock and later aggregates status, paths, summaries, and missing-artifact
  diagnostics.
- Requests mentioning "当前本地数据", "本地 artifacts", "不要联网", or "不要调用实时接口"
  force `allow_network=false`, `allow_token_read=false`, and
  `provider_mode=no_live_provider`.
- If a user only says "只用本地 artifacts，不要调用实时接口" without a selected
  stock or stock pool, treat it as a context modifier. If no prior
  `code`, `company_name`, or `stock_pool` exists, orchestration must stop and
  ask the user to provide the target; it must not guess a stock, use the
  network to resolve one, or call a provider.

## 3. Request Schema

The user request should be normalized into a stable schema before orchestration
begins.

Example single-stock request:

```json
{
  "code": "600406",
  "company_name": "国电南瑞",
  "stock_pool": null,
  "report_type": "fundamental_research_report_v1",
  "output_format": "html",
  "data_mode": "offline_local_artifacts",
  "provider_mode": "no_live_provider",
  "provider_transport": "none",
  "allow_network": false,
  "allow_token_read": false,
  "reasoning_level": "high",
  "not_for_trading_advice": true,
  "requested_sections": [],
  "language": "zh-CN",
  "strict_evidence_boundary": true
}
```

Recommended fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `code` | string or null | A-share stock code for a single-stock request. |
| `company_name` | string or null | User-provided or locally resolved company name. |
| `stock_pool` | array or null | Optional list of `{code, company_name}` items for batch-style requests. |
| `report_type` | enum | Default `fundamental_research_report_v1`. |
| `output_format` | enum | `json`, `markdown`, `html`, or `all`; default `html`. |
| `data_mode` | enum | `offline_local_artifacts`, `local_provider_comparison`, or future `future_live_provider`. |
| `provider_mode` | enum | `no_live_provider` in current V1 user invocation. |
| `allow_network` | boolean | Must default to `false`; only future explicit live-provider mode may set it true. |
| `allow_token_read` | boolean | Must default to `false`; only future explicit live-provider mode may set it true. |
| `provider_transport` | enum | `none` for offline modes; future values may include `sdk` only behind explicit gates. |
| `reasoning_level` | enum | `high` for planning, audit, and report-quality review. |
| `not_for_trading_advice` | boolean | Must be `true` for all Research Report V1 user-facing outputs. |
| `requested_sections` | array | Optional list of sections to emphasize or include. |
| `language` | string | Default `zh-CN` for Chinese reports and summaries. |
| `strict_evidence_boundary` | boolean | Must be `true`; candidate evidence cannot be upgraded by wording. |

Schema invariants:

- At least one of `code`, `company_name`, or `stock_pool` is required. If all
  three are missing, orchestration must stop and ask the user for the target
  security or pool instead of generating a report.
- `allow_network=false` and `allow_token_read=false` are the current V1
  defaults.
- `provider_transport=none` is required when `provider_mode=no_live_provider`.
- `not_for_trading_advice=true` is required for all report outputs.
- `strict_evidence_boundary=true` is required whenever Research Report V1 is
  generated, rendered, summarized, or returned.
- `output_format=html` should still retain JSON and Markdown paths in the final
  response if those artifacts exist or are generated as intermediate outputs.

## 4. Orchestration Pipeline

The single-stock orchestration pipeline is:

1. Parse user request.
2. Resolve stock code and company name from user text and local metadata.
3. Normalize request schema and enforce default safety flags.
4. Locate accepted local artifacts for the stock and selected data mode. Future
   locator hardening should read the accepted artifact manifest first and use
   timestamp-latest lookup only as a warned fallback.
5. If an artifact is missing, decide whether offline regeneration is possible.
6. Generate or locate `fact_candidates.json`.
7. Generate or locate `candidate_review_decisions.json`.
8. Generate or locate `fundamental_research_report_v1.json`.
9. Generate or locate Markdown presentation output.
10. Generate or locate HTML presentation output.
11. Run artifact-boundary, secret-scan, external-resource, caveat-visibility,
    evidence-label, and forbidden-output checks.
12. Return the final user response.

The final response should include:

- HTML path;
- Markdown path;
- JSON path;
- short Chinese summary;
- data-quality caveat;
- future freshness status / warning when the accepted manifest provides it;
- not-for-trading-advice statement;
- if applicable, missing-artifact diagnostics and the next data items needed.

Pipeline boundary rules:

- The orchestration layer chooses which deterministic builders to run or which
  existing artifacts to reuse. It does not invent report content.
- The Research Report V1 JSON builder remains the analysis source of record.
- Markdown and HTML are presentation outputs; they must not re-analyze or alter
  conclusions.
- If no valid evidence chain exists, orchestration stops and returns a missing
  data list instead of free-writing a report.
- The model may summarize accepted report outputs for the chat response, but it
  must not create new unsupported conclusions outside the artifact chain.

## 5. Data Mode Rules

### `offline_local_artifacts`

This is the current V1 default mode.

Rules:

- Read only existing local artifacts.
- Do not use the network.
- Do not read `TUSHARE_TOKEN`.
- Do not call Tushare, AkShare, or any other live provider.
- Do not connect MCP.
- Do not read local MCP config.
- Reuse existing Research Report V1, Markdown, or HTML artifacts when present.
- Future locator behavior should prefer
  `output/research_reports/accepted_manifest.json` when present. Missing
  manifest can fall back to local timestamp lookup only with a
  `manifest_missing_warning`.
- If offline regeneration is possible from already available local artifacts,
  run only the accepted local deterministic builders.
- If required upstream local artifacts are missing, stop and report the missing
  list.

### `local_provider_comparison`

This mode allows local provider comparison artifacts as inputs, but still does
not call live providers.

Rules:

- May read local artifacts under accepted provider comparison output roots.
- May use local `diff_report.json`, `diff_report.md`,
  `score_confidence_explainability.json`, provider-separated fundamentals,
  provider-separated evidence packs, `fact_candidates.json`, and
  `candidate_review_decisions.json` if present.
- If candidates, review decisions, JSON report, Markdown, or HTML are missing,
  orchestration may rebuild them offline from local artifacts only.
- Must not call live providers.
- Must not read tokens.
- Must not auto-merge AkShare / Tushare data.
- Must not auto-accept score drift, confidence drift, or provider conflicts.

### `future_live_provider`

This is a future mode and is not implemented in the current stage.

Rules for any future design:

- Requires explicit user authorization for live provider access.
- Requires explicit authorization before reading `TUSHARE_TOKEN`.
- Requires an accepted provider transport, most likely gated `sdk`.
- Must pass smoke gate, token scanner, provider-boundary checks, artifact
  boundary checks, and no-secret persistence checks.
- Must fail closed when token, transport, or provider boundary checks fail.
- Must not become the default mode.
- Must not automatically switch Tushare to primary.
- Must not automatically merge AkShare and Tushare data.
- Must not promote fixtures or regression expected files as a side effect.

## 6. Missing Artifact Behavior

The orchestration layer should resolve the shortest safe path to a user-visible
report.

Before artifact lookup, request validation must confirm that at least one of
`code`, `company_name`, or `stock_pool` is present. If the target is missing,
orchestration stops and asks the user to provide it; it must not free-write a
report, guess a stock, use the network, call a provider, read a token, or
connect MCP.

If HTML exists:

- Return the HTML path directly.
- Locate and return Markdown and JSON paths when available.
- Produce a short Chinese summary from the accepted report artifacts.
- Preserve the data-quality caveat and not-for-trading-advice statement.

If HTML is missing but Markdown exists:

- Generate HTML from Markdown.
- Use JSON only for display metadata, evidence labels, source references, and
  data-quality caveats when available.
- Run boundary and secret checks before returning the HTML path.

If Markdown is missing but JSON exists:

- Generate Markdown from `fundamental_research_report_v1.json`.
- Generate HTML from Markdown.
- Run boundary and content checks.

If JSON is missing but provider comparison artifacts exist:

- Generate or locate `fact_candidates.json`.
- Generate or locate `candidate_review_decisions.json`.
- Generate `fundamental_research_report_v1.json`.
- Generate Markdown.
- Generate HTML.
- Run boundary and content checks.

If provider comparison artifacts are also missing:

- Stop.
- Do not use the network.
- Do not call providers.
- Do not read `TUSHARE_TOKEN`.
- Do not connect MCP.
- Return a concise missing-data checklist, such as:
  - local provider comparison artifact root for the stock;
  - provider-separated fundamental artifacts;
  - provider-separated evidence packs;
  - `fact_candidates.json`;
  - `candidate_review_decisions.json`;
  - or a previously accepted Research Report V1 JSON artifact.

No fallback may ask the model to freely write a final report without the
accepted evidence chain.

## 7. Codex / GPT-5.5 Role Split

Codex is the user entry point and local tool executor. It receives the user's
natural-language request, normalizes it into the request schema, locates local
artifacts, invokes accepted local builders when allowed, runs checks, and
returns the final paths and summary.

GPT-5.5 with high reasoning is used for:

- planning the orchestration route;
- interpreting user intent;
- auditing whether the evidence boundary has been preserved;
- checking whether caveats, evidence gaps, and not-for-trading-advice language
  remain visible;
- reviewing professional analyst voice and summary quality.

The fundamental skill code is responsible for deterministic artifact
generation:

- candidate fact generation;
- review decision artifact generation;
- Research Report V1 JSON generation;
- Markdown rendering;
- HTML rendering;
- boundary and safety scans.

The model must not:

- bypass the skill and freely generate the final report;
- bypass the evidence boundary;
- write candidate facts as verified facts;
- treat review decisions as fixture promotion;
- hide caveats or unsupported assumptions;
- rewrite Markdown or HTML conclusions outside the accepted artifact chain;
- convert valuation fields into target prices or trading action language;
- produce technical trading signals.

## 8. Output Response Design

Codex's final chat response should be short and operational. It should confirm
that the report has been generated or located, then provide paths and a concise
Chinese summary. It should not copy the full report body into chat unless the
user explicitly asks for it.

Required response fields:

- report status;
- HTML path;
- Markdown path;
- JSON path;
- short Chinese summary;
- largest opportunity;
- largest risk;
- largest evidence gap;
- data-quality status;
- important statement: not trading advice, no target price, no position sizing.

Recommended response shape:

```text
已生成/已找到 600406 国电南瑞的基本面投研报告。

HTML: output/research_reports/<timestamp>/600406/fundamental_research_report_v1.html
Markdown: output/research_reports/<timestamp>/600406/fundamental_research_report_v1.md
JSON: output/research_reports/<timestamp>/600406/fundamental_research_report_v1.json

简短摘要：...
最大机会：...
最大风险：...
最大证据缺口：...
数据质量：...

重要声明：本报告仅用于基本面研究讨论，不构成买卖建议，
不包含目标价、仓位或技术面交易信号。
```

If generation stops because artifacts are missing, the response should say that
the report was not generated and list the missing local artifacts. It should
not suggest live-provider access unless the user explicitly asks for it.

## 9. CLI / Command Design And Runtime Acceptance

The detailed CLI / command wrapper design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`.

The stable accepted command target is:

```bash
python -m src.fundamental_skill.research_report.generate_report --code 600406 --format html --data-mode offline_local_artifacts
```

Company-name invocation is supported through the same command:

```bash
python -m src.fundamental_skill.research_report.generate_report --company-name 北方华创 --format html
```

The CLI goal is to let Codex trigger the accepted orchestration with one stable
command. It should call `normalize_report_request`,
`run_single_stock_report_orchestration`, and `format_orchestration_response`;
it should not reimplement report logic, import old runners, import provider
runtime modules, call providers, read tokens, connect MCP, or create a second
reporting pipeline.

Current V1 CLI defaults remain:

- `--format html`;
- `--data-mode offline_local_artifacts`;
- `--provider-mode no_live_provider`;
- `--provider-transport none`;
- `--no-network true`;
- `--no-token-read true`;
- `--strict-evidence-boundary true`;
- `--not-for-trading-advice true`.

The CLI implementation and `600406` / `002371` / `002050` CLI runtime runs are
accepted. The runtime closeout is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`. This orchestration
document records the relationship; the CLI document remains the source of truth
for command arguments, output behavior, error behavior, safety boundaries, and
implementation acceptance criteria.

## 10. Legacy Entry Point Reuse Boundary

Earlier entry points such as `real_stock_runner`, `ai_analyst.runner`,
`html_report_runner`, `scripts/generate_fundamental_html_report.py`, and the
early AkShare HTML report scripts may be used as implementation references only.
They must not be reused unchanged as the final one-sentence user invocation
path.

Any future reuse must be adapted to the current Research Report V1 artifact
chain:

- `fact_candidates.json`;
- `candidate_review_decisions.json`;
- `fundamental_research_report_v1.json`;
- Markdown presentation;
- HTML presentation;
- secret scan;
- forbidden-output checks;
- evidence boundary;
- `not_for_trading_advice`.

## 11. Safety / Non-Goals

This documentation sync and the accepted V1 orchestration runtime must not:

- read `TUSHARE_TOKEN`;
- use the network;
- call Tushare;
- call AkShare;
- connect MCP;
- read local MCP config;
- output buy / sell recommendations;
- output target prices;
- output position sizing, portfolio weights, or account actions;
- output technical trading signals;
- bypass evidence labels;
- write candidate facts as verified facts;
- hide data-quality caveats;
- submit runtime artifacts;
- write fixtures;
- promote validator fixtures;
- change regression expected files;
- change scoring / readiness;
- change Research Intelligence P1.1;
- automatically switch Tushare to primary;
- automatically merge AkShare and Tushare data;
- automatically accept provider drift;
- implement official parser / CNInfo ingestion;
- implement future live-provider mode;
- run real smoke tests.

Negative disclaimer wording such as "not trading advice", "no target price",
or "no position sizing" is allowed as boundary clarification. Positive
investment-action language remains prohibited.

## 12. Relation To Accepted Manifest / Freshness

Accepted artifact manifest / freshness design is now recorded in
`docs/FUNDAMENTAL_ACCEPTED_ARTIFACT_MANIFEST_FRESHNESS_DESIGN.md`.

Future orchestration behavior:

- Prefer accepted manifest entries over timestamp-latest artifact discovery.
- Treat the manifest as the user-facing accepted artifact selector for HTML,
  Markdown, and JSON.
- Surface `freshness_status`, `freshness_warning`, `accepted_at`,
  `valuation_as_of_date`, and `source_data_period` when available.
- Allow `current` artifacts by default.
- Allow `unknown` and `stale` artifacts only with visible warnings in V1.
- Do not use `superseded` or `invalidated` artifacts as accepted baselines.
- Fail closed if a manifest path is missing or an artifact hash mismatches.
- Keep the behavior offline: no provider call, no network, no token read, and
  no MCP.

The manifest is not a fixture, not a validator, not CNInfo ingestion, not
evidence-tier promotion, and not report conclusion rewriting. It records which
runtime artifacts have been accepted and whether they are fresh enough to be
returned without a warning.

## 13. Relation To Dashboard / Batch

User invocation / orchestration is the single-stock closed loop:

```text
natural language request
  -> structured request
  -> local artifact chain
  -> JSON
  -> Markdown
  -> HTML
  -> short chat summary and paths
```

Dashboard / batch is the multi-stock aggregation and inspection layer. It
should not replace the single-stock report generation path.

Design relationship:

- The single-stock user invocation / orchestration design and offline runtime
  implementation are accepted.
- The single-stock CLI / command wrapper design is recorded and should be
  implemented and accepted before batch.
- Let batch reuse the same single-stock orchestration pipeline for each stock,
  with manifest-first accepted artifact lookup.
- Let Dashboard read manifest-located outputs and show status, freshness,
  summaries, caveats, evidence gaps, and artifact links.
- Dashboard may sort or filter by `freshness_status` and
  `research_completeness`, but must not rank by target price, implied upside, or
  buy / sell action.
- Dashboard may provide a reader / audit view, but it should not become the
  report generator's hidden source of truth.
- Batch status should distinguish generated, reused, skipped, and missing-data
  cases per stock.

The first batch design should avoid new analysis logic. It should be a
composition layer over the same request schema, data-mode rules, safety gates,
and missing-artifact behavior.

## 14. Roadmap

Completed sequence:

1. Complete this design document.
2. Implement single-stock offline user invocation / orchestration.
3. Accept the Chinese summary patch.
4. Use `600406` for an end-to-end local offline runtime acceptance.
5. Use `002371` for a cross-profile local offline runtime acceptance.
6. Use `002050` for a cross-profile local offline runtime acceptance.
7. Freeze the one-sentence local report invocation baseline.
8. Record the acceptance closeout in
   `docs/FUNDAMENTAL_SKILL_OFFLINE_ORCHESTRATION_ACCEPTANCE_SUMMARY.md`.
9. Record the user invocation CLI / command wrapper design in
   `docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`.
10. Implement the CLI / command wrapper.
11. Accept `600406`, `002371`, and `002050` CLI runtime runs.
12. Freeze the single-stock offline CLI baseline.
13. Record the CLI runtime acceptance closeout in
    `docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`.
14. Record accepted artifact manifest / freshness design in
    `docs/FUNDAMENTAL_ACCEPTED_ARTIFACT_MANIFEST_FRESHNESS_DESIGN.md`.

Accepted implementation criteria:

- A user can ask for a report in natural language.
- Codex normalizes the request into the schema above.
- The default path uses only local artifacts.
- The user does not manually run multiple builders.
- The system returns HTML, Markdown, and JSON paths.
- The final response includes a short Chinese summary, maximum opportunity,
  maximum risk, maximum evidence gap, data-quality caveat, and
  not-for-trading-advice statement.
- Missing artifacts stop the run with a clear local data checklist.
- No token is read, no network is used, no provider is called, and no MCP is
  connected in the default V1 path.
- No buy / sell advice, target price, position sizing, portfolio weight,
  account action, or technical trading signal is emitted.

Next recommended sequence:

1. Commit the accepted artifact manifest / freshness documentation patch.
2. Enter manifest schema / writer / reader implementation.
3. Harden orchestration and CLI locators to read the accepted manifest first.
4. Generate ignored runtime manifests for `600406`, `002371`, and `002050`,
   then run a separately accepted manifest locator runtime stage.
5. Keep future live provider mode, Tushare token, MCP, CNInfo, official parser,
   validator, fixture promotion, Tushare primary, batch, and Dashboard for
   later separately accepted stages.
