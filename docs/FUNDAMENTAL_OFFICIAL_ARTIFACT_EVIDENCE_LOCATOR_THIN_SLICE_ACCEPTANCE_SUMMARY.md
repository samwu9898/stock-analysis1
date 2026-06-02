# Official Artifact Evidence Locator Thin Slice Acceptance Summary

## 1. Stage Name

Official Artifact Evidence Locator Thin Slice

## 2. Baseline Commits

- implementation commit: `20b3572`
- previous completed stage: Ticker-generalization Smoke acceptance summary commit `51cdac1`

## 3. Stage Objective

This thin slice moves the project from `official_disclosure_artifact_cache.v1` cached official PDF artifacts to `official_artifact_evidence_locator.v1` locator metadata.

The accepted scope is:

- Convert `artifact_status=cached` official PDF artifacts into locator results.
- Allow locator-level PDF text-layer extraction.
- Output `page_number`, bounded `snippet`, keyword hit, section locator, and locator confidence metadata.
- Do evidence locating only.
- Do not perform OCR.
- Do not parse tables.
- Do not extract revenue, net profit, cash flow, EPS, or any metric numeric values.
- Do not generate `official_metric_fact`.
- Do not generate `provider_official_conflict`.
- Do not perform provider-vs-official reconciliation.
- Do not connect to Report V1.
- Treat locator hits as metadata only; a locator hit is not `official_verified`.

## 4. Modified Files

The implementation commit only submitted these expected files:

- `src/fundamental_skill/data_verification/official_artifact_evidence_locator.py`
- `tests/test_official_artifact_evidence_locator.py`
- `tests/test_official_artifact_evidence_locator_safety.py`

## 5. Functional Summary

The implementation adds local schema/constants for:

- `official_artifact_evidence_locator.v1`
- `official_artifact_evidence_locator_item.v1`
- `official_artifact_text_hit.v1`
- `official_artifact_section_locator.v1`

Input and artifact handling:

- Input must be `official_disclosure_artifact_cache.v1`.
- The module calls and reuses `validate_official_disclosure_artifact_cache`.
- Only `artifact_status=cached` artifacts are processed.
- Skipped or blocked artifact items are carried into `skipped_items`.
- `cache_path` is validated.
- `cache_path` is forbidden in `output`, `fixtures`, `.local_experiments`, repo root, or accepted manifest paths.
- `cache_path` must be a `.pdf`.

PDF integrity and extraction policy:

- Before reading PDF bytes, the module first runs `stat()` on the cache path.
- It validates declared size, actual stat size, non-zero size, and `MAX_ARTIFACT_BYTES`.
- It validates `sha256`.
- It validates PDF magic bytes.
- It uses installed `pypdf 6.10.0` for PDF text-layer extraction.
- It does not add dependencies.
- It does not use OCR.
- It does not use an external binary.
- It does not read the image layer.
- It does not parse tables.
- Snippets are bounded to 200 characters.
- `page_number` is 1-based.
- It does not output full page text.
- It does not output the full `cache_path`; it outputs `cache_filename`.

## 6. Locator Scope

Allowed locator outputs include:

- `report_title_hits`
- `company_name_hits`
- `stock_code_hits`
- `report_period_hits`
- `section_heading_hits`
- `keyword_hits`
- `locator_confidence`
- `source_artifact_sha256`
- `source_file_size_bytes`
- `cache_filename`

Default safe keywords and sections include:

- 目录
- 重要提示
- 公司简介
- 管理层讨论与分析
- 经营情况讨论与分析
- 主营业务
- 财务报表
- 合并资产负债表
- 合并利润表
- 合并现金流量表

## 7. Patch And Review Summary

Initial implementation acceptance review result:

- `PASS_WITH_PATCH_NEEDED`

Patch 1: metric locator keyword blocker.

- Added `FORBIDDEN_METRIC_LOCATOR_KEYWORDS`.
- Blocks metric locator intent during `keywords` and custom `section_headings` normalization.
- Rejects metric-oriented locator keywords such as `revenue`, `operating revenue`, `net profit`, `net income`, `operating cash flow`, `EPS`, 营业收入, 主营业务收入, 净利润, 归母净利润, 经营现金流, and 每股收益.
- Allowed section headings still pass, including 财务报表, 合并利润表, and 合并现金流量表.

Patch 2: file size stat gate before `read_bytes`.

- Runs `stat()` on `cache_path` before reading bytes.
- Validates declared size, actual stat size, non-zero size, and `MAX_ARTIFACT_BYTES`.
- Size mismatch, missing size, zero size, and oversized files all fail before read.

After these patches, final implementation acceptance review result:

- `PASS`

## 8. Test Results

- pre-patch targeted tests: `91 passed`
- pre-patch related tests: `158 passed`
- patch targeted tests: `101 passed`
- patch related tests: `158 passed`
- When system Python was unavailable, Codex bundled Python was used.

## 9. Explicitly Untouched Boundaries

Confirmed untouched:

- `official_artifact_cache_acquisition.py`
- `real_official_metadata_anchor_handoff.py`
- `provider_metric_official_anchor.py`
- `provider_candidate_verification_queue.py`
- `live_evidence_research_pack_orchestration_entry.py`
- `live_evidence_aware_research_pack_vertical_slice.py`
- `evidence_aware_research_pack_scaffold.py`
- `ticker_research_context_skeleton.py`
- Tushare provider module
- Research Report V1 generator
- HTML renderer
- Dashboard
- `schemas.py` / `validators.py`
- `__init__.py`
- accepted manifest
- output baseline
- fixtures
- output read/write paths
- token / `.env` / `tushare_token` file reads
- `.local_experiments`
- unrelated mojibake files
- unrelated examples file
- OCR
- table extraction
- metric extraction
- `official_metric_fact`
- `provider_official_conflict`
- provider-vs-official reconciliation
- buy / sell / hold outputs
- target price outputs
- position advice
- technical signals

## 10. Remaining Untracked Items

The working tree still has existing untracked items that were not handled by this stage:

- `.local_experiments/`
- `output/`
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

## 11. Current Stage Conclusion

- implementation accepted
- no blocker
- this summary doc is docs-only
- the project has moved from artifact cached metadata to official artifact evidence locating
- the locator can now locate title, company name, stock code, report period, section, and safe keyword evidence in official PDF text layers
- this is still not `official_metric_fact`
- this is still not official metric verification
- this is still not provider-vs-official reconciliation
- this is still not formal Research Pack / Report V1
- this still contains no trading advice

The next stage should reassess before expanding scope. Reasonable follow-up options include:

- connect locator results into the live evidence vertical slice
- expose a public API or skill callable wrapper
- evaluate a very small metric evidence extraction step

The next stage should not jump directly to Report V1 or trading advice.
