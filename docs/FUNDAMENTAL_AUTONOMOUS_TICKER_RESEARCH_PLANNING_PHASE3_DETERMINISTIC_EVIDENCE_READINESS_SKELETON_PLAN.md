# Phase 3 Deterministic Evidence Inventory + Readiness Skeleton Plan

Date: 2026-05-30

Stage: Phase 3 Deterministic evidence inventory and readiness skeleton planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not read report artifacts,
does not write manifests, does not write output files, does not write fixtures,
does not call providers, does not use network, does not read tokens, does not
call MCP, does not commit, and does not push.

Reference baseline:

- Phase 2C Explicit Ticker Artifact Inventory Builder baseline:
  `34af90b35f0eb16d7874ac34350ae4bfef8aa92d`.
- Phase 2C acceptance summary:
  `4a5717c4f22725d92190f97c1243972ab7ce20c8`.

## 1. Phase 3 Goal

Phase 3 plans a deterministic readiness layer above the accepted Phase 2C
`ticker_local_artifact_inventory.v1` payload.

Phase 3 should generate:

- `deterministic_evidence_inventory.v1`;
- `readiness_skeleton.v1`.

The future implementation should consume validated artifact-state inventory and
produce conservative readiness state without reading artifact content or
promoting artifact state into verified facts.

Phase 3 plans only:

- deterministic evidence inventory assembly from
  `ticker_local_artifact_inventory.v1`;
- deterministic grouping of available, missing, candidate-only,
  review-required, conflict, and ignored artifact-state rows;
- readiness skeleton generation;
- fail-closed report readiness flags;
- caveats and lineage references back to explicit Phase 2C inventory inputs;
- mandatory `not_for_trading_advice=true` boundaries.

Phase 3 does not plan:

- hypothesis generation;
- macro reasoning;
- industry reasoning;
- Research Report V1 integration;
- real accepted manifest reading;
- real `output/` scanning;
- report artifact reading;
- report artifact content parsing;
- official disclosure raw text reading;
- live provider connection;
- CNInfo, Tushare, AkShare, or other provider access;
- fixture promotion;
- verified fact storage;
- trading advice.

The future implementation should start only after this planning document is
accepted in a separate review step.

## 2. Input Design

The future Phase 3 builder should accept one explicit request dictionary or a
small typed equivalent. Accepted inputs are limited to:

- a validated `ticker_local_artifact_inventory.v1` payload;
- validated `local_artifact_index_row.v1` rows already present in that
  inventory;
- optional Phase 1 schema constants, including readiness and safety constants;
- explicit `stock_code` and optional `company_name` hints supplied by the
  caller;
- required `not_for_trading_advice=true`.

Planned request shape:

```json
{
  "schema_version": "deterministic_evidence_readiness_request.v1",
  "stock_code": "600406",
  "company_name": "optional auxiliary name hint",
  "ticker_local_artifact_inventory": {
    "schema_version": "ticker_local_artifact_inventory.v1"
  },
  "not_for_trading_advice": true
}
```

Input field rules:

- `stock_code`: required exact six-digit ticker. It must match the inventory
  `stock_code`.
- `company_name`: optional auxiliary hint only. It cannot independently resolve
  identity.
- `ticker_local_artifact_inventory`: required validated Phase 2C inventory.
- `artifact_rows`: must come from the validated inventory payload and must pass
  `local_artifact_index_row.v1` validation if revalidated defensively.
- `not_for_trading_advice`: required and must be `true`.

Rejected input sources:

- raw accepted manifest dictionaries;
- accepted manifest file paths that Phase 3 would open;
- raw `output/` scan results;
- report artifact content;
- parsed report artifact sections;
- provider live responses;
- official disclosure raw text;
- hypotheses;
- Research Report V1 section payloads;
- prompt/model outputs;
- token, credential, or `.env` contents.

Phase 3 must not repair incomplete inputs by reading files, scanning
directories, calling providers, or entering any report generator.

All accepted inputs should be defensively copied. Caller-owned dictionaries and
lists must not be mutated.

## 3. Output Design

Phase 3 should produce two deterministic planning payloads.

