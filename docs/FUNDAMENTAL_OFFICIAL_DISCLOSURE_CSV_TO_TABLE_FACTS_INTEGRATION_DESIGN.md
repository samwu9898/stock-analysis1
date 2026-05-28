# Fundamental Official Disclosure CSV To Table Facts Integration Design

Date: 2026-05-28

Stage: Fundamental Skill CSV Normalized Table To Business Composition Facts
Integration Design.

Status: documentation-only design. This stage does not implement code, change
tests, write fixtures, update accepted manifests, change orchestration or CLI,
change Research Report V1, connect candidate generation, change pipeline /
scoring / readiness / P1.1, change regression expected files, generate output,
read tokens, use the network, call CNInfo / Tushare / AkShare / provider
runtime, connect MCP, execute smoke tests, or provide investment advice.

Latest accepted verification results are quoted, not rerun here. The current
superseding runtime acceptance summary is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_CSV_TABLE_FACTS_RUNTIME_ACCEPTANCE_SUMMARY.md`:

- targeted tests `424 passed`
- full pytest latest `1072 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

Accepted prerequisite baseline:

- Business Composition Table Parser Design accepted.
- Table schema / quality model implementation accepted.
- Caveat-only hardening accepted.
- Local Structured CSV Reader implementation accepted.
- Delimiter warning patch accepted.
- Local structured CSV sample runtime review accepted.
- Retained runtime CSV sample:
  `output/official_disclosures/local_structured_table_samples/600406_h1_product.csv`
- Retained runtime review artifact:
  `output/official_disclosures/20260528_233015/600406/normalized_tables_review.json`
- CSV table fact converter implementation accepted.
- Strict Gate Patch accepted.
- Retained CSV sample -> table facts runtime review accepted.
- Retained CSV sample -> table facts runtime baseline frozen.
- Retained table facts runtime review artifact:
  `output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json`

## 1. Positioning

CSV normalized table -> table facts integration is an internal Business
Composition Table Parser conversion design.

It is not:

- candidate generator integration;
- Research Report V1 integration;
- official disclosure facts writer integration;
- fixture promotion;
- accepted manifest update;
- live CNInfo or provider work;
- a trading or investment advice system.

Its goals are to:

- read a normalized table representation produced by
  `local_structured_table_reader.py`;
- determine whether the table satisfies table quality, row / column alignment,
  unit, period, classification, denominator, and source-location gates;
- generate `business_composition_table_facts` when all required gates pass;
- generate `table_caveats` when the table is incomplete, ambiguous, caveat-only,
  or unsuitable for numeric extraction;
- remain fail-closed;
- avoid direct fixture writes;
- avoid accepted manifest changes;
- avoid Research Report V1 and candidate-generator side effects.

## 2. Input

The input is a normalized table payload, not a fact payload. Relevant fields
include:

- `headers`
- `rows`
- `source_document_id`
- `source_table_id`
- `source_section`
- `source_file_path`
- `detected_unit`
- `detected_period`
- `classification_hint`
- `reader_warnings`
- `table_quality_hint`

Input rules:

- normalized table output is not an L1 fact;
- normalized table output is not a table fact;
- normalized table output must pass the quality gate before any fact is built;
- `reader_warnings` must be preserved and propagated into table caveats or
  fact caveats;
- raw headers, raw row order, and raw string cells remain source evidence;
- reader hints are advisory and cannot bypass the business composition table
  validator.

## 3. Column Mapping Design

The converter should build a `source_column_map` before extracting any fact.

Required logical mappings:

- `segment_name`: official segment / product / industry / region name column;
- `revenue`: main business revenue column;
- `cost`: main business cost column;
- `gross_margin`: gross margin column;
- `revenue_yoy`: revenue year-on-year change column;
- `cost_yoy`: cost year-on-year change column;
- `gross_margin_yoy_change`: gross-margin change column;
- `denominator`: total-row or explicit denominator mapping.

Mapping rules:

- allow only explicit caller mapping or clear header allowlist match;
- do not guess columns from position alone;
- do not infer a missing revenue column from cost, margin, or ratio columns;
- key columns missing -> fail closed to `table_caveats`;
- duplicate or ambiguous header match -> fail closed unless explicit mapping
  resolves it;
- header synonym allowlists must be explicit, reviewed, and separately tested;
- unsupported columns may remain in normalized table but must not become facts;
- every emitted fact must carry the final `source_column_map`.

Initial header allowlist examples:

- segment: `产品名称`, `行业名称`, `地区名称`, `项目`, `类别`, `segment`,
  `product`, `industry`, `region`;
- revenue: `主营业务收入`, `营业收入`, `收入`, `revenue`;
- cost: `主营业务成本`, `营业成本`, `成本`, `cost`;
- gross margin: `毛利率`, `gross margin`;
- revenue yoy: `主营业务收入比上年同期增减`, `收入同比`, `revenue_yoy`;
- cost yoy: `主营业务成本比上年同期增减`, `成本同比`, `cost_yoy`;
- gross-margin yoy change: `毛利率比上年同期增减`, `毛利率同比变动`,
  `gross_margin_yoy_change`.

Any broader synonym set should be added in a later implementation stage with
focused tests.

## 4. Row Mapping Design

Row extraction rules:

- preserve the official segment name exactly as read;
- do not map segment names to strategy labels, investment themes, or internal
  classification labels;
- identify total rows such as `合计`, `总计`, `小计`, or explicit total labels
  separately from ordinary segment rows;
- retain original row order;
- retain `source_row_index` in every emitted fact;
- preserve `source_column_name` for every emitted value;
- blank rows, comment rows, duplicate header rows, or mixed table fragments must
  produce caveats;
- duplicate segment names must produce caveats unless an explicit row-selection
  policy resolves them;
- total row values may be used as denominator evidence only when the row is
  clearly identified and row length is stable.

The converter must not silently delete rows. It may skip rows from fact output
only with a caveat reason recorded.

## 5. Unit / Period / Denominator Rules

Amount facts:

- unit must be explicit before numeric amount facts are emitted;
- `detected_unit` may be used only when it is clear and unambiguous;
- if unit is unknown, do not emit numeric amount facts unless a future accepted
  explicit caveat policy allows it;
- CNY / RMB / 元 / 万元 / 亿元 must not be mixed or silently normalized without an
  accepted unit-normalization policy.

Period:

- period must be explicit before any numeric fact is emitted;
- `detected_period` may be used only when clear and unambiguous;
- if period is missing, do not emit numeric facts.

Denominator:

- denominator must be explicit for ratio fields;
- revenue ratio must not be generated when denominator is missing;
- denominator from a total row must identify the row label and the column used;
- denominator may be a caveated total row only when the caveat is carried into
  every affected fact.

Margin and percentage fields:

- gross margin should use directly disclosed table values only;
- do not calculate gross margin from revenue and cost unless a later design
  explicitly accepts calculation rules;
- distinguish percent (`%`) from percentage point changes;
- `减少2.93个百分点` and `-2.93%` are not equivalent and must not be silently
  rewritten.

## 6. Quality Gate

The converter must pass these gates before emitting table facts:

- header exists;
- row lengths stable;
- `classification_hint` or explicit `classification_type` exists;
- segment column exists;
- revenue column exists for revenue facts;
- unit exists for numeric amount facts;
- period exists;
- denominator exists or accepted caveat exists for relevant fields;
- total row check performed when available;
- `table_quality` is not caveat-only;
- `reader_warnings` reviewed and propagated.

Quality handling:

- `structured_high`: possible only with direct structured official source,
  stable rows, complete mapping, explicit unit / period / denominator, and no
  unresolved warnings.
- `structured_medium`: default for local CSV samples that are structured but
  still require human review.
- `partially_structured`: limited fields only, human review required, and no L1
  promotion without accepted policy.
- `unreliable_text_copy`: table caveats only; never `table_facts`.
- `unusable`: table caveats only; never `table_facts`.

If a table is caveat-only, the converter must emit `table_caveats`, not
`table_facts`.

## 7. Fact Output Design

Future converter implementation should use the existing
`build_table_fact(...)` schema.

Required fields:

- `field_path`
- `value`
- `unit`
- `period`
- `source_document_id`
- `source_section`
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

Default local CSV behavior:

- `needs_human_review=true`;
- `table_quality=structured_medium`;
- caveats include `local_structured_sample_requires_human_review`;
- `evidence_tier=L1_official_disclosure` may be used only as a candidate after
  source table id, row, column, source section, period, unit, and denominator
  are complete;
- do not generate verified facts;
- do not write fixtures;
- do not update reports;
- do not update accepted manifests.

## 8. Caveat Output Design

The converter should emit `table_caveats` for reader warnings, failed gates,
and table-quality restrictions.

Required caveat reasons include:

- `unit_not_detected`
- `period_not_detected`
- `row_length_unstable`
- `delimiter_sniffed`
- `denominator_missing`
- `total_check_missing`
- `ambiguous_header`
- `unsupported_column`
- `unreliable_text_copy`
- `unusable_table`

Propagation rules:

- reader warnings must not disappear;
- warnings that do not block extraction, such as `delimiter_sniffed`, should be
  carried as caveats for auditability;
- blocking warnings must prevent relevant facts from being emitted;
- if a fact is emitted despite a non-blocking caveat, the caveat must be
  present on the fact;
- caveat-only table qualities must be represented through table caveats only.

## 9. Relation To Current 600406 CSV Sample

Current retained runtime CSV sample:

```text
output/official_disclosures/local_structured_table_samples/600406_h1_product.csv
```

Current retained runtime review artifact:

```text
output/official_disclosures/20260528_233015/600406/normalized_tables_review.json
```

Observed sample result:

- headers = 7;
- rows = 6;
- `classification_hint=product`;
- `table_quality_hint=structured_medium`;
- `unit_not_detected`;
- `period_not_detected`;
- `delimiter_sniffed` visible;
- normalized table validation passed.

Runtime facts were generated only for review:

- `电网智能`;
- `数能融合`;
- `合计`.

Those facts remain human-review-only because unit and period were supplied by
runtime review context, not fully auto-detected from the CSV header. They are
not fixtures, not accepted manifest entries, not candidate generator output,
and not Research Report V1 facts.

## 10. Safety / Non-Goals

This design does not:

- read tokens;
- use the network;
- call CNInfo;
- call Tushare or AkShare;
- call provider runtime;
- connect MCP;
- write fixtures;
- update accepted manifests;
- integrate Research Report V1;
- integrate candidate generation;
- change scoring, readiness, P1.1, or regression expected files;
- generate output;
- provide trading advice.

## 11. Roadmap

Recommended sequence:

1. CSV to table facts integration design.
2. CSV to table facts converter implementation.
3. CSV sample runtime review with converter.
4. `official_disclosure_facts` integration design.
5. Candidate generator integration design.
6. Research Report V1 L1 evidence integration design.

Do not skip directly to live CNInfo, PDF extraction, DOCX reader, Excel reader,
candidate generator integration, Research Report V1 integration, fixture
promotion, or validator work. The converter implementation and retained sample
runtime review are now accepted; the next recommended stage is
`CSV table facts -> official_disclosure_facts integration design`.

## 12. CSV Table Facts Runtime Acceptance Addendum

CSV table fact converter implementation, Strict Gate Patch, and retained CSV
sample -> table facts runtime review are accepted. The frozen runtime
acceptance closeout is recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_CSV_TABLE_FACTS_RUNTIME_ACCEPTANCE_SUMMARY.md
```

Current retained input CSV:

```text
output/official_disclosures/local_structured_table_samples/600406_h1_product.csv
```

Current retained runtime review artifact:

```text
output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json
```

Accepted reader runtime baseline:

- headers = 7;
- rows = 6;
- raw strings preserved;
- `delimiter_sniffed`, `unit_not_detected`, and `period_not_detected` visible;
- `classification_hint=product`;
- `table_quality_hint=structured_medium`;
- reader did not generate table facts.

Accepted converter runtime baseline:

- explicit `period=2025H1`;
- explicit `unit=CNY`;
- explicit `denominator=主营业务收入合计`;
- explicit `classification_type=product`;
- `table_quality=structured_medium`;
- `needs_human_review=true`;
- generated 6 runtime-review-only revenue facts;
- includes `电网智能`, `数能融合`, and `合计`;
- preserves official segment names, source table id, row index, column name,
  column map, period, unit, classification type, denominator, table quality,
  human-review requirement, and caveat
  `local_structured_sample_requires_human_review`;
- propagates reader warnings into caveats or conversion warnings;
- generates no verified fact.

Accepted fail-closed checks include missing explicit period, missing explicit
unit, duplicate revenue-like header -> `ambiguous_header`, caveat-only
`unreliable_text_copy`, and denominator omission -> `denominator_missing`.

Boundaries remain unchanged:

- runtime-review-only table facts;
- no `official_disclosure_facts.json` integration yet;
- no accepted manifest update;
- no fixture promotion;
- no candidate generator integration;
- no Research Report V1 integration;
- no scoring / P1.1 / regression update;
- no live CNInfo, provider call, token read, network, MCP, or trading advice.

Next recommended stage:

```text
CSV table facts -> official_disclosure_facts integration design
```
