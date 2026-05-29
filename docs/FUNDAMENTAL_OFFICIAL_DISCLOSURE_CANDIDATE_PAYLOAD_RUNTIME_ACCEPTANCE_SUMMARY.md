# Fundamental Official Disclosure Candidate Payload Runtime Acceptance Summary

Stage: Fundamental Skill Official Disclosure Candidate Payload Runtime
Acceptance Summary

Status: documentation-only closeout. The official disclosure facts -> official
candidate payload runtime baseline is frozen.

This document records the accepted runtime review for converting retained
`official_disclosure_facts_with_tables_review.json` into an independent
official disclosure candidate payload. It does not change code, tests,
fixtures, accepted manifests, orchestration, CLI behavior, Research Report V1,
the candidate generator main path, review decisions, pipeline / scoring /
P1.1, regression expected files, or runtime output.

## 1. Final Status

- Official disclosure candidate adapter implementation accepted.
- Official disclosure facts with tables -> official candidate payload runtime
  review accepted.
- Official disclosure facts -> official candidate payload runtime baseline
  frozen.
- No provider-centric `fact_candidates.json` output.
- No candidate generator main path modification.
- No Research Report V1 integration.
- No fixture promotion.
- No accepted manifest update.
- No live CNInfo.

## 2. Input Artifact Record

Input artifact:

```text
output/official_disclosures/20260528T173612Z/600406/official_disclosure_facts_with_tables_review.json
```

Artifact boundary:

- ignored runtime artifact;
- not staged / not tracked;
- contains `source_documents=1`;
- contains `extracted_facts=7`;
- contains 1 `basic_info.main_business_official_text` fact;
- contains 6 `business_composition.product_segment.revenue` table facts;
- contains `source_tables=1`;
- contains `table_caveats=4`;
- contains `table_conversion_warnings=4`;
- `not_for_trading_advice=true`;
- no verified fact.

## 3. Runtime Candidate Artifact Record

Generated runtime artifact:

```text
output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json
```

Artifact boundary:

- ignored runtime artifact;
- not staged / not tracked;
- not fixture;
- not regression expected;
- not accepted manifest update;
- not Research Report V1 update;
- not provider-centric `fact_candidates.json`;
- not candidate generator main output.

## 4. Candidate Payload Summary

Candidate payload:

- `version=official_disclosure_fact_candidates.v1`;
- `source_type=official_disclosure`;
- `candidate_rows=7`;
- includes 1 main business candidate;
- includes 6 revenue table candidates;
- all rows use `evidence_tier=L1_official_disclosure`;
- no `verified_fact`;
- no `review_status=verified`;
- no `auto_verified`.

Table segments:

- `电网智能`;
- `数能融合`;
- `能源低碳`;
- `工业互联`;
- `集成及其他`;
- `合计`.

## 5. Caveat / Warning Propagation

- `table_caveats[]` entered `candidate_caveats`.
- `table_conversion_warnings[]` entered `integration_warnings`.
- `local_structured_sample_requires_human_review` was preserved.
- `delimiter_sniffed` was preserved.
- `unit_not_detected` was preserved.
- `period_not_detected` was preserved.
- `denominator_missing` was not present in this input.
- Caveats did not become report conclusions.

## 6. Review Status Summary

- Main business candidate is `manual_review_required`.
- 6 table revenue candidates are `manual_review_required`.
- `structured_medium` remains manual review.
- Simulated missing unit / period / denominator row becomes
  `blocked_by_caveat`.
- Simulated `unreliable_text_copy` / `unusable` rows do not enter fact
  candidates.
- No verified status was generated.

## 7. Source Trace Caveat

- Current input has empty `source_page_or_anchor`.
- Candidate rows preserve it as empty.
- This is accepted as a baseline caveat because trace is still closed through
  source document + source section + table row / column / source_column_map.
- Future official page / anchor extraction can strengthen this trace later.
- Do not silently invent page or anchor.

## 8. Safety / Validation

- `validate_official_disclosure_candidate_payload(...)` passed.
- All rows passed `validate_official_disclosure_candidate_row(...)`.
- Input SHA256 before / after unchanged:
  `cb67702d3c9db77b0ae1c4710a369981e2d74c53b279eaf1295049a64ed1ced4`.
- No mutation of input artifact.
- No token / Bearer / MCP URL / `.env` / local secret path.
- No provider credential.
- No trading recommendation keys.

## 9. Boundary / Git Checks

- `git status` clean.
- Unstaged / staged diff empty.
- `git ls-files output` empty.
- Runtime artifact ignored.
- No accepted manifest change.
- No Research Report artifact change.
- No fixture / regression expected change.
- No candidate generator main output change.
- No provider-centric `fact_candidates.json` generated.

