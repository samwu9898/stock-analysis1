# Data Provider Abstraction + Tushare Migration Design

Date: 2026-05-26

Stage: Phase 3 Design Documentation Sync Patch.

Status: Phase 0 design documentation completed; Phase 1 provider abstraction skeleton accepted; Phase 2 `AkShareProvider` adapter implemented and accepted; Phase 3 `TushareProvider` MVP design audit completed and synchronized here as the basis for later mocked implementation. This documentation sync does not change code, tests, config, deterministic pipeline behavior, classifier rules, connector behavior, scoring, readiness, HTML / Dashboard behavior, generated output, or regression expectations.

Latest Phase 2 acceptance record:

- `AkShareProvider` is a thin adapter around the existing `RealDataConnector`.
- The default `real_stock_runner` production path still directly uses `RealDataConnector`.
- `ProviderRouter` supports `auto`, `akshare`, `tushare`, and `dual_compare` modes as optional provider-abstraction paths.
- `provider=tushare` still fails closed when no token / provider is available.
- `dual_compare` records comparison intent only; it does not fetch, merge, or change downstream results.
- Phase 2 did not connect real Tushare, read tokens, read local MCP config, call MCP, add network calls, or modify the deterministic pipeline.
- Latest recorded verification after Phase 2 acceptance: full `pytest` `520 passed`; regression suite `passed=47 failed=0 total=47`.

Latest Phase 3 design audit record:

- Phase 3 MVP is a mocked-only `TushareProvider` design for later implementation.
- Phase 3 MVP should add a `TushareClient` abstraction with mocked transport, `TushareProvider` mocked response mapping, canonical raw output, explicit `fetch_status` / `errors` / `source_trace`, token safety, no-token fail-closed behavior, and mock tests only.
- Phase 3 MVP should not require or request a real token, connect MCP, make real network calls in tests, switch `provider=auto` primary behavior, run dual-source comparison, replace news, replace commodity prices, add industry-specific operating indicators, add minute / realtime technical data, or change downstream deterministic behavior.
- Phase 3 mocked implementation does not require Claude / external review. External review is recommended before real API field validation, primary switching, dual-source comparison, real-token smoke, or MCP integration.

## 1. Background And Goals

The current real-data path depends primarily on AkShare. AkShare remains useful as a public-data aggregation source, but the project has observed instability in several endpoints and fetch traces. The user has purchased paid Tushare data access and wants Tushare to become the future primary provider for fundamental and low-frequency market data.

Migration goals:

- Introduce Tushare as the future primary data provider.
- Keep AkShare as fallback and comparison source.
- Preserve the current deterministic fundamental pipeline and its canonical raw-data contract.
- Avoid direct Tushare or AkShare dependencies in classifier, scoring, readiness, Research Intelligence P1.1, HTML Report, or Dashboard logic.
- Keep the current `evidence_pack` schema unchanged unless a later dedicated schema design explicitly changes it.
- Do not modify current regression expected outputs during Phase 1 / Phase 2.
- Do not generate or commit runtime output artifacts.

Non-goals for this stage:

- No real Tushare call.
- No token handling implementation.
- No MCP server integration.
- No technical-analysis provider.
- No changes to P1.1 frozen baseline.

## 2. Current Data Flow Summary

Current real-stock fundamental flow:

```text
RealDataConnector
  -> raw_<code>.json
  -> FundamentalSkillPipeline
  -> fundamental_<code>.json
  -> evidence_pack_<code>.json
  -> HTML Report / Research Intelligence P1.1
```

Key entry points:

- `src/fundamental_skill/real_data_connector.py`
- `src/fundamental_skill/real_stock_runner.py`
- `src/fundamental_skill/data_adapter.py`
- `src/fundamental_skill/ai_analyst/evidence_pack.py`
- `src/fundamental_skill/ai_analyst/research_intelligence_p1_builder.py`

Current responsibilities:

- `RealDataConnector` fetches public data and writes canonical raw JSON blocks.
- `real_stock_runner.py` writes `raw_<code>.json` and `fundamental_<code>.json`.
- `FundamentalSkillPipeline` consumes raw dict/file data and runs adapter, classifier, framework selection, readiness, context, scoring, and result assembly.
- `EvidencePackBuilder` compresses `raw_<code>.json` and `fundamental_<code>.json` into `evidence_pack_<code>.json`.
- HTML and Research Intelligence P1.1 consume evidence-pack-level fields and should not depend on provider-specific API shapes.

