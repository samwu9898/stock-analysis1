# Phase 2B-1 Manifest Locator Schema + Validators Implementation Plan

Date: 2026-05-30

Stage: Phase 2B-1 Read-only Manifest Locator Schema + Validators
implementation planning.

Status: documentation-only planning. This stage does not write production code,
does not write tests, does not generate runtime artifacts, does not read the
real accepted manifest, does not scan `output/`, does not update fixtures, does
not update any manifest, does not commit, and does not push.

Reference baseline:

- Phase 2A Local Artifact Index baseline:
  `9c7e626ada7622cff91a2227be8d9df37520006c`.
- Phase 2A acceptance summary:
  `a800cebd439d8d7bdc0a602c2630bc007ba5727c`.
- Phase 2B Read-only Manifest Locator plan:
  `568ad8bfd69b7ab15824e59eadec33f6fc3c02cc`.

## 1. Phase 2B-1 Goal

Phase 2B-1 is the first small implementation step for the future Read-only
Manifest Locator. It should define only schema constants, enum constants, and
pure validators for manifest locator payloads and manifest entry rows.

Allowed future implementation scope:

- define `manifest_locator_payload.v1`;
- define `manifest_entry_row.v1`;
- define status / enum constants;
- define required field constants;
- define pure validators for locator payloads;
- define pure validators for manifest entry rows;
- define conservative failure-mode state values;
- reuse Phase 2A path safety for `manifest_path` and `artifact_path`.

Phase 2B-1 must not:

- implement a synthetic manifest parser;
- implement a real manifest reader;
- implement manifest entry -> artifact row adapter;
- implement ticker-scoped local index builder;
- read the real accepted manifest;
- parse real `output/`;
- read real report artifacts;
- compute real file SHA-256;
- generate runtime artifacts.

The validator layer can validate dictionaries and path strings only. It must
not open files, list directories, parse JSON from disk, call providers, or
derive facts.

## 2. Expected Files

Future Phase 2B-1 code stage should be limited to:

```text
src/fundamental_skill/research_planning/manifest_locator.py
tests/test_manifest_locator.py
```

Default: do not modify any `__init__.py`.

If a future code stage proposes modifying `__init__.py`, it must state the
specific reason before implementation. Acceptable reasons should be narrow,
such as exposing a stable package-level import that existing project style
requires. Tests can import directly from
`src.fundamental_skill.research_planning.manifest_locator`, so no
`__init__.py` change is expected for Phase 2B-1.

Files that must not change in Phase 2B-1:

- production modules other than the new `manifest_locator.py`;
- existing Phase 1 schema / safety modules;
- existing Phase 2A `local_artifact_index.py`, unless a separate approved
  blocker requires it;
- fixtures;
- `output/`;
- accepted manifest files;
- report artifacts;
- provider, CNInfo, Tushare, MCP, dashboard, batch, or orchestrator modules.

## 3. Schema Plan

Phase 2B-1 should define two schemas:

```text
manifest_locator_payload.v1
manifest_entry_row.v1
```

### 3.1 Locator Payload Schema

Draft locator payload:

```json
{
  "schema_version": "manifest_locator_payload.v1",
  "manifest_path": "output/research_reports/accepted_manifest.json",
  "manifest_exists_status": "not_checked",
  "manifest_schema_status": "not_checked",
  "manifest_entry_count": 0,
  "matched_entries": [],
  "unmatched_reason": "",
  "stock_code": "",
  "company_name": "",
  "report_artifact_refs": [],
  "freshness_status": "unknown",
  "lineage_refs": [],
  "caveats": [],
  "not_for_trading_advice": true
}
```

Required fields:

- `schema_version`
- `manifest_path`
- `manifest_exists_status`
- `manifest_schema_status`
- `manifest_entry_count`
- `matched_entries`
- `unmatched_reason`
- `stock_code`
- `company_name`
- `report_artifact_refs`
- `freshness_status`
- `lineage_refs`
- `caveats`
- `not_for_trading_advice`

Field rules:

- `schema_version` must equal `manifest_locator_payload.v1`.
- `manifest_path` must pass Phase 2A `validate_artifact_path_safety`.
- `manifest_exists_status` must be a valid enum value.
- `manifest_schema_status` must be a valid enum value.
- `manifest_entry_count` must be a non-negative integer.
- `matched_entries` must be a list. The validator may optionally validate each
  child as `manifest_entry_row.v1` when the child is a dict.
