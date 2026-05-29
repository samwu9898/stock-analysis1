# Phase 2B-2 Synthetic Manifest Parser Plan

Date: 2026-05-30

Stage: Phase 2B-2 Synthetic Manifest Parser planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not read report artifacts,
does not write manifests, does not commit, and does not push.

Reference baseline:

- Phase 2B-1 Manifest Locator Schema + Validators baseline:
  `2448a958611dd11c8ecf4453b5903229c3af826d`.
- Phase 2B-1 acceptance summary:
  `26e2611586c909700241753ee002f7edf7c4cad2`.

## 1. Phase 2B-2 Goal

Phase 2B-2 is the second small step for the Read-only Manifest Locator. It
plans a parser for synthetic manifests used by tests only.

The future parser should:

- parse only an explicitly provided synthetic manifest path created under
  pytest `tmp_path`;
- parse only synthetic JSON shaped for manifest locator tests;
- return Phase 2B-1 `manifest_locator_payload.v1` payloads;
- convert synthetic manifest entries into `manifest_entry_row.v1` rows;
- preserve artifact references as locator state only;
- fail closed on missing, unreadable, invalid, unsafe, duplicate, conflict, or
  marker-violating synthetic inputs;
- remain read-only and side-effect free except for reading the one explicitly
  provided synthetic JSON file.

Phase 2B-2 must not:

- read the real `output/research_reports/accepted_manifest.json`;
- scan the real `output/` tree;
- read real report artifact content;
- parse real report JSON, Markdown, HTML, PDF, DOCX, XLSX, or CSV content;
- write any manifest;
- update any manifest;
- generate runtime artifacts;
- generate fixtures;
- promote fixtures;
- create Local Artifact Index rows;
- promote verified facts;
- generate hypotheses;
- enter Research Report V1 integration;
- call providers, CNInfo, Tushare, AkShare, MCP, tokens, or network.

The parser is a synthetic-input bridge into the already accepted Phase 2B-1
schema and validator layer. It is not a real accepted manifest reader.

## 2. Expected Files

Future Phase 2B-2 implementation should continue using:

```text
src/fundamental_skill/research_planning/manifest_locator.py
tests/test_manifest_locator.py
```

Default file policy:

- Do not add a parser-specific production module.
- Do not modify any `__init__.py`.
- Do not modify Phase 2A `local_artifact_index.py`.
- Do not modify Phase 1 schema or safety modules.
- Do not add fixtures.
- Do not write `output/`.
- Do not touch the real accepted manifest.
- Do not process unrelated mojibake untracked files.

Keeping the parser in `manifest_locator.py` is preferred because Phase 2B-1
already owns the manifest locator schema constants, builders, validators, enum
sets, path safety delegation, and marker safety rules. A separate parser module
should be proposed only if a future implementation review finds that
`manifest_locator.py` is becoming materially hard to read or that parser IO
boundaries need an isolated import surface. That reason must be documented
before implementation.

Tests should remain in `tests/test_manifest_locator.py` by default so the
schema, validator, and synthetic parser contract remain visible in one targeted
test file. A separate parser test file should be proposed only if the file grows
too large or parser-specific monkeypatching would obscure existing validator
tests.

## 3. Synthetic Manifest Input Schema Draft

The synthetic manifest is a test-only JSON document created with `tmp_path`. It
is not the real accepted manifest and must not become a retained fixture.

Minimal top-level shape:

```json
{
  "schema_version": "synthetic_manifest_locator_input.v1",
  "generated_at": "2026-05-30T00:00:00Z",
  "entries": [],
  "not_for_trading_advice": true
}
```

Top-level field rules:

- `schema_version` must equal `synthetic_manifest_locator_input.v1`.
- `generated_at` must be a string. The parser should preserve it only as
  synthetic metadata or ignore it; it must not infer freshness facts from wall
  clock time.
- `entries` must be a list.
- `not_for_trading_advice` must be `true`.
- Unknown top-level fields should be rejected or ignored conservatively. If
  ignored, the parser should add a caveat and never treat them as facts.

Minimal entry shape:

```json
{
  "stock_code": "600406",
  "company_name": "NARI Technology",
  "artifacts": [
    {
      "artifact_path": "output/research_reports/synthetic/600406/fundamental_research_report_v1.json",
      "artifact_kind": "research_report_v1",
      "artifact_format": "json",
      "accepted_status": "accepted",
      "freshness_status": "current",
      "hash_status": "not_checked",
      "source_status": "available",
      "caveats": [
        "Synthetic test manifest locator state only."
      ],
      "not_for_trading_advice": true
    }
  ],
  "not_for_trading_advice": true
}
```

