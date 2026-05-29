# Phase 2 Local Artifact Index Design / Implementation Plan

Date: 2026-05-29

Stage: Phase 2 Local Artifact Index design and implementation planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not update
fixtures, does not update the accepted manifest, does not commit, and does not
push.

## 1. Phase 2 Module Positioning

The Local Artifact Index is the local evidence discovery scaffold in the future
Codex Skill + Research Pack flow.

Its only responsibility is to discover and describe local artifact state:

- which local artifacts appear to exist;
- where they are located;
- which artifact family and artifact type they belong to;
- which ticker / company / period they appear to reference;
- which schema version, source status, review status, freshness status, caveats,
  checksum, file size, and lineage references can be safely recorded.

The index can produce artifact inventory rows and artifact-state rows. It must
not produce factual conclusions.

It is not:

- a verified fact store;
- Research Report V1 integration;
- a candidate merger;
- an accepted manifest writer;
- fixture promotion;
- a provider fetcher;
- a live CNInfo connector;
- a live Tushare connector;
- a report generator;
- Dashboard / Batch;
- a PDF, DOCX, HTML, or Excel parser;
- a hypothesis generator.

The design goal is to make local evidence discoverable while preserving a hard
boundary between artifact presence and fact verification.

## 2. Input Scope

Future implementation may read these artifact families in a read-only manner
when they are located under approved local roots and pass safety checks:

- accepted manifest entries;
- accepted Research Report V1 artifact paths;
- normalized fundamentals;
- provider-separated fundamentals;
- evidence packs;
- provider fact candidates;
- official disclosure facts;
- official disclosure candidates;
- candidate source bridges;
- bridge-aware review decisions;
- score / confidence explainability artifacts;
- existing local report artifacts.

The index should support ticker-scoped operation first. Repository-wide scanning
is not required for Phase 2 planning and should not be used as an excuse to
ingest unrelated files.

Allowed future reads should be shallow and structured. JSON files may be read
only enough to validate known schema markers, identity fields, status fields,
period metadata, lineage pointers, and caveats. Non-JSON report files can be
indexed by path and filesystem metadata only; they must not be parsed.

## 3. Key Boundaries

The following boundaries are mandatory:

- Artifact existence does not mean a fact is verified.
- `accepted_manifest` freshness marked current does not mean new facts have
  been verified.
- Provider candidates are not verified facts.
- Official disclosure candidates are not report-ready facts.
- Bridge artifacts are source indexes, not merge outputs.
- Review decisions are workflow signals, not fixture promotion.
- Anything under `output/` can be local artifact state only; it must not
  automatically become a fact.
- A row in the Local Artifact Index cannot directly become a hypothesis.
- A row in the Local Artifact Index cannot directly become a verified fact.
- A row in the Local Artifact Index cannot directly enter Research Report V1.

The only allowed downstream use is inventory / readiness planning through the
Phase 1 schema and validators.

## 4. Output Schema Draft

Recommended row schema version:

```text
local_artifact_index_row.v1
```

Draft artifact row:

```json
{
  "artifact_id": "",
  "artifact_type": "",
  "artifact_path": "",
  "stock_code": "",
  "company_name": "",
  "source_family": "",
  "schema_version": "",
  "created_at": "",
  "modified_at": "",
  "data_period": "",
  "sha256": "",
  "file_size": 0,
  "source_status": "",
  "review_status": "",
  "freshness_status": "",
  "caveats": [],
  "lineage_refs": [],
  "not_for_trading_advice": true
}
```

Field notes:

- `artifact_id`: deterministic local id derived from normalized path,
  artifact type, stock code, and optional period. It must not include secrets.
- `artifact_type`: classifier result such as
  `accepted_manifest`, `research_report_v1_json`, `evidence_pack`, or
  `official_disclosure_candidate`.
- `artifact_path`: normalized repo-relative path when possible. Absolute paths
  may be used only internally and should not leak outside local audit output
  unless explicitly approved.
- `stock_code`: ticker identity, preferred over company name.
- `company_name`: auxiliary identity label only.
- `source_family`: broad family such as `accepted_manifest`,
  `research_report_v1`, `provider_candidates`, or `official_disclosures`.
- `schema_version`: extracted from known JSON schema markers when safe, or
  empty / unknown.
