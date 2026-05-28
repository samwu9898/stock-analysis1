# Fundamental Official Disclosure Local Structured Table Reader Design

Date: 2026-05-28

Stage: Fundamental Skill Local Structured Table Reader Design.

Status: documentation-only design. This stage does not implement code, change
tests, change fixtures, change accepted manifests, change orchestration, change
CLI behavior, change Research Report V1, change candidate generation, change
review decisions, change pipeline / scoring / Research Intelligence P1.1,
change regression expected files, generate output, submit runtime artifacts,
run smoke tests, read `TUSHARE_TOKEN`, use the network, call CNInfo, call
Tushare or AkShare, call any provider, connect MCP, or provide investment
advice.

Latest accepted verification results are quoted, not rerun here:

- targeted tests `350 passed`
- full pytest `998 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

Accepted prerequisite baseline:

- Minimal official disclosure parser local-file implementation accepted.
- Real local official filing sample runtime accepted.
- Business Composition Table Parser Design accepted.
- Table schema / quality model implementation accepted.
- Caveat-only hardening accepted.
- Table schema / quality model baseline frozen.
- Current `600406_2025_semiannual_report_real.txt` remains an
  `unreliable_text_copy` boundary sample.

## 1. Design Positioning

The local structured table reader is the input-reading layer for the Business
Composition Table Parser. It is not the table fact validator itself.

Its goals are to:

- read user-provided local structured or semi-structured table files;
- produce a unified normalized table representation;
- preserve source location, row index, column names, unit hints, period hints,
  and classification hints;
- pass normalized tables to the accepted table quality model;
- avoid direct table fact writes unless a later implementation stage explicitly
  designs that behavior;
- avoid direct candidate generator integration;
- avoid direct Research Report V1 integration.

It is not:

- live CNInfo;
- a provider;
- PDF OCR;
- full PDF table extraction;
- fixture promotion;
- a validator;
- Research Report integration;
- candidate generator integration;
- Dashboard or Batch;
- an investment advice system.

## 2. Reader Source Priority

V1 local structured reader source priority:

1. CSV / Excel structured export.
2. Local HTML table.
3. DOCX table.
4. Future PDF table extraction output.
5. TXT copied from PDF only as an `unreliable_text_copy` boundary, not a
   structured reader input.

Design implications:

- CSV / Excel is the best first implementation target because users can provide
  explicit rows, columns, headers, and values with minimal parser ambiguity.
- Local HTML table is the second preferred path when real `<table>` structure
  is preserved.
- DOCX table can be an auxiliary path for user-converted local samples, but it
  should not be treated as a flawless official source.
- PDF table extraction remains later work and must have a separate design.
- Live CNInfo remains later work and must have a separate design.
- TXT copied from PDF must not participate in numeric extraction.

## 3. Normalized Table Representation

Reader output should use a normalized in-memory table representation such as:

```json
{
  "source_document_id": "doc_001",
  "source_table_id": "table_001",
  "source_file_path": "",
  "source_format": "csv",
  "source_section": "主营业务分产品情况",
  "source_page_or_anchor": "",
  "table_title": "",
  "headers": [],
  "rows": [],
  "row_count": 0,
  "column_count": 0,
  "detected_unit": "",
  "detected_period": "",
  "classification_hint": "",
  "reader_warnings": [],
  "table_quality_hint": ""
}
```

Rules:

- Reader output is not an L1 table fact.
- Reader output must be evaluated by the table quality model before any table
  fact is built.
- Reader output must preserve original headers and row order.
- Reader output must not silently rewrite official segment names.
- Reader output must not silently infer unit, period, or denominator.
- `headers` and `rows` should preserve raw cell strings where possible.
- `reader_warnings` should carry machine-readable reasons for ambiguity.
- `table_quality_hint` is only a hint and cannot bypass quality assignment.

## 4. CSV / Excel Reader Design

### CSV

CSV should be the first local structured implementation path.

Design requirements:

- Support UTF-8 and UTF-8-SIG.
- Require the first row, or a caller-specified row, to be the header row.
- Preserve column names exactly as read.
- Preserve raw cell strings.
- Do not automatically convert all numeric-looking strings into numbers.
- Do not silently delete empty columns.
- Record delimiter and encoding caveats.
- Record warnings for duplicate headers, empty headers, ragged rows, and
  unexpectedly blank rows.
- Do not treat a CSV table as L1 until quality, unit, period, classification,
  denominator, and row / column alignment checks pass.

### Excel

Excel may be designed in the same implementation stage as CSV or deferred one
stage later.

Design requirements:

- Sheet selection must be explicit or carefully caveated.
- The default reader must not read every sheet as accepted input.
- The caller may specify a sheet name or index.
- Auto-selected sheet names must be recorded with a caveat.
- Do not depend on hidden formula recalculation.
- Preserve raw cell values as exposed by the workbook.
- Record merged-cell caveats.
- Record hidden-row, hidden-column, formula-only, and multiple-table warnings
  when detected.
- Do not treat workbook formatting as authoritative evidence for unit, period,
  or denominator.

## 5. Local HTML Table Reader Design

Local HTML table reading is the second preferred path when a filing or
structured export preserves actual `<table>` markup.

Design requirements:

- Read only local `.html` or `.htm` files.
- Do not use the network.
- Do not load external resources.
- Parse only `<table>` content.
- Assign each table a table index and stable `source_table_id`.
- Preserve header rows.
- Preserve row order and visible cell text.
- Record caveats when `rowspan` or `colspan` must be expanded.
- Do not execute JavaScript.
- Do not read remote URLs.
- Do not download external CSS, images, scripts, or fonts.
- Record warnings for missing headers, nested tables, multiple candidate
  business-composition tables, and table layout ambiguity.

## 6. DOCX Table Reader Design

DOCX table reading is an auxiliary path for user-converted local samples.

Design requirements:

- Read only local `.docx` files.
- Use only user-provided local conversions.
- Do not treat DOCX as the primary path.
- Record `source_origin=local_converted_from_official_pdf` or an equivalent
  caveat when the DOCX came from a PDF conversion.
- Preserve table index and table order.
- Record merged-cell caveats.
- Record warnings for split tables, repeated headers, missing headers, and
  conversion artifacts.
- Do not treat Word conversion output as a flawless official table.
- Require a future real-sample runtime review before DOCX is accepted as a
  numeric extraction source.

## 7. Quality Gate Relationship

Reader output must pass through the following gates before table facts can be
accepted:

- table quality assignment;
- row / column alignment checks;
- unit checks;
- period checks;
- classification type checks;
- denominator checks;
- total checks.

The reader does not directly decide L1 eligibility. It cannot bypass
`business_composition_table.py` table fact validation. It may preserve source
evidence and warnings, but table fact construction remains a separate accepted
schema / quality model responsibility.

## 8. Fail-Closed Rules

The reader must not generate structured table facts when any of these
conditions apply:

- header missing;
- row length unstable;
- unit unknown;
- period unknown;
- classification unknown;
- segment column missing;
- revenue column missing;
- merged cells unresolved;
- `rowspan` / `colspan` ambiguous;
- formula-only value;
- multiple tables mixed;
- external resource dependency;
- text copied from PDF;
- parser confidence low.

Allowed output in those cases:

- normalized table warnings;
- table caveats;
- `business_composition_section_detected`;
- `table_structure_unreliable_due_to_pdf_text_copy`;
- `business_composition_table_unusable`.

`unreliable_text_copy` and `unusable` remain caveat-only and must not enter
`table_facts`.

## 9. Artifact Design

Two future artifact options are available.

### Option A: Standalone Normalized Tables Artifact

Future optional path:

```text
output/official_disclosures/<timestamp>/<code>/normalized_tables.json
```

Pros:

- keeps reader output separate from accepted fact output;
- supports runtime review of source-table normalization before fact extraction;
- makes table-reader debugging easier;
- avoids bloating `official_disclosure_facts.json` before the table fact schema
  integration is accepted.

Cons:

- adds one more runtime artifact;
- requires explicit linkage from future facts to normalized table records.

### Option B: Embed Source Tables In Official Disclosure Facts

Future conceptual shape:

- `official_disclosure_facts.json.source_tables`
- `official_disclosure_facts.json.table_caveats`

Pros:

- keeps document facts and table evidence in one payload;
- easier to bundle source tables with emitted table facts.

Cons:

- risks mixing reader diagnostics with accepted facts too early;
- can encourage downstream consumers to treat normalized tables as facts;
- increases payload size and validation surface.

### V1 Recommendation

V1 should prefer Option A: standalone ignored runtime artifact
`normalized_tables.json` for reader runtime review. After reader behavior is
accepted, a later integration design can decide whether selected normalized
table metadata should be embedded as `source_tables` inside
`official_disclosure_facts.json`.

Artifact boundary:

- runtime artifact remains ignored;
- not a fixture;
- not regression expected;
- does not update accepted manifest;
- does not directly change reports;
- does not enter candidate generator or Research Report V1.

## 10. Safety / Non-Goals

This design does not:

- read tokens;
- use the network;
- call CNInfo;
- call Tushare or AkShare;
- call any provider;
- connect MCP;
- execute JavaScript;
- load external resources;
- perform OCR;
- perform PDF table extraction;
- write output in this design stage;
- write fixtures;
- change scoring, readiness, P1.1, or regression expected files;
- integrate the candidate generator;
- integrate Research Report V1;
- provide trading advice.

## 11. Roadmap

Recommended sequence:

1. Local Structured Table Reader Design.
2. CSV reader schema / implementation.
3. One local CSV structured sample runtime review.
4. Local HTML table reader design / implementation.
5. DOCX table reader design / implementation.
6. Table quality integration runtime review.
7. Add table facts to `official_disclosure_facts.json`.
8. Candidate generator integration design.
9. Research Report V1 L1 evidence integration design.
10. Later PDF table extraction design.
11. Later live CNInfo / official disclosure discovery design.

The next implementation stage should be CSV reader schema / implementation.
It should remain local-only, fail-closed, and separate from providers, tokens,
MCP, fixtures, accepted manifests, candidate generation, Research Report V1,
scoring, P1.1, regression expected files, and trading advice.

## 12. CSV Implementation And Runtime Acceptance Addendum

Local Structured CSV Reader implementation, delimiter warning patch, and local
structured CSV sample runtime review are now accepted. The runtime baseline is
frozen and summarized in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_LOCAL_STRUCTURED_CSV_SAMPLE_ACCEPTANCE_SUMMARY.md
```

