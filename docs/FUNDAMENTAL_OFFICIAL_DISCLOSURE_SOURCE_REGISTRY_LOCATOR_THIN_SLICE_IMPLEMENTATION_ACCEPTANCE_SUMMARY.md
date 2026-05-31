# Official Disclosure Source Registry + Locator Thin Slice Minimal Implementation Acceptance Summary

Date: 2026-06-01

Stage: Official Disclosure Source Registry + Locator Thin Slice Minimal Implementation.

Status: accepted. Minimal implementation completed, committed, and pushed.

Baseline commit:

```text
0699944c5ab7218614e973158c4a87c77ac48fef
```

Commit message:

```text
feat: add official disclosure registry locator gate
```

## 1. Stage Goal

This stage implements the minimal production gate for official disclosure source
registry and locator behavior.

The implementation is intentionally limited to schema constants, enums,
validators, pure source registry helpers, pure locator helpers, and targeted
tests. It provides an upstream source-metadata gate for the existing official
verification data gate.

This stage does not implement live source discovery, downloading, parsing,
metric extraction, provider integration, Report V1 integration, accepted
manifest writes, output writes, fixture writes, or report generation.

## 2. Changed Files

Production files:

```text
src/fundamental_skill/data_verification/schemas.py
src/fundamental_skill/data_verification/validators.py
src/fundamental_skill/data_verification/official_disclosure_source_registry.py
src/fundamental_skill/data_verification/official_disclosure_locator.py
```

Test files:

```text
tests/test_official_disclosure_source_registry.py
tests/test_official_disclosure_locator.py
tests/test_official_disclosure_registry_locator_safety.py
```

No other production, test, output, fixture, manifest, provider, Report V1, or
token files were included in the implementation commit.

## 3. Schema / Enums Summary

Added schema versions:

```text
official_source_registry_entry.v1
official_disclosure_locator_result.v1
```

Added official disclosure source enums and constants for:

- official disclosure source type;
- official disclosure source status;
- official disclosure locator status;
- source refresh policy;
- source version;
- registry entry required keys;
- locator result required keys;
- selectable official source status sets;
- official/cache/discovery/provider source type groups.

`not_for_trading_advice=true` remains required and is enforced through the
existing recursive safety validator.

## 4. Source Registry Helper Summary

`official_disclosure_source_registry.py` adds pure helper functions only. The
helpers classify source types, validate sha256 strings, build source-conflict
reasons, determine whether a registry entry can enter official candidate or
official cache lanes, classify source status, and delegate full registry entry
validation.

The helpers do not read files, compute real file hashes, download PDFs, access
URLs, call providers, read tokens, write manifests, write outputs, or generate
reports.

## 5. Locator Helper Summary

`official_disclosure_locator.py` adds pure locator helpers only. The helpers
select a single official candidate only when exactly one selectable candidate
exists, classify locator status, reject non-official candidates, and build
blocked or review-required locator results.

The locator handles explicitly supplied candidates only. It does not fetch
URLs, download files, read local files, parse PDFs, refresh sources, call
providers, or trigger Report V1.

## 6. Cache / SHA256 / Versioning Policy

The implementation enforces:

- `file_sha256` must be a 64-character hex digest when present or required;
- `official_cached` requires original official `source_url`,
  `local_cache_path`, and `file_sha256`;
- local cache without original official URL is blocked;
- `.local_experiments` cache cannot enter production official cache;
- same URL with different sha256 is represented through a source-conflict
  helper;
- `registry_version` is required;
- `source_version` is required;
- `source_refresh_policy` is required;
- silent overwrite is not allowed by policy.

The first production slice remains explicit-metadata-only and does not perform
live download.

## 7. Fail-closed / Safety Summary

The implementation fails closed for:

- mirror source entering official candidate or official cache lanes;
- provider source entering official candidate or official cache lanes;
- unknown source entering official candidate or official cache lanes;
- local cache without original official source URL;
- missing sha256 for cached official file;
- invalid sha256 format;
- missing official metadata;
- missing registry/source version or refresh policy;
- multiple official candidates without review;
- selected locator source pointing to mirror/provider/unknown/blocked source;
- selected locator source that is not a complete registry entry;
- locator payloads containing metric extraction, official metric fact,
  provider official conflict, Report V1, accepted manifest, output write,
  provider live, token, network, PDF parser, or PDF table extraction intent.

The existing recursive safety scan is reused and extended to cover fixture write
and direct PDF parser / table extractor markers. It blocks token markers, `.env`
markers, `tushare_token.txt`, provider live markers, network markers, Report V1
markers, accepted manifest/output/fixture write markers, buy/sell/hold/target
price/portfolio/position/technical-signal markers, Chinese equivalents, and
nested markers.

## 8. Focused Audit Findings And Patch Result

Focused audit initially found three commit-before-merge issues:

1. `local_official_cache` could be classified too broadly for official
   candidate lane semantics.
2. `found_single_official_candidate` needed to reject multiple selectable
   official candidates instead of allowing silent selection.
3. Direct `pdf parser` marker coverage needed to be explicit in addition to
   existing parse/download markers.

Patch result:

- `local_official_cache` is blocked from `official_candidate` lane and may only
  enter the cache lane when official URL, local path, and sha256 requirements
  pass.
- locator validation now requires exactly one selectable official candidate for
  `found_single_official_candidate`.
- selected official source must be a complete registry entry and cannot point
  to mirror/provider/unknown/blocked candidates.
- `pdf_parser` / `pdf parser` markers are covered by safety tests and validator
  marker lists.

Post-patch focused audit found no blocker.

## 9. Test Results

System `python` was unavailable, so Codex bundled Python was used.

Targeted tests:

```text
239 passed
```

Related regression subset:

```text
180 passed
```

Extra subset:

```text
249 passed
```

## 10. Explicit Non-goals / Untouched Scope

This stage did not touch or implement:

- live download;
- network access;
- PDF parser;
- PDF table extractor;
- metric extraction;
- provider adapter;
- Report V1;
- accepted manifest;
- output baseline;
- fixtures;
- token / `.env` / `tushare_token.txt`;
- `.local_experiments`;
- unrelated mojibake files.

## 11. Current Remaining Untracked Items

The remaining untracked items after implementation commit and push were only:

```text
.local_experiments/
tushare_token.txt
unrelated mojibake HTML/Markdown/example files
```

These items were not staged, committed, read, modified, or pushed as part of
this stage.

## 12. Next Step Recommendation

Do not directly enter live source download, PDF parser productionization,
provider adapter work, Report V1 integration, accepted manifest writes, output
baseline writes, or fixture promotion.

Recommended next step is reassessment / planning:

- review whether the registry / locator gate API shape is sufficient;
- decide whether a separate implementation acceptance review is needed;
- plan any controlled official downloader as a separate stage with official
  domain allowlists, redirect policy, content/hash verification, and no token
  access;
- keep PDF parsing, provider integration, Report V1, and output/manifest/fixture
  writes out of scope until separately planned and accepted.
