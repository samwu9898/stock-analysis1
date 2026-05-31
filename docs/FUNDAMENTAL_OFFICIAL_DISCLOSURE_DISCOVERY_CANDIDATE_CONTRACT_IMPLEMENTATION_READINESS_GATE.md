# Official Disclosure Discovery Candidate Contract Implementation Readiness Gate

## 1. Phase Name and Current Baseline

Phase name: Official Disclosure Discovery Candidate Contract Implementation Readiness Gate.

This gate prepares the next possible phase, Official Disclosure Discovery Candidate Contract Minimal Implementation. It is a planning/readiness gate only. It does not implement production code, tests, provider adapters, live discovery, PDF parsing, metric extraction, output baselines, fixtures, accepted manifests, or report generation.

Current baseline commits:

- `c687792402973d6dcf7621326d2371169fefee3a` / `c687792` - `feat: add official verification data gate`
- `5695135aa1c72bbe2391c8545746a540014bc3b7` / `5695135` - `docs: accept official verification data gate`
- `ad95e14ae6b629ba6ef03b91c23110849922a22d` / `ad95e14` - `docs: add official disclosure source registry locator plan`
- `0699944c5ab7218614e973158c4a87c77ac48fef` / `0699944` - `feat: add official disclosure registry locator gate`
- `3d81527d22c9b740fc68e1fcc32ff6b5f0662ac6` / `3d81527` - `docs: add official disclosure registry locator acceptance summary`
- `52f23223511650658e76805e67696da53255e9b1` / `52f2322` - `docs: add official disclosure pipeline next-slice reassessment plan`

The previous reassessment recommended splitting Discovery Candidate Contract from Synthetic Pipeline Dry-Run. This gate covers only the Discovery Candidate Contract readiness decision. Synthetic dry-run behavior remains out of scope until this contract is separately approved and implemented.

## 2. Goal of This Gate

Define the future output contract for official disclosure discovery adapters before any implementation begins. The contract must lock down:

- discovery candidate schema;
- candidate normalization behavior;
- source type mapping;
- registry / locator handoff rules;
- safety and fail-closed rules;
- expected future implementation files;
- expected future tests;
- acceptance criteria for this readiness gate and the future implementation gate.

The output of future CNInfo, SSE, or exchange discovery adapters must remain an explicit candidate object. It must not silently promote itself into an official registry entry, official locator source, verified fact, `official_metric_fact`, provider conflict, accepted manifest entry, fixture, output baseline, or report artifact.

## 3. Proposed Schema

Schema version: `official_disclosure_discovery_candidate.v1`.

The candidate is a normalized metadata envelope. It contains source identity and discovery metadata only. It does not verify file existence, download documents, parse PDFs, extract tables, derive metrics, or produce investment advice.

### Required Fields

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | Must equal `official_disclosure_discovery_candidate.v1`. |
| `discovery_candidate_id` | string | Stable deterministic ID derived from explicit metadata only, such as stock code, period, announcement type, source type, normalized URL, title, and disclosure date. It must not depend on file content or live IO. |
| `stock_code` | string | Required normalized security code. Missing or blank value blocks the candidate. |
| `company_name` | string | Required normalized company name. Missing or blank value blocks the candidate. |
| `exchange` | string | Required exchange or market identifier when known from explicit metadata. Missing value is blocked for exchange-specific official sources. |
| `period_key` | string | Required reporting period key, for example `2024A`, `2024Q3`, or another project-approved period representation. |
| `period_end_date` | string | Required ISO date (`YYYY-MM-DD`) when the period has a known end date. |
| `announcement_type` | string | Required normalized type, such as annual report, semiannual report, quarterly report, correction, or exchange announcement. |
| `source_type` | string | Required source classification from the policy in Section 4. |
| `source_url` | string | Required for official source candidates. Must be metadata only; it must not be fetched in this layer. |
| `source_title` | string | Required for official source candidates. |
| `disclosure_date` | string | Required ISO date (`YYYY-MM-DD`) for official source candidates. |
| `discovered_at_utc` | string | Required ISO 8601 UTC timestamp supplied by the caller or adapter. |
| `discovery_method` | string | Required method label, such as `cninfo_search_result`, `sse_announcement_list`, `exchange_announcement_list`, or `manual_metadata_input`. |
| `source_domain` | string | Required normalized host/domain for URL-bearing candidates. |
| `not_for_trading_advice` | boolean | Required and must be `true`. Any `false`, missing, null, or non-boolean value is rejected. |

