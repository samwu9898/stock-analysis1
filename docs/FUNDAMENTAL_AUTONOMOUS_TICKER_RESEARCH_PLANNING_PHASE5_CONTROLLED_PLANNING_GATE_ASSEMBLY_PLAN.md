# Phase 5 Controlled Planning Gate Assembly Plan

Date: 2026-05-31

Stage: Phase 5 controlled planning gate assembly and orchestrator boundary
planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not read report
artifacts, does not call providers, does not call MCP, does not use network,
does not read tokens, does not generate reports, does not enter Research Report
V1 integration, does not generate trading advice, does not generate target
prices, does not generate position or portfolio guidance, does not generate
technical signals, does not process unrelated mojibake files, does not commit,
and does not push.

Reference baseline:

- Phase 4 Bounded Hypothesis Generator baseline:
  `9b261aa00aab194ab66ce9c7aca8f5de94b2e603`.
- Phase 4 acceptance summary:
  `0c69349b0d74e2d37411d529d88ca71dcd401795`.

## 1. Phase 5 Goal

Phase 5 plans a controlled assembly boundary above the accepted Phase 2C,
Phase 3, and Phase 4 planning outputs.

Phase 5 should plan only:

- controlled planning gate assembly;
- defensive re-validation of supplied Phase 2C, Phase 3, and Phase 4 payloads;
- consistency checks across ticker identity, company hint, readiness state, and
  hypothesis source readiness;
- assembly of one planning result payload;
- fail-closed readiness and blocked-state propagation;
- data-gap planning derived from already validated planning payloads;
- caveats and lineage references back to the validated upstream payloads;
- mandatory `not_for_trading_advice=true` boundaries.

The future implementation must consume only validated upstream payloads:

- validated `ticker_local_artifact_inventory.v1`;
- validated `deterministic_evidence_inventory.v1`;
- validated `readiness_skeleton.v1`;
- validated `bounded_hypothesis_payload.v1`.

Phase 5 should output exactly one planning result:

- `autonomous_ticker_research_planning_result.v1`.

The Phase 5 planning result is an orchestration boundary payload. It tells a
caller whether the assembled planning state is blocked, accepted-report-ready,
or experimental-report-ready under the existing readiness skeleton. It does not
create report content, evidence facts, provider data, or trading conclusions.

Phase 5 does not plan:

- full orchestrator implementation;
- Research Report V1 integration;
- report generation;
- live provider connection;
- CNInfo, Tushare, AkShare, MCP, browser, or network access;
- real accepted-manifest reading;
- real `output/` scanning;
- report artifact reading;
- PDF, DOCX, HTML, Excel, or other artifact-content parsing;
- fixture promotion;
- Dashboard or Batch integration;
- trading engine behavior;
- target price, position, portfolio, or technical signal behavior.

The future implementation should start only after this planning document is
accepted in a separate review step.

## 2. Input Design

The future Phase 5 assembler should accept one explicit request dictionary or a
small typed equivalent. Accepted inputs are limited to already supplied,
in-memory payload dictionaries and explicit identity hints.

Allowed inputs:

- a validated `ticker_local_artifact_inventory.v1` payload;
- a validated `deterministic_evidence_inventory.v1` payload;
- a validated `readiness_skeleton.v1` payload;
- a validated `bounded_hypothesis_payload.v1` payload;
- an explicit `stock_code` hint;
- an optional explicit `company_name` hint;
- required `not_for_trading_advice=true`.

Planned request shape:

```json
{
  "schema_version": "controlled_planning_gate_assembly_request.v1",
  "stock_code": "600406",
  "company_name": "optional auxiliary name hint",
  "ticker_local_artifact_inventory": {
    "schema_version": "ticker_local_artifact_inventory.v1"
  },
  "deterministic_evidence_inventory": {
    "schema_version": "deterministic_evidence_inventory.v1"
  },
  "readiness_skeleton": {
    "schema_version": "readiness_skeleton.v1"
  },
  "bounded_hypothesis_payload": {
    "schema_version": "bounded_hypothesis_payload.v1"
  },
  "not_for_trading_advice": true
}
```

Input field rules:

- `stock_code`: required exact six-digit ticker. It must match all supplied
  upstream payloads.
- `company_name`: optional auxiliary hint only and may be empty. If supplied,
  it must exactly match every upstream payload `company_name`. It cannot
  independently resolve identity, override upstream conflicts, fuzzy-match
  aliases, match abbreviations, or infer a company alias.
- `ticker_local_artifact_inventory`: required Phase 2C inventory payload that
  will be re-validated at the Phase 5 boundary.
- `deterministic_evidence_inventory`: required Phase 3 evidence inventory
  payload that will be re-validated at the Phase 5 boundary.
- `readiness_skeleton`: required Phase 3 readiness skeleton payload that will
  be re-validated at the Phase 5 boundary.
- `bounded_hypothesis_payload`: required Phase 4 payload that will be
  re-validated at the Phase 5 boundary with the supplied Phase 3 payloads.
- `not_for_trading_advice`: required and must be `true`.

Rejected input sources:

- raw accepted manifest dictionaries;
- accepted manifest file paths that Phase 5 would open;
- raw `output/` scan results;
- report artifact content;
- parsed report artifact sections;
- provider live responses;
- official disclosure raw text;
- unvalidated artifact rows;
- unvalidated hypothesis payloads;
- Research Report V1 section payloads;
- trading prompts;
- target price prompts;
- buy-sell prompts;
- portfolio or position prompts;
- technical signal prompts;
- token, credential, or `.env` contents.

Phase 5 must not repair incomplete inputs by reading files, scanning
directories, calling providers, reading report artifacts, or entering any
report generator. Missing or inconsistent inputs must fail closed into
validation errors or a blocked planning result according to the future public
API choice.

All accepted inputs should be defensively copied. Caller-owned dictionaries and
lists must not be mutated.

## 3. Output Schema Draft

Phase 5 should produce one planning payload:

- `autonomous_ticker_research_planning_result.v1`.

This payload is not a report, not a report section, not a verified fact store,
and not a trading artifact.

Product shape guard:

- `autonomous_ticker_research_planning_result.v1` is an internal planning
  boundary state for the Codex Skill and Research Pack.
- It is not a consumer-facing research report.
- It is not a report template.
- It is not a dashboard payload.
- It is not an investment product.
- It is not a report generation trigger.
- It is not a provider fetch trigger.
- It is not an artifact parser trigger.
- Any downstream Report V1, Dashboard, or consumer-facing phase requires
  separate planning and acceptance. Phase 5 output must not be treated as
  content or rendering permission.

Planned shape:

```json
{
  "schema_version": "autonomous_ticker_research_planning_result.v1",
  "stock_code": "600406",
  "company_name": "optional auxiliary name hint",
  "identity_resolution_status": "resolved",
  "artifact_inventory_summary": {
    "total_artifacts": 0,
    "available_artifacts": 0,
    "missing_artifacts": 0,
    "candidate_only_artifacts": 0,
    "review_required_artifacts": 0,
    "conflict_artifacts": 0,
    "ignored_artifacts": 0
  },
  "deterministic_evidence_inventory_ref": {
    "schema_version": "deterministic_evidence_inventory.v1",
    "stock_code": "600406",
    "lineage_ref": "deterministic_evidence_inventory.v1"
  },
  "readiness_skeleton_ref": {
    "schema_version": "readiness_skeleton.v1",
    "stock_code": "600406",
    "lineage_ref": "readiness_skeleton.v1"
  },
  "bounded_hypothesis_payload_ref": {
    "schema_version": "bounded_hypothesis_payload.v1",
    "stock_code": "600406",
    "lineage_ref": "bounded_hypothesis_payload.v1"
  },
  "readiness_level": "data_collection_required",
  "can_generate_accepted_report": false,
  "can_generate_experimental_report": false,
  "data_gap_plan": [],
  "blocked_reasons": [],
  "caveats": [],
  "lineage_refs": [],
  "not_for_trading_advice": true
}
```

Required output fields:

- `schema_version`: fixed value
  `autonomous_ticker_research_planning_result.v1`.
