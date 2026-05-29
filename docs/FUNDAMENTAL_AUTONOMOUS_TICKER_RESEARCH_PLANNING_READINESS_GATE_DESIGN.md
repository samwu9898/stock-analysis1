# Fundamental Autonomous Ticker Research Planning & Readiness Gate Design

Date: 2026-05-29

Stage: Autonomous Ticker Research Planning & Readiness Gate Design.

Status: documentation-only design. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not update
fixtures, does not update the accepted manifest, does not change the existing
Research Report V1 baseline, does not enter Research Report V1 L1 Evidence
Integration, does not call live CNInfo, does not call live Tushare, does not
read tokens, does not use the network, does not connect MCP, and does not
provide buy / sell advice, target prices, positions, portfolio weights, or
trading signals. It also does not build Dashboard / Batch flows and does not
add PDF, DOCX, HTML, or Excel parsing.

## 1. Module Positioning

The autonomous ticker research planning gate is a pre-Research Report V1
planning and readiness layer.

Its purpose is to answer this question:

> Given one user-supplied A-share ticker or company name, do current local
> artifacts contain enough traceable evidence to plan the research, identify
> company / industry / macro hypotheses, and decide whether a formal accepted
> report, an experimental report, or a fail-closed result is allowed?

It is not:

- the final report generator;
- Research Report V1 L1 Evidence Integration;
- a validator implementation;
- a live provider connector;
- a CNInfo downloader;
- a Tushare primary switch;
- a fixture promotion path;
- an accepted manifest writer;
- a manually maintained all-industry template library;
- a trading advice engine.

The gate may produce structured hypotheses and data plans, but those outputs
remain planning artifacts. They must not be written directly into Research
Report V1 sections until a later L1 Evidence Integration Design defines how
verified, reviewed, and caveated evidence can enter the report.

## 2. Design Principles

1. The user-facing target remains one-ticker autonomous research: the user
   inputs a stock code or company name, and the system resolves identity,
   searches local evidence, understands business exposure, infers supply-chain
   position, derives industry and macro research variables, plans required
   data, assesses current evidence, and chooses accepted / experimental /
   fail-closed readiness.
2. The system must not rely on developers manually maintaining a complete
   industry template library or manually entering conditions for every
   industry.
3. AI may generate industry, supply-chain, and macro hypotheses from local
   evidence, but every hypothesis must carry evidence references, confidence,
   caveats, required follow-up data, and allowed downstream use.
4. AI hypotheses are never verified facts.
5. Official disclosure candidates are still candidates unless a later reviewed
   evidence integration layer upgrades their use. The planning gate can cite
   them as evidence refs and caveats, but cannot write them into reports as
   final facts.
6. The gate is offline-only in V1. If a necessary data source requires live
   CNInfo, live Tushare, network, MCP, or token access, the gate must fail
   closed or return `data_collection_required`.
7. The gate must preserve the existing deterministic pipeline instead of
   building a parallel research system.
8. The output must always include `not_for_trading_advice=true`.

## 3. Inputs

### 3.1 User Query

The direct user input may be:

- `ticker`: A-share code such as `300475`;
- `company_name`: Chinese or English company name;
- optional user-provided local artifact hints, if future UI / CLI supports
  them.

The gate must treat the user input as an identity hint, not as resolved truth.

### 3.2 Local Artifact Index

The gate should read a local artifact index or build an in-memory index from
approved local paths. The index should only describe existing local artifacts
and should not fetch or create data.

Recommended index fields:

```json
{
  "artifact_id": "",
  "artifact_type": "",
  "artifact_path": "",
  "stock_code": "",
  "company_name": "",
  "source_family": "",
  "schema_version": "",
  "created_at": "",
  "data_period": "",
  "sha256": "",
  "not_for_trading_advice": true
}
```

Artifact families can include:

- normalized fundamentals;
- provider-separated fundamentals;
- evidence packs;
- provider candidate facts;
- official disclosure facts;
- official disclosure candidates;
- candidate source bridges;
- bridge-aware review decisions;
- score / confidence explainability;
- accepted Research Report V1 artifacts;
- accepted manifest entries.

### 3.3 Accepted Manifest

Read-only input:

```text
output/research_reports/accepted_manifest.json
```

The manifest can answer whether a Research Report V1 artifact has previously
been accepted and whether its freshness status is current, unknown, stale,
superseded, or invalidated.