Entry field rules:

- `stock_code` must be a six-digit code when present.
- `company_name` is auxiliary only and cannot confirm identity by itself.
- Each entry may contain `artifacts` or `report_artifacts`. The two names should
  be aliases for the same synthetic artifact reference list. A single manifest
  entry should not contain both unless a future implementation explicitly
  defines merge precedence.
- `artifacts` / `report_artifacts` must be lists.
- Every artifact item must include `artifact_path`, `artifact_kind`,
  `artifact_format`, `accepted_status`, `freshness_status`, `hash_status`,
  `source_status`, `caveats`, and `not_for_trading_advice`.
- `not_for_trading_advice` must be `true` at top level, entry level, and
  artifact level.
- Artifact enum values must be legal Phase 2B-1 enum values.
- `artifact_path` must pass Phase 2A path safety as a path string, but the
  parser must not open that path.
- `caveats` must be a list.
- No entry or artifact field may contain forbidden downstream markers such as
  verified fact promotion, manifest update/write, fixture promotion, Research
  Report V1 update, provider primary switch, trading signal, target price, or
  portfolio allocation markers.

The synthetic manifest is allowed to describe accepted, stale, superseded,
invalidated, missing, conflict, and review-required states only as manifest
locator state. It cannot validate report content and cannot establish evidence
facts.

## 4. Parser Output Design

The parser output should remain the Phase 2B-1 payload:

```text
manifest_locator_payload.v1
```

Matched synthetic manifest artifacts should become:

```text
manifest_entry_row.v1
```

Output rules:

- Use `build_manifest_locator_payload` / `validate_manifest_locator_payload`
  for the final payload.
- Use `build_manifest_entry_row` / `validate_manifest_entry_row` for each
  matched artifact row.
- `manifest_entry_count` should count parsed synthetic manifest entries after
  top-level schema validation, not real artifacts on disk.
- `matched_entries` should contain only validated `manifest_entry_row.v1` rows
  for the requested exact `stock_code`.
- `report_artifact_refs` may contain safe synthetic artifact paths from matched
  rows, but only as path state.
- `freshness_status`, `hash_status`, `accepted_status`, and `source_status`
  remain locator / artifact lineage state only.
- `caveats` should make synthetic-only and non-fact-promotion boundaries
  explicit.
- `not_for_trading_advice` must be `true`.

The parser must not output:

- `local_artifact_index_row.v1`;
- evidence fact rows;
- candidate facts;
- verified facts;
- official disclosure facts;
- Research Report V1 payloads;
- hypotheses;
- orchestrator plans;
- provider requests;
- trading advice.

No manifest entry should be adapted into a Local Artifact Index row in Phase
2B-2. Manifest entry -> artifact row adapter work belongs to a later explicit
phase.

## 5. Parser Behavior Boundaries

The future parser should accept only an explicit synthetic manifest path.

Allowed behavior:

- receive the synthetic manifest path directly from a test;
- read only that one JSON file;
- parse JSON;
- validate the synthetic input shape;
- map synthetic artifacts into Phase 2B-1 manifest entry rows;
- return a Phase 2B-1 locator payload;
- return missing / invalid / unmatched / conflict states as validated payloads
  where possible.

Required boundaries:

- Do not search directories.
- Do not discover manifests.
- Do not fallback to `output/research_reports/accepted_manifest.json`.
- Do not fallback to retained accepted samples.
- Do not read paths named inside `artifact_path`.
- Do not check whether real artifacts exist.
- Do not compute real file hashes.
- Do not list `output/`.
- Do not write any files.
- Do not update input JSON.
- Do not write fixtures.
- Do not generate runtime artifacts.
- Do not read `.env`, tokens, credentials, MCP config, or provider config.

Synthetic manifest path handling:

- The path must be the exact path provided by the caller.
- A missing path should return a manifest-missing payload state rather than
  searching elsewhere.
- A directory path should be treated as unsafe or unreadable.
- Path traversal, URI-like paths, secret-like paths, provider config paths,
  MCP-like paths, and paths outside the test-owned synthetic location should be
  rejected.
- The parser may need an internal test-only path check for the concrete
  `tmp_path` file it opens. The emitted `manifest_path` in
  `manifest_locator_payload.v1` must still be a validator-safe locator string
  and must not leak sensitive absolute temp paths.

Artifact path handling:

- `artifact_path` is data only.
- The parser must validate `artifact_path` as a safe path string.
- The parser must not call `Path.exists()` on `artifact_path`.
- The parser must not open `artifact_path`.
- The parser must not hash `artifact_path`.
- Unsafe artifact paths should produce `unsafe_path`, `ignored`, or
  `review_required` state without reading content.

## 6. Identity Matching

Identity matching must be exact, conservative, and code-first.

Rules:

- `stock_code` is the primary identity key.
- `company_name` is auxiliary display / review context only.
- An exact six-digit `stock_code` match is required for a confirmed match.
- `company_name` alone cannot confirm identity.
- Unknown ticker should return missing / unmatched state.
- Code/name conflict should return conflict / review-required state.
- Duplicate entries for the same requested `stock_code` should return
  duplicate / review-required state unless explicit supersession is later
  designed and accepted.
- Fuzzy matching is not allowed.
- Alias matching is not allowed.
- Historical-name matching is not allowed.
- English-name matching is not allowed as proof.
- Mojibake name matching is not allowed.
- The parser must not fallback from `300475` to `600406`, `002371`, `002050`,
  or any other accepted sample.
- Accepted status for `600406`, `002371`, or `002050` must not be generalized
  to a new ticker.

Recommended output state examples:

- Exact code match with no conflict: `matched_entries` populated,
  `unmatched_reason=""`, `manifest_schema_status="valid"`.
- Unknown requested code: `matched_entries=[]`,
  `unmatched_reason="data_collection_required"` or `"missing"`.
- Requested code conflicts with entry name expectation: `source_status` or
  `unmatched_reason="conflict_open"` plus caveat.
- Name-only lookup: `review_required`; no confirmed match.
- Duplicate exact-code entries: `unmatched_reason="duplicate_entries"` and
  review-required caveat.

## 7. Failure Modes

The future parser should cover these failure modes without reading real output,
report artifacts, providers, tokens, or network.

| Failure mode | Required behavior |
| --- | --- |
| Synthetic manifest missing | Return `manifest_exists_status="missing"`, `manifest_schema_status="not_checked"` or `"review_required"`, `unmatched_reason="manifest_missing"`, no fallback. |
| Synthetic manifest unreadable | Return `manifest_exists_status="unreadable"`, `manifest_schema_status="unreadable"`, no fallback. |
| Invalid JSON | Return `manifest_schema_status="invalid_json"`, `unmatched_reason="invalid_json"`, no accepted rows. |
| Invalid `schema_version` | Return `manifest_schema_status="schema_mismatch"`, `unmatched_reason="schema_mismatch"`, no accepted rows. |
| `entries` missing | Return `schema_mismatch` / `review_required`; do not infer entries. |
| `entries` not list | Return `schema_mismatch` / `review_required`; do not iterate arbitrary objects. |
| Duplicate entries | Return `unmatched_reason="duplicate_entries"` and review-required caveat unless explicit supersession is later accepted. |
| Code/name conflict | Return conflict / review-required state; code remains primary. |
| Unsafe manifest path | Reject before reading when possible, or return unreadable / unsafe state without fallback. |
| Unsafe artifact path | Do not read artifact path; return `unsafe_path`, `ignored`, or review-required state. |
| Invalid enum | Return schema mismatch / review-required; do not coerce values. |
| `not_for_trading_advice=false` | Reject or return schema mismatch; do not produce accepted rows. |
| Marker violation | Reject with safety violation; do not emit fact-promoting rows. |
| Unknown ticker unmatched | Return missing / data collection required; no accepted-sample fallback. |

Additional fail-closed rules:

- If the parser cannot validate top-level synthetic manifest shape, it should
  return zero matched entries.
- If an individual artifact row is invalid, the parser should not silently
  repair it. It should return review-required or schema-mismatch state.
- Error messages should not reveal sensitive paths, token-like strings, hashes,
  or secret-like substrings.
- Parser exceptions should not trigger directory searches or fallback reads.

## 8. Safety Constraints

Phase 2B-2 planning and future implementation must enforce these constraints:

- Do not read `.env`.
- Do not read tokens.
- Do not read credentials.
- Do not read MCP config.
- Do not use network.
- Do not call providers.
- Do not call CNInfo.
- Do not call Tushare.
- Do not call AkShare.
- Do not scan `output/`.
- Do not modify `output/`.
- Do not modify accepted manifests.
- Do not write manifests.
- Do not generate fixtures.
- Do not promote fixtures.
- Do not generate reports.
- Do not generate runtime artifacts.
- Do not parse report content.
- Do not create Local Artifact Index rows.
- Do not promote verified facts.
- Do not generate hypotheses.
- Do not enter orchestrator work.
- Do not enter Research Report V1 integration.
- Do not process unrelated mojibake files.
- Do not emit trading advice, target prices, buy/sell actions, position sizing,
  or portfolio allocation.

