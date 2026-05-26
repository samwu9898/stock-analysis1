# Data Provider Phase 4 Dual-Source Comparison Design

Date: 2026-05-26

Status: Phase 4 dual-source comparison dry-run implementation accepted; Phase 4 real-token smoke gate safety skeleton implemented and accepted; documentation sync patch only.

This document records the accepted Phase 4 implementation boundary for
dual-source comparison dry-run tooling and local real-token acceptance planning
after Phase 1 provider abstraction skeleton, Phase 2 `AkShareProvider` adapter,
Phase 3 mocked `TushareProvider` MVP, Phase 4 comparison-only dry-run tooling,
and the Phase 4 real-token smoke gate safety skeleton were accepted.

This patch does not change code, tests, config, pipeline, classifier,
connector, scoring / readiness, HTML / Dashboard, runtime output, or regression
expected files.

Accepted Phase 4 implementation inventory:

- isolated `compare_providers` runner
- `comparison_artifacts`
- `diff_classifier`
- `token_leak_scanner`
- `real_token_smoke_gate`
- `tushare_sdk_transport`
- CLI interlock for `--real-token-smoke` and `--provider-transport`
- strengthened token scanner
- `strategy_type_drift` diff category

Latest recorded verification after Phase 4 real-token smoke gate safety skeleton acceptance:

- targeted tests `42 passed, 1 skipped`
- full `pytest` `589 passed, 1 skipped`
- regression suite `passed=47 failed=0 total=47`

## 1. Phase 4 Positioning

Phase 4 is:

- dual-source comparison dry-run tooling
- local real-token acceptance planning
- local real-token smoke gate safety skeleton
- provider-separated artifact design
- drift report design
- token safety / local-only procedure design

Phase 4 is not:

- default switch to Tushare primary
- production path change
- regression expected update
- P1.1 / HTML / classifier / scoring change
- automatic AkShare / Tushare merge
- real token smoke execution
- MCP integration execution
- real Tushare execution
- network execution
- reading `TUSHARE_TOKEN`
- reading local MCP config

The accepted production path remains unchanged. `real_stock_runner` still uses
the existing AkShare-backed `RealDataConnector` unless a later phase explicitly
changes that behavior after review.

Default Phase 4 runner behavior is dry-run / comparison-only: it does not
generate `output/provider_comparison`, does not write production output, does
not run HTML, and does not run Research Intelligence P1.1. `--include-p1` is
off by default. The accepted real-token smoke gate safety skeleton requires
explicit `--real-token-smoke --provider-transport sdk`, rejects `--token`,
fails closed without a token, and has not executed a real smoke.

Phase roadmap snapshot:

- Phase 0 completed.
- Phase 1 accepted.
- Phase 2 accepted.
- Phase 3 accepted.
- Phase 4 dry-run accepted.
- Phase 4 real-token smoke gate safety skeleton accepted.
- Next: local real-token smoke execution acceptance review / external audit gate.

## 2. Dual-Source Comparison Dry-Run Design

The accepted comparison chain runs the two providers independently and keeps their
artifacts separated:

```text
AkShareProvider
  -> raw dict
  -> FundamentalSkillPipeline.analyze_from_dict
  -> EvidencePackBuilder.build

TushareProvider
  -> raw dict
  -> FundamentalSkillPipeline.analyze_from_dict
  -> EvidencePackBuilder.build
```

The comparison runner compares or is scoped to compare at least:

- `basic_info`
- `business_composition`
- raw `financial_indicator`
- evidence `financial_metrics`
- raw `valuation`
- evidence `valuation_metrics`
- `missing_fields`
- `fetch_status`
- `source_trace_summary`
- `strategy_type` / `sub_type`
- `status` / `confidence` / `score`
- P1.1 `research_questions`

P1.1 drift comparison is off by default. It may run only under an explicit
`--include-p1` style option, and any P1.1 comparison artifacts must still stay
inside the isolated comparison subdirectory. The default comparison path must
not run HTML, Dashboard, or P1.1.