## 3. Current Raw Blocks

The current canonical raw structure is:

```text
meta
blocks
fetch_status
errors
```

Current `blocks` include:

- `basic_info`
- `financial_indicator`
- `valuation`
- `business_composition`
- `news`
- `commodity_prices`, when applicable for resource stocks
- `commodity_price_foreign_reference`, when applicable

The provider abstraction should preserve these block names for downstream compatibility.

## 4. Current AkShare Dependencies And Instability Points

Current AkShare-dependent source functions:

- `stock_profile_cninfo` / `stock_individual_info_em`: basic stock and company information.
- `stock_financial_abstract` / `stock_financial_report_sina`: financial abstract, balance-sheet fields, profit-sheet fields, cash-flow fields, R&D, capex, and related derived indicators.
- `stock_value_em`: valuation fields such as PE TTM, PB, PS, and market cap.
- `stock_zygc_em`: business composition / main-business segment rows.
- `stock_news_em`: latest news rows.
- `ExternalCommodityPriceConnector`: external commodity prices for resource-related strategies, currently also backed by AkShare calls.

Known caveats from current validation and hardening:

- `latest_news missing`
- `news: Invalid regular expression: invalid escape sequence: \u`
- `WinError 10013`
- `basic_info` fetch failure traces
- `financial_indicator` fetch failure traces
- `valuation` fetch failure traces
- `business_composition` fetch failure traces

These caveats are upstream data-source issues. They must not be treated as company operating facts by Research Intelligence P1.1 or HTML reporting.

## 5. `evidence_pack` Canonical Fields

Downstream layers rely on these canonical evidence fields.

### `basic_info`

- `stock_code`
- `stock_name`
- `industry`
- `main_business`
- `listing_date`

### `business_composition`

- `period`
- `classification_type`
- `segment_name`
- `revenue`
- `revenue_ratio`
- `gross_margin`
- `cost`
- `profit`
- `profit_ratio`

### `financial_metrics`

- `period`
- `revenue`
- `revenue_yoy`
- `net_profit`
- `net_profit_yoy`
- `deducted_net_profit`
- `gross_margin`
- `net_margin`
- `roe`
- `operating_cashflow`
- `debt_to_asset`
- `inventory`
- `accounts_receivable`
- `contract_liabilities`
- `r_and_d_expense`
- `r_and_d_expense_ratio`
- `capex`

### `valuation_metrics`

- `pe_ttm`
- `pb`
- `ps`
- `market_cap`
- `dividend_yield`

### `latest_news` / `news`

- `title`
- `publish_time`
- `source`
- `url`
- `summary`

### Confidence And Provenance

- `confidence_basis`
- `missing_fields`
- `source_trace_summary`
- `data_limitations`
- `unknown_or_missing_evidence`

### Strategy And P1.1 Inputs

Classifier, scoring, readiness, and P1.1 depend on:

- `basic_info.industry`
- `basic_info.main_business`
- `business_composition.segments`
- `financial_metrics.*`
- `valuation_metrics.*`
- `latest_news`
- `raw_blocks`
- `stock.strategy_type`
- `stock.sub_type`
- `commodity_prices`, for resource strategies
- `source_trace_summary`
- `risk_flags`
- `enhanced_must_track_indicators`

Provider migration must preserve these fields and their absence semantics.

## 6. Tushare Coverage Mapping

The user has paid Tushare access at the 6000-point tier. The unlocked scope is mainly suitable for fundamental data, financial statements, macro data, low-frequency market data, and reference datasets.

Phase 3 mapping notes:

- Endpoint names below are placeholders / equivalent API concepts for mocked implementation design.
- This document does not claim that the user's exact endpoint permissions have been verified through a real API call.
- Phase 3 tests should use mocked responses only.
- Source-specific names stay inside `TushareClient` / `TushareProvider`; downstream raw block names stay canonical.

### Fields That Can Directly Replace AkShare

Basic information:

- Tushare can cover stock basic identity fields such as code, name, market/listing status, industry, and listing date.
- Mapping target: `basic_info.stock_code`, `basic_info.stock_name`, `basic_info.industry`, `basic_info.listing_date`.
- `basic_info.main_business` should be verified through company-profile or business-scope endpoints before replacing the current CNInfo-derived field.

