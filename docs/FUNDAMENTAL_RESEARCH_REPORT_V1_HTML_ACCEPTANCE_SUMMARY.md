# Fundamental Research Report V1 HTML Acceptance Summary

Date: 2026-05-28

Stage: Fundamental Skill Research Report V1 Three-Sample HTML Acceptance
Summary.

Status: documentation-only acceptance summary. This stage records that the
Research Report V1 HTML presentation-layer implementation and the three accepted
HTML runtime artifacts for `600406`, `002371`, and `002050` have passed
acceptance. It freezes the three-sample HTML presentation baseline. The next
user-facing orchestration design is recorded in
`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md` and does not
change the HTML baseline. This summary does not modify code, tests, fixtures,
pipeline behavior, scoring / readiness, Research Intelligence P1.1, regression
expected files, provider-primary behavior, or runtime artifacts. It does not run
a real smoke test, read `TUSHARE_TOKEN`, use the network, call Tushare or
AkShare, connect MCP, generate output, stage output, or provide investment
advice.

Latest verification results are quoted from the accepted stage input and were
not rerun in this documentation-only stage:

- targeted tests `124 passed`
- regression `passed=47 failed=0 total=47`

## 1. Final status

- HTML renderer implementation accepted.
- `600406` HTML accepted.
- `002371` HTML accepted.
- `002050` HTML accepted.
- Three-sample HTML validation passed.
- HTML presentation layer baseline frozen.

## 2. Accepted artifacts table

| code | company | profile | accepted HTML artifact path | acceptance result | key validation points | known limitations |
| --- | --- | --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | `stable_growth_grid_equipment` | `output/research_reports/20260528T012952/600406/fundamental_research_report_v1.html` | Accepted | Artifact boundary, secret scan, external resource scan, HTML structure, content consistency, profile isolation, data-quality caveat visibility, and no investment-action output passed. | V1 static HTML presentation layer only; not a Dashboard; content depth still depends on later official-source and evidence enrichment. |
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | `output/research_reports/20260528T090024/002371/fundamental_research_report_v1.html` | Accepted | Artifact boundary, secret scan, external resource scan, HTML structure, content consistency, semiconductor-equipment profile isolation, caveat visibility, and no investment-action output passed. | Content thickness remains V1 draft-level and can be strengthened with later orders, delivery, acceptance, revenue-recognition, collection, CNInfo, and official-parser evidence. |
| `002050` | 三花智控 | `advanced_manufacturing_thermal_management` | `output/research_reports/20260528T091133/002050/fundamental_research_report_v1.html` | Accepted | Artifact boundary, secret scan, external resource scan, HTML structure, content consistency, thermal-management profile isolation, caveat visibility, and no investment-action output passed. | Content thickness remains V1 draft-level and can be strengthened with later segment revenue, customer structure, orders, collections, CNInfo, and official-parser evidence. |

## 3. Acceptance summary

- Artifact boundary passed.
- Secret scan passed.
- External resource scan passed.
- HTML structure passed.
- Content consistency passed.
- Profile / cross-contamination passed.
- UI readability initial pass.
- Targeted tests `124 passed`.
- Regression `passed=47 failed=0 total=47`.

## 4. HTML guardrails

- HTML is a presentation layer, not an analysis layer.
- HTML does not re-analyze.
- HTML does not change Markdown conclusions.
- HTML does not change evidence labels.
- HTML does not hide caveats.
- HTML does not call providers.
- HTML does not read tokens.
- HTML does not use the network.
- HTML does not connect MCP.
- HTML does not output buy / sell / hold recommendations, target prices,
  position sizing, portfolio weights, account actions, or technical trading
  signals.
- HTML runtime artifacts remain ignored output and must not be committed.

## 5. Disclaimer note

Negative disclaimer wording such as "not a buy / sell recommendation", "does
not provide a target price", or "does not provide position-sizing guidance" is
allowed as boundary clarification. Positive investment-action language remains
prohibited.

If a future stage wants stricter literal zero-hit wording for investment-action
terms, that should be handled through a separately designed wording patch. Do
not manually edit the accepted runtime artifacts to chase stricter wording.

## 6. Known limitations

- HTML is a V1 presentation layer and is still not a Dashboard.
- UI received only static initial acceptance; no browser interaction smoke was
  run in this documentation-only stage.
- The three reports remain V1 drafts; content thickness still depends on later
  live provider, official parser, CNInfo, and evidence enrichment work.
- `002371` and `002050` content thickness can still be improved.
- Batch report has not been designed or accepted.
- Dashboard work has not been done for this Research Report V1 HTML baseline.
- User invocation / report orchestration is now designed but not implemented.
- Live provider report remains later work.
- Fixture promotion, validator, primary switch, promote rules, and Tushare
  primary remain later work.

## 7. Next recommended stage

1. Commit the user invocation / report orchestration design documentation patch.
2. Next work should move to single-stock user invocation / orchestration
   implementation, then local end-to-end runs for `600406`, `002371`, and
   `002050`.
3. Dashboard / batch report design should follow the accepted single-stock
   orchestration path, unless a separate stage asks only for focused HTML visual
   refinement.
4. Live provider report, official parser / CNInfo, fixture promotion,
   validator, and Tushare primary remain later work.

## 8. Safety confirmation

This documentation-only acceptance summary confirms:

- no token read;
- no network use;
- no provider call;
- no MCP connection;
- no new output generated;
- no runtime artifact submitted;
- no investment advice output.

## 9. User invocation follow-up

`docs/FUNDAMENTAL_SKILL_USER_INVOCATION_ORCHESTRATION_DESIGN.md` defines the
natural-language Codex / GPT-5.5 entry point, normalized request schema,
single-stock orchestration pipeline, data-mode rules, missing-artifact
behavior, role split, final response shape, future CLI shape, safety non-goals,
and relationship to Dashboard / batch.

That design keeps HTML as the final presentation layer. It does not ask HTML to
re-analyze, change conclusions, hide caveats, call providers, use the network,
read tokens, connect MCP, or produce trading advice.
