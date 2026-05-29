# Fundamental Candidate Review Decisions Artifact Design

Date: 2026-05-27

Stage: Fundamental Skill Candidate Review Decisions Artifact Design.

Status: design-only. This document does not implement code, does not modify
tests, fixtures, pipeline, scoring, Research Intelligence P1.1, regression
expected files, provider-primary behavior, default output, provider raw
artifacts, evidence packs, or generated candidate reports. It does not run
smoke tests, read `TUSHARE_TOKEN`, use the network, call Tushare or AkShare,
connect MCP, promote fixture values, automatically merge providers, or output
investment advice.

Current context:

- Offline Auto Fact Candidate Generator V1.1 is implemented and accepted.
- The `600406` V1.1 `fact_candidates.json` has been generated and passed
  usability review / audit.
- Candidate Report Review Protocol Design is recorded and accepted in
  `docs/FUNDAMENTAL_CANDIDATE_REPORT_REVIEW_PROTOCOL_DESIGN.md`.
- This stage designs the intermediate `candidate_review_decisions.json`
  artifact only.
- Promote rules, controlled fixture promotion, and validator design remain
  later independent stages.

## 1. Artifact Goal

`candidate_review_decisions.json` is the intermediate layer between a candidate
report and future promote rules.

Its job is to record review decisions for selected
`manual_review_priority_queue` items. It turns the Review Protocol into an
auditable decision record.

Required boundaries:

- It records what was reviewed, which metadata was checked, what decision was
  reached, and what follow-up is needed.
- It does not write the ground-truth fixture.
- It does not modify `fact_candidates.json`.
- It does not modify provider output.
- It does not change scoring, Research Intelligence P1.1, regression expected
  files, tests, or pipeline behavior.
- It does not switch provider primary behavior.
- It does not merge AkShare and Tushare outputs.
- It does not output buy / sell advice, target price, position sizing,
  portfolio weight, or any trading recommendation.

Important distinction:

- A review decision is not a ground-truth fixture value.
- A review decision is not fixture promotion.
- `confirmed_for_future_promotion` means only that a candidate may become
  eligible input to a later promote-rule stage.
- `eligible_for_future_promotion=true` is not permission to write a fixture.
- `fixture_write_allowed` must always be `false` in V1.

## 2. Inputs

Design-time inputs:

- `fact_candidates.json`
- `manual_review_priority_queue`
- Candidate Report Review Protocol
- Optional reviewer note

The first implementation may be based on:

```text
output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json
```

This design stage does not read that runtime artifact, does not parse it, and
does not write any runtime output.

Conceptual input contracts:

- `fact_candidates.json` provides candidate values, source trace, period, unit,
  confidence, review status, conflict status, and candidate summary.
- `manual_review_priority_queue` identifies the small number of high-priority
  items that need review attention.
- The Review Protocol maps raw queue labels into canonical review categories,
  review actions, allowed outcomes, and follow-up classes.
- Reviewer notes may explain a judgement, but must not contain credentials,
  secret paths, MCP URLs, large paid-source excerpts, or investment advice.

## 3. Output Path Design

Future runtime output path:

```text
output/ground_truth_candidate_reviews/<timestamp>/<code>/candidate_review_decisions.json
```

Runtime output rules:

- Runtime review artifacts stay out of git.
- The artifact must not write the ground-truth fixture.
- The artifact must not write default production output.
- The artifact must not write regression expected files.
- The artifact must not write `evidence_pack`.
- The artifact must not write provider raw artifacts.
- The artifact must not overwrite or mutate `fact_candidates.json`.

Optional git-safe example fixture path:

```text
tests/fixtures/ground_truth/review_decision_examples/600406_candidate_review_decisions.example.json
```

An example fixture may enter git only if it contains no real token, no MCP URL,
no paid-source long excerpt, no local secret path, no local machine-specific
absolute path, and no provider raw dump. This design stage does not create that
fixture.

## 4. Decision Schema

Recommended top-level shape:

```json
{
  "version": "candidate_review_decisions.v1",
  "code": "600406",
  "created_at": "YYYY-MM-DDTHH:MM:SS",
  "source_candidate_report": "fact_candidates.json",
  "review_mode": "protocol_guided_review",
  "decisions": [],
  "summary": {}
}
```

