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
- No Excel / HTML / DOCX / PDF reader implemented.
- No candidate generator integration.
- No Research Report V1 integration.

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

Runtime artifact:

```text
output/official_disclosures/20260528_233015/600406/normalized_tables_review.json
```

Record:

- ignored runtime artifact;
- not a fixture;
- not regression expected;
- not accepted manifest update;
- not Research Report V1 update;
- not candidate generator output.

## Runtime Result Summary

Accepted runtime observations:

- headers = 7;
- rows = 6;
- rows preserved as raw strings;
- `delimiter_sniffed` warning visible;
- `classification_hint=product`;
- `table_quality_hint=structured_medium`;
- `unit_not_detected`;
- `period_not_detected`;
- normalized table validation passed.

The table facts experiment generated 3 runtime-review-only revenue facts:

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

## Conservative Boundaries

- CSV reader output is a normalized table, not an L1 fact.
- Structured table facts are runtime review only.
- No fixture write.
- No accepted manifest update.
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

- targeted tests `385 passed`;
- full pytest `1033 passed, 1 skipped`;
- regression `passed=47 failed=0 total=47`;
- token / secret / provider scan passed;
- artifact boundary passed;
- git tracked output remained empty.

This documentation-only cleanup stage did not rerun pytest or regression.

## Known Limitations

- Sample is local manually prepared CSV.
- Sample is not official raw table extraction.
- Unit and period were not auto-detected from CSV header.
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

Recommended next stage:

```text
CSV normalized table -> business_composition_table_facts integration design
```

Alternative later stage:

```text
Local HTML table reader design
```

Preferred priority is `CSV normalized table -> business_composition_table_facts
integration design`.

Do not directly enter:

- live CNInfo;
- PDF extraction;
- DOCX reader;
- Excel reader;
- candidate generator integration;
- Research Report V1 integration;
- fixture promotion;
- validator.
