# Phase 5R Synthetic Planning Gate Assembly Dry-run Plan

Date: 2026-05-31

Stage: Phase 5R synthetic planning gate assembly dry-run planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not read report
artifacts, does not parse PDF, DOCX, HTML, Excel, or other artifact content,
does not generate reports, does not call providers, does not use network, does
not read tokens, does not process unrelated mojibake files, does not commit,
and does not push.

Reference baseline:

- Phase 5 Controlled Planning Gate Assembly baseline:
  `943ea5927c294ef63e713435e958586ad90405bd`.
- Phase 5 acceptance summary:
  `eb0e5d27cfe9c082ac03fea64a8ba2c15a237c42`.

## 1. Phase 5R Goal

Phase 5R plans a synthetic dry-run verification pass for the accepted Phase 5
controlled planning gate assembly.

Phase 5R uses only synthetic in-memory payloads:

- synthetic Phase 2C `ticker_local_artifact_inventory.v1`;
- synthetic Phase 3 `deterministic_evidence_inventory.v1`;
- synthetic Phase 3 `readiness_skeleton.v1`;
- synthetic Phase 4 `bounded_hypothesis_payload.v1`.

Phase 5R verifies only the behavior of:

- `autonomous_ticker_research_planning_result.v1`;
- fail-closed behavior for missing, inconsistent, or unsafe synthetic inputs;
- consistency behavior across ticker identity, company-name hint, readiness
  state, and bounded-hypothesis source readiness;
- product-boundary behavior that keeps the result planning-only and
  artifact-state-only.

Phase 5R must not:

- read a real `accepted_manifest`;
- scan real `output/`;
- read a report artifact;
- read or parse an `artifact_path`;
- check `artifact_path` existence;
- parse PDF, DOCX, HTML, Excel, or other artifact content;
- generate a report;
- generate Research Report V1 sections;
- connect to a provider;
- connect to CNInfo, Tushare, AkShare, MCP, browser, or network data sources;
- enter a real orchestrator;
- enter fixture promotion;
- enter Dashboard or Batch work;
- enter a trading engine.

The planned dry-run proves deterministic behavior on controlled dict/list
inputs. It does not prove real-world data collection readiness, real accepted
manifest compatibility, report-generation readiness, provider availability, or
investment usefulness for any ticker.

## 2. Synthetic Dry-run Scenarios

Future Phase 5R tests should cover at least the following synthetic scenarios.
All scenarios use in-memory dictionaries and lists only.

| Scenario | Required expectation |
| --- | --- |
| Valid full planning result | All four synthetic upstream payloads are present, internally valid, mutually consistent, and not-for-trading; output schema is `autonomous_ticker_research_planning_result.v1`, lineage refs are present, readiness flags follow the readiness skeleton, required caveat is present, no report content is emitted. |
| Missing Phase 2C inventory | Missing `ticker_local_artifact_inventory.v1` fails closed; no partial planning result is accepted. |
| Missing deterministic evidence inventory | Missing `deterministic_evidence_inventory.v1` fails closed; no partial planning result is accepted. |
| Missing readiness skeleton | Missing `readiness_skeleton.v1` fails closed; readiness cannot be inferred from hypotheses or artifact counts. |
| Missing bounded hypothesis payload | Missing `bounded_hypothesis_payload.v1` fails closed; no Phase 5 result is assembled from Phase 2C / Phase 3 alone. |
| `stock_code` mismatch | Any mismatch across request, Phase 2C, Phase 3 evidence, Phase 3 readiness, or Phase 4 payload fails closed. |
| `company_name` hint mismatch | A non-empty request hint that differs from any upstream `company_name` fails closed. |
| `company_name` fuzzy / abbreviation rejected | Fuzzy aliases, abbreviations, partial names, and inferred company aliases are rejected; Phase 5R allows exact-only consistency. |
| `source_readiness_level` mismatch | `bounded_hypothesis_payload.source_readiness_level` must match `readiness_skeleton.readiness_level`; mismatch fails closed. |
| Accepted readiness | Synthetic accepted readiness may produce `can_generate_accepted_report=true` only when all Phase 5 assembly checks pass; output remains planning-only and not report permission. |
| Experimental readiness | Synthetic experimental readiness may produce `can_generate_experimental_report=true` only when all Phase 5 assembly checks pass; output remains planning-only and not report permission. |
| Blocked readiness | Synthetic blocked readiness returns or validates as a blocked planning state with report flags false and structured blocked reasons. |
| Evidence conflict readiness | Synthetic evidence conflict readiness must not be accepted; conflict state appears in caveats, blocked reasons, or data gap planning without report conclusions. |
| Blocked hypothesis block reason propagation | `blocked_hypotheses.block_reason` may propagate to `blocked_reasons`; `blocked_hypotheses.hypothesis_text` must not appear in output. |
| Neutral data gap planning | `data_gap_plan` remains neutral data collection planning; it must not contain investment conclusions, target prices, buy/sell language, or report section content. |
| Required readiness-flags caveat | Final output includes the fixed caveat that readiness flags are planning indicators only and not Report V1 generation permission. |
| No report / investment / dashboard / template content | Final output contains no report section, research report, investment conclusion, target price, trading advice, dashboard payload, or template keys. |
| No file IO / provider / network | Dry-run execution does not open files, inspect filesystem metadata, read manifests, scan output, call providers, use network, or read tokens. |
| No input mutation | Caller-owned synthetic dict/list inputs are defensively copied or otherwise remain unchanged after invocation. |