### 3.1 `deterministic_evidence_inventory.v1`

This payload is an artifact-state evidence inventory. It is not a verified fact
store.

Planned shape:

```json
{
  "schema_version": "deterministic_evidence_inventory.v1",
  "stock_code": "600406",
  "company_name": "optional auxiliary name hint",
  "identity_resolution_status": "resolved",
  "evidence_inventory": [],
  "available_data_artifacts": [],
  "missing_data_artifacts": [],
  "candidate_only_artifacts": [],
  "review_required_artifacts": [],
  "conflict_artifacts": [],
  "ignored_artifacts": [],
  "caveats": [],
  "lineage_refs": [],
  "not_for_trading_advice": true
}
```

Required output fields:

- `schema_version`: fixed value `deterministic_evidence_inventory.v1`.
- `stock_code`: exact six-digit ticker from the request and inventory.
- `company_name`: caller hint or conservative inventory value when
  non-conflicting.
- `identity_resolution_status`: copied or mapped from validated Phase 2C
  inventory identity state.
- `evidence_inventory`: normalized artifact-state inventory entries derived
  from Phase 2C rows.
- `available_data_artifacts`: rows with accepted artifact-state availability,
  excluding candidate-only, review-required, conflict, ignored, or missing
  rows.
- `missing_data_artifacts`: rows whose validated artifact state says a required
  data artifact is missing.
- `candidate_only_artifacts`: rows whose validated artifact state is
  `candidate_only`.
- `review_required_artifacts`: rows whose validated artifact or review status
  requires review before downstream use.
- `conflict_artifacts`: rows whose artifact or review status indicates open
  conflict.
- `ignored_artifacts`: rows explicitly ignored by Phase 2C path, schema, ticker,
  or artifact policy.
- `caveats`: inventory-level caveats, including artifact-state / evidence-state
  boundary caveats.
- `lineage_refs`: references to Phase 2C inventory and row lineage, not copied
  content facts.
- `not_for_trading_advice`: always `true`.

### 3.2 `readiness_skeleton.v1`

This payload is a deterministic readiness decision scaffold. It does not
contain report prose, investment conclusions, hypotheses, or verified facts.

Planned shape:

```json
{
  "schema_version": "readiness_skeleton.v1",
  "stock_code": "600406",
  "company_name": "optional auxiliary name hint",
  "identity_resolution_status": "resolved",
  "evidence_inventory": [],
  "available_data_artifacts": [],
  "missing_data_artifacts": [],
  "candidate_only_artifacts": [],
  "review_required_artifacts": [],
  "conflict_artifacts": [],
  "ignored_artifacts": [],
  "readiness_level": "data_collection_required",
  "can_generate_accepted_report": false,
  "can_generate_experimental_report": false,
  "fail_closed_reason": "critical evidence is missing",
  "caveats": [],
  "lineage_refs": [],
  "not_for_trading_advice": true
}
```

Required output fields:

- `schema_version`: fixed value `readiness_skeleton.v1`.
- `stock_code`: exact six-digit ticker from the request and inventory.
- `company_name`: same conservative value used by the evidence inventory.
- `identity_resolution_status`: deterministic identity state.
- `evidence_inventory`: copied from the deterministic evidence inventory or
  referenced by lineage according to the future implementation choice.
- `available_data_artifacts`: available artifact-state rows.
- `missing_data_artifacts`: missing artifact-state rows.
- `candidate_only_artifacts`: candidate-only artifact-state rows.
- `review_required_artifacts`: review-required artifact-state rows.
- `conflict_artifacts`: conflict artifact-state rows.
- `ignored_artifacts`: ignored artifact-state rows.
- `readiness_level`: one of the Phase 1 aligned readiness levels.
- `can_generate_accepted_report`: fail-closed boolean.
- `can_generate_experimental_report`: fail-closed boolean.
- `fail_closed_reason`: empty only when readiness permits the requested
  downstream report class.
- `caveats`: readiness caveats, including no-fact-promotion caveats.
- `lineage_refs`: Phase 2C and Phase 3 lineage references.
- `not_for_trading_advice`: always `true`.

Output must not include:

