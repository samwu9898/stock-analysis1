# Phase 2B-1 Manifest Locator Schema + Validators Acceptance Summary

Date: 2026-05-30

Stage: Phase 2B-1 Read-only Manifest Locator Schema + Validators acceptance.

Status: baseline accepted and ready to freeze.

## 1. Conclusion

Phase 2B-1 Manifest Locator Schema + Validators baseline passed and can be
frozen.

This baseline is the schema / validator foundation for the future Read-only
Manifest Locator. It defines read-only locator payload and manifest entry row
contracts, status constants, builders, and validators.

It is not:

- a parser;
- a synthetic manifest parser;
- a real manifest reader;
- a manifest entry -> artifact row adapter;
- a ticker-scoped full index builder;
- a hypothesis generator;
- an orchestrator;
- Research Report V1 integration;
- a provider, CNInfo, Tushare, or MCP connector.

## 2. Commit

Phase 2B-1 commit hash:

```text
2448a958611dd11c8ecf4453b5903229c3af826d
```

## 3. Expected Files

```text
src/fundamental_skill/research_planning/manifest_locator.py
tests/test_manifest_locator.py
```

No `__init__.py` change was required.

## 4. Delivered Capabilities

- `manifest_locator_payload.v1`.
- `manifest_entry_row.v1`.
- Manifest locator payload builder / validator.
- Manifest entry row builder / validator.
- `manifest_exists_status` constants.
- `manifest_schema_status` constants.
- `accepted_status` constants.
- `freshness_status` constants.
- `hash_status` constants.
- `source_status` constants.
- `artifact_kind` constants.
- `artifact_format` constants.
- `unmatched_reason` constants.
- `manifest_path` validation through Phase 2A path safety.
- `artifact_path` validation through Phase 2A path safety.
- `matched_entries` child validation through `validate_manifest_entry_row`.
- `report_artifact_refs` path safety validation.
- Marker scan before path / report-ref masking.
- Masked `validate_payload_safety` call after marker scan.
- `accepted` / `current` manifest state remains artifact lineage state only.
- Unknown ticker state does not fallback to accepted samples such as `600406`,
  `002371`, or `002050`.

## 5. Safety / Boundary Summary

Confirmed boundaries:

- No real `accepted_manifest` read.
- No real `output/` scan.
- No report artifact content read.
- No real report file SHA-256 calculation.
- No `output/` write.
- No manifest write or update.
- No fixture write or promotion.
- No runtime artifact generation.
- No model call.
- No prompt orchestration.
- No network.
- No provider call.
- No CNInfo call.
- No Tushare call.
- No MCP connection.
- No Research Report V1 integration.
- No parser implementation.
- No manifest entry -> artifact row adapter.
- No ticker-scoped full index builder.
- No hypothesis generator.
- No orchestrator.
- No Dashboard / Batch work.
- No unrelated mojibake untracked file handling.

The implementation is pure schema / constants / validators plus tests.

## 6. Acceptance Fix

One blocker was found during implementation acceptance:

```text
report_artifact_refs containing legitimate report paths could be misclassified
by the generic safety scanner as high-entropy secret-like values.
```

Fix:

- `report_artifact_refs` now reuses Phase 2A path safety before common safety
  validation.
- `report_artifact_refs` are masked before the generic `validate_payload_safety`
  call.
- Row-level marker scanning still runs before any path / report-ref masking.

Final acceptance confirmed that marker payloads embedded in
`report_artifact_refs`, including:

```text
target_price
trading_signal
verified_fact
manifest_update
report_update
```

are still rejected and do not leak the full path in error messages.

## 7. Test Results

Accepted verification results:

```text
targeted tests: 38 passed
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

The local shell did not expose `python`; the accepted runs used the Codex
bundled Python interpreter.

## 8. Next Stage Recommendation

Proceed to Phase 2B-2 Synthetic Manifest Parser Planning.

Phase 2B-2 must remain synthetic-only until separately accepted:

- Do not read the real accepted manifest.
- Do not scan real `output/`.
- Do not read real report artifacts.
- Do not write manifest files.
- Do not write `output/`.
- Do not write fixtures.
- Do not generate runtime artifacts.
- Do not enter manifest entry -> artifact row adapter.
- Do not enter ticker-scoped full index builder.
- Do not enter hypothesis generator.
- Do not enter orchestrator.
- Do not enter Research Report V1 integration.
- Do not call live providers, CNInfo, Tushare, AkShare, MCP, model, token, or
  network.