Low-frequency market data:

- Tushare daily, weekly, and monthly market data can cover low-frequency OHLCV and historical market data.
- These are not currently core inputs to the deterministic fundamental pipeline, but they are useful for later comparison, report context, or technical-skill preparation.

Financial statements and indicators:

- Tushare income statement, balance sheet, cash-flow statement, and financial-indicator APIs can cover most current `financial_metrics`.
- Mapping targets include `revenue`, `net_profit`, `deducted_net_profit`, `gross_margin`, `net_margin`, `roe`, `operating_cashflow`, `debt_to_asset`, `inventory`, `accounts_receivable`, `contract_liabilities`, `r_and_d_expense`, `r_and_d_expense_ratio`, and `capex`.
- Derived fields such as `revenue_yoy` and `net_profit_yoy` may be taken directly if available or derived consistently by the provider adapter.

Valuation:

- Tushare daily-basic style valuation data can cover PE TTM, PB, PS or PS TTM, total market value, circulating market value, and dividend-yield style fields when available.
- Mapping targets: `valuation_metrics.pe_ttm`, `valuation_metrics.pb`, `valuation_metrics.ps`, `valuation_metrics.market_cap`, `valuation_metrics.dividend_yield`.

Business composition:

- If the relevant main-business composition interface is available under the user's permission, Tushare can replace AkShare `stock_zygc_em`.
- Mapping targets: `business_composition.period`, `classification_type`, `segment_name`, `revenue`, `revenue_ratio`, `gross_margin`, `cost`, `profit`, and `profit_ratio`.
- This should be verified with mocked responses first. Any real local-response validation should be handled only under a later explicit acceptance step before using it as primary.

### Fields That Can Enhance `evidence_pack`

Reference data:

- Pledge data can enhance risk context.
- Share unlock data can enhance supply-pressure and governance context.
- Buyback data can enhance capital-allocation context.
- Increase/decrease holding data can enhance insider/shareholder-change context.
- Top-list / abnormal trading data can enhance event context, but should not drive fundamental conclusions by itself.
- Margin financing and securities-lending data can enhance market-structure context.

Special datasets:

- Concept boards and constituents can help compare theme membership, but must not by themselves raise strategy classification confidence.
- Money flow can be stored as contextual evidence, but should not directly affect current fundamental scoring.
- Broker golden-stock data can be stored as external sentiment / reference context, but should not be treated as fundamental evidence.

Macro data:

- Macro data can support later research context or P1/P1.2 style questions.
- It should not directly alter current deterministic scoring or P1.1 driver logic in the migration phases.

### Fields Not Covered Or Uncertain

News and announcements:

- Tushare should not be assumed to fully replace current `stock_news_em` news coverage.
- AkShare or a future CNInfo / exchange-announcement provider should remain available for `latest_news` / `news`.

### Phase 3 Placeholder Endpoint To Canonical Raw Mapping

Phase 3 MVP should map mocked Tushare-like responses into existing canonical raw blocks only:

| Placeholder endpoint | Canonical raw block | Canonical fields |
| --- | --- | --- |
| `stock_basic` or equivalent | `basic_info` | `stock_code`, `stock_name`, `industry`, `listing_date` |
| profile / business-scope equivalent | `basic_info` | `main_business` remains uncertain; default to missing / fallback until verified |
| `income` | `financial_indicator` | `revenue`, `net_profit`, `deducted_net_profit`, `r_and_d_expense` |
| `balancesheet` | `financial_indicator` | `debt_to_asset`, `inventory`, `accounts_receivable`, `contract_liabilities` |
| `cashflow` | `financial_indicator` | `operating_cashflow`, `capex` |
| `fina_indicator` | `financial_indicator` | `revenue_yoy`, `net_profit_yoy`, `gross_margin`, `net_margin`, `roe`, `r_and_d_expense_ratio` |
| `daily_basic` or equivalent | `valuation` | `pe_ttm`, `pb`, `ps`, `market_cap`, `dividend_yield` |
| `fina_mainbz` or equivalent, if available | `business_composition` | `period`, `classification_type`, `segment_name`, `revenue`, `revenue_ratio`, `gross_margin`, `cost`, `profit`, `profit_ratio` |
| news equivalent | `news` | Not replaced in Phase 3 MVP; record missing / fallback to a future news provider |

