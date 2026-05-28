# Fundamental Official Disclosure CSV Table Facts Runtime Acceptance Summary

Date: 2026-05-29

Stage: Fundamental Skill CSV Table Facts Runtime Acceptance Summary.

Status: documentation-only closeout. This stage records the accepted retained
CSV sample -> table facts runtime review and freezes the retained CSV sample ->
table facts runtime baseline. It does not change code, tests, fixtures,
accepted manifests, orchestration, CLI behavior, Research Report V1, candidate
generation, review decisions, pipeline / scoring / Research Intelligence P1.1,
regression expected files, or runtime output.

Latest accepted verification results are quoted, not rerun here:

- targeted tests `424 passed`
- full pytest latest `1072 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

## 1. Final Status

- CSV table fact converter implementation accepted.
- Strict Gate Patch accepted.
- Retained CSV sample -> table facts runtime review accepted.
- Retained CSV sample -> table facts runtime baseline frozen.
- No candidate generator integration.
- No Research Report V1 integration.
- No `official_disclosure_facts.json` integration yet.
- No accepted manifest update.
- No fixture promotion.

## 2. Input CSV Record

Input CSV:

```text
output/official_disclosures/local_structured_table_samples/600406_h1_product.csv
```

Record:

- ignored runtime sample;
- not staged / not tracked;
- local structured CSV sample;
- not live CNInfo;
- not provider output;
- not fixture;
- no token / secret / URL / cookie;
- no trading recommendation key.

## 3. Runtime Artifact Record

Runtime artifact:

```text
output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json
```

Record:

- ignored runtime artifact;
- not a fixture;
- not regression expected;
- not accepted manifest update;
- not Research Report V1 update;
- not candidate generator output;
- contains normalized table summary, `table_facts`, `table_caveats`,
  `conversion_warnings`, validation summary, and
  `not_for_trading_advice=true`.

## 4. CSV Reader Runtime Summary

Accepted reader runtime observations:

- headers = 7;
- rows = 6;
- raw strings preserved;
- `delimiter_sniffed` warning visible;
- `unit_not_detected` warning visible;
- `period_not_detected` warning visible;
- `classification_hint=product`;
- `table_quality_hint=structured_medium`;
- reader did not generate table facts.

## 5. Converter Runtime Summary

Explicit runtime review parameters:

- `period=2025H1`
- `unit=CNY`
- `denominator=主营业务收入合计`
- `classification_type=product`
- `table_quality=structured_medium`
- `needs_human_review=true`

Accepted converter runtime output:

- generated 6 revenue facts;
- includes `电网智能`, `数能融合`, and `合计`;
- official segment names preserved;
- revenue values preserved as raw strings or traceable values;
- each fact includes `source_table_id`;
- each fact includes `source_row_index`;
- each fact includes `source_column_name`;
- each fact includes `source_column_map`;
- each fact includes `period=2025H1`;
- each fact includes `unit=CNY`;
- each fact includes `classification_type=product`;
- each fact includes `denominator=主营业务收入合计`;
- each fact uses `table_quality=structured_medium`;
- each fact uses `needs_human_review=true`;
- each fact includes caveat `local_structured_sample_requires_human_review`;
- reader warnings such as `delimiter_sniffed`, `unit_not_detected`, and
  `period_not_detected` are propagated to caveats or conversion warnings;
- no verified fact generated.

## 6. Negative / Fail-Closed Checks

Accepted negative / fail-closed checks passed:

- no explicit period + `period_not_detected` -> fail closed;
- no explicit unit + `unit_not_detected` -> fail closed;
- duplicate revenue-like header -> `ambiguous_header` fail closed;
- `table_quality=unreliable_text_copy` -> no table facts;
- denominator omitted -> `denominator_missing` appears in
  `conversion_warnings` and fact caveats if revenue facts are allowed.

## 7. Conservative Boundaries

- Facts are runtime-review-only.
- Facts are L1 official disclosure candidates only in a caveated,
  human-review-required sense.
- No verified fact.
- No fixture write.
- No accepted manifest update.
- No `official_disclosure_facts.json` integration yet.
- No candidate generator output.
- No Research Report V1 update.
- No scoring / P1.1 / regression update.
- No trading advice.
- Scanner false-positive risk around long mixed-case source ids remains a
  future dedicated hardening item, not part of this baseline.

## 8. Safety / Non-Goals

- No token read.
- No network.
- No CNInfo / Tushare / AkShare / provider call.
- No MCP.
- No live fetch.
- No OCR.
- No PDF table extraction.
- No DOCX / HTML / Excel reader.
- No fixture or regression expected changes.
- No accepted manifest update.
- No report integration.
- No candidate generator integration.
- No trading advice.

## 9. Verification

Latest accepted verification results:

- targeted tests `424 passed`;
- full pytest latest `1072 passed, 1 skipped`;
- regression `passed=47 failed=0 total=47`;
- runtime artifact validation passed;
- token / secret / provider scan passed;
- artifact boundary passed;
- git tracked output remained empty.

This documentation-only summary did not rerun pytest, regression, live smoke,
provider calls, or network checks.

## 10. Known Limitations

- Sample is local structured CSV.
- Sample is not official raw table extraction.
- Facts are runtime-review-only.
- Unit and period were supplied explicitly during review.
- Current converter generates only revenue facts by default.
- No cost / gross margin / YoY facts accepted yet.
- No `official_disclosure_facts.json` integration yet.
- No candidate generator integration yet.
- No Research Report V1 integration yet.
- No HTML / DOCX / Excel / PDF reader yet.

## 11. Next Recommended Stage

Historical next stage at runtime acceptance time:

```text
CSV table facts -> official_disclosure_facts integration design
```

Goal:

- design how to embed or link `table_facts` / `table_caveats` into
  `official_disclosure_facts.json`;
- still do not connect the candidate generator;
- still do not connect Research Report V1;
- still do not change fixtures, accepted manifests, scoring, or P1.1.

Do not directly enter:

- live CNInfo;
- PDF extraction;
- DOCX / HTML / Excel reader;
- candidate generator integration;
- Research Report V1 integration;
- fixture promotion;
- validator.

## 12. Table Facts To Official Disclosure Facts Integration Design Sync

The CSV table facts -> `official_disclosure_facts.json` integration design is
now recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_TABLE_FACTS_TO_OFFICIAL_DISCLOSURE_FACTS_INTEGRATION_DESIGN.md
```

Design scope:

- internal official disclosure parser artifact assembly;
- keep `extracted_facts[]` as the unified fact list;
- append table-derived facts under the `business_composition.*` namespace;
- add optional `source_tables[]` for normalized table trace;
- add optional `table_caveats[]` for table-level warnings and failed gates;
- preserve source document, source table, row / column location, unit, period,
  denominator, `table_quality`, and human-review caveats;
- keep `not_for_trading_advice=true`;
- generate no verified fact.

Still out of scope:

- implementation;
- fixture write;
- accepted manifest update;
- candidate generator integration;
- Research Report V1 integration;
- scoring / P1.1 / regression changes;
- live CNInfo, provider call, token read, network, MCP, smoke, or trading
  advice.

Current next recommended stage:

```text
Table facts -> official_disclosure_facts integration implementation
```
