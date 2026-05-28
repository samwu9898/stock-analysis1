# Fundamental Official Disclosure Business Composition Table Schema Acceptance Summary

Date: 2026-05-28

Stage: Fundamental Skill Business Composition Table Schema / Quality Model
Acceptance Summary.

Status: documentation-only closeout. The table schema / quality model
implementation is accepted, the caveat-only hardening patch is accepted, and
the schema / quality model baseline is frozen. This summary does not change
code, tests, fixtures, accepted manifests, orchestration, CLI behavior,
Research Report V1, candidate generation, review decisions, pipeline, scoring,
Research Intelligence P1.1, regression expected files, or runtime output.

Latest accepted verification results are quoted, not rerun here:

- targeted tests `350 passed`
- full pytest `998 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

## 1. Final Status

Business Composition Table Schema / Quality Model implementation is accepted.
The caveat-only hardening patch is accepted. The baseline is frozen.

Accepted boundaries:

- no reader implemented;
- no writer implemented;
- no HTML table reader implemented;
- no DOCX reader implemented;
- no PDF table extraction implemented;
- no CSV / Excel reader implemented;
- no candidate generator integration;
- no Research Report V1 integration.

## 2. Implemented Module

Accepted implementation files:

- `src/fundamental_skill/research_report/business_composition_table.py`
- `tests/test_business_composition_table.py`

Accepted core capabilities:

- `TABLE_QUALITY_VALUES`
- `CLASSIFICATION_TYPE_VALUES`
- `EVIDENCE_TIER_VALUES`
- `EXTRACTION_CONFIDENCE_VALUES`
- `get_table_quality_policy`
- `build_table_fact`
- `validate_table_fact`
- `build_business_composition_table_facts`
- `validate_business_composition_table_facts`
- `is_numeric_extraction_allowed`
- `build_table_caveat`
- `build_unreliable_text_copy_caveat`

The implementation is in-memory schema / validation only. It does not read
files, write output, call providers, use the network, connect MCP, or route
facts into any downstream report or candidate process.

## 3. Table Quality Model

Accepted `table_quality` values:

- `structured_high`
- `structured_medium`
- `partially_structured`
- `unreliable_text_copy`
- `unusable`

Quality policy:

- `structured_high` may allow structured numeric extraction when source table
  id, row / column location, unit, period, classification type, denominator,
  and source mapping are explicit. Human review is optional unless material.
- `structured_medium` may allow structured numeric extraction only with caveats
  and human review.
- `partially_structured` allows only limited fields that pass explicit checks;
  human review is required and candidate-generator eligibility is false by
  default.
- `unreliable_text_copy` is caveat-only.
- `unusable` is caveat-only.

Caveat-only quality is not allowed inside `table_facts`.

## 4. Caveat-Only Hardening

The accepted hardening rule is:

- `unreliable_text_copy` does not allow any table fact.
- `unusable` does not allow any table fact.
- A caveat-only table quality must be rejected even when `value` is
  nonnumeric, `None`, or section-detection text.
- Section detection must be represented through `table_caveats`, not
  `table_facts`.

Accepted caveat helpers can express:

- `business_composition_section_detected`
- `table_structure_unreliable_due_to_pdf_text_copy`
- `business_composition_table_unusable`

The accepted helper path is `build_table_caveat(...)` or
`build_unreliable_text_copy_caveat(...)`.

## 5. Table Fact Schema

Accepted table facts must include source and interpretation metadata,
including:

- `source_table_id`
- `source_row_index`
- `source_column_name`
- `source_column_map`
- `classification_type`
- `segment_name`
- `denominator`
- `table_quality`
- `evidence_tier`
- `extraction_confidence`
- `needs_human_review`
- `caveats`

Schema rules:

- L1 table facts must include `source_table_id` plus row / column location.
- L1 table facts must include unit, period, and classification type.
- If denominator is missing, a caveat is required.
- Secret-like data, token-like keys or values, Bearer strings, MCP URLs,
  `.env` paths, local secret paths, and trading-advice keys must fail closed.
- Forbidden recommendation keys remain rejected: `buy`, `sell`,
  `target_price`, `position`, and `portfolio_weight`.

## 6. Relation To Current TXT Sample

The current real local TXT sample remains a boundary sample:

```text
output/official_disclosures/local_real_samples/600406_2025_semiannual_report_real.txt
```

Accepted interpretation:

- The TXT can detect that business-composition sections exist.
- The TXT is copied or converted from PDF and does not preserve reliable table
  row / column structure.
- The TXT must not be used to extract revenue, cost, gross margin, revenue
  ratio, YoY, or segment values.
- If future numeric extraction is required, it must use a structured table
  source with explicit row / column alignment, unit, period, denominator, and
  source location.

## 7. Safety / Non-Goals

This accepted schema / quality model baseline does not:

- read tokens;
- use the network;
- call CNInfo;
- call Tushare or AkShare;
- call any provider;
- connect MCP;
- perform OCR;
- perform PDF table extraction;
- implement a DOCX reader;
- implement an HTML table reader;
- implement a CSV / Excel reader;
- write fixtures;
- update the accepted manifest;
- update Research Report V1;
- integrate the candidate generator;
- change scoring, readiness, P1.1, or regression expected files;
- provide trading advice.

## 8. Verification

Latest accepted verification results:

- targeted tests `350 passed`
- full pytest `998 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`
- static boundary passed
- no real output writes

These results are quoted from the implementation acceptance and caveat-only
hardening acceptance stages. They were not rerun in this documentation-only
summary stage.

## 9. Known Limitations

Known limitations:

- no actual table reader yet;
- no structured local table sample runtime review yet;
- no PDF table parsing;
- no DOCX table parsing;
- no HTML table parsing;
- no CSV / Excel reader;
- no candidate generator integration;
- no Research Report V1 integration.

## 10. Next Recommended Stage

Recommended next stage at schema acceptance time:

```text
Local Structured Table Reader Design
```

Recommended sequencing:

1. Design the local structured table reader before implementing extraction
   runtime.
2. Prefer CSV / Excel or local HTML table samples for the first structured
   path.
3. Treat DOCX table reading as an auxiliary path.
4. Keep PDF table extraction later and separately designed.
5. Keep live CNInfo later and separately designed.
6. Keep candidate generator integration later and separately accepted.
7. Keep Research Report V1 integration later and separately accepted.

The next stage should remain fail-closed, local-first, and separate from
provider calls, tokens, MCP, fixtures, accepted manifests, report generation,
candidate generation, scoring, P1.1, regression expected files, and trading
advice.

## 11. Local Structured Table Reader Design Sync

Local Structured Table Reader Design is now recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_LOCAL_STRUCTURED_TABLE_READER_DESIGN.md
```

That design keeps the table schema / quality model baseline unchanged:

- reader output is a normalized table representation, not a table fact;
- reader output must pass through the accepted table quality model;
- `unreliable_text_copy` and `unusable` remain caveat-only and cannot enter
  `table_facts`;
- no reader, writer, candidate generator integration, or Research Report V1
  integration is implemented by the design-only stage.

Updated recommended next stage:

```text
CSV Reader Schema / Implementation
```

The CSV implementation should be local-only, preserve raw headers and row
order, avoid silent numeric conversion, record delimiter / encoding caveats,
and remain separate from output writes, fixtures, accepted manifests,
candidate generation, Research Report V1, scoring, P1.1, regression expected
files, providers, tokens, network, MCP, and trading advice.
