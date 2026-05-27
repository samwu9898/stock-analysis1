# Fundamental Research Report V1 HTML Presentation Design

Date: 2026-05-28

Stage: Fundamental Skill Research Report V1 HTML Presentation Layer Design.

Status: documentation-only design. This stage does not write code, tests,
fixtures, pipeline changes, scoring / readiness changes, P1.1 changes,
regression expected files, provider-primary behavior, runtime output, default
output, provider raw artifacts, evidence packs, candidate reports, or review
decision artifacts. It does not run smoke tests, read `TUSHARE_TOKEN`, use the
network, call Tushare or AkShare, connect MCP, promote fixture values,
automatically merge providers, or output buy / sell advice, target prices,
position sizing, portfolio weights, or technical trading signals.

## 1. HTML Layer Positioning

The HTML layer is a presentation layer, not an analysis layer.

Required positioning:

- HTML displays accepted Research Report V1 content.
- HTML does not regenerate research conclusions.
- HTML does not reinterpret, improve, soften, strengthen, or override evidence
  labels.
- HTML does not call any data provider.
- HTML does not read `TUSHARE_TOKEN`.
- HTML does not use the network.
- HTML does not modify Research Report V1 JSON.
- HTML does not modify Markdown presentation output.
- HTML does not modify candidate reports, review decisions, or evidence packs.
- HTML does not modify scoring, readiness, or Research Intelligence P1.1.
- HTML does not switch a provider primary.
- HTML does not automatically merge AkShare and Tushare.
- HTML does not produce buy / sell / hold recommendations, target prices,
  position sizing, portfolio weights, account-level actions, or technical
  trading signals.

HTML V1 should be treated as a deterministic renderer over accepted report
content. If an input is incomplete, the HTML should expose the incompleteness as
a visible caveat rather than generating a stronger narrative.

## 2. Input Design

HTML V1 may accept two input classes.

### Preferred Input

The preferred input is the already generated Markdown presentation output, for
example:

```text
fundamental_research_report_v1.md
```

The Markdown presentation layer is the primary narrative source because it has
already passed the profile registry, profile-specific Markdown rendering, and
professional analyst voice gate.

### Optional Structured Input

The optional structured input is:

```text
fundamental_research_report_v1.json
```

The structured payload may be used only to supplement display metadata, cards,
evidence labels, source artifact references, data-quality caveats, and
technical appendix fields. It must not be used to re-analyze the company or to
rewrite the accepted Markdown conclusion.

### Input Rules

- HTML uses Markdown / presentation-layer output as the main content source.
- Structured payload can only assist presentation.
- Structured payload cannot change the report conclusion, evidence label,
  caveat state, profile wording, risk ordering, opportunity ordering, rebuttal
  condition, or follow-up variable.
- HTML must not generate conclusions directly from raw provider artifacts.
- HTML must not bypass Markdown profile selection.
- HTML must not bypass the professional analyst voice gate.
- If Markdown and structured payload conflict, the renderer should preserve the
  Markdown narrative and surface the structured mismatch as a technical caveat
  or validation issue for future implementation, not resolve it by analysis.
- Raw provider artifacts, evidence packs, fact candidates, review decisions,
  provider diffs, or P1.1 outputs are not direct HTML conclusion sources in V1.

## 3. Output Path Design

Future runtime output path:

```text
output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.html
```

Artifact rules:

- HTML runtime artifacts stay out of git.
- HTML generation does not write default output.
- HTML generation does not write provider raw artifacts.
- HTML generation does not write evidence packs.
- HTML generation does not write fixtures.
- HTML generation does not write regression expected files.
- HTML generation writes only when explicitly requested by the future renderer
  or report command.
- Before writing an HTML artifact, the content must pass a secret scan.
- The HTML must not contain real tokens, MCP URLs, local secret paths, `.env`
  paths, private connection strings, provider credentials, or raw local config
  paths.
- Source references should be sanitized relative artifact references.
- The artifact must include a visible `not_for_trading_advice` flag or
  equivalent statement.

## 4. HTML Information Architecture

HTML should present the report in three reading layers: first-level conclusion,
second-level evidence, and third-level technical appendix.

### Investment Manager Quick Read

Required elements:

- title: stock code + company name + `基本面研究报告 V1`;
- important statement / not-for-trading-advice notice;
- one-sentence conclusion;
- core opportunities;
- core risks;
- largest evidence gap;
- data-quality state.