- verified facts;
- generated hypotheses;
- report sections;
- provider payloads;
- official disclosure raw text;
- report artifact content;
- accepted manifest raw content;
- output scan results.

## 4. Readiness Levels

Phase 3 should reuse or align exactly with Phase 1 readiness levels:

```text
accepted_report_ready
experimental_report_ready
data_collection_required
classification_review_required
evidence_conflict_review_required
blocked
```

Planned meanings:

| Readiness level | Planned meaning |
| --- | --- |
| `accepted_report_ready` | Identity is resolved, no open conflicts exist, required official/business evidence and critical financial artifacts are available as artifact state, no candidate-only or review-required rows are needed for accepted readiness, and all safety gates pass. |
| `experimental_report_ready` | Identity is resolved and no open conflicts exist, but the evidence set only supports an explicitly caveated experimental report skeleton. Candidate-only and review-required artifacts still cannot become accepted evidence. |
| `data_collection_required` | Required official/business evidence or critical financial artifacts are missing, ignored, or not supplied. |
| `classification_review_required` | Artifact classification, candidate-only rows, review-required rows, unknown source family, or ambiguous grouping requires human review. |
| `evidence_conflict_review_required` | Conflict rows, identity conflicts, duplicate conflicts, or conflicting artifact-state signals are present. |
| `blocked` | Safety violation, invalid input, `not_for_trading_advice=false`, forbidden marker, or structurally unusable inventory blocks planning. |

### 4.1 Identity Resolution Status Alignment

Phase 3 should reuse the Phase 1 identity resolution enum by default:

```text
resolved
ambiguous
not_found
conflict_requires_review
blocked
```

Phase 3 must not introduce new identity enum values such as `resolved_exact` or
`resolved_fuzzy` unless a separate schema design adds and validates them first.
If a future phase needs exact, fuzzy, alias, historical-name, or
company-name-only identity distinctions, that distinction must be designed
separately and must not be invented inside the Phase 3 implementation.

Identity readiness rules:

- `accepted_report_ready` is allowed only when
  `identity_resolution_status == "resolved"`.
- `experimental_report_ready` is allowed only when
  `identity_resolution_status == "resolved"`.
- `ambiguous`, `not_found`, `conflict_requires_review`, and `blocked` must set
  `can_generate_accepted_report=false`.
- `ambiguous`, `not_found`, `conflict_requires_review`, and `blocked` must set
  `can_generate_experimental_report=false`.

### 4.2 Readiness Evidence Categories

Phase 3 may derive deterministic readiness categories from artifact-state rows.
These categories are readiness roles only. They are not verified facts,
investment conclusions, or report claims.

#### 4.2.1 `official_business_evidence_artifact_state`

This category means the inventory contains artifact state that can play the
official/business evidence role for readiness. It is not verified official or
business fact.

The category may be determined only from deterministic artifact-state fields,
such as:

- `artifact_type`;
- `source_family`;
- `source_status`;
- `review_status`;
- `caveats`.

Rules:

- `candidate_only`, `review_required`, and `conflict_open` rows cannot satisfy
  `accepted_report_ready`.
- Missing official/business evidence must set
  `can_generate_accepted_report=false`.
- Missing official/business evidence defaults to
  `can_generate_experimental_report=false`; the current Phase 3 does not allow
  data-gap-only experimental readiness.
- If a future policy wants data-gap-only experimental artifacts, it must be
  designed separately before implementation.

#### 4.2.2 `critical_financial_artifact_state`

This category means the inventory contains artifact state that can play the
critical financial data role for readiness. It is not verified financial fact.

The category may be mapped only from artifact-state rows, such as normalized
fundamentals, provider-separated fundamentals, financial summary artifacts,
accepted/current report artifact state, or another explicitly allowed financial
artifact-state family. The mapping must not read artifact content.

Rules:

- `candidate_only`, `review_required`, and `conflict_open` rows cannot satisfy
  `accepted_report_ready`.
- Missing critical financial artifacts must set
  `can_generate_accepted_report=false`.
- Missing critical financial artifacts must set
  `can_generate_experimental_report=false`.
