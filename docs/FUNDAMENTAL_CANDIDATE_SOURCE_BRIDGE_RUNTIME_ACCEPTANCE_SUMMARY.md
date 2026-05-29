# Fundamental Candidate Source Bridge Runtime Acceptance Summary

Date: 2026-05-29

Stage: Fundamental Skill Candidate Source Bridge Runtime Acceptance Summary.

Status: documentation-only closeout. This summary records the accepted retained
`600406` `candidate_source_bridge.v1` runtime baseline after fixing the bridge
artifact encoding bug. This stage does not write code, modify tests, promote
fixtures, update accepted manifests, change orchestration / CLI behavior,
integrate Research Report V1, change the candidate generator main path, update
review decisions, modify pipeline / scoring / P1.1 behavior, change regression
expected files, generate new runtime output, call providers, read tokens,
connect MCP, use the network, run smoke, or provide trading advice.

## 1. Final Status

- `candidate_source_bridge.v1` implementation accepted.
- Retained `600406` bridge runtime review accepted.
- Encoding bug fixed by regenerating the runtime bridge artifact with a
  UTF-8-correct company name.
- Retained `600406` candidate source bridge runtime baseline frozen.
- No provider-centric `fact_candidates.json` mutation.
- No candidate generator main path change.
- No Research Report V1 integration.
- No fixture promotion.
- No accepted manifest update.
- No live CNInfo.

## 2. Old Corrupted Artifact

Old corrupted artifact:

```text
output/candidate_source_bridges/20260529T032922Z/600406/candidate_source_bridge_review.json
```

Recorded bug:

- old SHA256:
  `A1F2D55A3497E5BF3399B064EB2D54F2E372F402BD865F7D834AAC97AF61548F`;
- expected `company_name="国电南瑞"`;
- actual `company_name="????"`;
- actual codepoints `[63, 63, 63, 63]`;
- this was an artifact-content encoding bug, not a terminal display problem;
- the old artifact was not accepted as baseline;
- the old artifact was deleted after the regenerated artifact passed
  validation;
- the old timestamp empty directory was cleaned if applicable.

## 3. New Baseline Artifact

New accepted baseline artifact:

```text
output/candidate_source_bridges/20260529T034024Z/600406/candidate_source_bridge_review.json
```

Baseline records:

- new SHA256:
  `49A683E178F85E101B0D3C63E75E0D2E4CC5741A09FD61088F22174070B91FBF`;
- `company_name="国电南瑞"`;
- codepoints `[22269, 30005, 21335, 29790]`;
- generated with ASCII-safe literal `"\u56fd\u7535\u5357\u745e"` or an
  equivalent UTF-8-safe path;
- validated by `validate_candidate_source_bridge(...)`;
- ignored runtime artifact;
- not staged and not tracked;
- not a fixture;
- not regression expected;
- not an accepted manifest update;
- not a Research Report V1 update;
- not candidate generator main output;
- not provider-centric `fact_candidates.json` mutation.

## 4. Input Artifacts

Provider input artifact:

```text
output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json
```

Provider input records:

- SHA256 unchanged:
  `9A94D2DBF1D28AA260E51CBA17B1E0A0BFFD20D3B7DD08C49581E8365AC0CC47`;
- `candidate_count=1004`;
- `manual_review_count=184`;
- conservative `blocked_count=807`;
- ignored runtime artifact;
- not modified.

Official disclosure input artifact:

```text
output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json
```

Official input records:

- SHA256 unchanged:
  `514464210CB49DC31BA0D63BBC895FB66B23C2FF8A713AAD723351E6E0733BFA`;
- `candidate_rows=7`;
- 1 main business candidate;
- 6 revenue table candidates;
- all rows use `L1_official_disclosure`;
- all rows remain human-review / caveated;
- no verified fact;
- ignored runtime artifact;
- not modified.

## 5. Bridge Payload Summary

Accepted bridge payload:

- `version=candidate_source_bridge.v1`;
- `code=600406`;
- `company_name=国电南瑞`;
- provider source counts `1004 / 184 / 807`;
- official source counts `7 / 7 / 0`;
- artifact refs are relative `output/` paths;
- `cross_source_conflicts=[]`;
- `review_priorities=8`;
- includes `cross_source_conflict_detection_not_performed_schema_mismatch`;
- no deep merge;
- no provider primary change;
- no auto verified;
- no Research Report V1 integration;
- `not_for_trading_advice=true`.

