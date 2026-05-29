# Phase 2B Read-only Manifest Locator Design / Implementation Plan

Date: 2026-05-30

Stage: Phase 2B Read-only Manifest Locator planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not update fixtures, does
not update any manifest, does not commit, and does not push.

## 1. Phase 2B Module Positioning

Phase 2B defines a read-only accepted manifest locator as a narrow helper layer
for the Local Artifact Index.

The future locator may inspect an accepted Research Report V1 manifest through a
strict read-only interface and emit only artifact-state / locator-state rows.
Its purpose is to describe where accepted report artifacts appear to be located,
which manifest entry selected them, and what artifact lineage state the manifest
claims.

Allowed outputs:

- manifest artifact-state rows;
- manifest locator rows;
- accepted report artifact reference state;
- missing / conflict / review-required locator state;
- caveats that preserve uncertainty;
- `not_for_trading_advice=true` on every row.

The locator must not validate new facts, generate report claims, or promote
manifest contents into evidence facts.

It is not:

- an accepted manifest writer;
- a manifest updater;
- fixture promotion;
- a verified fact store;
- Research Report V1 integration;
- a report generator;
- a candidate merger;
- a live provider connector;
- a live CNInfo connector;
- a live Tushare connector;
- a ticker-scoped full artifact index builder;
- a hypothesis generator;
- an orchestrator.

## 2. Input Boundaries

Phase 2B may design future read-only access to an accepted manifest, but this
planning stage must not actually read the retained runtime manifest at:

```text
output/research_reports/accepted_manifest.json
```

Future implementation input rules:

- The accepted manifest may be read only through a narrow read-only locator API.
- The manifest path must pass Phase 2A path safety checks before any read.
- Manifest payload validation must be shallow and schema-oriented.
- Manifest entry paths must pass Phase 2A path safety checks before becoming
  locator state.
- Report artifact contents must not be read by the manifest locator.
- Hash values recorded by the manifest may be compared only as artifact lineage
  state when a later implementation explicitly includes safe hash verification.

This stage and the Phase 2B locator design must not:

- read the real `output/research_reports/accepted_manifest.json`;
- scan the entire `output/` tree;
- read report artifact content;
- parse report JSON, Markdown, HTML, PDF, DOCX, XLSX, or CSV content;
- compute real report file SHA-256 in this planning stage;
- modify any manifest file;
- create or promote fixtures;
- create runtime artifacts.

## 3. Output Schema Draft

Recommended top-level locator schema version:

```text
read_only_manifest_locator_result.v1
```

Draft locator result:

```json
{
  "schema_version": "read_only_manifest_locator_result.v1",
  "manifest_path": "output/research_reports/accepted_manifest.json",
  "manifest_exists_status": "unknown",
  "manifest_schema_status": "not_checked",
  "manifest_entry_count": 0,
  "matched_entries": [],
  "unmatched_reason": "",
  "stock_code": "",
  "company_name": "",
  "report_artifact_refs": [],
  "freshness_status": "unknown",
  "lineage_refs": [],
  "caveats": [],
  "not_for_trading_advice": true
}
```

Field notes:

- `manifest_path`: normalized repo-relative accepted manifest path.
- `manifest_exists_status`: `exists`, `missing`, `unreadable`, `unknown`, or
  `not_checked`.
- `manifest_schema_status`: `valid`, `invalid_json`, `schema_mismatch`,
  `unreadable`, `not_checked`, or `review_required`.
- `manifest_entry_count`: number of manifest entries after schema validation;
  `0` when missing, unreadable, invalid, or not checked.
- `matched_entries`: list of manifest entry rows matching the requested
  `stock_code`, or review-required rows when identity is ambiguous.
- `unmatched_reason`: `missing`, `data_collection_required`,
  `unrelated_ticker`, `conflict_open`, `schema_mismatch`, `manifest_missing`,
  `manifest_unreadable`, or empty when matched.
- `stock_code`: requested or resolved six-digit code; code is the primary
  identity key.
- `company_name`: auxiliary label only; it must not confirm identity.
- `report_artifact_refs`: artifact references copied from accepted manifest
  entries as path state, not content facts.
- `freshness_status`: manifest freshness state preserved as artifact lineage
  state only.
- `lineage_refs`: manifest entry references and superseded/superseding artifact
  references when safely available.
- `caveats`: conservative warnings, including conflict, stale, missing, unsafe,
  hash mismatch, and non-fact-promotion warnings.
- `not_for_trading_advice`: always `true`.

Recommended status values:

