# Data Provider Phase 4 Score / Confidence Explainability Design

Date: 2026-05-27

Status: comparison-only score / confidence explainability implementation,
narrative hints patch, narrative-hints artifact review, and Phase 4 closeout
baseline freeze completed and accepted; this patch is documentation
synchronization only.

This document consolidates the Gemini / DeepSeek / Kimi external audit feedback
after the third Tushare real-token smoke review and records the accepted
comparison-only score / confidence explainability implementation boundary,
including the accepted reviewer-facing `narrative_hints[]` extension.

This documentation sync only adds and synchronizes documentation. It does not change code,
tests, config, pipeline behavior, classifier behavior, scoring / readiness,
Research Intelligence P1.1, HTML / Dashboard behavior, runtime output,
comparison output, or regression expected files. It does not read a token, call
Tushare, use the network, read local MCP config, connect MCP, run a real smoke,
switch provider primary behavior, merge providers, or automatically accept
drift.

Reference smoke artifact root recorded by the prior review:

```text
output/provider_comparison/20260526T233804
```

Latest recorded score / confidence explainability implementation verification:

- targeted tests: `27 passed`
- full `pytest`: `648 passed, 1 skipped`
- regression suite: `passed=47 failed=0 total=47`

Previous recorded verification from the third real-token smoke review:

- `pytest`: `630 passed, 1 skipped`
- regression suite: `passed=47 failed=0 total=47`

## 1. Current Conclusion

The third Tushare real-token smoke result is:

- overall status: `partial_pass_data_review_required`
- token leak: none observed
- artifact boundary failure: none observed
- default output pollution: none observed
- `output/reports` modification: none observed
- regression expected modification: none observed
- Tushare endpoints are usable
- non-news Tushare blocks are non-empty
- canonical raw shape is correct
- `market_cap` units have been corrected
- `gross_margin` has been corrected
- business-level `gross_margin` has been derived
- no `missing_field_regression`
- no `strategy_type_drift`
- no `classification_drift`
- score drift remains
- confidence drift remains for `000426` and `002837`

Current decision:

- Tushare data availability has passed the real-token smoke data-availability
  gate.
- Canonical mapping has materially improved compared with earlier Phase 4
  states.
- Score / confidence drift explainability implementation has been completed and
  accepted as comparison-only tooling.
- Narrative hints have been completed and accepted as reviewer-facing
  explanation only.
- The narrative-hints explainability artifacts have been regenerated from the
  third smoke artifact root and reviewed successfully.
- Phase 4 is frozen as a comparison-only baseline. The next recommended phase
  is Fundamental Ground Truth Benchmark Design, not more Phase 4 smoke.
- Later provider-mapping / sidecar policy decisions remain separate designs,
  not provider reachability issues.
- Tushare must not become primary yet.
- AkShare and Tushare data must not be automatically merged.
- Drift must not be automatically accepted.
- A new real-token smoke is not needed for this documentation sync or for
  explainability artifact review unless later provider mapping or sidecar
  execution changes are introduced.
- The user does not need to provide any token for this stage.

## 2. Drift Classification

Remaining drift should be described with explicit human-review subcategories:

- `Tushare mapping gap`
- `provider coverage caveat`
- `scoring explainability gap`
- `scoring_penalty_due_to_provider_gap`
- `domain_evidence_missing`
- `provider_coverage_caveat`

Sample-level interpretation from the third smoke review:

| Code | Primary Remaining Drift | Design Interpretation |
| --- | --- | --- |
| `600406` | score drift | Explain the dimension-level scoring delta and whether it comes from mapped input differences, missing ratio fields, readiness caps, or provider coverage caveats. |
| `002050` | score drift | Explain score delta without normalizing away missing main-business / ratio inputs. |
| `002371` | score drift | Explain score delta at the mapped-field and scoring-dimension level. |
| `603259` | score drift | Explain score delta at the mapped-field and scoring-dimension level. |
| `000426` | confidence + score drift | Commodity evidence is provider-independent sidecar context. Missing sidecar coverage in the Tushare-only view should be marked as `provider_coverage_caveat` / `external_sidecar_missing`, not silently merged into Tushare raw data. |
| `002837` | confidence + score drift | AI datacenter evidence such as liquid-cooling revenue share, orders, customer validation, and batch delivery is domain evidence outside generic Tushare fundamentals. Missing evidence should be marked as `domain_evidence_missing`. |

The design must distinguish:

- true Tushare mapping gaps that may be remediated in provider mapping
- provider coverage caveats that reflect the provider's legitimate data boundary
- scoring explainability gaps where the comparison currently lacks enough
  narrative to explain why an existing scoring rule penalized the Tushare view