- `unmatched_reason` must be empty or a valid enum value.
- `stock_code` must be empty or a six-digit ticker code.
- `company_name` must be a string and must not be treated as identity proof.
- `report_artifact_refs` must be a list of strings or structured refs. Phase
  2B-1 should validate shape only and should not read targets.
- `freshness_status` must be a valid enum value.
- `lineage_refs` must be a list.
- `caveats` must be a list.
- `not_for_trading_advice` must be `true`.

The locator payload represents locator state only. It must not represent a
verified fact, a report claim, a provider merge, an official disclosure fact, a
hypothesis, or a trading recommendation.

### 3.2 Manifest Entry Row Schema

Draft manifest entry row:

```json
{
  "schema_version": "manifest_entry_row.v1",
  "stock_code": "",
  "company_name": "",
  "artifact_path": "",
  "artifact_kind": "unknown",
  "artifact_format": "unknown",
  "accepted_status": "review_required",
  "freshness_status": "unknown",
  "hash_status": "not_checked",
  "source_status": "review_required",
  "caveats": [],
  "not_for_trading_advice": true
}
```

Required fields:

- `schema_version`
- `stock_code`
- `company_name`
- `artifact_path`
- `artifact_kind`
- `artifact_format`
- `accepted_status`
- `freshness_status`
- `hash_status`
- `source_status`
- `caveats`
- `not_for_trading_advice`

Field rules:

- `schema_version` must equal `manifest_entry_row.v1`.
- `stock_code` must be empty or a six-digit ticker code.
- `company_name` must be a string and auxiliary only.
- `artifact_path` must be empty only for missing/unmatched state. Non-empty
  values must pass Phase 2A `validate_artifact_path_safety`.
- `artifact_kind` must be a valid enum value.
- `artifact_format` must be a valid enum value.
- `accepted_status` must be a valid enum value.
- `freshness_status` must be a valid enum value.
- `hash_status` must be a valid enum value.
- `source_status` must be a valid enum value.
- `caveats` must be a list.
- `not_for_trading_advice` must be `true`.

The entry row is a manifest locator row. It is not a Local Artifact Index row
yet. It must not create `local_artifact_index_row.v1` records in Phase 2B-1.

## 4. Enums / Constants Plan

Phase 2B-1 should define explicit constants to make failure modes stable and
testable.

Recommended constants:

```text
MANIFEST_LOCATOR_PAYLOAD_SCHEMA_VERSION = "manifest_locator_payload.v1"
MANIFEST_ENTRY_ROW_SCHEMA_VERSION = "manifest_entry_row.v1"
```

Recommended enum groups:

```text
MANIFEST_EXISTS_STATUSES
MANIFEST_SCHEMA_STATUSES
ACCEPTED_STATUSES
FRESHNESS_STATUSES
HASH_STATUSES
SOURCE_STATUSES
ARTIFACT_KINDS
ARTIFACT_FORMATS
UNMATCHED_REASONS
```

Recommended `manifest_exists_status` values:

```text
exists
missing
unreadable
unknown
not_checked
```

Recommended `manifest_schema_status` values:

```text
valid
invalid_json
schema_mismatch
unreadable
not_checked
review_required
```

Recommended `accepted_status` values:

```text
accepted
missing
stale
superseded
invalidated
conflict_open
review_required
unknown
```

Recommended `freshness_status` values:

```text
current
unknown
stale
superseded
invalidated
not_applicable
```

Recommended `hash_status` values:

```text
match
mismatch
missing
not_checked
not_applicable
review_required
```

Recommended `source_status` values should remain Phase 2A-compatible:

```text
available
missing
partial
candidate_only
review_required
conflict_open
stale
invalidated
unreadable
ignored
```

Recommended `artifact_kind` values:

```text
accepted_manifest
research_report_v1
superseded_report_artifact
lineage_artifact
unknown
```

Recommended `artifact_format` values:

```text
json
markdown
html
manifest
unknown
```

Recommended `unmatched_reason` values:

```text
""
missing
data_collection_required
unrelated_ticker
conflict_open
schema_mismatch
manifest_missing
manifest_unreadable
invalid_json
duplicate_entries
unsafe_path
artifact_missing
hash_mismatch
review_required
```

The empty unmatched reason is allowed only when a locator payload has no
unmatched condition.