- `stock_code`: exact six-digit ticker copied from validated upstream payloads.
- `company_name`: copied only when all non-empty upstream payload names and any
  caller hint are exactly identical. A request hint may be empty. Any mismatch
  between a supplied hint and any upstream `company_name` must fail closed.
- `identity_resolution_status`: copied from validated upstream identity state;
  conflicting upstream states must fail closed.
- `artifact_inventory_summary`: derived counts and state summaries from
  validated Phase 2C and Phase 3 artifact-state payloads.
- `deterministic_evidence_inventory_ref`: lineage reference to the validated
  `deterministic_evidence_inventory.v1` input, not copied report content.
- `readiness_skeleton_ref`: lineage reference to the validated
  `readiness_skeleton.v1` input.
- `bounded_hypothesis_payload_ref`: lineage reference to the validated
  `bounded_hypothesis_payload.v1` input.
- `readiness_level`: copied directly from
  `readiness_skeleton.v1.readiness_level`.
- `can_generate_accepted_report`: copied from
  `readiness_skeleton.v1.can_generate_accepted_report` and then constrained by
  Phase 5 conflict and safety rules. This is only a planning indicator for
  upstream readiness and Phase 5 assembly state.
- `can_generate_experimental_report`: copied from
  `readiness_skeleton.v1.can_generate_experimental_report` and then constrained
  by Phase 5 conflict and safety rules. This is only a planning indicator for
  upstream readiness and Phase 5 assembly state.
- `data_gap_plan`: planning-only follow-up data needs assembled from Phase 3
  missing/review/conflict state and Phase 4 required follow-up data.
- `blocked_reasons`: structured workflow-state reasons explaining why the
  planning result cannot proceed to the corresponding future downstream
  boundary.
- `caveats`: caveats from upstream payloads plus Phase 5 assembly caveats. The
  returned caveats must include the fixed caveat:
  `readiness flags are planning indicators only; they are not Report V1 generation permissions and do not authorize report content creation.`
- `lineage_refs`: references to the validated upstream payloads and upstream
  lineage; no report text or verified facts.
- `not_for_trading_advice`: always `true`.

`artifact_inventory_summary` should be a compact summary, not a replacement for
the full upstream payloads. It may include counts and state category names, but
must not copy report artifact content, raw disclosure text, or provider data.

`data_gap_plan` must be a list. Each item must be a structured dictionary, not
a free-text research conclusion or long-form narrative.

`data_gap_plan` item draft:

```json
{
  "gap_id": "data_gap_001",
  "gap_type": "missing_required_evidence",
  "description": "neutral description of the missing data need",
  "source_phase": "phase3",
  "source_ref": "readiness_skeleton.v1",
  "priority": "high",
  "required_follow_up_data": [
    "planning-only data collection need"
  ],
  "caveats": [],
  "not_for_trading_advice": true
}
```

Allowed `source_phase` values:

- `phase2c`;
- `phase3`;
- `phase4`;
- `phase5_assembly`.

Allowed `priority` values:

- `high`;
- `medium`;
- `low`.

Allowed `gap_type` values:

- `missing_phase2c_inventory`;
- `missing_phase3_readiness`;
- `missing_phase4_hypothesis_payload`;
- `missing_required_evidence`;
- `candidate_only_evidence`;
- `review_required_evidence`;
- `evidence_conflict`;
- `identity_conflict`;
- `readiness_blocked`;
- `hypothesis_blocked`;
- `downstream_use_blocked`;
- `forbidden_marker`;
- `not_for_trading_advice_violation`;
- `other`.

`data_gap_plan` element rules:

- `description` must be a neutral data-need description only.
- Items must not contain `hypothesis_text`.
- Items must not contain investment conclusions.
- Items must not contain buy/sell language, target prices, portfolio weights,
  trading signals, or recommendations.
- Items must not contain report sections, dashboard payloads, or template
  payloads.
- Items must pass the forbidden marker and prohibited key scan.
- `data_gap_plan` is data collection planning, not investment advice.

`blocked_reasons` must be a list. Each item must be a structured dictionary,
not a free-text research conclusion or long-form narrative.

`blocked_reasons` item draft:

