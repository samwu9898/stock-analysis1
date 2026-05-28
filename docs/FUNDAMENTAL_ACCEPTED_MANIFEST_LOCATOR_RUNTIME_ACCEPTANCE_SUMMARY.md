# Fundamental Accepted Manifest Locator Runtime Acceptance Summary

Date: 2026-05-28

Stage: Fundamental Skill Manifest Locator Runtime Acceptance Summary.

Status: documentation-only closeout. Accepted manifest module, manifest-first
locator hardening, runtime-aware test boundary, and retained runtime manifest
review are accepted. The retained ignored runtime manifest is
`output/research_reports/accepted_manifest.json`, and the manifest locator
runtime baseline is frozen for `600406`, `002371`, and `002050`.

Latest accepted verification results are quoted, not rerun here:

- targeted tests `251 passed`
- full pytest `899 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

## 1. Final status

- Accepted manifest module accepted.
- Manifest locator hardening accepted.
- Retained runtime manifest review accepted.
- `600406` manifest runtime accepted.
- `002371` manifest runtime accepted.
- `002050` manifest runtime accepted.
- Manifest locator runtime baseline frozen.

## 2. Runtime manifest record

- Path: `output/research_reports/accepted_manifest.json`.
- Ignored by `.gitignore`.
- Not staged and not tracked.
- `git ls-files output` remains empty.
- SHA256:
  `C1F97162A59DE113CD4C9F1A9531AEC3A915A3D6F09365098201234E6F5BEB7F`.
- Size: `7678`.
- mtime UTC: `2026-05-28 10:17:55`.
- Entries count: `3`.
- Freshness status for all entries: `current`.

## 3. Accepted manifest entries

| code | company | profile | accepted HTML | accepted Markdown | accepted JSON | freshness_status | manifest validation result | CLI runtime result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | `stable_growth_grid_equipment` | `output/research_reports/20260528T012952/600406/fundamental_research_report_v1.html` | `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md` | `output/research_reports/20260527T103241/600406/fundamental_research_report_v1.json` | `current` | Passed: manifest read, schema validation, artifact existence, and hash verification all matched. | Accepted: exit code `0`, `Manifest 状态：used`, `Freshness 状态：current`. |
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.html` | `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.md` | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.json` | `current` | Passed: mixed timestamp bundle preserved and hashes matched. | Accepted: exit code `0`, manifest-selected HTML / Markdown from `20260528T125518`, JSON from `20260527T220148`. |
| `002050` | 三花智控 | `advanced_manufacturing_thermal_management` | `output/research_reports/20260528T091133/002050/fundamental_research_report_v1.html` | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` | `output/research_reports/20260527T222558/002050/fundamental_research_report_v1.json` | `current` | Passed: manifest read, schema validation, artifact existence, and hash verification all matched. | Accepted: exit code `0`, `Manifest 状态：used`, `Freshness 状态：current`. |

`002371` retained superseded lineage:

- old Markdown:
  `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md`
- old HTML:
  `output/research_reports/20260528T090024/002371/fundamental_research_report_v1.html`

## 4. Validated manifest-first flow

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

## 5. Recheck results

- Manifest validation passed.
- Artifact hashes all matched.
- CLI `600406` exit code `0`.
- CLI `002371` exit code `0`.
- CLI `002050` exit code `0`.
- All CLI runs showed `Manifest 状态：used`.
- All CLI runs showed `Freshness 状态：current`.
- No `manifest_missing_warning`.
- No timestamp fallback warning.
- No English JSON summary leak.
- No full body dump.
- No positive trading advice.

## 6. Runtime-aware test boundary

- Tests no longer require the real manifest to be absent.
- If the real manifest exists, tests verify hash / mtime / size unchanged.
- Tests write only tmpdir.
- The real ignored manifest remains unmodified.
- Targeted tests with retained manifest passed: `251 passed`.
- Full pytest with retained manifest passed: `899 passed, 1 skipped`.
- Regression passed: `passed=47 failed=0 total=47`.

## 7. Safety / non-goals

- No token read.
- No network.
- No provider call.
- No MCP.
- No live provider.
- No fixture write.
- No scoring / P1.1 change.
- No regression expected change.
- No runtime artifact committed.
- No buy / sell / target price / position sizing / trading signal.
- Manifest does not promote evidence labels.
- Manifest does not verify official facts.
- Manifest is not a CNInfo parser.
- Manifest is not a validator.
- Manifest is not fixture promotion.

## 8. Known limitations

- Freshness is currently manually recorded / static.
- CNInfo / official parser is not implemented.
- L1 evidence tier is not implemented.
- Batch / dashboard is not implemented.
- Live Tushare is not implemented.
- Manifest currently covers only three accepted samples.
- Future runtime updates require acceptance before manifest update.

## 9. Next recommended stage

1. Submit the manifest locator runtime acceptance summary documentation patch.
2. Enter Minimal CNInfo / official disclosure parser design, or A-share
   specific risk framework design.
3. Batch / dashboard design can start after manifest closeout, but should
   depend on the manifest.
4. Live Tushare / token / MCP remain later work.