Additional recommended coverage:

- `not_for_trading_advice=false` on request is rejected;
- `not_for_trading_advice=false` on any synthetic upstream payload is rejected;
- forbidden report or trading markers in synthetic upstream payloads fail
  closed and are not propagated;
- `allowed_downstream_use` is not promoted;
- `experimental_report_context_candidate` remains planning context only;
- lineage refs point to synthetic payload state only, not real files.

## 3. Input Constraints

Phase 5R dry-run inputs are limited to synthetic Python dict/list data.

Allowed inputs:

- synthetic request dictionaries;
- synthetic `ticker_local_artifact_inventory.v1` dictionaries;
- synthetic `deterministic_evidence_inventory.v1` dictionaries;
- synthetic `readiness_skeleton.v1` dictionaries;
- synthetic `bounded_hypothesis_payload.v1` dictionaries;
- scalar strings, booleans, numbers, and lists needed to model artifact state,
  readiness state, caveats, lineage, blocked hypotheses, and follow-up data;
- `not_for_trading_advice=true`.

Disallowed inputs and behavior:

- no real `accepted_manifest`;
- no real `output/`;
- no report artifact;
- no `artifact_path` read;
- no `artifact_path` existence check;
- no `Path.exists`, `Path.stat`, or equivalent filesystem metadata probe for
  artifact paths;
- no real hash calculation;
- no real artifact content read;
- no PDF, DOCX, HTML, Excel, or other artifact-content parsing;
- no provider payload;
- no live connector payload;
- no token, credential, `.env`, or MCP config read;
- no file write of any kind during dry-run execution;
- no fixture write or promotion;
- no runtime artifact write.

Synthetic `artifact_path` values, if present, must be inert strings only. They
are lineage or artifact-state strings, not filesystem targets.

All test inputs should be copied before invocation and compared after
invocation to prove no caller-owned dictionary or list mutation.

## 4. Output Checks

Phase 5R should inspect only the returned planning payload:

- `autonomous_ticker_research_planning_result.v1`.

Required schema and identity checks:

- `schema_version` equals
  `autonomous_ticker_research_planning_result.v1`;
- `stock_code` matches the synthetic request and every synthetic upstream
  payload;
- `company_name` is present only when exact consistency rules allow it;
- no fuzzy, abbreviation, alias, or fallback identity resolution is accepted.

Required readiness checks:

- `readiness_level` is copied from the synthetic readiness skeleton;
- `can_generate_accepted_report` follows the synthetic readiness skeleton and
  Phase 5 assembly constraints;
- `can_generate_experimental_report` follows the synthetic readiness skeleton
  and Phase 5 assembly constraints;
- accepted readiness does not grant Report V1 generation permission;
- experimental readiness does not grant Report V1 generation permission;
- blocked or conflict readiness forces the relevant report flags false.

Required planning-state checks:

- `data_gap_plan` is a list of structured planning-only dictionaries;
- `blocked_reasons` is a list of structured workflow-state dictionaries;
- `caveats` includes the fixed readiness-flags caveat:
  `readiness flags are planning indicators only; they are not Report V1 generation permissions and do not authorize report content creation.`;
- `lineage_refs` reference synthetic upstream payloads only;
- `not_for_trading_advice` is `true`;
- output is artifact-state / planning-state only.

Required safety and product-boundary checks:

- no report content;
- no report section content;
- no Research Report V1 payload;
- no investment advice;
- no investment conclusion;
- no target price;
- no trading advice;
- no buy/sell recommendation;
- no portfolio or position sizing;
- no technical signal;
- no dashboard payload;
- no template payload;
- no provider payload;
- no raw accepted manifest payload;
- no output scan payload;
- no artifact content;
- no verified fact or accepted report fact promotion.

Suggested forbidden output key scan:

```text
report
report_sections
report_section
research_report
professional_research_report
investment_conclusion
investment_recommendation
investment_advice
recommendation
target_price
trading_advice
buy_sell_decision
buy_recommendation
sell_recommendation
position_size
portfolio_weight
technical_signal
dashboard_payload
template_payload
provider_payload
accepted_manifest
output_scan
artifact_content
verified_facts
accepted_report_facts
report_fact
token
credential
```

The key scan should apply to synthetic request and returned payload dictionaries
only. It must not scan the real repository, real `output/`, accepted manifests,
report artifacts, or artifact paths.

## 5. Expected Files

Future Phase 5R implementation should default to changing only:

```text
tests/test_planning_gate_assembly.py
```

Default file policy:

- Do not modify production code during Phase 5R planning or initial dry-run
  test implementation.
- Add synthetic dry-run coverage to the existing planning gate assembly test
  file because Phase 5R reviews the accepted Phase 5 assembly boundary.
