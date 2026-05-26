# Data Provider Phase 4 Local Real-Token Smoke Gate

Date: 2026-05-26

Status: Gate documentation completed; safety skeleton implemented and accepted.

This document records the local real-token smoke acceptance gate for the data
provider abstraction work after Phase 4 dry-run comparison tooling was accepted.
The safety skeleton has now been implemented and accepted, but this document
does not execute a real token smoke, does not request credentials, does not read
`TUSHARE_TOKEN`, does not read local MCP config, does not call MCP, does not
call real Tushare, does not use the network, and does not generate output
artifacts.

Latest recorded verification after v1.1 false-positive strategy patch:

- targeted tests: `33 passed, 1 skipped`
- pytest: `604 passed, 1 skipped`
- regression: `passed=47 failed=0 total=47`

## 1. Current Executability

Current real-token smoke execution is still not authorized and has not been
performed. The project now has a safety skeleton for a future local-only SDK
smoke, but execution still requires a separate Claude review or strict human
audit gate.

Current state:

- `--real-token-smoke` requires explicit `--provider-transport sdk`.
- `--real-token-smoke` without `--provider-transport` fails closed.
- `--provider-transport` without `--real-token-smoke` fails closed.
- `--provider-transport http` and `--provider-transport mcp-local` fail closed
  as reserved for future implementation.
- `--token` CLI arguments are rejected.
- There is an SDK transport skeleton with injected SDK object / factory support
  for tests and future local-only execution.
- There is no real Tushare HTTP transport.
- There is no real Tushare MCP transport.
- Token read is gated behind explicit `--real-token-smoke --provider-transport
  sdk`; dry-run, tests, and CI do not read real environment variables.
- No-token state fails closed before any SDK call.
- Precheck / runtime / postcheck / cleanup orchestration exists in
  `real_token_smoke_gate.py`.
- The project should not request the user to provide a token at this stage.

## 2. Gate Principles

Real-token smoke may only be a local-only explicit acceptance action.

It must not:

- run in CI or default tests
- run automatically
- read tokens by default
- use network by default
- write production output
- write `output/reports`
- switch provider primary behavior
- automatically merge AkShare and Tushare data
- automatically accept classification, confidence, score, or P1 drift

Any implementation that violates these principles is out of scope for Phase 4
local real-token acceptance.

## 3. Pre-Run Gate

All pre-run gates must pass before any real-token smoke is allowed.

- `git status` is clean.
- `output/provider_comparison` does not exist, or the target timestamp
  directory does not exist.
- There is no uncommitted output.
- The token is present only in local `TUSHARE_TOKEN` or local MCP config.
- The token is not present in prompts, docs, tests, code, logs, output, or
  commits.
- Token leak scanner passes over repo tracked files, staged diff, docs, tests,
  and source.
- Runner invocation explicitly includes `--real-token-smoke`.
- Runner invocation explicitly includes `--provider-transport sdk`.
- Runner invocation explicitly includes `--output-dir output/provider_comparison`.
- Runner invocation explicitly includes the sample list.
- `output/reports` path set and SHA-256 baseline is captured.
- Default output path set and SHA-256 baseline is captured for `output/raw_*`,
  `output/fundamental_*`, and `output/evidence_pack_*`.
- Production output writes are forbidden.
- `output/reports` writes are forbidden.

If any pre-run gate fails, the smoke must not start.

## 4. Run Gate

During the run, writes are allowed only under:

```text
output/provider_comparison/<timestamp>/<code>/
```

Forbidden writes:

- `output/raw_<code>.json`
- `output/fundamental_<code>.json`
- `output/evidence_pack_<code>.json`
- `output/reports`

Runtime safety requirements:

- Logs may show only `<masked>` for secret-like values.
- Errors may show only `<masked>` for secret-like values.
- `source_trace` may show only `<masked>` for secret-like values.
- Every payload must pass token scan before it is written.
- Every diff report, including field names, values, notes, descriptions, and
  metadata, must pass token scan before it is written.
- If raw token text, raw authorization credential text, `mcp?token`, or raw MCP URL text is
  detected, the runner must fail closed immediately.

## 5. Post-Run Gate

After a real-token smoke, all post-run gates must pass.

- Scan comparison artifacts.
- Scan logs.
- Scan git diff.
- Scan `output/provider_comparison/<timestamp>`.
- Confirm no token or MCP URL leaked.
- Confirm `output/reports` is unchanged.
- Confirm `output/reports` path set and SHA-256 hashes are unchanged.
- Confirm default output path set and SHA-256 hashes are unchanged.
- Confirm comparison artifacts are not staged or committed to git.

If any post-run gate fails, delete the timestamp directory and record a
sanitized reason.

## 6. Sample Set

The local smoke sample set must stay minimal:

| Code | Purpose |
| --- | --- |
| `600406` | Stable Growth sample for financial completeness, ROE, OCF, receivables, capex, and valuation. |
| `002050` | Advanced Manufacturing sample for business composition, automotive thermal management, refrigeration / air-conditioning, and new-business / robotics boundaries. |
| `002371` | Semiconductor sample for equipment-chain classification inputs, R&D, inventory, capex, and domestic-substitution boundaries. |
| `603259` | CXO sample for business segments, financial quality, overseas / customer / order proxy boundaries. |
| `000426` | Resource Swing sample preserving the boundary that commodity context comes from `ExternalCommodityPriceConnector`. |
| `002837` | AI Datacenter cooling sample for liquid-cooling / datacenter thermal-control evidence and ordinary HVAC boundaries. |

This sample set is not enough to justify a primary-provider switch.

## 7. Command Draft

Future command draft only:

```bash
python -m src.fundamental_skill.data_providers.compare_providers \
  --codes 600406,002050,002371,603259,000426,002837 \
  --providers akshare,tushare \
  --output-dir output/provider_comparison \
  --real-token-smoke \
  --provider-transport sdk
```

The safety skeleton accepts only this explicit transport shape, but this
document does not authorize running the command. Real execution remains blocked
until a separate Claude review or strict human audit approves the local-only
execution gate.

## 8. Acceptance Rules

Real-token smoke passes only if:

- token does not leak
- artifacts exist only under `provider_comparison`
- default output is unchanged
- `output/reports` is unchanged
- AkShare side can run
- Tushare side canonical raw shape is correct
- `diff_report` is generated
- missing-field improvement / regression is explainable
- classification / confidence / score / P1 drift is not automatically accepted
- there is no primary switch
- there is no automatic merge

Blockers:

- token or MCP URL leak
- write to default output
- write to `output/reports`
- automatic provider primary switch
- automatic merge
- deterministic output modification
- regression expected modification
- automatic acceptance of classification, score, confidence, or P1 drift

Any blocker fails the smoke.

## 9. Token Leak Handling

The scanner must support:

- `dict`
- `list`
- `str`

The scanner must detect:

- exact fake-token references in tests
- keyed secret patterns
- authorization credential patterns
- MCP URL / `mcp?token`
- realistic 32+ character token-like values
- token-like values near case-insensitive `token`, `key`, `secret`, `auth`, or
  `credential` keywords
- dict keys and values
- URL query parameters

Findings must show only location and `<masked>`.

### v1.1 False-Positive Policy

The gate uses path-aware tracked-file scanning without weakening runtime
scanner sensitivity.

- `src/`, staged diff, generated artifacts, target output, payloads, diff
  reports, and logs remain strict fail-closed surfaces. Allowlist entries are
  never applied to those surfaces.
- `docs/` and `README.md` may contain safe placeholders such as
  `<TUSHARE_TOKEN>`, `<YOUR_TOKEN>`, `<YOUR_TUSHARE_TOKEN>`, `<REDACTED>`, and
  `<masked>`, plus scanner pattern names such as `token_like_value`.
- `tests/` may contain obvious invalid fake-token fixtures with `FAKE_`,
  `TEST_`, or `EXAMPLE_` prefixes. These prefixes are allowed only for tracked
  docs/tests policy scans, not for runtime payloads or artifacts.
- Documentation examples may use placeholder forms such as
  `token=<YOUR_TOKEN>`, `Bearer <REDACTED>`, and `mcp?token=<TUSHARE_TOKEN>`.
  They must not use real-style long random values.
- Realistic long token-like static literals in docs/tests still block unless a
  narrow line-hash allowlist entry exists.
- Root README false positives should be rewritten into prose rather than
  allowlisted.

If an allowlist is needed, each entry must use an exact relative `docs/` or
`tests/` path and a SHA-256 hash of the exact line content. Every entry must
include `path`, `line_content_hash`, `reason`, `category`, `owner`,
`review_date`, and `expiry`. The only categories are `doc_example` and
`test_fixture`. Wildcards, missing fields, expired entries, `src/`, `output/`,
artifact, and log paths fail closed.

Scanner enforcement points:

- pre-run
- run-time before writing each payload
- post-run

Any finding is a blocker.

## 10. Cleanup Procedure

On failure, cleanup is limited to the timestamp-scoped comparison directory:

```text
output/provider_comparison/<timestamp>
```

Do not delete:

- `output/raw_*`
- `output/fundamental_*`
- `output/evidence_pack_*`
- `output/reports`
- regression fixtures

Before deletion, record:

- timestamp
- sample list
- failed gate
- sanitized reason

The recorded reason must not include credentials, local MCP URL text, local MCP
config content, or token-like values.

## 11. Claude / External Audit

Audit stance:

- The safety skeleton implementation has been accepted.
- Before executing local real-token smoke, use Claude review or strict human
  audit.
- Before any primary-provider switch, external audit is required.

## 12. Next Recommendation

Current next-step rules:

- Do not request a token now.
- Do not execute a real smoke now.
- Next step should be local-only real-token smoke execution acceptance review,
  not direct execution.
- The user should provide a token only in a later local-only execution
  acceptance step.
- The token may be placed only in local `TUSHARE_TOKEN` or local MCP config.
- The token must not be pasted into prompts, code, docs, tests, logs, output, or
  commits.

This document must not contain real Tushare tokens, real MCP URLs, local MCP
config content, or output artifacts.
