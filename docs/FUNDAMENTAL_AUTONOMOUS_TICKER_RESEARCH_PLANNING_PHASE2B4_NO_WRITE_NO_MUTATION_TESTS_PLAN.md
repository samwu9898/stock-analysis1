# Phase 2B-4 No-write / No-mutation Tests Plan

Date: 2026-05-30

Stage: Phase 2B-4 No-write / No-mutation Tests planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not read report artifacts,
does not write manifests, does not write output files, does not write fixtures,
does not commit, and does not push.

Reference baseline:

- Phase 2B-3 Manifest Entry to Artifact Row Adapter baseline:
  `d0caa702138a75dc3573e3df3b7b964fde182c30`.
- Phase 2B-3 acceptance summary:
  `8b4484e6bd3989e34f4fcd2077dcf0a759cd4253`.

## 1. Phase 2B-4 Goal

Phase 2B-4 plans a narrow safety test layer for the accepted Phase 2B manifest
locator, synthetic parser, and manifest-entry adapter chain.

This phase plans future tests that prove the current chain remains:

- no-read beyond explicitly supplied synthetic test inputs;
- no-scan against real project output trees;
- no-write against manifests, output, fixtures, and runtime artifacts;
- no-mutation against caller-owned input dictionaries and lists;
- artifact-state only, with no promotion into verified facts or Research
  Report V1 integration.

Phase 2B-4 is planning only. It must not:

- add production functionality;
- implement a real manifest reader;
- implement an output scanner;
- implement a report artifact reader;
- implement a ticker-scoped full index builder;
- enter Research Report V1 integration;
- write tests in this planning step;
- generate runtime artifacts.

The future implementation should add tests only after this planning document is
accepted.

## 2. Test Subject Scope

Future Phase 2B-4 tests should cover the existing functions and linkages below:

```text
validate_manifest_entry_row
validate_manifest_locator_payload
parse_synthetic_manifest_locator
manifest_entry_to_artifact_row
validate_artifact_path_safety
validate_artifact_row
```

Scope notes:

- `validate_manifest_entry_row` should remain a schema and safety validator for
  manifest locator rows only.
- `validate_manifest_locator_payload` should remain a payload validator for
  locator-state payloads only.
- `parse_synthetic_manifest_locator` should read only the explicit synthetic
  JSON path supplied by a test.
- `manifest_entry_to_artifact_row` should adapt an already validated manifest
  entry row into a Local Artifact Index artifact-state row only.
- `validate_artifact_path_safety` should validate path string safety only; it
  must not become an existence check or content reader.
- `validate_artifact_row` should validate artifact-state row shape and safety
  only; it must not promote accepted/current state into facts.

The tests should exercise the chain boundaries without expanding the runtime
surface.

## 3. No-read / No-scan Boundary Tests

Future tests should prove the chain does not read or scan real project state.

Required no-read / no-scan assertions:

- does not read the real
  `output/research_reports/accepted_manifest.json`;
- does not scan the real `output/` tree;
- does not read the file pointed to by a manifest entry `artifact_path`;
- does not read report artifact content;
- does not check whether a real artifact exists;
- does not compute a real file hash;
- does not fall back to real accepted samples;
- does not fall back to `600406`, `002371`, or `002050`.

Recommended test shapes:

- Use `tmp_path` to create the only allowed synthetic manifest file.
- Monkeypatch `builtins.open` so any attempt to open the real accepted manifest
  path fails the test.
- Monkeypatch `pathlib.Path.read_text` so only the explicit `tmp_path`
  synthetic manifest can be read.
- Monkeypatch `pathlib.Path.exists` so existence checks against report
  artifacts fail the test.
- Monkeypatch `glob.glob`, `pathlib.Path.glob`, `pathlib.Path.rglob`, and
  `os.walk` so any scan of real `output/` fails the test.
- Use a manifest entry with an `artifact_path` pointing at a sentinel path that
  would fail if opened, hashed, or existence-checked.
