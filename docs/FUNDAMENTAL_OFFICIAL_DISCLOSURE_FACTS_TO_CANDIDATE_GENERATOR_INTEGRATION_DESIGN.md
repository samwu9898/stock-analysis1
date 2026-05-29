# Fundamental Official Disclosure Facts To Candidate Generator Integration Design

Stage: Fundamental Skill Official Disclosure Facts To Candidate Generator Integration Design

Status: documentation-only design. No code, tests, fixtures, output artifacts,
accepted manifests, scoring / P1.1 / regression expected files, orchestration,
CLI, candidate generator implementation, or Research Report V1 implementation
are changed by this stage.

## 1. Positioning

`official_disclosure_facts -> candidate generator integration` is the design
for bringing official evidence candidates into the candidate fact chain.

It is not:

- Research Report V1 integration;
- fixture promotion;
- a validator;
- an accepted manifest update;
- a provider-primary switch;
- live CNInfo;
- live Tushare;
- AkShare or other provider access;
- MCP;
- trading advice.

The goal is to:

- convert official text facts and table facts into candidate-generator
  consumable `fact_candidates`;
- preserve `L1_official_disclosure` as the evidence tier;
- preserve source document / section / page-or-anchor / table / row / column
  trace;
- preserve caveats and human-review requirements;
- keep official disclosure candidates out of `verified_fact` until a later
  reviewed promotion design accepts them.

This design starts after the retained table facts ->
`official_disclosure_facts` runtime baseline was frozen. It does not change the
runtime baseline or generate a new candidate report.

## 2. Input Scope

The future candidate-generator integration may read an
`official_disclosure_facts.json` payload that contains:

- `source_documents[]`;
- `extracted_facts[]`;
- `source_tables[]`;
- `table_caveats[]`;
- `table_conversion_warnings[]`;
- `extraction_warnings[]`;
- `data_quality_caveats[]`.

The candidate sources are:

- official text facts already present in `extracted_facts[]`;
- official table facts already present in `extracted_facts[]`, with table trace
  resolved through `source_tables[]`.

Required interpretation:

- text facts and table facts are both candidate sources;
- table facts remain caveated L1 candidates;
- `needs_human_review=true` must pass through to the candidate row;
- caveat `local_structured_sample_requires_human_review` must pass through;
- official disclosure facts do not become verified facts;
- `unreliable_text_copy` and `unusable` table-quality records do not become
  fact candidates.

An official payload should be treated as an input artifact only. It must not be
rewritten by candidate generation.

## 3. Candidate Schema Mapping

Each official disclosure fact candidate should be represented as a candidate
row with at least these fields:

| Candidate field | Mapping / rule |
| --- | --- |
| `candidate_id` | Deterministic id derived from stock code, source document id, fact id or field path, period, and table row / column trace when present. |
| `field_path` | Use the official fact `field_path`; table facts use `business_composition.*`. |
| `value` | Official fact value, preserving numeric type where available. |
| `unit` | Official fact `unit` or `data_unit`; missing unit can block the candidate for quantitative fields. |
| `period` | Official fact `period`, `report_period`, or disclosure-period equivalent. Missing period blocks period-sensitive facts. |
| `source_type` | Always `official_disclosure`. |
| `evidence_tier` | Always `L1_official_disclosure`. |
| `source_document_id` | Must reference an existing `source_documents[]` entry. |
| `source_section` | Preserve source section, such as `main_business` / `主营业务`, when present. |
| `source_page_or_anchor` | Preserve page, paragraph, heading, anchor, or text-span trace when present. |
| `source_table_id` | Preserve for table-derived facts; empty for pure text facts. |
| `source_row_index` | Preserve table row index when present. |
| `source_column_name` | Preserve table source column when present. |
| `source_column_map` | Preserve normalized column mapping for table facts. |
| `classification_type` | Preserve segment classification such as product, industry, region, or segment. |
| `segment_name` | Preserve official segment / product / industry / region name. |
| `denominator` | Preserve denominator for ratios or shares; missing denominator blocks ratio candidates. |
| `table_quality` | Preserve table-quality value such as `structured_medium`; empty for text facts. |
| `extraction_confidence` | Preserve official extraction confidence. |
| `needs_human_review` | Preserve source boolean; default to true when caveats require review. |
| `caveats` | Union of fact caveats, relevant table caveats, conversion warnings, extraction warnings, and data-quality caveats. |
| `review_status` | Derived by the review status rules in section 4. |
| `not_for_trading_advice` | Always `true`. |