## 5. Validator Rules

Phase 2B-1 should expose pure validators such as:

```text
validate_manifest_locator_payload(payload)
validate_manifest_entry_row(row)
```

Phase 2B-1 should not implement builders. Builder helpers, if ever needed,
should require a later explicit approval because this slice is limited to
schema constants, enum constants, required field constants, failure-mode
constants, and validators.

Required validator rules:

- `not_for_trading_advice` must be `true`.
- `stock_code` must be empty or exactly six digits.
- `company_name` must be a string and must not be used to confirm identity by
  itself.
- `manifest_path` must pass Phase 2A
  `local_artifact_index.validate_artifact_path_safety`.
- `artifact_path` must pass Phase 2A
  `local_artifact_index.validate_artifact_path_safety` when non-empty.
- Enum values must be legal.
- `matched_entries` must be a list.
- `report_artifact_refs` must be a list.
- `caveats` must be a list.
- `lineage_refs` must be a list.
- `manifest_entry_count` must be a non-negative integer.
- Validator return values should be defensive copies, not references to the
  caller's mutable dicts.

Required marker safety rules:

- Manifest `current` must not mean verified fact.
- `accepted_status=accepted` must not mean verified fact.
- Reject `verified_fact`.
- Reject `auto_verified`.
- Reject fixture promotion markers.
- Reject accepted manifest write/update markers.
- Reject provider primary switch markers.
- Reject Research Report V1 update markers.
- Reject trading advice markers.

Recommended forbidden marker set:

```text
verified_fact
auto_verified
fixture_promotion
promote_fixture
accepted_manifest_update
accepted_manifest_write
manifest_write
manifest_update
provider_primary_switch
research_report_v1_update
report_update
buy_advice
sell_advice
target_price
price_target
position_size
position_sizing
portfolio_weight
portfolio_allocation
technical_signal
trading_signal
trade_signal
```

The marker scan should inspect all text values and keys in the payload before
any path or hash masking that could hide unsafe downstream intent. Error
messages should not echo sensitive paths, secret-like values, or hashes.

Identity-related validator behavior:

- A valid row with only `company_name` and no `stock_code` can exist only as
  unresolved locator state.
- A name-only row should require `source_status=review_required`,
  `accepted_status=review_required`, or a caveat.
- The validator should not perform fuzzy matching.
- Unknown ticker state should be represented as `unmatched_reason=missing` or
  `data_collection_required`.
- Validators must not fallback to accepted sample tickers such as `600406`,
  `002371`, or `002050`.

## 6. Relationship To Phase 2A

Phase 2B-1 should reuse Phase 2A path safety rather than duplicating or
weakening it.

Required relationship:

- Import and reuse
  `src.fundamental_skill.research_planning.local_artifact_index.validate_artifact_path_safety`.
- Keep path normalization behavior aligned with Phase 2A.
- Preserve Phase 2A exclusions for absolute paths, URI paths, path traversal,
  `.env`, tokens, credentials, MCP config, secret-like paths, and unrelated
  mojibake paths.
- Do not create `local_artifact_index_row.v1` rows in Phase 2B-1.
- Do not call Phase 2A artifact row builders in Phase 2B-1.
- Leave manifest entry -> artifact row adapter to Phase 2B-3.
- Do not classify report artifacts as verified facts.
- Do not read any file contents.

Expected future flow after later phases:

```text
Phase 2B-1 schema + validators
  -> Phase 2B-2 synthetic manifest parser
  -> Phase 2B-3 manifest entry to Local Artifact Index row adapter
```

Phase 2B-1 stops at validated manifest locator dicts. It does not parse disk
manifest files and does not create Local Artifact Index rows.

## 7. Test Planning

Phase 2B-1 future tests should verify only schema constants, enum constants,
and validators. Tests should use pure dictionaries and strings.

Required testing boundaries:

- Do not use the real accepted manifest.
- Do not use real `output/`.
- Do not use `tmp_path` parser behavior; parser tests belong to Phase 2B-2.
- Do not create synthetic manifest files on disk in Phase 2B-1.
- Do not read real report artifacts.
- Do not compute file hashes.
- Do not write fixtures.
- Do not call providers.
- Do not use network.
- Do not read tokens or MCP config.

Required test coverage:

- valid minimal locator payload;
- valid manifest entry row;
- invalid `stock_code`;
- `not_for_trading_advice=false`;
- invalid enum;
- `matched_entries` is not a list;
- `report_artifact_refs` is not a list;
- `caveats` is not a list;
- `lineage_refs` is not a list;
- `manifest_path` unsafe;
- `artifact_path` unsafe;
- `verified_fact` marker rejected;
- `auto_verified` marker rejected;
- accepted manifest write/update marker rejected;
- fixture promotion marker rejected;
- provider primary switch marker rejected;
- Research Report V1 update marker rejected;
- trading advice marker rejected;
- accepted/current does not equal verified fact;
- name-only identity remains `review_required`;
- unknown ticker does not fallback to accepted samples;
- `600406`, `002371`, and `002050` accepted status is not generalized to new
  tickers.

Suggested future targeted command:

```text
pytest tests/test_manifest_locator.py
```

Suggested future regression subset:

```text
pytest tests/test_manifest_locator.py tests/test_local_artifact_index.py tests/test_autonomous_ticker_research_schema.py tests/test_autonomous_ticker_research_safety.py
```

Regression subset can be run after Phase 2B-1 implementation is explicitly
approved and added. This planning stage must not run implementation tests
because they do not exist yet.

## 8. Prohibited Work

Phase 2B-1 must not:

- read the real accepted manifest;
- read real report artifacts;
- scan `output/`;
- compute real file SHA-256;
- write `output/`;
- write any manifest;
- write fixtures;
- promote fixtures;
- generate reports;
- generate runtime artifacts;
- call a model;
- add prompt orchestration;
- call providers;
- call CNInfo;
- call Tushare;
- call AkShare;
- connect MCP;
- read tokens;
- use the network;
- implement a hypothesis generator;
- implement an orchestrator;
- implement Research Report V1 integration;
- implement Dashboard or Batch;
- parse PDF content;
- parse DOCX content;
- parse HTML content;
- parse Excel content;
- parse report JSON/Markdown/HTML content for claims;
- process unrelated mojibake untracked files.

Phase 2B-1 is deliberately a pure schema/validator slice. Any IO, parser,
reader, adapter, locator runtime behavior, dashboard, batch, provider, or
report integration belongs to a later explicit phase.

## 9. Acceptance Checklist

Documentation planning acceptance:

- [ ] Only this Phase 2B-1 implementation planning document is added.
- [ ] No production code is written.
- [ ] No tests are written.
- [ ] No runtime artifact is generated.
- [ ] No real accepted manifest is read.
- [ ] No real `output/` scan is performed.
- [ ] No report artifact content is read.
- [ ] No file SHA-256 is computed.
- [ ] No manifest is written or updated.
- [ ] No fixture is written or promoted.
- [ ] No provider, CNInfo, Tushare, AkShare, MCP, token, network, model, or
  prompt orchestration work is performed.
- [ ] No hypothesis generator, orchestrator, Research Report V1 integration,
  Dashboard, or Batch work is performed.
- [ ] Unrelated mojibake untracked files are not processed.
- [ ] `git status --short` is reviewed before handoff.
- [ ] `git log --oneline -5` is reviewed before handoff.
- [ ] No commit is created.
- [ ] No push is performed.

Future Phase 2B-1 implementation acceptance, only after explicit approval:

- [ ] Modify only `src/fundamental_skill/research_planning/manifest_locator.py`
  and `tests/test_manifest_locator.py`, unless a separately justified
  `__init__.py` change is accepted.
- [ ] Define `manifest_locator_payload.v1`.
- [ ] Define `manifest_entry_row.v1`.
- [ ] Define complete enum constants.
- [ ] Validate all required locator payload fields.
- [ ] Validate all required manifest entry row fields.
- [ ] Reuse Phase 2A `validate_artifact_path_safety`.
- [ ] Enforce `not_for_trading_advice=true`.
- [ ] Reject unsafe path, forbidden marker, and downstream promotion payloads.
- [ ] Do not read files or directories.
- [ ] Do not read the real accepted manifest.
- [ ] Do not create Local Artifact Index rows.
- [ ] Do not promote verified facts.
- [ ] Targeted `tests/test_manifest_locator.py` passes.
- [ ] Existing `tests/test_local_artifact_index.py` passes.
- [ ] Phase 1 schema and safety regression subset passes.
- [ ] `git status --short` contains only expected implementation files plus
  pre-existing unrelated mojibake untracked files.