- Assert unknown tickers remain unknown and never trigger accepted-sample
  fallback behavior.

The parser may read only the one synthetic manifest path explicitly passed by
the test. Adapter and validator calls should perform no file reads at all.

## 4. No-write / No-mutation Boundary Tests

Future tests should prove the chain does not write project state and does not
mutate caller-owned inputs.

Required no-write assertions:

- does not write the accepted manifest;
- does not write under `output/`;
- does not write under `fixtures/`;
- does not write runtime artifacts;
- does not stage, commit, or push;
- does not create report artifacts.

Required no-mutation assertions:

- does not modify the input synthetic manifest dictionary after it is parsed
  into memory by the test;
- does not modify the manifest entry row passed to
  `manifest_entry_to_artifact_row`;
- does not modify dictionaries passed to build or validate functions;
- does not share mutable defaults for `caveats` or `lineage_refs`;
- does not leak caveat or lineage mutations from one output row into another.

Recommended test shapes:

- Monkeypatch `pathlib.Path.write_text`, `pathlib.Path.write_bytes`, and
  `builtins.open` in write/append modes to fail the test.
- Monkeypatch `json.dump` and `json.dumps` only where useful to catch accidental
  manifest serialization; do not block normal parser reads from the explicitly
  supplied synthetic JSON.
- Create sentinel files under `tmp_path` and assert their contents remain
  unchanged after parser, validator, and adapter calls.
- Use `copy.deepcopy` before and after function calls to compare caller-owned
  dictionaries and lists.
- Invoke adapter/build/validate paths multiple times and mutate one returned
  row's `caveats` / `lineage_refs`; assert subsequent returned rows and the
  original inputs are unaffected.

No future test should require production code hooks, debug switches, or special
test-only parameters.

## 5. Recommended Test Techniques

Future Phase 2B-4 implementation may use:

- `tmp_path` synthetic manifests;
- monkeypatching `builtins.open`;
- monkeypatching `pathlib.Path.exists`;
- monkeypatching `pathlib.Path.read_text`;
- monkeypatching `pathlib.Path.write_text`;
- monkeypatching `pathlib.Path.write_bytes`;
- monkeypatching `glob.glob`, `pathlib.Path.glob`, `pathlib.Path.rglob`, and
  `os.walk`;
- monkeypatching `json.dump` where accidental writes must be detected;
- sentinel files to confirm no write occurred;
- `copy.deepcopy` before/after comparisons to confirm no input mutation.

Technique boundaries:

- Monkeypatching is for tests only.
- Production code must not gain test-only hooks.
- Production code must not gain debug flags to bypass normal safety behavior.
- Production code must not open real `output/` reads for test convenience.
- Production code must not loosen path safety to make tests easier.
- Tests should fail closed when accidental IO or mutation occurs.

## 6. No-mutation Input Tests

Future no-mutation tests should cover these cases:

- `parse_synthetic_manifest_locator` does not mutate the parsed synthetic
  manifest dictionary owned by the test.
- `manifest_entry_to_artifact_row` does not mutate the manifest entry row passed
  by the caller.
- Build and validation functions do not unexpectedly mutate caller-owned input.
- `caveats` does not share a mutable default between rows.
- `lineage_refs` does not share a mutable default between rows.
- Appending adapter boundary caveats to an output row does not append them to
  the input row.
- Appending lineage refs to an output row does not append them to the input row.
- Revalidating an already validated row returns safe independent data and does
  not mutate the original.

Recommended assertions:

- Keep an original Python object and a `deepcopy` snapshot.
- Call the target function.
- Assert the original object equals the snapshot.
- Mutate the returned object.
- Assert the original object and any second returned object remain unchanged.

## 7. Safety / Fact-boundary Tests

Future Phase 2B-4 tests should continue proving that locator and adapter output
remain artifact-state only.

Required safety / fact-boundary assertions:

- `accepted` does not mean verified fact.
- `current` does not mean verified fact.
- A manifest entry does not equal an evidence fact.
- Adapter output is only an artifact-state row.
- Forbidden markers are rejected.
- Trading advice markers are rejected.
- Unknown ticker inputs do not fall back to known tickers.
- Accepted samples do not generalize to a new ticker.

Marker coverage should continue rejecting markers for:

- verified facts;
- evidence facts;
- report facts;
- accepted report facts;
- hypotheses;
- hypothesis generation;
- Research Report V1 updates;
- manifest writes;
- fixture promotion;
- provider primary switches;
- trading signals;
- target prices;
- position sizing;
- portfolio allocation.

The future tests should be explicit that `accepted_status=accepted`,
`freshness_status=current`, and `source_status=available` remain locator /
artifact inventory state. They must not become evidence facts, accepted report
claims, or Research Report V1 input.

## 8. Expected Files

Future Phase 2B-4 implementation should default to modifying only:

```text
tests/test_manifest_locator.py
```

Default file policy:

- Do not modify production code.
- Do not modify `src/` unless acceptance finds a true bug.
- Do not modify any `__init__.py`.
- Do not modify real manifests.
- Do not modify `output/`.
- Do not add or modify fixtures.
- Do not generate runtime artifacts.
- Do not process unrelated mojibake untracked files.

A dedicated test file may be proposed only if it materially improves clarity,
for example:

```text
tests/test_manifest_locator_no_mutation.py
```

Acceptable reasons for a dedicated file:

- monkeypatch-heavy IO boundary tests would obscure the existing schema and
  adapter tests;
- no-mutation tests grow large enough to deserve a named safety suite;
- review needs a separate file to make no-read / no-write / no-mutation
  acceptance easy to audit.

If a dedicated test file is added, the future implementation summary must
explain why keeping all coverage in `tests/test_manifest_locator.py` was less
clear.

## 9. Prohibited Actions

Phase 2B-4 planning and future implementation must not:

- modify production code, unless acceptance finds a true bug;
- read the real accepted manifest;
- scan the real `output/` tree;
- read report artifact files;
- write manifests;
- write under `output/`;
- write fixtures;
- generate runtime artifacts;
- connect provider integrations;
- connect CNInfo;
- connect Tushare;
- connect AkShare;
- connect MCP;
- read tokens;
- use network access;
- enter a ticker-scoped full index builder;
- enter a hypothesis generator;
- enter an orchestrator;
- enter Research Report V1 integration;
- stage changes;
- commit changes;
- push changes;
- process unrelated mojibake files.

Any future discovery of a production bug must be documented before production
code is changed. The default expectation remains tests-only implementation
after this planning document is accepted.

## 10. Acceptance Checklist

Future Phase 2B-4 implementation acceptance should confirm:

- only expected test files changed;
- no production code changed, unless a true bug was found and documented;
- no real accepted manifest read;
- no real `output/` scan;
- no report artifact read;
- no accepted-sample fallback;
- no fallback to `600406`, `002371`, or `002050`;
- no manifest write;
- no output write;
- no fixture write;
- no runtime artifact generation;
- no stage / commit / push;
- no caller-owned input mutation;
- no shared mutable `caveats` default;
- no shared mutable `lineage_refs` default;
- targeted Phase 2B tests pass;
- relevant regression subset passes;
- git status is clean except unrelated mojibake untracked files.

Recommended targeted tests:

```text
tests/test_manifest_locator.py
```

Recommended regression subset:

```text
tests/test_local_artifact_index.py
tests/test_autonomous_ticker_research_schema.py
tests/test_autonomous_ticker_research_safety.py
tests/test_candidate_review_decisions_bridge.py
tests/test_generate_report_cli.py
tests/test_accepted_artifact_manifest.py
```

The future acceptance summary should state clearly whether Phase 2B-4 remained
tests-only and whether any production bug required a scoped fix.
