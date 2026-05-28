# Fundamental Skill Offline Orchestration Acceptance Summary

Date: 2026-05-28

Stage: Fundamental Skill Single-Stock Offline Orchestration Three-Sample
Acceptance Summary.

Status: documentation-only acceptance closeout. This summary records that the
single-stock offline orchestration implementation, the Chinese summary patch,
and the three accepted local runtime samples have passed end-to-end acceptance
for one-sentence local report invocation. The follow-on CLI / command wrapper
design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_CLI_DESIGN.md`, and the CLI
implementation plus three-sample CLI runtime acceptance closeout is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`. It does not modify
code, tests, fixtures, pipeline behavior, scoring / readiness, Research
Intelligence P1.1, regression expected files, provider-primary behavior, or
runtime artifacts. It does not run smoke tests, read `TUSHARE_TOKEN`, use the
network, call Tushare or AkShare, connect MCP, generate output, stage output,
or provide investment advice.

Latest verification results are quoted from the accepted stage input and were
not rerun in this documentation-only stage:

- targeted tests `163 passed`
- full pytest `811 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

## 1. Final status

- Single-stock offline orchestration implementation accepted.
- Chinese summary patch accepted.
- `600406` runtime accepted.
- `002371` runtime accepted.
- `002050` runtime accepted.
- One-sentence local report invocation baseline frozen.
- CLI / command wrapper design recorded.
- CLI implementation accepted.
- `600406` CLI runtime accepted.
- `002371` CLI runtime accepted.
- `002050` CLI runtime accepted.
- Single-stock offline CLI baseline frozen.
- Older `002371` Markdown / HTML runtime artifacts were superseded by the
  `20260528T125518` professional-voice regenerated artifacts; user-facing
  orchestration baseline should use the `20260528T125518` Markdown / HTML
  artifacts.

## 2. Accepted runtime table

| code | company | user prompt | selected HTML artifact | selected Markdown artifact | selected JSON artifact | status | result summary source | acceptance result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | `帮我生成 600406 国电南瑞的基本面投研报告。` | `output/research_reports/20260528T012952/600406/fundamental_research_report_v1.html` | `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md` | `output/research_reports/20260527T103241/600406/fundamental_research_report_v1.json` | Runtime accepted | Accepted Markdown Chinese summary extraction | Accepted: one-sentence offline local report invocation returned HTML / Markdown / JSON paths, opportunity / risk / evidence gap / data-quality summary, and not-for-trading-advice statement. |
| `002371` | 北方华创 | `分析一下北方华创的基本面，输出 HTML 报告。` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.html` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.md` | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.json` | Runtime accepted | Accepted Markdown Chinese summary extraction | Accepted: one-sentence offline local report invocation returned HTML / Markdown / JSON paths, opportunity / risk / evidence gap / data-quality summary, and not-for-trading-advice statement. |
| `002050` | 三花智控 | `用当前本地数据给我生成三花智控的研究报告。` | `output/research_reports/20260528T091133/002050/fundamental_research_report_v1.html` | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` | `output/research_reports/20260527T222558/002050/fundamental_research_report_v1.json` | Runtime accepted | Accepted Markdown Chinese summary extraction | Accepted: one-sentence offline local report invocation returned HTML / Markdown / JSON paths, opportunity / risk / evidence gap / data-quality summary, and not-for-trading-advice statement. |

## 3. Validated flow

The three accepted runtime samples validated the same default V1 flow:

```text
user natural-language request
  -> normalize request
  -> safe offline flags
  -> locate local artifacts
  -> reuse accepted HTML
  -> extract Chinese summary from Markdown
  -> return HTML / Markdown / JSON paths
  -> return opportunity / risk / evidence gap / data quality
  -> not-for-trading-advice statement
```

The accepted baseline is a local orchestration path over already accepted
artifacts. It is not a live data path and not a free-written model report.

## 4. Safety / boundary

The accepted offline orchestration runtime boundary is:

- no token read;
- no network;
- no provider call;
- no MCP;
- no live provider;
- no old runner reuse;
- no free-written report;
- no fixture write;
- no scoring / P1.1 change;
- no regression expected change;
- no runtime artifact committed;
- no buy / sell / target price / position sizing / trading signal.

## 5. Known limitations

- Current CLI supports only the single-stock offline local artifact path.
- Batch / Dashboard has not been implemented for this path.
- Live provider mode has not been implemented.
- Tushare token / MCP / CNInfo / official parser remain later work.
- Validator, fixture promotion, and Tushare primary remain later work.
- Runtime artifacts remain under ignored `output/` paths and do not enter git.
- CLI is currently a command wrapper, not a full GUI / dashboard.
- `002371` and `002050` content thickness still depends on future evidence
  enrichment.

## 6. Next recommended stage

1. Commit the CLI runtime acceptance summary documentation patch.
2. Enter batch / Dashboard design, or first add CLI usage documentation.
3. Keep live provider, Tushare token, MCP, CNInfo, official parser, validator,
   fixture promotion, and primary-provider switch for later separately accepted
   stages.
4. Do not continue single-stock CLI runtime generation unless a new sample or a
   regression check requires it.

## 7. Safety confirmation

This documentation-only acceptance summary confirms:

- no token read;
- no network use;
- no provider call;
- no MCP connection;
- no output generated;
- no runtime artifact submitted;
- no investment advice output.

## 8. CLI runtime acceptance sync

The CLI implementation and `600406` / `002371` / `002050` CLI runtime runs are
accepted. The dedicated closeout is recorded in
`docs/FUNDAMENTAL_SKILL_CLI_RUNTIME_ACCEPTANCE_SUMMARY.md`.

The validated CLI flow is:

```text
Codex / user command
  -> CLI argument parsing
  -> accepted offline orchestration
  -> normalize request
  -> safe offline flags
  -> locate local artifacts
  -> reuse accepted HTML
  -> extract Chinese summary from Markdown
  -> stdout returns HTML / Markdown / JSON paths
  -> stdout returns opportunity / risk / evidence gap / data quality
  -> not-for-trading-advice statement
```