- Missing critical financial artifacts should produce
  `readiness_level=data_collection_required`, unless safety violations,
  forbidden markers, or conflict states require `blocked` or
  `evidence_conflict_review_required`.

## 5. Deterministic Rules

The future implementation must apply deterministic rules only. No model call,
provider call, fuzzy reasoning, or content inference is allowed.

Required fail-closed rules:

- If identity is unresolved, ambiguous, invalid, missing, blocked, or otherwise
  not confidently resolved, then `can_generate_accepted_report=false`.
- If identity is unresolved, ambiguous, invalid, missing, blocked, or otherwise
  not confidently resolved, then `can_generate_experimental_report=false`.
- If identity status is `conflict_open`, `conflict_requires_review`, or any
  equivalent open conflict state, then `can_generate_accepted_report=false`.
- If identity status is `conflict_open`, `conflict_requires_review`, or any
  equivalent open conflict state, then
  `can_generate_experimental_report=false`.
- If any `conflict_artifacts` exist, readiness must be
  `evidence_conflict_review_required` or `blocked`, and
  both report-generation flags must be `false`.
- When `conflict_artifacts` is non-empty, Phase 3 must actively set
  `can_generate_accepted_report=false` and
  `can_generate_experimental_report=false`; it must not rely on a downstream
  validator to catch the conflict.
- If only ignored artifacts exist, readiness must be
  `data_collection_required` or `blocked`.
- If only ignored artifacts exist and a safety violation or forbidden marker is
  present, readiness must be `blocked`.
- If only ignored artifacts exist and no safety violation or forbidden marker
  is present, readiness must be `data_collection_required`.
- If only ignored artifacts exist, both report-generation flags must be
  `false`.
- If no artifacts exist, readiness must be `data_collection_required` or
  `blocked`.
- `candidate_only_artifacts` must never become accepted evidence.
- `review_required_artifacts` must never become accepted evidence.
- Accepted or current artifact state does not equal verified fact state.
- Manifest-derived artifact rows are artifact-state only.
- If no official/business evidence artifact state is available, then
  `can_generate_accepted_report=false`.
- If no critical financial artifact state is available, then
  `can_generate_accepted_report=false`.
- If a safety violation is detected, readiness must be `blocked`, and both
  report-generation flags must be `false`.
- If `not_for_trading_advice=false`, the request must be rejected and no
  readiness payload should be returned as valid.
- If forbidden fact-promotion, fixture-promotion, provider-switch,
  report-write, trading-advice, target-price, position-sizing, or portfolio
  markers appear, readiness must be `blocked`.
- If inventory `stock_code` differs from the requested `stock_code`, readiness
  must be `blocked` or `evidence_conflict_review_required`; no fallback ticker
  is allowed.
- Company-name-only matching, alias matching, historical-name matching,
  English-name matching, and mojibake-name matching are not allowed.
- `can_generate_experimental_report=true` is allowed only for
  `experimental_report_ready` or `accepted_report_ready`.
- `can_generate_experimental_report=true` must never bypass identity,
  conflict, or safety blockers.
- `can_generate_accepted_report=true` is allowed only for
  `accepted_report_ready`.

### 5.1 Positive Entry Conditions For `accepted_report_ready`

`accepted_report_ready` is allowed only when all of the following conditions are
true:

- `identity_resolution_status == "resolved"`;
- no safety violation exists;
- `conflict_artifacts` is empty;
- `not_for_trading_advice == true`;
- `official_business_evidence_artifact_state` is present and usable for formal
  readiness;
- `critical_financial_artifact_state` is present and usable for formal
  readiness;
- no `candidate_only`, `review_required`, or `conflict_open` artifact blocks
  critical readiness;
- no forbidden marker is present;
- no manifest, output scan, report artifact content, or provider-content
  assumption is used.

When `accepted_report_ready` is assigned:

- `can_generate_accepted_report=true`;
- `can_generate_experimental_report` may be `true` or `false`, but either value
  is still only readiness state and must not trigger report generation.

### 5.2 Positive Entry Conditions For `experimental_report_ready`

`experimental_report_ready` is allowed only when all of the following
conditions are true:

- `identity_resolution_status == "resolved"`;
- no safety violation exists;
- `conflict_artifacts` is empty;
- `not_for_trading_advice == true`;
- at least one available non-ignored artifact-state row exists;
- `official_business_evidence_artifact_state` is present;
- `critical_financial_artifact_state` is present;
- no forbidden marker is present;
- `accepted_report_ready` conditions are not fully satisfied, but enough
  artifact-state support exists for caveated experimental readiness.

When `experimental_report_ready` is assigned:

- `can_generate_accepted_report=false`;
- `can_generate_experimental_report=true`.

If official/business evidence or critical financial artifacts are missing,
Phase 3 must not assign `experimental_report_ready`; it should return
`data_collection_required` or a stricter state.

### 5.3 Readiness Flag Product Boundary

`can_generate_accepted_report` and `can_generate_experimental_report` are
readiness-level indicators only.

They do not:

- trigger report generation;
- contain report content;
- constitute investment advice;
- grant Research Report V1 integration permission;
- authorize any downstream report phase by themselves.

Any downstream report phase must go through a separate L1 Evidence Integration
and report-generation design before report content can be produced.

Recommended artifact-family minimums for accepted readiness:

- at least one available official disclosure or official/business evidence
  artifact-state row;
- at least one available critical financial artifact-state row, such as
  normalized fundamentals, provider fundamentals, score/confidence
  explainability, or another explicitly accepted financial source family from
  Phase 2C schema;
- no conflicts;
- no required classification review;
- no safety caveats requiring block.

These minimums are artifact-state minimums only. They do not prove that the
underlying business or financial facts are correct.

## 6. Artifact-State vs Evidence-State Boundary

Phase 3 must keep a hard boundary between artifact state and evidence state:

- The deterministic evidence inventory is not a verified fact store.
- An available artifact is not a verified fact.
- A missing artifact is a data gap, not an investment conclusion.
- A candidate-only artifact is a review need, not a fact.
- A review-required artifact is workflow state, not report permission.
- A conflict artifact must block accepted report readiness.
- Accepted/current artifact state means the artifact row is accepted/current as
  artifact state only.
- Manifest-derived rows are artifact-state, even when the manifest calls them
  accepted or current.
- Phase 3 does not read artifact content, so it cannot judge content facts.
- Phase 3 may say "the inventory contains available official disclosure
  artifact state"; it must not say "the official disclosure fact is verified."
- Phase 3 may say "critical financial artifacts are missing"; it must not infer
  company quality, valuation, risk, or investment action from that gap.
- Phase 3 may produce caveated readiness flags; it must not generate report
  claims or hypotheses.

The term "evidence inventory" in Phase 3 means deterministic organization of
artifact-state rows for readiness planning. It does not mean verified factual
evidence suitable for report claims without later review and content-aware
processing.

## 7. Relationship To Phase 1 / Phase 2

Phase 3 depends on the accepted planning foundations:

- Phase 1 provides schema, readiness levels, fail-closed report flags, and
  safety boundaries.
- Phase 2A provides `local_artifact_index_row.v1` and local artifact row
  validation.
- Phase 2B provides manifest locator planning, synthetic manifest parser
  planning, and manifest-entry-to-artifact-row adapter planning.
- Phase 2C provides `ticker_local_artifact_inventory.v1`.
- Phase 3 builds deterministic evidence inventory and readiness skeletons from
  Phase 2C inventory.

Phase 3 must not bypass validators:

- Validate or defensively revalidate `ticker_local_artifact_inventory.v1`.
- Validate or defensively revalidate contained `local_artifact_index_row.v1`
  rows.
- Reuse or align with Phase 1 readiness constants.
- Reuse Phase 1 safety scanning for forbidden markers when applicable.
- Preserve `not_for_trading_advice=true`.

Phase 3 must not enter:

- AI hypothesis generator;
- orchestrator integration;
- Research Report V1 integration;
- provider integration;
- CLI integration;
- output scanning;
- real accepted manifest reading.

## 8. Tests Strategy

Tests are not written in this planning stage. Future Phase 3 tests should use
only pure dictionaries, strings, and synthetic in-memory rows.