Phase 3 must not rename raw blocks to downstream evidence names. In particular, raw output remains `financial_indicator` and `valuation`; it does not introduce raw blocks named `financial_metrics` or `valuation_metrics`.

Commodity prices:

- Current `commodity_prices` are provided by `ExternalCommodityPriceConnector`.
- Tushare coverage for the exact commodity spot/futures series, units, and contract selection required by resource strategies must be separately validated.
- Keep AkShare / future commodity provider fallback until a dedicated commodity-data design is completed.

Industry-specific operating indicators:

- AI datacenter PUE, rack-up rate, cabinet count, MW scale, liquid-cooling revenue share, customer capex cycle, and real order backlog are not automatically solved by generic Tushare data.
- CXO backlog, customer concentration, overseas / U.S. exposure, CDMO utilization, clinical project count, project cancellation, and compliance events still require annual reports, announcements, or future specialized providers.
- Satellite capacity utilization, transponder / bandwidth capacity, remaining useful life, launch/failure/insurance events, and customer renewal details still require specialized disclosure sources.

Minute-level and realtime technical data:

- The current 6000-point access is mainly appropriate for fundamental, financial, macro, and low-frequency data.
- Minute K-line, realtime quote, intraday signal, and live technical workflows require separate permission confirmation or other providers.

## 7. Data Provider Abstraction Design

Recommended directory:

```text
src/fundamental_skill/data_providers/
  __init__.py
  base.py
  schemas.py
  akshare_provider.py
  tushare_provider.py
  provider_router.py
  tushare_client.py
  token_safety.py
```

Core principles:

- Providers output the current canonical raw blocks.
- Downstream modules do not directly depend on Tushare or AkShare.
- `evidence_pack` schema remains unchanged.
- Classifier, scoring, readiness, Research Intelligence P1.1, HTML Report, and Dashboard do not directly know the data source.
- `AkShareProvider` wraps the existing `RealDataConnector` and is complete as of Phase 2.
- `TushareProvider` should later convert Tushare responses into the same canonical raw blocks; this starts no earlier than Phase 3.
- Provider adapters own all source-specific API names, response shapes, unit conversions, and source traces.
- Missing or unavailable provider fields should continue to flow through `fetch_status.*.missing_fields`.

Suggested conceptual interface:

```python
class DataProvider:
    name: str

    def fetch_to_raw_json(
        self,
        stock_code: str,
        *,
        force_refresh: bool = False,
    ) -> dict:
        ...
```

`schemas.py` should keep provider-facing structures lightweight and separate from downstream Pydantic models unless a later phase needs stricter validation.

### Phase 2 AkShareProvider Adapter Status

Phase 2 implemented and accepted `src/fundamental_skill/data_providers/akshare_provider.py`.

Accepted behavior:

- `name = "akshare"`.
- The adapter internally wraps `RealDataConnector`.
- `fetch_to_raw_json(stock_code, force_refresh=False)` delegates directly to `RealDataConnector.fetch_to_raw_json(...)`.
- The adapter returns the connector raw dict without reshaping or rewriting `meta`, `blocks`, `fetch_status`, or `errors`.
- The canonical raw top-level structure remains `meta`, `blocks`, `fetch_status`, and `errors`.
- Existing block names remain unchanged, including `basic_info`, `financial_indicator`, `valuation`, `business_composition`, `news`, and optional `commodity_prices` / `commodity_price_foreign_reference`.
- Fake connector / connector factory injection is supported for equivalence tests.
- The default production `real_stock_runner` path was not changed and still directly uses `RealDataConnector`.

Phase 2 explicitly did not add real Tushare access, token reading, MCP access, new network calls, classifier changes, scoring / readiness changes, evidence-pack schema changes, Research Intelligence P1.1 changes, HTML / Dashboard changes, regression expected changes, or committed output artifacts.

### Phase 3 TushareProvider MVP Scope

Phase 3 MVP should design / later implement only:

- `TushareClient` abstraction.
- Mocked transport.
- `TushareProvider` mocked response mapping.
- `basic_info`.
- `financial_indicator`.
- `valuation`.
- `business_composition`, where the interface is available or represented by mocked permission-positive responses.
- `news` explicitly marked as missing / fallback.
- `fetch_status`, `errors`, and `source_trace`.
- Token safety.
- No-token fail-closed behavior.
- Mock tests only.