The planning gate must not update the manifest. Manifest presence does not
verify new facts. It only supports accepted artifact location, freshness
awareness, and lineage.

### 3.4 Existing Provider Candidates

Existing provider candidate artifacts such as `fact_candidates.json` can
provide local provider evidence candidates, source traces, auto-acceptance
state, manual review queues, blocked rows, caveats, and provider gaps.

Provider candidates are not automatically verified facts. They can support
planning and data-gap analysis only under their recorded confidence and caveat
status.

### 3.5 Official Disclosure Candidates

Existing official disclosure candidates can provide L1 official disclosure
source traces, business description candidates, main business candidates,
business-composition table candidates, periods, units, denominators, extraction
confidence, and caveats.

Official disclosure candidates must not be written directly into Research
Report V1. They can be cited by the gate as `evidence_refs` for hypotheses or
evidence inventory, with explicit candidate caveats.

### 3.6 Bridge And Review Decision Artifacts

The gate should read bridge and review artifacts when present:

- `candidate_source_bridge.v1`;
- `candidate_review_decisions_bridge.v1`;
- older provider candidate review decisions, if present.

Bridge artifacts are source indexes, not merges. Review decisions are review
workflow signals, not verified facts. `accepted_for_report_candidate` remains
a candidate status and still requires a future report evidence integration
design before report use.

### 3.7 Future Provider Metadata Interface

The design reserves an input interface for future provider metadata without
connecting live providers in this stage:

```json
{
  "provider_metadata": [
    {
      "provider_name": "",
      "artifact_path": "",
      "schema_version": "",
      "data_cutoff": "",
      "source_reliability": "",
      "coverage_notes": [],
      "known_limitations": [],
      "requires_live_access": false,
      "not_for_trading_advice": true
    }
  ]
}
```

If `requires_live_access=true` and no local artifact can satisfy the need, the
gate must not connect to the provider. It should return
`data_collection_required` or `blocked` with a fail-closed reason.

## 4. Output Schema

Recommended schema version:

```text
autonomous_ticker_research_planning_gate.v1
```

Top-level payload:

```json
{
  "schema_version": "autonomous_ticker_research_planning_gate.v1",
  "generated_at": "",
  "stock_code": "",
  "company_name": "",
  "identity_resolution_status": "",
  "market": "",
  "exchange": "",
  "evidence_inventory": [],
  "business_description_evidence": [],
  "industry_hypotheses": [],
  "supply_chain_position_hypotheses": [],
  "macro_factor_hypotheses": [],
  "key_research_questions": [],
  "required_data_plan": [],
  "available_data_artifacts": [],
  "missing_data_artifacts": [],
  "evidence_confidence": "",
  "hypothesis_confidence": "",
  "report_readiness_level": "",
  "can_generate_accepted_report": false,
  "can_generate_experimental_report": false,
  "fail_closed_reason": "",
  "caveats": [],
  "not_for_trading_advice": true
}
```

### 4.1 Identity Fields

`identity_resolution_status` enum:

- `resolved`;
- `ambiguous`;
- `not_found`;
- `conflict_requires_review`;
- `blocked`.

`market` should identify the market family, for example `A-share`.

`exchange` should be derived from stock code and available metadata, for
example `SSE`, `SZSE`, or `BSE`. Code-derived exchange is a routing inference
and should be caveated when company identity evidence is missing.

### 4.2 Evidence Inventory

Each evidence inventory row should record local source availability:

```json
{
  "evidence_id": "",
  "artifact_type": "",
  "artifact_path": "",
  "source_family": "",
  "schema_version": "",
  "field_paths": [],
  "period": "",
  "source_status": "",
  "review_status": "",
  "confidence": "",
  "caveats": [],
  "sha256": ""
}
```

`source_status` examples:

- `available`;
- `missing`;
- `partial`;
- `candidate_only`;
- `review_required`;
- `conflict_open`;
- `stale`;
- `invalidated`.

### 4.3 Business Description Evidence

Business description evidence should contain only traceable local evidence:

```json
{
  "evidence_id": "",
  "field_path": "basic_info.main_business",
  "text_preview": "",
  "source_family": "",
  "artifact_path": "",
  "period": "",
  "confidence": "",
  "candidate_status": "",
  "caveats": []
}
```

This section may include official disclosure candidates, provider candidates,
and normalized basic info, but must preserve candidate status and caveats.

### 4.4 Required Data Plan

