# Phase 3R Synthetic Readiness Dry-run Review Plan

Date: 2026-05-30

Stage: Phase 3R synthetic runtime / dry-run readiness review planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not read report
artifacts, does not generate reports, does not generate hypotheses, does not
call providers, does not use network, does not read tokens, does not commit,
and does not push.

Reference baseline:

- Phase 3 Deterministic Evidence Inventory + Readiness Skeleton baseline:
  `c0f8b1c389d2b9060cb68f3dcc38e8577eb235c3`.
- Phase 3 acceptance summary:
  `64d748a806422e93a568d243b0f36a8f94e5219b`.

## 1. Phase 3R Goal

Phase 3R plans a synthetic dry-run review of the accepted Phase 3 deterministic
evidence readiness layer.

Phase 3R uses only synthetic in-memory `ticker_local_artifact_inventory.v1`
inputs to verify that Phase 3 readiness outputs remain fail-closed.

Phase 3R should verify:

- `deterministic_evidence_inventory.v1`;
- `readiness_skeleton.v1`;
- readiness-level assignment from artifact-state only;
- fail-closed report readiness flags;
- caveats and lineage references;
- mandatory `not_for_trading_advice=true`;
- absence of report content, investment advice, recommendation, target price,
  position sizing, and trading advice keys.

Phase 3R must not:

- read a real `accepted_manifest`;
- scan real `output/`;
- read a report artifact;
- generate a report;
- generate a hypothesis;
- call or connect to any provider;
- enter the hypothesis generator;
- enter the orchestrator;
- enter Research Report V1 integration;
- promote fixtures;
- enter Dashboard / Batch work.

The planned review is intentionally synthetic. It proves deterministic runtime
behavior on controlled dict/list inputs, not real-world data collection or
report readiness for a real ticker.

## 2. Synthetic Dry-run Scenarios

Future Phase 3R tests should cover at least the following synthetic scenarios.
All inputs are in-memory dictionaries and lists.

| Scenario | Required expectation |
| --- | --- |
| `accepted_report_ready` positive path | Resolved identity, no conflicts, no safety marker, available official/business evidence artifact-state, available critical financial artifact-state, `can_generate_accepted_report=true`, `can_generate_experimental_report=false`, no report content. |
| `experimental_report_ready` positive path | Resolved identity, no conflicts, no safety marker, enough artifact-state for experimental readiness, `can_generate_accepted_report=false`, `can_generate_experimental_report=true`, explicit caveats, no report content. |
| Missing official/business evidence | `readiness_level=data_collection_required` or stricter, both report flags `false`, fail-closed reason names official/business evidence gap. |
| Missing critical financial artifacts | `readiness_level=data_collection_required` or stricter, both report flags `false`, fail-closed reason names critical financial artifact gap. |
| `conflict_artifacts` plus otherwise good artifacts | `readiness_level=evidence_conflict_review_required` or `blocked`, both report flags `false`, conflict caveat and lineage retained. |
| Identity `ambiguous` | Both report flags `false`; readiness is classification review, conflict review, data collection, or blocked according to the synthetic input. |
| Identity `not_found` | Both report flags `false`; no fallback ticker or company-name-only recovery. |
| Identity `conflict_requires_review` | Both report flags `false`; readiness fails closed with conflict/review reason. |
| Identity `blocked` | `readiness_level=blocked`, both report flags `false`. |
| `candidate_only` only | Candidate rows cannot become accepted or experimental readiness; both flags `false`. |
| `review_required` only | Review-required rows cannot become accepted or experimental readiness; both flags `false`. |
| Only ignored artifacts without safety violation | `readiness_level=data_collection_required`, both flags `false`, no safety block. |
| Only ignored artifacts with safety / forbidden marker | `readiness_level=blocked`, both flags `false`. |
| Artifact-state with accepted/current but not verified fact | Output may preserve accepted/current artifact-state but must not emit verified facts or report claims. |
| Output contains no report/recommendation/target price/trading advice keys | Returned payloads must not contain report sections, recommendation, target price, trading advice, position sizing, portfolio action, or report-generation content keys. |

