# Fundamental Official Candidate Payload To Fact Candidates Bridge Design

Stage: Fundamental Skill Official Candidate Payload To Provider-Centric Fact
Candidates Bridge Design.

Status: documentation-only design. This stage does not write code, tests,
fixtures, runtime output, accepted manifests, scoring / P1.1 / regression
expected files, candidate generator main-path changes, Research Report V1
integration, provider calls, token reads, network access, MCP integration, or
trading advice.

## 1. Positioning

This design defines how the independent
`official_disclosure_fact_candidates.v1` payload can coexist with, or be
referenced by, the existing provider-centric `fact_candidates.json` artifact.

It is not:

- a direct candidate generator main-path change;
- Research Report V1 integration;
- fixture promotion;
- a validator;
- an accepted manifest update;
- a provider primary switch;
- live CNInfo;
- live Tushare;
- AkShare or other provider access;
- MCP;
- trading advice.

The goal is to:

- let official candidates become visible to the existing candidate-fact chain;
- avoid polluting the current provider-centric candidate schema;
- preserve official source trace;
- preserve caveats and human-review status;
- avoid upgrading official candidates into verified facts;
- avoid automatically overwriting Tushare / AkShare candidates.

## 2. Current Schema Constraints

The current `fact_candidates.json` artifact is provider-centric.

Provider candidate rows depend on fields such as:

- `source_provider`;
- `source_artifact`;
- `source_block`;
- `source_endpoint`;
- `source_trace`;
- provider-oriented period / unit / confidence / conflict metadata.

The official candidate payload uses a different source model:

- `source_type=official_disclosure`;
- `evidence_tier=L1_official_disclosure`;
- source document trace;
- source section / page-or-anchor trace;
- table id / row / column / `source_column_map` trace;
- official extraction confidence;
- candidate caveats and integration warnings.

Directly appending official rows into provider-centric `fact_candidates.json`
would either require many optional provider fields to become empty, or require
provider-focused consumers to understand official-only trace fields. That would
pollute the schema and could break provider-centric tests or review tooling.

Therefore the previous runtime stage correctly avoided a merge function. The
accepted output remains an independent official candidate payload, not a
provider-centric `fact_candidates.json`.

## 3. Bridge Options

### Option A: Extend Unified `fact_candidates.json`

Description:

- keep one candidate pool;
- add `source_type`;
- add `evidence_tier`;
- add official trace fields;
- add an official candidate namespace or subsection.

Pros:

- one candidate pool;
- later review can be more uniform;
- cross-source conflicts can be represented close to candidate rows.

Cons:

- changes the main candidate schema;
- increases regression risk;
- may affect provider-centric tests and review tooling;
- may imply a source merge before source-precedence policy is accepted.

### Option B: Parallel Official Candidate Artifact

Description:

- keep the independent official-only artifact:
  `official_disclosure_fact_candidates.v1`;
- retain a concrete runtime artifact such as
  `official_disclosure_candidates_review.json`;
- let the provider-centric `fact_candidates.json` record only a reference or
  summary in a later stage, if the schema allows it.

Pros:

- does not pollute the current provider-centric schema;
- low risk for the current stage;
- preserves official source trace and caveats without lossy mapping;
- matches the accepted runtime baseline.

Cons:

- review tooling must know about two artifacts;
- later merge or conflict logic still needs orchestration design;
- candidate review decisions need explicit source references.

### Option C: Bridge Index Artifact

Description:

- add a lightweight bridge / source-index artifact, for example:
  `candidate_source_bridge.json`, `candidate_source_index.json`, or
  `candidate_inputs_manifest.json`;
- record provider candidate artifact refs, official candidate artifact refs,
  counts, source types, review queues, and cross-source conflict summaries.

Pros:

- does not break any existing schema;
- can scale to more source types later;
- can be a transition layer before candidate schema v2;
- keeps review orchestration explicit and auditable.

Cons:

- introduces one more intermediate artifact;
- requires future orchestration support;
- conflict summaries must avoid implying automatic verification.

## 4. V1 Recommendation

V1 should use Option B + Option C:

- keep independent `official_disclosure_fact_candidates.v1` artifacts;
- add a lightweight bridge / source-index design;
- do not directly append official rows to provider-centric
  `fact_candidates.json`;
- let a later review layer read provider candidates and official candidates
  side by side;
- defer a unified candidate pool until candidate schema v2.