Suggested V1 candidate row shape:

```json
{
  "candidate_id": "official_disclosure:600406:600406_2025_semiannual_report_real:business_composition.revenue:2025H1:table_001:3:revenue",
  "field_path": "business_composition.revenue",
  "value": 12224749159.44,
  "unit": "CNY",
  "period": "2025H1",
  "source_type": "official_disclosure",
  "evidence_tier": "L1_official_disclosure",
  "source_document_id": "600406_2025_semiannual_report_real",
  "source_section": "business_composition",
  "source_page_or_anchor": "",
  "source_table_id": "table_001",
  "source_row_index": 3,
  "source_column_name": "revenue",
  "source_column_map": {},
  "classification_type": "product",
  "segment_name": "",
  "denominator": "total_revenue",
  "table_quality": "structured_medium",
  "extraction_confidence": "medium",
  "needs_human_review": true,
  "caveats": ["local_structured_sample_requires_human_review"],
  "review_status": "manual_review_required",
  "not_for_trading_advice": true
}
```

This shape is a candidate row, not a reviewed fact, not a fixture record, and
not a Research Report V1 evidence item.

## 4. Review Status Rules

Recommended official-disclosure candidate `review_status` values:

- `auto_candidate`;
- `manual_review_required`;
- `blocked_by_caveat`;
- `unsupported_or_missing`.

Rules:

- `needs_human_review=true` -> `manual_review_required`;
- missing `unit`, `period`, or `denominator` on quantitative or ratio fields ->
  `blocked_by_caveat`;
- `table_quality=structured_medium` -> usually `manual_review_required`;
- `table_quality=structured_high` may still require manual review until an
  official auto-accept policy is accepted;
- `table_quality=unreliable_text_copy` or `unusable` -> do not emit fact
  candidates; emit caveat candidates or warnings only;
- source lineage mismatch -> no candidate row;
- malformed official payload -> no candidate row;
- conflicting source value -> candidate may be emitted with a conflict status,
  but must remain manual review;
- no row may be marked `verified_fact`.

`auto_candidate` means "ingested as a candidate with official trace", not
"accepted as truth." A later candidate-review or promotion design may decide
whether any official candidate can be accepted.

## 5. Official Text Facts

Official text facts should be ingested as candidate facts when their source
location and confidence are available.

V1 text fact handling:

- `main_business_official_text`: emit an official candidate for the official
  main-business text, preserving source section / anchor and extraction
  confidence.
- periodic report basics: emit candidates for report title, report type, stock
  code, company name, and other parser basics only when they are explicit in
  the official payload.
- disclosure date: emit a candidate with disclosure-date trace and confidence.
- report period: emit a candidate with report-period trace and confidence.
- risk trigger text: emit as caveated text candidates or warnings when trigger
  extraction is conservative and traceable.
- management guidance placeholder: keep as placeholder or unsupported candidate
  until a later guidance-specific parser is accepted.

Boundaries:

- preserve source location;
- preserve extraction confidence;
- preserve caveats;
- do not overwrite provider `main_business`;
- do not directly enter Research Report V1;
- do not promote text facts to `verified_fact`;
- do not use text trigger candidates as trading signals.

If a provider already has `main_business`, the official text candidate sits
beside the provider candidate. It can be considered a stronger source
candidate in later review, but it does not automatically replace provider data.

## 6. Official Table Facts

Business-composition table facts should be ingested only when table quality,
lineage, and row / column trace are sufficient.

V1 scope accepts revenue facts as the design sample:

- `business_composition.revenue`;
- segment / product / industry / region classification;
- official segment name;
- period;
- unit;
- source table id;
- row index;
- source column name;
- normalized column map;
- table quality;
- caveats.

