# Industry Framework Template

Date: 2026-05-20

Use this template when designing a new fundamental industry framework.

Core rules:

- Expand by business model, not by a single stock.
- Do not treat theme popularity as fundamental realization.
- Label proxies clearly; never present a proxy as a fact.
- Confidence means evidence confidence in the current `fundamental_view`; it does not mean positive strength.
- Do not output trading advice.
- Do not introduce technical analysis or technical indicators.
- Do not connect trading accounts.
- Do not implement `technical_skill` or `trader_skill`.

## 1. Framework Name

`<Human-readable framework name>`

Example:

- Satellite Communication Infrastructure
- Low Altitude Economy Infrastructure
- AI Data Center Infrastructure

## 2. strategy_type

`<snake_case_strategy_type>`

Naming guidance:

- Name the durable business model.
- Avoid stock names, ticker codes, slogans, and temporary market themes.
- Keep the value stable enough for regression fixtures.

## 3. Definition

Define the framework in one to three paragraphs.

Include:

- What the company monetizes.
- What assets, licenses, resources, capabilities, or customer contracts drive economics.
- Why this deserves a distinct fundamental framework.

Avoid:

- "Company X is this framework."
- "Stocks related to a popular theme."
- Definitions based only on news mentions, policy wording, or market attention.

## 4. Business Model Boundary

Describe the business model that should be included.

Include:

- Revenue source.
- Asset / resource base.
- Customer type.
- Contract model.
- Operating cycle.
- Margin and cash-flow drivers.

Explicitly state what is outside the boundary.

## 5. Positive Classification Signals

List signals that support classification into this framework.

Preferred signal hierarchy:

- Main business description.
- Business composition / revenue by segment.
- Product or service revenue tied to the framework.
- Assets, licenses, capacity, or operating resources.
- Customer contracts and contract duration.
- Cash-flow or margin evidence linked to the framework.

Do not use theme mentions alone as positive classification evidence.

## 6. Negative / Exclusion Signals

List signals that should exclude or demote the framework.

Examples:

- Main revenue comes from adjacent equipment or components.
- The company is a software, chip, materials, system-integration, or manufacturing supplier rather than an operator of the target business model.
- The evidence is only policy exposure, press releases, investor relations wording, or news keywords.
- Revenue contribution is tiny, unverified, or unrelated to the framework economics.
- The company has no disclosed assets, contracts, customers, or segment revenue tied to the framework.

## 7. Positive Samples

List candidate positive samples.

For each sample, include:

- Code / name.
- Why it fits the business model.
- Evidence source expected in current data.
- Whether it should be a v1 regression fixture.

Template:

```text
- <code> <name>: <business-model reason>; expected evidence: <fields>; regression: yes/no.
```

## 8. Negative Samples

List close negative samples that could be misclassified.

For each sample, include:

- Code / name.
- Why it is close to the theme.
- Why it should not classify into this framework.
- Whether it should be a v1 regression fixture.

Template:

```text
- <code> <name>: close because <reason>; exclude because <business-model reason>; regression: yes/no.
```

## 9. Required Data

Required data must be realistic and available in the current deterministic pipeline.

Use required fields only when absence should materially prevent a reliable `fundamental_view`.

Template:

```text
- basic_info: required for main business and industry context.
- business_composition: required/preferred because <reason>.
- revenue / profit / gross_margin: required because <reason>.
- operating_cashflow: required/preferred because <reason>.
```

## 10. Preferred Data

Preferred data improves confidence but should not necessarily block classification.

Examples:

- Segment revenue detail.
- Customer mix.
- Contract duration.
- Capacity / utilization.
- Asset age or remaining life.
- Order backlog or contract liabilities.
- Capex plan.

## 11. Optional Data

Optional data is useful for interpretation but may be unavailable, unstable, or too manual for v1.

Examples:

- Peer-specific operating indicators.
- Detailed customer concentration.
- Project-level economics.
- International peer valuation fields.
- Management commentary that is hard to normalize.

## 12. Confidence-Gating Indicators

List indicators that should cap confidence when missing.

Important:

- Confidence is evidence confidence in the current `fundamental_view`.
- Confidence is not a positive / negative score.
- Missing key operating indicators should keep confidence conservative even when classification is correct.

Template:

```text
- <indicator>: if missing, confidence cannot exceed <low/medium>; reason: <why>.
```

## 13. Interpretation Guards

Interpretation guards prevent over-reading weak evidence.

Include rules such as:

- Policy support is not the same as realized revenue.
- Contract liabilities may be an order-visibility proxy, not confirmed backlog.
- Segment revenue must be separated from group-level revenue when possible.
- Announced projects are not capacity utilization.
- Theme keywords are not proof of business-model fit.
- Proxy fields must be labeled as proxy in evidence pack and AI report.

## 14. Risk Guards

Risk guards should identify framework-specific risks and false-positive risks.

Examples:

- Theme-only evidence guard.
- Proxy-as-fact guard.
- Customer concentration guard.
- Receivables / cash-conversion guard.
- Capex / depreciation pressure guard.
- Policy dependency guard.
- Business-model mismatch guard.
- Data insufficiency guard.

Risk guards should not become optimistic scoring boosts.

## 15. Must-Track Indicators

List indicators a professional analyst must track for this framework.

Include:

- Core operating drivers.
- Demand drivers.
- Pricing / margin drivers.
- Cash-flow and balance-sheet drivers.
- Capex and asset lifecycle drivers.
- Framework-specific risk indicators.
- Valuation fields only when they are already part of the fundamental framework and not used for trading advice.

## 16. Readiness / Confidence Rules

Define how readiness and confidence should behave.

Template:

```text
- `insufficient_data`: use when <conditions>.
- `neutral`: use when core classification is supported but key operating indicators are incomplete.
- `low` confidence: use when classification is plausible but evidence is limited.
- `medium` confidence: use when required data and several preferred indicators are present.
- `high` confidence: use only when the framework has strong, direct, current, and multi-field evidence.
```

State explicit caps:

- If only theme/news evidence exists, confidence remains `low` or classification remains `theme_only`.
- If business model is correct but key operating indicators are missing, confidence should not be upgraded aggressively.
- If proxy evidence is used, confidence must reflect proxy limitations.

## 17. Scoring Notes

Describe what may affect scoring in v1.

Include:

- Which fields may enter scoring.
- Which fields are interpretation-only.
- Which fields are deferred until stable.
- Which missing fields should cap confidence instead of creating a negative score.

Avoid:

- Unapproved proxy scoring.
- Theme heat scoring.
- Technical indicators.
- Trading timing logic.

## 18. Evidence Pack Requirements

Define what evidence pack fields must show.

Include:

- Classification evidence.
- Positive and negative signals.
- Required / preferred / optional data availability.
- Proxy labels.
- Missing indicators.
- Risk guard triggers.
- Must-track indicators.
- Source field names from the deterministic pipeline.

The evidence pack must support the AI report without inviting unsupported claims.

## 19. AI Report Requirements

Define report behavior.

The AI report must:

- State the framework classification and confidence conservatively.
- Explain the business model using available evidence.
- Separate facts, missing evidence, and proxies.
- Avoid treating theme popularity as fundamental realization.
- Avoid trading advice, target prices, position sizing, timing advice, and account actions.
- Avoid technical analysis and technical indicators.
- Mention key missing indicators when confidence is capped.
- Use professional must-track indicators for the framework.
- Preserve schema and safety requirements.

Optional quality guards:

- Garbled text guard.
- Forbidden trading phrase guard.
- Unsupported certainty guard.
- Proxy-as-fact guard.

## 20. Regression Test Plan

Define regression coverage before implementation.

Include:

- At least one positive sample when feasible.
- Close negative samples that share theme keywords but differ by business model.
- Existing framework samples likely to drift.
- Expected `strategy_type`, status, confidence, key risk flags, and must-track terms.
- Forbidden phrase checks for trading advice.
- AI schema / safety checks when AI output is involved.

Template:

```text
Positive:
- <code>: expected strategy_type=<type>, status=<status>, confidence=<confidence>.

Negative:
- <code>: expected strategy_type != <type>; reason=<boundary>.

Drift-sensitive existing samples:
- <code>: expected unchanged <fields>.
```

## 21. v1 Implementation Scope

List what will be implemented in v1.

Examples:

- Add `strategy_type` to schema.
- Add classifier rules using main business and segment evidence.
- Add exclusion rules.
- Add data readiness requirements.
- Add framework-specific must-track indicators.
- Add conservative confidence caps.
- Add evidence pack fields.
- Add AI report requirements.
- Add positive and negative regression fixtures.

Keep v1 narrow and traceable to design.

## 22. Deferred / Not-in-v1 Items

List items intentionally not implemented.

Examples:

- New external connector.
- Hard-to-source operating metrics.
- Peer valuation model.
- Detailed project-level scoring.
- Alternative data.
- Trading account integration.
- Technical analysis.
- `technical_skill`.
- `trader_skill`.

Explain whether each item is deferred because of data availability, scope control, uncertainty, or safety boundary.

## 23. Acceptance Criteria

The framework can be accepted only when:

- Target positive samples classify correctly.
- Close negative samples do not misclassify into the framework.
- Old regression samples do not drift unexpectedly.
- Confidence remains conservative when evidence is incomplete.
- Proxy evidence is labeled and not presented as fact.
- Risk guards trigger under theme-only, proxy-only, or data-insufficient conditions.
- Must-track indicators are framework-specific and professional.
- Evidence pack supports the AI report.
- AI report passes schema and safety checks.
- No trading advice is produced.
- No technical analysis is introduced.
- `pytest` passes when implementation changes code.
- Regression suite passes when implementation changes behavior or fixtures.

Documentation-only framework planning does not require pytest, but the final note should say tests were skipped because no code changed.