Recommended full top-level fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `version` | Yes | Must be `candidate_review_decisions.v1` for V1 artifacts. |
| `code` | Yes | A-share stock code, for example `600406`. |
| `created_at` | Yes | Artifact creation timestamp. |
| `source_candidate_report` | Yes | Reference to the candidate report filename or sanitized relative reference. |
| `source_candidate_report_digest` | Optional | Future non-secret digest for traceability. Not required in V1 design. |
| `review_mode` | Yes | V1 value: `protocol_guided_review`. |
| `review_protocol_version` | Optional | Human-readable reference to the accepted review protocol version. |
| `decisions` | Yes | Array of decision records. |
| `summary` | Yes | Counts and next-stage recommendation. |

Each decision should include at least:

```json
{
  "decision_id": "600406-A1",
  "field_path": "valuation_metrics.as_of_date",
  "queue_item_type": "valuation_as_of_date_review_required",
  "source_queue_priority": "A",
  "related_candidate_ids": [],
  "representative_candidates": [],
  "review_action": "check_same_valuation_date_metadata",
  "metadata_checked": [
    "as_of_date",
    "source_provider",
    "source_endpoint",
    "source_trace",
    "canonical_unit"
  ],
  "decision_outcome": "keep_manual_review_required",
  "decision_reason": "Same-date valuation metadata is required before any later promotion.",
  "follow_up_type": "manual_review_later",
  "follow_up_detail": "Review PE, PB, and market_cap only when same-date metadata is explicit.",
  "eligible_for_future_promotion": false,
  "fixture_write_allowed": false,
  "reviewed_by": "reviewer_id_or_role",
  "reviewed_at": "YYYY-MM-DDTHH:MM:SS",
  "confidence_after_review": "low",
  "not_for_trading_advice": true
}
```

Decision field rules:

- `decision_id` should be stable inside one artifact. Recommended pattern:
  `<code>-<priority><sequence>`, for example `600406-A1`.
- `field_path` must match the candidate report field path when possible.
- `queue_item_type` should use the canonical Review Protocol type.
- `source_queue_priority` should preserve the queue priority or review plan
  priority such as `A`, `B`, or `C`.
- `related_candidate_ids` should be used when the generator emits stable
  candidate IDs.
- `representative_candidates` may be used when V1 candidate IDs are absent.
  It should contain sanitized references, not raw provider dumps.
- `review_action` names the review action performed or planned.
- `metadata_checked` records the metadata categories actually checked or
  required by the decision.
- `decision_outcome` must use the enum in section 5.
- `decision_reason` should be concise and auditable.
- `follow_up_type` must use the enum in section 7.
- `follow_up_detail` should explain what later stage should do.
- `eligible_for_future_promotion` means only "eligible for later promote-rule
  consideration".
- `fixture_write_allowed` must be `false` in every V1 decision.
- `reviewed_by` may be a human reviewer alias or system role, but must not
  contain credentials.
- `confidence_after_review` should be one of `high`, `medium`, `low`, or
  `unavailable`.
- `not_for_trading_advice` must be `true`.

## 5. Decision Outcome Enum

V1 uses the Review Protocol outcome enum:

| Outcome | Meaning |
| --- | --- |
| `confirmed_for_future_promotion` | The reviewed candidate appears eligible for a later promote-rule stage, subject to separate promote rules. |
| `keep_manual_review_required` | The issue remains unresolved; the candidate must stay out of fixture promotion. |
| `requires_provider_mapping_patch` | The source appears usable, but provider or canonical mapping must be fixed first. |
| `requires_official_parser` | The field needs CNInfo, annual report, exchange disclosure, or official profile parser support. |
| `coverage_caveat` | The gap is a known coverage limitation rather than a field to manually fill now. |
| `reject_candidate` | The candidate is wrong, stale, incomparable, mixed-period, mixed-group, or otherwise unsuitable. |
| `defer_until_live_provider` | Offline artifacts are insufficient; wait for an accepted live-provider path. |
| `defer_until_sidecar` | The field belongs to sidecar evidence, such as commodity, customer, order, or domain operating evidence. |

Outcome boundaries:

- An outcome cannot directly write the fixture.
- `confirmed_for_future_promotion` is not fixture promotion.
- `eligible_for_future_promotion=true` is only input for later promote rules.
- `fixture_write_allowed` must always be `false` in V1.
- If a future design wants review decisions to authorize fixture writes, that
  must be a separate design, implementation, and acceptance cycle.

## 6. `600406` First-Version Decision Plan

