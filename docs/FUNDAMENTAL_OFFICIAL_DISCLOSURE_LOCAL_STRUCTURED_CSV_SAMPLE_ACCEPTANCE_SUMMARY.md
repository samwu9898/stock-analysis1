# Fundamental Official Disclosure Local Structured CSV Sample Acceptance Summary

Date: 2026-05-28

Stage: Fundamental Skill Local Structured CSV Runtime Cleanup + Acceptance
Summary.

Status: documentation-only acceptance closeout. This stage does not change
code, tests, fixtures, accepted manifests, orchestration, CLI behavior,
Research Report V1, candidate generation, review decisions, pipeline /
scoring / readiness, P1.1, regression expected files, or tracked output.

## Final Status

- Local Structured CSV Reader implementation accepted.
- Delimiter warning patch accepted.
- Local structured CSV sample runtime review accepted.
- Local structured CSV sample runtime baseline frozen.
- CSV table fact converter implementation accepted.
- Strict Gate Patch accepted.
- Retained CSV sample -> table facts runtime review accepted.
- Retained CSV sample -> table facts runtime baseline frozen.
- No Excel / HTML / DOCX / PDF reader implemented.
- No candidate generator integration.
- No Research Report V1 integration.
- No `official_disclosure_facts.json` integration yet.
- No accepted manifest update.
- No fixture promotion.

## CSV Sample Record

Runtime sample:

```text
output/official_disclosures/local_structured_table_samples/600406_h1_product.csv
```

Record:

- ignored runtime sample;
- not staged / not tracked;
- local structured sample;
- not live CNInfo;
- not provider output;
- not official full parser output;
- used only for reader / quality model runtime review.

## Runtime Review Artifact Record

Reader runtime artifact:

```text
output/official_disclosures/20260528_233015/600406/normalized_tables_review.json
```

Current table facts runtime artifact:

```text
output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json
```

Record:

- ignored runtime artifact;
- not a fixture;
- not regression expected;
- not accepted manifest update;
- not Research Report V1 update;
- not candidate generator output.

The table facts runtime artifact contains normalized table summary,
`table_facts`, `table_caveats`, `conversion_warnings`, validation summary, and
`not_for_trading_advice=true`.

## Runtime Result Summary

Accepted reader runtime observations:

- headers = 7;
- rows = 6;
- rows preserved as raw strings;
- `delimiter_sniffed` warning visible;
- `classification_hint=product`;
- `table_quality_hint=structured_medium`;
- `unit_not_detected`;
- `period_not_detected`;
- normalized table validation passed.

The reader-stage table facts experiment generated 3 runtime-review-only
revenue facts before the dedicated converter runtime review:

- `电网智能`;
- `数能融合`;
- `合计`.

All 3 runtime-review-only facts use:

- `structured_medium`;
- `needs_human_review=true`;
- `period=2025H1`;
- `classification_type=product`;
- `denominator=主营业务收入合计`;
- caveat `local_structured_sample_requires_human_review`.

The superseding retained CSV sample -> table facts converter runtime review
generated 6 runtime-review-only revenue facts with explicit review parameters:

- `period=2025H1`;
- `unit=CNY`;
- `denominator=主营业务收入合计`;
- `classification_type=product`;
- `table_quality=structured_medium`;
- `needs_human_review=true`.

Each accepted runtime-review-only converter fact preserves official segment
names, source table id, source row index, source column name,
`source_column_map`, period, unit, classification type, denominator, table
quality, human-review requirement, and caveat
`local_structured_sample_requires_human_review`. Reader warnings including
`delimiter_sniffed`, `unit_not_detected`, and `period_not_detected` are
propagated to caveats or conversion warnings. No verified fact was generated.

## Conservative Boundaries

- CSV reader output is a normalized table, not an L1 fact.
- Structured table facts are runtime review only.
- No fixture write.
- No accepted manifest update.
- No `official_disclosure_facts.json` integration yet.
- No Research Report V1 update.
- No candidate generator integration.
- Human review caveat required.
- `source_column_map`, row location, and column location required.
- `unreliable_text_copy` remains caveat-only.
- No numeric extraction from copied PDF TXT.