## 10. Safety / Non-Goals

This stage did not:

- read a token;
- use the network;
- call CNInfo / Tushare / AkShare / provider;
- connect MCP;
- perform a live fetch;
- promote fixtures;
- update accepted manifests;
- integrate Research Report V1;
- integrate the candidate generator main path;
- change scoring / P1.1 / regression behavior;
- emit trading advice.

## 11. Verification

Latest accepted verification results are quoted here, not rerun by this
documentation-only stage:

- targeted tests `496 passed`;
- full pytest latest `1144 passed, 1 skipped`;
- regression `passed=47 failed=0 total=47`;
- runtime validation passed;
- token / secret / provider scan passed;
- artifact boundary passed.

## 12. Known Limitations

- Output is an independent official candidate payload.
- It is not merged into provider-centric `fact_candidates.json`.
- Existing candidate generator schema remains provider-centric.
- No Research Report V1 integration.
- No fixture promotion.
- No standalone promotion validator.
- No live CNInfo.
- `source_page_or_anchor` is empty in current input.
- Official candidates still require human review.
- Table facts currently cover revenue only, not cost / gross margin / YoY.

## 13. Next Recommended Stage

Historical recommended next stage, now recorded in the bridge design:

```text
official candidate payload -> provider-centric fact_candidates bridge design
```

Goal:

- design how the official candidate payload can coexist with or be referenced
  by provider-centric `fact_candidates.json` without polluting the existing
  provider-centric schema;
- design first, without code;
- do not directly enter Research Report V1;
- do not write fixtures;
- do not build a validator;
- do not connect live CNInfo.

Do not directly enter:

- Research Report V1 integration;
- fixture promotion;
- validator work;
- live CNInfo;
- Tushare primary switch;
- Dashboard / Batch.

## 14. Bridge Design Sync

The bridge design is now recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_CANDIDATE_PAYLOAD_TO_FACT_CANDIDATES_BRIDGE_DESIGN.md
```

Design decision:

- keep the retained official candidate payload independent;
- do not directly append official rows to provider-centric
  `fact_candidates.json`;
- add a future lightweight bridge / source-index artifact first;
- let later review tooling read provider candidates and official candidates
  side by side;
- defer a unified candidate pool until candidate schema v2.

This sync does not change the frozen runtime baseline, generate output, update
fixtures, update accepted manifests, modify the candidate generator main path,
integrate Research Report V1, call providers, read tokens, connect MCP, change
scoring / P1.1 / regression expected files, or emit trading advice.

Current recommended next stage:

```text
Candidate Review Decisions Update Design For Bridge Sources
```

## 15. Candidate Source Bridge Runtime Acceptance Sync

The bridge artifact implementation, retained `600406` bridge runtime review,
and UTF-8 encoding fix are now accepted and frozen in:

```text
docs/FUNDAMENTAL_CANDIDATE_SOURCE_BRIDGE_RUNTIME_ACCEPTANCE_SUMMARY.md
```

Bridge runtime baseline:

- old corrupted bridge artifact
  `output/candidate_source_bridges/20260529T032922Z/600406/candidate_source_bridge_review.json`
  had `company_name="????"` with codepoints `[63, 63, 63, 63]`, SHA256
  `A1F2D55A3497E5BF3399B064EB2D54F2E372F402BD865F7D834AAC97AF61548F`, and
  was deleted after validation of the replacement artifact;
- new retained baseline artifact:
  `output/candidate_source_bridges/20260529T034024Z/600406/candidate_source_bridge_review.json`;
- new SHA256:
  `49A683E178F85E101B0D3C63E75E0D2E4CC5741A09FD61088F22174070B91FBF`;
- `company_name="国电南瑞"` with codepoints
  `[22269, 30005, 21335, 29790]`;
- provider input SHA256 remained
  `9A94D2DBF1D28AA260E51CBA17B1E0A0BFFD20D3B7DD08C49581E8365AC0CC47`;
- official input SHA256 remained
  `514464210CB49DC31BA0D63BBC895FB66B23C2FF8A713AAD723351E6E0733BFA`;
- provider source counts are `1004 / 184 / 807`;
- official source counts are `7 / 7 / 0`;
- `cross_source_conflicts=[]`;
- `review_priorities=8`;
- no official rows were appended to provider-centric `fact_candidates.json`;
- no candidate generator main path, Research Report V1, fixture, accepted
  manifest, regression expected, scoring / P1.1, provider, token, MCP, or live
  CNInfo behavior changed.

Current recommended next stage:

```text
Candidate Review Decisions Update Design For Bridge Sources
```
