# Research Intelligence P1.1 Selected Validation Hardening Plan

Date: 2026-05-25

Stage: documentation freeze for the Selected Validation Hardening Plan.

Status: documentation-only. This file records the unified audit scope for the upcoming Batch 1-4 validation runs. It must not change code, tests, config, pipeline behavior, classifier rules, connectors, scoring, readiness, HTML / Dashboard behavior, generated output, or regression expectations.

## 1. Frozen Baseline Summary

The current P1.1 baseline is frozen as an independent AI analyst-layer Research Intelligence artifact. It reads `output/evidence_pack_<code>.json` plus optional P0 artifacts and writes only independent runtime artifacts:

- `output/research_intelligence_p1_<code>.json`
- `output/research_questions_p1_<code>.json`
- `output/research_questions_p1_<code>.md`

P1.1 must not mutate deterministic `status`, `confidence`, `score`, `strategy_type`, `sub_type`, classifier routing, connector output, readiness, scoring, HTML Report, Dashboard, or regression expectations.

The accepted P1.1 support scope is limited to these 8 expansions:

1. `ai_datacenter_infrastructure`
2. `life_science_cxo_services`
3. `satellite_communication_infrastructure`
4. `low_altitude_economy_infrastructure`
5. `resource_swing`
6. `semiconductor_cycle`
7. `advanced_manufacturing_growth`
8. `stable_growth`

Universal hardening guardrails:

- `company_transmission_path` must cite concrete evidence-pack field/value nodes.
- If no concrete path can be verified, it must be exactly `传导路径无法从当前证据包验证` and the row must use `confidence_cap=not_assessable`.
- Source independence is counted by source bucket, not by file, article, API endpoint, or repeated mentions.
- `not_assessable` and `missing` are expected outcomes when current evidence does not support a driver.
- Contract liabilities are not backlog.
- Capex is not capacity release, utilization, delivery, or revenue conversion.
- R&D ratio is not a technology moat.
- Policy, news, theme heat, customer capex, strategic layout wording, and industry demand are not company realization without company-level evidence.
- Valuation metrics are evidence-sufficiency context only, never target price, upside / downside, or trading judgment.
- P1.1 must not output trading advice, position sizing, execution instructions, technical analysis, K-line content, or account actions.

## 2. Accepted Expansion Scope

| Expansion | First-version positive sample | Validation / boundary sample | Deferred / unsupported scope |
| --- | --- | --- | --- |
| AI Datacenter | `002837`, `300442` | `002335`, `002518`, `301018` | AI server supply-chain exposure, optical modules, PCB, storage / PV-only exposure, ordinary HVAC, and generic power equipment remain unsupported unless datacenter-specific revenue, orders, customers, assets, or operation evidence exists. `300308` and `300476` remain outside AI Datacenter P1.1 support. |
| CXO | `603259` | `300759`, `002821`, `300347`, `300363` | Self-owned drug pipelines, ordinary API / formulation manufacturing, medical devices, distribution, TCM, consumer healthcare, software-only AI drug discovery, general testing labs, and news-only CXO wording remain unsupported. |
| Satellite | `601698` | `600118`, `002465`, `688066`, `002895`, `999997` news-only satellite sample | Satellite manufacturing, terminals, remote sensing, data software, military electronics, rockets, drones, and generic communication equipment remain unsupported. |
| Low Altitude | `000099` | `688631`, `688070`, `002085`, `001696`, `600967`, `002895` | Drone OEMs, eVTOL OEMs, engines, components, auto parts, airports, aviation leasing, remote sensing, defense, policy-only, announcement-only, and theme-only names remain unsupported. |
| Resource Swing | `000426` | `601899`, `603993` | `resource_core` remains design-only. Resource steadiness, dividend capacity, mine life, cost-curve position, hedging, production, sales volume, and sustaining capex remain unsupported unless direct evidence exists. |
| Semiconductor | `002371` | `688012`, `688981`, `603501`, `300604`, `300308`, `300476` | Materials, fabless, foundry, and OSAT are not fully implemented. Validation samples must not inherit the `002371` equipment first-version order logic without a new accepted cycle. |
| Advanced Manufacturing | `002050` | `601689` | `601689` and other advanced-manufacturing candidates remain future validation / boundary only. Robotics, humanoid robotics, actuator, customer concentration, and large-customer narratives require independent revenue, order, customer, mass-production, delivery, and collection evidence. |
| Stable Growth | `600406` | `002028`; excluded: `600276` | `600276` remains excluded because refreshed classifier output is `unknown / insufficient_data`. `right_trend_growth`, pharmaceutical / biotech pipeline-risk cases, and generic stability labels remain unsupported for the accepted first version. |

## 3. Expansion-Level Validation Targets

AI Datacenter validation should confirm that `002837` and `300442` still produce the accepted P1.1 datacenter-infrastructure behavior, while mixed UPS / storage / PV and ordinary HVAC boundaries remain conservative. Supply-chain names must not be pulled into AI Datacenter P1.1 because of AI theme exposure alone.