Required future test boundaries:

- Do not depend on the real accepted manifest.
- Do not depend on real `output/`.
- Do not read report artifacts.
- Do not write `output/`, fixtures, manifests, or runtime artifacts.
- Do not call providers.
- Do not use network.
- Do not read tokens, credentials, `.env`, or MCP config.
- Do not process unrelated mojibake untracked files.

Required future coverage:

- valid inventory produces a deterministic evidence inventory and readiness
  skeleton;
- no artifacts results in `data_collection_required` or `blocked`;
- all ignored artifacts results in `data_collection_required` or `blocked`;
- candidate-only artifacts alone cannot produce accepted readiness;
- review-required artifacts alone cannot produce accepted readiness;
- conflict artifacts produce `evidence_conflict_review_required` or `blocked`;
- conflict artifacts plus otherwise good available artifacts still set
  `can_generate_accepted_report=false` and
  `can_generate_experimental_report=false`;
- identity `ambiguous`, `not_found`, `conflict_requires_review`, and `blocked`
  all set both report-generation flags to `false`;
- missing official/business evidence prevents accepted readiness;
- missing official/business evidence prevents experimental readiness in current
  Phase 3 policy;
- missing critical financial artifacts prevents accepted readiness;
- missing critical financial artifacts prevents experimental readiness;
- accepted/current artifact state is not treated as verified fact;
- manifest-derived artifact rows remain artifact-state only;
- safety marker violations are rejected or blocked;
- `not_for_trading_advice=false` is rejected;
- experimental readiness cannot bypass identity, conflict, or safety blockers;
- experimental readiness positive path requires resolved identity, no conflict,
  no safety violation, official/business evidence, and critical financial
  artifacts;
- identity mismatch fails closed;
- company-name-only matching is not allowed;
- no fallback to retained sample tickers;
- only ignored artifacts with a safety violation returns `blocked` and both
  report-generation flags `false`;
- only ignored artifacts without a safety violation returns
  `data_collection_required` and both report-generation flags `false`;
- candidate-only artifacts alone cannot produce accepted or experimental
  readiness;
- review-required artifacts alone cannot produce accepted or experimental
  readiness;
- readiness flags do not imply report generation or Research Report V1
  integration;
- output contains no report section, recommendation, target price, trading
  advice, or report-generation permission keys;
- no input mutation;
- no shared mutable `caveats` or `lineage_refs`;
- no file IO;
- no directory scan;
- no provider or network call.

Recommended test techniques:

- Build all inputs as dicts and lists.
- Use `copy.deepcopy` before and after calls to prove no input mutation.
- Monkeypatch `builtins.open`, `Path.read_text`, `Path.read_bytes`,
  `Path.write_text`, and `Path.write_bytes` to fail if called.
- Monkeypatch `glob.glob`, `Path.glob`, `Path.rglob`, and `os.walk` to fail if
  called.
- Monkeypatch provider/client entry points to fail if called.
- Mutate returned `caveats` or `lineage_refs` and assert caller-owned inputs and
  sibling rows are unchanged.

Suggested future targeted command:

```text
python -m pytest tests/test_evidence_readiness.py -p no:cacheprovider
```

Suggested future regression subset:

```text
python -m pytest tests/test_evidence_readiness.py tests/test_local_artifact_index.py tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py -p no:cacheprovider
```

## 9. Expected Files

Future implementation should default to adding only:

```text
src/fundamental_skill/research_planning/evidence_readiness.py
tests/test_evidence_readiness.py
```

Default file policy:

- Prefer a new `evidence_readiness.py` module because Phase 3 is a distinct
  deterministic readiness layer above the Phase 2C local artifact inventory.
- Keep `local_artifact_index.py` as the Phase 2A/2C artifact-row and inventory
  surface. Do not expand it into readiness scoring unless implementation review
  finds a concrete reason.
- Prefer `tests/test_evidence_readiness.py` so Phase 3 no-read / no-write /
  no-provider tests stay focused and do not obscure Phase 2 local artifact
  index tests.
- Do not modify `src/fundamental_skill/research_planning/__init__.py` unless a
  later accepted implementation step requires public exports and documents why.
