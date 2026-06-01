# Fundamental Live Network Discovery Client Readiness Gate

Status: docs-only readiness gate

This document defines the safety boundary for a future live official-source metadata discovery client. It does not approve or implement a network client, real network access, PDF download, PDF parsing, provider fallback, metric extraction, Report V1 integration, fixtures, output baselines, or accepted manifests.

## 1. Stage Name And Current Baseline

Stage name: Live Network Discovery Client Readiness Gate.

Recent key commits:

- `05cfa02 docs: add post metadata adapter next-slice reassessment plan`
- `3a3ead4 docs: accept official source discovery metadata adapter`
- `f6461f8 feat: add official source discovery metadata adapter`
- `227e069 docs: add official source discovery metadata readiness gate`
- `625f1ac docs: accept request synthetic dry-run integration`
- `caef73b feat: add request synthetic dry-run integration`

Current baseline:

- A metadata-only fake / injected adapter already exists.
- There is no real live discovery client.
- There is no real network client.
- There is no provider adapter in this path.
- There is no PDF parser or PDF table extraction.
- There is no metric extraction.
- There is no Report V1 integration.
- There is no output baseline, fixture, or accepted manifest for this stage.
- There is no token use.
- This stage is readiness planning only and must not implement production behavior.

## 2. Current Capability Map

The current system is understood to have the following readiness capabilities:

- `security_identity.v1`
- `official_disclosure_discovery_request.v1`
- `request_synthetic_dry_run_integration`
- `official_source_discovery_adapter` metadata-only behavior
- `official_disclosure_discovery_candidate.v1`
- official source registry / locator boundary
- synthetic dry-run path
- official verification data gate
- recursive safety scan
- no-IO / no-network fake metadata pipeline

These capabilities are sufficient to plan a live discovery boundary, but not sufficient to turn on real network discovery.

## 3. Current Gap Map

The current system is not yet expected to have:

- real live official metadata discovery client
- CNInfo / SSE / SZSE / BSE live query behavior
- network client abstraction
- exact domain allowlist enforcement against real responses
- redirect handling against real responses
- timeout / retry / rate-limit policy in a live environment
- content-type enforcement against live responses
- malformed live response handling
- source freshness policy
- live response to metadata adapter handoff
- download/cache acquisition
- PDF parser / table extraction
- metric extraction
- provider reconciliation
- Evidence Panel / Research Pack integration

This gap map is intentional. The next approved implementation must close only the metadata discovery boundary, not downstream document or metric processing.

## 4. Questions This Gate Resolves

This readiness gate resolves the planning questions below:

- A future network client must be a constrained metadata discovery client, not a generic fetcher.
- The first implementation should prefer an injected fake client interface and fake response adapter.
- A real client must be disabled by default.
- Official domain allowlists must be explicit, host-based, and source-family scoped.
- Redirects must be bounded and every hop must satisfy allowlist and content policy.
- Timeout, retry, and rate-limit behavior must fail closed into structured discovery errors.
- Content type must be used only to validate metadata discovery responses.
- The path must remain metadata-only.
- PDF download must be impossible in the discovery stage.
- PDF parsing must be impossible in the discovery stage.
- Provider fallback must be impossible in the discovery stage.
- A live response must first become a metadata-only record.
- The metadata-only record must be handed to the existing `official_source_discovery_adapter`.
- Blocked, rejected, and review-required states must be explicit.
- Third-party audit is not required for this docs-only gate, but is recommended or required for specific future live-client work described below.

## 5. Network Client Abstraction Policy

Future client input:

- The client input must be `official_disclosure_discovery_request.v1` or a request-derived typed metadata query.
- The request remains the hard constraint for stock code, exchange, period, announcement type, and source family.
- Arbitrary URL fetch is not allowed.
- A user-provided URL must not be requested directly.
- Source family and domain allowlist must be checked before any future request is made.

Future client output:

- The client output may only be a metadata response.
- The client must not return PDF bytes.
- The client must not return PDF text.
- The client must not return extracted tables.
- The client must not return extracted metrics.
- The client must not return local cache paths, output paths, fixture paths, or accepted manifest paths.

Required structured outcomes:

- `transport_error`
- `timeout`
- `rate_limited`
- `redirect_rejected`
- `domain_rejected`
- `content_type_rejected`
- `malformed_response`
- `empty_result`
- `policy_rejected`