```text
manifest_exists_status:
  exists
  missing
  unreadable
  unknown
  not_checked

manifest_schema_status:
  valid
  invalid_json
  schema_mismatch
  unreadable
  not_checked
  review_required

unmatched_reason:
  missing
  data_collection_required
  unrelated_ticker
  conflict_open
  schema_mismatch
  manifest_missing
  manifest_unreadable
  invalid_json
  duplicate_entries
  unsafe_path
  artifact_missing
  hash_mismatch
```

## 4. Manifest Entry Row Draft

Recommended manifest entry row schema version:

```text
manifest_locator_entry_row.v1
```

Draft manifest entry row:

```json
{
  "schema_version": "manifest_locator_entry_row.v1",
  "stock_code": "",
  "company_name": "",
  "artifact_path": "",
  "artifact_kind": "",
  "artifact_format": "",
  "accepted_status": "",
  "freshness_status": "unknown",
  "hash_status": "not_checked",
  "source_status": "review_required",
  "caveats": [],
  "not_for_trading_advice": true
}
```

Field notes:

- `stock_code`: primary identity key from the manifest entry.
- `company_name`: auxiliary identity label only.
- `artifact_path`: normalized repo-relative path from the manifest entry after
  path safety validation.
- `artifact_kind`: `research_report_v1`, `accepted_manifest`,
  `superseded_report_artifact`, `lineage_artifact`, or `unknown`.
- `artifact_format`: `json`, `markdown`, `html`, `manifest`, or `unknown`.
- `accepted_status`: `accepted`, `missing`, `stale`, `superseded`,
  `invalidated`, `conflict_open`, or `review_required`.
- `freshness_status`: copied from manifest freshness metadata as artifact
  lineage state only.
- `hash_status`: `match`, `mismatch`, `missing`, `not_checked`,
  `not_applicable`, or `review_required`.
- `source_status`: Phase 2A-compatible status such as `available`, `missing`,
  `partial`, `review_required`, `conflict_open`, `stale`, `invalidated`,
  `unreadable`, or `ignored`.
- `caveats`: warnings that prevent fact promotion and describe uncertainty.
- `not_for_trading_advice`: always `true`.

The future adapter from manifest entry rows to Local Artifact Index rows should
map each entry to `artifact_type=report_artifact_state` or
`artifact_type=accepted_manifest` only when the path classifier and row
validator accept it.

## 5. Critical Boundaries

Mandatory boundaries:

- Accepted manifest current does not mean new facts have been verified.
- Accepted report artifact path does not mean report content is a current fact.
- Manifest entry does not equal official disclosure fact.
- Manifest hash / freshness can only be artifact lineage state.
- Manifest locator must not turn report artifacts into evidence facts.
- Manifest locator must not infer verified facts from report JSON, Markdown, or
  HTML.
- Manifest locator must not parse report content to extract conclusions.
- Manifest locator must not convert accepted report references into
  hypothesis inputs.
- Manifest locator must not convert accepted report references into verified
  facts.
- Manifest locator must not generalize accepted status for `600406`, `002371`,
  or `002050` to any new ticker.
- A current manifest entry may support local artifact readiness planning only.
- Any downstream use must remain subject to Phase 1 schema and safety
  validators.

## 6. Relationship To Phase 2A

Phase 2A delivered Local Artifact Index schema and pure path classifiers. Phase
2B must build on that baseline without bypassing it.

Rules:

- Phase 2B future implementation should turn manifest locator rows into
  `local_artifact_index_row.v1` rows only through Phase 2A row builders and
  validators.
- Phase 2B must not bypass Phase 2A path safety.
- Phase 2B must not accept absolute paths, path traversal, URI paths,
  secret-like paths, MCP config paths, token paths, or mojibake/unrelated paths.
- Phase 2B must not bypass Phase 1 planning schema or safety validators.
- Phase 2B must not turn manifest rows into hypotheses.
- Phase 2B must not turn manifest rows into verified facts.
- Phase 2B must not enter ticker-scoped full artifact index building.
- Phase 2B must not scan all local artifacts.

The only allowed relationship is:

```text
read-only manifest locator row
  -> Phase 2A path safety
  -> Phase 2A local_artifact_index_row.v1 validation
  -> local artifact readiness state
```

There is no direct route from a manifest row to a Research Report V1 claim,
official disclosure fact, candidate merge, hypothesis, or trading advice.

## 7. Identity Matching

Identity matching must be conservative and code-first.

Rules:

- `stock_code` is the primary identity key.
- `company_name` is auxiliary only.
- Exact six-digit `stock_code` match is required for a confirmed manifest
  entry match.
- `company_name` may help explain or display a row, but cannot confirm identity
  by itself.
- If manifest `stock_code` and `company_name` conflict with the requested
  ticker identity, return `conflict_open` or `review_required`.
