# Data Provider Phase 4 Real-Token Smoke Implementation Design v1.1

Date: 2026-05-26

Status: v1.1 design accepted; local-only SDK real-token smoke gate safety skeleton implemented and accepted.

This document records the minimal safe implementation design and accepted
safety skeleton for a future local-only Tushare real-token smoke after Phase 4
dual-source comparison dry-run tooling was accepted and the local real-token
smoke gate was documented.

This documentation sync patch does not change code, tests, config, pipeline, classifier,
connector, scoring / readiness, HTML / Dashboard, runtime output, or regression
expected files. It does not request credentials, read `TUSHARE_TOKEN`, read
local MCP config, call MCP, call real Tushare, use the network, run a smoke, or
generate `output/provider_comparison`.

Claude external audit conclusion for the prior design: `B`. After this v1.1
revision, the local-only SDK real-token smoke gate safety skeleton was
implemented and accepted. This still does not authorize real smoke execution or
any primary-provider switch.

Latest recorded verification after safety skeleton acceptance:

- targeted tests: `42 passed, 1 skipped`
- pytest: `589 passed, 1 skipped`
- regression: `passed=47 failed=0 total=47`

## 0. Implementation Acceptance Record

Accepted implementation inventory:

- `src/fundamental_skill/data_providers/real_token_smoke_gate.py`
- `src/fundamental_skill/data_providers/tushare_sdk_transport.py`
- CLI interlock in `compare_providers.py`
- strengthened `token_leak_scanner.py`
- `strategy_type_drift` in `diff_classifier.py`

Accepted safety skeleton capabilities:

- precheck, runtime, postcheck, and cleanup helper for the real-token smoke
  path only
- repo tracked-file, staged-diff, docs / tests / source, and target-output scan
- `output/reports` path set plus SHA-256 baseline
- default output path set plus SHA-256 baseline for `output/raw_*`,
  `output/fundamental_*`, and `output/evidence_pack_*`
- payload and diff-report token scan before write
- cleanup limited to the strict timestamp comparison directory
- SDK transport skeleton with fake SDK / factory injection
- no-token fail closed before any SDK call
- `--provider-transport` / `--real-token-smoke` interlock
- `http` and `mcp-local` reserved fail closed
- `--token` rejected

Accepted safety boundary:

- No real smoke executed.
- No real token read.
- No network.
- No MCP.
- No `output/provider_comparison` generated.
- No default output change.
- No `output/reports` change.
- No primary switch.
- No automatic merge.
- No automatic drift acceptance.

## 1. Current Executability Review

Current code still has not executed a real-token smoke and execution remains
blocked pending a separate execution acceptance review.

- `--real-token-smoke` now requires explicit `--provider-transport sdk`.
- `--provider-transport` without `--real-token-smoke` fails closed.
- `--real-token-smoke` without `--provider-transport` fails closed.
- `--provider-transport http` and `--provider-transport mcp-local` fail closed
  as reserved.
- `--token` is rejected.
- There is an SDK transport skeleton with injected SDK / factory support.
- There is no real Tushare HTTP transport.
- There is no real Tushare MCP transport.
- The token read helper is reachable only after explicit real-smoke/sdk
  interlock; dry-run, tests, and CI do not read real environment variables.
- Missing token fails closed before any SDK call.
- Precheck / runtime / postcheck / cleanup orchestration exists.
- Current code should not execute a real Tushare smoke until a separate Claude
  review or strict human audit approves the execution gate.

The accepted Phase 4 runner remains dry-run / comparison-only by default.
`TushareClient` and `TushareProvider` remain mockable abstractions with injected
transports only. Real-token smoke requires a separate implementation and
acceptance cycle.

## 2. Minimal Implementation Target

The accepted safety skeleton is limited to a future local-only real-token smoke.

Required enablement gates:

- Only an explicit `--real-token-smoke` may enable the path.
- A real provider transport must be explicitly selected, for example
  `--provider-transport sdk`.
- `--output-dir output/provider_comparison` must be explicit.
- The sample list must be explicit.
- Writes are allowed only under
  `output/provider_comparison/<timestamp>/<code>/`.

Required non-goals:

- Do not run Research Intelligence P1.1 by default.
- Do not run HTML or Dashboard.
- Do not modify default output.
- Do not modify the current `evidence_pack`.
- Do not switch provider primary behavior.
- Do not automatically merge AkShare and Tushare data.
- Do not automatically accept drift.
- Do not change classifier, connector, scoring, readiness, or regression
  expected files.