Deferred table fact classes:

- cost facts;
- future gross margin facts;
- future YoY facts.

Rules:

- table facts must preserve row / column trace;
- `source_table_id` must resolve to `source_tables[]`;
- `source_document_id` must resolve to `source_documents[]`;
- source table trace must be auditable from the candidate row;
- denominator missing must block the candidate or be preserved as a blocking
  caveat, depending on field semantics;
- `local_structured_sample_requires_human_review` must be preserved;
- no candidate is emitted if source lineage mismatches;
- no candidate is emitted from `unreliable_text_copy` or `unusable` tables.

For the retained 600406 baseline, the six accepted table facts are revenue
facts only. Cost, gross margin, and YoY handling remain later designs.

## 7. Conflict / Dedupe Policy

Official disclosure candidates coexist with provider candidates.

V1 policy:

- do not automatically overwrite Tushare candidates;
- do not automatically overwrite AkShare candidates;
- do not switch provider primary;
- do not auto-merge provider and official values;
- official `L1_official_disclosure` candidates may be treated as stronger
  source candidates in later review;
- multi-source consistency belongs to a later L2 design;
- conflicts enter manual review;
- period, unit, or denominator mismatch requires manual review;
- same `field_path` + same period + different value -> conflict candidate;
- same value but different source trace remains distinct until a later dedupe
  rule accepts source-level merge.

Suggested conflict metadata, if the existing candidate generator supports it:

- `conflict_status=official_provider_conflict`;
- `conflict_with_candidate_ids=[]`;
- `conflict_reason=period_mismatch | unit_mismatch | denominator_mismatch |
  value_mismatch | classification_mismatch`;
- `review_status=manual_review_required`.

If the current candidate generator does not yet support these fields, retain
the conflict in `caveats` and `manual_review_note` rather than silently
dropping it.

## 8. Output Artifact Design

Three bridge options are possible.

### Option A: Extend Unified `fact_candidates.json`

Description:

- keep one unified candidate report;
- add `source_type=official_disclosure`;
- add `evidence_tier`;
- add official trace fields;
- add an official namespace or subsection if needed.

Pros:

- one candidate-review queue;
- easier conflict comparison with provider candidates;
- consistent downstream audit surface.

Cons:

- expands the main schema;
- existing provider-focused consumers must tolerate official trace fields;
- regression risk is higher because the current artifact is provider-centric.

### Option B: Keep A Parallel Official Candidate Artifact

Description:

- keep the independent official-only candidate payload;
- do not directly append official rows to provider-centric
  `fact_candidates.json`;
- merge or compare later.

Pros:

- clean isolation from provider candidates;
- avoids polluting the current schema;
- preserves official parsing caveats and source trace.

Cons:

- creates a second review surface;
- delays full provider-official conflict handling until orchestration exists.

### Option C: Add A Bridge Index Artifact

Description:

- add `candidate_source_bridge.json`, `candidate_source_index.json`, or
  `candidate_inputs_manifest.json`;
- record provider and official candidate artifact refs, counts, source types,
  review queues, and conflict summaries.

Pros:

- does not break either existing artifact schema;
- can scale to more source types later;
- gives review tooling a single place to discover candidate inputs.

Cons:

- introduces one more intermediate artifact;
- requires future orchestration support.

### V1 Recommendation

Use Option B + Option C for the bridge stage:

- keep `official_disclosure_fact_candidates.v1` independent;
- design a lightweight bridge / source-index artifact;
- do not directly append official rows to provider-centric
  `fact_candidates.json`;
- let later review tooling read provider candidates and official candidates
  together;
- defer a unified candidate pool until candidate schema v2.

This updates the near-term output recommendation after the accepted official
candidate payload runtime baseline. The official rows are still valid candidate
inputs, but the current provider-centric schema should not be mutated by a
direct append in V1.

## 9. Safety / Validation

Future implementation should validate:

- official payload is valid;
- every official candidate references a valid `source_document_id`;
- table candidates reference a valid `source_table_id`;
- table candidates preserve row / column trace;
- candidate rows preserve source section or source anchor where available;
- candidate rows preserve caveats;
- candidate rows preserve `needs_human_review`;
- candidate rows preserve `not_for_trading_advice=true`;
- no token, Bearer string, MCP URL, `.env` reference, local secret path, or
  credential is present in candidate output;
- no trading recommendation keys are present;
- no `verified_fact` marker is present;
- no fixture is written;
- no accepted manifest is updated;
- no Research Report V1 artifact is updated;
- no source lineage mismatch is tolerated.

Fail-closed cases:

- invalid official payload;
- source document id mismatch;
- missing source table for table fact;
- unresolved row / column trace for table fact;
- unsupported table quality;
- missing period / unit / denominator where required;
- candidate id collision that cannot be proven identical.

## 10. Relation To Current Runtime Baseline

Current accepted official disclosure facts baseline:

- base official facts with main-business official text;
- integrated table facts review artifact:
  `output/official_disclosures/20260528T173612Z/600406/official_disclosure_facts_with_tables_review.json`;
- integrated `extracted_facts=7`;
- 6 revenue facts;
- `source_tables=1`;
- `table_caveats=4`;
- `table_conversion_warnings=4`;
- no verified fact;
- no provider-centric candidate generator output.

Current accepted official candidate payload baseline:

- official disclosure candidate adapter implementation accepted;
- runtime review artifact:
  `output/official_disclosures/20260528T182057Z/600406/official_disclosure_candidates_review.json`;
- `version=official_disclosure_fact_candidates.v1`;
- `source_type=official_disclosure`;
- `candidate_rows=7`;
- 1 main business candidate;
- 6 revenue table candidates;
- table segments: `电网智能`, `数能融合`, `能源低碳`, `工业互联`,
  `集成及其他`, and `合计`;
- all rows use `evidence_tier=L1_official_disclosure`;
- main business and all revenue table candidates remain
  `manual_review_required`;
- `source_page_or_anchor` is empty in the current input and preserved as empty;
- trace remains closed through source document + source section + table row /
  column / source_column_map;
- no `verified_fact`, no `review_status=verified`, and no `auto_verified`;
- no provider-centric `fact_candidates.json`;
- no candidate generator main path modification;
- no Research Report V1 integration;
- no fixture promotion;
- no accepted manifest update.

Latest accepted verification results are quoted here, not rerun by this
documentation-only stage:

- targeted tests `496 passed`;
- full pytest latest `1144 passed, 1 skipped`;
- regression `passed=47 failed=0 total=47`.

This documentation-only acceptance summary does not generate a new runtime
artifact and does not change the frozen baseline.

## 11. Safety / Non-Goals

This stage does not:

- read `TUSHARE_TOKEN`;
- use the network;
- call CNInfo;
- call Tushare;
- call AkShare;
- call any provider;
- connect MCP;
- run smoke tests;
- write code;
- modify tests;
- write fixtures;
- promote fixtures;
- update accepted manifests;
- change orchestration or CLI;
- implement candidate generator ingestion;
- implement Research Report V1 integration;
- change scoring / readiness / P1.1 / regression expected files;
- generate output;
- emit trading advice.

Official disclosure candidates are not target-price inputs, portfolio inputs,
position-sizing inputs, buy / sell / hold labels, or trading signals.

## 12. Roadmap

Completed sequence:

1. `official_disclosure_facts -> candidate generator integration` design.
2. Official disclosure candidate adapter implementation.
3. Retained 600406 official facts with tables -> official candidate payload
   runtime review.
4. Runtime acceptance summary and baseline freeze.

Historical recommended next stage, now recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_CANDIDATE_PAYLOAD_TO_FACT_CANDIDATES_BRIDGE_DESIGN.md
```

The bridge design should decide how an independent official candidate payload
can coexist with or be referenced by provider-centric `fact_candidates.json`
without silently changing the existing provider-centric schema.

Do not proceed directly to Research Report V1 integration, fixture promotion,
validator work, live CNInfo, Tushare primary switch, Dashboard / Batch, scoring
/ P1.1 changes, regression expected changes, or trading advice.

Current recommended next stage:

```text
Bridge artifact implementation
```