Accepted runtime baseline artifacts remain ignored output:

- `output/official_disclosures/local_structured_table_samples/600406_h1_product.csv`
- `output/official_disclosures/20260528_233015/600406/normalized_tables_review.json`

Runtime review result:

- headers = 7;
- rows = 6;
- raw string cells preserved;
- `delimiter_sniffed` warning visible;
- `classification_hint=product`;
- `table_quality_hint=structured_medium`;
- `unit_not_detected`;
- `period_not_detected`;
- normalized table validation passed;
- 3 runtime-review-only revenue facts were validated with
  `structured_medium`, `needs_human_review=true`, `period=2025H1`,
  `classification_type=product`, `denominator=主营业务收入合计`, and caveat
  `local_structured_sample_requires_human_review`.

Boundaries remain unchanged:

- no Excel / HTML / DOCX / PDF reader;
- no OCR;
- no candidate generator integration;
- no Research Report V1 integration;
- no fixture write;
- no accepted manifest update;
- no regression expected update;
- no live CNInfo, provider call, token read, network, MCP, or trading advice.

Historical next recommended stage after CSV reader acceptance:

```text
CSV normalized table -> business_composition_table_facts integration design
```

## 13. CSV To Table Facts Integration Design Sync

The CSV normalized table -> business composition table facts integration design
is now recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_CSV_TO_TABLE_FACTS_INTEGRATION_DESIGN.md
```

This design keeps the reader boundary intact:

- reader output remains a normalized table, not an L1 fact;
- reader warnings must be propagated into table caveats or fact caveats;
- delimiter inference remains visible through `delimiter_sniffed`;
- conversion requires explicit column mapping or reviewed header allowlists;
- conversion requires row / column location, unit, period, classification, and
  denominator gates;
- `unreliable_text_copy` and `unusable` remain caveat-only;
- no candidate generator or Research Report V1 integration is included.

Historical next recommended stage after the integration design:

```text
CSV to table facts converter implementation
```

## 14. CSV Table Facts Runtime Acceptance Sync

CSV table fact converter implementation, Strict Gate Patch, and retained CSV
sample -> table facts runtime review are now accepted. The frozen runtime
acceptance closeout is recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_CSV_TABLE_FACTS_RUNTIME_ACCEPTANCE_SUMMARY.md
```