Forbidden client responsibilities:

- The client must not directly generate `official_metric_fact`.
- The client must not directly generate a registry entry.
- The client must not directly generate a locator result.
- The client must not write output, fixtures, or accepted manifests.
- The client must not call provider libraries or fallback paths.

## 6. Injected Fake Client Vs Real Client Policy

Readiness-stage policy:

- This stage is docs-only.
- No client implementation is approved by this document.
- No real network behavior is approved by this document.

Future first implementation policy:

- The first implementation should prioritize an injected fake client interface and fake response adapter.
- Tests must default to injected fake responses only.
- Real network tests must not enter the default pytest suite.
- The fake client must exercise the same metadata-only handoff shape expected from the future real client.

Future real client policy:

- The real client must be disabled by default.
- The real client requires separate approval.
- The real client requires separate third-party audit before acceptance.
- The real client must not read token files, `.env`, or `tushare_token.txt`.
- The real client must not call AkShare, Tushare, or provider libraries.
- The real client must not introduce provider fallback.
- The real client must not download, cache, or parse PDF files.

## 7. Official Domain Allowlist Policy

Future allowlist must be source-family scoped and exact-host based.

Proposed initial host decisions:

| Source family | Allowed exact hosts | Explicitly not allowed by default |
| --- | --- | --- |
| CNInfo | `www.cninfo.com.cn`, `static.cninfo.com.cn` | `cninfo.com.cn` apex host unless separately approved |
| SSE | `www.sse.com.cn` | `sse.com.cn` apex host unless separately approved |
| SZSE | `www.szse.cn` | `szse.cn` apex host unless separately approved |
| BSE | `www.bse.cn` | `bse.cn` apex host unless separately approved |

Allowlist rules:

- No wildcard matching.
- No substring matching.
- Host-based matching only.
- Path or query strings containing an allowlisted host string must not be treated as host validation.
- Userinfo URLs are blocked.
- Encoded hosts must be normalized before validation.
- Punycode hosts must be normalized before validation.
- Trailing-dot hosts must be normalized before validation.
- Mixed-case hosts must be normalized to lower case before validation.
- A non-allowlisted domain is rejected.
- A third-party mirror is rejected.
- A search engine result is rejected.
- A provider endpoint is rejected.

Any later need to allow an apex host or additional official host must be treated as a policy change requiring explicit review.

## 8. Redirect Policy

Future redirect policy:

- The client must not silently follow cross-domain redirects.
- Redirect chain length must be bounded; proposed maximum is 3 hops.
- Every redirect hop must be allowlisted for the same source family.
- Redirect to a non-allowlisted domain is rejected.
- Redirect to a download or binary endpoint during metadata discovery is rejected.
- Malformed redirect targets are rejected.
- URL shorteners are rejected.
- Tracking interstitials are rejected.
- Third-party interstitials are rejected.

This policy is for future implementation only. This readiness stage must not request any URL.

## 9. Content-Type Policy

Metadata discovery may consider only the following content types:

- `application/json`
- `text/html`

`text/plain` is rejected by default. It may be allowed only for a specific official metadata endpoint after separate review, with no parser promotion and no binary handling.

Forbidden content types:

- `application/pdf`
- `application/octet-stream`
- zip / archive content
- image content
- binary content
- unknown content type

Content-type enforcement:

- PDF content type must not trigger a download in the discovery stage.
- Binary content type is blocked.
- Content-type mismatch must fail closed.
- Content type may only validate a metadata response.
- Content type must not trigger a PDF parser, table extractor, metric extractor, or cache writer.

## 10. No-Download / No-Parser Policy

Discovery client behavior is limited to reading metadata responses.

The discovery stage must not:

- download PDF bytes
- save PDF files
- calculate `downloaded_file_sha256`
- create a local cache
- write fixtures
- write output
- write accepted manifests
- run a PDF parser
- run table extraction
- run metric extraction
- generate official metric facts
- generate provider-official conflicts

The only allowed successful product is a metadata-only record, which is then handed to the existing metadata-only adapter path.

## 11. Timeout / Retry / Rate-Limit Policy

Future live behavior must be bounded and conservative:

- Timeout must be finite and conservative.
- Retry count must be bounded.
- Retry is allowed only for transient safe errors.
- Infinite retry is forbidden.
- Rate limits must fail closed.
- Retry exhaustion becomes a blocked discovery error.
- Timeout becomes a blocked discovery error.
- Rate limit becomes `blocked` or `retry_later` and must not generate a candidate.
- All errors must be structured and must not escape as uncontrolled exceptions.

The client must preserve enough structured context for review without storing response bodies that would violate metadata-only policy.

## 12. Source Freshness Policy

Future client freshness behavior:

- The client must expose `freshness_status`.
- The client must not query the "latest reporting period" as default behavior.
- The request remains the hard constraint.
- Missing `disclosure_date` is blocked.
- A stale response should be `review_required` unless the request explicitly allows historical disclosures.
- A duplicate disclosure should be `review_required`.
- A correction or revised announcement should be `review_required` unless the request explicitly targets that announcement type.
- Freshness must not automatically promote a candidate to verified.

Freshness is an advisory and blocking signal, not a replacement for request matching, adapter validation, or official verification.

## 13. Metadata-Only Response Shape

Future live metadata response records should contain only metadata fields:

- `schema_version`
- `request_id`
- `source_family`
- `source_domain`
- `normalized_url`
- `source_url`
- `source_title`
- `disclosure_date`
- `stock_code`
- `exchange`
- `company_name_hint`
- `period_key`
- `period_end_date`
- `announcement_type`
- `source_type`
- `content_type`
- `artifact_kind`
- `is_downloaded=false`
- `discovery_status`
- `freshness_status`
- `policy_decisions`
- `error_code`
- `error_message`
- `not_for_trading_advice=true`

The response record must not contain:

- PDF bytes
- PDF text
- table extraction
- metrics
- `local_cache_path`
- `downloaded_file_sha256`
- output path
- fixture path
- accepted manifest path

`not_for_trading_advice=true` is mandatory. Missing or false values must be rejected.

## 14. Handoff To Metadata Adapter

Future handoff sequence:

1. Request-derived typed metadata query is created from `official_disclosure_discovery_request.v1`.
2. Future client receives only the typed query, not arbitrary URLs.
3. Live response is normalized into a metadata-only record.
4. Metadata-only record is passed to the existing `official_source_discovery_adapter`.
5. The adapter performs request-to-metadata matching.
6. Existing discovery candidate validation remains in force.

Boundary rules:

- The live client must not bypass `official_source_discovery_adapter`.
- The live client must not bypass discovery candidate validation.
- The request remains the hard constraint.
- The adapter remains responsible for request-to-metadata matching.
- The live client must not directly generate registry entries, locator results, verified facts, or metric facts.

## 15. Fail-Closed Error Model

The future client must fail closed for at least these conditions:

- `invalid_request`
- `unsupported_source_family`
- `non_allowlist_domain`
- `redirect_rejected`
- `content_type_rejected`
- `timeout`
- `retry_exhausted`
- `rate_limit`
- `network_unavailable`
- `malformed_response`
- `empty_result`
- `missing_source_title`
- `missing_disclosure_date`
- `missing_source_url`
- `period_mismatch`
- `announcement_type_mismatch`
- `stock_code_mismatch`
- `company_mismatch_when_verifiable`
- `duplicate_candidate`
- `multiple_plausible_candidates`
- `provider_fallback_attempt`
- `pdf_download_attempt`
- `parser_attempt`
- `output_fixture_manifest_write_attempt`
- `forbidden_marker`
- `not_for_trading_advice_invalid`

Error handling rules:

- `blocked` means no candidate is generated.
- `rejected` means the candidate or response cannot proceed.
- `review_required` means the response may be preserved as metadata for human review, but must not become verified automatically.
- Provider fallback, PDF download, parser invocation, and output/fixture/manifest writes are policy violations, not recoverable discovery outcomes.

## 16. Future Implementation Expected Files

Readiness stage:

- Only this docs readiness file is allowed.

Future implementation, if separately accepted later, may consider:

Production:

- `src/fundamental_skill/data_verification/live_network_discovery_client.py`
- `src/fundamental_skill/data_verification/__init__.py` only if public API exposure is required

Tests:

- `tests/test_live_network_discovery_client.py`
- `tests/test_live_network_discovery_client_safety.py`

Optional files requiring separate approval:

- network client abstraction helper file
- source-family-specific mapper file
- official domain policy file

These optional files may be changed only after a separate implementation readiness / acceptance step.