Phase 3 MVP must not do:

- Real token smoke.
- MCP integration.
- Real network calls in tests.
- `provider=auto` primary switch.
- Dual-source comparison.
- News replacement.
- `commodity_prices` replacement.
- Industry-specific operating indicators.
- Minute / realtime technical data.
- Classifier, scoring, or readiness changes.
- `evidence_pack` schema changes.
- HTML / P1.1 changes.
- Regression expected changes.

### Phase 3 Canonical Raw Output

`TushareProvider.fetch_to_raw_json(...)` must output the existing canonical raw structure:

```text
meta
blocks
fetch_status
errors
```

`blocks` must keep the existing canonical raw names:

- `basic_info`
- `financial_indicator`
- `valuation`
- `business_composition`
- `news`

Phase 3 must not introduce a new downstream schema and must not rename raw blocks to `financial_metrics` or `valuation_metrics`. Adapter and evidence-pack layers may continue to expose downstream names, but provider raw output remains compatible with the current connector contract.

Each `fetch_status.<block>` should record non-secret diagnostics such as `success`, `error`, `missing_fields`, `fetched_at`, `source_trace`, `warnings`, and source name. `source_trace` should record provider/function names, canonical field names, source periods, derivation flags, units, and row counts where useful; it must not record credentials, MCP URLs, or local config values.

### Phase 3 Missing And Fallback Semantics

All missing, unavailable, or failed data must be explicit in `fetch_status`, `errors`, or `missing_fields`. These states must not become company operating facts.

| Scenario | Required Phase 3 behavior |
| --- | --- |
| Tushare field missing | Keep the field absent or `None`; add the canonical field to `missing_fields`; use warnings if the block otherwise succeeded. |
| Endpoint permission unavailable | Return an empty or partial block; mark the block failed or partial in `fetch_status`; use a sanitized `permission_denied` style error; include missing canonical fields. |
| Empty dataframe / empty response | Return an empty block list; mark `success=False`; use `error="empty_response"` or equivalent; include expected missing fields. |
| API error | Mark the affected block failed; store only sanitized error text; add a block-level error entry. |
| No token | `provider=tushare` fails closed before real access; do not call the client and do not fabricate data. |
| Rate limit | Mark the affected block failed or partial; store sanitized `rate_limit` error; include missing fields. |
| Malformed response | Mark the affected block failed; use sanitized `malformed_response`; include missing fields. |
| `business_composition` unavailable | Keep `business_composition: []`; add `business_composition.segments` or expected segment fields to `missing_fields`; record unavailable / permission status. |
| `news` unavailable | Keep `news: []`; mark news missing / fallback; do not claim Tushare replaces news in MVP. |

## 8. ProviderRouter Design

Supported provider modes:

- `provider=auto`
- `provider=tushare`
- `provider=akshare`
- `provider=dual_compare`

Routing rules:

- `auto`: use Tushare when token/client is available; otherwise fall back to AkShare.
- `tushare`: use only Tushare; if token/client is unavailable, fail closed with a clear non-secret error.
- `akshare`: preserve current behavior.
- `dual_compare`: Phase 2 records comparison intent only and does not fetch or merge. A later comparison phase may generate provider-separated AkShare and Tushare outputs for review, but must not automatically merge data.

Phase 2 accepted behavior:

- `provider=akshare` can select the `AkShareProvider` optional path.
- `provider=auto` selects AkShare when no usable Tushare provider is available.
- `provider=tushare` still fails closed without a token / provider.
- `dual_compare` does not automatically merge, fetch, or change results.
- The router is not wired into the default `real_stock_runner` production path.

The router should not change downstream output semantics. It only decides which provider produces canonical raw JSON when the optional provider-abstraction path is used.

## 9. Token And MCP Security Design

Required security rules:

- Tushare token is allowed only from environment variables or local MCP configuration.
- Recommended environment variable name: `TUSHARE_TOKEN`.
- Phase 3 mocked implementation does not require a real token.
- `.env` must remain in `.gitignore`.
- `.env.example` may be added later, but it may only contain:

```text
TUSHARE_TOKEN=<TUSHARE_TOKEN>
```

