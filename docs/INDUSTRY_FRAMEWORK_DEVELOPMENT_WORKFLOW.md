# Industry Framework Development Workflow

Date: 2026-05-20

Scope:

- Standard workflow for adding new fundamental industry frameworks.
- This workflow is based on the completed `satellite_communication_infrastructure` expansion.
- It is intended for future frameworks such as `low_altitude_economy_infrastructure`, CXO, AI data center infrastructure, and intelligent driving.
- It is documentation-only. It does not change classifier, connector, pipeline, dashboard, scoring, `technical_skill`, or `trader_skill`.

Non-negotiable boundaries:

- Do not connect trading accounts.
- Do not output trading advice, target prices, position sizing, timing advice, or account actions.
- Do not introduce technical analysis or technical indicators.
- Do not implement `technical_skill`.
- Do not implement `trader_skill`.
- Do not change the deterministic pipeline outside the approved implementation stage.
- Do not let industry expansion weaken tests or the regression suite.
- Expand by business model, not by a single stock.

## Completed Case Reference: satellite_communication_infrastructure

The `satellite_communication_infrastructure` framework is the baseline case for this workflow.

Observed sequence:

- Out-of-sample audit on 601698 China Satellite Communications showed `unknown` / `insufficient_data` / `low`, which was conservative but not professionally descriptive for the business model.
- The design audit created the `satellite_communication_infrastructure` framework before implementation.
- Negative samples included 600118, 002465, 688066, and 002895 to prevent confusing satellite manufacturing, terminals, remote sensing, or data software with satellite communication infrastructure operations.
- After implementation, 601698 classified as `satellite_communication_infrastructure` / `neutral` / `low`.
- Regression coverage expanded to 19 samples and passed.
- A garbled text guard was added as an AI report quality guard.

This case should be used as the reference path: first observe a framework gap, then design boundaries, then review, then implement narrowly, then freeze the baseline.

## 1. Out-of-Sample Generalization Audit

Purpose:

- Run the current system on a stock outside existing frameworks.
- Observe whether classification is `unknown`, `theme_only`, or a wrong existing framework.
- Observe whether the AI report becomes overconfident despite weak framework support.
- Observe whether must-track indicators are generic or unprofessional for the business model.
- Decide whether a new industry framework is justified.

Inputs:

- One real target sample outside existing frameworks.
- Existing deterministic pipeline and AI analyst layer.
- No code changes during this stage.

Required artifacts:

- `output/fundamental_<code>.json`
- `output/evidence_pack_<code>.json`
- `output/ai_prompt_<code>.md`
- `output/ai_report_<code>.json` and/or `output/ai_report_<code>.md`
- Out-of-sample audit conclusion

Checklist:

- Did the current classifier return `unknown`, `theme_only`, or an existing framework?
- If classified into an existing framework, is that classification commercially defensible?
- Is the AI report cautious about missing framework-specific evidence?
- Are must-track indicators specific to the company's actual business model?
- Are important economic drivers missing from the current analysis context?
- Is the gap recurring for a business model, not just a one-stock edge case?
- Is there enough public information to define a repeatable framework?
- Would a new framework improve classification quality without weakening existing boundaries?
- Are all outputs free of trading advice and technical analysis?

Decision rule:

- Proceed to Framework Design Audit only if the issue is a repeatable business-model gap and cannot be solved by simple data completeness wording.
- Do not create a framework only because one stock is popular, high-profile, or difficult to classify.

## 2. Framework Design Audit

Purpose:

- Design only; do not implement.
- Define `strategy_type`, classification boundary, data requirements, risk guards, must-track indicators, confidence rules, and regression samples.
- Make the business-model boundary explicit before touching deterministic code.

Required artifact:

- `docs/<FRAMEWORK_NAME>_DESIGN_AUDIT.md`

Checklist:

- Is `strategy_type` explicit, stable, and named by business model?
- Is the framework defined by business model rather than a single stock?
- Is the definition narrow enough to be testable?
- Are positive classification signals tied to main business and revenue composition?
- Are negative / exclusion signals specific and realistic?
- Are positive samples reasonable?
- Are negative samples concrete and close enough to catch misclassification risk?
- Are Required / Preferred / Optional data realistic under public-data constraints?
- Which fields are hard to obtain from public data?
- Which fields are proxies and how are they labeled?
- Does the design avoid treating theme popularity as fundamental realization?
- Are confidence rules conservative enough?
- Do risk guards cover theme-only, proxy-as-fact, and business-model confusion?
- Are must-track indicators professional for the framework?
- Does the design explain what should not enter v1 scoring?
- Is the regression plan clear enough to lock both positive and negative cases?
- Does the design preserve no-trading-advice and no-technical-analysis boundaries?

Minimum design sections:

- Framework name
- `strategy_type`
- Definition
- Business model boundary
- Positive classification signals
- Negative / exclusion signals
- Positive samples
- Negative samples
- Required data
- Preferred data
- Optional data
- Confidence-gating indicators
- Interpretation guards
- Risk guards
- Must-track indicators
- Readiness / confidence rules
- Scoring notes
- Evidence pack requirements
- AI report requirements
- Regression test plan
- v1 implementation scope
- Deferred / not-in-v1 items
- Acceptance criteria

## 3. Optional External Review

Purpose:

- Use Claude or another model for independent design audit when the framework boundary is complex.
- Focus review on classification boundary, misclassification risk, data availability, risk guards, and test design.
- External review does not directly change code.

Checklist:

- Was the external reviewer given the design audit, not implementation files only?
- Did the review assess business-model boundaries rather than stock opinions?
- Did it identify false-positive risks and close negative samples?
- Did it challenge unavailable or unstable data fields?
- Did it review confidence gating separately from scoring strength?
- Did it check whether proxies are clearly labeled?
- Did it review regression sample coverage?
- Did it preserve the no-trading-advice and no-technical-analysis boundaries?
- Are all external suggestions treated as input for human / main-planner judgment, not automatic changes?

Output:

- External review notes, pasted or summarized in the design audit or a companion note.
- Clear recommendation: proceed, revise before implementation, or defer.

## 4. Design Revision

Purpose:

- Revise the design after external review and main-planner judgment.
- Explicitly state which suggestions are accepted, deferred, or rejected.
- Define v1 implementation scope and out-of-scope items.

Checklist:

- Are accepted external suggestions listed?
- Are deferred suggestions listed with reasons?
- Are rejected suggestions listed when they would violate scope or data reality?
- Is v1 scope narrow enough to implement safely?
- Are not-in-v1 items explicit?
- Are hard-to-obtain fields moved from Required to Preferred / Optional when needed?
- Are scoring notes conservative?
- Are confidence caps stated for missing key indicators?
- Are proxy fields labeled as proxy and excluded from fact claims?
- Are regression samples still specific and feasible?
- Does the revised design still avoid trading advice and technical analysis?

Output:

- Updated `docs/<FRAMEWORK_NAME>_DESIGN_AUDIT.md`.
- Implementation authorization only after design revision is accepted.

## 5. Implementation

Purpose:

- Implement only the approved v1 scope.
- Modify classifier, framework logic, data requirements, analysis context, scoring config, evidence pack, and tests only as approved by design.
- Do not add out-of-design proxies, scoring rules, data connections, dashboards, trading features, or technical indicators.

Allowed change areas, when explicitly required by the accepted design:

- Classifier / classification schema.
- Framework-specific data readiness requirements.
- Analysis context and result assembly.
- Scoring configuration and conservative confidence rules.
- Evidence pack fields.
- AI prompt / markdown rendering safety requirements.
- Unit tests and regression fixtures.
- Documentation updates.

Implementation checklist:

- Is every code change traceable to the accepted design audit?
- Are only allowed files modified?
- Are new tests added for the new framework?
- Is a positive regression fixture added?
- Are negative regression fixtures added?
- Do old samples show no unintended drift?
- Is there no trading advice?
- Is there no technical analysis?
- Is no proxy treated as fact?
- Are missing confidence-gating indicators handled conservatively?
- Are risk guards implemented as guards, not as optimistic scoring boosts?
- Are must-track indicators framework-specific?
- Are AI report requirements aligned with evidence pack fields?
- Are schema and safety checks still passing?

Hard stops:

- Do not implement `technical_skill`.
- Do not implement `trader_skill`.
- Do not connect trading accounts.
- Do not change deterministic pipeline architecture beyond the approved framework expansion.
- Do not add data probes, cache outputs, or generated `output/` artifacts to commits.

## 6. Acceptance

Purpose:

- Verify real target samples, negative samples, regression stability, AI report safety, confidence behavior, and risk guards.

Acceptance checklist:

- Does the target sample classify into the intended `strategy_type`?
- Is the target sample status reasonable under available evidence?
- Is confidence conservative and not over-upgraded by theme evidence?
- Do negative samples avoid false classification into the new framework?
- Are old regression samples unchanged except for intentional, documented changes?
- Does the AI report avoid overconfidence?
- Does the AI report avoid trading advice?
- Does the AI report avoid technical analysis?
- Does the AI report distinguish facts from proxies?
- Do schema and safety checks pass?
- Does `pytest` pass?
- Does the regression suite pass?
- Do risk guards fire when theme-only or proxy-only evidence appears?
- Are must-track indicators professional for the new framework?

Recommended commands:

```bash
python -m pytest tests
python scripts/run_regression_suite.py
```

When the change only updates documentation, tests are optional. If tests are skipped for a documentation-only stage, state that explicitly in the final summary.

## 7. Commit / Baseline Freeze

Purpose:

- Freeze the new framework after tests and regression pass.
- Keep the repository clean.
- Avoid committing generated runtime artifacts.

Checklist:

- Did `pytest` pass?
- Did the regression suite pass?
- Is `git status` reviewed?
- Are only intended source, test, and documentation files staged?
- Are `output/`, cache files, data probe outputs, and ad hoc generated artifacts excluded?
- Is the commit message explicit about the framework and scope?
- Is the branch pushed if required?
- Is the regression baseline now the new reference point?

Output:

- Commit containing only intended implementation, tests, and documentation.
- Clean working tree after commit, except for intentionally untracked local files.

## Applying This Workflow To low_altitude_economy_infrastructure

For `low_altitude_economy_infrastructure`, start with the same sequence:

1. Run an out-of-sample audit on representative low-altitude economy stocks without changing code.
2. Check whether current outputs become `theme_only`, `unknown`, or misclassified into advanced manufacturing, communications equipment, or generic theme exposure.
3. Confirm whether the candidate framework is an infrastructure business model, not a broad low-altitude theme bucket.
4. Design boundaries before implementation: infrastructure operators, airspace / route / takeoff-and-landing infrastructure, dispatch / operation platforms, and service monetization may differ from drone manufacturing, parts, sensors, batteries, mapping, or speculative policy themes.
5. Define negative samples close to the boundary, especially drone OEMs, component suppliers, mapping software, defense electronics, and theme-only companies.
6. Treat policy pilots, demonstration zones, and intent announcements as proxies unless revenue, contracts, assets, or cash-flow evidence supports realization.
7. Cap confidence when operational utilization, paid service revenue, contract duration, customer mix, or infrastructure asset data is missing.

The key discipline is the same as the satellite case: build a repeatable business-model framework, not a stock-specific explanation.
