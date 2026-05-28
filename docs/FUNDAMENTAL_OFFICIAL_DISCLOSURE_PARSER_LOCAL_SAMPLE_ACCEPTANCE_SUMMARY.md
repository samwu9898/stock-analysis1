# Fundamental Official Disclosure Parser Local Sample Acceptance Summary

Date: 2026-05-28

Stage: Fundamental Skill Official Disclosure Parser Local Sample Runtime
Acceptance Summary.

Status: documentation-only closeout. This summary records the accepted local
sample runtime review for the Minimal Official Disclosure Parser. It does not
change code, tests, fixtures, accepted manifests, orchestration, CLI behavior,
Research Report V1 builders or renderers, candidate generation, review
decisions, scoring, Research Intelligence P1.1, regression expected files, or
runtime output.

Latest accepted verification results are quoted, not rerun here:

- targeted tests `298 passed`
- full pytest latest `946 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

The real local downloaded filing sample runtime review has since been accepted
and is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_PARSER_REAL_LOCAL_FILING_ACCEPTANCE_SUMMARY.md`.
That later review used a user-prepared real local TXT sample for `600406` 2025
semiannual report and froze the official disclosure parser real-local-file
baseline.

## 1. Final status

- Minimal official disclosure parser local-file implementation accepted.
- Conservative Period Patch accepted.
- Local sample runtime review accepted.
- Local-file parser baseline frozen.
- Real local official filing sample runtime accepted in the later review.
- Official disclosure parser real-local-file baseline frozen in the later
  review.
- Live CNInfo fetch is not implemented.
- PDF table parser is not implemented.
- Candidate generator integration is not implemented.
- L1 official disclosure integration is not implemented.
- Research Report V1 integration is not implemented.

This acceptance confirms only the local-file runtime minimum loop. It does not
mean live CNInfo ingestion, complete real announcement parsing, or direct
Research Report V1 use of L1 official evidence is available.

## 2. Local sample record

Local sample path:

```text
output/official_disclosures/local_samples/600406_annual_report_sample.txt
```

Record:

- This is a local sample text.
- It is not a complete real CNInfo announcement.
- It is not full PDF table parsing.
- It does not enter git.
- It is covered by the ignored `output/` boundary.

## 3. Runtime artifact record

Runtime artifact path:

```text
output/official_disclosures/20260528_194020/600406/official_disclosure_facts.json
```

Record:

- It is an ignored runtime artifact.
- It is not staged and not tracked.
- It is not a fixture.
- It is not a regression expected file.
- It is not an accepted manifest update.
- It is not a Research Report V1 update.

## 4. Validated flow

The accepted local runtime flow was:

```text
local sample text
  -> read_local_official_text
  -> extract_periodic_report_basics
  -> extract_main_business_candidate
  -> build_official_disclosure_facts
  -> write_official_disclosure_facts
  -> read_official_disclosure_facts
  -> validate_official_disclosure_facts
```

## 5. Extracted result summary

- `size_bytes=589`
- source text sha256:
  `59c787e4d4abf7a6e612607a6772417baa2f22674e2cac3e14088c5376ab5d6a`
- periodic basics:
  - `document_type=annual_report`
  - `report_period=2025A`
  - `disclosure_date=2026-04-30`
- main business candidate:
  - `evidence_tier=L1_official_disclosure`
  - `source_section=主营业务`
  - body length `133`
  - `needs_human_review=true`
- `source_documents=1`
- `extracted_facts=4`
- all L1 facts have source location
- `not_for_trading_advice=true`

## 6. Conservative boundaries

- The parser does not treat the disclosure date year as the report period.
- Missing report period must stay missing or caveated.
- An L1 fact requires source location.
- `needs_human_review=true` cannot replace source location.
- No verified fact is produced.
- No fixture is written.
- No report is changed.
- No accepted manifest is changed.
- No candidate generator integration exists yet.
- No Research Report V1 integration exists yet.

## 7. Safety / non-goals

- No token read.
- No network.
- No CNInfo call.
- No Tushare call.
- No AkShare call.
- No provider call.
- No MCP.
- No live fetch.
- No OCR.
- No full PDF table parsing.
- No fixture write.
- No accepted manifest update.
- No scoring, P1.1, or regression change.
- No trading advice, target price, position sizing, or technical signal.

## 8. Verification

- targeted tests `298 passed`
- full pytest latest `946 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`
- local sample runtime validation passed
- token / secret / provider scan passed
- artifact boundary passed

This documentation-only summary did not rerun pytest or regression.

## 9. Known limitations

- The sample is local official-style text, not live CNInfo.
- A real downloaded local official filing TXT sample has since been accepted,
  but only for conservative local read / extract / write / validate behavior.
- The parser does not parse PDF.
- The parser does not parse complex tables.
- The parser does not update `fact_candidates`.
- The parser does not update Research Report V1.
- The parser does not update the accepted manifest.
- L1 evidence tier integration remains future work.

## 10. Real local filing addendum

The later real local filing acceptance used:

```text
output/official_disclosures/local_real_samples/600406_2025_semiannual_report_real.txt
```

It wrote only the ignored runtime artifact:

```text
output/official_disclosures/20260528T125521Z/600406/official_disclosure_facts.json
```

Recorded result:

- input size `32961` bytes
- sha256
  `7a16dca91ac2d0a9ec6def90a17fa28e820f0ebdb87cdf86a0e9a6fb0df1acc3`
- `document_type=semiannual_report`
- `report_period=2025H1`
- `disclosure_date=2025-08-28`
- extraction confidence `medium`
- main business L1 candidate generated from `source_section=主营业务`
- `needs_human_review=true`
- no verified fact generated
- `source_documents=1`
- `extracted_facts=1`

Business composition regions were detected (`分行业`, `分产品`,
`主营业务分行业情况`, `主营业务分产品情况`, `主营业务分地区情况`, and `分地区`),
but only as `business_composition_section_detected` with
`table_structure_unreliable_due_to_pdf_text_copy`. Revenue, cost, gross margin,
revenue ratio, YoY, and segment values were not extracted because the TXT was
copied or converted from PDF and table structure is unreliable.

## 11. Next recommended stage

Recommended next stage:

```text
Official Disclosure Business Composition Table Parser Design
```

The next design should not extract numeric values from disordered TXT tables.
It should design an independent table parser, prefer official HTML table / PDF
table extraction / DOCX table / structured table source, and explicitly model
`table_quality`, source location, row / column alignment, unit, denominator,
and total checks.

Do not directly enter:

- live CNInfo fetch;
- Tushare;
- MCP;
- fixture promotion;
- candidate generator integration;
- Research Report V1 integration;
- validator;
- Dashboard / Batch implementation.
