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

## 1. Final status

- Minimal official disclosure parser local-file implementation accepted.
- Conservative Period Patch accepted.
- Local sample runtime review accepted.
- Local-file parser baseline frozen.
- Live CNInfo fetch is not implemented.
- L1 official disclosure integration is not implemented.

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
- No real downloaded full annual report sample has been accepted yet.
- The parser does not parse PDF.
- The parser does not parse complex tables.
- The parser does not update `fact_candidates`.
- The parser does not update Research Report V1.
- The parser does not update the accepted manifest.
- L1 evidence tier integration remains future work.

## 10. Next recommended stage

Recommended next option A:

- `official_disclosure_facts -> candidate generator integration design`

Recommended next option B:

- `real local downloaded official filing sample review`
- The user manually provides a real downloaded annual report, semiannual
  report, or announcement text file.
- The parser reads that local file only, with no network access.

Do not directly enter:

- live CNInfo fetch;
- Tushare;
- MCP;
- validator;
- fixture promotion;
- Dashboard / Batch implementation.