### Optional Fields

| Field | Type | Rule |
| --- | --- | --- |
| `raw_candidate_metadata` | object | Optional caller-supplied metadata snapshot. It must remain inert and must not trigger IO, provider calls, parsing, cache acquisition, report generation, or fact generation. |
| `normalized_candidate_metadata` | object | Optional normalized metadata derived only from explicit input fields. It must not contain hidden source promotion, filesystem authority, provider authority, parsed metrics, or report-ready facts. |
| `caveats` | array of strings | Optional warnings that preserve ambiguity without promotion. |

### Conditional Fields

| Field | Condition | Rule |
| --- | --- | --- |
| `rejection_reason` | Required when candidate is rejected or discovery-only. | Must explain why the candidate cannot enter the official lane. |
| `source_url` | Required for official source candidates. | Missing URL blocks official source normalization. Discovery-only or rejected objects may omit it only when `rejection_reason` is present. |
| `source_title` | Required for official source candidates. | Missing title blocks official source normalization. |
| `disclosure_date` | Required for official source candidates. | Missing disclosure date blocks official source normalization. |
| `source_domain` | Required when `source_url` is present. | Must be derived from the provided URL string only; no DNS lookup or request is allowed. |
| `exchange` | Required for exchange announcement candidates. | Missing exchange blocks exchange official source normalization. |

## 4. Source Type Policy

Only the following `source_type` values may normalize into an official discovery candidate:

- `cninfo_official_pdf`: a CNInfo official disclosure PDF candidate represented by explicit metadata only.
- `sse_exchange_announcement`: an SSE official exchange announcement candidate represented by explicit metadata only.
- `exchange_official_pdf`: another recognized exchange official PDF candidate represented by explicit metadata only.

The following values are discovery-only or rejected and must not enter the official lane:

- `mirror_source_candidate`: discovery-only or rejected. A mirror may be useful as a lead, but it cannot become official evidence.
- `provider_source_candidate`: rejected from official lane. Provider endpoints, provider records, AkShare/Tushare-derived records, and other provider data cannot become official disclosure candidates.
- `unknown_source_candidate`: rejected until a future approved source type policy classifies it.

`local_official_cache` must not automatically enter a cache lane in the discovery candidate layer. Local cache intent, local paths, and cached filenames are inert metadata only at this layer. Cache lane control remains the responsibility of the official disclosure source registry layer, where cache policy can be validated explicitly.

## 5. Normalization Rules

Normalization is pure metadata normalization. It must perform no IO and no source refresh.

Allowed normalization behavior:

- trim and normalize explicit string fields;
- canonicalize known enum values;
- normalize dates from explicit input into ISO date strings when unambiguous;
- derive `source_domain` from an explicit URL string without network access;
- compute `discovery_candidate_id` from explicit metadata only;
- copy allowed raw fields into `raw_candidate_metadata`;
- populate `normalized_candidate_metadata` with explicitly derived metadata only;
- set `rejection_reason` and `caveats` when the candidate is blocked or discovery-only.

Forbidden normalization behavior:

- no URL access;
- no HTTP request, fetch, browser navigation, or network call;
- no download;
- no local source file read;
- no token read;
- no `.env` read;
- no `tushare_token.txt` read;
- no local file existence verification;
- no real file `sha256` calculation;
- no PDF parsing;
- no PDF table extraction;
- no source refresh;
- no provider adapter call;
- no AkShare, Tushare, CNInfo live, SSE live, or exchange live integration;
- no metric extraction;
- no `official_metric_fact` generation;
- no `provider_official_conflict` generation;
- no accepted manifest write;
- no output baseline write;
- no fixture write;
- no Report V1 generation;
- no investment advice, target price, position, portfolio, or technical signal output.

The normalized candidate may only become explicit input for registry/locator validation. It must not auto-promote into any verified or official downstream object.

## 6. Registry / Locator Handoff Rules

A discovery candidate may become a registry entry candidate only through an explicit validator-controlled handoff. The handoff must:

- preserve source identity, source URL, source title, source domain, period, period end date, announcement type, disclosure date, and discovery method;
- reject mirror, provider, and unknown source candidates from the official lane;
- block missing required metadata;
- block forbidden markers anywhere in nested metadata;
- block local path authority and treat any local path as inert metadata only;
- require `not_for_trading_advice=true`;
- prevent silent source promotion;
- prevent verified fact generation;
- prevent `official_metric_fact` generation;
- prevent accepted manifest or output baseline writes;
- return an explicit blocked/discovery-only status when the candidate cannot be handed off.

The locator may receive only explicit, validated candidate metadata. It must not infer that a discovery candidate proves file existence, PDF validity, content authenticity, table availability, metric availability, or investment relevance.

## 7. Fail-Closed Rules

The future validator/normalizer must fail closed in these cases:

- missing `stock_code` blocks the candidate;
- missing `company_name` blocks the candidate;
- missing `period_key` or `period_end_date` blocks official normalization;
- missing `announcement_type` blocks official normalization;
- missing `source_url`, `source_title`, or `disclosure_date` blocks official source normalization;
- missing `source_domain` when `source_url` exists blocks official handoff;
- unknown `source_type` blocks official normalization;
- `provider_source_candidate` cannot become official;
- provider endpoints cannot become official;
- `mirror_source_candidate` cannot become official;
- local file path is inert metadata only and cannot prove official status;
- local cache intent cannot enter cache lane from the discovery layer;
- normalized candidates cannot silently become verified facts;
- normalized candidates cannot generate `official_metric_fact`;
- normalized candidates cannot generate `provider_official_conflict`;
- `not_for_trading_advice=true` is required;
- `not_for_trading_advice=false` is rejected;
- missing, null, string, numeric, or otherwise non-boolean `not_for_trading_advice` is rejected;
- forbidden safety markers in top-level or nested metadata are rejected.

## 8. Safety Markers

The future implementation must reject or block the following English markers, whether they appear in top-level fields or nested metadata:

- `token`
- `.env`
- `tushare_token.txt`
- `provider live`
- `AkShare live`
- `Tushare live`
- `network`
- `HTTP`
- `fetch`
- `download`
- `CNInfo live`
- `SSE live`
- `PDF parser`
- `table extractor`
- `parse PDF`
- `metric extraction`
- `official_metric_fact`
- `provider_official_conflict`
- `Report V1`
- `accepted manifest write`
- `output baseline write`
- `fixture write`
- `buy`
- `sell`
- `hold`
- `target price`
- `portfolio`
- `position`
- `technical signal`
- `trading advice`
- `investment advice`

The future implementation must also reject or block equivalent Chinese markers, including but not limited to:

- `买入`
- `卖出`
- `持有`
- `目标价`
- `仓位`
- `组合`
- `技术信号`
- `投资建议`
- `下载`
- `网络`
- `联网`
- `解析PDF`
- `PDF解析`
- `表格抽取`
- `指标抽取`
- `正式研报`
- `输出基线`
- `写入fixture`
- `写入accepted manifest`

Marker checks must inspect nested strings, arrays, and metadata objects. If a marker appears in inert metadata for audit purposes, the implementation must either reject the candidate or require an explicitly approved exception. This readiness gate does not approve any exceptions.

## 9. Future Implementation Expected Files

If this readiness gate passes, the future minimal implementation may consider only these production files:

- `src/fundamental_skill/data_verification/schemas.py`
- `src/fundamental_skill/data_verification/validators.py`
- `src/fundamental_skill/data_verification/official_disclosure_discovery_candidate.py`
- `src/fundamental_skill/data_verification/__init__.py` only if a public API export is required

Expected tests:

- `tests/test_official_disclosure_discovery_candidate.py`
- `tests/test_official_disclosure_discovery_candidate_safety.py`

Optional / requires approval:

- Additional production helper files under `src/fundamental_skill/data_verification/` only if the implementation would otherwise create unclear duplication in the approved files. Any such file requires explicit implementation approval before editing.
- Additional regression tests only if the implementation changes shared schema/validator behavior. Such tests must remain narrow and must not add fixtures, output baselines, provider adapters, live integration, PDF parsing, or report generation.

## 10. Future Implementation Forbidden Files and Scope

The future implementation must not modify or create:

- Report V1 generator;
- provider adapter;
- accepted manifest;
- output baseline;
- fixtures;
- examples;
- `.local_experiments`;
- `tushare_token.txt`;
- `.env`;
- unrelated mojibake files;
- source download/cache acquisition code;
- PDF parser;
- PDF table extractor;
- metric extraction code;
- Research Pack implementation;
- Evidence Panel implementation.

The future implementation must not connect to live AkShare, Tushare, CNInfo, SSE, exchange, provider, HTTP, browser, or download flows.

## 11. Future Tests

The future minimal implementation should cover at least:

- valid CNInfo discovery candidate normalization;
- valid SSE / exchange discovery candidate normalization;
- mirror candidate remains discovery-only and cannot become official;
- provider candidate is rejected from official lane;
- unknown source is blocked;
- missing `stock_code` is blocked;
- missing `company_name` is blocked;
- missing `period_key` or `period_end_date` is blocked;
- missing `announcement_type` is blocked;
- missing `source_title` is blocked;
- missing `disclosure_date` is blocked;
- missing official URL is blocked;
- missing `source_domain` is blocked when URL exists;
- local cache intent is rejected or inert;
- network/download/parser/provider/token/Report V1/output/fixture markers are rejected;
- `not_for_trading_advice` is required;
- `not_for_trading_advice=false` is rejected;
- nested forbidden markers are rejected;
- normalized candidates can only be handed off explicitly to registry/locator;
- no IO, no network, and no file read occur during normalization or validation.

## 12. Regression Subset

After the future implementation, run at least:

- `tests/test_official_disclosure_discovery_candidate.py`
- `tests/test_official_disclosure_discovery_candidate_safety.py`
- `tests/test_official_disclosure_source_registry.py`
- `tests/test_official_disclosure_locator.py`
- `tests/test_official_disclosure_registry_locator_safety.py`
- `tests/test_official_verification_safety.py`

If `schemas.py` or `validators.py` changes shared official verification behavior, also run the relevant official verification schema/validator subset before acceptance.

## 13. Acceptance Criteria

Readiness gate acceptance:

- only this docs readiness gate file is added;
- no production code is changed;
- no tests are changed;
- no output, fixtures, or accepted manifest are changed;
- no token, `.env`, or `tushare_token.txt` is read;
- no `.local_experiments` or unrelated mojibake files are handled;
- schema fields are clear;
- required, optional, and conditional rules are clear;
- source type mapping is clear;
- normalization no-IO policy is clear;
- registry/locator handoff rules are clear;
- fail-closed behavior is clear;
- safety markers are clear;
- future expected files and tests are clear;
- future forbidden scope is clear;
- implementation entry can be approved or rejected from this document.

Future implementation acceptance:

- only expected production and test files are changed;
- no live download, network, PDF parser, provider adapter, Report V1, output baseline, fixture, token, `.env`, or `tushare_token.txt` behavior is introduced;
- validator and normalizer fail closed;
- safety tests pass;
- registry/locator regression tests pass;
- official verification safety regression passes;
- no blocker remains open.

## 14. Blocker Checklist Before Implementation

Implementation must not begin until every item is accepted:

- schema version fixed as `official_disclosure_discovery_candidate.v1`;
- required fields fixed;
- optional and conditional fields fixed;
- source type mapping fixed;
- no-IO policy accepted;
- no-network policy accepted;
- no-download policy accepted;
- no-parser policy accepted;
- no-provider policy accepted;
- safety markers accepted in English and Chinese;
- nested marker rejection accepted;
- registry/locator handoff boundary accepted;
- no silent promotion accepted;
- no verified fact or `official_metric_fact` generation accepted;
- expected production files accepted;
- expected test files accepted;
- future forbidden files accepted;
- rollback scope limited to the approved implementation files;
- no dependency on token, `.env`, `.local_experiments`, fixtures, output, accepted manifest, provider adapter, live source, or local cache acquisition.

## Readiness Recommendation

Recommendation: proceed to readiness gate acceptance review.

Rationale: the proposed contract narrows discovery output to explicit metadata candidates, keeps official source promotion behind validator-controlled registry/locator handoff, and blocks live IO, provider data, PDF parsing, fact generation, report generation, and investment advice. If accepted, the next implementation slice can be constrained to the expected files and tests listed above.