The smoke should produce provider-separated comparison artifacts only. It must
not become a production data refresh, a primary-provider migration, or a
deterministic pipeline behavior change.

## 3. Transport Selection

Three transport options are available for future implementation.

### Python Tushare SDK Transport

Recommended first implementation.

- It is the smallest realistic implementation path.
- It can be wrapped behind the existing `TushareClient` transport boundary.
- It is straightforward to fake in unit tests by monkeypatching or injecting a
  mock SDK object.
- It keeps source-specific API details out of classifier, scoring, readiness,
  P1.1, HTML, Dashboard, and default production paths.

The accepted safety skeleton exposes only the SDK transport skeleton.

### HTTP Transport

Recommended as a fallback.

- It can be useful if the SDK is unavailable or insufficient.
- It should still be wrapped by `TushareClient`.
- It carries higher leakage risk because URLs, headers, payloads, and HTTP
  errors can contain credential-like text.
- It should not be the first transport unless the SDK path is blocked.

### MCP-Backed Local Transport

Recommended only as a local tool-layer fallback.

- It must not become a deterministic pipeline dependency.
- Business logic must not depend on MCP availability, MCP config shape, local
  connector state, or local connection strings.
- MCP URL text must not enter the repository, logs, source traces, errors, or
  artifacts.

Implementation decision and accepted skeleton:

- First version opens only `sdk`.
- `--provider-transport` may reserve values such as `sdk`, `http`, and
  `mcp-local`, but only `sdk` is executable in the accepted safety skeleton.
- `http` and `mcp-local` fail closed as reserved for future implementation.
- Do not add a `--token` CLI parameter, because command-line tokens can leak
  into shell history, logs, process lists, and review text.

## 4. Token Read Design

Token reading is allowed only inside the explicit real-token smoke path.

Required behavior:

- Read `TUSHARE_TOKEN` only after `--real-token-smoke` is present and a real
  transport is explicitly selected.
- Dry-run, tests, and CI must not read environment variables.
- Missing token must fail closed before any real call.
- Tokens must not enter logs, errors, `source_trace`, output, diff reports, or
  artifacts.
- Every exception message must be sanitized before it is recorded.
- Every payload must be token-scanned before artifact write.
- Every artifact must be token-scanned after write.
- Tests must use fake tokens and monkeypatching only.
- Do not add a real `.env` file.
- If `.env.example` is added later, it may contain only a placeholder value,
  never a real token.

Safe display should remain `<masked>` or an equivalent non-reversible marker.
No implementation should print token prefixes, suffixes, lengths, hash digests,
or other reconstructable hints.

### Exception and Response Sanitization

Exception sanitization must be implemented at the source boundary, before any
exception, response, status, or payload can be passed to logging, storage,
`fetch_status`, `errors`, source traces, artifacts, or diff reports.

Required sanitization rules:

- Sanitization must use pattern-based scanning. Exact matching against the
  current token string is required but insufficient.
- The scanner must cover `token=...`, `Bearer ...`, API error bodies, URL query
  strings, JSON error fields, headers-like text, and arbitrary response text.
- API response fields in every position must be treated as possible carriers of
  token-like text. This includes field names, scalar values, nested JSON /
  dict values, metadata, error bodies, and provider messages.
- Sanitization must happen before logging / storage / status capture. The
  design must not rely on a logging handler as the final cleanup layer.
- Sanitized exceptions may preserve only safe context such as the gate name,
  provider name, code, timestamp, and high-level error class.
- Sanitized exceptions must never preserve token values, token-derived text,
  MCP URLs, local MCP config content, headers, raw request URLs, raw response
  bodies, or secret-like argument strings.

### Token Lifetime

Token handling must avoid retaining extra accessible references beyond the
transport setup needed for the local-only smoke.

Required lifetime rules:

- The token string should not remain as a long-lived `TushareClient` class
  attribute after transport initialization.
- After connection / client initialization, the transport layer should avoid
  exposing token references back to calling code.
- Token values must not enter object `repr`, debug state, source traces,
  exception objects, cached payloads, comparison artifacts, or diff reports.
