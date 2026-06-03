# Controlled Real LLM Local Manual Smoke Minimal Harness Thin Slice Acceptance Summary

## 1. Stage Name

Controlled Real LLM Local Manual Smoke Minimal Harness Thin Slice

## 2. Baseline Commits

- implementation commit: `2410374`
- previous completed stage: Fake LLM Frontstage Quality Comparison acceptance summary commit `54bf00f`
- ticker-only fake LLM renderer mode acceptance summary commit `86bc104`
- quality evaluation acceptance summary commit `9105bf0`
- rulebook replacement commit `381b2ed`

## 3. Stage Positioning

This stage is the minimal executable harness for a local/manual real LLM smoke.

This stage is not a planning gate.

This stage is not production-level LLM integration.

This stage is not a formal real LLM renderer adapter.

This stage is not Report V1 integration.

This stage is not an HTML renderer.

This stage is not official metric verification.

This stage is not provider-vs-official reconciliation.

This stage does not generate any runtime artifact.

The stage goal is to verify whether real DeepSeek can use the existing sanitized model-facing context, safety boundary, parse/validate path, and quality check to produce an acceptable professional brief preview.

## 4. Modified Files

The implementation commit submitted only these expected files:

- `src/fundamental_skill/research_planning/controlled_real_llm_manual_smoke.py`
- `tests/test_controlled_real_llm_manual_smoke.py`
- `tests/test_controlled_real_llm_manual_smoke_safety.py`

## 5. Functional Summary

- Added `controlled_real_llm_manual_smoke_request.v1`.
- Added `controlled_real_llm_manual_smoke_result.v1`.
- Added `controlled_real_llm_manual_smoke_readiness.v1`.
- Added `controlled_real_llm_manual_smoke_summary.v1`.
- Added `build_controlled_real_llm_manual_smoke_result`.
- Supports `llm_provider=deepseek`.
- Supports `llm_client_mode=fake / injected / env_live`.
- Supports env-live DeepSeek local/manual smoke.
- Reads only `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, and `DEEPSEEK_MODEL` from environment variables.
- Handles missing key, missing SDK, 402 insufficient balance, auth failure, rate limit, API error, and network error as structured skip paths.
- Handles invalid JSON, missing required section, trading advice, and engineering-label output as structured blocked paths.
- Result returns only sanitized summary and optional professional preview.
- Result does not return raw prompt.
- Result does not return raw LLM response.
- Result does not return raw provider bundle.
- Result does not return `candidate_items`.
- The harness does not write files.

## 6. DeepSeek Manual Smoke Summary

- Python runtime: `D:\anaconda\envs\ashare-copilot\python.exe`
- `DEEPSEEK_API_KEY=set`
- `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- `DEEPSEEK_MODEL=deepseek-v4-pro`
- openai SDK installed.
- `llm_client_mode=env_live`
- The smoke actually called the DeepSeek API endpoint.
- The ready result was not produced by the fake or injected client path.
- `professional_preview_present=true` was produced after DeepSeek response parse/validate.
- `smoke_status=ready`
- `readiness.status=ready`
- `blocked_reasons=[]`
- `llm_provider=deepseek`
- `model=deepseek-v4-pro`
- `quality_check_status=pass`
- `token/key_present_in_output=false`
- `files_written=false`
- `trading_advice_present=false`
- `engineering_labels_present=false`
- No API key was output.
- No prompt was output.
- No raw LLM response was output.
- No file was written by the smoke.

## 7. Test Results

- targeted tests: `64 passed`
- related tests: split coverage completed with `551 passed`
- When system Python was unavailable, Codex bundled Python was used for automated tests.
- Manual DeepSeek smoke used Conda Python: `D:\anaconda\envs\ashare-copilot\python.exe`.
- Initial smoke with Codex bundled Python structured-skipped as `deepseek_sdk_unavailable`.
- After switching to Conda Python, env-live DeepSeek smoke returned ready.
- Initial sandbox network execution structured-skipped as `deepseek_network_error`; after approved network execution, the env-live smoke succeeded.
- `deepseek_sdk_unavailable` and `deepseek_network_error` were both handled by structured paths.

## 8. Safety And Boundary Summary

- DeepSeek API key was not committed.
- Tushare token was not committed.
- No key or token was output.
- `.env`, key files, and `tushare_token.txt` were not read.
- `output`, `fixtures`, and accepted manifest were not written.
- Report V1 artifact was not generated.
- HTML artifact was not generated.
- Markdown or JSON runtime artifact was not generated.
- `official_metric_fact` was not generated.
- `provider_official_conflict` was not generated.
- Provider-vs-official reconciliation was not performed.
- Result does not contain raw prompt.
- Result does not contain raw LLM response.
- Result does not contain raw provider bundle.
- Result does not contain `candidate_items`.
- Result does not contain backend trace.
- Professional preview has no engineering labels.
- Professional preview has no user-responsibility-shifting wording.
- Professional preview has no trading advice.
- English trading phrases and Chinese trading terms continue to be blocked.
- Engineering labels continue to be blocked.

## 9. Explicitly Untouched Areas

The stage did not touch:

- production-level LLM integration
- formal real LLM renderer adapter
- Report V1 builder
- HTML renderer
- PDF download, read, or parse
- table extraction
- metric extraction as official fact
- `official_metric_fact`
- `provider_official_conflict`
- provider-vs-official reconciliation
- `output`
- `fixtures`
- accepted manifest
- `.local_experiments`
- `tushare_token.txt`
- `.env`
- key files
- unrelated mojibake files
- unrelated examples file
- cache PDF
- token/key output
- raw LLM response output
- prompt artifact output
- trading advice output

## 10. Remaining Untracked Items

The working tree still has existing untracked items that were intentionally not handled:

- `.local_experiments/`
- unrelated mojibake files
- unrelated examples file

## 11. Stage Conclusion

- Implementation accepted.
- No blocker.
- This summary document is docs-only.
- This stage completed the controlled real LLM local/manual smoke minimal harness.
- This stage successfully verified real DeepSeek env-live smoke.
- This stage proves that real DeepSeek can produce an acceptable professional preview under the existing model-facing context, safety boundary, and quality check.
- This is still not production LLM integration.
- This is still not a formal real LLM renderer adapter.
- This is still not Report V1 or HTML.
- This is still not official metric verification.
- This is still not provider-vs-official reconciliation.
- This contains no trading advice.
- The next stage should reassess before expanding scope.

Possible future evaluation areas:

- professional brief human review
- controlled real LLM renderer integration planning
- Report V1 integration planning
- official metric extraction and reconciliation

Do not directly enter trading advice or an unbounded full autonomous agent.
