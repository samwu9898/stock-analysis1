# Official Artifact Download / Cache Acquisition Thin Slice Acceptance Summary

## Stage Name

Official Artifact Download / Cache Acquisition Thin Slice.

## Baseline Commits

- Implementation commit: `5cfa74625ad01e0209a442fff3966cddab4f590c`
- Previous completed stage: Real Official Metadata Discovery for Anchor Handoff acceptance summary commit `63302dd`

## Stage Goal

This thin slice implements safe official PDF artifact acquisition from matched official disclosure anchors.

- Input is `provider_metric_official_disclosure_anchor_map.v1`.
- Only `official_anchor_status=matched` official disclosure anchors are eligible for artifact acquisition.
- The matched anchor `source_url` points to an official PDF artifact.
- The module downloads official PDF bytes into an explicitly supplied `cache_dir`.
- The module produces `official_disclosure_artifact_cache.v1`.
- The module records PDF byte-level cache metadata.
- The module calculates `sha256`.
- The module records `file_size_bytes`.
- The module records source lineage.
- It does not parse PDFs.
- It does not extract text.
- It does not extract tables.
- It does not extract metrics.
- It does not generate `official_metric_fact`.
- It does not generate `provider_official_conflict`.
- It does not perform provider-vs-official reconciliation.
- It does not connect to Report V1.
- `artifact_status=cached` is not `official_verified`.

## Changed Files

- `src/fundamental_skill/data_verification/official_artifact_cache_acquisition.py`
- `tests/test_official_artifact_cache_acquisition.py`
- `tests/test_official_artifact_cache_acquisition_safety.py`

## Functional Summary

- Added local schema version `official_disclosure_artifact_cache.v1`.
- Added local schema version `official_disclosure_artifact_cache_item.v1`.
- Added local schema version `official_disclosure_artifact_download_result.v1`.
- Added local schema version `official_artifact_source_lineage.v1`.
- Accepts only `provider_metric_official_disclosure_anchor_map.v1`.
- Processes only anchors with `official_anchor_status=matched`.
- Routes unmatched, missing, ambiguous, and conflict anchors into `skipped_items`.
- Requires `source_url` and `final_url` hosts to remain in the official allowlist.
- Allows official PDF byte download for cache and integrity metadata only.
- Requires `cache_dir` to be explicitly supplied.
- Allows creating `cache_dir` when it does not exist.
- Rejects `cache_dir` paths under `output`, `fixtures`, `.local_experiments`, repo root, or accepted manifest locations.
- Writes through a temporary file and then performs an atomic rename.
- Records `sha256`, `file_size_bytes`, `content_type`, `cache_path`, and `source_lineage`.
- Reuses cache metadata for duplicate same `source_url` or same `sha256`.

## Download And Cache Policy

- `allow_network=False` fails closed.
- The default client uses HTTP `GET`.
- Timeout is `20s`.
- `MAX_ARTIFACT_BYTES` is `80MB`.
- Source host and final host allowlist:
  - `www.cninfo.com.cn`
  - `static.cninfo.com.cn`
  - `www.sse.com.cn`
  - `www.szse.cn`
  - `www.bse.cn`
- `application/pdf` is accepted when PDF magic bytes are valid.
- `application/octet-stream`, `binary/octet-stream`, and empty content type are accepted only when the URL is a `.pdf` URL and magic bytes are `%PDF-`.
- `text/html`, `application/json`, zip content, image content, and unknown non-PDF content are rejected.
- PDF magic bytes must start with `%PDF-`.
- The default urllib client checks final host before reading the body.
- A redirect to a non-allowlist final host fails before body read.
- Output `final_url` is sanitized by removing query and fragment.
- URLs containing `token`, `.env`, or `tushare_token` are rejected.
- Cache filenames are derived from `stock_code`, `period_end_date`, `announcement_type`, and `sha256`.
- `source_title` is not used as the cache filename.