```json
{
  "reason_id": "blocked_reason_001",
  "reason_type": "blocked_readiness",
  "source_phase": "phase3",
  "source_ref": "readiness_skeleton.v1",
  "blocking_state": "blocked",
  "description": "neutral description of the upstream blocking state",
  "caveats": [],
  "not_for_trading_advice": true
}
```

Allowed `reason_type` values:

- `missing_upstream_payload`;
- `stock_code_mismatch`;
- `company_name_conflict`;
- `invalid_readiness_flags`;
- `source_readiness_mismatch`;
- `forbidden_marker`;
- `not_for_trading_advice_violation`;
- `blocked_readiness`;
- `evidence_conflict_readiness`;
- `all_artifacts_ignored`;
- `no_hypotheses_allowed_downstream`;
- `payload_validation_failed`;
- `other`.

`blocked_reasons` element rules:

- Items may derive only from existing upstream payload state, such as
  `readiness_skeleton.v1.readiness_level`,
  `readiness_skeleton.v1.fail_closed_reason`,
  upstream `identity_resolution_status`, or
  `bounded_hypothesis_payload.v1.blocked_hypotheses.block_reason`.
- Items must not copy Phase 4 `hypothesis_text`.
- Items must not generate research conclusions.
- Items must not generate investment conclusions.
- Items must not contain trading language, target prices, or recommendations.
- Items must pass the forbidden marker and prohibited key scan.

Forbidden output fields and semantic equivalents:

- `report_sections`;
- `research_report`;
- `professional_research_report`;
- `investment_conclusion`;
- `investment_recommendation`;
- `trading_advice`;
- `target_price`;
- `position_size`;
- `portfolio_weight`;
- `technical_signal`;
- `verified_facts`;
- `accepted_report_facts`;
- `provider_payload`;
- `raw_manifest`;
- `output_scan`;
- `artifact_content`.

## 4. Key Boundaries

The Phase 5 planning result must preserve these boundaries:

- A planning result is not a report.
- A planning result is not a report section.
- A planning result is not a verified fact store.
- A planning result does not generate investment conclusions.
- `can_generate_accepted_report` and `can_generate_experimental_report`
  reflect only upstream readiness and Phase 5 assembly state.
- Readiness flags are not Report V1 generation permissions.
- Readiness flags do not trigger report generation.
- Readiness flags do not authorize template assembly.
- Readiness flags do not authorize dashboard rendering.
- Readiness flags do not constitute investment advice.
- Phase 5 does not create, trigger, or authorize any report generation
  behavior.
- Bounded hypotheses are not report-ready facts.
- Bounded hypotheses are not accepted facts.
- `data_gap_plan` is not investment advice.
- `data_gap_plan` is not a target-price or trading checklist.
- `blocked_reasons` are workflow state, not research conclusions.
- `artifact_inventory_summary` is artifact-state summary, not factual company
  analysis.
- `lineage_refs` prove input provenance; they do not authorize reading
  referenced files.
- A planning result does not trigger report generation.
- A planning result does not trigger provider fetch.
- A planning result does not trigger artifact-content parsing.

Phase 5 may say that a future boundary could consider an accepted or
experimental report only when upstream readiness already says so and Phase 5
assembly rules do not find conflicts. Phase 5 itself must not create or grant
Report V1 content permission.

## 5. Assembly Rules

The future assembler should be deterministic, pure, in-memory, and
side-effect-free.

Mandatory rules:

- Require all four upstream payloads to be present, non-`None`, and validated:
  `ticker_local_artifact_inventory.v1`,
  `deterministic_evidence_inventory.v1`, `readiness_skeleton.v1`, and
  `bounded_hypothesis_payload.v1`.
- If any required upstream payload is missing, `None`, or fails its validator,
  Phase 5 must fail closed and must not generate a partial
  `autonomous_ticker_research_planning_result.v1`.
- Re-validate every supplied upstream payload at the Phase 5 boundary.
- Re-validate `ticker_local_artifact_inventory.v1` with the Phase 2C validator.
- Re-validate `deterministic_evidence_inventory.v1` with the Phase 3 evidence
  inventory validator.
- Re-validate `readiness_skeleton.v1` with the Phase 3 readiness skeleton
  validator.