- If the language runtime cannot guarantee memory clearing, the implementation
  must still guarantee that it does not keep additional accessible token
  references in client objects, provider state, closures, cached data, or test
  diagnostics.

## 5. Precheck / Postcheck Design

The implementation added a dedicated helper:

```text
src/fundamental_skill/data_providers/real_token_smoke_gate.py
```

That helper is called only by the real-token smoke path. Dry-run,
ordinary tests, CI, and default provider comparison should not call it.

### Precheck

Precheck must pass before any real Tushare call.

- Repo tracked files scan.
- Staged diff scan.
- Docs / tests / source scan.
- Target output directory scan.
- `output/reports` baseline snapshot, recording both relative file paths and
  SHA-256 content hashes.
- Default output baseline snapshot for `output/raw_*`,
  `output/fundamental_*`, and `output/evidence_pack_*`, recording both
  relative file paths and SHA-256 content hashes.
- CLI flag validation:
  - `--real-token-smoke` is present.
  - `--provider-transport` is present.
  - `--output-dir output/provider_comparison` is present.
  - The sample list is present and non-empty.

Baseline snapshots must be immutable comparison inputs for postcheck. If any
precheck fails, the smoke must not start.

### Runtime Gate

Runtime guardrails must run before each write and around every captured error.

- Scan every payload before writing.
- Sanitize every error before storing it in status, logs, reports, or artifacts.
- Run the same source-boundary sanitizer for exceptions before values can reach
  logging, storage, `fetch_status`, `errors`, source traces, or artifacts.
- Treat every API response field position as potentially containing token-like
  text, including keys, values, nested metadata, error bodies, and provider
  messages.
- Treat any token-like hit as an immediate blocker.
- Stop execution on blocker.
- Do not write partial artifacts outside the timestamp-scoped directory.

### Postcheck

Postcheck must run after the smoke attempt, whether it succeeds or fails.

- Scan generated artifacts.
- Scan git diff.
- Confirm `output/reports` is unchanged by verifying both the path set and each
  recorded SHA-256 content hash.
- Confirm default output is unchanged by verifying both the path set and each
  recorded SHA-256 content hash for `output/raw_*`, `output/fundamental_*`,
  and `output/evidence_pack_*`.
- Treat any added file, deleted file, modified file, or content-hash change in
  those protected paths as a blocker.
- Confirm comparison artifacts are not staged.
- Confirm comparison artifacts are not tracked.
- On blocker, delete only the timestamp directory and record a sanitized reason.

The sanitized reason may include the failed gate name, timestamp, sample list,
and high-level failure class. It must not include credentials, local MCP URL
text, local MCP config content, or token-like values.

## 6. Artifact Boundary Enforcement

Real-token smoke must enforce a stricter artifact boundary than ordinary
planning.

Required path rules:

- In real-smoke mode, `output_dir.resolve()` must equal the repository-local
  `output/provider_comparison` directory.
- Timestamp must use a strict format such as `YYYYMMDDTHHMMSS`.
- Stock code must be exactly six digits.
- Artifact names must come from an allowlist.
- Every write path must be inside `timestamp_dir` via `relative_to`.
- `relative_to` checks must use `Path.resolve()` for both the artifact path and
  `timestamp_dir` to prevent symlink-based traversal.
- Path traversal must fail closed.
- Artifact name, timestamp, and code validation must all pass before resolving
  a write path. Artifact names must remain allowlisted, timestamps must remain
  strict, and codes must remain six digits.

Forbidden writes:

- `output/raw_*`
- `output/fundamental_*`
- `output/evidence_pack_*`
- `output/reports`

Cleanup rule:

- Deletion is allowed only for `output/provider_comparison/<timestamp>`.
- The resolved deletion target must be verified before deletion.
- Before deleting `output/provider_comparison/<timestamp>`, all of these
  conditions must be true:
  - `target.resolve().parent == output/provider_comparison.resolve()`.
  - `target.resolve().name` matches the strict timestamp format, for example
    `YYYYMMDDTHHMMSS`.
  - `target.is_dir()` is true.
  - `target.resolve() != output/provider_comparison.resolve()`.
- Any failed cleanup condition must fail closed.
- The cleanup path must never touch default output, reports, regression
  fixtures, or regression expected files.
- Cleanup must never delete `output/raw_*`, `output/fundamental_*`,
  `output/evidence_pack_*`, `output/reports`, regression fixtures, or
  regression expected files.

