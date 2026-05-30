# Phase 4 Bounded Hypothesis Generator Plan

Date: 2026-05-30

Stage: Phase 4 bounded hypothesis generator planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not read report
artifacts, does not call providers, does not use network, does not read tokens,
does not generate reports, does not enter Research Report V1 integration, does
not generate trading advice, does not generate target prices, does not generate
position or portfolio guidance, does not process unrelated mojibake files, does
not commit, and does not push.

Reference baseline:

- Phase 3 Deterministic Evidence Inventory + Readiness Skeleton baseline:
  `c0f8b1c389d2b9060cb68f3dcc38e8577eb235c3`.
- Phase 3 acceptance summary:
  `64d748a806422e93a568d243b0f36a8f94e5219b`.
- Phase 3R Synthetic Readiness Dry-run Tests baseline:
  `991bd8e0f571d6dfa2ad8bf2ca711b2de811c4b0`.
- Phase 3R acceptance summary:
  `a074a9a75b0c3f448d55309cddd0bf26cc98c34a`.

## 1. Phase 4 Goal

Phase 4 plans a bounded research-reasoning layer above the accepted Phase 3
deterministic evidence readiness outputs.

Phase 4 should plan only:

- a bounded hypothesis generator;
- generation of artifact-state-grounded company, industry, supply-chain,
  business-model, and macro hypotheses;
- explicit research questions and follow-up data needs;
- fail-closed downstream-use decisions for each hypothesis;
- caveats and lineage references back to validated Phase 3 payloads;
- mandatory `not_for_trading_advice=true` boundaries.

The future generator must consume only validated Phase 3 payloads:

- `deterministic_evidence_inventory.v1`;
- `readiness_skeleton.v1`.

Every generated hypothesis must be grounded in artifact-state evidence and
lineage. Artifact-state evidence may support planning, prioritization, or
experimental context candidacy, but it must not be promoted into a verified
fact.

Phase 4 does not plan:

- a verified fact generator;
- Research Report V1 integration;
- a report generator;
- a trading advice engine;
- a target price generator;
- a portfolio or position generator;
- a technical signal generator;
- a live provider connector;
- an output scanner;
- a real accepted-manifest reader;
- a report artifact reader;
- a replacement for Phase 1, Phase 2, or Phase 3 validators.

The future implementation should start only after this planning document is
accepted in a separate review step.

## 2. Input Boundary

The future Phase 4 generator should accept one explicit request dictionary or a
small typed equivalent.

Allowed inputs:

- a validated `deterministic_evidence_inventory.v1` payload;
- a validated `readiness_skeleton.v1` payload;
- optional `stock_code` and `company_name` hints supplied by the caller;
- optional bounded model reasoning context supplied by the caller as inert
  planning context, not as a data source;
- required `not_for_trading_advice=true`.

Planned request shape:

```json
{
  "schema_version": "bounded_hypothesis_request.v1",
  "stock_code": "600406",
  "company_name": "optional auxiliary name hint",
  "deterministic_evidence_inventory": {
    "schema_version": "deterministic_evidence_inventory.v1"
  },
  "readiness_skeleton": {
    "schema_version": "readiness_skeleton.v1"
  },
  "bounded_reasoning_context": {
    "purpose": "optional planning-only context"
  },
  "not_for_trading_advice": true
}
```

Input field rules:

- `stock_code`: optional only when both validated Phase 3 payloads contain the
  same exact six-digit ticker. If supplied, it must match both payloads.
- `company_name`: optional auxiliary hint only. It cannot independently resolve
  identity and cannot override Phase 3 conflict or blocked states.
- `deterministic_evidence_inventory`: required validated Phase 3 evidence
  inventory.
- `readiness_skeleton`: required validated Phase 3 readiness skeleton for the
  same ticker and lineage.
- `bounded_reasoning_context`: optional planning-only context. It may shape
  wording or prioritization, but cannot introduce unreferenced evidence,
  verified facts, provider data, target prices, recommendations, or report
  content.
- `not_for_trading_advice`: required and must be `true`.

Rejected input sources:

- raw accepted manifest dictionaries;
- accepted manifest paths that Phase 4 would open;
- raw `output/` scan results;
- report artifact content;
- parsed report artifact sections;
- provider live responses;
- official disclosure raw text;
- unvalidated artifact rows;
- Research Report V1 section payloads;
- trading prompts;
- target price prompts;
- buy-sell prompts;
- portfolio or position prompts;
- token, credential, or `.env` contents.

Phase 4 must not repair incomplete inputs by reading files, scanning
directories, calling providers, reading report artifacts, or entering any
report generator.

All accepted inputs should be defensively copied. Caller-owned dictionaries and
lists must not be mutated.

## 3. Output Schema Draft

Phase 4 should produce one planning payload:

- `bounded_hypothesis_payload.v1`.

This payload is not a report section, not a verified fact store, and not a
trading artifact.

Planned shape:

```json
{
  "schema_version": "bounded_hypothesis_payload.v1",
  "stock_code": "600406",
  "company_name": "optional auxiliary name hint",
  "source_readiness_level": "data_collection_required",
  "industry_hypotheses": [],
  "supply_chain_position_hypotheses": [],
  "business_model_hypotheses": [],
  "macro_factor_hypotheses": [],
  "key_research_questions": [],
  "required_follow_up_data": [],
  "blocked_hypotheses": [],
  "caveats": [],
  "lineage_refs": [],
  "not_for_trading_advice": true
}
```

Required output fields:

- `schema_version`: fixed value `bounded_hypothesis_payload.v1`.
- `stock_code`: exact six-digit ticker copied from validated Phase 3 payloads.
- `company_name`: conservative name copied from Phase 3 payloads or caller hint
  when non-conflicting.
- `source_readiness_level`: copied from `readiness_skeleton.v1`.
- `industry_hypotheses`: bounded industry hypotheses.
- `supply_chain_position_hypotheses`: bounded supply-chain or value-chain
  position hypotheses.
- `business_model_hypotheses`: bounded company business-model hypotheses.
- `macro_factor_hypotheses`: bounded macro-factor hypotheses with explicit
  transmission paths.
- `key_research_questions`: follow-up questions derived from gaps, caveats,
  conflicts, and low-confidence areas.
- `required_follow_up_data`: concrete data needs required before stronger
  downstream use.
- `blocked_hypotheses`: candidate hypotheses that could not pass fail-closed
  evidence or readiness rules.
- `caveats`: payload-level caveats, including artifact-state boundary caveats.
- `lineage_refs`: references to Phase 3 payload lineage, not copied report
  content or verified facts.
- `not_for_trading_advice`: always `true`.

Forbidden output fields and equivalents:

- `verified_facts`;
- `accepted_report_facts`;
- `report_sections`;
- `research_report`;
- `recommendation`;
- `trading_advice`;
- `target_price`;
- `position_size`;
- `portfolio_weight`;
- `technical_signal`;
- provider payloads;
- raw accepted-manifest payloads;
- raw report artifact content.

## 4. Hypothesis Item Schema

Every generated hypothesis must include:

```json
{
  "hypothesis_id": "industry-001",
  "hypothesis_type": "industry",
  "hypothesis_text": "Planning-only hypothesis text.",
  "evidence_refs": [
    "deterministic_evidence_inventory.v1:evidence_inventory:official_business_evidence"
  ],
  "evidence_state_refs": [
    "readiness_skeleton.v1:readiness_evidence_categories:official_business_evidence:available"
  ],
  "confidence": "low",
  "caveats": [],
  "required_follow_up_data": [],
  "allowed_downstream_use": "planning_only",
  "not_for_trading_advice": true
}
```

Required hypothesis fields:

- `hypothesis_id`: stable payload-local identifier.
- `hypothesis_type`: one of the supported bounded hypothesis types.
- `hypothesis_text`: concise planning-only hypothesis. It must avoid verified
  fact language.
- `evidence_refs`: non-empty lineage references to validated Phase 3 evidence
  inventory entries unless the item is explicitly blocked.
- `evidence_state_refs`: non-empty artifact-state references describing the
  state that supports, limits, or blocks the hypothesis.
- `confidence`: one of `high`, `medium`, `low`, or `not_assessable`.
- `caveats`: caveats specific to the hypothesis.
- `required_follow_up_data`: data needed before stronger use.
- `allowed_downstream_use`: constrained downstream-use marker.
- `not_for_trading_advice`: always `true`.

