# Phase 2B-3 Manifest Entry To Artifact Row Adapter Plan

Date: 2026-05-30

Stage: Phase 2B-3 Manifest Entry to Artifact Row Adapter planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not read report artifacts,
does not write manifests, does not write fixtures, does not commit, and does
not push.

Reference baseline:

- Phase 2B-2 Synthetic Manifest Parser baseline:
  `b205e02e824c0566eb67a5d501b186542493168e`.
- Phase 2B-2 acceptance summary:
  `53598b2a87b00d2dd55b56cda75bea257bfc1472`.

## 1. Phase 2B-3 Goal

Phase 2B-3 is the narrow adapter layer between the Read-only Manifest Locator
and the Local Artifact Index. It plans one future conversion:

```text
manifest_entry_row.v1 -> local_artifact_index_row.v1
```

The adapter should:

- accept only an already validated `manifest_entry_row.v1`;
- convert that locator row into one `local_artifact_index_row.v1`;
- validate the output with `validate_artifact_row`;
- preserve manifest state as artifact inventory / artifact-state only;
- record lineage back to the manifest locator source;
- preserve caveats and append an explicit non-fact-promotion caveat;
- keep `not_for_trading_advice=true`.

Phase 2B-3 must not:

- read manifest files;
- read report artifacts;
- inspect report JSON, Markdown, HTML, PDF, DOCX, XLSX, or CSV content;
- check whether `artifact_path` exists;
- compute a real file hash;
- write `output/`;
- write a manifest;
- write fixtures;
- generate reports;
- generate runtime artifacts;
- output verified facts;
- output evidence facts;
- generate hypotheses;
- enter a ticker-scoped full index builder;
- enter an orchestrator;
- enter Research Report V1 integration;
- connect live providers, CNInfo, Tushare, AkShare, MCP, tokens, or network.

The output row is local artifact state. It is not a verified fact, evidence
fact, accepted report claim, hypothesis, or Research Report V1 input.

## 2. Expected Files

Future Phase 2B-3 implementation should default to the existing files:

```text
src/fundamental_skill/research_planning/manifest_locator.py
tests/test_manifest_locator.py
```

Default file policy:

- Prefer adding the adapter function to `manifest_locator.py`.
- Keep adapter tests in `tests/test_manifest_locator.py`.
- Do not modify any `__init__.py`.
- Do not modify real manifests.
- Do not modify `output/`.
- Do not add fixtures.
- Do not process unrelated mojibake untracked files.

Rationale for reusing `manifest_locator.py`:

- Phase 2B already owns `manifest_entry_row.v1` constants and validation.
- Phase 2B already delegates path safety to Phase 2A.
- The adapter is a direct continuation of manifest locator state, not a new
  reader or builder subsystem.
- Keeping it colocated makes the `manifest_entry_row.v1` boundary visible next
  to the conversion code.

A tiny adapter module may be proposed only if implementation review finds a
clear reason, such as:

- `manifest_locator.py` becomes materially hard to read;
- the adapter needs a deliberately small import surface for dependency control;
- local project conventions strongly favor separating cross-schema adapters.

If a separate module is proposed, the implementation plan must name it
explicitly and justify why reuse of `manifest_locator.py` is insufficient.
Default remains: no new adapter module and no `__init__.py` change.

## 3. Adapter Input

The adapter input is one `manifest_entry_row.v1` dictionary.

Required input rules:

- The caller must pass a row that has already passed
  `validate_manifest_entry_row`.
- The adapter should call `validate_manifest_entry_row` again defensively and
  use the returned defensive copy.
- Raw manifest dictionaries are not accepted.
- Synthetic manifest top-level dictionaries are not accepted.
- Real accepted manifest dictionaries are not accepted.
- Unvalidated entries are not accepted.
- Lists of entries are not accepted by the single-row adapter.
- The adapter must not open, search for, or parse any manifest file.

The adapter should treat `stock_code` as the primary identity field and
`company_name` as auxiliary context only. Name-only identity must remain
review-required or caveated state and cannot confirm ticker identity.

## 4. Adapter Output

The adapter output is one `local_artifact_index_row.v1` dictionary.

Required output rules:

- Build a Local Artifact Index row with the Phase 2A builder or an equivalent
  dict path that is then validated.