- Keep scenarios focused on Phase 5 assembly behavior, not Phase 2C inventory
  construction, Phase 3 readiness implementation, or Phase 4 hypothesis
  generation internals.
- Do not add runtime fixtures.
- Do not write under `output/`.
- Do not modify accepted manifest, provider, report, artifact-reader,
  fixture-promotion, CLI, orchestrator, Dashboard, or Batch code.

A dedicated dry-run test file may be proposed only if there is a clear review
reason, such as:

- `tests/test_planning_gate_assembly.py` becomes materially hard to review;
- monkeypatch-heavy no-IO guards obscure existing Phase 5 tests;
- the dry-run scenario matrix needs a dedicated naming surface to separate
  synthetic dry-run acceptance from core unit tests.

If a dedicated file is proposed, the future implementation summary must name
the file explicitly, explain why the default file was insufficient, and keep
the change set limited to tests unless a true production bug is discovered.

Production code should not change unless synthetic dry-run tests expose a true
bug in the accepted Phase 5 implementation. If that happens, stop, report the
bug and proposed minimal fix, and wait for confirmation before changing
production code.

## 6. Prohibited Work

Phase 5R planning and future dry-run review must not:

- modify production code unless dry-run tests reveal a true bug and the user
  confirms the fix;
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
- enter Research Report V1 integration;
- generate report content;
- generate report sections;
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
- enter trading-engine work;
- process unrelated mojibake untracked files;
- commit;
- push.

Phase 5R is not:

- a real orchestrator;
- Research Report V1 integration;
- a report generator;
- a live provider connector;
- a real accepted-manifest reader;
- an output scanner;
- a report artifact reader;
- an artifact-content parser;
- a PDF, DOCX, HTML, or Excel parser;
- fixture promotion;
- Dashboard or Batch work;
- a trading engine.

## 7. Acceptance Checklist

Documentation planning acceptance:

- [ ] Only this Phase 5R planning document is added.
- [ ] No production code is written.
- [ ] No tests are written.
- [ ] No runtime artifact is generated.
- [ ] No real accepted manifest is read.
- [ ] No real `output/` scan is performed.
- [ ] No report artifact is read.
- [ ] No PDF, DOCX, HTML, Excel, or artifact-content parsing is performed.
- [ ] No provider, CNInfo, Tushare, AkShare, token, MCP, or network work is
  performed.
- [ ] No Research Report V1, report generator, orchestrator, Dashboard, Batch,
  or trading-engine work is performed.
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

Future Phase 5R dry-run acceptance, only after explicit approval:

- [ ] Only expected tests changed by default:
  `tests/test_planning_gate_assembly.py`.
- [ ] A dedicated dry-run test file is added only with an explicit reason.
- [ ] No production code change unless a true bug is found and confirmed.
- [ ] Any production bug fix is minimal and explicitly justified.
- [ ] No real file IO.
- [ ] No real accepted manifest read.
- [ ] No real `output/` scan.
- [ ] No report artifact read.
- [ ] No artifact path existence check.
- [ ] No real file hash calculation.
- [ ] No PDF, DOCX, HTML, Excel, or artifact-content parsing.
- [ ] No provider or network access.
- [ ] No token, credential, `.env`, or MCP data access.
- [ ] All planned synthetic scenarios are covered.
- [ ] Valid full planning result is covered.
- [ ] Missing Phase 2C inventory is covered.
- [ ] Missing deterministic evidence inventory is covered.
- [ ] Missing readiness skeleton is covered.
- [ ] Missing bounded hypothesis payload is covered.
- [ ] `stock_code` mismatch is covered.
- [ ] `company_name` hint mismatch is covered.
- [ ] `company_name` fuzzy / abbreviation rejection is covered.
- [ ] `source_readiness_level` mismatch is covered.
- [ ] Accepted readiness is covered.
- [ ] Experimental readiness is covered.
- [ ] Blocked readiness is covered.
- [ ] Evidence conflict readiness is covered.
- [ ] `blocked_hypotheses.block_reason` propagates to `blocked_reasons`.
- [ ] `blocked_hypotheses.hypothesis_text` does not propagate.
- [ ] `data_gap_plan` remains neutral data collection planning.
- [ ] Final output contains the required readiness-flags caveat.
- [ ] Final output contains no report section, investment conclusion, target
  price, trading advice, dashboard payload, or template keys.
- [ ] Output remains artifact-state / planning-state only.
- [ ] No input mutation.
- [ ] Targeted tests pass.
- [ ] Regression subset passes.
- [ ] `git status --short` is clean except unrelated mojibake untracked files
  and any explicitly reviewed Phase 5R files.

Suggested future targeted command:

```text
python -m pytest tests/test_planning_gate_assembly.py -p no:cacheprovider
```

Suggested future regression subset:

```text
python -m pytest tests/test_planning_gate_assembly.py tests/test_bounded_hypothesis_generator.py tests/test_evidence_readiness.py tests/test_local_artifact_index.py tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py -p no:cacheprovider
```

Phase 5R should move to dry-run implementation only after this planning
document is accepted and a separate implementation request is made.