The first `600406` decision artifact should be small. It should cover the
highest-value queue items from the Review Protocol and avoid row-by-row review
of the entire candidate report.

### Priority A

| Field path | Review action | Metadata checked | Likely outcome | Follow-up type | Eligible for future promotion | Why it cannot directly write fixture |
| --- | --- | --- | --- | --- | --- | --- |
| `valuation_metrics.as_of_date` | `check_same_valuation_date_metadata` | `as_of_date`, `source_provider`, `source_endpoint`, `source_trace`, row selector, valuation fields covered by the same date. | `confirmed_for_future_promotion` if PE, PB, and market cap share explicit same-date metadata; otherwise `keep_manual_review_required` or `requires_provider_mapping_patch`. | `none` if confirmed; otherwise `provider_mapping_patch` or `manual_review_later`. | Conditional. `true` only when same-date metadata is explicit. | Valuation is trade-date sensitive, promote rules are not designed, and V1 decisions cannot authorize fixture writes. |
| `business_composition.period` | `check_selected_period_and_row_grouping` | `report_period`, `source_period`, `classification_type`, `segment_name`, `row_selector`, `source_endpoint`, `source_provider`, `denominator_scope`. | Usually `keep_manual_review_required`; may become `requires_provider_mapping_patch` or `requires_official_parser`. | `provider_mapping_patch`, `official_parser_needed`, or `manual_review_later`. | Usually `false` until period and group semantics are explicit. | Segment rows can be mixed across periods or groups; no promotion can happen before grouping rules are accepted. |
| `business_composition.classification_type` | `check_composition_classification_type` | Provider type such as `P` / `D` / `I`, source endpoint, segment name, row selector, report period, canonical classification mapping. | Likely `requires_provider_mapping_patch` when provider type metadata exists but canonical output omits it; otherwise `requires_official_parser` or `coverage_caveat`. | `provider_mapping_patch` or `official_parser_needed`. | `false` until type metadata is reliable. | Product, region, and industry rows cannot be compared or promoted interchangeably. |
| `business_composition.revenue_ratio` | `check_ratio_denominator_scope` | Numerator source, denominator source, `derived`, `derivation_method`, `denominator_scope`, report period, classification group, source trace. | `keep_manual_review_required` unless denominator scope is explicit; may require mapping patch or official parser. | `provider_mapping_patch`, `official_parser_needed`, or `manual_review_later`. | Conditional, but likely `false` in first artifact if denominator scope remains unclear. | A ratio without clear same-period, same-group denominator is not a reviewed fact. |

### Priority B

| Field path | Review action | Metadata checked | Likely outcome | Follow-up type | Eligible for future promotion | Why it cannot directly write fixture |
| --- | --- | --- | --- | --- | --- | --- |
| `main_business` | `check_official_business_text_source` | `source_provider`, `source_endpoint`, `source_trace`, text freshness, official report / CNInfo / exchange / official profile availability. | Likely `requires_official_parser` or `coverage_caveat`; may remain `keep_manual_review_required`. | `official_parser_needed` or `coverage_caveat`. | `false` until official text is reviewed. | Narrative text must not be derived from largest segment rows and needs official-source support before fixture promotion. |
| `business_composition.gross_margin` | `check_margin_source_or_derivation` | Direct source flag, `derived`, profit, revenue, formula, report period, classification group, unit, source trace. | `keep_manual_review_required` until period and type are clear; may be `confirmed_for_future_promotion` only if direct or correctly derived metadata is complete. | `manual_review_later`, `provider_mapping_patch`, or `official_parser_needed`. | Conditional; likely `false` until composition period/type decisions are resolved. | Gross margin can be invalid if mixed across periods, groups, numerator, or denominator definitions. |

Recommended first artifact behavior:

- Create one decision per Priority A field path.
- Create one decision per Priority B field path only if review capacity permits.
- Do not create low-value row-by-row decisions for all low-confidence
  candidates.
- Collapse low-confidence detail into follow-up classes: provider mapping,
  official parser, live provider, sidecar, coverage caveat, reject, or later
  manual review.

## 7. Follow-Up Type Enum

Recommended V1 follow-up enum:

| Follow-up type | Meaning |
| --- | --- |
| `none` | No additional follow-up is needed before later promote-rule consideration. |
| `provider_mapping_patch` | Provider or canonical mapping should expose source field, unit, period, type, row selector, or denominator metadata. |
| `official_parser_needed` | CNInfo, annual report, exchange disclosure, or official profile parser support is needed. |
| `live_provider_needed` | Offline artifact review is insufficient; wait for guarded live-provider execution. |
| `sidecar_needed` | The field belongs to separate sidecar evidence rather than core financial candidate review. |
| `coverage_caveat` | Record a limitation and keep the field outside direct promotion for now. |
| `reject` | Candidate should be rejected or excluded from later promotion. |
| `manual_review_later` | The item is not resolved in this review round and should remain queued. |

The enum is intentionally operational. It tells the next stage what kind of
work is needed without asking the user to manually fill a full benchmark table.

## 8. Summary Design

Recommended `summary` shape:

```json
{
  "total_decisions": 0,
  "confirmed_for_future_promotion_count": 0,
  "keep_manual_review_required_count": 0,
  "requires_provider_mapping_patch_count": 0,
  "requires_official_parser_count": 0,
  "coverage_caveat_count": 0,
  "rejected_count": 0,
  "defer_until_live_provider_count": 0,
  "defer_until_sidecar_count": 0,
  "fixture_write_allowed_count": 0,
  "eligible_for_future_promotion_count": 0,
  "next_recommended_stage": "review_decisions_artifact_acceptance"
}
```

Summary rules:

- `total_decisions` must equal the length of `decisions`.
- Outcome counts must be derived from `decision_outcome`.
- `rejected_count` counts `reject_candidate`.
- `fixture_write_allowed_count` must be `0` in V1.
- `eligible_for_future_promotion_count` may be non-zero, but it still does not
  permit fixture writes.
- `next_recommended_stage` should normally be one of:
  `review_decisions_artifact_acceptance`, `promote_rule_design`,
  `provider_mapping_patch_design`, `official_parser_design`, or
  `manual_review_later`.

## 9. Relationship With Promote Rules

The review decisions artifact is input to future promote rules. Promote rules
are not designed in this stage.

Required relationship:

- Promotion must be a later independent stage.
- Promotion cannot happen directly from `fact_candidates.json`.
- Promotion cannot happen from an unreviewed decision.
- Promotion cannot happen merely because a candidate is auto-accepted in the
  candidate report.
- Promotion cannot happen merely because a review decision says
  `confirmed_for_future_promotion`.
- Promotion must inspect `eligible_for_future_promotion`, `decision_outcome`,
  `metadata_checked`, `confidence_after_review`, and follow-up status.
- Promotion must check the V1 boundary that `fixture_write_allowed=false`.
- Any future change that lets review decisions authorize fixture writes must be
  separately designed and accepted.

Practical implication:

```text
fact_candidates.json
  -> candidate_review_decisions.json
  -> future promote rules
  -> future controlled fixture promotion artifact
  -> reviewed ground-truth fixture
```

The fixture must not be written by the candidate report or by the review
decision artifact.

## 10. Relationship With User Experience

The intended user experience is still an automated fundamental research
analyst, not an audit spreadsheet.

Workflow:

- The system generates the candidate report.
- The system generates the manual review priority queue.
- The Review Protocol converts the queue into a few review actions.
- `candidate_review_decisions.json` records the results of those review
  actions.
- The user handles only the small number of issues the system cannot determine:
  period, unit, source conflict, classification group, denominator, provider
  mapping, official source availability, sidecar need, or coverage caveat.
- Later promote rules decide whether reviewed candidates can enter the fixture.

The user should not need to find full financial data manually, fill all fields
by hand, compare every candidate row, or treat the ground-truth fixture as a
data-entry surface.

## 11. Safety / Non-Goals

This stage explicitly does not:

- read `TUSHARE_TOKEN`;
- use the network;
- call Tushare;
- call AkShare;
- connect MCP;
- run real smoke;
- read runtime artifacts;
- write runtime output;
- write fixtures;
- write validator code;
- modify tests;
- modify scoring, Research Intelligence P1.1, pipeline, or regression
  expected files;
- switch provider primary behavior;
- automatically merge AkShare and Tushare;
- auto-accept drift;
- write `evidence_pack`;
- write provider raw artifacts;
- write default output;
- output buy / sell advice, target prices, position sizing, portfolio weights,
  or any trading recommendation.

## 12. Roadmap

Recommended sequence:

1. This design document.
2. Review decisions artifact implementation.
3. Generate `600406` `candidate_review_decisions.json`.
4. Review decisions artifact acceptance.
5. Promote-rule design.
6. Controlled fixture promotion.
7. Validator design and implementation only after reviewed fixture fields
   exist.

Do not skip directly from `fact_candidates.json` to fixture promotion. Do not
write a validator before reviewed fixture fields exist.

## 13. Official Candidate Bridge Relationship

The official candidate payload -> provider-centric `fact_candidates.json`
bridge design is recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_CANDIDATE_PAYLOAD_TO_FACT_CANDIDATES_BRIDGE_DESIGN.md
```

Future `candidate_review_decisions.json` artifacts may reference both provider
candidates and official disclosure candidates. To avoid ambiguity, decision
records should include:

- `source_type`;
- `candidate_id`;
- `artifact_ref`;
- optional `artifact_digest`;
- `field_path`;
- `period`;
- `unit`.

Review decisions remain an audit layer only:

- an official candidate decision is not fixture promotion;
- an official candidate decision is not a verified fact;
- `fixture_write_allowed` remains `false` in V1;
- official candidates do not overwrite provider candidates;
- provider / official conflicts remain manual-review items;
- promotion rules remain a later independent stage.

Current recommended next stage for official candidates:

```text
Candidate Review Decisions Update Design For Bridge Sources
```

Do not proceed directly to Research Report V1 integration, fixture promotion,
validator work, live CNInfo, provider calls, token reads, MCP, scoring / P1.1
changes, regression expected changes, or trading advice.

## 14. Candidate Source Bridge Runtime Acceptance Sync

The `candidate_source_bridge.v1` implementation and retained `600406` runtime
baseline are accepted and frozen in:

```text
docs/FUNDAMENTAL_CANDIDATE_SOURCE_BRIDGE_RUNTIME_ACCEPTANCE_SUMMARY.md
```

The accepted bridge baseline indexes:

- provider candidates from
  `output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json`
  with counts `1004 / 184 / 807`;
- official disclosure candidates from
  `output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json`
  with counts `7 / 7 / 0`;
- the new UTF-8-correct bridge artifact at
  `output/candidate_source_bridges/20260529T034024Z/600406/candidate_source_bridge_review.json`;
- `company_name="国电南瑞"` with codepoints
  `[22269, 30005, 21335, 29790]`;
- `cross_source_conflicts=[]`;
- `review_priorities=8`, including the schema-mismatch caveat
  `cross_source_conflict_detection_not_performed_schema_mismatch`.

Next review-decision design work should define how
`candidate_review_decisions.json` references both source families using:

- `source_type`;
- `candidate_id`;
- `artifact_ref`;
- optional `artifact_digest`;
- `field_path`;
- `period`;
- `unit`;
- review outcome and caveat status.

This update remains a design boundary only. Review decisions are not fixture
promotion, are not verified facts, do not overwrite provider candidates, do not
rewrite official candidate payloads, and do not enter Research Report V1.
Promotion rules remain later.

Current recommended next stage for official candidates:

```text
Candidate Review Decisions Update Design For Bridge Sources
```

## 15. Bridge Sources Review Decision Addendum

The bridge-sources update design is now recorded in:

```text
docs/FUNDAMENTAL_CANDIDATE_REVIEW_DECISIONS_BRIDGE_SOURCES_DESIGN.md
```

It extends the V1 review-decision design boundary to support three source
families without changing implementation in this documentation-only stage:

- `provider_candidates`;
- `official_disclosure_candidates`;
- `bridge_review_priority`.

Bridge-aware decision records should preserve:

- `source_type`;
- `candidate_id`;
- `artifact_ref`;
- optional `bridge_ref`;
- `field_path`;
- `period`;
- `unit`;
- decision enum;
- review status;
- follow-up class;
- caveats;
- `not_for_trading_advice=true`.

The bridge-sources decision enum is:

- `accepted_for_report_candidate`;
- `manual_review_required`;
- `blocked_by_caveat`;
- `rejected`;
- `needs_more_evidence`;
- `conflict_requires_review`.

`accepted_for_report_candidate` is only an evidence-readiness decision for a
later Report V1 L1 evidence design. It is not a verified fact, not fixture
promotion, not an accepted manifest update, not a scoring / P1.1 change, and
not trading advice.

The next recommended stage is:

```text
Bridge-aware review decisions implementation
```
