# Fundamental Official Disclosure Business Composition Table Parser Design

Date: 2026-05-28

Stage: Fundamental Skill Official Disclosure Business Composition Table Parser
Design.

Status: parser design accepted. The follow-on table schema / quality model
implementation and caveat-only hardening patch are also accepted, and the
schema / quality model baseline is frozen. The acceptance summary is recorded
in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_SCHEMA_ACCEPTANCE_SUMMARY.md`.
No reader, writer, HTML / DOCX / PDF / CSV / Excel parser, candidate-generator
integration, or Research Report V1 integration is accepted yet.

Latest accepted verification results are quoted, not rerun here:

- targeted tests `350 passed`
- full pytest latest `998 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

## 1. Design Positioning

The business-composition table parser is an independent future module after the
minimal official disclosure text parser. It is not part of the current text
parser and must not weaken the current conservative behavior.

The table parser's goal is to extract business composition from structured or
semi-structured official table sources and eventually serve future table facts
inside `official_disclosure_facts.json`.

It should support:

- `L1_official_disclosure` candidates only when table source, row / column
  location, unit, denominator, period, and quality checks are explicit;
- official disclosure candidate generation in a later integration stage;
- source location, table index, row / column alignment, unit, denominator, and
  total-check records;
- caveats for unreliable tables instead of forced numeric extraction.

It is not:

- live CNInfo fetch;
- a Tushare or AkShare provider;
- an OCR system;
- a full PDF table parser;
- fixture promotion;
- a validator;
- Research Report V1 integration;
- candidate generator integration;
- Dashboard or Batch;
- an investment advice system.

## 2. Table Source Priority

Table sources should be evaluated in this priority order:

1. Official HTML table, if the source preserves real `<table>` row / column
   structure.
2. PDF table extraction, such as a future separately designed evaluation of
   `pdfplumber`, `camelot`, `tabula`, or another parser. This stage does not
   implement PDF extraction.
3. DOCX table, as an auxiliary source when a user locally converts a filing
   into Word while preserving table cells.
4. CSV / Excel structured table, when the user locally provides a structured
   export.
5. TXT copied from PDF, only for detecting that a business-composition section
   exists. TXT copied from PDF must not be used for structured numeric
   extraction.

Rules:

- TXT fallback may record `business_composition_section_detected` and caveats
  only.
- TXT fallback must not extract revenue, cost, gross margin, revenue ratio,
  YoY, or segment values.
- Word / DOCX can be an auxiliary local sample path, but it is not the primary
  path.
- PDF table extraction requires a separate implementation design.
- Live CNInfo and online discovery remain later work.

## 3. Business Composition Fields

Future table facts may represent these fields:

- `classification_type`: `industry`, `product`, `region`, or `other`
- `segment_name`
- `revenue`
- `revenue_unit`
- `cost`
- `cost_unit`
- `gross_margin`
- `revenue_yoy`
- `cost_yoy`
- `gross_margin_yoy_change`
- `revenue_ratio`
- `denominator` / total revenue scope
- `period`
- `currency`
- `source_document_id`
- `source_table_id`
- `source_row_index`
- `source_column_map`
- `evidence_tier`
- `extraction_confidence`
- `needs_human_review`
- `caveats`

Field interpretation rules:

- Segment names preserve official wording and are not mapped to strategy labels
  at parse time.
- Revenue ratio must explain its denominator, such as total operating revenue
  or main-business revenue total.
- Gross margin is direct-disclosure only unless a later accepted design permits
  derivation.
- YoY fields require a table header or source text that clearly defines the
  comparison basis.
- Currency and numeric unit must be explicit; values must not silently mix CNY,
  RMB ten-thousand yuan, RMB hundred-million yuan, percentages, and percentage
  points.

## 4. Table Quality Model

`table_quality` should be one of:

| table_quality | Structured numeric extraction | Human review | L1 candidate eligible | Candidate generator eligible | Required behavior |
| --- | --- | --- | --- | --- | --- |
| `structured_high` | Yes | Optional unless material | Yes | Later integration may allow | Row / column structure is complete, headers are clear, unit is clear, and totals can be checked. |
| `structured_medium` | Yes, with caveats | Yes | Possible after integration | Later integration may allow | Structure is mostly complete, but source location, unit, denominator, or total checks need caveats. |
| `partially_structured` | Limited fields only | Yes | Usually no unless accepted by a later policy | No by default | Some columns align, but one or more fields remain ambiguous; record only fields that pass checks. |
| `unreliable_text_copy` | No | Yes | No | No | Caveat-only. TXT copied from PDF or similar text order loss; record section detection through table caveats only. |
| `unusable` | No | Yes if retained | No | No | Caveat-only. Missing table structure, missing source location, broken rows, or obvious copy / OCR corruption; record failure reason through table caveats only. |

Quality assignment must happen before numeric extraction. If a table cannot be
graded at least `partially_structured`, the parser must fail closed and emit
caveats only.

## 5. Row / Column Alignment Checks

Before extracting structured numeric values, the table parser must pass all
required checks:

- Table header exists.
- At least one segment-name column is identified.
- At least one revenue column is identified.
- Unit is explicit.
- Period is explicit.
- `classification_type` is explicit.
- Row and column counts are stable.
- Each extracted row has a consistent numeric-column count.
- Revenue, cost, gross margin, ratio, and YoY columns do not conflict.
- A total row, when present, can be identified and checked.
- Total error is within an accepted tolerance.
- Denominator / total revenue scope can be explained.
- Multiple tables are not mixed into one row / column map.

Recommended source-location fields:

- `source_document_id`
- `source_section`
- `source_page_or_anchor`
- `source_table_id`
- `source_table_index`
- `source_row_index`
- `source_column_name`
- `source_column_map`

## 6. Caveat And Fail-Closed Rules

The parser must not extract structured numeric values when any of these
conditions apply:

- TXT copied from PDF has disordered rows or columns.
- Header is missing.
- Unit is missing.
- Period is missing.
- `classification_type` is missing.
- Revenue cannot be aligned with cost or gross margin columns.
- Totals clearly do not match.
- Cross-page tables break row / column continuity.
- OCR or copy corruption is suspected.
- Segment name cannot be located.
- Table interpretation requires human judgement but has no source location.

Allowed caveat output in these cases:

- `business_composition_section_detected`
- `table_structure_unreliable_due_to_pdf_text_copy`
- `business_composition_table_unusable`
- caveats explaining why extraction was blocked

Fail-closed means the module may preserve evidence that a relevant table region
exists, but it must not invent row / column alignment or numeric values.
After caveat-only hardening, `unreliable_text_copy` and `unusable` must not
enter `table_facts` at all, even when the value is nonnumeric, null, or section
detection text. They must be represented through `table_caveats`.

## 7. Official Disclosure Fact Schema Extension

Future `official_disclosure_facts.json` table facts may use this shape:

```json
{
  "fact_id": "fact_table_001_row_001",
  "field_path": "business_composition.product_segment.revenue",
  "value": 12224749159.44,
  "unit": "CNY",
  "period": "2025H1",
  "source_document_id": "doc_001",
  "source_section": "主营业务分产品情况",
  "source_page_or_anchor": "",
  "source_table_id": "table_001",
  "source_row_index": 1,
  "source_column_name": "主营业务收入",
  "source_column_map": {
    "segment_name": "产品名称",
    "revenue": "主营业务收入",
    "denominator": "合计行"
  },
  "classification_type": "product",
  "segment_name": "电网智能",
  "denominator": "主营业务收入合计",
  "evidence_tier": "L1_official_disclosure",
  "extraction_confidence": "medium",
  "needs_human_review": true,
  "table_quality": "structured_medium",
  "caveats": []
}
```

Schema rules:

- L1 table facts must include `source_table_id` and row / column location.
- Table facts do not automatically write fixtures.
- Table facts do not automatically update Research Report V1.
- Table facts do not automatically update the accepted manifest.
- Table facts do not automatically enter scoring / Research Intelligence P1.1.
- Table facts do not automatically enter the candidate generator until a
  separate integration design is accepted.

## 8. Relation To Current Real Local TXT Sample

The accepted real local filing sample is:

```text
output/official_disclosures/local_real_samples/600406_2025_semiannual_report_real.txt
```

The accepted runtime artifact is:

```text
output/official_disclosures/20260528T125521Z/600406/official_disclosure_facts.json
```

Recorded experience:

- Business-composition regions were detected, including by industry, product,
  and region sections.
- The TXT was copied or converted from PDF, so table structure is unreliable.
- Current accepted behavior is to not extract revenue, cost, gross margin,
  revenue ratio, YoY, or segment values from that TXT.
- A future table parser needs structured sources, such as HTML table, PDF table
  extraction output after separate design, DOCX table, CSV, or Excel.
- This TXT should be retained conceptually as a negative / boundary sample for
  `unreliable_text_copy`, not as a numeric-extraction fixture.

## 9. Relation To Candidate Generator And Research Report V1

Future table parser output can be written into `official_disclosure_facts.json`
after implementation and acceptance. It may later become input to the candidate
generator.

Required boundaries:

- Candidate generator integration requires a separate design.
- Research Report V1 integration requires a separate design.
- The table parser does not directly change reports.
- The table parser does not directly update accepted manifests.
- The table parser does not directly write fixtures.
- The table parser does not directly change provider primary behavior.
- The table parser does not directly change scoring, readiness, P1.1, or
  regression expected files.

## 10. Safety / Non-Goals

This stage does not:

- read tokens;
- use the network;
- call CNInfo;
- call Tushare or AkShare;
- call any provider;
- connect MCP;
- implement OCR;
- implement PDF extraction;
- write output;
- submit runtime artifacts;
- write fixtures;
- change scoring / P1.1 / regression;
- provide buy / sell advice, target prices, position sizing, portfolio weights,
  or technical trading signals.

## 11. Roadmap

Recommended sequence:

1. Business composition table parser design.
2. Table schema / quality model implementation.
3. DOCX / CSV / HTML local structured table reader design or implementation.
4. One structured local table sample runtime review.
5. Add table facts to `official_disclosure_facts.json`.
6. Candidate generator integration design.
7. Research Report V1 L1 evidence integration design.
8. Later PDF table extraction design.
9. Later live CNInfo / official disclosure discovery design.

Table schema / quality model implementation and caveat-only hardening are now
accepted and frozen. The next recommended stage is:

```text
Local Structured Table Reader Design
```

It should first design a local structured table reader, preferably starting
with CSV / Excel or local HTML table samples. DOCX table reading can remain an
auxiliary path. PDF table extraction, live CNInfo, candidate generator
integration, and Research Report V1 integration remain later separately
accepted stages.

## 12. Schema / Quality Model Acceptance Addendum

The accepted implementation is:

- `src/fundamental_skill/research_report/business_composition_table.py`
- `tests/test_business_composition_table.py`

Accepted capabilities:

- table quality constants and policy lookup;
- classification, evidence-tier, and extraction-confidence enums;
- table fact builder and validator;
- optional top-level in-memory payload builder and validator;
- numeric-extraction permission helper;
- machine-readable table caveat helpers;
- secret-like data and forbidden recommendation-key rejection;
- caveat-only hardening for `unreliable_text_copy` and `unusable`.

Accepted boundaries:

- no reader;
- no writer;
- no HTML / DOCX / PDF / CSV / Excel parser;
- no fixture write;
- no accepted manifest update;
- no candidate generator integration;
- no Research Report V1 integration;
- no provider call, network use, token read, MCP, OCR, PDF extraction, scoring
  change, P1.1 change, regression expected change, or trading advice.
