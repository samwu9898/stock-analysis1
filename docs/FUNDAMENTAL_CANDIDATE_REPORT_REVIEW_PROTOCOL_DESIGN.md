# Fundamental Candidate Report Review Protocol Design

Date: 2026-05-27

Stage: Fundamental Skill Candidate Report Review Protocol Design.

Status: design-only. This document does not implement code, does not modify
tests, fixtures, pipeline, scoring, Research Intelligence P1.1, regression
expected files, or provider-primary behavior. It does not run smoke tests, read
`TUSHARE_TOKEN`, use the network, call Tushare or AkShare, connect MCP, promote
fixture values, automatically merge providers, or output investment advice.

Current input reference:

- Candidate report:
  `output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json`
- Report mode: `offline_artifact_candidate_generation`
- `auto_accepted_core_fields`: 8 core fields
- `manual_review_priority_queue`: 20 items
- Explicit high-priority queue coverage:
  `valuation_metrics.as_of_date` and `business_composition.period`

The candidate report has passed artifact audit, but it is not reviewed ground
truth.

## 1. Protocol Goal

The Candidate Report Review Protocol is not a manual table-filling workflow.
The user should not inspect 1000+ raw candidates one by one, search for every
financial value again, or use the ground-truth fixture as a data-entry surface.

The protocol's goal is to turn `manual_review_priority_queue` into a small
number of high-value, executable review actions:

- compress many candidate rows into a few review decisions;
- route human attention only to high-priority uncertainty;
- confirm whether a candidate remains eligible for a later promote step;
- identify whether uncertainty is caused by source conflict, period, unit,
  classification, denominator, provider coverage, mapping, or unavailable
  source data;
- record review outcomes without writing the ground-truth fixture.

Review confirms whether candidate facts can later be promoted. It does not
repeat provider data collection, does not fetch new data, and does not decide
buy / sell, target price, position sizing, or portfolio weight.

## 2. Review Queue Categories

The protocol uses canonical review queue item types. The generator may emit
more compact labels, but the review protocol maps them into these types before
presenting actions to the reviewer.

| Queue item type | Why review is needed | Blocks promote? | Metadata to inspect first | Parser / mapping follow-up | Coverage caveat? |
| --- | --- | --- | --- | --- | --- |
| `source_conflict` | Providers or source blocks disagree beyond tolerance after normalization. | Yes, for the affected field until resolved. | `source_provider`, `source_artifact`, `source_block`, `source_endpoint`, `source_trace`, `value`, `report_period`, `as_of_date`, `canonical_unit`, `conflict_status`. | Create a provider mapping patch only if conflict is caused by wrong field, unit, or endpoint mapping. Use official parser if provider conflict cannot be resolved. | No, unless the field is out of V1 scope. |
| `unit_unknown` | The value may be numeric but the source unit or canonical unit is unclear. | Yes. | `data_unit`, `canonical_unit`, `source_endpoint`, `source_field`, `source_trace`, provider documentation captured in metadata. | Usually requires provider mapping patch; official parser may be needed when source table units are only in filing text. | No. |
| `period_mismatch` | Values refer to different report periods or trade dates. | Yes for period-sensitive fields; may be a caveat for non-promoted display hints. | `report_period`, `as_of_date`, `ann_date`, `disclosure_date`, `source_period`, `row_selector`, `source_endpoint`. | Mapping patch if period came from the wrong row selector. Official parser if provider cannot expose comparable periods. | Sometimes, when the field is not promoted and is only shown as a limitation. |
| `valuation_as_of_date_review_required` | `pe_ttm`, `pb`, and `market_cap` are trade-date sensitive and must share the same valuation date before strict comparison. | Yes for the valuation block until date clarity exists. | `as_of_date`, valuation endpoint, `source_trace`, `source_provider`, `value`, `canonical_unit`, row selector, same-date coverage across PE / PB / market cap. | Mapping patch if provider emits valuation without date metadata. | No. |
| `business_composition_period_review_required` | Segment rows must belong to the same report period and same classification group before ratio or margin review. | Yes for composition rows and derived ratios. | `report_period`, `source_period`, `classification_type`, `segment_name`, `row_selector`, `source_endpoint`, `source_provider`, `denominator_scope`. | Provider mapping patch if `fina_mainbz` type or group semantics are missing; official parser if provider rows cannot be grouped safely. | No for promoted rows; may be a coverage caveat for V1. |
| `main_business_review_required` | `main_business` is narrative text and can be stale, provider-derived, or incomplete. | Yes for `main_business`; not for unrelated numeric fields. | `source_provider`, `source_endpoint`, `source_trace`, `value`, official profile / annual report reference when available, text freshness. | Prefer CNInfo / annual report / official profile parser. Do not solve by largest segment derivation. | Yes, when no official source is available and the field remains display-only. |
| `classification_type_missing` | Business composition rows cannot be safely compared or ratio-derived without group type. | Yes for affected composition rows and ratios. | `classification_type`, provider-specific type such as `P` / `D` / `I`, `source_endpoint`, `segment_name`, `row_selector`, `source_period`. | Usually requires provider mapping patch; official parser if provider lacks the classification group. | No for promoted rows. |
| `ratio_denominator_unclear` | A ratio or margin may be derived from an unclear denominator or mixed group total. | Yes for `revenue_ratio`, `gross_margin`, `profit_ratio`, and similar derived fields. | `derived`, `derivation_method`, `denominator_scope`, numerator source field, denominator source field, classification group, report period. | Mapping patch if numerator / denominator source fields are known but not exposed; official parser if table totals are only in filing text. | No for promoted ratios; yes as V1 coverage caveat when ratio is unavailable. |
| `provider_missing` | One provider lacks a field or block, reducing cross-provider confidence. | Not automatically; blocks only when the missing provider is needed to resolve uncertainty. | `providers_present`, provider quality summary, `fetch_status`, `errors`, `source_artifacts`, per-field missing category. | Mapping patch if provider should contain the field but canonical output drops it; otherwise document provider limitation. | Often yes. |
| `mapping_missing` | Source/provider appears to have relevant data, but canonical mapping does not expose it. | Yes for affected fields. | `source_endpoint`, `source_field`, `json_pointer`, `source_block`, `raw_block`, `source_trace`, `value`, expected canonical field. | Provider mapping patch is the primary follow-up. Official parser only if provider cannot expose the source field. | No, unless deferred to later scope. |
| `not_available` | No usable candidate value is available for this report version. | Yes for the absent field; no for unrelated fields. | `value`, `source_endpoint`, `source_provider`, `missing_category`, `manual_review_note`, provider support status. | Official parser, live provider, or sidecar may be needed depending on field type. | Usually yes. |

