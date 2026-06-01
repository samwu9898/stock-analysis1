# Official Source Discovery Adapter / Live Metadata Discovery Readiness Gate

## 1. Stage Name And Current Baseline

Stage name: **Official Source Discovery Adapter / Live Metadata Discovery Readiness Gate**.

Current key baseline commits:

- `625f1ac docs: accept request synthetic dry-run integration`
- `caef73b feat: add request synthetic dry-run integration`
- `f0f5b6c docs: add request synthetic dry-run integration plan`
- `0a64ea2 docs: accept official disclosure request contract`
- `cc86447 feat: add official disclosure request contract`

This stage is a docs-only readiness gate. It defines the future boundary for a metadata-only official source discovery adapter. It does not implement the adapter, does not add tests, does not perform live discovery, and does not change production behavior.

## 2. Current Capability Map

The current disclosure verification chain already has these capabilities available as planning or implemented baseline components:

- `security_identity.v1`
- `official_disclosure_discovery_request.v1`
- Request-driven synthetic dry-run integration
- `official_disclosure_discovery_candidate.v1`
- Registry / locator boundary
- Synthetic dry-run path
- Official verification data gate
- Recursive safety scan
- No-IO synthetic pipeline

Together these establish an in-memory, request-scoped path from security identity to discovery request, synthetic discovery candidate generation, registry / locator handling, and readiness result production without requiring live official source discovery.

## 3. Current Gap Map

The following capabilities are not yet available and must not be assumed present:

- Metadata-only official source discovery adapter
- CNInfo official metadata discovery
- SSE / Exchange official metadata discovery
- Official domain allowlist
- Redirect policy
- Content-type policy
- Rate limit / retry / timeout policy
- Source freshness policy
- Discovery error model
- Discovery result to discovery candidate handoff
- Live download
- PDF parser
- Metric extraction
- Provider reconciliation
- Evidence Panel / Research Pack integration

These gaps define the boundary for future work. The readiness gate only records the expected future constraints and acceptance criteria.

## 4. Future Adapter Goal

The future metadata-only adapter goal is:

- Input: `official_disclosure_discovery_request.v1`
- Output: a list of `official_disclosure_discovery_candidate.v1` candidates
- Discover only official announcement metadata
- Do not download PDFs
- Do not read PDFs
- Do not parse PDFs
- Do not generate registry entries
- Do not generate verified facts
- Do not generate metrics
- Do not connect to provider adapters
- Do not generate formal research reports

The adapter should be a strict discovery boundary. It may identify candidate official disclosures from allowed official metadata sources, but it must not promote metadata into verified financial facts or investment conclusions.

## 5. Allowed Official Sources Policy

Future discovery may consider only these official source types:

- `cninfo_official_pdf`
- `sse_exchange_announcement`
- `exchange_official_pdf`

The following source types are forbidden:

- `provider_source_candidate`
- `mirror_source_candidate`
- `unknown_source_candidate`
- `local_official_cache`
- Third-party mirrors
- Search engine results
- Scraped unofficial sites

Any result that cannot be classified as an allowed official source type must fail closed.

## 6. Domain / Endpoint Allowlist Policy

Future implementation may plan for an explicit official domain allowlist such as:

- `cninfo.com.cn`
- `static.cninfo.com.cn`
- `sse.com.cn`
- `www.sse.com.cn`
- `szse.cn`
- `www.szse.cn`
- `bse.cn`
- `www.bse.cn`

This readiness gate does not access these domains, does not perform DNS lookup, and does not verify live URLs.

Future redirect policy:

- Redirects must be evaluated before candidate acceptance.
- Redirects are allowed only when every hop remains inside the official allowlist.
- Redirects to non-allowlist domains must be rejected.
- Missing, malformed, or ambiguous redirect targets must be rejected.
- Redirect shortening, tracking, or third-party interstitial URLs must be rejected.

Future domain enforcement policy:

- A non-allowlist source domain must be rejected.
- A URL with an allowlist-looking string outside the host component must be rejected.
- Userinfo, encoded-host, punycode, mixed-case, and trailing-dot variants must be normalized before policy evaluation.
- Domain matching must be host-based, not substring-based.

## 7. Metadata-Only Discovery Policy

The future adapter may collect only metadata needed to construct discovery candidates:

- `source_url`
- `source_title`
- `disclosure_date`
- `stock_code`
- `company_name` / company hint
- `exchange`
- `period_key`
- `period_end_date`
- `announcement_type`
- `source_type`
- `source_domain`
- `discovered_at_utc`
- `discovery_method`

The future adapter must not collect, compute, or write:

- File content
- PDF text
- Table extraction
- Metrics
- SHA-256 of a downloaded file
- Local cache path
- Accepted manifest writes
- Output writes

Metadata discovery must remain a candidate-discovery step, not a document ingestion or evidence extraction step.

## 8. Request-To-Discovery Policy

The `official_disclosure_discovery_request.v1` request is a hard constraint. A discovery result must match the request scope before it can become a discovery candidate.

Required matching constraints:

- `stock_code`
- `exchange`
- `query_period`
- `period_end_date`
- `requested_announcement_type`
- `allowed_source_types`

Required preservation constraints:

- Request caveats must be preserved.
- Request `identity_confidence` must not be raised by discovery results.
- Company hints must not become verified company matches.
- Discovery results must not expand the original request scope.

If a source result is relevant-looking but outside the request scope, the adapter must reject it or mark the discovery as blocked / review-required according to the future error model.

## 9. Fail-Closed Rules

Future implementation must fail closed for:

- Invalid request
- Request blocked
- Unsupported source type
- Non-allowlist domain
- Redirect to non-allowlist domain
- Metadata missing
- Disclosure date missing
- Period mismatch
- Announcement type mismatch
- Stock code mismatch
- Company mismatch when verifiable
- Duplicate candidates
- Multiple candidates requiring review
- No candidates found
- Network error
- Timeout
- Rate limit
- Malformed response
- Forbidden marker
- Provider fallback attempt
- PDF download attempt
- Parser attempt
- Output / fixture / manifest write attempt

Expected outcomes:

- Duplicate candidates should be deduplicated when exact metadata identity is available, otherwise marked `review_required`.
- Multiple plausible candidates should be `review_required`, not silently accepted.
- No candidates found should produce a blocked discovery result, not a fabricated candidate.
- Network, timeout, and rate-limit failures should be modeled as blocked discovery outcomes rather than uncontrolled exceptions.
- Forbidden operational attempts, including provider fallback, PDF download, parser execution, and output writes, must be rejected by safety tests.

## 10. Future Implementation Expected Files

If this readiness gate is accepted, a future implementation may consider changing only these production files:

- `src/fundamental_skill/data_verification/official_source_discovery_adapter.py`
- `src/fundamental_skill/data_verification/__init__.py` only if a public API export is required

Expected tests:

- `tests/test_official_source_discovery_adapter.py`
- `tests/test_official_source_discovery_adapter_safety.py`

If future implementation needs a network client abstraction, it must be listed separately as optional / requires approval. A real live network client must not be implemented by default.

## 11. Future Implementation Forbidden Files

Future implementation must not modify or create:

- Provider adapter
- Report V1 generator
- Accepted manifest
- Output baseline
- Fixtures
- Examples
- `.local_experiments`
- `tushare_token.txt`
- `.env`
- Unrelated mojibake files
- PDF parser
- PDF table extractor
- Metric extraction
- Research Pack implementation
- Evidence Panel implementation
- `official_metric_fact` generation
- `provider_official_conflict` generation

These files and capabilities remain outside the metadata-only official source discovery adapter scope.

## 12. Future Tests

Future implementation should cover at least:

- Valid CNInfo metadata result to discovery candidate
- Valid SSE metadata result to discovery candidate
- Non-allowlist domain rejected
- Provider / mirror / unknown source rejected
- Local cache rejected
- Request mismatch rejected
- Missing metadata blocked
- Duplicate candidates marked `review_required`
- No candidates found blocked
- Network error modeled as blocked and not as an uncontrolled failure
- Timeout modeled as blocked
- Rate limit modeled as blocked
- Forbidden markers rejected
- No PDF download
- No PDF parser
- No metric extraction
- No output / fixture / manifest write
- Request caveats preserved
- Identity confidence not raised
- Company hint not verified

These tests should protect the adapter boundary and prevent metadata discovery from becoming evidence extraction, provider fallback, or report generation.

## 13. Third-Party Audit Recommendation

Current docs-only readiness gate: third-party audit is not required.

Future fake / client-injected metadata adapter with tests: third-party audit may remain optional if the implementation stays no-IO, injected-client only, and limited to the expected files and tests listed above.

Third-party audit is recommended if future work introduces any of the following:

- Real network client
- Domain allowlist enforcement
- Redirect handling
- Source promotion boundary
- Changes to `schemas.py`
- Changes to `validators.py`
- Changes to shared safety scan
- Changes to registry locator boundary

Suggested reviewers for higher-risk future implementation: Gemini / DeepSeek / Kimi.

## 14. Acceptance Criteria

Readiness acceptance requires:

- Only this docs readiness gate file is added
- No production code changes
- No tests added or changed
- No live network access
- No token, `.env`, or `tushare_token.txt` read
- No mojibake handling
- Allowed sources are clear
- Domain policy is clear
- Metadata-only policy is clear
- Fail-closed rules are clear
- Expected files and tests are clear
- Forbidden scope is clear

Future implementation acceptance requires:

- Only expected files changed
- No PDF download
- No PDF parser
- No provider fallback
- No output / fixture / manifest write
- Metadata-only adapter fails closed
- Request / discovery / request-dry-run regressions pass
- Safety tests pass
- No blocker remains open

## Readiness Gate Decision

This readiness gate supports moving to acceptance review for the metadata-only official source discovery adapter plan.

It does not recommend moving directly to a live network implementation. The next implementation, if approved, should begin with a fake or injected-client metadata adapter and safety tests. A real network client should require separate approval and a higher-risk review path.
