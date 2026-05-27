# Data Provider Phase 4 Closeout Release Note

Date: 2026-05-27

Status: Phase 4 completed and baseline frozen.

This release note records the final closeout state for Data Provider Phase 4.
It is documentation-only and does not change code, tests, config, pipeline,
classifier, scoring / readiness, Research Intelligence P1.1, HTML / Dashboard,
runtime output, comparison output, or regression expected files.

## 1. Final Status

Phase 4 is frozen as comparison-only provider tooling. Tushare is usable for
comparison and data-review workflows, but it is not primary.

Closeout wording distinguishes three paths:

- the default comparison path does not read tokens, call the network, call
  Tushare, connect MCP, or execute real-token smoke
- the accepted safety skeleton is the gate mechanism for any controlled local
  real-token smoke
- later local-only real-token smoke reviews have occurred, with the third review
  recorded under `output/provider_comparison/` timestamp `20260526T233804`

Final accepted state:

- `partial_pass_data_review_required`
- comparison usable
- Tushare primary switch blocked
- no automatic AkShare / Tushare merge
- no automatic drift acceptance
- no default-output pollution
- no token leak observed in the accepted review path

## 2. Completed Modules

Accepted Phase 4 modules and calibrations:

- `compare_providers`
- `comparison_artifacts`
- `diff_classifier`
- `token_leak_scanner`
- `real_token_smoke_gate`
- `tushare_sdk_transport`
- `tushare_provider` `ts_code` normalization
- `tushare_provider` canonical mapping calibration
- `score_confidence_explainability`

The accepted explainability artifact may include top-level
`narrative_hints[]`. Hints are reviewer-facing only, always carry
`automatic_acceptance=false` and `not_for_scoring=true`, and do not change
score, confidence, drift acceptance, scoring, classifier, readiness, canonical
fields, provider primary selection, or merge behavior.

## 3. Real-Token Smoke History

Smoke history summary:

- First smoke: Tushare rows were zero because of the `ts_code` issue.
- Second smoke: Tushare returned non-empty data, but canonical mapping issues
  remained.
- Third smoke: Tushare data availability passed and canonical mapping materially
  improved; remaining score / confidence drift required data review and
  comparison-only explainability.

Third-smoke artifact root:

```text
output/provider_comparison/
20260526T233804
```

This artifact root can remain locally for human review. It must remain ignored
and untracked.

## 4. Guardrails

Frozen Phase 4 guardrails:

- no primary switch
- no automatic merge
- no automatic drift acceptance
- no default output pollution
- no `output/reports` writes
- no regression expected modification
- no token leak
- no real token in prompts, docs, code, tests, logs, outputs, commits, or
  review comments
- no MCP URL from local config in repository files

`score_confidence_explainability.json` remains explicit explainability output
only and is written only under:

```text
output/provider_comparison/<timestamp>/<code>/score_confidence_explainability.json
```

It must not modify raw artifacts, fundamental artifacts, evidence packs,
`diff_report.json`, or `diff_report.md`.

## 5. Latest Verification

Latest accepted verification:

- targeted tests: `27 passed`
- full `pytest`: `648 passed, 1 skipped`
- regression suite: `passed=47 failed=0 total=47`

No additional pytest or regression run is required for this documentation-only
closeout.

## 6. Remaining Known Gaps

Known gaps after Phase 4 freeze:

- `main_business` gap
- business composition `classification_type`
- business composition `revenue_ratio`
- business composition `profit_ratio`
- commodity sidecar policy
- AI datacenter domain evidence
- news fallback

These gaps should be handled by later design work, not by automatic provider
merge, primary switch, or score normalization.

## 7. Next Recommended Phase

Recommended next sequence:

1. Fundamental Ground Truth Benchmark Design
2. Tushare block-level primary design
3. P1.1 deep validation
4. `fina_mainbz type=P/D/I` ratio derivation
5. sidecar data availability design

Ground Truth Benchmark Design should come before any primary-provider decision.

## 8. Do-Not-Do List

Do not:

- run another real-token smoke unless provider mapping or sidecar execution
  changes
- set or request a real token for the closeout phase
- switch Tushare primary
- automatically merge AkShare and Tushare data
- automatically accept drift
- expand P1.1 industry support before deep validation
- start the technical-skill phase yet
- write local MCP config, MCP URL, secrets, or token-like values into the repo
