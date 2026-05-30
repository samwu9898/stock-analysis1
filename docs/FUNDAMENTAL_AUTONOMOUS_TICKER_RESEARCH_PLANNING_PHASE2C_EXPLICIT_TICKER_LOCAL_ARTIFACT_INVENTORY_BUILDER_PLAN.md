# Phase 2C Explicit-Input Ticker-Scoped Local Artifact Inventory Builder Plan

Date: 2026-05-30

Stage: Phase 2C Explicit-input ticker-scoped local artifact inventory builder
planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not read report artifacts,
does not write manifests, does not write output files, does not write fixtures,
does not commit, and does not push.

Reference baseline:

- Phase 2B-4 No-write / No-mutation Tests baseline:
  `997cc5da14a9d8ff9bc48d549effa95e318380e4`.
- Phase 2B-4 acceptance summary:
  `aa1e2745e633da6471dcaaae3e194d2c3d47a1bf`.

## 1. Phase 2C Goal

Phase 2C plans a narrow explicit-input builder for a ticker-scoped local
artifact inventory payload.

The future builder should only assemble inventory state from caller-supplied,
already explicit inputs:

- a six-digit `stock_code`;
- an optional `company_name` hint;
- explicit artifact path strings;
- optional validated `manifest_locator_payload.v1`;
- optional validated `manifest_entry_row.v1` rows;
- optional validated `local_artifact_index_row.v1` rows.

The Phase 2C builder is an inventory builder. It must remain artifact-state
only and must not become a discovery engine, fact reader, or report integration
layer.

Phase 2C plans only:

- explicit-input ticker-scoped inventory assembly;
- conservative validation and conflict handling for supplied rows;
- output grouping into available, missing, ignored, and conflict artifact
  buckets;
- lineage references to the supplied input row types;
- non-trading-advice and non-fact-promotion boundaries.

Phase 2C does not plan:

- real `output/` scanning;
- real accepted manifest reading;
- report artifact content reading;
- live provider integration;
- hypothesis generation;
- orchestrator integration;
- Research Report V1 integration;
- Dashboard / Batch work;
- fixture promotion.

The future implementation should start only after this planning document is
accepted in a separate review step.

## 2. Input Design

The future builder should accept a single explicit request dictionary or a
small typed equivalent. The planned input schema is:

```json
{
  "schema_version": "ticker_local_artifact_inventory_request.v1",
  "stock_code": "600406",
  "company_name": "optional auxiliary name hint",
  "artifact_paths": [
    "output/example/path/from/caller.json"
  ],
  "manifest_locator_payload": {},
  "manifest_entry_rows": [],
  "artifact_rows": [],
  "not_for_trading_advice": true
}
```

Input field rules:

- `stock_code`: required primary identity key. It must be exactly six digits.
- `company_name`: optional auxiliary hint only. It cannot independently resolve
  ticker identity.
- `artifact_paths`: optional caller-supplied path strings. Each path must pass
  Phase 2A path safety before it can be represented as an artifact-state row.
- `manifest_locator_payload`: optional, already validated
  `manifest_locator_payload.v1`. It is supplied by the caller; Phase 2C must not
  read a real manifest file to obtain it.
- `manifest_entry_rows`: optional list of already validated or defensively
  revalidated `manifest_entry_row.v1` dictionaries.
- `artifact_rows`: optional list of already validated or defensively
  revalidated `local_artifact_index_row.v1` dictionaries.
- `not_for_trading_advice`: required and must be `true`.

Accepted input sources are explicit objects and strings only. The builder must
not derive inputs by reading project state, scanning directories, opening report
artifacts, calling providers, reading tokens, or connecting to networked
systems.

Rejected input sources:

- raw real accepted manifest dictionaries;
- raw `output/` scan results;
- report artifact content or parsed report sections;
- full repository discovery results;
- live provider responses;
- generated hypotheses;
- Research Report V1 section payloads.

Recommended adapter paths:

| Explicit input | Planned handling |
| --- | --- |
| `artifact_paths` | Validate path safety, derive path-state rows with unknown / review-required metadata, and never check existence. |
| `manifest_locator_payload.v1` | Defensively validate and use only its supplied rows / state; do not read real manifest files. |
| `manifest_entry_row.v1` | Defensively validate with `validate_manifest_entry_row`, adapt through the existing manifest-entry adapter behavior, then validate artifact rows. |
| `local_artifact_index_row.v1` | Defensively validate with `validate_artifact_row`, filter by exact ticker, and preserve artifact-state caveats. |

All adapters should return defensive copies. Caller-owned dictionaries and lists
must not be mutated.

## 3. Output Design

The future output should be a ticker-scoped artifact inventory payload:

```json
{
  "schema_version": "ticker_local_artifact_inventory.v1",
  "stock_code": "600406",
  "company_name": "optional auxiliary name hint",
  "identity_resolution_status": "exact_code_match",
  "artifact_rows": [],
  "available_data_artifacts": [],
  "missing_data_artifacts": [],
  "ignored_artifacts": [],
  "conflict_artifacts": [],
  "caveats": [],
  "lineage_refs": [],
  "not_for_trading_advice": true
}
```

Required output fields:

- `schema_version`: planned value `ticker_local_artifact_inventory.v1`.
- `stock_code`: the exact six-digit ticker requested by the caller.
- `company_name`: the caller-supplied auxiliary hint or a conservative value
  copied from matching explicit rows when non-conflicting.
- `identity_resolution_status`: exact-code result or conservative conflict /
  review state.
- `artifact_rows`: normalized artifact-state rows that apply to the requested
  ticker.
- `available_data_artifacts`: rows whose validated `source_status` indicates
  caller-supplied artifact state is available.
- `missing_data_artifacts`: rows whose validated `source_status` indicates
  missing state. Phase 2C must not create real missing rows from filesystem
  discovery.
- `ignored_artifacts`: supplied paths or rows ignored because they are unsafe,
  unrelated, mismatched, unknown, or outside allowed artifact-state boundaries.
- `conflict_artifacts`: supplied paths or rows with ticker, company, duplicate,
  status, or schema conflicts.
- `caveats`: inventory-level caveats, including non-fact-promotion caveats.
- `lineage_refs`: references to explicit input row types, not copied content
  facts.
- `not_for_trading_advice`: always `true`.

Recommended `identity_resolution_status` values:

```text
exact_code_match
review_required
conflict_open
invalid
no_artifacts_available
```

Bucket rules:

- `available_data_artifacts` means only that explicit validated artifact state
  says the artifact row is available. It does not mean file content was read,
  facts were verified, or report claims are ready.
- `missing_data_artifacts` can only reflect explicit supplied missing state. The
  builder must not check paths to discover missing files.
- `ignored_artifacts` should retain generic caveats without leaking secret-like
  path content.
- `conflict_artifacts` should preserve enough row lineage for review while
  avoiding content reads or fact promotion.

## 4. Key Boundaries

Mandatory semantic boundaries:

- An artifact inventory is not an evidence fact.
- An artifact row is not a verified fact.
- A manifest-derived row is still only artifact-state.
- `accepted` does not mean a fact was verified.
- `current` does not mean a fact was verified.
- An output path existing in a supplied row does not mean the content is
  trustworthy.
- The builder does not read artifact content.
- The builder does not read report JSON, Markdown, HTML, PDF, DOCX, XLSX, CSV,
  or any other report artifact content.
- The builder does not generate candidate facts, official disclosure facts,
  verified facts, hypotheses, report claims, or Research Report V1 sections.
- The builder does not enter Research Report V1.
- The builder does not upgrade manifest freshness, accepted state, hash state,
  or review state into verified facts.
- The builder does not use local artifact rows for trading advice.

The only planned use is inventory / readiness planning from explicitly supplied
artifact-state inputs.

## 5. Input Validation

Required validation rules:

- `stock_code` must be a string of exactly six digits.
- `company_name` is auxiliary. It cannot confirm identity by itself.
- Every explicit artifact path must pass Phase 2A path safety before it can be
  represented in output.
- A supplied manifest payload must pass Phase 2B-1 / Phase 2B-2 validators.
- Every supplied manifest entry must pass `validate_manifest_entry_row`.
- Every supplied artifact row must pass `validate_artifact_row`.
- `not_for_trading_advice` must be `true` at request, row, and output levels.
- Unknown or mismatched stock codes must become `conflict_open` or `ignored`,
  depending on whether the row is relevant enough to review.
- Duplicate `artifact_id` values must be detected and marked conflict unless
  the duplicated rows are byte-for-byte equivalent explicit state.
- Duplicate `artifact_path` values must be detected and marked conflict when
  metadata differs.
- Fuzzy matching is not allowed.
- Company-name-only matching is not allowed.
- Alias matching, historical-name matching, English-name matching, and mojibake
  name matching are not allowed.
- There is no fallback to retained samples or known tickers such as `600406`,
  `002371`, or `002050`.

Defensive validation should return copied data structures. The original request,
manifest payload, manifest entry rows, artifact rows, caveats, and lineage refs
must remain unmodified.

## 6. Behavior Boundaries

Phase 2C planning and future implementation must enforce these behavior
boundaries:

- Do not search directories.
- Do not use `glob`, `rglob`, or `os.walk`.
- Do not read the real accepted manifest.
- Do not read report artifacts.
- Do not inspect report artifact content.
- Do not check whether `artifact_path` exists.
- Do not call `Path.exists`, `Path.stat`, or equivalent existence / metadata
  probes for artifact paths.