The parser should preserve Phase 2B-1 marker safety. Synthetic inputs that
contain downstream intent markers must fail before any output row could be
treated as accepted evidence.

## 9. Tests Strategy

Tests are not written in this planning stage. Future Phase 2B-2 tests must use
only `tmp_path` synthetic manifests.

Required testing boundaries:

- Use `tmp_path` to create synthetic manifest JSON.
- Do not depend on the real `output/research_reports/accepted_manifest.json`.
- Do not read real `output/`.
- Do not read real report artifacts.
- Do not write the real accepted manifest.
- Do not write fixtures.
- Do not generate runtime artifacts.
- Do not call providers.
- Do not use network.
- Do not read tokens, `.env`, credentials, or MCP config.
- Do not process unrelated mojibake untracked files.

Required coverage:

- valid synthetic manifest;
- synthetic manifest missing;
- unreadable synthetic manifest, if portable in the test environment;
- invalid JSON;
- invalid schema version;
- missing `entries`;
- `entries` not list;
- invalid entry shape;
- invalid artifact enum;
- `not_for_trading_advice=false` at top level, entry level, and artifact level;
- unsafe synthetic manifest path;
- unsafe artifact path;
- duplicate entries;
- code/name conflict;
- unknown ticker does not fallback to accepted samples;
- `300475` does not fallback to `600406`, `002371`, or `002050`;
- parser performs no directory scan;
- parser performs no report artifact read;
- parser performs no file write;
- parser performs no provider, network, token, or MCP access;
- accepted/current synthetic state does not become verified fact;
- parser output validates as `manifest_locator_payload.v1`;
- matched artifacts validate as `manifest_entry_row.v1`;
- parser does not create `local_artifact_index_row.v1`.

Suggested future targeted command:

```text
python -m pytest tests/test_manifest_locator.py -p no:cacheprovider
```

Suggested future regression subset:

```text
python -m pytest tests/test_manifest_locator.py tests/test_local_artifact_index.py tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py -p no:cacheprovider
```

Tests should monkeypatch file and directory operations where useful to prove
that the parser opens only the explicit synthetic manifest path, never lists a
directory, never opens artifact paths, and never writes.

## 10. Phase 2B-2 Acceptance Checklist

Documentation planning acceptance:

- [ ] Only this Phase 2B-2 planning document is added.
- [ ] No production code is written.
- [ ] No tests are written.
- [ ] No runtime artifact is generated.
- [ ] No real accepted manifest is read.
- [ ] No real `output/` scan is performed.
- [ ] No report artifact content is read.
- [ ] No manifest is written or updated.
- [ ] No fixture is written or promoted.
- [ ] No provider, CNInfo, Tushare, AkShare, MCP, token, or network work is
  performed.
- [ ] No unrelated mojibake untracked files are processed.
- [ ] `git status --short` is reviewed before handoff.
- [ ] `git log --oneline -5` is reviewed before handoff.
- [ ] No commit is created.
- [ ] No push is performed.

Future Phase 2B-2 implementation acceptance, only after explicit approval:

- [ ] Modify only `src/fundamental_skill/research_planning/manifest_locator.py`
  and `tests/test_manifest_locator.py`, unless a separately justified file
  change is accepted.
- [ ] Keep default no parser-specific module.
- [ ] Keep default no `__init__.py` change.
- [ ] Parse only explicit `tmp_path` synthetic manifest JSON.
- [ ] No real manifest read.
- [ ] No output scan.
- [ ] No report artifact read.
- [ ] No manifest write.
- [ ] No runtime artifact generation.
- [ ] No artifact row adapter.
- [ ] No Local Artifact Index row creation.
- [ ] No verified fact promotion.
- [ ] No hypothesis generation.
- [ ] No Research Report V1 integration.
- [ ] No provider, CNInfo, Tushare, AkShare, MCP, token, or network calls.
- [ ] Valid synthetic manifest test passes.
- [ ] Missing / invalid JSON / invalid schema / entries-not-list tests pass.
- [ ] Unsafe manifest and artifact path tests pass.
- [ ] Unknown ticker no-fallback test passes.
- [ ] Duplicate and conflict tests pass.
- [ ] No directory scan / no report artifact read / no file write tests pass.
- [ ] Targeted `tests/test_manifest_locator.py` passes.
- [ ] Regression subset passes.

Phase 2B-2 should move to implementation only after this planning document is
accepted in a separate review step.