- `created_at`: artifact creation timestamp if available from safe metadata or
  known payload metadata.
- `modified_at`: filesystem modification timestamp.
- `data_period`: period covered by the artifact, if safely available.
- `sha256`: optional file checksum. It must not be computed for secret-like or
  ignored paths.
- `file_size`: filesystem size in bytes.
- `source_status`: availability and usability enum.
- `review_status`: workflow review state when available; otherwise unknown.
- `freshness_status`: freshness state from manifest or local metadata when
  available.
- `caveats`: conservative warnings about candidate-only, conflicts, stale
  data, unreadable files, schema mismatch, or identity ambiguity.
- `lineage_refs`: references to parent artifacts or related local source rows.
- `not_for_trading_advice`: always `true`.

Recommended `freshness_status` values:

```text
current
unknown
stale
superseded
invalidated
not_applicable
```

Recommended `review_status` values:

```text
unknown
not_reviewed
review_required
reviewed
accepted_for_report_candidate
rejected
conflict_open
invalidated
```

## 5. `source_status` Enum

Recommended enum:

```text
available
missing
partial
candidate_only
review_required
conflict_open
stale
invalidated
unreadable
ignored
```

Definitions:

- `available`: artifact exists and passes path / type / shallow schema checks.
- `missing`: expected artifact path is not present.
- `partial`: artifact exists but expected companion rows, periods, or metadata
  are incomplete.
- `candidate_only`: artifact contains candidate evidence, not reviewed facts.
- `review_required`: artifact or identity requires human / workflow review.
- `conflict_open`: identity, period, source, or review status conflicts with
  another local artifact.
- `stale`: artifact is present but freshness metadata marks it stale or older
  than the configured policy.
- `invalidated`: manifest or review metadata marks it invalidated.
- `unreadable`: file exists but cannot be read safely.
- `ignored`: file is outside allowed families, secret-like, unrelated,
  mojibake/unclassifiable, or explicitly excluded.

## 6. Artifact Type / Source Family Mapping

This phase only designs classifiers. It does not scan the full `output/`
directory now.

Recommended mapping:

| Path or schema signal | artifact_type | source_family | Notes |
| --- | --- | --- | --- |
| `output/research_reports/accepted_manifest.json` | `accepted_manifest` | `accepted_manifest` | Read-only manifest locator input. Never write. |
| Accepted manifest entry pointing to report JSON | `accepted_research_report_v1_json` | `research_report_v1` | Path state only; report facts are not ingested. |
| Accepted manifest entry pointing to report Markdown | `accepted_research_report_v1_markdown` | `research_report_v1` | Path and metadata only. No Markdown parsing. |
| Accepted manifest entry pointing to report HTML | `accepted_research_report_v1_html` | `research_report_v1` | Path and metadata only. No HTML parsing. |
| `output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.json` | `research_report_v1_json` | `research_report_v1` | Existing local report artifact only. |
| `output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.md` | `research_report_v1_markdown` | `research_report_v1` | Existing local report artifact only. |
| `output/research_reports/<timestamp>/<code>/fundamental_research_report_v1.html` | `research_report_v1_html` | `research_report_v1` | Existing local report artifact only. |
| `output/fundamental_<code>.json` | `normalized_fundamentals` | `normalized_fundamentals` | Existing normalized artifact state. |
| Provider-specific fundamentals path or schema marker | `provider_separated_fundamentals` | `provider_fundamentals` | Preserve provider separation. Do not merge. |
| `output/evidence_pack_<code>.json` | `evidence_pack` | `evidence_packs` | Inventory evidence pack state only. |
| `output/ground_truth_candidates/<timestamp>/<code>/fact_candidates.json` | `provider_fact_candidates` | `provider_candidates` | Candidate-only unless review says otherwise; still not verified. |
| `output/official_disclosures/<timestamp>/<code>/*candidate*.json` | `official_disclosure_candidate` | `official_disclosures` | Candidate-only; not report-ready. |
| `output/official_disclosures/<timestamp>/<code>/*facts*.json` | `official_disclosure_facts` | `official_disclosures` | Local artifact state only; not automatic verification. |
| `output/candidate_source_bridges/<timestamp>/<code>/*.json` with bridge schema | `candidate_source_bridge` | `candidate_source_bridges` | Source index only; not merge. |
| `output/candidate_review_decisions_bridge_reviews/<timestamp>/<code>/*.json` | `bridge_aware_review_decisions` | `review_decisions` | Workflow signal only. |
| `output/ground_truth_candidate_reviews/<timestamp>/<code>/candidate_review_decisions.json` | `provider_candidate_review_decisions` | `review_decisions` | Workflow signal only. |
| Provider comparison / score explainability schema markers | `score_confidence_explainability` | `score_confidence_explainability` | Explainability state, not fact promotion. |
| Unknown, unrelated, mojibake, secret-like, token-like, or unsafe paths | `ignored` | `ignored` | Must not be auto-collected. |