Additional recommended scenario checks:

- `not_for_trading_advice=false` is rejected or blocked;
- mismatched request ticker and inventory ticker fails closed;
- candidate-only plus otherwise insufficient artifacts still fails closed;
- review-required plus otherwise insufficient artifacts still fails closed;
- experimental readiness cannot bypass identity, conflict, safety,
  official/business, or critical financial artifact gates;
- returned `caveats` and `lineage_refs` are copied and do not share mutable
  input state.

## 3. Input Constraints

Phase 3R dry-run inputs are limited to synthetic Python dict/list data.

Allowed inputs:

- synthetic request dictionaries;
- synthetic `ticker_local_artifact_inventory.v1` dictionaries;
- synthetic `local_artifact_index_row.v1` dictionaries nested inside the
  synthetic inventory;
- scalar strings, booleans, and lists needed to model artifact-state;
- `not_for_trading_advice=true`.

Disallowed inputs and behavior:

- no real `accepted_manifest`;
- no real `output/`;
- no report artifact;
- no `artifact_path` read;
- no `artifact_path` existence check;
- no `Path.exists`, `Path.stat`, or equivalent filesystem metadata probe for
  artifact paths;
- no real file hash calculation;
- no real artifact content read;
- no report content read;
- no provider payload;
- no token, credential, `.env`, or MCP config read;
- no file write of any kind during dry-run execution;
- no fixture write or promotion;
- no runtime artifact write.

The dry-run should treat `artifact_path` values, if present in synthetic rows,
as inert strings only. They are lineage / artifact-state strings, not filesystem
targets.

All test inputs should be defensively copied before invocation and compared
after invocation to prove no caller-owned dict/list mutation.

## 4. Output Checks

Phase 3R should inspect both returned Phase 3 payloads:

- `deterministic_evidence_inventory.v1`;
- `readiness_skeleton.v1`.

Required readiness checks:

- `readiness_level`;
- `can_generate_accepted_report`;
- `can_generate_experimental_report`;
- `fail_closed_reason`;
- `caveats`;
- `lineage_refs`;
- `not_for_trading_advice=true`.

Required safety / boundary checks:

- output is artifact-state only;
- output contains no report content;
- output contains no investment advice;
- output contains no recommendation;
- output contains no target price;
- output contains no trading advice;
- output contains no position sizing;
- output contains no portfolio action;
- output contains no generated hypothesis;
- output contains no Research Report V1 section payload;
- output contains no provider response payload;
- accepted/current artifact-state is not promoted to verified fact state;
- `lineage_refs` point back to synthetic artifact-state inputs, not real files.

Suggested forbidden output key scan:

```text
report
report_sections
research_report
recommendation
target_price
trading_advice
investment_advice
position_size
portfolio_action
hypothesis
provider_payload
accepted_manifest
output_scan
artifact_content
verified_facts
```

The key scan should apply to returned payload dictionaries only. It must not
scan the real repository, real `output/`, or artifact paths.

## 5. Expected Files

Future Phase 3R implementation should default to changing only:

```text
tests/test_evidence_readiness.py
```

Default file policy:

- Do not modify production code during Phase 3R planning or initial dry-run
  test implementation.
- Add synthetic dry-run coverage to the existing evidence readiness test file
  because Phase 3R reviews the accepted Phase 3 evidence readiness surface.
- Keep scenarios focused on Phase 3 readiness behavior, not Phase 2 inventory
  construction.
- Do not add runtime fixtures.
- Do not write under `output/`.
- Do not modify accepted manifest, provider, report, CLI, orchestrator,
  Dashboard, or Batch code.

A dedicated dry-run test file may be proposed only if there is a clear review
reason, such as:

- `tests/test_evidence_readiness.py` becomes materially hard to review;
- monkeypatch-heavy no-IO guards obscure existing Phase 3 tests;
- the dry-run scenario matrix needs a dedicated naming surface to separate
  runtime-readiness review from core unit tests.

If a dedicated file is proposed, the future implementation summary must name
the file explicitly, explain why the default file was insufficient, and keep the
change set limited to tests unless a true production bug is discovered.