This recommendation supersedes a direct-append implementation for the current
stage. Official rows can still become part of a future unified candidate schema,
but only after provider-centric consumers, tests, review decisions, conflict
metadata, and safety validation are redesigned around mixed source types.

## 5. Bridge Artifact Schema

Future bridge artifact path candidates:

```text
output/ground_truth_candidate_bridges/<timestamp>/<code>/candidate_source_bridge.json
output/ground_truth_candidates/<timestamp>/<code>/candidate_inputs_manifest.json
```

The path choice is implementation work for a later stage. Either path must
remain ignored runtime output unless a separate fixture-promotion design creates
a sanitized example.

Recommended V1 shape:

```json
{
  "version": "candidate_source_bridge.v1",
  "code": "600406",
  "company_name": "Guodian NARI",
  "created_at": "",
  "candidate_sources": [
    {
      "source_type": "provider_candidates",
      "artifact_path": "",
      "candidate_count": 0,
      "manual_review_count": 0,
      "blocked_count": 0
    },
    {
      "source_type": "official_disclosure_candidates",
      "artifact_path": "",
      "candidate_count": 0,
      "manual_review_count": 0,
      "blocked_count": 0
    }
  ],
  "cross_source_conflicts": [],
  "review_priorities": [],
  "not_for_trading_advice": true
}
```

Recommended source entry extensions:

```json
{
  "source_type": "official_disclosure_candidates",
  "artifact_path": "output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json",
  "artifact_version": "official_disclosure_fact_candidates.v1",
  "artifact_digest": "",
  "candidate_count": 7,
  "manual_review_count": 7,
  "blocked_count": 0,
  "source_summary": {
    "evidence_tier": "L1_official_disclosure",
    "source_documents": 1,
    "source_tables": 1
  }
}
```

Recommended conflict entry shape:

```json
{
  "conflict_id": "600406-conflict-001",
  "field_path": "business_composition.product_segment.revenue",
  "period": "2025H1",
  "unit": "CNY",
  "provider_candidate_ref": {
    "source_type": "provider_candidates",
    "artifact_ref": "",
    "candidate_id": ""
  },
  "official_candidate_ref": {
    "source_type": "official_disclosure_candidates",
    "artifact_ref": "",
    "candidate_id": ""
  },
  "conflict_type": "value_mismatch",
  "review_status": "manual_review_required",
  "not_for_trading_advice": true
}
```

Recommended review-priority entry shape:

```json
{
  "priority_id": "600406-official-A1",
  "priority_level": "high",
  "source_type": "official_disclosure_candidates",
  "artifact_ref": "",
  "candidate_id": "",
  "field_path": "business_composition.product_segment.revenue",
  "reason": "official_provider_conflict",
  "review_action": "compare_period_unit_denominator_and_source_trace",
  "blocked": false,
  "not_for_trading_advice": true
}
```

## 6. Cross-Source Conflict Design

Conflict detection should compare provider candidates and official candidates
only after normalizing field identity, period, unit, and denominator.

Rules:

- same `field_path` + same `period` + same unit + same value ->
  multi-source consistency candidate;
- same `field_path` + same `period` + different value -> conflict;
- same field but different period -> not directly comparable;
- same value but different denominator -> manual review;
- same value but different unit normalization path -> manual review unless the
  conversion is explicit and accepted;
- same field with different classification group, such as product vs region ->
  not directly comparable;
- official L1 source can be a stronger source candidate, but it is still not
  an automatic verified fact;
- a conflict must not automatically change provider primary selection;
- a conflict must not automatically enter Research Report V1.

Suggested conflict types:

- `multi_source_consistency_candidate`;
- `value_mismatch`;
- `period_mismatch`;
- `unit_mismatch`;
- `denominator_mismatch`;
- `classification_mismatch`;
- `source_lineage_mismatch`;
- `manual_review_required`.

## 7. Review Priority Design

Review priority should make official evidence visible without implying that the
official candidate is accepted truth.

Priority rules:

- official L1 candidate with complete source trace can be higher priority than
  an untraced provider candidate;
- missing unit, period, or denominator should become blocked or high-priority
  review depending on field semantics;
- source lineage mismatch should be blocked;
- `table_quality=structured_medium` remains manual review;
- official / provider conflict becomes high-priority manual review;
- caveat-only official table evidence stays caveat-only and does not become a
  fact candidate;