No automatic data merge should occur. If Tushare improves one field and AkShare
improves another, Phase 4 should record that fact in the diff report rather than
constructing a blended canonical payload.

## 3. Artifact Boundary

Default dry-run behavior must not create `output/provider_comparison`. When
artifact writing is explicitly enabled, comparison artifacts must be written
under an isolated timestamp directory:

```text
output/provider_comparison/<timestamp>/<code>/
```

For each stock code, write only provider-separated comparison artifacts:

```text
akshare_raw.json
tushare_raw.json
akshare_fundamental.json
tushare_fundamental.json
akshare_evidence_pack.json
tushare_evidence_pack.json
diff_report.json
diff_report.md
```

If P1.1 comparison is explicitly enabled, also write:

```text
akshare_research_questions_p1.json
tushare_research_questions_p1.json
akshare_research_intelligence_p1.json
tushare_research_intelligence_p1.json
```

Forbidden writes:

- `output/raw_<code>.json`
- `output/fundamental_<code>.json`
- `output/evidence_pack_<code>.json`
- `output/reports`

Comparison artifacts are runtime artifacts and must not be committed to git.
The timestamp directory must be removable as a single unit, so cleanup can be:

```text
delete output/provider_comparison/<timestamp>
```

Deleting that directory must not affect the current baseline, default raw /
fundamental / evidence files, report files, regression fixtures, or regression
expected files.

## 4. Sample Set

The first local comparison sample set should stay small:

| Code | Purpose |
| --- | --- |
| `600406` | `stable_growth` / financial-rich sample. Compare financial indicator completeness, ROE, operating cash flow, receivables, capex, valuation context, and Stable Growth P1.1 drift when explicitly enabled. |
| `002050` | `advanced_manufacturing` / business-composition sample. Compare segment mapping, automotive thermal management, refrigeration / air-conditioning, emerging-business exposure, and robotics boundary handling. |
| `002371` | `semiconductor` / equipment sample. Compare equipment-chain classification inputs, R&D, inventory, capex, financial period handling, and domestic-substitution boundary evidence. |
| `603259` | CXO / financial and business sample. Compare CXO segment evidence, financial statement quality, overseas / customer / order proxy limitations, and business-composition coverage. |
| `000426` | `resource_swing` / commodity caveat sample. Compare financial and business fields while preserving the rule that commodity context currently comes from `ExternalCommodityPriceConnector`, not from a generic Tushare replacement. |
| `002837` | AI datacenter cooling sample. Compare cooling / liquid-cooling infrastructure evidence, business-composition clarity, financial completeness, and ordinary-HVAC boundary handling. |

This sample set is meant for smoke and review. It is not enough to justify a
primary-provider switch.

## 5. Diff Classification

Each `diff_report` item should include:

- `category`
- `field_path`
- `akshare_value`
- `tushare_value`
- `severity`
- `review_required`
- `note`

Required diff categories:

- `exact_match`
- `expected_provider_difference`
- `harmless_format_difference`
- `unit_difference`
- `missing_field_improvement`
- `missing_field_regression`
- `stale_or_failed_akshare_field`
- `tushare_permission_missing`
- `canonical_mapping_issue`
- `strategy_type_drift`
- `classification_drift`
- `confidence_drift`
- `score_drift`
- `P1_question_drift`
- `safety_boundary_risk`
- `token_or_secret_risk`

Suggested severity levels:

- `info`: exact match, harmless format difference, or expected provider wording
- `review`: unit difference, provider-period difference, or explained missing
  field movement
- `blocker`: token / secret exposure, default-output overwrite, canonical shape
  breakage, or unreviewed classification / score / confidence / P1.1 drift

Accepted diff-classifier behavior:

