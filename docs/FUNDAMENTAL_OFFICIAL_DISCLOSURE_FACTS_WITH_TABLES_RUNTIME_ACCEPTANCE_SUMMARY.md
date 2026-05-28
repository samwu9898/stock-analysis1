# Fundamental Official Disclosure Facts With Tables Runtime Acceptance Summary

Stage: Fundamental Skill Official Disclosure Facts With Tables Runtime
Acceptance Summary

Status: documentation-only acceptance closeout. The table facts ->
`official_disclosure_facts` runtime baseline is frozen after explicit
`source_document_id` alignment.

This document records the retained CSV table facts -> official disclosure facts
runtime review after source lineage alignment. It does not change code, tests,
fixtures, accepted manifests, orchestration, CLI behavior, Research Report V1,
candidate generation, review decisions, pipeline / scoring / P1.1, regression
expected files, or runtime output.

## 1. Final Status

- Table facts -> `official_disclosure_facts` integration implementation
  accepted.
- Source-document alignment runtime review accepted.
- Table facts -> `official_disclosure_facts` runtime baseline frozen.
- No candidate generator integration.
- No Research Report V1 integration.
- No fixture promotion.
- No accepted manifest update.
- No live CNInfo.

## 2. Previous Stop Gate

The previous runtime attempt correctly failed closed on source lineage:

- base official payload `source_document_id`:
  `600406_2025_semiannual_report_real`;
- old CSV table facts `source_document_id`:
  `doc_600406_2025H1_real_local`;
- integration correctly stopped because the table facts referenced a source
  document that did not exist in the base official disclosure payload;
- no integration artifact was generated in the stopped run;
- this was correct fail-closed behavior, not an implementation failure.

## 3. Aligned Runtime Input Record

Inputs:

```text
output/official_disclosures/20260528T125521Z/600406/official_disclosure_facts.json
output/official_disclosures/local_structured_table_samples/600406_h1_product.csv
output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json
```

Aligned source lineage:

- base source document id: `600406_2025_semiannual_report_real`;
- rebuilt normalized table `source_document_id`:
  `600406_2025_semiannual_report_real`;
- rebuilt table facts `source_document_id`:
  `600406_2025_semiannual_report_real`.

## 4. Runtime Result Summary

Official disclosure payload result:

- base `source_documents=1`;
- base `extracted_facts=1`;
- integrated `extracted_facts=7`;
- original fact preserved;
- new table facts appended;
- `source_tables=1`;
- `table_caveats=4`;
- `table_conversion_warnings=4`;
- `source_documents` remained 1;
- `not_for_trading_advice=true`;
- no verified fact.

Table facts result:

- 6 revenue facts generated;
- includes `电网智能`;
- includes `数能融合`;
- includes `合计`;
- `电网智能` revenue `12224749159.44`;
- `数能融合` revenue `3900471200.41`;
- `合计` revenue `24211165881.72`;
- all facts include source table / row / column / column map;
- all facts include caveat `local_structured_sample_requires_human_review`;
- all facts are `structured_medium`;
- all facts require human review.

## 5. Runtime Artifact Record

Runtime review artifact:

```text
output/official_disclosures/20260528T173612Z/600406/official_disclosure_facts_with_tables_review.json
```

Artifact boundary:

- ignored runtime artifact;
- not staged / not tracked;
- not fixture;
- not regression expected;
- not accepted manifest update;
- not Research Report V1 update;
- not candidate generator output.

## 6. Validation / Safety

Validation passed:

- `validate_official_disclosure_table_integration_payload(...)`;
- `validate_official_disclosure_facts(...)`;
- integrated table facts passed `validate_table_fact(...)`;
- all table facts reference an existing source document;
- source table trace valid;
- `table_quality_hint` / `table_quality_final` legal enum:
  `structured_medium`;
- no `fact_id` collision;
- no `source_table` trace conflict;
- no caveat-only table facts;
- no verified fact.

## 7. Boundary / Git Checks

Boundary checks passed:

- base official disclosure facts unchanged;
- retained CSV unchanged;
- old CSV table facts review artifact unchanged;
- only new ignored runtime review artifact retained;
- `git status` clean;
- `git diff` / staged diff empty;
- `git ls-files output` empty;
- no accepted manifest change;
- no Research Report artifacts change;
- no fixture / regression expected change.

## 8. Token / Secret / Provider Checks

Scanned clean:

- input CSV;
- base official payload;
- old CSV table facts review artifact;
- new integrated runtime artifact;
- git diff;
- staged diff.

Confirmed:

- no token;
- no Bearer;
- no MCP URL;
- no `.env`;
- no local secret path;
- no provider credential;
- no trading recommendation keys;
- no `TUSHARE_TOKEN` read;
- no network;
- no CNInfo / Tushare / AkShare / provider call;
- no MCP.

## 9. Conservative Boundaries

- Integrated table facts remain runtime-review-only.
- Facts are caveated L1 official disclosure candidates.
- Facts are not verified facts.
- Facts are not fixtures.
- Facts are not accepted manifest entries.
- Facts are not candidate generator output.
- Facts are not Research Report V1 evidence yet.
- Explicit `source_document_id` alignment is mandatory.
- Source lineage mismatch must continue to fail closed.
- No automatic source id rewriting is allowed.

## 10. Verification

Latest accepted verification results:

- targeted tests `466 passed`;
- full pytest latest `1114 passed, 1 skipped`;
- regression `passed=47 failed=0 total=47`;
- runtime artifact validation passed;
- artifact boundary passed;
- token / secret / provider scan passed.

This documentation-only closeout did not rerun pytest, regression, live smoke,
provider calls, token reads, network access, or MCP.

## 11. Known Limitations

- CSV sample remains a local structured sample.
- It is not official raw table extraction.
- Unit and period were supplied explicitly during review.
- Facts require human review.
- Current path only validates revenue facts.
- No cost / gross margin / YoY facts accepted yet.
- No candidate generator output yet.
- No Research Report V1 integration yet.
- No live CNInfo.
- No PDF / DOCX / HTML / Excel reader integration.

## 12. Next Recommended Stage

Historical next stage, now recorded in a separate design:

```text
official_disclosure_facts -> candidate generator integration design
```

Goal:

- design how text facts and table facts in `official_disclosure_facts` enter
  `fact_candidates`;
- still do not directly enter Research Report V1;
- still do not write fixtures;
- still do not update accepted manifests;
- still do not do live CNInfo.

Do not directly enter:

- Research Report V1 integration;
- fixture promotion;
- validator;
- live CNInfo;
- PDF extraction;
- Dashboard / Batch.

## 13. Candidate Generator Integration Design Sync

The official disclosure facts -> candidate generator integration design is now
recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_FACTS_TO_CANDIDATE_GENERATOR_INTEGRATION_DESIGN.md
```

Design position:

- `official_disclosure_facts.json` is the future official-evidence input to
  `fact_candidates.json`;
- text facts and table facts can become official disclosure candidates;
- `source_type=official_disclosure` and
  `evidence_tier=L1_official_disclosure` must be preserved;
- source document, section, page / anchor, table, row, column, column map,
  classification, segment, denominator, quality, confidence, and caveats must
  remain traceable;
- `needs_human_review=true` and
  `local_structured_sample_requires_human_review` must pass through;
- no official candidate is promoted to `verified_fact`.

The current runtime baseline remains unchanged:

- integrated `extracted_facts=7`;
- 6 revenue facts;
- `source_tables=1`;
- `table_caveats=4`;
- `table_conversion_warnings=4`;
- no candidate generator output yet;
- no Research Report V1 integration yet.

Next recommended stage:

```text
official_disclosure_facts -> candidate generator integration implementation
```

That future implementation must remain separate from fixture promotion,
accepted manifest updates, Research Report V1 integration, provider calls,
token reads, network access, MCP, scoring / P1.1 changes, regression expected
changes, and trading advice.