- domain evidence gaps where neither generic Tushare fundamentals nor generic
  financial statements can prove a strategy-specific operating claim

## 3. No Scoring Normalization

The next patch must not implement provider-specific scoring normalization.

Explicitly forbidden:

- modifying the scoring algorithm
- modifying scoring weights, caps, or constraints
- modifying data-readiness behavior
- modifying regression expected outputs
- granting Tushare provider-specific score normalization because `main_business`
  or business-composition ratio fields are missing
- masking a real evidence gap by scaling, smoothing, or offsetting the Tushare
  score

The correct sequence is:

1. explain remaining score / confidence drift
2. identify whether each drift source is a mapping gap, coverage caveat,
   domain-evidence gap, readiness cap, or scoring penalty caused by provider
   input differences
3. decide later whether a specific provider-mapping patch is warranted

The comparison system must not hide true evidence gaps. If the Tushare-only view
lacks domain evidence, the explainability artifact should say so directly.

## 4. Implemented Comparison-Only Explainability V1 Scope

The accepted explainability implementation is limited to:

- comparison-only behavior
- default off
- generated only when `compare_providers` receives explicit `--explainability`
- no token read
- no network
- no Tushare call
- no real smoke execution in the explainability or default comparison path
- no default output writes
- no current `evidence_pack` mutation
- no Research Intelligence P1.1 change
- no HTML / Dashboard change
- no classifier change
- no scoring change
- no readiness change
- no regression expected change
- no primary-provider switch
- no automatic provider merge
- no automatic drift acceptance
- reviewer-facing `narrative_hints[]` only

The implementation may run against injected provider outputs and dry-run test
fixtures. It must not require a real token.

## 5. Output Boundary

The recommended V1 output is one independent artifact:

```text
score_confidence_explainability.json
```

Allowed write location:

```text
output/provider_comparison/<timestamp>/<code>/score_confidence_explainability.json
```

Required boundary rules:

- The artifact has been added to the comparison artifact allowlist as
  `EXPLAINABILITY_ARTIFACT_NAMES`.
- It is generated only in explicit explainability mode.
- It must not write `output/raw_*.json`.
- It must not write `output/fundamental_*.json`.
- It must not write `output/evidence_pack_*.json`.
- It must not write `output/reports`.
- It must not enter git.
- It must not change default `diff_report.json` or `diff_report.md` content.
- If a future patch wants `diff_report.md` to reference explainability, that
  must be separately designed and reviewed; it is not part of V1.

Why use an independent artifact:

- It reduces schema pressure on the existing `diff_report` output.
- It avoids changing default comparison behavior.
- It makes it easier to prove the artifact does not flow back into scoring,
  evidence packs, Research Intelligence P1.1, HTML, Dashboard, or default
  production output.

## 6. Explainability Schema

Proposed V1 schema:

```json
{
  "code": "000000",
  "providers": {
    "akshare": {
      "artifact_refs": {
        "raw": "akshare_raw.json",
        "fundamental": "akshare_fundamental.json",
        "evidence_pack": "akshare_evidence_pack.json"
      }
    },
    "tushare": {
      "artifact_refs": {
        "raw": "tushare_raw.json",
        "fundamental": "tushare_fundamental.json",
        "evidence_pack": "tushare_evidence_pack.json"
      }
    }
  },
  "automatic_acceptance": false,
  "explainability_only": true,
  "score_summary": {
    "akshare_score": 0,
    "tushare_score": 0,
    "score_delta": 0,
    "score_drift_reason": "scoring_penalty_due_to_provider_gap"
  },
  "confidence_summary": {
    "akshare_confidence": "medium",
    "tushare_confidence": "low",
    "confidence_delta": "medium_to_low",
    "confidence_drift_reason": "domain_evidence_missing"
  },
  "dimension_breakdown": [
    {
      "dimension": "growth_quality",
      "akshare_raw_score": 0,
      "tushare_raw_score": 0,
      "akshare_constrained_score": 0,
      "tushare_constrained_score": 0,
      "weight": 0.0,
      "delta": 0,
      "key_input_fields": [
        "business_composition.ratio",
        "basic_info.main_business"
      ],
      "missing_fields": [
        "basic_info.main_business"
      ],
      "readiness_penalties": [
        "insufficient_domain_evidence"
      ],
      "caps_or_constraints": [
        "readiness_cap"
      ],
      "provider_caveats": [
        "provider_coverage_caveat"
      ],
      "drift_subcategory": "scoring_penalty_due_to_provider_gap"
    }
  ],
  "provider_caveats": [
    {
      "code": "provider_coverage_caveat",
      "provider": "tushare",
      "field": "commodity_prices",
      "category": "external_sidecar_missing",
      "note": "Commodity prices are provider-independent sidecar evidence and are not part of generic Tushare fundamentals."
    }
  ],
  "derived_hints": [
    {
      "field": "business_composition.max_segment",
      "value": "example segment",
      "source": "fina_mainbz:selected_period",
      "derived": true,
      "not_for_scoring": true,
      "reason": "Largest segment may help reviewers understand composition, but it must not become canonical basic_info.main_business."
    }
  ],
  "narrative_hints": [
    {
      "code": "business_quality_main_business_gap",
      "scope": "score_drift",
      "provider": "tushare",
      "related_fields": [
        "basic_info.main_business",
        "business_composition.revenue_ratio"
      ],
      "message": "Reviewer-facing explanation only.",
      "automatic_acceptance": false,
      "not_for_scoring": true
    }
  ],
  "domain_evidence_policy": {
    "resource_swing": {
      "sidecar_policy": "commodity_prices are provider-independent evidence",
      "missing_policy": "mark external_sidecar_missing / provider_coverage_caveat"
    },
    "ai_datacenter_cooling": {
      "required_evidence_examples": [
        "liquid_cooling_revenue_share",
        "orders",
        "customer_validation",
        "batch_delivery"
      ],
      "missing_policy": "mark domain_evidence_missing"
    },
    "cxo": {
      "required_evidence_examples": [
        "backlog",
        "new_orders",
        "customer_region_exposure",
        "capacity_utilization"
      ],
      "missing_policy": "mark domain_evidence_missing when generic fundamentals cannot prove the domain claim"
    }
  }
}
```