Required data rows should be actionable but offline-safe:

```json
{
  "data_item": "",
  "reason": "",
  "priority": "critical",
  "expected_artifact_family": "",
  "acceptable_source_types": [],
  "current_status": "",
  "blocks_accepted_report": true,
  "blocks_experimental_report": false,
  "offline_boundary_note": ""
}
```

If a data item requires live access under current conditions, the row should
say so and the top-level readiness should fail closed or require data
collection.

## 5. Hypothesis Mechanism

The gate should use a bounded AI hypothesis generator. It can reason across
local evidence, but it must not invent facts or silently promote weak signals.

### 5.1 Hypothesis Inputs

The generator can use:

- official disclosure source traces and candidates;
- main business descriptions;
- business-composition rows;
- revenue structure and gross margin by segment when locally available;
- existing provider candidate facts and review states;
- industry fields from normalized basic info;
- product and service keywords;
- customer / supplier text evidence when locally available;
- financial features such as revenue growth, gross margin, inventory,
  accounts receivable, operating cash flow, contract liabilities, capex, and
  R&D spending when locally available;
- candidate source bridge and bridge-aware review decision caveats;
- accepted manifest freshness and lineage as artifact-state evidence, not
  operating fact evidence.

### 5.2 Hypothesis Output Shape

Every hypothesis must use this minimum shape:

```json
{
  "hypothesis_id": "",
  "hypothesis_type": "supply_chain_position",
  "hypothesis_text": "",
  "evidence_refs": [],
  "confidence": "",
  "caveats": [],
  "required_follow_up_data": [],
  "allowed_downstream_use": ""
}
```

`hypothesis_type` enum:

- `industry`;
- `supply_chain_position`;
- `industry_driver`;
- `macro_factor`;
- `business_model`;
- `data_gap`;
- `conflict`.

`confidence` enum:

- `high`;
- `medium`;
- `low`;
- `not_assessable`.

`allowed_downstream_use` enum:

- `planning_only`;
- `data_collection_prioritization`;
- `experimental_report_context_candidate`;
- `blocked_until_review`;
- `not_allowed_downstream`.

No hypothesis can use `accepted_report_fact` as an allowed downstream use in
this gate. A later L1 Evidence Integration Design is required before any
source can enter Research Report V1 as report evidence.

### 5.3 Evidence Reference Rules

Each hypothesis should include at least one `evidence_ref`.

An evidence ref should identify:

```json
{
  "evidence_id": "",
  "artifact_path": "",
  "field_path": "",
  "candidate_id": "",
  "source_type": "",
  "review_status": "",
  "period": "",
  "caveats": []
}
```

If no evidence ref exists, the generator may only emit a blocked data-gap
hypothesis:

```json
{
  "hypothesis_text": "No evidence-backed business or industry hypothesis can be formed from current local artifacts.",
  "evidence_refs": [],
  "confidence": "not_assessable",
  "allowed_downstream_use": "blocked_until_review"
}
```

### 5.4 Supply-Chain Position Hypotheses

Supply-chain position hypotheses should be inferred from the company's own
business evidence, not from a hardcoded all-industry profile.

Possible evidence signals:

- segment names and segment revenue shares;
- verbs and nouns in main business descriptions, such as manufacture,
  distribution, agency, solution, service, operation, design, integration,
  equipment, components, software, resources, capacity, or platform;
- customer / supplier concentration evidence;
- inventory, receivables, gross margin, and operating cash flow patterns;
- product keywords and source-industry terms;
- bridge conflicts or review decisions that constrain confidence.

Example output pattern:

```json
{
  "hypothesis_type": "supply_chain_position",
  "hypothesis_text": "Current local evidence suggests the company may sit in an electronic-components distribution / semiconductor supply-chain service position rather than a semiconductor-equipment manufacturing position.",
  "evidence_refs": ["business_description_evidence:main_business:001"],
  "confidence": "low",
  "caveats": [
    "candidate_only",
    "requires official segment revenue and business model review"
  ],
  "required_follow_up_data": [
    "official business-composition table",
    "major customer / supplier concentration",
    "inventory and receivables trend",
    "gross-margin trend by business segment"
  ],
  "allowed_downstream_use": "data_collection_prioritization"
}
```

### 5.5 Industry Driver Hypotheses

Industry driver hypotheses should map evidence-backed business exposure to
candidate driver variables.

Allowed inference pattern:

1. Identify product / service exposure from local evidence.
2. Infer likely economic activity that affects that exposure.
3. Translate it into trackable industry variables.
4. Mark confidence and required follow-up data.

For example, a business model involving electronic component distribution may
lead to candidate industry variables such as demand from downstream computing,
storage, consumer electronics, automotive electronics, inventory cycle,
supplier allocation, price spread, customer concentration, and working-capital
turnover. These are hypotheses until confirmed by evidence.

The gate must not say that these drivers are verified unless a later reviewed
evidence layer supports that claim.

### 5.6 Macro Factor Hypotheses

Macro factor hypotheses should be derived from company and industry exposure.

Allowed inference pattern:

1. Start from company evidence: products, customers, revenue model, assets,
   working capital, financing needs, and geographic exposure.
2. Infer industry transmission variables: demand cycle, capex cycle, tender
   rhythm, commodity prices, inventory cycle, capacity utilization, technology
   migration, policy exposure, exchange-rate exposure.
3. Map industry variables to macro variables: interest rates, liquidity,
   credit, fiscal rhythm, industrial policy, trade restrictions, exchange
   rates, commodity prices, downstream capex, and inventory cycle.
4. Keep the result as mechanism and tracking variables, not macro forecasts.

Macro hypotheses must not forecast market price, target price, trading timing,
or account action.

## 6. Macro / Industry / Company Three-Layer Framework

The gate should reason bottom-up from target-specific evidence.

### 6.1 Company Layer

Company layer nodes are evidence-backed observations from local artifacts:

- identity;
- main business;
- segment revenue;
- revenue structure;
- gross margin;
- inventory;
- receivables;
- operating cash flow;
- capex;
- R&D;
- customers / suppliers;
- official disclosure candidates;
- provider candidate facts and caveats;
- bridge conflicts and review decisions.

The company layer is the only layer allowed to introduce target-specific facts.

### 6.2 Industry Layer

Industry layer variables are generated from company layer evidence:

- "What activity does this company monetize?"
- "Where does it sit in the value chain?"
- "Which downstream demand or upstream supply variables plausibly affect it?"
- "Which operating indicators would verify or falsify the exposure?"

This layer may use a lightweight generic taxonomy of driver categories, such
as demand, price, volume, cost, inventory, capacity, customer concentration,
supplier concentration, policy, technology migration, and working capital.

It must not require a manually maintained full industry template library.
Existing deterministic frameworks can still provide guardrails when classifier
confidence is high, but AI hypotheses can propose adjacent or alternative
research directions if the evidence suggests the deterministic label is
incomplete or uncertain.

### 6.3 Macro Layer

Macro layer variables are derived from industry variables:

- demand cycle -> GDP / industrial production / downstream capex / consumer
  demand;
- financing sensitivity -> interest rates / credit / liquidity;
- working capital pressure -> credit conditions / payment cycle / inventory
  cycle;
- import / export exposure -> exchange rates / trade restrictions / global
  demand;
- commodity input exposure -> commodity prices and supply constraints;
- public infrastructure exposure -> fiscal rhythm / policy implementation.

The macro layer should output mechanisms and monitoring variables only. It
must not output market forecasts, target prices, or trading calls.

## 7. Readiness Levels

Recommended planning-gate readiness enum:

| Readiness level | Meaning | Accepted report | Experimental report |
| --- | --- | --- | --- |
| `accepted_report_ready` | Identity is resolved, required local evidence exists, official disclosure evidence is present or accepted local report artifact is current, key conflicts are closed, critical financial / business data is available, and no safety gate is triggered. | Allowed by planning gate, still subject to existing Research Report V1 orchestration and future L1 Evidence Integration boundary. | Allowed. |
| `experimental_report_ready` | Identity is resolved and enough evidence exists for a caveated exploratory report, but official evidence, freshness, review status, or data depth is insufficient for accepted-report readiness. | Not allowed. | Allowed with visible caveats and `not_for_trading_advice=true`. |
| `data_collection_required` | Identity is likely resolved, but required local artifacts or critical data are missing. | Not allowed. | Not allowed unless future policy explicitly permits a data-gap-only experimental artifact. |
| `classification_review_required` | Deterministic classification, AI hypotheses, and evidence signals disagree or confidence is too low to choose a research frame. | Not allowed. | Usually blocked; may allow planning-only output. |
| `evidence_conflict_review_required` | Provider, official, bridge, or review-decision sources conflict on material identity, business, segment, period, unit, denominator, or financial fields. | Not allowed. | Usually blocked; planning output can list conflicts. |
| `blocked` | Identity, safety, data, source, or offline-boundary conditions prevent report generation. | Not allowed. | Not allowed. |

