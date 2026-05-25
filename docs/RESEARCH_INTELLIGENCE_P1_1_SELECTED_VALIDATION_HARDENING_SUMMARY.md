# Research Intelligence P1.1 Selected Validation Hardening Summary

Date: 2026-05-26

Stage: Selected Validation Hardening Summary / Release Note.

Status: documentation-only. This file archives the Batch 1-4 selected validation hardening results for the frozen P1.1 independent Research Intelligence artifact baseline. It does not change code, tests, config, pipeline behavior, classifier rules, connectors, scoring, readiness, HTML / Dashboard behavior, generated output, or regression expectations.

## 1. Hardening Summary

Research Intelligence P1.1 Selected Validation Hardening has completed Batch 1 through Batch 4.

The current P1.1 frozen baseline remains stable:

- Batch 1: passed.
- Batch 2: passed.
- Batch 3: passed.
- Batch 4: passed.
- No `matrix_logic_failure` was found.
- No `safety_failure` was found.
- No `artifact_boundary_failure` was found.

The validation confirms that the P1.1 artifact layer remains independent from the deterministic fundamental pipeline and continues to write only runtime P1 artifacts:

- `output/research_intelligence_p1_<code>.json`
- `output/research_questions_p1_<code>.json`
- `output/research_questions_p1_<code>.md`

Runtime artifacts are not intended to be committed.

Recent frozen baseline reference results remain:

- `pytest`: `484 passed`
- Regression suite: `passed=47 failed=0 total=47`

## 2. Batch 1 Summary

Batch 1 validated the accepted first-version positive samples:

- `002837`
- `300442`
- `603259`
- `601698`
- `000099`
- `000426`
- `002371`
- `002050`
- `600406`

Result:

- All 9 first-version positive samples entered the expected P1.1 driver matrix.
- No positive sample regressed into generic `unsupported_pilot_strategy`.
- `company_transmission_path` behavior passed: non-fallback paths were evidence-pack-bound, and fallback paths used `confidence_cap=not_assessable`.
- Source bucket counting remained bucket-deduplicated.
- Consensus / divergence / contradiction remained inside the P1.1 shell boundary.
- Safety boundary passed: no trading advice, target price, position sizing, technical analysis, K-line content, or account-action language.
- `output/reports` was not modified.
- Data caveats were mainly upstream `latest_news` / `news` limitations and did not affect the P1.1 matrix conclusion.

Batch 1 is recommended as passed.

## 3. Batch 2 Summary

Batch 2 validated same-strategy validation and boundary samples:

- `002335`
- `002518`
- `301018`
- `300759`
- `002821`
- `300347`
- `300363`
- `688631`
- `688012`
- `688981`
- `603501`
- `300604`
- `601689`
- `002028`

Result:

- Same-strategy validation and boundary samples did not widen first-version support.
- `301018` entered the AI Datacenter cooling matrix as a same-subtype validation observation, not as force-fit behavior.
- `688631` was recorded as `sample_identity_scope_difference`: historical handoff described it as a Low Altitude representative positive, while this hardening matrix treats it as an `airspace_platform_system` boundary sample.
- Semiconductor validation samples did not inherit the `002371` first-version equipment-specific logic.
- `601689` remained an Advanced Manufacturing validation / boundary sample and did not become first-version positive support.
- `002028` remained Stable Growth validation / boundary only and did not become first-version positive support.
- Generic unsupported support-scope wording was observed as `wording_weakness`, not matrix failure, because behavior stayed conservative and `not_assessable`.

Batch 2 is recommended as passed.

## 4. Batch 3 Summary

Batch 3 validated negative, excluded, adjacent, unsupported, theme-only, news-only, and synthetic-boundary samples:

- `600118`
- `002465`
- `688066`
- `002895`
- `688070`
- `002085`
- `001696`
- `600967`
- `601899`
- `603993`
- `002371`
- `002050`
- `300308`
- `300476`
- `600276`
- `999997`
- `999998`
- `999999`