CXO validation should confirm that `603259` remains the positive first-version path, while future validation samples only stress sub-type coverage and evidence gaps. Backlog, new orders, overseas regulatory risk, CDMO utilization, clinical project stage, and customer concentration must remain `missing` or `not_assessable` unless directly evidenced.

Satellite validation should confirm that `601698` remains the only first-version positive satellite-communication infrastructure sample. Manufacturing, terminal, remote sensing, military electronics, and news-only satellite exposure should stay boundary / unsupported.

Low Altitude validation should confirm that `000099` remains the first-version positive aviation-operations sample. Flight hours, sorties, platform dispatch volume, airspace / route approvals, project acceptance, government payment cycle, and safety events should remain `missing` or `not_assessable` unless evidence-pack fields support them.

Resource validation should confirm that `000426` remains the only first-version `resource_swing` positive sample. Commodity price must not become company revenue, reserves must not become production, production must not become sales, inventory movement must not become demand judgment, and `resource_core` must stay out of first-version support.

Semiconductor validation should confirm that `002371` remains the only first-version `semiconductor_cycle` positive sample and equipment sub-chain path. Validation samples are observation / boundary samples and must not be force-fit into the `002371` order, localization, inventory, customer-qualification, or capex logic.

Advanced Manufacturing validation should confirm that `002050` remains the only first-version positive path and that the three business layers stay separated: refrigeration / air-conditioning, automotive thermal management, and robotics / emerging business. `601689` must stay `unsupported_pilot_strategy` / `not_assessable` until a later accepted expansion.

Stable Growth validation should confirm that `600406` remains the only first-version positive path. `002028` is validation / boundary only, and high `missing / not_assessable` share is expected. The `stable_growth` label, rigid-demand wording, SOE / central-SOE attributes, or one-period revenue / OCF movement must not become stability conclusions.

## 4. Batch 1-4 Validation Matrix

| Batch | Sample group | Primary samples | Boundary / validation samples | Objective |
| --- | --- | --- | --- | --- |
| Batch 1 | Accepted first-version positives | `002837`, `300442`, `603259`, `601698`, `000099`, `000426`, `002371`, `002050`, `600406` | None unless a rerun needs a paired sanity sample | Confirm every accepted positive path still generates P1.1 artifacts within the frozen scope and does not regress into generic unsupported behavior. |
| Batch 2 | Same-strategy validation / boundary samples | None | `002335`, `002518`, `301018`, `300759`, `002821`, `300347`, `300363`, `688631`, `688012`, `688981`, `603501`, `300604`, `601689`, `002028` | Confirm validation samples are observed without widening first-version support or force-fitting primary-sample logic. |
| Batch 3 | Negative, excluded, adjacent, or unsupported strategy samples | None | `600118`, `002465`, `688066`, `002895`, `688070`, `002085`, `001696`, `600967`, `601899`, `603993`, `300308`, `300476`, `600276`, `999997`, `999998`, `999999` | Confirm unsupported, excluded, adjacent, theme-only, and insufficient-data cases remain conservative and do not generate unsupported business-realization conclusions. |
| Batch 4 | Caveat, wording, and audit-consistency replay | Previously flagged samples from Batch 1-3 | `688631`, `601689`, semiconductor validation samples with `latest_news` caveats, generic unsupported outputs | Reconcile data caveats, sample-identity differences, and wording weaknesses separately from true matrix logic failures. |

Recommended next run: enter Batch 1 validation run first.

## 5. Per-Batch Validation Goals

Batch 1 goals:

- Verify each accepted positive sample can still create P1.1 JSON and question artifacts.
- Confirm positive support remains limited to the accepted first-version scope.
- Confirm expected `missing` / `not_assessable` rows are preserved rather than filled with narrative conclusions.
- Confirm no deterministic pipeline field changes.

Batch 2 goals:

- Verify boundary / validation samples do not expand first-version support.
- Confirm unsupported samples return `unsupported_pilot_strategy`, `not_assessable`, fallback `company_transmission_path`, or conservative boundary behavior where expected.
- Confirm same-strategy validation samples are not force-fit into primary-sample-specific logic.
- Confirm source-bucket independence and safety boundary are preserved.

Batch 3 goals:

- Verify negative, excluded, adjacent, theme-only, and insufficient-data samples remain unsupported or conservative.
- Confirm no scope creep into `resource_core`, `right_trend_growth`, unknown, theme-only, supply-chain-only, news-only, policy-only, or unsupported adjacent frameworks.
- Confirm generic unsupported artifacts remain safety-compliant and do not mutate deterministic classifications.

Batch 4 goals:

- Normalize caveat handling across all previous batches.
- Separate true matrix failures from data-source failures, stale unsupported wording, sample identity differences, and upstream news limitations.
- Produce final audit notes before any Batch 1-4 conclusion is treated as a hardening pass.

## 6. Unified Checklist For Every Batch

Use the same checklist for every sample:

- Input is existing evidence-pack data only; no new connector, web source, or manual data injection is introduced.
- Generated P1.1 artifacts are runtime outputs only and are not committed.
- `strategy_type`, `sub_type`, `status`, `confidence`, and score fields are not changed.
- The sample is assigned the correct audit identity: positive, validation, boundary, excluded, unsupported, data caveat, wording weakness, or sample identity scope difference.
- `company_transmission_path` either cites concrete evidence-pack field/value nodes or uses exactly `传导路径无法从当前证据包验证`.
- Any fallback `company_transmission_path` row uses `confidence_cap=not_assessable`.
- A non-fallback path does not rely on generic macro, industry, policy, news, theme, valuation, customer capex, strategic layout, or classifier label wording.
- `required_evidence`, `available_evidence`, `missing_evidence`, `what_was_checked`, `not_assessable_reason`, and `research_question` remain present and specific.
- Source independence is counted by source bucket.
- Consensus / divergence / contradiction stays `not_assessable` when fewer than two independent source buckets exist.
- Proxy guardrails are preserved: contract liabilities, capex, R&D ratio, inventory movement, policy support, customer capex, news, and theme heat do not become realization claims.
- Safety guardrails are preserved: no trading advice, target price, position sizing, execution instruction, technical analysis, or K-line language.
- Data caveats and wording weaknesses are recorded without automatically converting them into matrix logic failures.

## 7. Unified Data Caveat Record

Every data caveat should be recorded in the audit notes with the same fields:

```text
sample_code:
sample_name:
batch:
expansion:
audit_identity:
artifact_path:
artifact_generated_at:
observed_issue:
affected_block_or_field:
upstream_stage:
expected_p1_1_behavior:
audit_classification:
disposition:
follow_up:
```

Allowed `audit_classification` values:

- `data_caveat`: upstream raw / news / source block issue; not a P1.1 matrix failure by itself.
- `wording_weakness`: output text is stale, generic, or imprecise, while matrix behavior remains conservative.
- `sample_identity_scope_difference`: historical handoff identity differs from the current hardening matrix identity.
- `matrix_logic_failure`: P1.1 expands support, force-fits logic, violates fallback behavior, or makes unsupported claims.
- `safety_failure`: output contains trading, technical-analysis, target-price, or account-action language.
- `artifact_boundary_failure`: P1.1 mutates deterministic fields or writes outside allowed runtime artifact paths.

Known data caveat pattern:

- `news` / `latest_news` may report `Invalid regular expression: invalid escape sequence: \u`. Record this as `data_caveat` unless the P1.1 matrix incorrectly uses the failed news block as operating evidence.

## 8. Pass / Fail Standards

Pass when all of the following are true:

- The sample behavior matches its accepted audit identity.
- Positive samples stay inside their first-version expansion scope.
- Validation / boundary samples are not force-fit into positive primary-sample logic.
- Unsupported and excluded samples stay unsupported, `not_assessable`, or conservative.
- Fallback `company_transmission_path` and `confidence_cap=not_assessable` behavior is correct.
- Evidence paths cite concrete evidence-pack nodes when non-fallback.
- Missing evidence remains explicit and research-question-oriented.
- Proxy and safety guardrails are preserved.
- Runtime artifacts remain independent and are not committed.
- Any caveat is recorded under the appropriate caveat class rather than silently ignored.

Fail when any of the following are true:

- P1.1 mutates deterministic `status`, `confidence`, score, `strategy_type`, `sub_type`, classifier routing, connector behavior, readiness, scoring, HTML, Dashboard, config, tests, regression expected files, or committed output.
- A boundary, excluded, theme-only, unknown, or unsupported sample is treated as first-version positive support without a new accepted design / implementation / acceptance cycle.
- A validation sample is force-fit into another sample's primary-sample-specific logic.
- A row uses unsupported narrative as `company_transmission_path`.
- A fallback path does not use `confidence_cap=not_assessable`.
- Contract liabilities are treated as backlog; capex as capacity / utilization / revenue conversion; R&D ratio as moat; inventory movement as demand; news / policy / theme as realization; valuation as target price or trading signal.
- Output contains trading advice, technical analysis, target price, position sizing, execution instructions, or account actions.
- Data caveats are used as evidence, hidden, or misclassified as successful validation.

## 9. Special Audit Notes

`688631` sample identity note:

- `688631` was historically described in handoff material as a Low Altitude representative positive.
- In this Selected Validation Hardening matrix, `688631` is treated as a boundary sample for `airspace_platform_system` / low-altitude platform validation.
- Later audit should label this as `sample_identity_scope_difference`.
- Do not directly mark `688631` as a matrix logic failure solely because its historical identity and current hardening identity differ.

Generic unsupported wording note:

- Some generic unsupported text may still contain old descriptions from before the current scope update.
- If the artifact remains conservative, uses unsupported / `not_assessable` behavior, does not widen support, and preserves safety, record this first as `wording_weakness`.
- Do not directly mark stale generic unsupported wording as a matrix logic failure unless it causes actual scope expansion, force-fitting, unsafe claims, or incorrect evidence-path behavior.

## 10. Next-Step Recommendation

Enter Batch 1 validation run.

Batch 1 should start with the accepted first-version positive samples and confirm the frozen baseline before moving to boundary, negative, and caveat-focused batches.