Supported hypothesis types should reuse Phase 1 constants where they already
fit and add only the minimum Phase 4-specific surface needed:

- `industry`;
- `supply_chain_position`;
- `business_model`;
- `macro_factor`;
- `data_gap`;
- `conflict`.

`industry_driver` may remain available as a compatibility type if Phase 1
validators already expose it, but Phase 4 should prefer the clearer
industry/company/macro buckets in the payload lists.

Hypothesis text rules:

- Use bounded language such as "may indicate", "could suggest", or "requires
  follow-up".
- Do not state artifact-state as a verified business fact.
- Do not produce report-ready claims.
- Do not produce buy/sell/hold, price target, position, portfolio, or technical
  signal language.
- Do not infer a specific industry or supply-chain role without evidence
  references.
- Do not mix tickers or hard-code one company's profile into another company's
  hypothesis.

## 5. Allowed Downstream Use Boundary

Allowed `allowed_downstream_use` values:

- `planning_only`;
- `data_collection_prioritization`;
- `experimental_report_context_candidate`;
- `blocked_until_review`;
- `not_allowed_downstream`.

Forbidden `allowed_downstream_use` values and semantic equivalents:

- `verified_fact`;
- `accepted_report_fact`;
- `report_fact`;
- `trading_signal`;
- `target_price`;
- `buy_sell_decision`;
- `portfolio_weight`;
- accepted fact promotion;
- auto-verified fact promotion;
- report-ready fact promotion.

Downstream-use rules:

- `planning_only` is the default for evidence-grounded but still preliminary
  hypotheses.
- `data_collection_prioritization` may be used when the hypothesis primarily
  identifies what to collect next.
- `experimental_report_context_candidate` may be used only when identity is
  resolved, readiness is not blocked, conflicts are absent, and evidence is
  current enough for experimental context candidacy. It still is not a report
  fact.
- `blocked_until_review` is required when evidence is candidate-only,
  review-required, conflicting, or otherwise cannot support even experimental
  context without review.
- `not_allowed_downstream` is required when safety, identity, conflict,
  missing-evidence, or unsupported-reasoning rules block the hypothesis.

## 6. Hypothesis Fail-Closed Rules

The future generator and validators must fail closed.

Required fail-closed rules:

- Generic hypotheses without `evidence_refs` must be rejected.
- Hypotheses without `evidence_state_refs` must be rejected or blocked.
- When `readiness_skeleton.v1` is `blocked`, no downstream-allowed hypothesis
  may be generated.
- When identity is not `resolved`, no downstream-allowed hypothesis may be
  generated.
- When `conflict_artifacts` is non-empty, hypotheses must be
  `blocked_until_review` or `not_allowed_downstream`.
- When official/business evidence is missing, formal company and industry
  hypotheses must not be generated.
- When critical financial artifacts are missing, financial-quality hypotheses
  must not be generated.
- Candidate-only evidence may support only `planning_only` or
  `blocked_until_review`.
- Review-required evidence may support only `planning_only` or
  `blocked_until_review`.
- Artifact states such as accepted/current must not be treated as verified
  facts.
- Macro hypotheses must state a transmission path from macro factor to
  industry or business mechanism; otherwise they must be blocked.
- Any trading advice, target price, buy-sell decision, portfolio weight,
  position sizing, or technical signal marker must be rejected.
- Forbidden output keys must be rejected recursively in returned payloads.
- The generator must not mutate input dictionaries or lists.

Readiness-to-downstream-use rules:

| Source readiness level | Maximum allowed hypothesis use |
| --- | --- |
| `accepted_report_ready` | `experimental_report_context_candidate`, still not a report fact |
| `experimental_report_ready` | `experimental_report_context_candidate`, still not a report fact |
| `data_collection_required` | `planning_only` or `data_collection_prioritization` |
| `classification_review_required` | `planning_only` or `blocked_until_review` |
| `evidence_conflict_review_required` | `blocked_until_review` or `not_allowed_downstream` |
| `blocked` | `not_allowed_downstream` |