### 7.1 Accepted Report Readiness

`can_generate_accepted_report=true` only when all are true:

- identity is `resolved`;
- local evidence inventory contains required business and financial evidence;
- official disclosure evidence or an already accepted local report artifact is
  available and not invalidated;
- material source conflicts are absent or already reviewed;
- critical financial fields are available;
- existing deterministic readiness is compatible with at least
  `usable_with_warnings`;
- no trading-advice safety risk is triggered;
- no live provider access is required under the current offline boundary.

This boolean means "the planning gate does not block accepted-report
generation or reuse." It does not itself generate a report and does not
authorize writing AI hypotheses into Research Report V1.

### 7.2 Experimental Report Readiness

`can_generate_experimental_report=true` only when:

- identity is resolved;
- at least some local evidence exists;
- hypotheses have evidence refs and visible caveats;
- missing data does not include identity or all official/business evidence;
- output can remain clearly experimental and not-for-trading-advice.

Experimental readiness is not a downgrade path for unsafe accepted reports. If
the gate hits an identity, conflict, source, or safety blocker, it must stay
blocked.

## 8. Fail-Closed Rules

The gate must refuse accepted-report generation when any of the following are
true:

1. Identity cannot be resolved.
2. Ticker and company name conflict.
3. Market / exchange cannot be inferred or conflicts with local artifacts.
4. No official disclosure evidence or accepted local report artifact is
   available for formal-report readiness.
5. Only AI hypotheses exist and no local evidence supports them.
6. The supply-chain or industry classification has material unresolved
   conflicts.
7. Key financial data is missing for the selected research frame, especially
   revenue, net profit, gross margin, operating cash flow, receivables,
   inventory, valuation date, or segment revenue when the frame depends on
   them.
8. Provider and official sources conflict on material field, period, unit,
   denominator, or source lineage and no review decision closes the conflict.
9. Official disclosure candidate caveats block report use.
10. Accepted manifest entry is invalidated or hash verification fails in a
    future implementation.
11. Required data would need live CNInfo, live Tushare, network, token access,
    MCP, or any other disabled boundary.
12. Output would create buy / sell advice, target price, position sizing,
    portfolio weight, technical trading signal, or account action guidance.
13. Secret-like material, token strings, `.env` references, local credential
    paths, or remote-control URLs are detected in candidate payloads.
14. A hypothesis attempts to present itself as a verified fact.

Fail-closed output should preserve useful planning information when safe:

```json
{
  "report_readiness_level": "blocked",
  "can_generate_accepted_report": false,
  "can_generate_experimental_report": false,
  "fail_closed_reason": "identity_unresolved",
  "key_research_questions": [],
  "required_data_plan": [],
  "not_for_trading_advice": true
}
```

## 9. Relationship To Existing Pipeline

The planning gate should reuse the existing pipeline and evidence engineering
chain. It should not fork a separate research stack.

### 9.1 `data_adapter`

Use `FundamentalDataAdapter` to normalize existing local raw / provider
fundamental artifacts into `NormalizedFundamentalInput`.

The gate should not add provider fetching to the adapter. Missing normalized
inputs should become evidence gaps, not live provider calls.

### 9.2 `classifier`

Use `StockClassifier` for the deterministic baseline classification.

AI-generated industry hypotheses can supplement or challenge the deterministic
classification, but cannot silently override it. If deterministic
classification and AI hypotheses disagree materially, the gate should return
`classification_review_required` unless evidence supports a clear conservative
choice.

### 9.3 `framework_selector`

Use `FrameworkSelector` to obtain current framework guardrails when the
deterministic classification is usable.

The gate should not expand `industry_frameworks.yaml` into a full manual
template library. New hypothesis-driven research directions should be
represented as hypotheses and required data plan rows, not as immediate
framework config changes.

### 9.4 `readiness_planner`

Use `DataReadinessPlanner` for deterministic field readiness under the selected
baseline framework.

The planning gate should wrap this with source-readiness checks:

- official evidence presence;
- candidate-only vs reviewed status;
- bridge conflict status;
- accepted manifest freshness;
- artifact availability;
- offline-boundary availability.

### 9.5 `analysis_context`

