# Phase 2B-2 Synthetic Manifest Parser Acceptance Summary

Date: 2026-05-30

Stage: Phase 2B-2 Synthetic Manifest Parser acceptance.

Status: baseline accepted and ready to freeze.

## 1. Conclusion

Phase 2B-2 Synthetic Manifest Parser baseline passed and can be frozen.

This baseline is the synthetic-only parser step for the Read-only Manifest
Locator. It reads only an explicitly provided synthetic manifest path, designed
for tests that create a manifest with `tmp_path`.

It is not:

- a real accepted manifest reader;
- an output scanner;
- a report artifact reader;
- a manifest writer;
- fixture promotion;
- a manifest entry to artifact row adapter;
- a ticker-scoped full index builder;
- Research Report V1 integration;
- a hypothesis generator;
- an orchestrator;
- a live provider connector.

## 2. Commit

Phase 2B-2 commit hash:

```text
b205e02e824c0566eb67a5d501b186542493168e
```

## 3. Expected Files

```text
src/fundamental_skill/research_planning/manifest_locator.py
tests/test_manifest_locator.py
```

No `__init__.py` change was required.

## 4. Delivered Capabilities

- `parse_synthetic_manifest_locator`.
- `synthetic_manifest_locator_input.v1`.
- Output as `manifest_locator_payload.v1`.
- Matched artifacts converted to `manifest_entry_row.v1`.
- `artifacts` / `report_artifacts` alias support.
- Valid synthetic manifest handling.
- Missing synthetic manifest handling.
- Unreadable synthetic manifest handling.
- Invalid JSON handling.
- Invalid schema handling.
- Missing `entries` handling.
- `entries` not list handling.
- Unsafe synthetic manifest path handling.
- Unsafe artifact path handling.
- Invalid artifact enum handling.
- `not_for_trading_advice=false` rejection.
- Forbidden marker rejection.
- Unknown ticker returns unmatched / `data_collection_required`.
- Unknown ticker does not fall back to `600406`, `002371`, or `002050`.
- Code / name conflict returns `conflict_open` / review-required state.
- Duplicate requested-code entries return `duplicate_entries` /
  review-required state.
- `artifact.caveats` must be a list and is not silently converted.

The parser returns locator state only. It does not create Local Artifact Index
rows, evidence facts, hypotheses, Research Report V1 payloads, provider calls,
or trading advice.

## 5. Safety / Boundary Summary

Confirmed boundaries:

- No real `output/research_reports/accepted_manifest.json` read.
- No real `output/` scan.
- No report artifact content read.
- No artifact existence check.
- No real file hash calculation.
- No manifest write.
- No `output/` write.
- No fixture write or promotion.
- No runtime artifact generation.
- No model call.
- No prompt orchestration.
- No network.
- No provider call.
- No CNInfo call.
- No Tushare call.
- No AkShare call.
- No MCP connection.
- No Research Report V1 integration.
- No manifest entry to artifact row adapter.
- No ticker-scoped full index builder.
- No hypothesis generator.
- No orchestrator.

The implementation reads only the explicit synthetic manifest path passed to
the parser. Artifact paths inside the manifest remain data-only path state:
they are not opened, checked for existence, hashed, scanned, or converted into
facts.

## 6. Acceptance Fix

One schema strictness issue was found during implementation acceptance:

```text
artifact.caveats values that were not lists could be converted before row
validation.
```

Fix:

- `artifact.caveats` is now required to be present.
- `artifact.caveats` must be a list.
- Non-list caveats fail closed with schema-mismatch locator state.
- A targeted test now covers the non-list caveats case.

Final acceptance confirmed coverage for:

- invalid JSON;
- invalid schema;
- missing `entries`;
- `entries` not list;
- unsafe manifest path;
- unsafe artifact path;
- unknown ticker no fallback;
- duplicate entries;
- code / name conflict;
- marker violation;
- no directory scan;
- no report artifact read;
- no file write.

## 7. Test Results

Accepted verification results:

```text
targeted tests: 58 passed
regression subset: 215 passed
```

Targeted command:

```text
python -m pytest tests/test_manifest_locator.py -p no:cacheprovider
```

Regression subset:

```text
python -m pytest tests/test_local_artifact_index.py tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py tests/test_candidate_review_decisions_bridge.py tests/test_generate_report_cli.py tests/test_accepted_artifact_manifest.py -p no:cacheprovider
```

The local shell did not expose `python`; accepted runs used the Codex bundled
Python interpreter.

## 8. Next Stage Recommendation

Proceed to Phase 2B-3 Manifest Entry to Artifact Row Adapter Planning.

Phase 2B-3 should start with planning only. It should not directly enter
implementation.

Phase 2B-3 planning must preserve these boundaries:

- Do not read the real accepted manifest.
- Do not scan real `output/`.
- Do not read real report artifacts.
- Do not write manifests.
- Do not write `output/`.
- Do not write fixtures.
- Do not generate runtime artifacts.
- Do not enter ticker-scoped full index building.
- Do not enter hypothesis generation.
- Do not enter orchestrator work.
- Do not enter Research Report V1 integration.
- Do not call live providers, CNInfo, Tushare, AkShare, MCP, model, token, or
  network.

The Phase 2B-3 adapter should remain a narrow, explicit, validation-driven
planning step before any code is written.
