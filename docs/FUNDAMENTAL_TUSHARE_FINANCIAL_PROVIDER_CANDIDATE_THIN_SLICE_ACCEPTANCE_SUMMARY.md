# Tushare Financial Statement Provider Candidate Thin Slice Acceptance Summary

## 1. Stage name

Tushare Financial Statement Provider Candidate Thin Slice.

## 2. Baseline commits

- Implementation commit: `2fda6935e19df91ffa422b0403c2d286eed67388`
- Previous completed stage: Live Network Discovery Client Injected-Fake acceptance summary commit `f5761e8`

## 3. Stage objective

This stage added Tushare as a real structured financial statement provider data source for provider-candidate use.

- Output scope: provider candidate financial snapshot and provider candidate financial trend table.
- Target stock: `600406.SH`, Guodian NARI / 国电南瑞.
- Target periods: `2025FY` and `2026Q1`.
- Target Tushare interfaces: `income`, `balancesheet`, `cashflow`, and `fina_indicator`.
- Tushare rows are provider candidate observations only.
- Tushare data is not an official verified fact source.
- Follow-up work still needs official disclosure lineage verification for key fields before any report-grade acceptance.

## 4. Modified files in implementation commit

The implementation commit included exactly these expected files:

- `src/fundamental_skill/data_providers/tushare_financial_provider.py`
- `tests/test_tushare_financial_provider.py`
- `tests/test_tushare_financial_provider_safety.py`

## 5. Functional summary

- Added `provider_candidate_financial_snapshot.v1`.
- Added `provider_candidate_financial_trend_table.v1`.
- Supports an injected fake `api_client` for deterministic tests.
- Supports `allow_network=True` by creating a Tushare client from the `TUSHARE_TOKEN` environment variable.
- Defaults to no network access.
- Does not read `tushare_token.txt`.
- Does not read `.env`.
- Does not print or persist the token.
- Builds trend table rows for `2025FY` and `2026Q1`.
- Preserves provider row metadata: `provider`, `table_name`, `ts_code`, `period`, `ann_date`, `end_date`, `original_fields`, and `selected_fields`.
- Selected metrics cover core fields from `income`, `balancesheet`, `cashflow`, and `fina_indicator`.

## 6. Live smoke summary

- `TUSHARE_TOKEN set: True`.
- Manual live smoke was executed.
- Token was not printed.
- `tushare_token.txt` and `.env` were not read.
- No `output`, `fixtures`, or manifest files were written.
- `600406.SH` returned Tushare provider candidate data for both `2025FY` and `2026Q1`.
- All four tables returned rows: `income`, `balancesheet`, `cashflow`, and `fina_indicator`.
- `trend_table_rows=2`.
- `blocked_reasons_count=1`.
- `missing_tables_count=0`.
- For `20251231`, all four tables returned rows; `fina_indicator.inv_turn` was missing and the other selected fields were present.
- For `20260331`, all four tables returned rows; `cashflow` returned two rows and recorded `multiple_provider_rows`; `fina_indicator.inv_turn` was missing and the other selected fields were present.
- `multiple_provider_rows:cashflow:20260331` is a handled provider candidate caveat, not a blocker.

## 7. Patch and review summary

- Initial implementation acceptance review result: `PASS_WITH_PATCH_NEEDED`.
- The patch passed final implementation acceptance review.
- Patch contents:
  - Provider rows fail closed when returned `ts_code`, `period`, or `end_date` does not match the request.
  - Provider rows fail closed when identity fields are missing.
  - Mismatched rows do not enter provider row buckets.
  - Mismatched rows do not enter the trend table.
  - For the same table and same period, multiple rows are handled deterministically by selecting the row with the greatest `ann_date`.
  - If `ann_date` is tied, input order is preserved and the first row is selected.
  - `multiple_provider_rows` is recorded in caveats or blocked reasons.
  - Fixed a false positive where the real Tushare field name `sell_exp` was incorrectly treated as a trading-advice marker.
- No blocker remains after the patch.

## 8. Test results

- Targeted tests: `66 passed`.
- Related regression tests: `394 passed`.
- System `python` was unavailable, so Codex bundled Python was used.
- Import-impact tests were not run because `rg` confirmed that `test_generate_report_cli.py` and `test_candidate_review_decisions_bridge.py` do not import this provider, and this patch did not touch the Report V1 or bridge import chain.

## 9. Explicitly untouched restricted areas

This stage did not touch:

- official verification modules
- official source discovery modules
- Report V1
- accepted manifest
- output baseline
- fixtures
- output writes
- token, `.env`, or `tushare_token.txt` file reads
- `.local_experiments`
- unrelated mojibake files
- unrelated examples file
- buy, sell, or hold recommendations
- target price
- position sizing
- technical signals
- `official_verified` marking

## 10. Remaining untracked and excluded items

The working tree still has existing untracked or explicitly excluded items that were not handled by this stage:

- `.local_experiments/`
- `output/` was not read, written, staged, or committed by this stage
- `tushare_token.txt`
- unrelated mojibake files
- unrelated examples file

## 11. Stage conclusion

- Implementation accepted.
- No blocker remains.
- This summary is docs-only.
- Tushare provider candidate data has been connected and live-smoked successfully.
- Tushare data remains provider candidate data, not official verified fact data.
- The next stage should begin with reassessment and planning.
- Follow-up planning should route provider candidates into an official verification queue rather than directly into Report V1 or any trading-advice workflow.