Use `AnalysisContextBuilder` concepts for safe downstream permissions,
prohibited claims, confidence caps, blocked dimensions, and required risks.

The gate should map blocked or restricted context dimensions into caveats,
required data rows, and fail-closed reasons.

### 9.6 `scoring_engine`

Use `FundamentalScoringEngine` only as a deterministic data-quality and
confidence signal when normalized inputs, classification, framework, readiness,
and context are available.

Scoring output is not a trading signal and should not decide accepted-report
readiness by itself.

### 9.7 `result_assembler`

`FundamentalResultAssembler` remains the existing deterministic fundamental
result assembler. The planning gate should not use it to create a new Research
Report V1 artifact.

If an existing local assembled result or accepted report artifact is present,
its status, missing fields, and data sources can be read as artifact-state
evidence. The gate must not rewrite it or treat it as proof that new
hypotheses are verified.

### 9.8 Research Report V1 Accepted Manifest

Use the accepted manifest read-only to locate accepted Research Report V1
artifacts and freshness status.

The gate must not:

- update the manifest;
- add 300475 to the manifest;
- change accepted paths;
- change hashes;
- treat manifest freshness as operating evidence.

### 9.9 Candidate Source Bridge

Use `candidate_source_bridge.v1` as a source index that tells the gate which
provider and official candidate artifacts exist and where review priorities
are.

The bridge is not a data merge and not a verified fact store.

### 9.10 Bridge-Aware Review Decisions

Use `candidate_review_decisions_bridge.v1` as review workflow input:

- `manual_review_required` limits readiness;
- `blocked_by_caveat` can fail closed for material fields;
- `needs_more_evidence` creates data-plan rows;
- `conflict_requires_review` creates conflict-review readiness;
- `accepted_for_report_candidate` remains a candidate and still requires
  future L1 Evidence Integration before report use.

## 10. Relationship To Research Report V1

This stage outputs only a research planning / readiness result.

It must not write its hypotheses, business description evidence, macro
mechanisms, industry drivers, or data plans directly into Research Report V1.

Future integration path:

1. This gate produces `autonomous_ticker_research_planning_gate.v1`.
2. A future L1 Evidence Integration Design defines which evidence classes may
   enter Research Report V1, how candidate-only official evidence is labeled,
   how conflicts are displayed, and how hypotheses are separated from facts.
3. Research Report V1 consumes only the evidence-integration-approved payload,
   not raw AI hypotheses.

Until step 2 exists, the gate may support planning and runtime review only.

## 11. 300475 Sample Plan

`300475` / 香农芯创 should be used later as an autonomous runtime review sample.
The goal is not to force it into the existing `002371` 北方华创 semiconductor
equipment profile.

### 11.1 Review Objectives

The runtime review should verify that the gate can:

- resolve `300475` identity from local artifacts;
- find local provider / official / bridge evidence when present;
- avoid hard-applying the `002371` semiconductor-equipment-cycle profile;
- inspect business description and segment evidence before choosing a
  research frame;
- propose hypotheses that fit the evidence instead of a manually coded
  industry template.

### 11.2 Candidate Research Directions

If supported by local evidence, the gate may generate hypotheses around:

- electronic components distribution;
- storage / chip supply-chain position;
- AI computing demand transmission;
- inventory cycle;
- customer and supplier concentration;
- gross margin volatility;
- accounts receivable and cash-flow quality;
- agency / distribution business model quality;
- downstream demand and product-price cycle;
- working-capital funding pressure.

These are hypotheses only. They must not be written as verified facts unless a
future reviewed evidence layer supports them.

### 11.3 Required Boundaries

For `300475`, the gate must:

- not infer semiconductor equipment exposure merely because the code appears
  near semiconductor examples;
- not reuse `002371` required indicators unless the business evidence supports
  equipment manufacturing;
- not treat "chip", "storage", or "AI" keywords as proof of business
  realization;
- not conclude AI computing demand benefit without revenue, customer,
  product, inventory, order, or margin evidence;
- not turn a distributor / agent business-model hypothesis into a confirmed
  business model without official disclosure evidence;
- not generate accepted-report readiness if identity, official evidence,
  critical financials, or conflict review is missing.

### 11.4 Expected Runtime Review Assertions

Future runtime review should check:

- `stock_code=300475`;
- `identity_resolution_status=resolved` only when local artifacts support it;
- if local evidence is insufficient, readiness is `data_collection_required`
  or `blocked`;
