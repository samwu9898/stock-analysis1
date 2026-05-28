# Fundamental Skill CLI Runtime Acceptance Summary

Date: 2026-05-28

Stage: Fundamental Skill CLI Runtime Acceptance Summary.

Status: documentation-only runtime acceptance closeout. This summary records
that the single-stock offline CLI / command wrapper implementation, the
three accepted CLI runtime samples, and the retained manifest-first runtime
locator baseline have passed acceptance. It freezes the single-stock offline
CLI baseline and the manifest locator runtime baseline. This stage does not modify code, tests,
fixtures, pipeline behavior, scoring / readiness, Research Intelligence P1.1,
regression expected files, provider-primary behavior, or runtime artifacts. It
does not run smoke tests, read `TUSHARE_TOKEN`, use the network, call Tushare
or AkShare, connect MCP, generate output, stage output, or provide investment
advice.
Accepted artifact manifest / freshness design is recorded in
`docs/FUNDAMENTAL_ACCEPTED_ARTIFACT_MANIFEST_FRESHNESS_DESIGN.md`; this summary
now links the accepted manifest locator runtime closeout in
`docs/FUNDAMENTAL_ACCEPTED_MANIFEST_LOCATOR_RUNTIME_ACCEPTANCE_SUMMARY.md`.

Latest verification results are quoted from the accepted stage input and were
not rerun in this documentation-only stage:

- targeted tests with retained manifest `251 passed`
- full pytest with retained manifest `899 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

## 1. Final status

- CLI implementation accepted.
- `600406` CLI runtime accepted.
- `002371` CLI runtime accepted.
- `002050` CLI runtime accepted.
- Single-stock offline CLI baseline frozen.
- Accepted manifest module accepted.
- Manifest-first locator hardening accepted.
- Retained runtime manifest review accepted.
- Manifest locator runtime baseline frozen.
- Default CLI mode remains offline local artifacts / no live provider / no
  token / no network / no MCP.

## 2. Accepted CLI runtime table

| code | company | command | selected HTML artifact | selected Markdown artifact | selected JSON artifact | exit code | stdout status | acceptance result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | `python -m src.fundamental_skill.research_report.generate_report --code 600406 --format html --data-mode offline_local_artifacts` | `output/research_reports/20260528T012952/600406/fundamental_research_report_v1.html` | `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md` | `output/research_reports/20260527T103241/600406/fundamental_research_report_v1.json` | `0` | Chinese operational success; accepted local artifacts located and returned. | Accepted. |
| `002371` | 北方华创 | `python -m src.fundamental_skill.research_report.generate_report --company-name 北方华创 --format html` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.html` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.md` | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.json` | `0` | Chinese operational success; accepted local artifacts located and returned. | Accepted. |
| `002050` | 三花智控 | `python -m src.fundamental_skill.research_report.generate_report --company-name 三花智控 --format html` | `output/research_reports/20260528T091133/002050/fundamental_research_report_v1.html` | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` | `output/research_reports/20260527T222558/002050/fundamental_research_report_v1.json` | `0` | Chinese operational success; accepted local artifacts located and returned. | Accepted. |

## 3. Validated CLI flow

The three accepted CLI runtime samples validated the same local-only command
wrapper flow:

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

The accepted CLI remains a thin command wrapper over the already accepted
single-stock offline orchestration. It is not a live data path and not a
free-written model report path.

## 4. Acceptance summary

- Exit code `0` for all three accepted CLI runtime runs.
- Stdout Chinese and operational.
- Selected artifacts correct.
- Manifest status `used` for all three retained-manifest runs.
- Freshness status `current` for all three retained-manifest runs.
- No `manifest_missing_warning`.
- No timestamp fallback warning.
- No English JSON summary leaked.
- No full report body dumped.
- No cross-profile contamination.
- Artifact boundary passed.
- Token / secret / provider scan passed.
- Forbidden output check passed.
- Targeted tests with retained manifest `251 passed`.
- Full pytest with retained manifest `899 passed, 1 skipped`.
- Regression `passed=47 failed=0 total=47`.

## 5. Safety / guardrails

- CLI is a thin wrapper over accepted orchestration.
- No token read.
- No network.
- No provider call.
- No MCP.
- No live provider.
- No old runner reuse.
- No free-written report.
- No fixture write.
- No scoring / P1.1 change.
- No regression expected change.
- No runtime artifact committed.
- No buy / sell / target price / position sizing / trading signal.

## 6. Known limitations

- Current CLI supports only the single-stock offline local artifact path.
- Batch / dashboard is not implemented.
- Live provider mode is not implemented.
- Tushare token / MCP / CNInfo / official parser remain later work.
- Validator / fixture promotion / primary switch remain later work.
- Runtime artifacts remain under ignored `output/`.
- CLI is currently a command wrapper, not a full GUI / dashboard.
- Freshness is manually recorded / static in the manifest.
- Manifest currently covers only three accepted samples.
- Batch / dashboard is not implemented.
- CNInfo / official parser, L1 evidence tier, live Tushare, token, and MCP work
  remain later stages.

## 7. Next recommended stage

1. Submit the manifest locator runtime acceptance summary documentation patch.
2. Enter Minimal CNInfo / official disclosure parser design, or A-share
   specific risk framework design.
3. Start batch / dashboard design after manifest closeout, and make it depend
   on manifest-located artifacts.
4. Keep live provider / Tushare token / MCP / live smoke work later.

## 8. Safety confirmation

This documentation-only CLI runtime acceptance summary confirms:

- no token read;
- no network use;
- no provider call;
- no MCP connection;
- no output generated;
- no runtime artifact submitted;
- no investment advice output.
- accepted artifact manifest / freshness design only, with no implementation
  side effect.

## 9. Manifest locator runtime acceptance addendum

The retained ignored manifest
`output/research_reports/accepted_manifest.json` is the accepted source of
truth for current CLI artifact selection. It remains ignored, untracked, and
unstaged; `git ls-files output` remains empty. The recorded manifest SHA256 is
`C1F97162A59DE113CD4C9F1A9531AEC3A915A3D6F09365098201234E6F5BEB7F`, size is
`7678`, and mtime UTC is `2026-05-28 10:17:55`.

The accepted flow is now manifest-first:

```text
CLI / orchestration
  -> read accepted_manifest.json
  -> validate manifest
  -> verify artifact hashes
  -> locate accepted HTML / Markdown / JSON from manifest
  -> expose Manifest 状态
  -> expose Freshness 状态
  -> return Chinese summary and paths
  -> no timestamp fallback when manifest current
```