- No real token may enter code, documentation, tests, logs, output artifacts, fixtures, commits, or review comments.
- Logs and errors must mask token-like values.
- All token-like strings must be masked in exceptions, object representations, `fetch_status`, `errors`, logs, and test diagnostics.
- Tests must use fake token values and monkeypatching.
- Documentation may only use `<TUSHARE_TOKEN>` as a placeholder.
- MCP URL text from local configuration must not be written into the repository.
- Source traces must record provider/function names and field provenance, not credentials or local connection strings.
- Phase 2 does not require a real token. Phase 3 should continue to use mocks / fake tokens until an explicit real-token acceptance step is designed.
- `provider=tushare` with no token must fail closed.
- Real-token smoke must be a later local-only explicit acceptance step, not part of Phase 3 mocked implementation or CI.

Recommended masking behavior:

- Full token is never printed.
- Safe display should be either `<masked>` or a short masked form that cannot reconstruct the secret.
- Exception wrappers should sanitize messages before they are logged or stored in `fetch_status`.

## 10. MCP / SDK / HTTP Access Decision

Business logic should not directly call the MCP server.

Recommended layering:

```text
ProviderRouter
  -> TushareProvider
  -> TushareClient
  -> transport
```

Possible transports:

- Python Tushare SDK
- HTTP API
- Local MCP-backed transport

MVP preference:

- Use a mockable `TushareClient` abstraction first.
- Python SDK is the likely MVP transport because it is straightforward to mock in unit tests.
- HTTP can be added later if SDK limitations appear.
- MCP is better treated as a local tool-layer option and should not become a hard dependency of the deterministic pipeline.

This keeps provider selection, credentials, transport mechanics, and API-shape normalization outside classifier, scoring, readiness, HTML, and P1.1.

## 11. Dual-Source Comparison Design

Comparison mode should generate provider-separated artifacts in a temporary or explicitly chosen comparison directory, not the normal production `output` path unless the user explicitly requests it.

For the same stock sample set, generate:

- AkShare `raw` / `fundamental` / `evidence_pack`
- Tushare `raw` / `fundamental` / `evidence_pack`
- Diff report

Comparison dimensions:

- `basic_info`
- `business_composition`
- `financial_metrics`
- `valuation_metrics`
- `strategy_type`
- `sub_type`
- `status`
- `confidence`
- `fundamental_score`
- `missing_fields`
- `source_trace_summary`
- P1.1 research-question drift

Diff report should classify differences:

- expected provider-field improvement
- harmless formatting / unit difference
- missing-field improvement
- missing-field regression
- classification drift
- scoring/readiness drift
- P1.1 question drift
- safety or boundary concern

No automatic data merge should occur in `dual_compare`.

## 12. Testing And Regression Strategy

New test categories for later implementation:

- Fake provider tests for canonical raw-block shape.
- `TushareClient` mocked response tests.
- Mocked `TushareProvider` tests with representative Tushare-like responses.
- `TushareProvider` mapping tests for `basic_info`, `financial_indicator`, `valuation`, `business_composition`, and missing `news`.
- `ProviderRouter` priority and fallback tests.
- ProviderRouter tests with an injected `TushareProvider`.
- No-token fail-closed tests.
- Permission-denied, empty-response, malformed-response, and rate-limit tests.
- Token masking tests for logs, errors, object representations, `fetch_status`, and provider/client exceptions.
- Canonical raw shape tests for `meta`, `blocks`, `fetch_status`, `errors`, and unchanged raw block names.
- Dual-source comparison smoke tests.
- AkShare adapter equivalence tests proving current behavior is unchanged.

Regression rules:

- Phase 1 and Phase 2 must not modify regression expected outputs.
- Phase 3 mocked implementation must not modify regression expected outputs.
- Current regression suite remains the baseline.
- Any provider migration must prove that `provider=akshare` remains equivalent to current behavior.
- CI tests must not make real Tushare API calls or require real credentials.

Before switching primary provider:

- Run full `pytest`.
- Run the current regression suite with all 47 samples.
- Run representative P1.1 samples covering positive, validation, boundary, unsupported, and caveat cases.
- Run HTML report schema / prompt / renderer tests.
- Review dual-source diff reports for classification, confidence, missing-field, and P1.1 drift.

## 13. Phase Roadmap

Phase 0: design doc. Completed.

- Record the migration design and safety boundaries.
- No code change.

Phase 1: provider abstraction skeleton. Implemented and accepted.

- Add provider directory and lightweight base/schema/router/token-safety skeletons.
- Do not call real Tushare.
- Keep default behavior unchanged.