The quick read should make the most important conclusion easy to find, but it
must not hide caveats. If evidence is weak, candidate-level, or missing, that
state must appear in the quick-read area.

### Research Body

Required sections:

- analyst judgement;
- data-quality explanation;
- macro and industry logic;
- company fundamentals;
- opportunity analysis;
- risk analysis;
- evidence gaps;
- rebuttal conditions;
- follow-up checklist.

The body should preserve the Markdown section order unless the future renderer
has an explicit profile-aware mapping from accepted Markdown headings to stable
HTML slots. Even then, the renderer must not rewrite conclusions.

### Technical Appendix

Required sections:

- presentation profile metadata;
- evidence label definitions;
- source artifact references;
- data-quality caveats;
- `not_for_trading_advice` flag.

The technical appendix can be visually secondary, but it must remain discoverable
and readable. Data-quality caveats may be collapsible, but their existence and
status must remain visible.

## 5. Visual and Interaction Design

Recommended visual structure:

- Use a clear card-based layout for repeated items such as opportunities,
  risks, evidence gaps, rebuttal conditions, and follow-up variables.
- Place first-level information before evidence details and technical notes.
- Show opportunities, risks, and evidence gaps in separate groups.
- Use checklist styling for follow-up variables.
- Display evidence labels as badges or small labels near each judgement.
- Keep data-quality caveats visible; collapsible detail is allowed only when a
  non-collapsed summary still states the caveat.
- Use restrained colors that indicate category, evidence state, and urgency
  without implying trading direction.
- Do not use red / green buy-sell visual language.
- Do not use large `买入`, `卖出`, `强烈推荐`, or similar investment-action
  styling.
- Do not use visual ranking that implies certainty of upside, certainty of
  realization, or execution urgency.

Suggested card groups:

- quick-read summary cards: judgement, opportunity, risk, evidence gap, data
  quality;
- evidence cards: label, supporting artifacts, caveats, follow-up variables;
- risk cards: condition, evidence label, monitoring variable;
- follow-up checklist: variable, reason, current evidence state;
- appendix cards: profile metadata, source refs, caveat inventory.

## 6. Profile-Aware Display

HTML must preserve profile-aware display capability.

Accepted first profiles:

- `600406` / `stable_growth_grid_equipment`: grid equipment, digital grid,
  power automation, relay protection, State Grid / China Southern Power Grid,
  UHV, distribution-grid language.
- `002371` / `semiconductor_equipment_cycle`: semiconductor equipment,
  domestic substitution, wafer-fab capex, customer validation, delivery,
  acceptance, revenue confirmation, R&D, and inventory-cycle language.
- `002050` / `advanced_manufacturing_thermal_management`: thermal management,
  refrigeration control, new-energy vehicle thermal management, and
  new-business optionality language.

Profile rules:

- HTML must not mix industry language across profiles.
- HTML must not recompose industry copy outside the accepted Markdown renderer.
- HTML must not use `600406` grid wording for `002371` or `002050`.
- HTML must not use semiconductor equipment wording for `600406` or `002050`.
- HTML must not use thermal-management / new-energy-vehicle wording for
  `600406` or `002371`.
- Profile metadata may be displayed in the technical appendix.
- Profile metadata should not dominate the main reading view.
- When profile metadata is missing or unreliable, HTML should fall back to a
  neutral display shell and preserve the accepted Markdown text, rather than
  inventing industry-specific language.

## 7. Evidence Boundary

HTML must explicitly preserve the accepted evidence boundary.

Required statements or display behavior:

- A candidate is not a verified fact.
- A review decision is not fixture promotion.
- A P1.1 proxy is not an operating fact.
- Industry narrative is not company realization.
- Data-quality caveats must not be visually weakened into near-invisibility.
- Unsupported assumptions must remain displayed as to-be-verified assumptions.
- Forward tracking variables must remain displayed as monitoring items, not
  current evidence.

Evidence-label handling:

- `verified_fact` may be displayed as a reviewed fact only if the accepted
  report already labels it that way.
- `auto_accepted_candidate` must remain candidate-level evidence.
- `manual_review_required` must remain visible and cannot be collapsed away
  without a visible summary.
- `unsupported_assumption` must be visibly weaker than factual labels.
- `coverage_caveat` must remain visible wherever it constrains a judgement.
- `forward_tracking_variable` must be rendered as follow-up, not proof.