Retained input CSV:

```text
output/official_disclosures/local_structured_table_samples/600406_h1_product.csv
```

Retained table facts runtime artifact:

```text
output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json
```

Reader boundary remains intact:

- reader output is a normalized table, not a table fact;
- reader runtime observed headers = 7 and rows = 6;
- raw strings were preserved;
- `delimiter_sniffed`, `unit_not_detected`, and `period_not_detected` remained
  visible;
- `classification_hint=product`;
- `table_quality_hint=structured_medium`;
- reader did not generate table facts.

Converter runtime acceptance used explicit review parameters:

- `period=2025H1`;
- `unit=CNY`;
- `denominator=主营业务收入合计`;
- `classification_type=product`;
- `table_quality=structured_medium`;
- `needs_human_review=true`.

The converter generated 6 runtime-review-only revenue facts, including
`电网智能`, `数能融合`, and `合计`, with source table id, row index, column name,
`source_column_map`, period, unit, classification type, denominator,
`structured_medium`, `needs_human_review=true`, and caveat
`local_structured_sample_requires_human_review`. Reader warnings were
propagated to caveats or conversion warnings. No verified fact was generated.

The retained CSV sample and runtime artifact remain ignored output, not
fixtures, not regression expected files, not accepted manifest updates, not
Research Report V1 updates, and not candidate generator output.

Accepted fail-closed checks include missing explicit period, missing explicit
unit, duplicate revenue-like header -> `ambiguous_header`, caveat-only
`unreliable_text_copy`, and denominator omission -> `denominator_missing`.

Latest accepted verification results are quoted, not rerun here:

- targeted tests `424 passed`;
- full pytest latest `1072 passed, 1 skipped`;
- regression `passed=47 failed=0 total=47`.

Next recommended stage:

```text
CSV table facts -> official_disclosure_facts integration design
```