- Do not compute real file hashes.
- Do not write any files.
- Do not write manifests.
- Do not write under `output/`.
- Do not write fixtures.
- Do not generate runtime artifacts.
- Do not modify input objects.
- Do not stage changes.
- Do not commit.
- Do not push.
- Do not call live CNInfo, Tushare, AkShare, or any provider.
- Do not use the network.
- Do not read tokens, credentials, `.env`, or MCP configuration.
- Do not process unrelated mojibake untracked files.
- Do not enter hypothesis generator, orchestrator, Dashboard / Batch, or
  Research Report V1 integration work.

The builder may inspect only the explicit in-memory values passed by the caller
and, where a later test requires it, synthetic `tmp_path` inputs explicitly
constructed for tests.

## 7. Failure Modes

The future builder should fail closed or return conservative conflict / ignored
state for these cases:

| Failure mode | Required behavior |
| --- | --- |
| Invalid `stock_code` | Reject request before inventory assembly; no fallback ticker. |
| `company_name` conflict | Mark `identity_resolution_status=conflict_open`; place affected rows in `conflict_artifacts`. |
| Unsafe artifact path | Ignore or reject the supplied path through Phase 2A safety; do not read it. |
| Invalid manifest payload | Reject that payload; do not attempt real manifest reads. |
| Invalid manifest entry | Reject that row; no artifact row emitted from it. |
| Invalid artifact row | Reject that row; do not repair it by reading files. |
| Duplicate `artifact_id` | Mark conflict unless explicit rows are identical and safe to deduplicate. |
| Duplicate path | Mark conflict when row metadata differs; do not check filesystem identity. |
| Mismatched ticker | Mark row `conflict_open` or `ignored`; never coerce to requested ticker. |
| All artifacts ignored | Return inventory with `identity_resolution_status=no_artifacts_available` or `review_required` and caveats. |
| No artifacts available | Return a valid empty inventory with caveats; do not scan `output/` to fill gaps. |
| Forbidden marker violation | Reject the row or request; do not downgrade verified-fact markers into caveats. |
| `not_for_trading_advice=false` | Reject request or row; no inventory output that claims trading advice. |
| Missing required schema version | Reject or mark invalid according to the relevant validator. |
| Unknown row schema | Ignore or mark review-required; never promote to available. |
| Mixed accepted/current status tries fact promotion | Reject through safety marker validation. |

Failure messages should be specific enough for review but should not leak
tokens, credentials, secret-like path fragments, or artifact content.

## 8. Tests Strategy

Tests are not written in this planning stage. Future Phase 2C tests should use
only pure dictionaries, strings, and `tmp_path` synthetic inputs.

Required future test boundaries:

- Do not depend on the real accepted manifest.
- Do not depend on real `output/`.
- Do not read real report artifacts.
- Do not write manifests.
- Do not write under `output/`.
- Do not write fixtures.
- Do not generate runtime artifacts.
- Do not call providers.
- Do not use network.
- Do not read tokens, credentials, `.env`, or MCP config.
- Do not process unrelated mojibake untracked files.

Required future coverage:

- valid explicit artifact paths produce ticker-scoped inventory rows;
- valid synthetic manifest payload produces inventory rows;
- manifest entry adapter rows produce inventory rows;
- validated `local_artifact_index_row.v1` inputs are grouped into output
  buckets;
- duplicate `artifact_id` handling;
- duplicate path handling;
- company-name conflict handling;
- mismatched ticker conflict handling;
- unknown ticker has no fallback to `600406`, `002371`, or `002050`;
- all artifacts ignored returns conservative empty / caveated inventory;
- no directory scan;
- no `glob`, `rglob`, or `os.walk`;
- no artifact content read;
- no artifact existence check;
- no real file hash computation;
- no writes;
- no input mutation;
- no shared mutable `caveats` or `lineage_refs`;
- `not_for_trading_advice=false` is rejected;
- artifact-state is not a fact boundary.

Recommended test techniques:

- Monkeypatch `glob.glob`, `pathlib.Path.glob`, `pathlib.Path.rglob`, and
  `os.walk` to fail if called.
- Monkeypatch `pathlib.Path.exists`, `pathlib.Path.stat`, and file hash helpers
  to fail for artifact paths.
- Monkeypatch `builtins.open`, `Path.read_text`, and `Path.read_bytes` to fail
  for report artifacts and the real accepted manifest.
- Monkeypatch `Path.write_text`, `Path.write_bytes`, and write / append `open`
  modes to fail.
- Use `copy.deepcopy` before and after calls to prove no input mutation.
- Mutate one returned row's `caveats` or `lineage_refs` and assert no other row
  or caller-owned input changes.