## 17. Future Implementation Forbidden Files

Future implementation must not modify or create:

- provider adapter
- Report V1 generator
- accepted manifest
- output baseline
- fixtures
- examples
- `.local_experiments`
- `tushare_token.txt`
- `.env`
- unrelated mojibake files
- PDF parser
- PDF table extractor
- metric extraction
- Research Pack implementation
- Evidence Panel implementation
- `official_metric_fact` generation
- `provider_official_conflict` generation
- `official_source_discovery_adapter.py`, unless a handoff boundary bug is found and work stops first for explanation
- request / identity / registry / locator / validators / schemas, unless explicitly approved

These forbidden areas keep live discovery from expanding into provider reconciliation, document parsing, investment research generation, or persistent output production.

## 18. Future Tests

Future implementation should plan at least:

- injected fake client success path
- CNInfo metadata response normalized
- SSE metadata response normalized
- SZSE metadata response normalized
- BSE metadata response normalized
- non-allowlist domain rejected
- path/query allowlist spoof rejected
- userinfo URL rejected
- cross-domain redirect rejected
- malformed redirect rejected
- timeout modeled as blocked
- retry exhaustion modeled as blocked
- rate limit modeled as blocked
- malformed response rejected
- empty result blocked
- content-type PDF rejected without download
- binary content-type rejected
- no PDF download
- no parser
- no provider fallback
- no output / fixture / manifest write
- handoff to `official_source_discovery_adapter`
- no direct registry / locator / fact generation
- safety marker nested rejected
- real network client disabled by default

Default tests must use injected fake clients only. Real network tests, if later approved, must be opt-in and isolated from the default suite.

## 19. Regression Subset

After a future implementation, recommended regression subset:

- `tests/test_live_network_discovery_client.py`
- `tests/test_live_network_discovery_client_safety.py`
- `tests/test_official_source_discovery_adapter.py`
- `tests/test_official_source_discovery_adapter_safety.py`
- `tests/test_request_synthetic_dry_run_integration.py`
- `tests/test_request_synthetic_dry_run_integration_safety.py`
- `tests/test_official_disclosure_request.py`
- `tests/test_official_disclosure_request_safety.py`
- `tests/test_official_disclosure_discovery_candidate.py`
- `tests/test_official_disclosure_discovery_candidate_safety.py`
- `tests/test_official_verification_safety.py`

If `schemas.py` or `validators.py` is modified, the official verification schema / validator subset must also be run.

## 20. Third-Party Audit Judgment

Current docs-only readiness gate:

- Third-party audit is not required.

Future injected fake client abstraction only:

- Third-party audit may be deferred if there is no real network access, no provider fallback, no PDF download, no parser, and no shared schema or validator change.

Future real network client:

- Gemini / DeepSeek / Kimi third-party audit is required before acceptance.

Audit is also recommended if future work implements or changes:

- redirect handling
- domain allowlist enforcement
- source promotion from live response
- network error model
- `schemas.py`
- `validators.py`
- shared safety scan
- registry / locator boundary

## 21. Acceptance Criteria

Readiness gate acceptance:

- Only a docs readiness gate file is added.
- No production code is modified.
- No tests are modified.
- No network is used.
- No token, `.env`, or `tushare_token.txt` is read.
- No unrelated mojibake file is handled.
- Network abstraction policy is clear.
- Injected fake client vs real client policy is clear.
- Domain allowlist policy is clear.
- Redirect policy is clear.
- Content-type policy is clear.
- No-download / no-parser policy is clear.
- Fail-closed error model is clear.
- Future files and tests are clear.
- Audit triggers are clear.
- Implementation entry can be approved or rejected from this document.

Future implementation acceptance:

- Only expected files are changed.
- No PDF download occurs.
- No PDF parser is introduced.
- No provider fallback is introduced.
- No output, fixture, or manifest write occurs.
- Metadata-only client behavior fails closed.
- Real network is disabled by default unless explicitly approved.
- Adapter, request, discovery, and request dry-run regressions pass.
- Safety tests pass.
- No blocker remains open.

## Recommendation

Future implementation is recommended only as a separate metadata-only injected fake client abstraction slice. Direct real network implementation is not recommended as the immediate next slice. Real network work should wait until the injected boundary, safety tests, and adapter handoff contract are accepted, and should then go through separate approval plus third-party audit.