## 6. Boundary / Git Checks

Accepted boundary:

- provider artifact unchanged;
- official artifact unchanged;
- old corrupted artifact removed;
- new artifact retained;
- `git status --short -uno` clean;
- `git diff` empty;
- staged diff empty;
- `git ls-files output` empty;
- no accepted manifest change;
- no Research Report artifacts change;
- no fixture / regression expected change;
- no candidate generator main output change.

## 7. Token / Secret / Provider Checks

The following scan targets were clean:

- provider candidate artifact;
- official candidate artifact;
- new bridge artifact;
- git diff;
- staged diff.

Confirmed absent:

- token;
- Bearer string;
- MCP URL;
- `.env` reference;
- local secret path;
- provider credential;
- trading recommendation keys;
- `verified_fact` / `auto_verified`;
- provider primary switch.

Execution boundary confirmed:

- no `TUSHARE_TOKEN` read;
- no network;
- no CNInfo / Tushare / AkShare / provider call;
- no MCP.

## 8. Conservative Boundaries

- The bridge artifact is a source index, not a merge.
- Official rows are not appended to provider-centric `fact_candidates.json`.
- Provider candidates remain provider-centric.
- Official candidates remain an independent payload.
- The bridge only lets a future review layer see both sources.
- Cross-source conflicts are review signals only.
- Review priorities are not fixture promotion.
- Review priorities are not verified facts.
- No automatic report rewrite.

## 9. Verification

Latest accepted verification results are quoted here, not rerun by this
documentation-only stage:

- targeted tests `549 passed`;
- full pytest latest `1197 passed, 1 skipped`;
- regression `passed=47 failed=0 total=47`;
- `validate_candidate_source_bridge(...)` passed;
- artifact boundary passed;
- token / secret / provider scan passed.

## 10. Known Limitations

- No deep cross-source matching yet.
- No provider / official conflict resolution yet.
- No candidate review decision update yet.
- No candidate schema v2 yet.
- No Research Report V1 L1 evidence integration yet.
- Bridge artifact is a runtime ignored baseline only.
- Existing provider-centric `fact_candidates.json` remains unchanged.
- Unrelated untracked files may exist in a developer workspace but were not
  part of this stage.

## 11. Next Recommended Stage

Recommended next stage:

```text
Candidate Review Decisions Update Design For Bridge Sources
```

Goal:

- design how `candidate_review_decisions.json` can reference provider
  candidates and official disclosure candidates;
- require `source_type`, `candidate_id`, and `artifact_ref`;
- keep review decisions separate from fixture promotion;
- keep review decisions separate from verified facts;
- defer promotion rules;
- defer Research Report V1 L1 evidence integration.

Do not directly enter:

- Research Report V1 integration;
- fixture promotion;
- validator work;
- live CNInfo;
- provider primary switch;
- Dashboard / Batch.

## 12. Review Decisions Bridge Sources Design Sync

The bridge-aware candidate review decisions design is now recorded in:

```text
docs/FUNDAMENTAL_CANDIDATE_REVIEW_DECISIONS_BRIDGE_SOURCES_DESIGN.md
```

That design treats this accepted bridge artifact as review queue input only:

- provider candidates remain referenced from
  `output/ground_truth_candidates/20260527T155056/600406/fact_candidates.json`;
- official disclosure candidates remain referenced from
  `output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json`;
- bridge priorities remain referenced from
  `output/candidate_source_bridges/20260529T034024Z/600406/candidate_source_bridge_review.json`;
- `review_priorities=8` affects review order, not factual truth;
- `cross_source_conflicts=[]` is not proof of source agreement because deep
  conflict matching is still blocked by schema mismatch;
- review decisions must preserve `source_type`, `candidate_id`,
  `artifact_ref`, caveats, and review status.

The next recommended stage after this documentation-only design is:

```text
Bridge-aware review decisions implementation
```

It should still avoid fixture promotion, verified fact generation, accepted
manifest updates, Research Report V1 integration, live CNInfo, provider calls,
token reads, MCP, scoring / P1.1 changes, regression expected changes, and
trading advice.
