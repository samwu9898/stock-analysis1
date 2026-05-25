# Research Intelligence P1.1 Expansion Baseline Release Note

Date: 2026-05-25

Current stage: P1.1 independent Research Intelligence artifact baseline.

Status: P1.1 expansion baseline frozen.

## 1. Baseline Status

Research Intelligence P1.1 has completed the current expansion baseline across implementation, acceptance, observation, and documentation sync. This baseline is frozen as an independent AI analyst-layer Research Intelligence artifact. It does not change the deterministic fundamental pipeline and should not be widened implicitly.

## 2. Accepted Support Scope

Current P1.1 accepted support includes only these 8 strategy types:

- `ai_datacenter_infrastructure`
- `life_science_cxo_services`
- `satellite_communication_infrastructure`
- `low_altitude_economy_infrastructure`
- `resource_swing`
- `semiconductor_cycle`
- `advanced_manufacturing_growth`
- `stable_growth`

## 3. First-Version Scope By Expansion

- AI Datacenter: first-version support covers cooling / liquid-cooling infrastructure and datacenter operator paths. Representative accepted samples are `002837` and `300442`.
- CXO: first-version support covers `life_science_cxo_services`. Representative samples include `603259` and related accepted CXO samples.
- Satellite: first-version support centers on `601698`.
- Low Altitude: first-version support centers on `000099`.
- Resource Swing: first-version support is `000426` only. `resource_core` is deferred.
- Semiconductor: first-version support is `002371` only.
- Advanced Manufacturing: first-version support is `002050` only. `601689` is validation / boundary only.
- Stable Growth: first-version support is `600406` only. `002028` is validation / boundary only, and `600276` is excluded.

## 4. Deferred / Unsupported Scope

- `resource_core`: design-only / deferred.
- `right_trend_growth`: not included in P1.1.
- `theme_only` / `unknown`: unsupported / `not_assessable`.
- `601899` / `603993`: Resource validation / boundary only.
- `601689`: Advanced Manufacturing validation / boundary only.
- `002028`: Stable Growth validation / boundary only.
- `600276`: Stable Growth excluded.

## 5. Artifact Boundary

P1.1 only writes independent runtime artifacts:

- `output/research_intelligence_p1_<code>.json`
- `output/research_questions_p1_<code>.json`
- `output/research_questions_p1_<code>.md`

P1.1 does not write:

- `output/reports`
- HTML Report
- Dashboard
- deterministic result

P1.1 output artifacts are generated runtime artifacts and should not be committed to git.

## 6. Architecture Boundary

P1.1 remains inside the independent Research Intelligence artifact layer:

- It does not call LLMs or the OpenAI API.
- It does not use network access.
- It does not connect new data sources.
- It does not modify connector, classifier, scoring, readiness, or result assembler behavior.
- It does not modify `status`, `confidence`, `score`, `strategy_type`, or `sub_type`.
- It does not connect to the HTML renderer or Dashboard.

## 7. Core Guardrails

The accepted P1.1 expansion baseline keeps these shared guardrails:

- `company_transmission_path` must be evidence-bound.
- When no concrete evidence node exists, the path must be exactly: `传导路径无法从当前证据包验证`.
- Source bucket counting deduplicates by bucket.
- Consensus / divergence / contradiction remain P1.1 shell-boundary fields rather than full multi-source adjudication.
- Contract liabilities are not backlog.
- Capex is not capacity release, utilization, or revenue conversion.
- R&D ratio is not a technology barrier.
- Policy, news, and theme heat are not business realization.
- Commodity price is not company revenue.
- Semiconductor cycle is not company benefit.
- Robotics theme is not revenue realization.
- The `stable_growth` label is not operating steadiness.
- Industry rigid demand, infrastructure attributes, and SOE / central-SOE attributes are not demand durability.
- Valuation explainability must not output valuation high/low, target price, or trading judgment.
- P1.1 must not output trading advice, target price, position sizing, technical analysis, or K-line content.

## 8. Recent Validation Results

- `pytest`: `484 passed`
- Regression suite: `passed=47 failed=0 total=47`
- P1.1 baseline check: passed
- Git hygiene: `.pytest_tmp*/` is ignored

This release note does not rerun tests. It records the latest accepted validation results.

## 9. Known Caveats

- Some samples still have upstream `latest_news` / `news` data caveats, including errors such as `Invalid regular expression: invalid escape sequence: \u`.
- These upstream/news data caveats do not affect the P1.1 baseline boundary audit conclusion.
- Future data needs remain open for multi-period data, customer / order evidence, capex split, receivable aging, product-level inventory, and other company-level transmission nodes.

## 10. Next-Step Recommendation

Do not move directly into P1.2 and do not immediately expand `right_trend_growth` by default. The preferred immediate action is to keep this P1.1 baseline release note / archive as the frozen checkpoint.

Future optional routes:

- A. `right_trend_growth` design audit
- B. P1.2 multi-source consensus / divergence design audit
- C. P1.1 selected validation hardening

Priority should be decided by the next user need rather than by implicit widening of the accepted P1.1 baseline.