- `strategy_type_drift` must set `review_required=true`.
- `classification_drift` must set `review_required=true`.
- `confidence_drift` must set `review_required=true`.
- `score_drift` must set `review_required=true`.
- `P1_question_drift` must set `review_required=true`.
- `token_or_secret_risk` must be `blocker`.
- No drift is automatically accepted, even when the raw-data difference appears reasonable.

Strategy-type, classification, confidence, score, and P1.1 question drift
require human review before any migration decision.

## 6. Token Leak Scanner

Accepted scanner behavior:

- Supports scanning `dict`, `list`, and `str` payloads.
- Supports exact token reference matching when a fake token reference is
  intentionally injected by tests.
- Detects `token=`.
- Detects `api_key=`.
- Detects `Bearer`.
- Detects MCP URL / `mcp?token=`.
- Detects realistic 32+ character token-like values, especially near
  case-insensitive keywords such as `token`, `key`, `secret`, `auth`, and
  `credential`.
- Scans dict keys, dict values, nested metadata, and URL query parameters.
- Emits only finding location and `<masked>` for detected secret-like values.

Any token-like hit in comparison artifacts, logs, source traces, or diagnostics
is a blocker for real-token acceptance.

## 7. Acceptance Thresholds

Phase 4 dry-run acceptance passed under these boundaries:

- no token / MCP URL is leaked
- comparison artifacts are not committed to git
- default dry-run does not generate `output/provider_comparison`
- default production output is unchanged
- `output/reports` is unchanged
- AkShare path still runs
- Tushare raw canonical shape is correct
- Tushare reduces missing fields on several core fields or the provider
  difference is clearly explained
- classification drift is manually audited and not automatically accepted
- score / confidence drift is not automatically accepted
- P1.1 question drift is manually audited
- there is no automatic primary-provider switch
- `--include-p1` is off by default
- real-token smoke remains local-only, explicitly gated, and not executed
- regression expected files are unchanged

Tushare does not need to win every field. A useful Phase 4 result may be a
clear matrix of field-level wins, losses, permission gaps, unit differences, and
mapping issues.

## 8. Local Real-Token Procedure

This section records the accepted local safety skeleton for a later real-token
smoke. It does not execute a real-token smoke and does not request credentials.
The next step is execution acceptance review / external audit gate work, not
direct execution of a real-token smoke.

Allowed credential placement for a later local smoke:

- user sets `TUSHARE_TOKEN` on the local machine
- or user configures the token in local MCP config

The token must never enter:

- prompt
- code
- docs
- tests
- logs
- output
- commits
- review comments

The runner should use this procedure:

1. Run precheck before any real smoke, including repo tracked-file scan,
   staged-diff scan, docs / tests / source scan, target output scan, and
   protected-output snapshots.
2. Record `output/reports` and default output path sets plus SHA-256 hashes.
3. Require explicit `--real-token-smoke --provider-transport sdk`; default mode
   remains dry-run.
4. Reject `--token` CLI arguments; keep `http` and `mcp-local` reserved and
   fail closed.
5. Fail closed when no local token is available, before any SDK call.
6. Scan every payload and diff report before write.
7. Run postcheck after the attempt, verify protected path sets and hashes, and
   confirm comparison artifacts are not staged or tracked.
8. If any blocker occurs, delete only the strict timestamp comparison
   directory and record only a sanitized reason.

Source traces should include provider names, endpoint / function names,
canonical field names, source periods, derivation flags, units, and row counts
where useful. They must not include credentials, local config values, or local
connection strings.

## 9. MCP / SDK / HTTP Decision

Phase 4 local smoke should prefer:

- Python SDK transport, or
- another mockable `TushareClient` transport

The accepted safety skeleton implements only the SDK transport skeleton. Tests
use fake SDK objects / factories. HTTP and MCP-local transports remain reserved
and explicitly fail closed.

MCP is only a local tool-layer fallback. The deterministic pipeline must not
depend directly on MCP availability, MCP URLs, MCP config shape, or local
connector state.

