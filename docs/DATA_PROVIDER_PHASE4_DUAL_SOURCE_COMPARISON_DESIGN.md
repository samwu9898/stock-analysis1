# Data Provider Phase 4 Dual-Source Comparison Design

Date: 2026-05-26

Status: Design documentation patch only.

This document freezes the Phase 4 design for dual-source comparison smoke and
local real-token acceptance planning after Phase 1 provider abstraction
skeleton, Phase 2 `AkShareProvider` adapter, and Phase 3 mocked
`TushareProvider` MVP were accepted.

This patch does not change code, tests, config, pipeline, classifier,
connector, scoring / readiness, HTML / Dashboard, runtime output, or regression
expected files.

## 1. Phase 4 Positioning

Phase 4 is:

- dual-source comparison smoke design
- local real-token acceptance planning
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

The accepted production path remains unchanged. `real_stock_runner` still uses
the existing AkShare-backed `RealDataConnector` unless a later phase explicitly
changes that behavior after review.

## 2. Dual-Source Comparison Design

The comparison chain should run the two providers independently and keep their
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

The comparison runner should compare at least:

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

Comparison artifacts must be written under an isolated timestamp directory:

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

Classification, confidence, score, and P1.1 question drift must not be accepted
automatically. They require human review even if the raw-data difference appears
reasonable.

## 6. Acceptance Thresholds

Phase 4 local smoke passes only if:

- no token / MCP URL is leaked
- comparison artifacts are not committed to git
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

Tushare does not need to win every field. A useful Phase 4 result may be a
clear matrix of field-level wins, losses, permission gaps, unit differences, and
mapping issues.

## 7. Local Real-Token Procedure

This section designs the later local procedure. It does not execute a real-token
smoke and does not request credentials.

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

The runner should use this procedure:

1. Run token leakage precheck before any real smoke.
2. Require an explicit real-smoke flag such as `--real-token-smoke`; default
   mode remains dry-run.
3. Allow logs / errors / source traces to display only `<masked>`.
4. Run token leakage postcheck after the smoke.
5. If any artifact contains a token-like value, Bearer credential, or raw MCP
   URL text, fail immediately and delete the affected timestamp comparison
   directory.

Source traces should include provider names, endpoint / function names,
canonical field names, source periods, derivation flags, units, and row counts
where useful. They must not include credentials, local config values, or local
connection strings.

## 8. MCP / SDK / HTTP Decision

Phase 4 local smoke should prefer:

- Python SDK transport, or
- another mockable `TushareClient` transport

MCP is only a local tool-layer fallback. The deterministic pipeline must not
depend directly on MCP availability, MCP URLs, MCP config shape, or local
connector state.

HTTP may be added if the SDK is insufficient, but it must still be wrapped by
`TushareClient`. HTTP details must not leak into classifier, scoring, readiness,
P1.1, HTML, or Dashboard logic.

MCP URL text from local config must not be written into the repository.

## 9. Testing Plan

Phase 4 implementation should include tests for:

- comparison artifact path behavior
- no writes to default production output
- token leak detection
- diff classifier behavior
- provider-separated output
- dry-run mode
- local-only real-token smoke skipped by default
- regression unchanged behavior
- `dual_compare` still does not return a merged raw payload

Real-token smoke tests must not run in CI by default and must not require real
credentials.

## 10. CLI / Runner Design

Suggested future runner:

```bash
python -m src.fundamental_skill.data_providers.compare_providers \
  --codes 600406,002050 \
  --providers akshare,tushare \
  --output-dir output/provider_comparison \
  --dry-run
```

Runner requirements:

- default dry-run
- real-token smoke requires explicit `--real-token-smoke`
- default does not write production output
- default does not modify current `evidence_pack`
- default does not run HTML / P1.1
- P1.1 requires explicit `--include-p1`
- token safe

The runner should fail closed if the requested provider is unavailable, if the
Tushare token is absent for a real-token smoke, if canonical raw shape is
broken, or if the artifact boundary would write outside the comparison
directory.

## 11. Risk Review

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

## 12. Claude / External Audit

Recommended external-audit stance:

- Phase 4 design audit can proceed without Claude.
- Phase 4 implementation can proceed without Claude if it remains dry-run /
  comparison-only.
- Local real-token acceptance should have Claude review or strict human audit
  before execution.
- Primary-provider switch must have external audit before acceptance.

## 13. Next Recommendation

Recommendation: proceed to Phase 4 implementation with a tightly isolated
minimum scope:

- isolated `compare_providers` runner
- diff classifier
- artifact writer
- dry-run mode
- token leak scanner
- provider-separated pipeline / evidence builder

Do not change:

- default runner
- provider primary behavior
- regression expected files
- HTML / Dashboard / P1.1 default chain

The user does not need to provide a token now. A token is needed only for a
later local-only real-token smoke, and then only through local `TUSHARE_TOKEN`
or local MCP config, never through prompts or repository files.