## Patch And Review Summary

- Initial implementation acceptance review: `PASS_WITH_PATCH_NEEDED`.
- The blocker was that the default urllib client did not check redirect final host before reading body.
- The patch is complete.
- Patch contents:
  - Added `OfficialArtifactFinalHostBlocked`.
  - Updated `_default_official_http_client` to inspect `response.geturl()` before `response.read(...)`.
  - Fail closed when final host is not in the official allowlist.
  - Added `test_default_client_redirect_final_host_non_allowlist_blocks_before_reading_body`.
  - Added `test_default_client_allowlist_final_host_succeeds`.
  - Preserved content-type, size-limit, and PDF magic-byte test coverage.
- Final implementation acceptance review: `PASS`.
- Process note: one `rg docs src tests` search range was too broad and the output included `tests/fixtures` path fragments.
- Planning accepted this process note as not a blocker because fixture content was not read, written, staged, or used.

## Manual Live Smoke Summary

- Manual live smoke was executed.
- The first network attempt was unavailable in the sandbox; the smoke then succeeded after the normal permission flow.
- Downloaded object: `国电南瑞2026年第一季度报告`
- `source_domain`: `static.cninfo.com.cn`
- `final_domain`: `static.cninfo.com.cn`
- `content_type`: `application/pdf`
- `file_size_bytes`: `182673`
- `sha256` first 12 characters: `a0a35625f79f`
- `cache_filename`: `600406_20260331_quarterly_report_a0a35625f79fd3026671dedb9caa8cd4271af37fd96abe5e39b3741cab7ab7b3.pdf`
- `artifact_status`: `cached`
- Cache was written to a temporary directory.
- No cache file was committed.
- No `output`, `fixtures`, or manifest file was written.
- No PDF parsing occurred.
- No text, table, or metric extraction occurred.
- No PDF content was printed.

## Test Results

- Pre-patch targeted tests: `84 passed`.
- Pre-patch related tests: `165 passed`.
- Post-patch targeted tests: `86 passed`.
- Post-patch related tests: `165 passed`.
- The system `python` command was unavailable, so validation used Codex bundled Python.

## Explicitly Untouched Boundaries

The stage did not touch or change:

- `real_official_metadata_anchor_handoff.py`
- `provider_metric_official_anchor.py`
- `official_disclosure_request.py`
- `official_source_discovery_adapter.py`
- `provider_candidate_verification_queue.py`
- Tushare provider module
- Research Report V1 generator
- HTML renderer
- Dashboard
- `schemas.py` / `validators.py`
- accepted manifest
- output baseline
- fixtures
- output read/write paths
- token files, `.env`, or `tushare_token.txt`
- `.local_experiments`
- unrelated mojibake files
- unrelated examples file
- PDF parser
- text extraction
- table extraction
- metric extraction
- `official_metric_fact`
- `provider_official_conflict`
- provider-vs-official reconciliation
- buy / sell / hold outputs
- target price outputs
- position outputs
- technical signal outputs

## Remaining Local Items

The local workspace still has existing untracked or protected local items that were not handled by this stage:

- `.local_experiments/`
- `output/`
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

## Stage Conclusion

- Implementation accepted.
- No blocker remains.
- This summary is docs-only.
- The project now has the capability to safely acquire and cache official PDF artifacts from matched official disclosure anchors.
- Cached artifacts are still not official verified facts.
- This is still not PDF parsing.
- This is still not official evidence extraction.
- This is still not `official_metric_fact`.
- This is still not a formal Research Pack or Report V1.
- The next stage should reassess direction before implementation.
- Planning noted that the project should not continue endlessly expanding infrastructure after this stage.
- The next stage should return toward a research-value vertical slice.
- Recommended next planning target: `600406` Live Evidence-aware Research Pack Vertical Slice, or a very small official evidence extraction slice.
- The project should not jump directly to Report V1 or trading advice.