- Re-validate `bounded_hypothesis_payload.v1` with the Phase 4 payload
  validator, supplying the validated Phase 3 evidence inventory and readiness
  skeleton where the validator supports cross-payload checks.
- Require `not_for_trading_advice=true` on request, all upstream payloads, data
  gap items, and the final result.
- Require `stock_code` to match across request, Phase 2C inventory, Phase 3
  evidence inventory, Phase 3 readiness skeleton, and Phase 4 hypothesis
  payload.
- Allow request `company_name` hint to be empty.
- If request `company_name` hint is supplied, require it to exactly match every
  upstream payload `company_name`.
- If any upstream `company_name` differs from the request hint, Phase 5 must
  fail closed.
- Do not use fuzzy matching, abbreviation matching, company alias inference, or
  any Phase 5 identity-resolution behavior for `company_name` consistency.
- Keep identity resolution in prior phases.
- Copy `identity_resolution_status` from validated upstream identity state.
  Conflicts or unresolved states must fail closed for accepted and experimental
  readiness flags.
- Copy `readiness_level` directly from `readiness_skeleton.v1`.
- Do not recompute readiness from hypotheses or prompt text.
- Require `bounded_hypothesis_payload.v1.source_readiness_level` to equal
  `readiness_skeleton.v1.readiness_level`.
- If readiness is `blocked`, the planning result must be blocked.
- If readiness is `evidence_conflict_review_required`, the planning result must
  not be accepted.
- If any conflict artifacts are present, the planning result must not be
  accepted.
- If upstream identity is ambiguous, not found, conflict-required, or blocked,
  the planning result must not be accepted or experimental.
- If Phase 4 contains `blocked_hypotheses`, preserve only their caveats, block
  reasons, and safe follow-up data in `caveats`, `blocked_reasons`, or
  `data_gap_plan`; do not copy `hypothesis_text`.
- Do not promote any `allowed_downstream_use` value.
- Do not convert `experimental_report_context_candidate` into a report section,
  template slot, dashboard payload, or accepted report fact.
- Do not convert Phase 4 hypotheses into verified facts.
- Build `data_gap_plan` and `blocked_reasons` only as structured dictionary
  lists matching the output schema rules. Do not emit free-text research
  conclusions in either field.
- Do not copy raw artifact content into the result.
- Do not mutate caller-owned inputs.
- Do not read files, metadata, manifests, artifact paths, output directories,
  providers, tokens, or network resources.
- Before returning a final planning result, run the Phase 3 / Phase 4
  compatible safety chain: forbidden marker scan, prohibited key scan, payload
  safety scan, and `not_for_trading_advice=true` enforcement.
- Do not silently propagate any upstream forbidden marker into the final
  planning result.

Readiness flag propagation:

- Start with `can_generate_accepted_report` and
  `can_generate_experimental_report` from the validated readiness skeleton.
- Treat both flags only as planning indicators for upstream readiness and
  Phase 5 assembly state.
- Force both flags to `false` when Phase 5 detects any hard assembly conflict,
  forbidden marker violation, identity conflict, missing required upstream
  payload, or `not_for_trading_advice=false`.
- Force `can_generate_accepted_report=false` when readiness is not
  `accepted_report_ready`.
- Force `can_generate_experimental_report=false` when readiness is not
  `experimental_report_ready`.
- Preserve the upstream distinction that `accepted_report_ready` is not the
  same state as `experimental_report_ready`.
- Do not treat either readiness flag as Report V1 generation permission,
  template assembly permission, dashboard rendering permission, or investment
  advice.
- Include this fixed caveat in `caveats`:
  `readiness flags are planning indicators only; they are not Report V1 generation permissions and do not authorize report content creation.`

Blocked result policy:

- A missing, `None`, or validator-failed required payload must fail closed and
  must not be used to assemble a partial planning result.
- An inconsistent supplied payload should fail validation by default, because
  allowing an assembled result from inconsistent identity or readiness lineage
  would hide a caller bug.
- A valid but blocked upstream readiness state should return a valid blocked
  planning result with caveats and data gaps preserved.

## 6. Failure Modes

Future implementation and review should cover these failure modes:

- missing Phase 2C inventory;
- missing Phase 3 deterministic evidence inventory;
- missing Phase 3 readiness skeleton;
- missing Phase 4 bounded hypothesis payload;
- payload `stock_code` mismatch;
- payload `company_name` conflict;
- unresolved or conflicting identity state;
- invalid readiness flags;
- readiness flag inconsistent with readiness level;
- bounded hypothesis `source_readiness_level` mismatch;
- forbidden marker violation;
- prohibited output key violation;
- `not_for_trading_advice=false` on request;
- `not_for_trading_advice=false` on any upstream payload;
- `not_for_trading_advice=false` on any output data gap item;
- blocked readiness;
- evidence conflict readiness;
- all artifacts ignored;
- no available artifacts;
- no hypotheses allowed downstream;
- Phase 4 `blocked_hypotheses` omitted from caveats or data gaps;
- `allowed_downstream_use` promoted beyond the Phase 4 value;
- `experimental_report_context_candidate` converted into report content;
- raw accepted manifest supplied;
- raw `output/` scan supplied;
- report artifact content supplied;
- provider live response supplied;
- unvalidated artifact rows supplied;
- unvalidated hypothesis payload supplied;
- Research Report V1 payload supplied;
- trading, target-price, buy-sell, portfolio, or technical-signal prompt
  supplied;
- input mutation.

Suggested handling:

- Missing or malformed required inputs should raise validation errors at the
  public boundary.
- Valid upstream blocked states should assemble a blocked planning result.
- Valid upstream conflict states should assemble a non-accepted planning result
  with explicit `blocked_reasons` and `caveats`.
- Safety violations should fail closed and should not produce partial report
  content.

## 7. Safety Constraints

Phase 5 planning and future implementation must preserve these constraints:

- no real accepted-manifest read;
- no `output/` scan;
- no report artifact read;
- no PDF, DOCX, HTML, Excel, or other artifact-content parsing;
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
- no investment conclusion;
- no target price;
- no position sizing;
- no portfolio weight;
- no technical signal;
- no Dashboard or Batch payload generation;
- no processing of unrelated mojibake files.

Safety scanning should apply to in-memory request and response payloads only.
It must not scan the real repository, real `output/`, accepted manifests,
report artifacts, or artifact paths.

The same forbidden marker and prohibited key scan should apply to request
payloads, `data_gap_plan`, `blocked_reasons`, `caveats`, and any string-bearing
summary field. These fields must not contain buy/sell language, target prices,
portfolio weights, trading signals, investment recommendations,
`verified_fact`, `accepted_report_fact`, `report_fact`, report sections,
dashboard payloads, template payloads, provider payloads, raw manifest content,
output scan content, artifact content, tokens, or credentials.

Final output safety scan:

- Before returning `autonomous_ticker_research_planning_result.v1`, run the
  same safety scan chain used by Phase 3 / Phase 4 boundaries.
- The final result must pass forbidden marker scan.
- The final result must pass prohibited key scan.
- The final result must pass payload safety scan.
- The final result must enforce `not_for_trading_advice=true` on the request,
  all relevant upstream payloads, every `data_gap_plan` item, every
  `blocked_reasons` item, and the final payload.
- The final result must not silently propagate upstream forbidden markers.

Suggested forbidden marker scan for returned payloads:

```text
verified_fact
accepted_report_fact
report_fact
research_report
professional_research_report
report_sections
report_section
investment_conclusion
recommendation
trading_advice
investment_advice
investment_recommendation
target_price
position_size
portfolio_weight
technical_signal
buy_sell_decision
buy_recommendation
sell_recommendation
buy_signal
sell_signal
trading_signal
dashboard_payload
template_payload
provider_payload
accepted_manifest
output_scan
artifact_content
token
credential
```

## 8. Relationship To Prior Phases

Phase 5 depends on the accepted autonomous ticker research planning chain:

- Phase 1 provides schema, readiness, downstream-use, and safety foundations.
- Phase 2C provides `ticker_local_artifact_inventory.v1`.
- Phase 3 provides `deterministic_evidence_inventory.v1` and
  `readiness_skeleton.v1`.
- Phase 4 provides `bounded_hypothesis_payload.v1`.
- Phase 5 assembles only validated payloads from Phase 2C, Phase 3, and Phase
  4.

