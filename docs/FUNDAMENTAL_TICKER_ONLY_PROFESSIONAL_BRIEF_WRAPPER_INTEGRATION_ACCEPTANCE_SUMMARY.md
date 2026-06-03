# Ticker-only Professional Brief Wrapper Integration Acceptance Summary

## 1. Stage

Ticker-only Professional Brief Wrapper Integration Thin Slice

## 2. Baseline Commits

- implementation commit: `7aea06edd53ffdd17a62069574929fa31f593e2d`
- previous completed stage: LLM Analyst Renderer Handoff Contract + Fake Renderer Integration acceptance summary commit `0e3d556`
- professional compact brief quality acceptance summary commit `e1b63a6`
- controlled real Tushare professional brief acceptance summary commit `d592c72`
- rulebook update commit: `02dcc2a`

## 3. Stage Positioning

This stage connects the controlled ticker-only professional brief path into the existing callable wrapper. It is not a full autonomous agent, not true LLM integration, not Report V1 integration, not the HTML renderer, not official metric verification, and not provider-vs-official reconciliation.

The stage does not generate runtime artifacts. Its goal is to make the existing wrapper closer to the final skill callable entry: a ticker-only request can now enter the controlled Tushare professional compact brief path through the wrapper. This remains a controlled narrow path, not an unbounded agent.

## 4. Changed Files

- `src/fundamental_skill/research_planning/a_share_fundamental_skill_wrapper.py`
- `tests/test_a_share_fundamental_skill_wrapper.py`
- `tests/test_a_share_fundamental_skill_wrapper_safety.py`

## 5. Functional Summary

- Added `input_mode=ticker_only_professional_brief`.
- Added `output_mode=professional_compact_brief`.
- Added `output_mode=professional_compact_brief_and_internal_payload`.
- Wrapper response now includes `professional_compact_brief`.
- Wrapper response now includes `professional_internal_payload`.
- Readiness now includes `has_professional_compact_brief`.
- Readiness now includes `has_professional_internal_payload`.
- The ticker-only branch calls the controlled Tushare professional compact brief pilot through a lazy import.
- The lazy import avoids circular import risk.
- The old `analysis_brief` path remains compatible.
- The old `orchestration_result` path remains compatible.
- The old `compact_response` behavior remains compatible.
- No Report V1, HTML, or output artifact is generated.

## 6. Ticker-only Call Chain

```text
stock_code / ts_code
-> wrapper input_mode=ticker_only_professional_brief
-> controlled_real_tushare_professional_compact_brief_pilot
-> professional_analyst_context / fake_llm or deterministic renderer boundary
-> professional_compact_brief
-> wrapper response
```

The wrapper does not return `provider_candidate_bundle` by default. It does not return `candidate_items` by default. It does not return backend trace by default. `internal_payload` is returned only when `output_mode=professional_compact_brief_and_internal_payload`. That payload is a sanitized summary, not a raw provider bundle.

## 7. Network And Token Boundary

- Tests default to fake or injected clients and do not use network access.
- `env_live` is allowed only under `input_mode=ticker_only_professional_brief` + `tushare_client_mode=env_live` + `allow_network=true`.
- Old `analysis_brief` and `orchestration_result` modes still reject `allow_network=true`.
- `allow_file_writes` is always disallowed.
- Token parameters are not accepted.
- Token fields are not accepted.
- Raw token strings are not accepted.
- `tushare_token.txt` is not read.
- `.env` is not read.
- Tokens are not output.
- Tokens are not written into the commit.

## 8. User-facing Professional Output

`professional_compact_brief` is the user-facing primary view.

It does not show `provider_candidate`, `pending_official_verification`, or `official verification`. It does not show `待核验`, `数据缺口`, or `推理`. It does not show `page`, `snippet`, `source_url`, `sha256`, or `cache_path`.

It does not write phrases that shift responsibility to the user, including `用户自行判断`, `自行跟踪`, `需要用户`, or `建议用户`. It provides professional analytical views. It does not output buy/sell/hold, target price, position sizing, or technical signals. Its `source_note` is `数据来源：Tushare。`

## 9. Test Results

- targeted tests: `126 passed`
- related tests: `267 passed`
- When system Python was unavailable, Codex bundled Python was used.
- Live smoke was not executed because this stage only integrates the wrapper, and the controlled pilot live path had already passed smoke in the previous stage.

## 10. Safety And Boundary Summary

- No real LLM API was called.
- No OpenAI, Claude, Gemini, DeepSeek, or Kimi API was called.
- No LLM API key was read.
- `tushare_token.txt` and `.env` were not read.
- No token was output.
- No live provider was called during tests.
- No `output`, `fixtures`, or accepted manifest was written.
- No Report V1 artifact was generated.
- No HTML artifact was generated.
- No Markdown or JSON runtime artifact was generated.
- No `official_metric_fact` was generated.
- No `provider_official_conflict` was generated.
- No provider-vs-official reconciliation was performed.
- `professional_compact_brief` has no backend trace.
- `professional_compact_brief` has no engineering labels.
- `professional_compact_brief` has no user-responsibility-shifting phrasing.
- `professional_compact_brief` has no trading advice.
- English trading phrases and Chinese trading words continue to be blocked.
- Engineering labels continue to be blocked.

## 11. Explicit No-touch Zones

The stage did not touch true LLM APIs, OpenAI / Claude / Gemini / DeepSeek / Kimi APIs, LLM keys or API keys, CNInfo live paths, Report V1 builder, HTML renderer, PDF download/read/parse, table extraction, metric extraction as official fact, `official_metric_fact`, `provider_official_conflict`, provider-vs-official reconciliation, `output`, `fixtures`, accepted manifest, `.local_experiments`, `tushare_token.txt`, `.env`, unrelated mojibake files, unrelated examples files, cache PDFs, token output, or trading advice output.

## 12. Remaining Untracked Items

- `.local_experiments/`
- unrelated mojibake files
- unrelated examples file

## 13. Stage Conclusion

Implementation is accepted. There is no blocker. This summary doc is docs-only.

This stage completes ticker-only professional brief wrapper integration. It makes the wrapper closer to the final skill callable entry, and ticker-only requests can now enter the controlled professional brief path.

This is still not a true LLM analyst, not a full autonomous agent, not Report V1 or HTML, not official metric verification, and not provider-vs-official reconciliation. It contains no trading advice.

The next stage should reassess before expanding scope. Future work may evaluate controlled real LLM local/manual smoke planning, professional brief human review, Report V1 integration planning, and official metric extraction / reconciliation. Do not directly enter trading advice or an unbounded full autonomous agent.