Result:

- Negative, excluded, adjacent, and unsupported samples did not expand into formal first-version support.
- `002371` was handled as a correct-special-case: although it appeared in Resource boundary audit identity, its actual `strategy_type=semiconductor_cycle` correctly entered the Semiconductor first-version matrix.
- `002050` was handled as a correct-special-case: although it appeared in Resource boundary audit identity, its actual `strategy_type=advanced_manufacturing_growth` correctly entered the Advanced Manufacturing first-version matrix.
- `601899` remained `resource_core` design-only / unsupported / `not_assessable`.
- `603993` had `strategy_type=resource_swing` but did not enter Resource first-version positive support, because Resource first-version only supports `000426`.
- `600276` remained Stable Growth excluded with conservative unsupported behavior.
- `300308` and `300476` remained `right_trend_growth` unsupported boundaries.
- Missing synthetic samples were recorded as `data_caveat: evidence_pack_missing`.

Batch 3 is recommended as passed.

## 5. Batch 4 Summary

Batch 4 replayed caveat, wording, and audit-consistency classifications across Batch 1-3.

Result:

- Only `data_caveat`, `wording_weakness`, and `sample_identity_scope_difference` / correct-special-case observations were found.
- No `matrix_logic_failure` was found.
- No `safety_failure` was found.
- No `artifact_boundary_failure` was found.
- Data caveats were upstream or operator-side issues and did not affect P1.1 matrix conclusions.
- Wording weaknesses did not cause scope expansion, force-fitting, or unsafe claims.

Batch 4 is recommended as passed.

## 6. Data Caveat Summary

The following caveats were observed across Batch 1-4 and should be classified as upstream / operator-side caveats unless P1.1 uses failed data as operating evidence:

| Caveat | Scope | Classification | Hardening impact | Follow-up |
| --- | --- | --- | --- | --- |
| `latest_news missing` | Repeated across samples with existing evidence packs | `data_caveat` | Does not affect pass/fail | Data-source / connector future issue |
| `news: Invalid regular expression: invalid escape sequence: \u` | Repeated across samples with existing evidence packs | `data_caveat` | Does not affect pass/fail | Data-source / connector future issue |
| `WinError 10013` | Observed on a subset of connector fetch traces | `data_caveat` | Does not affect pass/fail | Data-source / connector future issue |
| `basic_info` fetch failure trace | Observed on a subset of evidence packs | `data_caveat` | Does not affect pass/fail | Data-source / connector future issue |
| `financial_indicator` fetch failure trace | Observed on a subset of evidence packs | `data_caveat` | Does not affect pass/fail | Data-source / connector future issue |
| `valuation` fetch failure trace | Observed on a subset of evidence packs | `data_caveat` | Does not affect pass/fail | Data-source / connector future issue |
| `business_composition` fetch failure trace | Observed on a subset of evidence packs | `data_caveat` | Does not affect pass/fail | Data-source / connector future issue |
| `evidence_pack_missing` | `600118`, `002465`, `688066`, `999997`, `999998`, `999999` | `data_caveat` | Does not affect pass/fail; samples were not run | Data-source / fixture availability issue |
| PowerShell / JSON / REPL parsing caveat | Operator-side command parsing and REPL redeclaration during audit work | operator-side caveat | Does not affect artifacts or pass/fail | Record only |

These caveats did not become P1.1 matrix failures because the P1.1 artifacts did not treat failed news, failed raw data, failed connector traces, or missing evidence packs as company operating facts.

## 7. Wording Weakness Summary

The following wording weaknesses were observed:

- Generic unsupported support-scope wording does not fully include `stable_growth` / `600406`.
- Unsupported question wording, especially `what expansion template would be required before assessment?`, is too broad.
- Generic fallback questions repeat across unsupported samples.
- Some unsupported wording is stale or generic compared with the current frozen support scope.