- If path-derived code and manifest entry code conflict, return
  `conflict_open`.
- If multiple manifest entries share the same `stock_code`, return
  `duplicate_entries` plus `review_required` unless the schema explicitly marks
  older entries as superseded.
- If multiple codes share a similar or identical `company_name`, return
  `conflict_open` for name-based lookup.
- Fuzzy company-name matching must not confirm identity.
- Aliases, abbreviations, English names, historical names, and mojibake names
  may be caveats only.
- A new ticker that is not in the manifest must return `missing` /
  `data_collection_required`; it must not fall back to similar accepted samples.
- Accepted status for `600406`, `002371`, or `002050` must not be copied to any
  other ticker.

## 8. Failure Modes

The design must cover these failure modes:

| Failure mode | Required locator state |
| --- | --- |
| Manifest missing | `manifest_exists_status=missing`, `unmatched_reason=manifest_missing`; no fallback to timestamp latest in Phase 2B. |
| Manifest unreadable | `manifest_exists_status=unreadable`, `manifest_schema_status=unreadable`, `source_status=unreadable`. |
| Manifest invalid JSON | `manifest_schema_status=invalid_json`, no entry rows emitted as accepted. |
| Schema mismatch | `manifest_schema_status=schema_mismatch`, `review_required`; do not infer paths from unknown shapes. |
| Stale entry | `freshness_status=stale`, `source_status=stale`, visible caveat; still not a fact. |
| Superseded entry | `freshness_status=superseded`, `accepted_status=superseded`, not usable as accepted baseline. |
| Invalidated entry | `freshness_status=invalidated`, `source_status=invalidated`, fail closed. |
| Artifact path unsafe | `unmatched_reason=unsafe_path`, `source_status=ignored`; do not reveal sensitive path details. |
| Artifact path missing | `source_status=missing`, `accepted_status=missing`, caveat that manifest points to absent artifact state. |
| Hash mismatch | `hash_status=mismatch`, `source_status=conflict_open` or `invalidated`; do not use as accepted. |
| Code/name conflict | `source_status=conflict_open`, `review_required`; code wins over name. |
| Duplicate entries | `unmatched_reason=duplicate_entries`, `review_required` unless supersession is explicit. |
| Unrelated ticker | `unmatched_reason=unrelated_ticker` or `data_collection_required`; no similar-sample fallback. |

Additional conservative handling:

- Missing hash metadata should produce `hash_status=missing` or `not_checked`,
  not failure unless the accepted policy requires hashes.
- Unknown freshness should be allowed only as artifact state with a caveat.
- Any unsafe, secret-like, or ignored path must stay outside hash and content
  reads.

## 9. Safety Constraints

Mandatory constraints for this planning stage and future Phase 2B
implementation:

- Do not read `.env`.
- Do not read tokens.
- Do not read credentials.
- Do not read MCP config.
- Do not use the network.
- Do not call providers.
- Do not call CNInfo.
- Do not call Tushare.
- Do not call AkShare.
- Do not modify `output/`.
- Do not modify `output/research_reports/accepted_manifest.json`.
- Do not write any manifest.
- Do not generate fixtures.
- Do not promote fixtures.
- Do not generate reports.
- Do not generate runtime artifacts.
- Do not process unrelated mojibake untracked files.
- Do not emit trading advice, target price, buy/sell action, position sizing,
  or portfolio allocation.

Secret-like path exclusions must remain inherited from Phase 2A and should
include `.env`, token, secret, credential, API key, private key, MCP, and
MCP-config-like path segments.

When a path is excluded by safety policy, the future locator should return a
generic ignored/review-required state and must not disclose file contents or
secret-like substrings.

## 10. Implementation Phasing Recommendation

Phase 2B should be implemented only after this planning document is accepted.

Recommended sequence:

### Phase 2B-1: Manifest locator schema + validators

- Define `read_only_manifest_locator_result.v1`.
- Define `manifest_locator_entry_row.v1`.
- Implement pure validators for schemas and status enums.
- Keep validators side-effect free.
- Reject downstream markers such as verified fact promotion, Research Report V1
  update, fixture promotion, trading advice, and provider primary switch.

### Phase 2B-2: Synthetic manifest parser using `tmp_path` only

- Parse synthetic accepted manifests from tests only.
- Use `tmp_path` synthetic files.
- Do not read real `output/research_reports/accepted_manifest.json`.
- Do not scan real `output/`.
- Do not read report artifacts.
- Return structured missing / invalid / schema mismatch states.

### Phase 2B-3: Manifest entry to artifact row adapter

- Convert valid manifest entry rows into Phase 2A
  `local_artifact_index_row.v1` rows.
