# Fundamental Research Report V1 Markdown Profile Acceptance Summary

Date: 2026-05-28

Stage: Fundamental Skill Research Report V1 Cross-Industry Markdown Profile
Acceptance Summary.

Status: documentation-only Markdown acceptance summary, now followed by
accepted HTML presentation-layer implementation and three-sample HTML baseline
freeze. The current HTML acceptance summary is
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_ACCEPTANCE_SUMMARY.md`, and the HTML
design boundary remains in
`docs/FUNDAMENTAL_RESEARCH_REPORT_V1_HTML_PRESENTATION_DESIGN.md`.

This summary records the accepted Markdown presentation profiles and their
relationship to the now-frozen HTML baseline. It does not modify code, tests,
fixtures, pipeline behavior, scoring / readiness, Research Intelligence P1.1,
HTML / Dashboard implementation, regression expected files, or runtime output.
It does not run smoke tests, read `TUSHARE_TOKEN`, use the network, call Tushare
or AkShare, connect MCP, or provide buy / sell advice, target prices, position
sizing, portfolio weights, or technical trading signals.

Markdown-stage verification results are quoted from the accepted stage input and
were not rerun here:

- targeted tests `86 passed`
- full pytest `734 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

HTML-stage verification results are quoted from the accepted stage input and
were not rerun here:

- targeted tests `124 passed`
- regression `passed=47 failed=0 total=47`

## 1. Final status

- `600406` Markdown accepted.
- `002371` Markdown accepted.
- `002050` Markdown accepted.
- Presentation profile registry accepted.
- Professional analyst voice gate accepted.
- Cross-industry Markdown validation passed.
- HTML renderer implementation accepted.
- `600406`, `002371`, and `002050` HTML accepted.
- HTML presentation layer baseline frozen.

## 2. Accepted Markdown artifacts

| code | company | profile | industry focus | accepted runtime artifact path | known limitations |
| --- | --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | `stable_growth_grid_equipment` | Grid equipment, digital grid, power automation | `output/research_reports/20260527T210301/600406/fundamental_research_report_v1.md` | Main-business official source, business-composition period / classification / ratio, and valuation-date evidence still depend on later evidence enrichment. |
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | Semiconductor equipment, domestic substitution, wafer-fab capex | `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md` | Content thickness remains V1 draft-level; orders, delivery, acceptance, revenue recognition, and collection evidence can be strengthened later. |
| `002050` | 三花智控 | `advanced_manufacturing_thermal_management` | Thermal management, refrigeration control, new-energy vehicles, new-business optionality | `output/research_reports/20260528T003826/002050/fundamental_research_report_v1.md` | Content thickness remains V1 draft-level; segment revenue, customer structure, orders, and collection evidence can be strengthened later. |

## 3. Cross-contamination summary

- `600406` did not inherit semiconductor or robot / new-business language.
- `002371` did not inherit grid or thermal-management language.
- `002050` did not inherit grid or semiconductor-equipment language.
- Current V1 hard-fail term isolation is effective for the three accepted
  samples.
- Future cross-industry terms require a separately designed
  evidence-label-aware allowlist.

## 4. Product readability summary

- Markdown remains the accepted narrative source for the HTML presentation
  layer.
- The three Markdown reports are usable as investment-manager draft baselines,
  with visible evidence labels, data-quality caveats, evidence gaps, rebuttal
  conditions, and follow-up variables.
- The reports are still V1 drafts, not final formal research reports.
- Content depth still depends on later live provider, official parser, CNInfo,
  and evidence enrichment work.

## 5. HTML acceptance follow-up

The Markdown profile baseline is now paired with the frozen three-sample HTML
presentation baseline:

| code | company | profile | accepted HTML artifact |
| --- | --- | --- | --- |
| `600406` | 国电南瑞 | `stable_growth_grid_equipment` | `output/research_reports/20260528T012952/600406/fundamental_research_report_v1.html` |
| `002371` | 北方华创 | `semiconductor_equipment_cycle` | `output/research_reports/20260528T090024/002371/fundamental_research_report_v1.html` |
| `002050` | 三花智控 | `advanced_manufacturing_thermal_management` | `output/research_reports/20260528T091133/002050/fundamental_research_report_v1.html` |

HTML acceptance confirmed artifact boundary, secret scan, external resource
scan, HTML structure, content consistency, profile isolation, caveat visibility,
and initial UI readability. HTML did not re-analyze, did not change Markdown
conclusions, did not change evidence labels, did not hide caveats, did not call
providers, did not use the network, did not read tokens, did not connect MCP,
and did not output investment-action recommendations, target prices, position
sizing, portfolio weights, or technical trading signals.

## 6. Known limitations

- HTML is a V1 presentation layer and is still not a Dashboard.
- UI acceptance was static initial acceptance; no browser interaction smoke was
  run in this documentation-only stage.
- `002371` and `002050` content thickness can still be improved.
- Batch report has not been designed or accepted.
- Dashboard work has not been done for this Research Report V1 HTML baseline.
- Live provider report remains later work.
- Official parser / CNInfo remains later work.
- Fixture promotion, validator, promote rules, and Tushare primary remain later
  work.

## 7. Next recommended stage

The next step is no longer single-stock HTML generation. Recommended next
directions are Dashboard / batch report design or HTML visual refinement.
Promote rules, validator, fixture promotion, live provider report, official
parser / CNInfo, and Tushare primary remain later work.

## 8. Safety

This documentation-only summary confirms:

- no token read;
- no network use;
- no provider call;
- no MCP connection;
- no new output generated;
- no runtime artifact submitted;
- no investment advice output.