## Safety / Non-Goals

- No token read.
- No network.
- No CNInfo / Tushare / AkShare / provider call.
- No MCP.
- No Excel / HTML / DOCX / PDF reader.
- No OCR.
- No fixture or regression expected changes.
- No scoring / P1.1 changes.
- No trading advice.

## Verification

Latest accepted verification results are quoted from the implementation and
runtime review stages:

- targeted tests `424 passed`;
- full pytest latest `1072 passed, 1 skipped`;
- regression `passed=47 failed=0 total=47`;
- runtime artifact validation passed;
- token / secret / provider scan passed;
- artifact boundary passed;
- git tracked output remained empty.

This documentation-only cleanup stage did not rerun pytest or regression.

## Known Limitations

- Sample is local manually prepared CSV.
- Sample is not official raw table extraction.
- Unit and period were not auto-detected from CSV header.
- Facts are runtime-review-only.
- Unit and period were supplied explicitly during converter review.
- Current converter generates only revenue facts by default.
- No cost / gross margin / YoY facts accepted yet.
- No `official_disclosure_facts.json` integration yet.
- No Excel reader.
- No HTML table reader.
- No DOCX reader.
- No PDF table extraction.
- No candidate generator integration.
- No Research Report V1 integration.
- Long mixed-case source id / file name false-positive risk in the scanner
  should be considered in a later dedicated scanner-hardening stage, not here.

## Runtime Cleanup

Invalid / intermediate ignored runtime files removed during closeout:

- `output/official_disclosures/local_structured_table_samples/600406_2025H1_business_composition_product.csv`
- `output/official_disclosures/20260528_232908/600406/normalized_tables_review.json`

Retained baseline artifacts:

- `output/official_disclosures/local_structured_table_samples/600406_h1_product.csv`
- `output/official_disclosures/20260528_233015/600406/normalized_tables_review.json`

## Next Recommended Stage

Historical next stage at reader-runtime acceptance time:

```text
CSV normalized table -> business_composition_table_facts integration design
```

Alternative later stage:

```text
Local HTML table reader design
```

That historical preferred priority was `CSV normalized table ->
business_composition_table_facts integration design`.

That design, converter implementation, Strict Gate Patch, and retained CSV
sample -> table facts runtime review are now accepted. The current next
recommended stage is:

```text
CSV table facts -> official_disclosure_facts integration design
```

Do not directly enter:

- live CNInfo;
- PDF extraction;
- DOCX reader;
- Excel reader;
- candidate generator integration;
- Research Report V1 integration;
- fixture promotion;
- validator.

## CSV To Table Facts Integration Design Sync

The next-stage design is now recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_CSV_TO_TABLE_FACTS_INTEGRATION_DESIGN.md
```

Design scope:

- convert normalized CSV tables into `business_composition_table_facts` or
  `table_caveats`;
- remain inside the Business Composition Table Parser boundary;
- require explicit column mapping or reviewed header allowlists;
- preserve official segment names and source row / column locations;
- require unit, period, denominator, classification, and table quality gates;
- propagate `reader_warnings` into table caveats or fact caveats;
- keep local CSV facts `structured_medium` and human-review-only by default.

Still out of scope:

- fixture writes;
- accepted manifest updates;
- official disclosure facts writer integration;
- candidate generator integration;
- Research Report V1 integration;
- live CNInfo / provider calls;
- Excel / HTML / DOCX / PDF readers.

## CSV Table Facts Runtime Acceptance Sync

The retained CSV sample -> table facts runtime acceptance closeout is now
recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_CSV_TABLE_FACTS_RUNTIME_ACCEPTANCE_SUMMARY.md
```

The accepted table facts runtime artifact is:

```text
output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json
```

The runtime baseline confirms:

- CSV table fact converter implementation accepted;
- Strict Gate Patch accepted;
- retained CSV sample -> table facts runtime review accepted;
- retained CSV sample -> table facts runtime baseline frozen;
- no candidate generator integration;
- no Research Report V1 integration;
- no `official_disclosure_facts.json` integration yet;
- no accepted manifest update;
- no fixture promotion.