Comparison artifacts are runtime artifacts and must remain ignored / untracked.

## 7. Real-Smoke Sample Set

The local real-token smoke sample set must remain small:

| Code | Purpose |
| --- | --- |
| `600406` | Stable Growth sample for financial completeness, ROE, operating cash flow, receivables, capex, and valuation. |
| `002050` | Advanced Manufacturing sample for business composition, automotive thermal management, refrigeration / air-conditioning, and robotics / new-business boundaries. |
| `002371` | Semiconductor equipment sample for classification inputs, R&D, inventory, capex, financial period handling, and domestic-substitution boundary evidence. |
| `603259` | CXO sample for segment evidence, financial quality, overseas / customer / order proxy boundaries, and business-composition coverage. |
| `000426` | Resource Swing sample for financial and business fields while preserving the rule that commodity context is not replaced by generic Tushare data. |
| `002837` | AI datacenter cooling sample for liquid-cooling / thermal-control evidence, business-composition clarity, financial completeness, and ordinary-HVAC boundaries. |

This sample set is only a smoke and review set. It is not sufficient to justify
a primary-provider switch.

## 8. Tushare Real Response Mapping Risk

Real response mapping must treat source differences as review evidence, not as
automatic wins.

Risks to validate:

- Field units may differ from AkShare or current canonical expectations.
- Financial statement periods may differ by `period`, `end_date`, `ann_date`,
  report type, or disclosure date.
- Null-like values must remain missing, not zero.
- Permission errors must be recorded as sanitized unavailable states.
- Empty dataframes must become failed or partial blocks with missing fields.
- Rate limits must be recorded as sanitized failures or partial results.
- `business_composition` may be unavailable under the active permission set.
- Valuation units may differ, especially market capitalization and dividend
  yield.
- `main_business` may be missing and must not be inferred from industry,
  themes, or concept labels.
- Tushare smoke does not prove news coverage replacement.
- Tushare smoke does not replace `commodity_prices` or the existing commodity
  context boundary.

Provider adapters own unit conversion, period selection, permission handling,
and source traces. Downstream deterministic logic should continue to consume
canonical raw blocks and missing-field semantics.

## 9. Diff Acceptance Rules

Diffs must not be automatically accepted.

- `missing_field_improvement` may be recorded, but it must not trigger a primary
  source switch.
- `missing_field_regression` requires human audit.
- `strategy_type_drift` requires human audit.
- `classification_drift` requires human audit.
- `confidence_drift` requires human audit.
- `score_drift` requires human audit.
- `P1_question_drift` requires human audit.
- `token_or_secret_risk` is a blocker.
- `automatic_acceptance` must remain `false`.
- No primary switch.
- No automatic merge.
- No automatic drift acceptance.

Any drift that changes deterministic interpretation, confidence, score, or
research-question behavior is a review item, not a migration success.

`strategy_type_drift` is one of the highest-priority drift types because it can
change the applicability of the entire analysis framework. Even if the new
strategy type looks more reasonable, it must not be automatically accepted.
`strategy_type_drift` must not trigger a primary-provider switch and must not
automatically update classifier, scoring, readiness, or P1.1 behavior.

Diff reports must be scanned before write using the same standard as payload
scanning.

Required diff report scanning rules:

- Field names, field values, drift descriptions, notes, and Tushare-sourced
  metadata must all pass the token scanner.
- Scanning must cover `diff_report.json` and `diff_report.md` before they are
  written, not just provider payloads before diff generation.
- Any token-like value in `akshare_value`, `tushare_value`, `note`, metadata,
  field names, or drift descriptions is an immediate blocker.
- Diff report scan findings may record only location and `<masked>`, never the
  matched text.

## 10. CLI Design

Future command draft only. This documentation sync patch does not execute it.

```bash
python -m src.fundamental_skill.data_providers.compare_providers \
  --codes 600406,002050,002371,603259,000426,002837 \
  --providers akshare,tushare \
  --output-dir output/provider_comparison \
  --real-token-smoke \
  --provider-transport sdk
```

Suggested `--provider-transport` values:

- `sdk`
- `http`
- `mcp-local`

The accepted safety skeleton makes only `sdk` executable. Unsupported transport
values fail closed. Missing transport under `--real-token-smoke` fails closed.

CLI interlock rules:

- `--provider-transport` is valid only when `--real-token-smoke` is present.
- Passing `--provider-transport` without `--real-token-smoke` must fail closed.
- The error message must be safe and must not echo secret-like arguments,
  environment values, local MCP URLs, or raw command text.
- `--provider-transport http` must explicitly fail closed in the first
  implementation with a safe "reserved for future implementation" message.
- `--provider-transport mcp-local` must explicitly fail closed in the first
  implementation with a safe "reserved for future implementation" message.
- First implementation should allow only `sdk`.

## 11. Test Design

Accepted implementation tests cover:

- No-token fail closed.
- Fake token masked.
- SDK transport mocked.
- HTTP transport reserved fail-closed.
- MCP-local transport reserved fail-closed.
- Precheck fails on token in tracked file.
- Staged diff token hit fails.
- Payload write blocked on token leak.
- Diff report write blocked on token-like field names, values, notes, and
  Tushare metadata.
- Postcheck deletes timestamp directory on blocker.
- Artifact path enforcement.
- Artifact path enforcement rejects symlink traversal by resolving both the
  artifact path and timestamp directory.
- `output/reports` unchanged.
- `output/reports` path set and SHA-256 hashes unchanged.
- Default output path set and SHA-256 hashes unchanged for `output/raw_*`,
  `output/fundamental_*`, and `output/evidence_pack_*`.
- Real-token smoke skipped by default.
- CI does not require a real token.
- Regression unchanged.
- `--real-token-smoke` without transport fails closed.
- `--provider-transport` without `--real-token-smoke` fails closed without
  echoing secret-like arguments.
- `--provider-transport http` and `--provider-transport mcp-local` fail closed
  as reserved for future implementation.
- `--output-dir` outside `output/provider_comparison` fails closed.
- Cleanup refuses to delete the `output/provider_comparison` parent directory.
- Cleanup refuses to delete `output/reports` or any non-timestamp comparison
  directory.
- Cleanup allows deletion only for strict timestamp directories directly under
  `output/provider_comparison`.

Tests did not call real Tushare, read real credentials, read local MCP config,
connect MCP, use network, write production output, or change regression
expected files.

### Token Scanner Test Requirements

Scanner tests must prove both exact-reference and pattern-based detection.

Required scanner behavior:

- Support exact matching of the current token reference when a fake token is
  intentionally injected by the test.
- Detect token-like patterns such as long alphanumeric strings, especially near
  case-insensitive keywords including `token`, `key`, `secret`, `auth`, and
  `credential`.
- Scan JSON / dict keys and values.
- Scan URL query parameters.
- Treat keyword matching as case-insensitive.
- Record only finding location and `<masked>`. Test diagnostics and failure
  messages must not record the matched text.

Fake token tests must use realistic token-like strings, not weak placeholder
values. Use random long alphanumeric strings, for example 32 or more
characters, so tests verify realistic token-like detection. Test failure
messages must not print the fake token value.

## 12. Claude / External Audit

Recommended audit stance:

- Claude conclusion for the prior implementation design was `B`; after this
  v1.1 revision, the safety skeleton entered implementation and was accepted.
- After safety skeleton acceptance, the next phase may be local-only real-token
  smoke execution acceptance review.
- Before local real-token smoke execution, use Claude review or strict human
  audit.
- Before any primary-provider switch, external audit is required.

The primary-provider switch is a separate phase and must not be coupled to the
real-token smoke implementation.

## 13. Current Token Status

The user does not need to provide a token now.

Current rules:

- Do not execute a real smoke now.
- Do not request a token in this stage.
- A later local-only acceptance step may use a token only from local
  `TUSHARE_TOKEN` or local MCP config.
- Tokens must not be pasted into prompts, code, docs, tests, logs, output, or
  commits.
- Tokens must not enter git commit messages.
- Commit messages that describe real-token smoke results may include only a
  sanitized run ID, timestamp, and high-level result.
- Commit messages must not include token values, token-derived text, MCP URLs,
  or local configuration content.
- Real MCP URLs and local MCP config content must not be written into the
  repository.

Current recommendation: freeze the accepted safety skeleton baseline. Do not
execute a real token smoke until a separate Claude review or strict human audit
approves the execution gate. Do not consider any primary-provider switch until
a separate external audit approves that phase. The user still does not need to
provide a token now.