Current classification:

- `wording_weakness`
- Not `matrix_logic_failure`

Reason:

- Artifact behavior remains conservative.
- Unsupported samples remain `unsupported_pilot_strategy` / `not_assessable`.
- No first-version support was widened.
- No force-fit into primary sample logic was observed.
- No unsafe claim was observed.

Recommended follow-up:

- A small wording-only unsupported template patch can improve clarity.
- The patch should update the unsupported support-scope wording to include `stable_growth` / `600406`.
- The patch should replace the generic fallback question with a more specific evidence-gate question.
- The patch should not change P1.1 routing, matrix logic, classifier behavior, scoring, readiness, or output boundaries.

## 8. Sample Identity / Correct-Special-Case Summary

| Sample | Actual behavior | Audit classification |
| --- | --- | --- |
| `688631` | Historical handoff described it as Low Altitude representative positive, while hardening treats `low_altitude_economy_infrastructure / airspace_platform_system` as boundary | `sample_identity_scope_difference` |
| `002371` | Resource boundary identity in Batch 3, but actual `semiconductor_cycle` correctly enters Semiconductor first-version matrix | correct-special-case |
| `002050` | Resource boundary identity in Batch 3, but actual `advanced_manufacturing_growth` correctly enters Advanced Manufacturing first-version matrix | correct-special-case |
| `301018` | AI Datacenter same-subtype cooling sample enters cooling matrix | validation observation, not force-fit |
| `603993` | `strategy_type=resource_swing`, but not first-version positive because Resource first-version only supports `000426` | boundary / unsupported |
| `002028` | `strategy_type=stable_growth`, but validation / boundary only because Stable Growth first-version only supports `600406` | boundary / unsupported |
| `601899` | `strategy_type=resource_core` remains design-only | design-only / unsupported |
| `300308` | `strategy_type=right_trend_growth` remains unsupported | unsupported boundary |
| `300476` | `strategy_type=right_trend_growth` remains unsupported | unsupported boundary |

These identity notes do not indicate matrix failures.

## 9. Hardening Conclusion

P1.1 selected validation hardening passed.

The current baseline can continue to remain frozen.

Confirmed boundaries:

- Runtime P1 artifacts should not be committed.
- `output/reports` was not modified by the validation runs.
- Source independence remains counted by source bucket.
- Fallback `company_transmission_path` remains `传导路径无法从当前证据包验证`.
- Fallback rows use `confidence_cap=not_assessable`.
- Non-fallback paths remain evidence-pack-bound.
- Proxy guardrails remain intact:
  - Contract liabilities are not backlog.
  - Capex is not capacity release, utilization, delivery, or revenue conversion.
  - R&D ratio is not a technology moat.
  - News, policy, and theme heat are not business realization.
  - Commodity price is not company revenue.
  - Semiconductor cycle is not company benefit.
  - Robotics theme is not revenue realization.
  - The `stable_growth` label is not operating steadiness.
- Safety boundary remains intact:
  - No trading advice.
  - No target price.
  - No position sizing.
  - No technical analysis.
  - No K-line content.
  - No account-action language.

## 10. Follow-Up Patch Recommendation

Batch 4 follow-up classification:

- A. No real P1.1 logic patch needed.
- B. Documentation-only caveat summary patch: this file is that patch.
- C. Wording-only unsupported template patch: recommended as a small follow-up.
- D. Data-source / connector future issue: `news` / `latest_news`, `WinError 10013`, and regex caveats should be handled in a future data-source or connector phase.
- E. Real P1.1 logic patch: not needed at this time.

## 11. Next-Step Recommendation

Recommended next steps:

1. Commit this summary document.
2. Consider one small wording-only unsupported template patch.
3. Do not directly enter `right_trend_growth`.
4. Do not directly enter P1.2.
5. Keep Tushare / data provider abstraction for P1.2 or a dedicated data-source upgrade stage.