Current 600406 queue labels map into the canonical protocol as follows:

| Current queue label | Canonical review type |
| --- | --- |
| `valuation_as_of_date_review_required` | `valuation_as_of_date_review_required` |
| `business_composition_period_review_required` | `business_composition_period_review_required` |
| `main_business_review` | `main_business_review_required` |
| `business_composition_field_review` for `classification_type` | `classification_type_missing` |
| `business_composition_field_review` for `revenue_ratio` | `ratio_denominator_unclear` |
| `business_composition_field_review` for `gross_margin` | `ratio_denominator_unclear` plus period / type checks |
| `block_mapping_missing` | `mapping_missing` |
| `block_provider_missing` | `provider_missing` |
| `text_field_review` | field-specific manual review; usually low-priority unless it is `main_business` or a composition group label |
| `akshare_only_review` | provider coverage caveat unless confirmed by an accepted source |
| `low_confidence_candidates` | not a root cause; map to the underlying period, unit, source, mapping, or availability issue |

`source_conflict` and `unit_unknown` are not currently present in the 600406
summary counts, but they remain required protocol categories for future
candidate reports.

## 3. Review Action Design

Each queue item should become a review action with this conceptual shape:

```json
{
  "review_action_id": "600406-A1",
  "field_path": "valuation_metrics.as_of_date",
  "queue_item_type": "valuation_as_of_date_review_required",
  "scope": "valuation_metrics block",
  "metadata_to_check": ["as_of_date", "source_provider", "source_endpoint"],
  "decision_rule": "same valuation date required for PE, PB, and market_cap",
  "allowed_outcomes": ["confirmed_for_future_promotion", "keep_manual_review_required"],
  "promotion_effect": "eligibility only; no fixture write",
  "follow_up": null
}
```

### `valuation_metrics.as_of_date`

Action:

- verify the same valuation date for `pe_ttm`, `pb`, and `market_cap`;
- confirm that provider metadata carries that date for each valuation field;
- if the same date is confirmed, allow the valuation candidates to remain
  eligible for future promotion;
- if the date is unclear, keep `manual_review_required`;
- do not promote the valuation block without `as_of_date` clarity.

Possible outcomes:

- `confirmed_for_future_promotion`
- `keep_manual_review_required`
- `requires_provider_mapping_patch`
- `reject_candidate`

### `business_composition.period`

Action:

- verify the selected report period;
- verify the classification group;
- do not derive ratios across mixed product / region / industry groups;
- do not compare AkShare and Tushare rows as if they were automatically merged;
- if Tushare lacks reliable `type=P/D/I` or equivalent classification metadata,
  create a provider mapping follow-up;
- do not promote composition rows yet.

Possible outcomes:

- `keep_manual_review_required`
- `requires_provider_mapping_patch`
- `requires_official_parser`
- `coverage_caveat`