- Use Phase 2A path safety and row validators.
- Map accepted report paths to artifact state only.
- Preserve freshness and hash status as lineage state only.
- Do not promote facts.

### Phase 2B-4: No-write / no-mutation tests

- Assert no manifest write calls.
- Assert no real output mutation.
- Assert no report content reads.
- Assert no provider, network, token, or MCP calls.
- Assert unsafe paths are ignored before hash or content checks.

### Phase 2B-5: Retained accepted-sample dry-run design

- Design a dry-run over retained accepted samples only after synthetic tests
  pass.
- Keep the dry-run read-only and no-mutation.
- Do not generalize `600406`, `002371`, or `002050` acceptance to other
  tickers.
- Do not update the real accepted manifest.
- Do not generate runtime artifacts.

## 11. Test Strategy

Tests are not written in this planning stage. Future Phase 2B tests must use
synthetic inputs.

Required strategy:

- Use `tmp_path` synthetic manifest files.
- Do not depend on real `output/research_reports/accepted_manifest.json`.
- Do not write the real accepted manifest.
- Do not read real report artifacts.
- Do not scan real `output/`.
- Do not generate runtime artifacts.
- Do not promote fixtures.
- Do not call providers.
- Do not use network.
- Do not read tokens or MCP config.

Required coverage:

- manifest missing;
- manifest unreadable;
- manifest invalid JSON;
- schema mismatch;
- stale entry;
- superseded entry;
- invalidated entry;
- conflict between requested code and manifest code;
- conflict between manifest code and path-derived code;
- duplicate entries;
- unrelated ticker;
- unsafe artifact path;
- missing artifact path;
- hash mismatch;
- missing hash metadata;
- unknown freshness;
- manifest current does not become verified fact;
- accepted report artifact path does not become current content fact;
- unknown ticker does not fall back to accepted samples;
- `600406`, `002371`, and `002050` accepted status is not generalized to a new
  ticker;
- `.env`, token, credential, MCP, absolute path, URI, and path traversal inputs
  are rejected or ignored without content reads or hashing;
- unrelated mojibake files are ignored.

Suggested future targeted tests:

```text
future tests/test_read_only_manifest_locator_schema.py
future tests/test_read_only_manifest_locator_parser.py
future tests/test_manifest_locator_to_local_artifact_index_adapter.py
```

Suggested regression subset after implementation:

```text
tests/test_autonomous_ticker_research_schema.py
tests/test_autonomous_ticker_research_safety.py
tests/test_local_artifact_index.py
future tests/test_read_only_manifest_locator_schema.py
future tests/test_read_only_manifest_locator_parser.py
future tests/test_manifest_locator_to_local_artifact_index_adapter.py
```

## 12. Phase 2B Acceptance Checklist

Documentation planning acceptance:

- [ ] Change scope is limited to this Phase 2B planning document.
- [ ] No production code is written.
- [ ] No tests are written.
- [ ] No runtime artifact is generated.
- [ ] No accepted manifest read is performed.
- [ ] No accepted manifest write is performed.
- [ ] No real `output/` scan is performed.
- [ ] No report content read is performed.
- [ ] No real report file SHA-256 is computed.
- [ ] No verified fact promotion is performed.
- [ ] No hypothesis generation is performed.
- [ ] No Research Report V1 integration is performed.
- [ ] No ticker-scoped full artifact index builder is implemented.
- [ ] No provider, CNInfo, Tushare, AkShare, network, token, or MCP work is
  performed.
- [ ] No fixture is generated or promoted.
- [ ] Unrelated mojibake untracked files are not processed.
- [ ] `git status --short` is reviewed before handoff.
- [ ] `git log --oneline -5` is reviewed before handoff.
- [ ] No commit is created.
- [ ] No push is performed.

Future implementation acceptance, only after explicit approval:

- [ ] Phase 2B-1 schema and validators pass targeted tests.
- [ ] Phase 2B-2 synthetic `tmp_path` parser tests pass.
- [ ] Phase 2B-3 adapter tests pass through Phase 2A row validation.
- [ ] Phase 2B-4 no-write / no-mutation tests pass.
- [ ] Phase 2B-5 retained accepted-sample dry-run design is accepted before
  any retained-sample run.
- [ ] Missing / unreadable / invalid JSON / stale / conflict / duplicate /
  unsafe path / hash mismatch coverage is present.
- [ ] Tests prove manifest current is not verified fact.
- [ ] Tests prove unknown ticker does not fall back to accepted samples.
- [ ] Existing Phase 1 schema and safety tests still pass.
- [ ] Existing Phase 2A Local Artifact Index tests still pass.
- [ ] Regression subset passes.