- Always pass the result through `validate_artifact_row`.
- Use conservative mappings for `source_family`, `artifact_type`,
  `source_status`, `review_status`, and `freshness_status`.
- Set `not_for_trading_advice=true`.
- Preserve manifest caveats.
- Append a caveat such as:
  `Manifest locator state only; not a verified fact.`
- Record manifest locator lineage in `lineage_refs`.
- Leave `created_at`, `modified_at`, `data_period`, `sha256`, and `file_size`
  empty / zero unless provided by the validated manifest entry row in a future
  explicitly approved schema. The adapter must not compute or read them.
- Keep `sha256=""` unless a validated manifest-state field is later designed.
  `hash_status=match` is not permission to compute or emit a real file hash.

The output must not contain:

- `verified_fact`;
- `auto_verified`;
- evidence fact schema markers;
- accepted report fact markers;
- Research Report V1 section markers;
- trading advice markers;
- target prices;
- position sizing;
- portfolio allocation.

## 5. Mapping Rules

Recommended field mapping:

| Manifest entry field | Artifact row field | Rule |
| --- | --- | --- |
| `stock_code` | `stock_code` | Copy after `validate_manifest_entry_row`; must remain six-digit or empty per validator. |
| `company_name` | `company_name` | Copy as auxiliary label only; never use as identity proof. |
| `artifact_path` | `artifact_path` | Copy validated safe path string; do not check existence, open, hash, or parse. |
| `artifact_kind` | `artifact_type` | Map conservatively to Phase 2A artifact types; unknown or unsupported kinds become review-required / ignored only if the resulting row validates. |
| `artifact_format` | `caveats` or future metadata | Preserve as caveat or lineage detail because `local_artifact_index_row.v1` has no dedicated format field. Do not infer content facts from format. |
| `accepted_status` | `source_status` / `review_status` | Map conservatively; accepted/current remains artifact-state and never becomes verified. |
| `freshness_status` | `freshness_status` | Copy only if legal in Phase 2A; otherwise reject. |
| `hash_status` | `caveats` / `lineage_refs` | Preserve status as manifest hash state only; do not compute or emit real `sha256`. |
| `source_status` | `source_status` | Map through legal Phase 2A status values; downgrade to review-required for conflict or unsafe states. |
| `caveats` | `caveats` | Preserve list and append adapter boundary caveat. |
| `not_for_trading_advice` | `not_for_trading_advice` | Must remain `true`; false is rejected. |

Recommended `artifact_kind -> artifact_type / source_family` mapping:

| `artifact_kind` | `artifact_type` | `source_family` | Notes |
| --- | --- | --- | --- |
| `accepted_manifest` | `accepted_manifest` | `accepted_manifest` | Manifest state only; never a manifest writer. |
| `research_report_v1` | `report_artifact_state` | `research_report_v1` | Report artifact path state only; do not read content. |
| `superseded_report_artifact` | `report_artifact_state` | `research_report_v1` | Preserve stale / superseded caveat. |
| `lineage_artifact` | `existing_local_report_artifact` | `existing_local_reports` | Lineage reference state only; no content read. |
| `unknown` | `ignored` or reject | `ignored` | Prefer reject or review-required behavior; do not promote. |

Recommended `accepted_status -> source_status / review_status` mapping:

| `accepted_status` | `source_status` | `review_status` | Notes |
| --- | --- | --- | --- |
| `accepted` | `available` if source allows, else `review_required` | `unknown` or `review_required` | Accepted manifest state only, not verified fact. |
| `missing` | `missing` | `review_required` | Do not check path existence. |
| `stale` | `stale` | `review_required` | Preserve stale caveat. |
| `superseded` | `stale` | `review_required` | Freshness may be `superseded`. |
| `invalidated` | `invalidated` | `invalidated` | No downstream fact use. |
| `conflict_open` | `conflict_open` | `conflict_open` | Requires review. |
| `review_required` | `review_required` | `review_required` | No promotion. |
| `unknown` | `review_required` | `review_required` | Fail closed. |

Recommended `source_status` handling:

- If manifest `source_status` is `available` and `accepted_status=accepted`,
  output may use `source_status=available`, with caveats that it remains
  artifact state only.
- If either status indicates `missing`, `stale`, `invalidated`,
  `conflict_open`, `unreadable`, `ignored`, or `review_required`, preserve or
  downgrade to the more conservative Phase 2A status.