Phase 2: `AkShareProvider` adapter. Implemented and accepted.

- Wrap existing `RealDataConnector`.
- Prove current raw/fundamental/evidence behavior is unchanged.
- Keep regression expected unchanged.
- Keep the default `real_stock_runner` path directly on `RealDataConnector`.
- Do not call real Tushare, read tokens, read MCP config, call MCP, or add network calls.

Phase 3: `TushareProvider` MVP.

- Implement mockable Tushare client with mocked transport only.
- Map mocked responses for basic info, financial statements / indicators, valuation, and business composition.
- Mark news as missing / fallback; keep fallback for commodity prices and specialized fields.
- Phase 3 is the first phase for `TushareProvider` MVP work. It still does not require a real token before a separate explicit real-token acceptance step; use mocks / fake tokens for implementation tests.

Recommended Phase 3 implementation sequence:

- 3.1 `TushareClient` abstraction with mocked transport only.
- 3.2 `TushareProvider` mocked mapping into canonical raw blocks.
- 3.3 `ProviderRouter` injection tests.
- 3.4 No-token / masking tests.
- 3.5 Optional local-only smoke design, not executed by default.

Phase 3 acceptance criteria:

- No real token required.
- No network calls in tests.
- Canonical raw shape preserved.
- Mocked Tushare responses map to expected raw blocks.
- No downstream behavior change.
- Default `real_stock_runner` unchanged.
- Classifier, scoring, readiness, `evidence_pack`, HTML, and Dashboard unchanged.
- Full `pytest` green.
- Regression suite `passed=47 failed=0 total=47`.
- No token or MCP URL leak.
- Regression expected files unchanged.

Phase 4: dual-source comparison smoke.

- Generate separated AkShare and Tushare comparisons.
- Produce drift report.
- No automatic merge.

Phase 5: config switch to primary Tushare.

- Enable Tushare primary behind explicit config.
- Keep AkShare fallback.
- Fail closed for `provider=tushare` without token.

Phase 6: docs / regression freeze.

- Freeze provider behavior once accepted.
- Update documentation and regression strategy only after review.

## 14. Technical Skill Forward Look

Current Tushare 6000-point access is mainly suitable for:

- fundamental data
- financial statements and financial indicators
- macro data
- daily / weekly / monthly low-frequency market data

Future technical-analysis skill requirements may include:

- minute K-line
- realtime quotes
- intraday trends
- intraday signal generation
- live market monitoring

Those requirements need separate permission confirmation. If Tushare minute or realtime access is not available or not stable enough, future technical providers may include RQData, QMT, or broker realtime quote sources.

Technical-analysis data-source integration is explicitly out of scope for this migration documentation stage.

## 15. Current Go / No-Go Recommendation

Recommendation: Freeze Phase 2 baseline and proceed only to a separately scoped Phase 3 `TushareProvider` MVP design / implementation cycle.

Phase 3 mocked-only implementation does not require Claude / external audit before starting, because it does not use a real token, connect real APIs, connect MCP, switch primary provider, or change downstream behavior. If the scope expands into real API field mapping, primary provider switching, dual-source comparison, real-token smoke, or MCP integration, request Claude or another external audit before implementation / acceptance.

Completed Phase 1 / Phase 2 scope:

- Provider abstraction skeleton.
- Schema placeholders needed by the router and fake providers.
- Provider router config parser.
- Token masking helper.
- Fake-provider tests.
- `AkShareProvider` adapter around `RealDataConnector`.
- AkShare adapter equivalence tests.
- ProviderRouter tests for AkShare fallback, Tushare fail-closed behavior, and `dual_compare` no-merge behavior.

Phase 3 must not:

- call real Tushare
- require a real token
- depend on local MCP config
- change default behavior
- change `evidence_pack`
- change Research Intelligence P1.1
- change HTML Report or Dashboard
- change classifier, scoring, readiness, or deterministic pipeline behavior
- change regression expected outputs
- generate committed runtime artifacts

No-Go triggers:

- Any design that exposes credentials to code, docs, tests, logs, output, fixtures, or commits.
- Any design that makes MCP server availability a hard deterministic pipeline dependency.
- Any provider output that forces downstream schema changes before a dedicated schema migration review.
- Any unreviewed classification, scoring, readiness, P1.1, HTML, or regression change.