## 8. Prohibited Content

HTML must not contain investment-action language or trading signals, including:

- `买入`
- `卖出`
- `持有建议`
- `目标价`
- `仓位`
- `加仓`
- `减仓`
- `止损`
- `技术面交易信号`
- `确定性上涨`
- `必然兑现`
- `强烈推荐`

English equivalents are also prohibited in investment-action form, including:
`buy`, `sell`, `hold recommendation`, `target price`, `position sizing`,
`increase position`, `reduce position`, `stop loss`, `technical trading
signal`, `certain upside`, `inevitable realization`, and `strong recommend`.

Neutral explanatory text is allowed only when describing the prohibition itself
inside design docs, tests, or compliance messages.

## 9. Safety and Boundary Requirements

Renderer safety requirements:

- Escape HTML by default.
- Do not insert unsanitized raw HTML.
- Do not execute external JavaScript.
- Do not load external network resources.
- Do not load external fonts, CSS, images, scripts, trackers, analytics, or CDN
  resources.
- Prefer self-contained CSS and no JavaScript in V1; if JavaScript is later
  added for local interactions, it must be inline, deterministic, and
  non-networked.
- Do not leak local secret paths.
- Do not write tokens, MCP URLs, provider credentials, or local MCP config
  paths.
- Do not embed provider raw dumps.
- Do not embed long paid-source text.
- Do not expose absolute local paths unless a future local viewer explicitly
  needs them and they pass path-sanitization rules.
- Run a secret scan before writing an HTML runtime artifact.
- Treat Markdown text, structured payload fields, source refs, and profile
  metadata as untrusted strings for escaping purposes.

Content safety requirements:

- Keep `not_for_trading_advice=true` or equivalent visible.
- Preserve data-quality caveats.
- Preserve evidence labels.
- Preserve source-artifact trace without leaking sensitive local paths.
- Do not turn report presentation into an execution, portfolio, or trading
  assistant.

## 10. Future Implementation Suggestions

Suggested module:

```text
src/fundamental_skill/research_report/research_report_v1_html.py
```

Suggested public functions:

```python
render_research_report_v1_html(markdown: str, report: dict | None = None) -> str
write_research_report_v1_html(...)
```

Suggested implementation boundaries:

- The renderer accepts Markdown as required input.
- The optional report dict is display metadata only.
- The renderer has no provider imports.
- The writer has a strict path boundary under
  `output/research_reports/<timestamp>/<code>/`.
- The writer runs secret scanning before writing.
- The renderer does not access environment variables.
- The renderer does not access MCP config.
- The renderer does not make network calls.
- The renderer does not mutate input artifacts.

Suggested test coverage:

- HTML structure;
- visible not-for-trading-advice statement;
- three accepted profile samples;
- no cross-contamination between `600406`, `002371`, and `002050`;
- no investment-advice or trading-signal terms in rendered report content;
- caveats remain visible;
- evidence labels remain visible;
- HTML escaping;
- no external resources;
- secret scan;
- writer output boundary;
- no provider imports / calls;
- no environment-variable access;
- no network access;
- no MCP access;
- no writes to provider raw, evidence pack, fixtures, regression expected files,
  default output, or scoring / readiness artifacts.

## 11. Roadmap

Recommended sequence:

1. Complete this HTML design.
2. Implement HTML renderer.
3. Generate `600406` HTML.
4. Generate `002371` HTML.
5. Generate `002050` HTML.
6. Run three-sample HTML readability / UI acceptance.
7. Later evaluate Dashboard, batch reports, or live provider reports.

Do not move promote rules, validator implementation, fixture promotion,
official parser / CNInfo, live provider report, provider primary switch, or
AkShare / Tushare automatic merge ahead of HTML presentation validation.

## 12. Acceptance Checklist For This Design Stage

This design stage is accepted only if the work remains documentation-only:

- no code written;
- no tests changed;
- no fixtures changed;
- no pipeline changed;
- no scoring / readiness changed;
- no P1.1 changed;
- no regression expected files changed;
- no runtime output generated;
- no smoke test run;
- no token read;
- no network use;
- no Tushare or AkShare call;
- no MCP connection;
- no provider-primary switch;
- no automatic provider merge;
- no buy / sell advice, target price, position sizing, portfolio weight, or
  technical trading signal.