Classifier precedence should be:

1. safety exclusion by path and filename;
2. allowed root check;
3. exact known path pattern;
4. exact known filename;
5. known JSON schema marker from shallow read;
6. ignored / review_required fallback.

No fuzzy path matching should promote a file into a high-trust artifact type.

## 7. Identity Matching

Identity matching must be conservative.

Rules:

- `stock_code` is the primary identity key.
- `company_name` is an auxiliary hint only.
- A path code such as `<code>` must match any payload `stock_code` when both
  are available.
- If a manifest entry code and payload code disagree, mark the row
  `conflict_open` and add a caveat.
- If only `company_name` is available, the row can be inventoried with
  `review_required`; it cannot confirm ticker identity.
- Fuzzy name matching must not directly confirm identity.
- Chinese abbreviations, historical names, aliases, and English names may be
  recorded as caveats or hints, but cannot override a code conflict.
- Multiple codes for one company name require `conflict_open`.
- Multiple company names for one code require `review_required` unless an
  accepted local identity source resolves the alias.
- User-supplied ticker / company input is an identity hint, not truth.

Ticker-scoped builders should prefer exact code filters. Name-only operation can
return a review-required inventory candidate set, but not a resolved index.

## 8. SHA-256 And Lineage

SHA-256 behavior:

- Compute `sha256` for safe, allowed, non-secret local files when the future
  implementation needs deterministic lineage.
- Do not compute `sha256` for `.env`, token, credential, MCP config, secret-like,
  or ignored paths.
- Do not store file contents in the index.
- Do not log sensitive substrings from paths or payloads.

Lineage behavior:

- Record the artifact path.
- Record `source_family`.
- Record parent artifact references when safely known, for example:
  - accepted manifest entry -> report artifact path;
  - bridge-aware review decision -> candidate source bridge;
  - official disclosure facts -> official disclosure candidate payload;
  - evidence pack -> provider candidates / official disclosure rows when
    explicitly referenced.
- Keep lineage as references, not copied fact values.
- Lineage cannot upgrade a row into a verified fact.

## 9. Safety Constraints

Mandatory safety constraints:

- Do not read `.env`.
- Do not read tokens.
- Do not read credential files.
- Do not read MCP config.
- Do not use the network.
- Do not call providers.
- Do not call live CNInfo.
- Do not call live Tushare.
- Do not parse PDF, DOCX, HTML, or Excel content.
- Do not modify `output/`.
- Do not modify `output/research_reports/accepted_manifest.json`.
- Do not generate fixtures.
- Do not promote fixtures.
- Do not generate reports.
- Do not generate runtime artifacts.
- Do not process unrelated mojibake untracked files.
- Do not use local artifact rows for trading advice.

Secret-like path exclusions should include filenames or path segments matching
patterns such as:

```text
.env
token
secret
credential
apikey
api_key
mcp
config/mcp
```

When a file is excluded by safety policy, the preferred state is `ignored` with
a generic caveat. The index should not disclose secret-like content.

## 10. Relationship To Phase 1 Schema

Phase 1 established the planning schema and safety validators for
`autonomous_ticker_research_planning_gate.v1`.

The Local Artifact Index should later provide rows that can be transformed into:

- `evidence_inventory`;
- `available_data_artifacts`;
- `missing_data_artifacts`.

Phase 2 must not bypass Phase 1 safety validators.

Phase 2 must not convert an artifact row directly into:

- a hypothesis;
- a verified fact;
- a report claim;
- a Research Report V1 section;
- an accepted manifest entry;
- a fixture.

Any future bridge from Local Artifact Index rows into the planning gate must
validate the full payload through the Phase 1 schema and safety layer before
downstream use.