Suggested future targeted command:

```text
python -m pytest tests/test_local_artifact_index.py -p no:cacheprovider
```

Suggested future regression subset:

```text
python -m pytest tests/test_local_artifact_index.py tests/test_manifest_locator.py tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py -p no:cacheprovider
```

## 9. Expected Files

Future implementation should default to modifying only:

```text
src/fundamental_skill/research_planning/local_artifact_index.py
tests/test_local_artifact_index.py
```

Default file policy:

- Prefer placing the builder in `local_artifact_index.py` because Phase 2C
  builds a ticker-scoped inventory from Local Artifact Index rows and related
  explicit inputs.
- Prefer placing tests in `tests/test_local_artifact_index.py` because the
  builder belongs to the local artifact inventory surface.
- Do not modify `src/fundamental_skill/research_planning/__init__.py` unless a
  later accepted implementation step requires a public export and documents why.
- Do not modify existing pipelines.
- Do not modify Research Report V1.
- Do not modify accepted manifest code.
- Do not modify manifest writers.
- Do not modify fixtures.
- Do not modify `output/`.
- Do not process unrelated mojibake untracked files.

A dedicated builder module or dedicated test file may be proposed only if
implementation review finds a clear reason, such as:

- `local_artifact_index.py` becomes materially hard to review;
- the builder needs a deliberately narrow import surface to preserve no-IO
  boundaries;
- monkeypatch-heavy no-read / no-write tests would obscure existing
  `tests/test_local_artifact_index.py` coverage.

If a new module or test file is proposed, the implementation summary must name
it explicitly, explain why the default files were insufficient, and keep the
change set minimal.

## 10. Acceptance Checklist

Documentation planning acceptance:

- [ ] Only this Phase 2C planning document is added.
- [ ] No production code is written.
- [ ] No tests are written.
- [ ] No runtime artifact is generated.
- [ ] No real accepted manifest is read.
- [ ] No `output/` scan is performed.
- [ ] No report artifact is read.
- [ ] No manifest is written.
- [ ] No output file is written.
- [ ] No fixture is written or promoted.
- [ ] No input object is mutated.
- [ ] No verified fact promotion is performed.
- [ ] No hypothesis generator, orchestrator, Dashboard / Batch, or Research
  Report V1 integration work is performed.
- [ ] No live provider, CNInfo, Tushare, AkShare, MCP, token, or network work is
  performed.
- [ ] No unrelated mojibake untracked files are processed.
- [ ] `git status --short` is reviewed before handoff.
- [ ] `git log --oneline -5` is reviewed before handoff.
- [ ] No commit is created.
- [ ] No push is performed.

Future Phase 2C implementation acceptance, only after explicit approval:

- [ ] Modify only `src/fundamental_skill/research_planning/local_artifact_index.py`
  and `tests/test_local_artifact_index.py`, unless a separately justified
  minimal builder module or test file is accepted.
- [ ] Builder accepts explicit inputs only.
- [ ] `stock_code` must be exactly six digits.
- [ ] `company_name` remains auxiliary and cannot resolve identity alone.
- [ ] Explicit artifact paths pass Phase 2A path safety.
- [ ] Manifest payloads pass Phase 2B validators.
- [ ] Manifest entries pass `validate_manifest_entry_row`.
- [ ] Artifact rows pass `validate_artifact_row`.
- [ ] Raw real accepted manifest dictionaries are rejected.
- [ ] Raw `output/` scan results are rejected.
- [ ] Report artifact content and parsed report sections are rejected.
- [ ] Output uses `ticker_local_artifact_inventory.v1`.
- [ ] Output sets `not_for_trading_advice=true`.
- [ ] `available_data_artifacts`, `missing_data_artifacts`,
  `ignored_artifacts`, and `conflict_artifacts` are populated only from
  explicit validated state.
- [ ] No real manifest read.
- [ ] No output scan.
- [ ] No report artifact read.
- [ ] No artifact existence check.
- [ ] No real file hash computation.
- [ ] No manifest, output, fixture, or runtime artifact write.
- [ ] No input mutation.
- [ ] No fuzzy matching.
- [ ] No fallback to `600406`, `002371`, or `002050`.
- [ ] No verified fact, evidence fact, candidate fact, report claim, or
  hypothesis promotion.
- [ ] Valid explicit path, synthetic manifest payload, manifest-entry row,
  duplicate, conflict, unknown ticker no-fallback, no-scan, no-read, no-write,
  no-mutation, and fact-boundary tests pass.
- [ ] Targeted `tests/test_local_artifact_index.py` passes.
- [ ] Regression subset passes.
- [ ] `git status --short` is clean except unrelated mojibake untracked files.

Phase 2C should move to implementation only after this planning document is
accepted and a separate implementation request is made.