- Never upgrade `candidate_only`, `review_required`, `conflict_open`, stale, or
  invalidated state into `available`.

Recommended lineage refs:

```text
manifest_locator:manifest_entry_row.v1
manifest_locator:artifact_kind=<artifact_kind>
manifest_locator:accepted_status=<accepted_status>
manifest_locator:freshness_status=<freshness_status>
manifest_locator:hash_status=<hash_status>
manifest_locator:source_status=<source_status>
manifest_locator:artifact_path=<artifact_path>
```

Lineage refs are references to locator state, not copied report facts.

## 6. Key Boundaries

Mandatory semantic boundaries:

- `accepted_status=current` does not exist as a verified fact marker.
- `freshness_status=current` does not mean a report claim is current fact.
- `accepted_status=accepted` does not mean verified fact.
- `accepted_status=accepted` plus `freshness_status=current` still means only
  manifest artifact state.
- A manifest artifact path does not prove report content is current fact.
- Adapter output is an artifact-state row, not an evidence fact.
- Adapter output is not an evidence inventory fact for Phase 1.
- The adapter does not read report artifact content.
- The adapter does not convert report artifact content into evidence inventory
  facts.
- The adapter does not create candidate facts, official disclosure facts,
  verified facts, hypotheses, or report sections.
- Accepted sample status for `600406`, `002371`, or `002050` must not be
  generalized to a new ticker.
- Unknown ticker must not fallback to `600406`, `002371`, `002050`, or any
  retained sample.
- Name-only matching must not resolve identity.
- Fuzzy matching, alias matching, historical-name matching, and mojibake-name
  matching are not allowed.
- The adapter cannot write accepted manifests or update manifest state.

The adapter is allowed to preserve artifact location and manifest state for
future inventory / readiness planning only.

## 7. Failure Modes

The future adapter should fail closed on these cases:

| Failure mode | Required behavior |
| --- | --- |
| Invalid manifest entry row | Reject before conversion; no artifact row emitted. |
| Unvalidated raw manifest dict | Reject; caller must pass `manifest_entry_row.v1`. |
| Unsafe `artifact_path` | Reject through `validate_manifest_entry_row` / path safety; do not read path. |
| Missing `artifact_path` | Reject for adapter conversion unless a later explicit missing-row design is accepted. |
| Invalid enum | Reject; do not coerce unknown enum values. |
| `not_for_trading_advice=false` | Reject; no row emitted. |
| Accepted/current marker tries verified fact | Reject if any field or caveat contains verified-fact markers. |
| Code/name conflict | Emit conflict / review-required only if identity conflict is represented in legal validated input; otherwise reject. |
| Unknown `artifact_kind` | Reject or map only to `ignored` with review-required caveat; never promote. |
| Forbidden marker violation | Reject through marker safety; no row emitted. |
| `lineage_refs` type errors | Reject before validating artifact row. |
| `caveats` type errors | Reject before validating artifact row. |
| Phase 2A artifact row validation failure | Reject and surface a generic schema conversion error without reading files. |

Additional failure policy:

- Do not silently repair unsafe paths.
- Do not infer a stock code from path if `stock_code` is absent or conflicting.
- Do not infer company identity from `company_name`.
- Do not emit a row that fails `validate_artifact_row`.
- Do not downgrade a marker violation into a caveat and continue.
- Error messages should avoid leaking sensitive paths, tokens, hashes, or
  secret-like substrings.

## 8. Safety Constraints

Phase 2B-3 planning and future implementation must enforce these constraints:

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
- Do not read report artifacts.
- Do not modify `output/`.
- Do not modify accepted manifests.
- Do not write manifests.
- Do not write fixtures.
- Do not promote fixtures.
- Do not generate reports.
- Do not generate runtime artifacts.
- Do not compute real file hashes.
- Do not check artifact existence.
- Do not enter ticker-scoped full index builder work.
- Do not enter hypothesis generator work.
- Do not enter orchestrator work.
- Do not enter Research Report V1 integration.
- Do not process unrelated mojibake files.
- Do not emit trading advice, target prices, buy/sell actions, position sizing,
  or portfolio allocation.

## 9. Tests Strategy

Tests are not written in this planning stage. Future Phase 2B-3 tests must use
pure dictionaries and strings.

Required testing boundaries:

- Do not depend on the real accepted manifest.
- Do not depend on real `output/`.
- Do not read real report artifacts.
- Do not write real manifests.
- Do not write fixtures.
- Do not generate runtime artifacts.
- Do not call providers.
- Do not use network.
- Do not read tokens, `.env`, credentials, or MCP config.
- Do not process unrelated mojibake untracked files.

Required future coverage:

- valid `manifest_entry_row.v1` converts to `local_artifact_index_row.v1`;
- output passes `validate_artifact_row`;
- `accepted` / `current` remains artifact-state only;
- invalid manifest entry is rejected;
- unvalidated raw dict is rejected;
- unsafe path is rejected;
- missing `artifact_path` is rejected or represented only by an explicitly
  accepted future missing-row design;
- forbidden markers are rejected;
- caveats are preserved and adapter caveat is appended;
- manifest locator lineage refs are preserved or appended;
- `hash_status` is preserved as manifest state without computing `sha256`;
- unknown ticker has no fallback to `600406`, `002371`, or `002050`;
- code/name conflict remains conflict / review-required;
- no file IO;
- no directory scan;
- no report artifact read;
- no file write;
- no real manifest read;
- no output scan.

Suggested future targeted command:

```text
python -m pytest tests/test_manifest_locator.py -p no:cacheprovider
```

Suggested future regression subset:

```text
python -m pytest tests/test_manifest_locator.py tests/test_local_artifact_index.py tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py -p no:cacheprovider
```

Tests should monkeypatch `open`, directory listing APIs, and filesystem stat /
hash helpers where useful to prove that the adapter performs no file IO, no
report artifact reads, no output scans, no writes, and no hash computation.

## 10. Phase 2B-3 Acceptance Checklist

Documentation planning acceptance:

- [ ] Only this Phase 2B-3 planning document is added.
- [ ] No production code is written.
- [ ] No tests are written.
- [ ] No runtime artifact is generated.
- [ ] No real accepted manifest is read.
- [ ] No `output/` scan is performed.
- [ ] No report artifact content is read.
- [ ] No manifest is written or updated.
- [ ] No output file is written.
- [ ] No fixture is written or promoted.
- [ ] No file hash is computed.
- [ ] No provider, CNInfo, Tushare, AkShare, MCP, token, or network work is
  performed.
- [ ] No verified fact promotion is performed.
- [ ] No hypothesis generator, orchestrator, ticker-scoped full index builder,
  or Research Report V1 integration work is performed.
- [ ] No unrelated mojibake untracked files are processed.
- [ ] `git status --short` is reviewed before handoff.
- [ ] `git log --oneline -5` is reviewed before handoff.
- [ ] No commit is created.
- [ ] No push is performed.

Future Phase 2B-3 implementation acceptance, only after explicit approval:

- [ ] Modify only `src/fundamental_skill/research_planning/manifest_locator.py`
  and `tests/test_manifest_locator.py`, unless a separately justified tiny
  adapter module is accepted.
- [ ] Keep default no `__init__.py` change.
- [ ] Adapter accepts only validated `manifest_entry_row.v1`.
- [ ] Adapter rejects raw manifest dicts and unvalidated entries.
- [ ] Adapter outputs only `local_artifact_index_row.v1`.
- [ ] Adapter output passes `validate_artifact_row`.
- [ ] `source_family`, `artifact_type`, `source_status`, `review_status`, and
  `freshness_status` are mapped conservatively.
- [ ] `not_for_trading_advice=true` is enforced.
- [ ] Manifest caveats are preserved.
- [ ] Manifest locator lineage refs are recorded.
- [ ] Adapter caveat says locator state only / not verified fact.
- [ ] No real manifest read.
- [ ] No output scan.
- [ ] No report artifact read.
- [ ] No manifest, output, fixture, or runtime artifact write.
- [ ] No artifact existence check.
- [ ] No real file hash computation.
- [ ] No verified fact, evidence fact, candidate fact, or hypothesis promotion.
- [ ] Valid conversion test passes.
- [ ] Invalid entry, unsafe path, forbidden marker, policy false, conflict, and
  unknown ticker no-fallback tests pass.
- [ ] No file IO / no report artifact read / no write tests pass.
- [ ] Targeted `tests/test_manifest_locator.py` passes.
- [ ] Regression subset passes.

Phase 2B-3 should move to implementation only after this planning document is
accepted in a separate review step.