HTTP may be added if the SDK is insufficient, but it must still be wrapped by
`TushareClient`. HTTP details must not leak into classifier, scoring, readiness,
P1.1, HTML, or Dashboard logic.

MCP URL text from local config must not be written into the repository.

## 10. Testing Plan

Phase 4 dry-run acceptance included targeted coverage for:

- comparison artifact path behavior
- no writes to default production output
- token leak detection
- diff classifier behavior
- provider-separated output
- dry-run mode
- local-only real-token smoke skipped by default
- regression unchanged behavior
- `dual_compare` still does not return a merged raw payload

Latest recorded verification after safety skeleton acceptance: targeted tests
`42 passed, 1 skipped`; full `pytest` `589 passed, 1 skipped`; regression
suite `passed=47 failed=0 total=47`.

Real-token smoke tests must not run in CI by default and must not require real
credentials.

## 11. CLI / Runner Design

Accepted isolated runner:

```bash
python -m src.fundamental_skill.data_providers.compare_providers \
  --codes 600406,002050 \
  --providers akshare,tushare \
  --output-dir output/provider_comparison \
  --dry-run
```

Runner requirements:

- default dry-run
- real-token smoke path requires explicit `--real-token-smoke --provider-transport sdk`
- `--provider-transport` without `--real-token-smoke` fails closed
- `--real-token-smoke` without `--provider-transport` fails closed
- `--provider-transport http` and `--provider-transport mcp-local` fail closed as reserved
- `--token` is rejected
- default does not write production output
- default does not modify current `evidence_pack`
- default does not run HTML / P1.1
- P1.1 requires explicit `--include-p1`
- token safe

The runner should fail closed if the requested provider is unavailable, if the
local token is absent for a real-token smoke, if canonical raw shape is broken,
or if the artifact boundary would write outside the comparison directory. Safe
errors must not echo raw command text or secret-like arguments.

## 12. Risk Review

Main risks:

- Tushare field units may differ from AkShare units
- financial statement scope may differ
- business-composition classification may differ
- valuation units may differ
- selected reporting period may differ
- missing fields may move from AkShare to Tushare instead of improving
- classification drift
- confidence / score drift
- P1.1 question drift
- token leakage
- accidental default-output overwrite
- `000426` commodity context currently comes from `ExternalCommodityPriceConnector`; Phase 4 must not assume Tushare has replaced the commodity provider

Any drift that changes final deterministic interpretation should be treated as a
review finding, not as an automatic migration success.

## 13. Claude / External Audit

Recommended external-audit stance:

- Phase 4 design and dry-run implementation have been accepted without requiring real-token external audit because they remained comparison-only.
- Phase 4 real-token smoke gate safety skeleton has been implemented and
  accepted without executing real smoke.
- Local real-token smoke execution should have Claude review or strict human
  audit before execution.
- Primary-provider switch must have external audit before acceptance.

## 14. Next Recommendation

Recommendation: keep the accepted Phase 4 implementation frozen as a tightly
isolated dry-run plus real-token smoke gate safety baseline:

- isolated `compare_providers` runner
- diff classifier
- artifact writer
- dry-run mode
- token leak scanner
- real-token smoke gate helper
- SDK transport skeleton
- provider-separated pipeline / evidence builder

Next gate: local real-token smoke execution acceptance review / external audit gate.

Do not directly execute a real-token smoke. Real tokens may be used only in a
later local-only execution acceptance step through local `TUSHARE_TOKEN` or
local MCP config; they must never enter prompts, code, docs, tests, logs,
output, commits, or review comments.

Do not change:

- default runner
- provider primary behavior
- regression expected files
- HTML / Dashboard / P1.1 default chain

The user does not need to provide a token now. A token is needed only for a
later local-only real-token smoke, and then only through local `TUSHARE_TOKEN`
or local MCP config, never through prompts or repository files.