- industry hypotheses include evidence refs and caveats;
- supply-chain hypotheses do not claim verified fact status;
- `allowed_downstream_use` is no stronger than
  `data_collection_prioritization` or
  `experimental_report_context_candidate`;
- `can_generate_accepted_report=false` unless all formal readiness conditions
  are met;
- `not_for_trading_advice=true`;
- no buy / sell / target price / position / portfolio-weight keys appear.

## 12. Future Implementation Plan

This section is a recommendation only. No production code or tests are created
in the current stage.

### 12.1 Suggested Production Module Paths

Recommended module layout:

```text
src/fundamental_skill/research_planning/__init__.py
src/fundamental_skill/research_planning/autonomous_ticker_research_gate.py
src/fundamental_skill/research_planning/autonomous_ticker_research_schema.py
src/fundamental_skill/research_planning/local_artifact_index.py
src/fundamental_skill/research_planning/hypothesis_generator.py
```

Design intent:

- schema module defines the planning output and hypothesis shapes;
- local artifact index reads only local paths and accepted manifest state;
- gate orchestrator reuses existing deterministic modules;
- hypothesis generator produces bounded evidence-backed hypotheses;
- no live provider access is introduced.

### 12.2 Suggested Test Paths

Recommended future tests:

```text
tests/test_autonomous_ticker_research_schema.py
tests/test_autonomous_ticker_research_planning_gate.py
tests/test_autonomous_ticker_research_hypotheses.py
tests/test_autonomous_ticker_research_readiness_levels.py
tests/test_autonomous_ticker_research_300475_review.py
```

Test boundaries:

- no network;
- no token reads;
- no MCP;
- no accepted manifest writes;
- no fixture promotion unless a separate fixture design is accepted;
- no Research Report V1 artifact generation.

### 12.3 Suggested Fixture And Runtime Output Paths

Future runtime output path:

```text
output/autonomous_ticker_research_plans/<timestamp>/<code>/autonomous_ticker_research_planning_gate.json
```

Future sanitized fixtures, only after a separate fixture decision:

```text
tests/fixtures/autonomous_ticker_research/300475_minimal_offline.json
tests/fixtures/autonomous_ticker_research/300475_with_official_candidates.json
tests/fixtures/autonomous_ticker_research/300475_conflict_review_required.json
```

Current stage creates none of these files.

### 12.4 Acceptance Checklist

Future implementation should be accepted only if:

- output schema validates;
- identity resolution is conservative;
- evidence inventory preserves artifact paths, source families, review status,
  and caveats;
- every hypothesis has `hypothesis_text`, `evidence_refs`, `confidence`,
  `caveats`, `required_follow_up_data`, and `allowed_downstream_use`;
- hypotheses cannot appear as verified facts;
- official disclosure candidates remain candidates;
- bridge artifacts remain source indexes;
- review decisions remain workflow signals;
- `can_generate_accepted_report` is false when official evidence, identity,
  critical financials, or conflict review is missing;
- offline boundaries fail closed when live access would be required;
- no Research Report V1 artifact is generated;
- accepted manifest is read-only;
- no fixture, output, or existing baseline is modified by tests unless a later
  design explicitly allows it;
- no trading advice keys or phrases are emitted.

### 12.5 Runtime Review Checklist

Future runtime review, especially for `300475`, should record:

- input query and resolved identity;
- local artifacts discovered;
- accepted manifest state;
- provider candidate availability;
- official candidate availability;
- bridge and bridge-aware review decision availability;
- deterministic classification result and confidence;
- AI hypothesis list with evidence refs and caveats;
- required data plan;
- available vs missing artifacts;
- readiness level;
- fail-closed reason, if any;
- safety scan result;
- confirmation that no live CNInfo, live Tushare, token, network, MCP, output
  mutation, fixture mutation, manifest mutation, or Research Report V1
  integration occurred.

## 13. Summary

The autonomous ticker research planning gate fills the gap between "user enters
one ticker" and "Research Report V1 can be safely generated or reused."

It lets AI help form company, supply-chain, industry, and macro research
hypotheses from local evidence, while keeping a hard boundary between
hypothesis and verified fact. It reuses the existing deterministic pipeline and
accepted evidence-engineering artifacts, adds a readiness decision layer, and
fails closed whenever identity, evidence, conflict, financial data, source
boundary, or trading-advice safety conditions are not satisfied.
