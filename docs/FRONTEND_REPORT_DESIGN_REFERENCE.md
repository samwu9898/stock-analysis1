# Frontend Report Design Reference

Date: 2026-05-19

Purpose: record visual direction for a future Dashboard or HTML renderer. This document is only a design reference. It does not change the current dashboard, evidence pack, AI prompt, AI report, deterministic pipeline, or data connectors.

## Design Goal

Future reports should feel like a polished, source-grounded fundamental research workspace:

- dense enough for serious analysis;
- readable enough for fast scanning;
- visually clear about evidence, uncertainty, and missing data;
- restrained, dark, and structured rather than decorative;
- optimized for source traceability and data-quality inspection.

The first screen should make the stock identity, strategy type, report status, confidence, key evidence gaps, and data freshness immediately visible.

## Borrowable Visual Patterns

| pattern | target use |
| --- | --- |
| Hero area | Show stock name, strategy type, report status, confidence, and latest analysis date with a compact but premium first impression. |
| Core conclusion cards | Summarize business quality, financial quality, valuation context, industry cycle, and data coverage. |
| Section cards | Group fundamental thesis, supporting evidence, limiting evidence, risks, and must-track indicators. |
| Top navigation | Let users jump between Overview, Evidence, Financials, Must-Track, Risks, and Source Trace. |
| Tags | Mark strategy type, confidence level, data status, source type, and missing-data severity. |
| Scoring bars | Show deterministic scores and confidence dimensions without implying action. |
| Dark theme | Use a calm dark base with restrained accent colors for status and source quality. |
| Styled tables | Improve scanability for financial metrics, must-track indicators, and coverage rows. |
| Evidence / Risk / Must-track cards | Make each evidence item auditable, with source, date, value, and interpretation boundary. |
| Source trace accordion | Collapse raw source functions, periods, fields, warnings, and known data limitations into audit panels. |
| Data quality panel | Separate available, partial, and missing fields, so report limits are visible without overwhelming the main narrative. |

## Non-Borrowable Patterns

Do not introduce visual or copy patterns that imply account execution, price objectives, position management, entry/exit timing, technical K-line analysis, return-ratio framing, or action-oriented market timing language.

The renderer should stay in the fundamental evidence domain:

- source-grounded observations;
- confidence and limitation disclosure;
- business, financial, valuation, cycle, and risk interpretation;
- must-track indicators as monitoring variables, not action instructions.

## Information Architecture

Recommended future page structure:

1. Hero

   Compact title area with stock code, stock name, strategy type, report status, confidence, fundamental score, analysis date, and key missing-data count.

2. Core Conclusion Band

   Five compact cards: business quality, financial quality, valuation interpretability, cycle context, data coverage. Each card should include status, one source-backed sentence, and one limitation if present.

3. Evidence Matrix

   Three columns or tabs: supporting evidence, limiting evidence, unknown or missing evidence. Each evidence item should show value, source, source date, affected dimension, and confidence effect.

4. Must-Track Indicators

   A sortable table with indicator name, current status, current value, priority, source, source date, reason, and follow-up question. Missing indicators should be visually clear but not visually punitive.

5. Financial And Segment Tables

   Financial metrics, valuation fields, business composition, and commodity-price context should use readable tables with consistent units and source dates.

6. Risk And Invalidation

   Card list for risk flags and invalidation conditions. Each item should show evidence source and monitor method.

7. Source Trace And Data Quality

   Collapsed audit panels for source functions, periods, fields, warnings, missing fields, and forbidden-term checks.

## Visual System

Suggested style:

- dark neutral background with one restrained accent family plus semantic status colors;
- small-radius cards and tables;
- compact typography with clear hierarchy;
- avoid oversized marketing-style panels;
- use status tags and score bars sparingly;
- preserve source-date visibility near every evidence value;
- make missing data explicit through labels and muted states, not alarm-heavy styling.

## Component Notes

### Hero

The hero should not be a marketing banner. It should function as a report header: identity, status, confidence, and freshness. A subtle background texture or gradient is acceptable, but the text and status chips must stay readable.

### Core Conclusion Cards

Cards should summarize current report state, not create new conclusions. Each card should map to an existing evidence-pack dimension or deterministic result field.

### Tables

Tables should support:

- sticky header for long evidence tables;
- compact numeric alignment;
- unit display;
- source and source-date columns;
- row status labels for available / partial / missing.

### Source Trace Accordion

This should be the audit layer for advanced users. Keep raw source detail accessible but collapsed by default.

### Data Quality

Data quality should be surfaced early. A report with missing fields can still look polished, as long as the UI makes the boundaries visible and honest.

## Safety Boundaries

Future UI work must preserve these boundaries:

- no account integration;
- no technical-indicator module;
- no action-oriented language;
- no price-objective module;
- no position-management module;
- no hidden conversion from evidence gaps into stronger report claims.

## Implementation Timing

This is not the next priority. The current priority remains evidence-pack field coverage. Frontend work should resume only after the next data-field pass improves the must-have indicator coverage that currently limits AI report quality.