Production code should not change unless synthetic dry-run tests expose a true
bug in the accepted Phase 3 implementation. If that happens, the fix must be
minimal, documented, and reviewed as a bug fix rather than scope expansion.

## 6. Prohibited Work

Phase 3R planning and future dry-run review must not:

- modify production code unless dry-run tests reveal a true bug;
- read the real accepted manifest;
- scan real `output/`;
- read report artifacts;
- read artifact contents;
- check artifact path existence;
- compute real file hashes;
- write `output/`;
- write fixtures;
- write runtime artifacts;
- promote fixtures;
- enter the hypothesis generator;
- enter the orchestrator;
- enter Research Report V1 integration;
- generate report content;
- connect to live providers;
- connect to CNInfo;
- connect to Tushare;
- connect to AkShare;
- read tokens;
- read credentials;
- read `.env`;
- use network;
- call MCP for provider or data access;
- enter Dashboard / Batch work;
- process unrelated mojibake untracked files;
- commit;
- push.

## 7. Acceptance Checklist

Documentation planning acceptance:

- [ ] Only this Phase 3R planning document is added.
- [ ] No production code is written.
- [ ] No tests are written.
- [ ] No runtime artifact is generated.
- [ ] No real accepted manifest is read.
- [ ] No real `output/` scan is performed.
- [ ] No report artifact is read.
- [ ] No provider, CNInfo, Tushare, AkShare, token, MCP, or network work is
  performed.
- [ ] No hypothesis generator, orchestrator, Dashboard / Batch, or Research
  Report V1 integration work is performed.
- [ ] Synthetic dry-run scenarios are planned.
- [ ] Input constraints are documented.
- [ ] Output checks are documented.
- [ ] Expected files are documented.
- [ ] Prohibited work is documented.
- [ ] No unrelated mojibake untracked files are processed.
- [ ] `git status --short` is reviewed before handoff.
- [ ] `git log --oneline -5` is reviewed before handoff.
- [ ] No commit is created.
- [ ] No push is performed.

Future Phase 3R dry-run acceptance, only after explicit approval:

- [ ] Only expected tests changed by default:
  `tests/test_evidence_readiness.py`.
- [ ] No production code change unless a true bug is found.
- [ ] Any production bug fix is minimal and explicitly justified.
- [ ] No real file IO.
- [ ] No real accepted manifest read.
- [ ] No real `output/` scan.
- [ ] No report artifact read.
- [ ] No artifact path existence check.
- [ ] No real file hash calculation.
- [ ] No provider or network access.
- [ ] No token, credential, `.env`, or MCP data access.
- [ ] All planned synthetic dry-run scenarios are covered.
- [ ] `accepted_report_ready` positive path is covered.
- [ ] `experimental_report_ready` positive path is covered.
- [ ] Missing official/business evidence is covered.
- [ ] Missing critical financial artifacts is covered.
- [ ] Conflict artifacts plus otherwise good artifacts is covered.
- [ ] Identity ambiguous / not_found / conflict_requires_review / blocked are
  covered.
- [ ] Candidate-only only is covered.
- [ ] Review-required only is covered.
- [ ] Only ignored without safety violation is covered.
- [ ] Only ignored with safety / forbidden marker is covered.
- [ ] Accepted/current artifact-state is not promoted to verified fact state.
- [ ] Output has no report, recommendation, target price, trading advice,
  investment advice, position sizing, portfolio action, or hypothesis keys.
- [ ] Output remains artifact-state only.
- [ ] Targeted tests pass.
- [ ] Regression subset passes.
- [ ] `git status --short` is clean except unrelated mojibake untracked files.

Suggested future targeted command:

```text
python -m pytest tests/test_evidence_readiness.py -p no:cacheprovider
```

Suggested future regression subset:

```text
python -m pytest tests/test_evidence_readiness.py tests/test_local_artifact_index.py tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py -p no:cacheprovider
```

Phase 3R should move to dry-run implementation only after this planning
document is accepted and a separate implementation request is made.
