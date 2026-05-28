# Fundamental Official Disclosure Table Facts To Official Disclosure Facts Integration Design

Date: 2026-05-29

Stage: Fundamental Skill CSV Table Facts To Official Disclosure Facts
Integration Design.

Status: documentation-only design. This stage designs how accepted CSV
`table_facts` / `table_caveats` should be assembled into
`official_disclosure_facts.json`. It does not implement code, change tests,
write fixtures, update accepted manifests, change orchestration or CLI, change
Research Report V1, connect candidate generation, change pipeline / scoring /
Research Intelligence P1.1, change regression expected files, generate output,
read tokens, use the network, call CNInfo / Tushare / AkShare / provider
runtime, connect MCP, execute smoke tests, or provide investment advice.

Latest accepted verification results are quoted, not rerun here:

- targeted tests `424 passed`
- full pytest latest `1072 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

Accepted prerequisite baseline:

- Minimal official disclosure parser local-file implementation accepted.
- Business Composition Table Parser Design accepted.
- Table schema / quality model implementation accepted.
- Caveat-only hardening accepted.
- Local Structured CSV Reader implementation accepted.
- CSV table fact converter implementation accepted.
- Retained CSV sample -> table facts runtime review accepted.
- Retained table facts runtime artifact:
  `output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json`

## 1. Positioning

CSV table facts -> `official_disclosure_facts.json` integration is an internal
official disclosure parser artifact-assembly design.

It is not:

- candidate generator integration;
- Research Report V1 integration;
- fixture promotion;
- accepted manifest update;
- live CNInfo or provider work;
- a validator implementation;
- a trading or investment advice system.

Its goals are to:

- incorporate validated `table_facts` and `table_caveats` into
  `official_disclosure_facts.json`;
- preserve source document, source table, row / column location, unit, period,
  denominator, table quality, and human-review caveats;
- keep `not_for_trading_advice=true`;
- remain fail-closed;
- generate no verified fact;
- write no fixture;
- update no accepted manifest;
- enter no Research Report V1 path.

Table facts remain caveated L1 official disclosure candidates. They are not
reviewed facts, not fixture promotion, not report-ready facts, and not
candidate-generator output.

## 2. Inputs

The integration input should include:

- existing `official_disclosure_facts` payload;
- `table_facts` from `csv_table_fact_converter.py`;
- `table_caveats`;
- `conversion_warnings`;
- normalized table summary;
- source document metadata.

Input rules:

- existing `official_disclosure_facts` must be valid before assembly;
- table facts must already have passed `validate_table_fact(...)`;
- table caveats and conversion warnings must be carried forward, not dropped;
- normalized table summary is evidence trace, not a fact;
- source document metadata must identify the document that the table belongs
  to;
- table facts do not become reviewed facts through assembly;
- candidate generator integration remains later work.

## 3. `official_disclosure_facts.json` Schema Extension

### Option A: Put Table Facts Only Into `extracted_facts[]`

Shape:

- append converted table facts directly into the existing
  `extracted_facts[]` list;
- encode table-specific metadata on each fact.

Pros:

- keeps one unified fact list;
- minimizes top-level schema growth;
- simple for future candidate generation to scan.

Cons:

- source table trace becomes duplicated across facts;
- table-level caveats have no natural home;
- normalized table metadata may be lost or forced into each fact.

### Option B: Add `source_tables[]`, `table_facts[]`, And `table_caveats[]`

Shape:

- add `source_tables[]` for table trace;
- add a separate top-level `table_facts[]`;
- add top-level `table_caveats[]`.

Pros:

- cleanly separates table evidence from text facts;
- avoids duplicating table metadata across facts;
- gives table-level caveats an explicit location.

Cons:

- creates a second fact list that downstream consumers might miss;
- future candidate generator would need two fact-entry paths;
- increases schema and validation surface before downstream integration is
  designed.

### Option C: Keep Standard Facts In `extracted_facts[]` And Add Table Trace

Shape:

- keep `extracted_facts[]` as the unified fact list;
- append table-derived facts to `extracted_facts[]`;
- add optional `source_tables[]` for normalized table trace;
- add optional top-level `table_caveats[]` for table-level warnings and failed
  gates.

Pros:

- preserves one canonical fact list;
- keeps table trace without repeating full table metadata on every fact;
- gives table-level caveats a stable home;
- future candidate generator can still read one fact list;
- Research Report V1 remains disconnected until a later accepted design.

Cons:

- requires careful references from facts to `source_tables[]`;
- source table validation becomes part of the official-disclosure artifact
  validator;
- row storage policy must be explicit to avoid large artifacts.

### V1 Recommendation

Use Option C.

V1 schema extension:

```json
{
  "version": "official_disclosure_facts.v1",
  "source_documents": [],
  "source_tables": [],
  "extracted_facts": [],
  "table_caveats": [],
  "extraction_warnings": [],
  "data_quality_caveats": [],
  "not_for_trading_advice": true
}
```

V1 rules:

- `extracted_facts[]` remains the unified fact list;
- table facts use the `business_composition.*` namespace in `field_path`;
- `source_tables[]` stores normalized table trace;
- `table_caveats[]` stores table-level caveats, failed gates, and propagated
  warnings;
- `not_for_trading_advice=true` remains mandatory;
- no table fact is upgraded to `verified_fact`.

Recommended `field_path` namespace examples:

- `business_composition.revenue`
- `business_composition.cost`
- `business_composition.gross_margin`
- `business_composition.revenue_yoy`
- `business_composition.cost_yoy`
- `business_composition.gross_margin_yoy_change`

V1 implementation should accept only revenue facts by default because the
current converter runtime baseline accepted only revenue facts. Cost, gross
margin, and YoY fields remain later accepted-expansion work.

## 4. Required Fields For Table Facts

Every table-derived fact appended to `extracted_facts[]` must preserve:

- `fact_id`
- `field_path`
- `value`
- `unit`
- `period`
- `source_document_id`
- `source_section`
- `source_page_or_anchor`
- `source_table_id`
- `source_row_index`
- `source_column_name`
- `source_column_map`
- `classification_type`
- `segment_name`
- `denominator`
- `evidence_tier`
- `extraction_confidence`
- `needs_human_review`
- `table_quality`
- `caveats`

Required semantics:

- `evidence_tier=L1_official_disclosure` remains a candidate label, not a
  reviewed-fact label;
- `needs_human_review=true` remains the default for local structured CSV table
  facts;
- caveat `local_structured_sample_requires_human_review` must be preserved;
- reader / converter warnings such as `delimiter_sniffed`,
  `unit_not_detected`, and `period_not_detected` must remain traceable through
  fact caveats, table caveats, or conversion warnings;
- no fact may carry `verified_fact=true`, `review_status=verified`, or any
  equivalent verified marker in V1.

Suggested table fact shape inside `extracted_facts[]`:

```json
{
  "fact_id": "table_fact_001",
  "field_path": "business_composition.revenue",
  "value": "123.45",
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
    "revenue": "主营业务收入"
  },
  "classification_type": "product",
  "segment_name": "电网智能",
  "denominator": "主营业务收入合计",
  "evidence_tier": "L1_official_disclosure",
  "extraction_confidence": "medium",
  "needs_human_review": true,
  "table_quality": "structured_medium",
  "caveats": [
    "local_structured_sample_requires_human_review",
    "delimiter_sniffed",
    "unit_not_detected",
    "period_not_detected"
  ]
}
```

## 5. Source Table Trace

`source_tables[]` should preserve enough normalized-table trace to audit table
facts without forcing downstream consumers to treat the entire table as facts.

Required fields:

- `source_table_id`
- `source_document_id`
- `source_format`
- `source_file_path`
- `source_section`
- `table_title`
- `headers`
- `row_count`
- `column_count`
- `detected_unit`
- `detected_period`
- `classification_hint`
- `reader_warnings`
- `table_quality_hint`
- `table_quality_final`
- `source_hash` if available
- `caveats`

Suggested shape:

```json
{
  "source_table_id": "table_001",
  "source_document_id": "doc_001",
  "source_format": "csv",
  "source_file_path": "output/official_disclosures/local_structured_table_samples/600406_h1_product.csv",
  "source_section": "主营业务分产品情况",
  "table_title": "",
  "headers": ["产品名称", "主营业务收入"],
  "row_count": 6,
  "column_count": 7,
  "detected_unit": "",
  "detected_period": "",
  "classification_hint": "product",
  "reader_warnings": ["delimiter_sniffed", "unit_not_detected", "period_not_detected"],
  "table_quality_hint": "structured_medium",
  "table_quality_final": "structured_medium",
  "source_hash": "",
  "caveats": ["local_structured_sample_requires_human_review"]
}
```

Row storage policy:

- V1 may omit full `rows` to avoid large artifacts;
- if rows are stored, they must remain in ignored runtime artifacts only;
- row storage must preserve raw strings and must not normalize away source
  evidence;
- row storage must pass the same secret / URL / cookie / recommendation-key
  scan as facts;
- rows must not be promoted into fixtures without a later sanitized-fixture
  design.

Security boundary:

- `source_file_path` must be repo-relative or otherwise sanitized;
- no token, secret, Bearer string, MCP URL, `.env` path, local secret path,
  cookie, or private credential may appear in `source_tables[]`;
- `source_tables[]` is trace metadata, not a candidate generator result.

## 6. Caveat Propagation

Required propagation rules:

- reader warnings -> `table_caveats[]` and, when relevant, fact `caveats`;
- converter warnings -> `table_caveats[]` and, when relevant, fact `caveats`;
- `denominator_missing` -> `conversion_warnings` and fact `caveats` if
  revenue facts are still allowed by explicit policy;
- `unit_not_detected` -> fail closed unless explicit unit override exists; if
  override exists, preserve the caveat;
- `period_not_detected` -> fail closed unless explicit period override exists;
  if override exists, preserve the caveat;
- `delimiter_sniffed` -> trace caveat, not a blocking caveat by itself;
- `local_structured_sample_requires_human_review` -> fact caveat;
- `table_quality=structured_medium` -> preserve human-review requirement and
  caveat;
- `table_quality=unreliable_text_copy` or `unusable` -> append no table facts;
  append only table caveats.

Suggested `table_caveats[]` item shape:

```json
{
  "caveat_id": "table_caveat_001",
  "source_document_id": "doc_001",
  "source_table_id": "table_001",
  "reason": "unit_not_detected",
  "severity": "review_required",
  "applies_to": ["business_composition.revenue"],
  "propagated_to_fact_ids": ["table_fact_001"],
  "details": "Unit was supplied explicitly during runtime review and remains human-review-required."
}
```

Caveat severity vocabulary for V1:

- `trace`: non-blocking trace caveat such as `delimiter_sniffed`;
- `review_required`: facts may exist but require human review;
- `blocking`: no relevant facts may be appended.

## 7. Merge / Append Behavior

V1 integration behavior:

- do not overwrite existing `extracted_facts[]`;
- append table facts with unique `fact_id`;
- `fact_id` collision must fail closed;
- `source_document_id` mismatch must fail closed;
- each table fact must reference an existing `source_documents[]` entry;
- each table fact must reference a present `source_table_id`;
- source table id duplicate behavior must be explicit;
- if the same `source_table_id` and same normalized table trace already exist,
  reuse the existing `source_tables[]` entry only when hashes or stable trace
  fields match;
- if the same `source_table_id` points to different trace metadata, fail
  closed;
- if table quality is caveat-only, append no facts;
- if only caveats exist, append `table_caveats[]` only;
- do not automatically dedupe across providers;
- do not change provider primary behavior;
- do not overwrite main-business text facts or periodic report basics;
- do not update `source_documents[]` except through explicit source-document
  metadata supplied to this integration stage.

Recommended `fact_id` strategy:

- table facts should use a stable prefix such as `table_fact_`;
- the id should be deterministic from source document id, source table id,
  field path, row index, column name, period, and classification type;
- source values should not be hashed with secrets or absolute private paths;
- id collision is a validation error, not a dedupe signal.

## 8. Validation Rules

Integration must validate:

- `official_disclosure_facts` payload is valid;
- `not_for_trading_advice=true`;
- all table facts pass `validate_table_fact(...)`;
- all table facts reference an existing `source_document_id`;
- all table facts include `source_table_id`;
- L1 facts include row and column location;
- `field_path` uses the allowed `business_composition.*` namespace;
- no table fact carries a verified-fact marker;
- table quality allows numeric extraction;
- caveat-only table qualities append no facts;
- all warnings are either propagated or explicitly represented in
  `table_caveats[]`;
- no token / secret / Bearer string / MCP URL / `.env` path / local secret path
  appears in facts, source tables, caveats, warnings, or metadata;
- no trading recommendation keys such as `buy`, `sell`, `target_price`,
  `position`, or `portfolio_weight`;
- no fixture write;
- no accepted manifest update.

Validation failure policy:

- fail closed before writing any assembled artifact;
- do not partially append table facts;
- return validation errors as runtime review data only;
- do not silently drop failed facts unless a table-level caveat records the
  failed gate;
- do not repair missing unit, period, denominator, or source mapping by
  guessing.

## 9. Relation To Current Runtime Sample

Current retained CSV sample:

```text
output/official_disclosures/local_structured_table_samples/600406_h1_product.csv
```

Reader runtime review artifact:

```text
output/official_disclosures/20260528_233015/600406/normalized_tables_review.json
```

CSV table facts runtime review artifact:

```text
output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json
```

Accepted runtime observations:

- the retained CSV sample is local structured CSV;
- reader observed headers = 7 and rows = 6;
- reader preserved raw strings;
- `delimiter_sniffed`, `unit_not_detected`, and `period_not_detected` were
  visible;
- converter review supplied `period=2025H1`, `unit=CNY`, and
  `denominator=主营业务收入合计`;
- 6 revenue facts were generated;
- facts include `电网智能`, `数能融合`, and `合计`;
- all facts use `table_quality=structured_medium`;
- all facts use `needs_human_review=true`;
- all facts retain caveat `local_structured_sample_requires_human_review`;
- no verified fact was generated;
- table facts are not integrated into `official_disclosure_facts.json` yet.

The current sample should be used for the later integration implementation
runtime review, still as ignored runtime output and not as a fixture.

## 10. Safety / Non-Goals

This design does not:

- read tokens;
- use the network;
- call CNInfo;
- call Tushare or AkShare;
- call provider runtime;
- connect MCP;
- run live fetch;
- run smoke tests;
- write fixtures;
- update accepted manifests;
- integrate Research Report V1;
- integrate candidate generation;
- change orchestration or CLI;
- change scoring, readiness, P1.1, or regression expected files;
- generate output;
- provide trading advice.

## 11. Roadmap

Recommended sequence:

1. Table facts -> `official_disclosure_facts` integration design.
2. Integration implementation.
3. Runtime review using retained CSV table facts artifact.
4. Candidate generator integration design.
5. Research Report V1 L1 evidence integration design.
6. Later live CNInfo / official discovery design.

Do not skip directly to live CNInfo, PDF extraction, DOCX / HTML / Excel
reader, candidate generator integration, Research Report V1 integration,
fixture promotion, accepted manifest update, validator work, scoring / P1.1
change, or trading-advice output.