### `business_composition.classification_type`

Action:

- verify whether each row belongs to product, region, industry, or another
  stable source group;
- preserve the source group in review output;
- if the group is missing because canonical mapping omits provider type
  metadata, mark `requires_provider_mapping_patch`;
- if the provider cannot supply group semantics, mark `requires_official_parser`
  or `coverage_caveat`;
- do not promote segment rows whose group is unclear.

Possible outcomes:

- `requires_provider_mapping_patch`
- `requires_official_parser`
- `keep_manual_review_required`
- `coverage_caveat`

### `business_composition.revenue_ratio`

Action:

- verify numerator, denominator, report period, and classification group;
- ensure denominator scope is the group total for the same classification type;
- do not derive a product revenue ratio from a region or industry total;
- do not treat AkShare-only ratio coverage as reviewed ground truth;
- keep the field unpromoted until denominator clarity exists.

Possible outcomes:

- `confirmed_for_future_promotion`
- `keep_manual_review_required`
- `requires_provider_mapping_patch`
- `requires_official_parser`
- `reject_candidate`

### `business_composition.gross_margin`

Action:

- verify whether the value is directly sourced or derived;
- if derived, check `profit / revenue * 100`, source fields, period, and group;
- reject or keep manual review when revenue, profit, or group semantics are not
  aligned;
- do not use a mixed-period or mixed-group row for scoring or fixture promotion.

Possible outcomes:

- `confirmed_for_future_promotion`
- `keep_manual_review_required`
- `requires_provider_mapping_patch`
- `requires_official_parser`
- `reject_candidate`

### `main_business`

Action:

- require CNInfo, annual report, exchange disclosure, or official profile parser
  support before promotion;
- do not derive `main_business` from the largest business segment;
- allow display-only hints when clearly marked as unreviewed;
- keep `main_business` outside scoring unless reviewed official text is
  available.

Possible outcomes:

- `requires_official_parser`
- `keep_manual_review_required`
- `coverage_caveat`
- `reject_candidate`

### Block-Level Provider Or Mapping Items

Action:

- `mapping_missing`: inspect endpoint, source field, JSON pointer, and expected
  canonical field; produce a provider mapping patch follow-up instead of asking
  the user to fill all missing rows.
- `provider_missing`: decide whether the missing provider is required for this
  field. If not, record coverage caveat. If yes, defer until live provider or
  official parser.
- `not_available`: keep unavailable values out of fixture promotion and route to
  `defer_until_live_provider`, `defer_until_sidecar`, or `coverage_caveat`
  depending on field type.

### Source, Unit, And Period Items

Action:

- `source_conflict`: compare only after unit and period normalization; if the
  conflict is unresolved, reject or keep manual review.
- `unit_unknown`: require explicit `data_unit` and `canonical_unit`; otherwise
  keep manual review and consider provider mapping patch.
- `period_mismatch`: require same report period or same trade date for
  comparable fields; otherwise keep manual review or reject the candidate for
  promotion.

## 4. Review Outcome Enum

Review outcomes describe the decision produced by review. They do not write the
ground-truth fixture.

| Outcome | Meaning |
| --- | --- |
| `confirmed_for_future_promotion` | The candidate appears eligible for a later promote step, subject to accepted promote rules. |
| `keep_manual_review_required` | The issue remains unresolved and the field must stay out of reviewed fixture promotion. |
| `requires_provider_mapping_patch` | The source appears usable, but provider / canonical mapping must be patched before reliable promotion. |
| `requires_official_parser` | The field needs CNInfo, annual report, exchange disclosure, or official profile parsing. |
| `coverage_caveat` | The missing or weak field is a known coverage limitation, not a field to be manually filled now. |
| `reject_candidate` | The candidate is wrong, incomparable, stale, mixed-period, mixed-group, or otherwise unsuitable. |
| `defer_until_live_provider` | The offline artifact is insufficient; review must wait for an accepted live-provider path. |
| `defer_until_sidecar` | The field belongs to sidecar evidence such as commodity, domain operating evidence, customer/order validation, or other non-core data. |

Important boundaries:

- A review outcome is not fixture promotion.
- Promote to fixture must be a later, independent stage.
- Candidate reports cannot automatically modify fixture values.
- Unreviewed candidates must never enter the fixture.
- Even `confirmed_for_future_promotion` only means "eligible later", not
  "written now".

## 5. 600406 First-Round Review Plan

The first 600406 review round should be small and action-oriented.

### Priority A

1. `valuation_metrics.as_of_date`
   - Confirm same valuation date for `pe_ttm`, `pb`, and `market_cap`.
   - Expected decision: keep valuation candidates eligible only if same-date
     metadata is clear.