Schema notes:

- `automatic_acceptance` must always be `false` in V1.
- `explainability_only` must always be `true` in V1.
- `artifact_refs` are non-secret local filenames or relative comparison-artifact
  references only; they must not contain tokens, credentials, MCP configuration,
  or absolute local secret paths.
- `provider_caveats.code` is a standardized caveat code, not a stock code.
- `derived_hints` may help reviewers understand likely explanations but must be
  excluded from scoring and canonical evidence-pack fields.
- `narrative_hints` are reviewer-facing explanations only. Every item must
  include `automatic_acceptance=false` and `not_for_scoring=true`.
- `narrative_hints` must not change score, confidence, drift acceptance,
  classifier output, readiness, scoring, provider mapping, canonical fields,
  primary-provider selection, or merge behavior.
- `domain_evidence_policy` is extensible. Initial named policies include
  `resource_swing`, `ai_datacenter_cooling`, and `cxo`.

## 6.1 Accepted Narrative Hints

The accepted narrative hints patch adds reviewer-facing explanation depth
without recalculating scores or changing any downstream decision.

Accepted sample / strategy coverage:

| Code | Accepted narrative hints |
| --- | --- |
| `600406` | `business_quality_main_business_gap`, `business_ratio_missing` |
| `002050` | `advanced_manufacturing_business_exposure_gap` |
| `002371` | `semiconductor_business_text_or_ratio_gap`, `semiconductor_financial_inputs_available` |
| `603259` | `cxo_domain_proxy_gap` |
| `000426` | `external_sidecar_missing`, `commodity_context_provider_independent` |
| `002837` | `domain_evidence_missing`, `liquid_cooling_revenue_share_missing`, `orders_customer_validation_batch_delivery_missing` |

Narrative hint policy:

- reviewer-facing only
- `automatic_acceptance=false`
- `not_for_scoring=true`
- no scoring change
- no confidence change
- no drift-acceptance change
- no scoring / classifier / readiness participation
- no canonical-field writeback
- no primary-provider switch basis
- no automatic merge basis

Content boundaries:

- `600406` hints may explain business_quality, main-business text, and
  business-composition ratio gaps.
- `002050` hints may explain that automotive thermal, refrigeration, and new
  business exposure still need finer business-composition ratio or
  main-business evidence. They must not claim robotics exposure is proven.
- `002371` hints may explain semiconductor equipment business text / ratio gaps
  while separately noting that R&D, inventory, and capex-style inputs are
  available. They must not add domestic-substitution conclusions.
- `603259` hints must stay conservative: generic fundamentals cannot directly
  prove CXO backlog, customer exposure, geography, or CDMO utilization.
- `000426` hints must keep commodity context as provider-independent sidecar
  evidence and must not merge commodity rows into Tushare raw data.
- `002837` hints must keep liquid-cooling revenue share, orders, customer
  validation, and batch delivery as missing domain evidence. Generic Tushare
  financials must not be treated as liquid-cooling evidence.

