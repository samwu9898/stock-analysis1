# Fundamental Candidate Review Decisions Bridge Sources Design

Date: 2026-05-29

Stage: Fundamental Skill Candidate Review Decisions Update Design For Bridge
Sources.

Status: documentation-only design. This stage does not write code, modify
tests, generate runtime output, write fixtures, update accepted manifests,
change orchestration / CLI, change the candidate generator main path, implement
review decisions, connect Research Report V1, modify pipeline / scoring / P1.1
behavior, change regression expected files, call providers, read tokens,
connect MCP, use the network, run smoke, or provide trading advice.

Latest accepted verification results are quoted for continuity only and are
not rerun by this documentation-only stage:

- targeted tests `549 passed`;
- full pytest latest `1197 passed, 1 skipped`;
- regression `passed=47 failed=0 total=47`.

## 1. Positioning

This is the post-bridge `candidate_review_decisions.json` design for multiple
candidate fact sources:

- provider candidates;
- official disclosure candidates;
- `candidate_source_bridge.v1`.

It is not:

- fixture promotion;
- verified fact generation;
- Research Report V1 integration;
- a provider primary switch;
- an accepted manifest update;
- a validator;
- live CNInfo;
- live provider access;
- trading advice.

The goal is to let review decisions reference provider candidates, official
disclosure candidates, and bridge review priorities while preserving source
lineage.

Required boundaries:

- review decisions can reference provider candidates;
- review decisions can reference official disclosure candidates;
- review decisions can reference the bridge artifact;
- each decision preserves `source_type`, `candidate_id`, and `artifact_ref`;
- bridge-backed decisions can preserve `bridge_ref`;
- caveats and review status remain explicit;
- a review decision is not a verified fact;
- a review decision is not fixture promotion;
- `not_for_trading_advice` must stay `true`.

## 2. Current Input Sources

This design is anchored on the retained `600406` runtime baseline. The artifacts
below are design references only in this stage.

Provider candidates:

```text
output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json
```

Provider records:

- candidate count `1004`;
- manual review count `184`;
- blocked count `807`;
- provider-centric schema remains unchanged.

Official disclosure candidates:

```text
output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json
```

Official records:

- candidate rows `7`;
- all rows are L1 official disclosure candidates;
- all rows remain human-review / caveated;
- no official candidate is a verified fact;
- official payload remains independent from provider-centric
  `fact_candidates.json`.

Bridge:

```text
output/candidate_source_bridges/20260529T034024Z/600406/candidate_source_bridge_review.json
```

Bridge records:

- `version=candidate_source_bridge.v1`;
- bridge has provider and official source entries;
- bridge has `review_priorities=8`;
- bridge has no deep cross-source conflict matching yet;
- current lack of deep conflicts is due to schema mismatch, not proof of
  agreement.

## 3. Review Decision Reference Schema

Bridge-aware review decisions need a source reference shape that can point to
provider candidate rows, official disclosure candidate rows, or bridge review
priority entries without merging the underlying artifacts.

Recommended decision reference shape:

```json
{
  "decision_id": "",
  "source_type": "provider_candidates",
  "candidate_id": "",
  "artifact_ref": "",
  "bridge_ref": "",
  "field_path": "",
  "period": "",
  "unit": "",
  "decision": "",
  "decision_reason": "",
  "review_status": "",
  "follow_up_class": "",
  "caveats": [],
  "not_for_trading_advice": true
}
```

`source_type` must at least support:

- `provider_candidates`;
- `official_disclosure_candidates`;
- `bridge_review_priority`.

Field rules:

- `decision_id` is stable inside one review-decision artifact.
- `source_type` identifies the referenced source family, not factual truth.
- `candidate_id` is required for provider and official candidate decisions.
- `artifact_ref` is a local relative reference to the source artifact.
- `bridge_ref` is required when `source_type=bridge_review_priority` and may
  point to a bridge `priority_id` or future conflict id.
- `field_path` should use the candidate field path when available.
- `period` and `unit` should preserve source metadata and may stay empty only
  when the source candidate lacks the concept.
- `decision` must use the enum in section 4.
- `review_status` records review workflow state, not verified fact status.
- `follow_up_class` records the next operational action.
- `caveats` must preserve candidate caveats and bridge caveats.
- `not_for_trading_advice` must be `true`.

For future cross-source support decisions, the reference may include related
source refs without creating a merged candidate:

```json
{
  "decision_id": "600406-ms-001",
  "source_type": "bridge_review_priority",
  "candidate_id": "",
  "artifact_ref": "output/candidate_source_bridges/20260529T034024Z/600406/candidate_source_bridge_review.json",
  "bridge_ref": "priority_id_or_conflict_id",
  "field_path": "business_composition.revenue",
  "period": "2025H1",
  "unit": "CNY",
  "decision": "manual_review_required",
  "decision_reason": "Provider and official candidates should be compared by period, unit, denominator, and source trace before report use.",
  "review_status": "pending_human_review",
  "follow_up_class": "cross_source_review",
  "caveats": [
    "multi_source_support_candidate_not_verified"
  ],
  "related_source_refs": [
    {
      "source_type": "provider_candidates",
      "candidate_id": "",
      "artifact_ref": "output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json"
    },
    {
      "source_type": "official_disclosure_candidates",
      "candidate_id": "",
      "artifact_ref": "output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json"
    }
  ],
  "not_for_trading_advice": true
}
```

## 4. Decision Status Rules

Allowed `decision` values:

| Decision | Meaning |
| --- | --- |
| `accepted_for_report_candidate` | Reviewed as potentially suitable report evidence input, subject to later report evidence integration. |
| `manual_review_required` | Source remains unresolved and needs human review before stronger use. |
| `blocked_by_caveat` | Caveats prevent the candidate from being accepted as report evidence input. |
| `rejected` | Candidate is wrong, stale, incomparable, or not useful for the reviewed field. |
| `needs_more_evidence` | Existing source trace is insufficient and another source or parser is needed. |
| `conflict_requires_review` | Provider and official sources conflict or cannot be reconciled automatically. |

Decision boundaries:

- `accepted_for_report_candidate` is not a verified fact.
- `accepted_for_report_candidate` does not write a fixture.
- `accepted_for_report_candidate` does not update an accepted manifest.
- `accepted_for_report_candidate` does not change scoring, P1.1, pipeline
  behavior, or regression expected files.
- `accepted_for_report_candidate` does not directly enter Research Report V1.
- `accepted_for_report_candidate` does not become trading advice.
- No decision value authorizes fixture promotion.
- No decision value authorizes provider primary changes.
- No decision value authorizes live provider or CNInfo calls.

Suggested `review_status` values for future implementation:

- `pending_human_review`;
- `reviewed_caveated`;
- `reviewed_rejected`;
- `reviewed_candidate_ready`;
- `reviewed_conflict_open`;
- `deferred`.

These workflow statuses also do not represent verified facts.

## 5. Provider Vs Official Review Logic

Review policy:

- An official L1 candidate with complete source trace can be prioritized for
  review over provider-only candidates.
- Official `structured_medium` extraction confidence still requires manual
  review.
- If a provider auto candidate and an official L1 candidate agree on field,
  value, period, unit, denominator, and source lineage, the decision may mark
  the item as a multi-source support candidate.
- Multi-source support does not automatically become verified.
- Provider / official conflicts must enter manual review.
- Denominator, period, unit, row group, or segment classification mismatch must
  enter manual review.
- Caveat-only official evidence can record a caveat, but must not enter
  `accepted_for_report_candidate`.
- Source lineage mismatch must be blocked.
- Official candidates do not overwrite Tushare, AkShare, or other provider
  candidates.
- Provider candidates do not erase official caveats.

Decision mapping guidance:

- Complete official L1 trace plus no caveats may become
  `accepted_for_report_candidate` only after human review.
- Official L1 trace with `structured_medium`, missing page anchor, table caveat,
  or extraction caveat should remain `manual_review_required` or
  `blocked_by_caveat`.
- Provider-only candidate with weak source trace should remain
  `manual_review_required`, `needs_more_evidence`, or `blocked_by_caveat`.
- Provider-official agreement can reduce review priority after human review,
  but cannot skip review.
- Any mismatch that changes interpretation should use
  `conflict_requires_review`.

## 6. Bridge Review Priorities

The bridge `review_priorities[]` array can be used as review queue input.

Priority rules:

- `high`, `medium`, and `low` affect review order only.
- Priority is not factual truth.
- Priority is not fixture promotion.
- Priority is not report acceptance.
- Priority is not provider primary precedence.
- Priority is not trading advice.

Bridge priority classes:

- schema mismatch caveat priorities should become framework / schema follow-up
  tasks;