2. `business_composition.period`
   - Confirm selected report period and row grouping.
   - Expected decision: keep composition rows out of promotion until period and
     group semantics are resolved.

3. `business_composition.classification_type`
   - Confirm product / region / industry grouping.
   - Expected decision: likely `requires_provider_mapping_patch` if `fina_mainbz`
     type metadata is missing from canonical output.

4. `business_composition.revenue_ratio`
   - Confirm denominator scope and same-group ratio derivation.
   - Expected decision: do not promote ratio rows until denominator clarity
     exists.

### Priority B

1. `main_business`
   - Require CNInfo, annual report, or official profile parser before promotion.
   - Do not derive from max segment.
   - Display-only hint is allowed only when marked unreviewed and not used for
     scoring.

2. `business_composition.gross_margin`
   - Verify whether the value is directly sourced or derived.
   - Check same report period, same classification group, and numerator /
     denominator fields.
   - Keep out of promotion if classification type or period remains unclear.

### Priority C

1. AkShare-only text candidates
   - Keep as review material and coverage evidence.
   - Do not auto-accept in V1.

2. Low-confidence candidates
   - Do not inspect row by row.
   - Collapse into root causes: period, unit, provider, mapping, denominator,
     or unavailable source.

3. Other text identity fields
   - Review later only if they are needed for fixture promotion.
   - They are not the first bottleneck for the 600406 benchmark.

The 8 Tushare `auto_accepted_core_fields` are positive candidate-quality
evidence, but they are still not reviewed ground truth. Do not promote any field
until the review protocol and promote rules are accepted.

## 6. Relationship With Auto Fact Candidate Generator

The generator and review protocol have separate jobs:

- The generator automatically produces candidates and the
  `manual_review_priority_queue`.
- The review protocol converts that queue into executable review actions.
- The protocol does not change underlying candidates.
- The protocol does not change auto-accept rules.
- The protocol does not read tokens, fetch data, call providers, connect MCP, or
  inspect local provider secrets.
- The protocol may recommend later provider mapping, official parser, live
  provider, or sidecar follow-up work.

The generator remains an offline artifact candidate producer for this stage.
The protocol is the decision layer after report generation and before any later
promotion.

The review decisions artifact design is recorded in
`docs/FUNDAMENTAL_CANDIDATE_REVIEW_DECISIONS_ARTIFACT_DESIGN.md`. That artifact
materializes protocol-guided review actions as
`candidate_review_decisions.json`, but it still does not change candidate
reports, fixtures, provider outputs, scoring, P1.1, regression expected files,
or provider-primary behavior.

## 7. Relationship With Ground Truth Fixture

The fixture receives only fields that pass a later promote process. The review
protocol produces review decisions, not fixture writes.

Rules:

- Do not let `fact_candidates.json` write to the fixture.
- Do not let unreviewed candidates enter the fixture.
- Do not promote a field merely because it appears in
  `auto_accepted_core_fields`.
- Do not use the fixture as a manual data collection worksheet.
- Require a later promote-to-fixture stage that consumes review decisions and
  applies accepted promote rules.

## 8. Relationship With Validator

The validator remains delayed. It should run only after reviewed fixture fields
exist.

Current position:

- Do not write validator code in this stage.
- Do not validate unreviewed candidates as truth.
- Do not compare provider output against an unreviewed candidate report.
- Future validator input should be a reviewed fixture, not the raw candidate
  report.

## 9. Relationship With Product Experience

The intended product experience is:

- the system automatically fetches data;
- the system automatically generates candidate facts;
- the system automatically compresses abnormal or uncertain items into a review
  queue;
- the system tells the user "these few points need review";
- the user does not need to find full data manually;
- the user handles only the small number of issues the system cannot determine.

This keeps the product as an automated fundamental research analyst, not a
manual spreadsheet audit workflow.

## 10. Safety / Non-Goals

This stage explicitly does not:

- read `TUSHARE_TOKEN`;
- use the network;
- call Tushare;
- call AkShare;
- connect MCP;
- run real smoke;
- modify fixtures;
- write validator code;
- change tests;
- change pipeline, scoring, P1.1, or regression expected files;
- switch Tushare primary;
- automatically merge AkShare and Tushare;
- auto-accept drift;
- write provider raw artifacts, evidence packs, default outputs, or reports;
- output buy / sell advice, target prices, position sizing, portfolio weights,
  or any trading recommendation.

Recommended stages after review protocol and review-decision design acceptance:

1. Implement the `review decisions artifact`.
2. Generate `600406` `candidate_review_decisions.json`.
3. Accept the review decisions artifact.
4. Then design promote rules.
5. Then consider controlled fixture promotion.
6. Then design and implement the validator.

Do not directly promote candidates to the fixture from this protocol, and do
not write a validator before reviewed fixture fields exist.