## 7. Module Boundary

Accepted implementation module:

```text
src/fundamental_skill/data_providers/score_confidence_explainability.py
```

Required module boundary:

- pure functions
- read-only behavior
- no side effects except returning an explainability payload to the comparison
  runner, which may then write the explicit artifact under the allowlisted
  comparison directory
- no import from `scoring_engine`
- no import from readiness modules
- no import from classifier modules
- no import from Research Intelligence P1 builder modules
- no default-output writes
- no mutation of `evidence_pack`
- read only existing AkShare / Tushare comparison artifacts for raw,
  fundamental, evidence, and diff data
- output only the independent explainability artifact in explicit mode
- no participation in downstream decisions
- narrative hints are returned in the independent artifact only and remain
  reviewer-facing diagnostics

The module should be a narrative and diagnostic layer over already-produced
comparison data. It must not recalculate final scores by importing the scoring
engine. If a dimension-level score is already available in comparison artifacts,
the explainability module may read and report it. If it is not available, it
should report the gap as an explainability limitation instead of invoking
downstream scoring.

## 8. CLI / Runner Design

The accepted implementation adds:

```text
--explainability
```

CLI requirements:

- `default=False`
- supported only by `compare_providers`
- behavior is completely unchanged when the flag is absent
- does not require `--real-token-smoke`
- can be used with existing artifacts, fake provider fixtures, or dry-run data
- does not automatically execute real-token smoke
- cannot be combined with `--real-token-smoke` in V1
- does not automatically run Research Intelligence P1.1
- does not automatically modify `diff_report`
- does not automatically accept drift

The flag is an artifact-generation request for diagnostics only. It is not a
migration acceptance flag.

## 9. Diff Classifier Subcategory Design

The accepted implementation adds reviewer-aid drift subcategory values in
`diff_classifier` for explainability use. These values must not alter scoring,
readiness, classifier output, default `diff_report` schema, or migration
acceptance.

Recommended subcategories:

- `missing_field`
- `unit_diff`
- `provider_coverage_caveat`
- `domain_evidence_missing`
- `scoring_penalty_due_to_provider_gap`
- `mapping_gap`
- `readiness_cap`
- `external_sidecar_missing`

These subcategories are reviewer aids. They must not be used to automatically
repair scores, normalize scores, merge providers, or accept drift.

## 10. Main-Business Gap Policy

`main_business` remains a high-risk semantic field because a largest business
segment is not always the same as a canonical company main-business description.

Policy:

- Do not derive canonical `basic_info.main_business` from the largest segment.
- The largest segment may appear only in `derived_hints`.
- `derived_hints.not_for_scoring` must be `true`.
- Derived hints must not enter classifier logic.
- Derived hints must not enter scoring logic.
- Derived hints must not mutate the evidence-pack canonical field.
- The long-term solution is a dedicated official-source provider such as CNInfo,
  an annual-report parser, or an official company-profile provider.

## 11. Business Composition Ratio / Classification Policy

`fina_mainbz` type and period selection remain a separate mapping topic.

Policy:

- `fina_mainbz` `type=P/D/I` plus selected-period ratio derivation is a later
  patch, not part of explainability V1.
- Do not derive ratios across groups.
- Do not derive ratios across periods.
- Do not use missing ratios as a reason for provider-specific score
  normalization.
- Explainability V1 may only report how `ratio_missing` or
  `classification_missing` affected score / confidence drift.

The comparison system may state that a score changed because a ratio or
classification input was absent. It must not infer the missing value to repair
the score.

## 12. Commodity / Domain Evidence Sidecar Policy

This section is design-only and does not implement sidecar code.

Policy:

- `commodity_prices` are provider-independent evidence, not a responsibility of
  `TushareProvider`.
- The commodity context for `000426` must not be generalized away or replaced
  by generic Tushare fundamentals.
- Dual comparison must not automatically merge sidecar evidence into Tushare
  raw data.
- If a future sidecar comparison is designed, it must explicitly distinguish:
  - provider-only view
  - `provider+independent_sidecar` view
- Explainability V1 may only record `external_sidecar_missing`,
  `sidecar_missing`, or `provider_coverage_caveat`.
- Explainability V1 must not implement sidecar fetching or sidecar merge logic.

For `000426`, score and confidence drift caused by missing commodity context is
expected to be explainable as a provider-independent evidence boundary, not a
Tushare endpoint failure.

## 13. AI Datacenter Domain Evidence Policy

For `002837`, the key missing evidence is domain-specific operating evidence,
not generic fundamental-provider coverage.

Policy:

- Liquid-cooling revenue share, orders, customer validation, and batch delivery
  evidence are not guaranteed by generic Tushare fundamental endpoints.
- Tushare confidence reduction caused by missing AI datacenter domain evidence
  is a reasonable outcome.
- Explainability should mark this as `domain_evidence_missing`.
- Scoring normalization must not smooth away this evidence gap.
- A future `DomainEvidenceProvider` may be designed later, but it is out of
  scope for this phase.

The design should preserve the distinction between:

- provider mapping correctness
- provider coverage limits
- domain-evidence availability
- deterministic scoring penalties that correctly follow from missing evidence

## 14. Must-Not-Touch Boundary

This phase and the V1 explainability implementation must not touch:

- scoring algorithm
- scoring weights
- readiness
- classifier
- Research Intelligence P1.1
- HTML / Dashboard
- `real_stock_runner` default path
- `evidence_pack` schema
- regression expected files
- provider primary switch
- AkShare / Tushare automatic merge
- automatic drift acceptance
- `output/reports`
- default output

Any future change to one of these areas requires a separate design, acceptance
gate, and external audit where appropriate.

## 15. Implementation Acceptance Record

Accepted implementation verification:

- targeted tests: `27 passed`
- full `pytest`: `648 passed, 1 skipped`
- regression suite: `passed=47 failed=0 total=47`

The accepted implementation boundary verifies:

- no scoring import
- default `compare_providers` behavior unchanged
- no explainability output unless explicit flag is enabled
- explainability output only under the provider-comparison timestamp directory
- no token leak
- no real token required
- no network
- no MCP
- no default output writes
- no regression expected changes
- full `pytest` green
- regression suite `47/47` green
- existing `diff_report` unchanged unless a separate explicit design says
  otherwise
- comparison artifact allowlist enforced
- accepted `narrative_hints[]` schema and sample / strategy coverage
- every narrative hint has `automatic_acceptance=false` and
  `not_for_scoring=true`

Recommended test posture:

- unit tests with fake comparison artifacts
- dry-run tests with explicit `--explainability`
- negative test proving no artifact is produced without the flag
- import-boundary test proving the module does not import scoring, readiness,
  classifier, or P1 builder modules
- artifact-boundary test proving writes are limited to
  `output/provider_comparison/<timestamp>/<code>/score_confidence_explainability.json`

This documentation-only sync does not require pytest or regression to be rerun;
it cites the accepted implementation and narrative-hints acceptance results
above.

## 16. Whether Another Real Smoke Is Needed

No new real-token smoke is needed for this documentation sync, explainability
artifact review, or Phase 4 closeout baseline freeze.

Rationale:

- The explainability layer is based on already-produced comparison artifacts.
- It can be tested with mock / fake data and existing artifact shapes.
- It must not call Tushare.
- It must not read a token.
- It must not use network or MCP.

A future real-token smoke becomes relevant only if a later patch implements:

- `fina_mainbz` `type=P/D/I` selected-period ratio derivation
- sidecar policy execution
- a new provider mapping that depends on real endpoint behavior
- a domain evidence provider that needs external data validation

## 17. Roadmap

Recommended roadmap:

1. Score / confidence explainability design. Completed.
2. Comparison-only explainability implementation. Completed.
3. Acceptance for the implementation boundary. Completed.
4. Narrative hints patch and acceptance. Completed.
5. Documentation synchronization. This patch.
6. Review `score_confidence_explainability.json` artifacts when useful.
7. Decide whether to implement `fina_mainbz` `type=P/D/I` selected-period ratio
   derivation.
8. Sidecar policy design.
9. Primary-provider switch remains remote and must require external audit.

Primary-provider switching is not a near-term step. The current state is data
availability pass plus accepted comparison-only explainability tooling; artifact
review and later mapping / sidecar decisions remain separate.

## 18. External Audit Feedback Adoption

Gemini audit adoption (`A`):

- Proceed only within comparison-only explainability.
- Do not allow hidden merge through sidecars.
- Keep ratio derivation strictly within the same group and same period if it is
  ever implemented in a later patch.

DeepSeek audit adoption (`B`, proceed after design changes):

- Use an independent `score_confidence_explainability.json` artifact.
- Keep explainability default-off.
- Do not change `diff_report` in V1.
- Do not import scoring, readiness, classifier, or P1 modules.

Kimi audit adoption (`B`, proceed after design changes):

- Keep explainability read-only and isolated.
- Keep it default-off.
- Prevent feedback into scoring, evidence packs, P1.1, HTML, Dashboard, or
  default output.
- Treat sidecar handling as design-only in this phase.