- official candidate priorities should become official evidence review tasks;
- provider candidate priorities should remain provider candidate review tasks;
- cross-source priorities should preserve both source refs when available;
- bridge priorities with insufficient source refs should become
  `needs_more_evidence` or `manual_review_required`.

The current bridge includes the schema-mismatch caveat
`cross_source_conflict_detection_not_performed_schema_mismatch`. A
review-decision implementation should preserve that caveat as a framework /
schema follow-up rather than interpreting `cross_source_conflicts=[]` as source
agreement.

## 7. Cross-Source Conflict Handling

Current state:

- the bridge currently has no deep conflicts because deep matching was not
  performed across mismatched schemas;
- `cross_source_conflicts=[]` means no emitted conflict entries, not no
  disagreement in the underlying evidence;
- future implementation may produce explicit conflict entries.

Future conflict decision requirements:

- conflict decisions must preserve provider refs;
- conflict decisions must preserve official refs;
- conflict decisions must preserve `artifact_ref` for each source;
- conflict decisions must preserve `candidate_id` for each source when
  available;
- conflict decisions must record `field_path`, `period`, `unit`, denominator,
  value comparison, and caveats when available;
- conflicts must enter manual review.

Conflict boundaries:

- a conflict does not change provider primary behavior;
- a conflict does not write a report;
- a conflict does not write a fixture;
- a conflict does not update accepted manifests;
- a conflict does not alter scoring / P1.1 / regression expected files;
- a conflict does not become trading advice.

## 8. Relation To Research Report V1

Research Report V1 must not directly read review decisions as verified facts.

Allowed relationship:

- review decisions can provide an evidence readiness signal;
- review decisions can identify official L1 candidates that may be considered
  by a later report evidence design;
- review decisions can carry caveats that a later report integration may
  surface as caveats.

Forbidden relationship in this stage:

- no automatic report rewrite;
- no direct Report V1 ingestion of review decisions as report truth;
- no direct Report V1 ingestion of bridge priorities as report truth;
- no buy / sell advice;
- no target price;
- no position sizing;
- no portfolio weight;
- no trading signal.

Later L1 evidence integration for Research Report V1 must be a separate design,
implementation, and acceptance stage.

## 9. Relation To Fixture Promotion / Validator

Review decisions are not fixture promotion.

Promotion / validator boundaries:

- promotion rules are later;
- validator work is later;
- ground truth fixtures are not written in this stage;
- accepted manifests are not updated in this stage;
- regression expected files are not changed in this stage;
- `accepted_for_report_candidate` is not permission to write a fixture;
- `reviewed_candidate_ready` is not permission to write a fixture;
- `not_for_trading_advice=true` remains required.

Future promotion design, if accepted later, must consume review decisions as
inputs only after separate promotion rules validate source lineage, caveats,
period, unit, denominator, and field semantics.

## 10. Safety / Validation

Future implementation must validate:

- artifact refs are local relative paths;
- artifact refs point to ignored or otherwise allowed runtime artifact
  locations;
- `source_type` is one of the allowed values;
- `candidate_id` is non-empty for provider and official candidate refs;
- `decision` uses the allowed enum;
- `not_for_trading_advice=true`;
- caveats are preserved;
- no token appears;
- no Bearer string appears;
- no MCP URL appears;
- no `.env` reference appears;
- no local secret path appears;
- no trading recommendation keys appear;
- no verified fact key appears;
- no automatic fixture write flag appears.

Recommended hard blocks:

- absolute local secret paths;
- provider credentials;
- raw paid-source dumps;
- `fixture_write_allowed=true`;
- `review_status=verified`;
- `auto_verified=true`;
- report recommendation keys such as target price, position size, buy / sell,
  portfolio weight, or trading signal;
- source lineage mismatch;
- period, unit, or denominator mismatch for quantitative fields;
- bridge priority records with no source reference and no caveat.

## 11. Roadmap

Recommended sequence:

1. Candidate review decisions bridge-sources design.
2. Bridge-aware review decisions implementation.
3. Retained `600406` review decisions runtime review.
4. Candidate schema v2 design.
5. Research Report V1 L1 evidence integration design.
6. Fixture promotion / validator later.
7. Live CNInfo later.

Do not skip directly to Research Report V1 integration, fixture promotion,
validator work, live CNInfo, provider calls, token reads, MCP, scoring / P1.1
changes, regression expected changes, or trading advice.