- empty `source_page_or_anchor` is accepted only when trace remains closed
  through source document + source section + table row / column /
  `source_column_map`;
- no priority item may mark a candidate as `verified_fact`.

Recommended review priority reasons:

- `official_l1_trace_available`;
- `official_provider_conflict`;
- `missing_period`;
- `missing_unit`;
- `missing_denominator`;
- `source_lineage_mismatch`;
- `structured_medium_requires_review`;
- `caveat_only_no_candidate`;
- `source_anchor_missing_but_table_trace_closed`.

## 8. Relationship To Review Decisions

Future `candidate_review_decisions.json` artifacts can reference both provider
candidates and official candidates.

Required reference fields:

- `source_type`;
- `candidate_id`;
- `artifact_ref`;
- optional `artifact_digest`;
- `field_path`;
- `period`;
- `unit`;
- review outcome and follow-up type.

Review decisions remain an intermediate audit layer:

- they are not fixture promotion;
- they are not verified facts;
- they do not authorize fixture writes;
- they do not overwrite provider candidates;
- they do not rewrite official candidate payloads;
- promotion rules remain a later stage.

## 9. Relationship To Research Report V1

Research Report V1 must not directly read the official candidate payload in the
current baseline.

The bridge layer only makes stronger official evidence candidates visible to
the candidate review chain. It does not turn those candidates into report-ready
facts.

Required boundaries:

- Research Report V1 L1 evidence integration requires a later accepted design;
- official candidate rows are still candidates, not `verified_fact`;
- report generation must not automatically rewrite an accepted report when a
  bridge artifact appears;
- report output must not include buy / sell / hold advice, target prices,
  position sizing, portfolio weights, or trading signals;
- Research Report V1 should continue to surface caveats until review and
  acceptance policies explicitly allow stronger evidence labels.

## 10. Safety / Validation

Future implementation must validate:

- all artifact refs are local, ignored, and allowed for the runtime mode;
- no token, Bearer string, MCP URL, `.env` reference, local secret path, or
  credential appears in bridge artifacts;
- no trading recommendation keys appear;
- no `verified_fact` marker appears;
- no fixture is written;
- no accepted manifest is updated;
- no provider primary switch occurs;
- no Research Report V1 output is updated;
- no candidate generator main path is changed without a separate accepted
  implementation stage;
- every source entry reports `not_for_trading_advice=true` or inherits the
  top-level invariant;
- the top-level bridge artifact has `not_for_trading_advice=true`;
- every official candidate ref resolves to an official candidate artifact;
- every provider candidate ref resolves to a provider candidate artifact;
- cross-source conflict entries do not imply automatic verification or report
  inclusion.

Fail-closed cases:

- missing source artifact;
- source artifact not local or not allowed;
- malformed artifact version;
- source lineage mismatch;
- candidate id collision that cannot be proven identical;
- missing period / unit / denominator for comparable quantitative fields;
- bridge artifact attempts to write fixtures, accepted manifests, report
  artifacts, or regression expected files.

## 11. Relation To Current Runtime Baseline

Current official candidate payload artifact:

```text
output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json
```

Accepted runtime facts:

- `candidate_rows=7`;
- 1 main business candidate;
- 6 revenue table candidates;
- all rows use `source_type=official_disclosure`;
- all rows use `evidence_tier=L1_official_disclosure`;
- all current candidates require human review or retain caveats;
- no `verified_fact`;
- no `review_status=verified`;
- no `auto_verified`;
- no provider-centric `fact_candidates.json` has been generated from official
  rows;
- no candidate generator main path integration exists yet.

Latest accepted verification results remain quoted, not rerun by this
documentation-only design:

- targeted tests `496 passed`;
- full pytest latest `1144 passed, 1 skipped`;
- regression `passed=47 failed=0 total=47`.

## 12. Roadmap

Recommended sequence:

1. Bridge design.
2. Bridge artifact implementation.
3. Retained 600406 bridge runtime review.
4. Review decisions update design.
5. Candidate schema v2 design.
6. Research Report V1 L1 evidence integration design.
7. Later fixture promotion / validator.
8. Later live CNInfo.

Do not skip directly to Research Report V1 integration, fixture promotion,
validator work, live CNInfo, provider calls, token reads, MCP, Dashboard /
Batch, scoring / P1.1 changes, regression expected changes, or trading advice.