Phase 5 must not:

- bypass Phase 1 validators;
- bypass Phase 2C artifact inventory validators;
- bypass Phase 3 evidence readiness validators;
- bypass Phase 4 bounded hypothesis validators;
- read real accepted manifests directly;
- scan output directly;
- read report artifacts;
- parse PDF, DOCX, HTML, Excel, or other artifact content;
- enter Research Report V1;
- write Phase 5 output into Research Report V1;
- convert Phase 4 hypotheses into accepted report facts;
- trigger providers or live data fetch;
- trigger fixture promotion;
- trigger Dashboard or Batch flows.

Phase 5 output may become a candidate input for a future orchestrator boundary,
but only after explicit acceptance and only inside a separate phase. This plan
does not authorize that future integration.

## 9. Tests Strategy

Tests are not written in this planning stage. Future tests should use synthetic
in-memory dictionaries and lists only. They should not read real manifests,
scan `output/`, read report artifacts, call providers, use network, read
tokens, or write runtime artifacts.

Required future test scenarios:

- valid full planning result;
- missing Phase 2C inventory;
- missing Phase 3 deterministic evidence inventory;
- missing Phase 3 readiness skeleton;
- missing Phase 4 hypothesis payload;
- `stock_code` mismatch;
- `company_name` conflict;
- `company_name` hint mismatch with any upstream payload rejected;
- `company_name` abbreviation or fuzzy alias rejected;
- readiness mismatch;
- bounded hypothesis `source_readiness_level` mismatch;
- blocked readiness;
- conflict readiness;
- experimental readiness;
- accepted readiness;
- blocked hypotheses preserved;
- `blocked_hypotheses.block_reason` propagates to `blocked_reasons` while
  `hypothesis_text` does not;
- blocked hypothesis caveats preserved;
- downstream use not promoted;
- `experimental_report_context_candidate` remains a planning context candidate
  and does not become report content;
- output contains no report section;
- output contains no Research Report V1 payload;
- output contains no investment conclusion;
- output contains no target price;
- output contains no trading advice;
- output forbidden marker scan rejects report, trading, and template keys;
- output contains no position sizing;
- output contains no portfolio weight;
- output contains no technical signal;
- forbidden markers rejected;
- prohibited keys rejected;
- raw accepted manifest rejected;
- raw `output/` scan rejected;
- report artifact content rejected;
- provider live response rejected;
- unvalidated artifact rows rejected;
- unvalidated hypothesis payload rejected;
- `not_for_trading_advice=false` rejected;
- all artifacts ignored returns blocked or non-accepted state;
- no hypotheses allowed downstream returns blocked or caveated state;
- data gap plan is planning-only;
- `data_gap_plan` item containing target price or trading advice marker
  rejected;
- `data_gap_plan.required_follow_up_data` remains safe data collection
  planning and does not become investment advice;
- `blocked_reasons` item containing `hypothesis_text` or report conclusion
  rejected;
- missing each of the four upstream payloads fails closed;
- final output contains the required readiness-flags caveat;
- readiness flags do not trigger report generation or dashboard rendering;
- lineage refs are preserved;
- no input mutation;
- no file IO;
- no provider access;
- no network access;
- no token access.
- no PDF, DOCX, HTML, or Excel parsing.

Suggested regression subset:

- Phase 1 schema and safety tests that cover readiness and downstream-use
  validation;
- Phase 2C local artifact inventory tests;
- Phase 3 evidence readiness tests;
- Phase 4 bounded hypothesis generator tests.

Suggested no-IO guards:

- monkeypatch filesystem path reads and metadata probes where the assembler
  boundary could accidentally reach for artifact paths;
- monkeypatch provider/client entry points if imports make them reachable;
- assert that returned payloads contain only allowed schema fields;
- assert that the assembler can run with only synthetic in-memory payloads.

The no-IO guards should operate on the future assembler boundary only. They
must not scan real repository output or artifact directories.

## 10. Expected Files

Future Phase 5 implementation should default to changing only:

```text
src/fundamental_skill/research_planning/planning_gate_assembly.py
tests/test_planning_gate_assembly.py
```

Recommended module choice:

- Add a new `planning_gate_assembly.py` module for the Phase 5 request
  validation, upstream payload re-validation, cross-payload consistency rules,
  planning-result schema validation, and deterministic assembly.
- Reuse existing validators from `local_artifact_index.py`,
  `evidence_readiness.py`, and `bounded_hypothesis_generator.py`.
- Reuse existing Phase 1 constants from
  `autonomous_ticker_research_schema.py` where they already match, especially
  identity statuses, readiness levels, downstream-use markers, and safety
  helpers.
- Do not retrofit Phase 5 output into the existing Phase 1 planning payload
  schema. The Phase 1 payload includes broader planning-gate and Research Pack
  placeholder concepts, while Phase 5 needs a narrower
  `autonomous_ticker_research_planning_result.v1` boundary assembled from
  Phase 2C, Phase 3, and Phase 4 payloads.
- Do not append Phase 5 assembly to `bounded_hypothesis_generator.py`; Phase 4
  remains a bounded hypothesis payload layer, while Phase 5 is a separate
  orchestrator boundary planning layer.
- Export future public helpers from `research_planning/__init__.py` only after
  the assembler surface is accepted.

Potential future public helpers:

```text
CONTROLLED_PLANNING_GATE_ASSEMBLY_REQUEST_SCHEMA_VERSION
AUTONOMOUS_TICKER_RESEARCH_PLANNING_RESULT_SCHEMA_VERSION
build_autonomous_ticker_research_planning_result
validate_controlled_planning_gate_assembly_request
validate_autonomous_ticker_research_planning_result
```

Default file policy:

- Keep implementation separate from Report V1, provider, CLI, orchestrator,
  Dashboard, and Batch code.
- Do not add runtime fixtures.
- Do not write under `output/`.
- Do not modify accepted manifest, provider, report, artifact-reader, or
  fixture-promotion code.
- Do not change Phase 2C, Phase 3, or Phase 4 production code unless Phase 5
  tests reveal a true accepted-interface bug; if that happens, isolate and
  explain the bug before changing upstream code.

## 11. Acceptance Checklist

Planning acceptance should confirm:

- only this Phase 5 planning document changed;
- no production code was written;
- no tests were written;
- no runtime artifact was generated;
- no provider, network, token, credential, or MCP path was touched;
- no real accepted manifest was read;
- no real `output/` scan was performed;
- no report artifact was read;
- no PDF, DOCX, HTML, Excel, or other artifact-content parsing was performed;
- no Research Report V1 integration was entered;
- no verified fact promotion is planned;
- no trading advice, investment conclusion, target price, portfolio, position,
  or technical signal output is planned;
- all future inputs are re-validated at the Phase 5 boundary;
- all four upstream payloads are required, non-`None`, and validator-passing;
- no partial upstream payload set can produce
  `autonomous_ticker_research_planning_result.v1`;
- `company_name` hint consistency is exact-only, with no fuzzy matching,
  abbreviation matching, alias inference, or Phase 5 identity resolution;
- readiness level is copied from `readiness_skeleton.v1`;
- readiness flags are constrained, planning-only, and cannot be promoted to
  Report V1 generation permission, template assembly permission, dashboard
  rendering permission, or investment advice;
- the required readiness-flags caveat is present in `caveats`;
- `data_gap_plan` items are structured dictionaries and remain neutral data
  collection planning;
- `blocked_reasons` items are structured dictionaries derived only from
  upstream blocking state;
- final output safety scan covers forbidden markers, prohibited keys, payload
  safety, and `not_for_trading_advice=true` enforcement;
- bounded hypothesis source readiness consistency is enforced;
- `allowed_downstream_use` is not promoted;
- `experimental_report_context_candidate` remains non-report planning context;
- blocked hypotheses, blocked reasons, caveats, and data gaps are preserved;
- future tests are targeted and synthetic;
- regression subset is identified;
- git status remains clean except unrelated mojibake untracked files and this
  planning document until it is reviewed.

## 12. Next Stage Recommendation

Recommended next stage after this document is reviewed:

```text
Phase 5 planning acceptance review
```

Do not enter Phase 5 implementation until the planning acceptance review is
explicitly approved.