These are ceilings, not entitlements. A hypothesis must still pass all evidence,
identity, conflict, caveat, and safety rules.

## 7. Macro / Industry / Company Boundary

Company-level hypotheses:

- must derive from validated business or artifact-state evidence;
- must identify the evidence and evidence-state references used;
- must remain planning-only until follow-up data confirms the underlying
  business fact;
- must not infer operating segments, products, customers, geography, or
  revenue quality without support.

Industry hypotheses:

- must be based on company artifact-state plus explicit reasoning;
- must not rely on generic industry templates alone;
- must not classify a company into an industry without evidence references;
- must not hard-code another ticker's profile, such as applying a `002371`
  profile to `300475`.

Supply-chain position hypotheses:

- must identify whether the reasoning is about upstream inputs, midstream
  production, downstream customers, channels, or end markets;
- must cite evidence and evidence-state references;
- must remain blocked or planning-only when the value-chain role is inferred
  from incomplete or candidate-only artifact-state evidence.

Business-model hypotheses:

- must be grounded in official/business or validated artifact-state evidence;
- must not become financial-quality hypotheses when critical financial
  artifacts are missing;
- must name required follow-up data when business model mechanics are inferred
  from partial evidence.

Macro factor hypotheses:

- must derive from an industry or business mechanism;
- must state a transmission path, such as macro factor -> industry demand,
  cost, financing, regulation, capex, FX, commodity input, or customer budget ->
  company exposure to be researched;
- must not produce broad macro essays;
- must not assert macro sensitivity as fact without evidence;
- must be blocked when no plausible mechanism can be stated from the validated
  Phase 3 artifact-state inputs.

Manual category labels may help organize review output in a future
implementation, but manual industry template libraries must not be used as a
hypothesis source and must not replace bounded reasoning or evidence-state
grounding.

## 8. Safety Constraints

Phase 4 planning and future implementation must preserve these constraints:

- no real accepted-manifest read;
- no `output/` scan;
- no report artifact read;
- no report generation;
- no Research Report V1 integration;
- no live provider access;
- no CNInfo, Tushare, AkShare, MCP, browser, or network access for generation;
- no token, credential, `.env`, or secret read;
- no runtime artifact generation;
- no fixture promotion;
- no accepted-manifest update or write;
- no provider-primary switch;
- no verified fact generation;
- no report fact generation;
- no trading advice;
- no target price;
- no position sizing;
- no portfolio weight;
- no technical signal;
- no processing of unrelated mojibake files.

Safety scanning should apply to in-memory request and response payloads only.
It must not scan the real repository, real `output/`, or artifact paths.

Suggested forbidden marker scan for returned payloads:

```text
verified_fact
accepted_report_fact
report_fact
research_report
report_sections
recommendation
trading_advice
investment_advice
target_price
position_size
portfolio_weight
technical_signal
buy_sell_decision
provider_payload
accepted_manifest
output_scan
artifact_content
token
credential
```

## 9. Relationship To Prior Phases

Phase 4 depends on the prior planning chain:

- Phase 1 provides schema, hypothesis, downstream-use, readiness, and safety
  foundations.
- Phase 2 provides artifact-state inventory boundaries.
- Phase 3 provides `deterministic_evidence_inventory.v1` and
  `readiness_skeleton.v1`.
- Phase 3R provides synthetic dry-run coverage that confirms Phase 3 readiness
  behavior remains fail-closed.
- Phase 4 may reason only on validated Phase 3 inputs.

Phase 4 must not:

- bypass Phase 1 validators;
- bypass Phase 2 artifact-state boundaries;
- bypass Phase 3 readiness validators;
- read real accepted manifests directly;
- scan output directly;
- enter Research Report V1;
- write Phase 4 output into Research Report V1;
- convert Phase 4 hypotheses into accepted report facts.

Phase 4 output may become a candidate planning input for later review, but only
after explicit acceptance and only inside a separate phase.

## 10. Tests Strategy

Future tests should use synthetic in-memory dictionaries and lists only. They
should not read real manifests, scan `output/`, read report artifacts, call
providers, use network, read tokens, or write runtime artifacts.

Required future test scenarios:

- valid bounded industry hypothesis;
- valid supply-chain hypothesis;
- valid business-model hypothesis;
- valid macro factor hypothesis with explicit transmission path;
- hypothesis without evidence rejected;
- hypothesis without evidence-state references rejected or blocked;
- blocked readiness rejects downstream hypothesis;
- unresolved identity rejects downstream hypothesis;
- conflict readiness blocks downstream hypothesis;
- candidate-only evidence limits downstream use;
- review-required evidence limits downstream use;
- missing official/business evidence blocks formal company and industry
  hypotheses;
- missing critical financial artifacts blocks financial-quality hypotheses;
- forbidden markers rejected;
- trading advice rejected;
- target price rejected;
- portfolio weight rejected;
- technical signal rejected;
- no report section keys;
- no verified fact promotion;
- no accepted/current artifact-state promotion to verified fact;
- macro hypothesis without transmission path blocked;
- ticker/profile mismatch blocked;
- no input mutation;
- no file IO;
- no provider access;
- no network access.

Suggested regression subset:

- Phase 1 schema and safety tests that cover hypothesis and downstream-use
  validation;
- Phase 3 evidence readiness tests;
- Phase 3R synthetic readiness dry-run tests.

Suggested no-IO guards:

- monkeypatch filesystem path reads and metadata probes where the generator
  boundary could accidentally reach for artifact paths;
- monkeypatch provider/client entry points if imports make them reachable;
- assert that returned payloads contain only allowed schema fields.

The no-IO guards should operate on the future generator boundary only. They
must not scan real repository output or artifact directories.

## 11. Expected Files

Future Phase 4 implementation should default to changing only:

```text
src/fundamental_skill/research_planning/bounded_hypothesis_generator.py
tests/test_bounded_hypothesis_generator.py
```

Recommended module choice:

- Add a new `bounded_hypothesis_generator.py` module for the Phase 4 generator,
  request validation, payload validation, and fail-closed hypothesis rules.
- Reuse existing Phase 1 constants from
  `autonomous_ticker_research_schema.py` where they already match, especially
  hypothesis types, confidence levels, readiness levels, and downstream-use
  markers.
- Do not retrofit Phase 4 output into the existing Phase 1 planning payload
  schema. The Phase 1 payload includes Research Pack placeholders and broader
  planning-gate fields, while Phase 4 needs a narrower
  `bounded_hypothesis_payload.v1` surface with `evidence_state_refs` and
  explicit Phase 3 lineage.
- Export future public helpers from `research_planning/__init__.py` only after
  the generator surface is accepted.

Potential future public helpers:

```text
BOUNDED_HYPOTHESIS_PAYLOAD_SCHEMA_VERSION
build_bounded_hypothesis_payload
validate_bounded_hypothesis_payload
validate_bounded_hypothesis
```

Default file policy:

- Keep implementation separate from Report V1, provider, CLI, orchestrator,
  Dashboard, and Batch code.
- Do not add runtime fixtures.
- Do not write under `output/`.
- Do not modify accepted manifest, provider, report, or artifact-reader code.
- Do not change Phase 3 production code unless Phase 4 tests reveal a true
  accepted-interface bug; if that happens, isolate and explain the bug before
  changing Phase 3.

## 12. Acceptance Checklist

Planning acceptance should confirm:

- only the expected planning document changed;
- no production code was written;
- no tests were written;
- no runtime artifact was generated;
- no provider, network, token, or credential path was touched;
- no real accepted manifest was read;
- no real `output/` scan was performed;
- no report artifact was read;
- no Research Report V1 integration was entered;
- no verified fact promotion is planned;
- no trading advice, target price, portfolio, position, or technical signal
  output is planned;
- future hypotheses require `evidence_refs`;
- future hypotheses require `evidence_state_refs`;
- downstream use is constrained to planning-safe values;
- macro hypotheses require transmission paths;
- company, industry, and supply-chain hypotheses are artifact-state-grounded;
- future tests are targeted and synthetic;
- regression subset is identified;
- git status remains clean except unrelated mojibake untracked files.

## 13. Next Stage Recommendation

Recommended next stage after this document is reviewed:

```text
Phase 4 planning acceptance review
```

Do not enter Phase 4 implementation until the planning acceptance review is
explicitly approved.