- Do not modify pipelines.
- Do not modify Research Report V1.
- Do not modify accepted manifest code.
- Do not modify manifest writers.
- Do not modify providers.
- Do not modify CLI.
- Do not modify fixtures.
- Do not modify `output/`.
- Do not process unrelated mojibake untracked files.

An implementation may instead reuse existing modules only if a separate review
finds the Phase 3 surface is small enough to stay in an existing file without
blurring Phase 2 artifact-index responsibilities. If that happens, the
implementation summary must explicitly justify the deviation and keep the
change set minimal.

## 10. Acceptance Checklist

Documentation planning acceptance:

- [ ] Only this Phase 3 planning document is added.
- [ ] No production code is written.
- [ ] No tests are written.
- [ ] No runtime artifact is generated.
- [ ] No real accepted manifest is read.
- [ ] No `output/` scan is performed.
- [ ] No report artifact is read.
- [ ] No manifest is written.
- [ ] No output file is written.
- [ ] No fixture is written or promoted.
- [ ] No provider, CNInfo, Tushare, AkShare, token, MCP, or network work is
  performed.
- [ ] No verified fact promotion is performed.
- [ ] No hypothesis generation is performed.
- [ ] No orchestrator, pipeline, CLI, Dashboard / Batch, or Research Report V1
  integration work is performed.
- [ ] Readiness rules are fail-closed.
- [ ] Artifact-state vs evidence-state boundaries are documented.
- [ ] Future targeted tests are planned.
- [ ] Future regression subset is planned.
- [ ] Expected implementation files are documented.
- [ ] No unrelated mojibake untracked files are processed.
- [ ] `git status --short` is reviewed before handoff.
- [ ] `git log --oneline -5` is reviewed before handoff.
- [ ] No commit is created.
- [ ] No push is performed.

Future Phase 3 implementation acceptance, only after explicit approval:

- [ ] Modify only `src/fundamental_skill/research_planning/evidence_readiness.py`
  and `tests/test_evidence_readiness.py`, unless a separately justified minimal
  deviation is accepted.
- [ ] Accept validated `ticker_local_artifact_inventory.v1` only.
- [ ] Accept validated `local_artifact_index_row.v1` rows only.
- [ ] Reject raw accepted manifests.
- [ ] Reject raw output scan results.
- [ ] Reject report artifact content.
- [ ] Reject provider live responses.
- [ ] Reject hypotheses and Research Report V1 section payloads.
- [ ] Output `deterministic_evidence_inventory.v1`.
- [ ] Output `readiness_skeleton.v1`.
- [ ] Preserve `not_for_trading_advice=true`.
- [ ] Identity unresolved or conflicted fails closed.
- [ ] Conflict artifacts block accepted report readiness.
- [ ] Conflict artifacts also block experimental report readiness.
- [ ] Candidate-only artifacts never become accepted evidence.
- [ ] Review-required artifacts never become accepted evidence.
- [ ] Accepted/current artifact state never becomes verified fact state.
- [ ] Missing official/business evidence blocks accepted readiness.
- [ ] Missing official/business evidence blocks experimental readiness under
  current Phase 3 policy.
- [ ] Missing critical financial artifacts blocks accepted readiness.
- [ ] Missing critical financial artifacts blocks experimental readiness.
- [ ] Safety violations block readiness.
- [ ] Experimental readiness cannot bypass identity, conflict, or safety
  blockers.
- [ ] Readiness flags are indicators only and do not trigger report generation
  or Research Report V1 integration.
- [ ] No real manifest read.
- [ ] No output scan.
- [ ] No report artifact read.
- [ ] No artifact content read.
- [ ] No manifest, output, fixture, or runtime artifact write.
- [ ] No input mutation.
- [ ] No provider, token, MCP, or network access.
- [ ] No hypothesis generation.
- [ ] No Research Report V1 integration.
- [ ] Targeted `tests/test_evidence_readiness.py` passes.
- [ ] Regression subset passes.
- [ ] `git status --short` is clean except unrelated mojibake untracked files.

Phase 3 should move to implementation only after this planning document is
accepted and a separate implementation request is made.