## 11. Future Implementation Phases

Recommended phased implementation:

### Phase 2A: Local Artifact Index schema + pure path classifiers

- Define row schema / enum constants.
- Implement pure path and filename classifiers.
- Keep all functions side-effect free.
- No manifest reads yet.
- No repository-wide runtime scan.

### Phase 2B: Read-only manifest locator wrapper

- Read `accepted_manifest` through a narrow read-only wrapper.
- Return accepted report artifact path state.
- Never call manifest writers.
- Preserve manifest freshness as artifact metadata only.

### Phase 2C: Artifact row builder + SHA-256 helper

- Build rows from classifier results and filesystem metadata.
- Compute SHA-256 only for safe allowed paths.
- Record file size, modified time, caveats, and lineage refs.
- Fail closed for unreadable or unsafe files.

### Phase 2D: Ticker-scoped local index builder

- Build a ticker-scoped in-memory index.
- Prefer stock code filters.
- Return conflict / review_required for ambiguous identity.
- Return missing rows for expected local artifact families when useful.

### Phase 2E: Tests + fixture-free synthetic tempdir tests

- Add synthetic `tmp_path` tests.
- Do not depend on real `output/`.
- Do not write accepted manifest.
- Do not promote fixtures.

### Phase 2F: Retained 600406 / 300475 dry-run planning

- Plan a retained dry-run acceptance shape for `600406` and `300475`.
- Use dry-run inventory expectations only.
- Do not generate runtime artifacts without a later explicit approval.

## 12. Test Strategy

Tests should be introduced only in a later implementation phase, not in this
planning phase.

Required strategy:

- Use `tmp_path` synthetic files.
- Do not depend on real `output/`.
- Do not write or mutate the accepted manifest.
- Do not promote fixtures.
- Do not call providers.
- Do not use network.
- Do not parse PDF, DOCX, HTML, or Excel content.
- Test `unreadable`.
- Test `missing`.
- Test `stale`.
- Test `conflict_open`.
- Test `candidate_only`.
- Test `review_required`.
- Test secret-like paths and filenames are rejected or ignored.
- Test `.env` is rejected or ignored without hashing or reading content.
- Test token-like filenames are rejected or ignored without hashing or reading
  content.
- Test MCP config-like paths are rejected or ignored.
- Test unrelated mojibake / unclassifiable files are not auto-collected.
- Test `artifact existence != verified fact` by asserting no row exposes a
  verified-fact status or report-ready claim.
- Test accepted manifest current freshness does not become fact verification.

Suggested regression subset after implementation:

```text
tests/test_autonomous_ticker_research_schema.py
tests/test_autonomous_ticker_research_safety.py
future tests/test_local_artifact_index.py
```

Full suite can be run after the targeted subset passes and only when the user
approves implementation work.

## 13. Phase 2 Acceptance Checklist

Documentation planning acceptance:

- [ ] Only this Phase 2 planning document is added or updated.
- [ ] No production code is written.
- [ ] No tests are written.
- [ ] No runtime artifacts are generated.
- [ ] No network is used.
- [ ] No provider is called.
- [ ] No token or secret is read.
- [ ] No MCP config is read.
- [ ] No accepted manifest write is performed.
- [ ] No `output/` mutation is performed.
- [ ] No fixture generation or fixture promotion is performed.
- [ ] No verified fact promotion is performed.
- [ ] No Research Report V1 integration is performed.
- [ ] No hypothesis generator implementation is performed.
- [ ] No orchestrator implementation is performed.
- [ ] No live CNInfo / Tushare integration is performed.
- [ ] No unrelated mojibake files are processed.
- [ ] `git status --short` is reviewed before handoff.
- [ ] `git log --oneline -5` is reviewed before handoff.

Future implementation acceptance, when explicitly approved:

- [ ] Phase 2A path classifier tests pass.
- [ ] Phase 2B read-only manifest locator tests pass.
- [ ] Phase 2C row builder / SHA-256 helper tests pass.
- [ ] Phase 2D ticker-scoped builder tests pass.
- [ ] Synthetic tempdir tests cover missing / unreadable / stale / conflict /
  candidate_only / review_required.
- [ ] Secret-like path tests prove ignored behavior without content reads.
- [ ] Existing Phase 1 schema and safety tests still pass.
- [ ] Regression subset passes.
