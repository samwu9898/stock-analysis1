# Fundamental Auto Fact Candidate Generator Design

Date: 2026-05-27

Stage: Fundamental Skill Auto Fact Candidate Generator Design Documentation
Patch.

Status: design-only. This patch does not implement generator code, does not
modify the ground-truth fixture, does not implement a validator, does not read a
token, does not use the network, does not call Tushare, does not connect MCP,
does not change pipeline, classifier, scoring / readiness, P1.1, HTML /
Dashboard, provider-primary behavior, default output, provider raw artifacts,
evidence packs, or regression expected files, and does not output trading
advice.

Latest accepted project baseline referenced by this design:

- `pytest`: `655 passed, 1 skipped`
- regression suite: `passed=47 failed=0 total=47`

No pytest or regression run is required for this documentation-only stage.

## 1. Project Goal Correction

The project is not a manual spreadsheet-filling tool. The user should not be
responsible for finding most financial values or manually entering canonical
fields.

The intended product remains an automated A-share fundamental analysis Skill:

- The user inputs a stock code or a stock pool.
- The system fetches public and licensed data through approved providers.
- The system normalizes provider outputs into canonical fundamental fields.
- The system checks source, period, unit, type, missingness, and conflicts.
- The system decides which values are usable, which values are low-confidence,
  and which values require review.
- The system produces professional fundamental analysis with risks,
  opportunities, evidence gaps, and research judgement.

Human review is reserved for exception items such as source conflict, missing
source trace, unclear units, period mismatch, business-composition type gaps,
official-disclosure conflicts, and non-structured domain evidence. Ground truth
is a calibration and audit mechanism for the automated fact layer. It is not
the product's main user workflow.

The long-term target is an automated fundamental research analyst: the system
should collect the data, judge data quality, expose evidence gaps, and keep the
human focused on abnormal or ambiguous cases.

## 2. Candidate vs Ground Truth

`provider_fact_candidate` means a candidate fact automatically extracted from
Tushare, AkShare, existing provider-comparison artifacts, future CNInfo /
annual-report parsers, future announcement parsers, or later reviewed terminal
exports.

`accepted_candidate` means a candidate field that passes automatic source,
period, unit, type, and conflict checks. An accepted candidate is still an
auditable candidate until it is promoted to the reviewed fixture.

`manual_review_required` means the candidate is present but cannot be accepted
without human review because at least one gate is unclear or conflicting.

`reviewed_ground_truth` means a field value that has either passed the
auto-accept gate or has been confirmed by a human reviewer after candidate
generation. This is the only class of value that may enter the ground-truth
fixture.

Required boundaries:

- Provider output must not be written directly as reviewed ground truth.
- AkShare and Tushare must not be automatically merged.
- Tushare must not skip source, unit, period, or conflict checks merely because
  it is a paid structured source.
- The user must not carry the main burden of finding and entering financial
  data.
- The ground-truth fixture is a reviewed benchmark for calibration, not a user
  data-entry surface.

## 3. Auto Candidate Data Sources

V1 should start with offline artifact candidate generation. It can read
existing, already generated comparison artifacts without reading a token or
using the network.

V1 offline sources:

1. Existing provider-comparison artifacts, especially
   `output/provider_comparison/20260526T233804`.
2. Tushare canonical raw / fundamental output inside those artifacts.
3. AkShare canonical raw / fundamental output inside those artifacts.

Future live-provider sources:

1. Tushare canonical raw / fundamental output from an explicit, guarded provider
   path.
2. AkShare canonical raw / fundamental output from the existing public-data
   path.
3. Other approved provider outputs after provider-abstraction review.

Future official-disclosure parser sources:

1. CNInfo announcement records.
2. Company annual reports, semiannual reports, and quarterly reports.
3. Exchange disclosure records.
4. Announcement parsers for structured financial tables and business
   composition.

Future reference sources:

1. Wind / Choice / iFind manual exports as comparison inputs, storing only
   reviewed values and source references, not raw paid-source dumps.

The three generation modes are distinct:

- `offline_artifact_candidate_generation`: reads existing local artifacts only.
- `future_live_provider_candidate_generation`: fetches through approved
  provider paths with token / network safeguards.
- `future_official_disclosure_parser_candidate_generation`: parses official
  filings and announcement documents into candidate facts.

## 4. Candidate Field Scope

V1 automatic candidates should stay narrow and focus on fields that can be
traced, normalized, and compared.

### `basic_info`

- `stock_code`
- `stock_name`
- `industry`
- `listing_date`
- `main_business`: low confidence by default and usually
  `manual_review_required`.

### `financial_metrics`

- `period`
- `revenue`
- `net_profit`
- `gross_margin`
- `roe`
- `operating_cashflow`
- `accounts_receivable`
- `inventory`
- `contract_liabilities`
- `capex`

### `valuation_metrics`

- `as_of_date`
- `pe_ttm`
- `pb`
- `market_cap`

### `business_composition`

- `period`
- `classification_type`
- `segment_name`
- `revenue`
- `revenue_ratio`
- `gross_margin`

V1 excludes or defaults to manual review for:

- news narrative
- commodity prices
- domain evidence
- long-form `main_business`
- order validation
- customer validation
- liquid-cooling revenue share
- non-structured operating KPIs
- other sidecar evidence

Those fields can be handled later through sidecar or official-disclosure parser
designs, but they should not enter the first automatic financial fact
candidate scope.

## 5. Candidate Metadata

Every candidate must carry enough metadata to be audited, rejected, promoted,
or compared against another provider.

Required candidate keys:

- `field_path`
- `value`
- `source_provider`
- `source_artifact`
- `source_block`
- `source_endpoint`
- `source_trace`
- `report_period`
- `ann_date`
- `disclosure_date`
- `as_of_date`
- `data_unit`
- `canonical_unit`
- `derived`
- `derivation_method`
- `confidence`
- `review_status`
- `missing_category`
- `conflict_status`
- `manual_review_note`

Recommended `review_status` values:

- `auto_accepted`
- `manual_review_required`
- `rejected`
- `not_available`
- `source_conflict`
- `period_mismatch`
- `unit_unknown`
- `mapping_missing`
- `provider_missing`

Recommended `confidence` values:

- `high`
- `medium`
- `low`
- `unavailable`

`source_trace` should be structured enough to identify the artifact path,
provider, raw block, endpoint / function, source field, row selector, report
period, and whether the value was derived. It must not contain credentials,
local secret paths, MCP URLs, or raw paid-source exports.

Example `source_trace` shape:

```json
{
  "artifact_root": "output/provider_comparison/20260526T233804",
  "code": "600406",
  "provider": "tushare",
  "artifact_file": "tushare_raw.json",
  "block": "financial_indicator",
  "endpoint": "income",
  "source_field": "revenue",
  "json_pointer": "/blocks/financial_indicator/revenue",
  "row_selector": {"period": "YYYYMMDD"}
}
```

## 6. Auto Accept / Manual Review Rules

A field may be marked `auto_accepted` only when all of these conditions are
true:

- `source_provider` is Tushare or a future official parser.
- `report_period` or `as_of_date` is explicit and field-appropriate.
- `data_unit` is explicit.
- `canonical_unit` is normalized.
- `source_trace` is complete.
- `value` type matches the expected field type.
- Other available providers do not conflict beyond tolerance, or the conflict
  is explained by documented unit / period normalization.
- The field is not domain evidence.
- The field is not long-form `main_business`.
- The field is not a commodity / sidecar field.
- The field is not a news or narrative field.

AkShare-only values can be emitted as candidates, but should not be
auto-accepted as ground-truth-ready in V1. AkShare / Tushare agreement can
increase confidence, but agreement alone is not proof of reviewed ground truth.

A field must be marked `manual_review_required` or a more specific review
status when any of these conditions apply:

- period mismatch
- unit unknown
- provider conflict above threshold
- missing `source_trace`
- `main_business`
- missing `business_composition.classification_type`
- derived ratio with unclear denominator
- `market_cap` as-of-date mismatch
- domain evidence
- sidecar evidence
- commodity prices
- news / public narrative fields
- official-disclosure conflict with provider output

## 7. Conflict / Tolerance Rules

Candidate comparison should normalize values before conflict detection.

Amount fields:

- Convert to `RMB yuan` before comparison.
- Treat values as consistent when relative error is `<= 1%`.
- Preserve an absolute floor such as `RMB 1,000,000` for large-company amount
  fields where tiny relative values are not meaningful.

Ratio fields:

- Use percentage points as the canonical unit.
- Treat values as consistent when absolute error is `<= 0.5pct`.
- Allow `<= 1pct` only when the difference is explainable by rounding or
  definition differences, and record that note.

Valuation fields:

- `market_cap`, `pe_ttm`, and `pb` are date-sensitive.
- Compare only on the same `as_of_date`.
- If dates differ, mark `as_of_date_mismatch` / `period_mismatch` instead of
  accepting or failing the field as a fact.

Business composition:

- Compare only within the same report period and same classification group.
- Do not compare a `by_product` ratio against a `by_region` or `by_industry`
  ratio.
- Derived `revenue_ratio` requires a clear denominator and classification
  scope.

Text fields:

- Default to manual review.
- Normalize whitespace and punctuation for review assistance only.
- Do not auto-accept long-form `main_business`.

Provider disagreement policy:

- Provider disagreement above threshold is `source_conflict`.
- Tushare / AkShare agreement can raise candidate confidence, but it does not
  by itself create reviewed ground truth.
- Tushare / AkShare conflict must not be resolved by automatically choosing one
  provider unless source priority, unit, period, and trace are sufficient for
  the specific field.

## 8. Candidate Report Output Design

Future generator output path:

```text
output/ground_truth_candidates/<timestamp>/<code>/fact_candidates.json
```

Potential git-safe example fixture path:

```text
tests/fixtures/ground_truth/candidate_examples/600406_fact_candidates.example.json
```

Rules:

- A candidate report is not reviewed ground truth.
- Generated output stays out of git.
- Example fixtures may enter git only if they contain no credentials, MCP URLs,
  private paths, raw paid-source dumps, or large copyrighted excerpts.
- Candidate reports are used for audit and later promotion.
- The generator must not write default output.
- The generator must not write regression expected files.
- The generator must not write evidence packs.
- The generator must not write provider raw artifacts.

Candidate report review is a separate protocol layer, documented in
`docs/FUNDAMENTAL_CANDIDATE_REPORT_REVIEW_PROTOCOL_DESIGN.md`. That protocol
turns `manual_review_priority_queue` into a small set of executable review
actions. It does not change generator candidates, auto-accept rules, fixtures,
provider primary behavior, or provider data, and it does not read tokens, use
the network, call Tushare / AkShare, or connect MCP.

The review decisions artifact design is recorded in
`docs/FUNDAMENTAL_CANDIDATE_REVIEW_DECISIONS_ARTIFACT_DESIGN.md`. It turns the
protocol actions into `candidate_review_decisions.json` records under a future
isolated runtime path and remains an intermediate audit layer, not a fixture
write, provider merge, scoring change, or validator.

Recommended `fact_candidates.json` shape:

```json
{
  "code": "600406",
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "mode": "offline_artifact_candidate_generation",
  "source_artifacts": {
    "akshare_fundamental": "akshare_fundamental.json",
    "tushare_fundamental": "tushare_fundamental.json"
  },
  "candidates": [
    {
      "field_path": "financial_metrics.revenue",
      "value": null,
      "source_provider": "tushare",
      "source_artifact": "tushare_fundamental.json",
      "source_block": "financial_metrics",
      "source_endpoint": "income",
      "source_trace": {
        "artifact_file": "tushare_fundamental.json",
        "json_pointer": "/financial_metrics/revenue"
      },
      "report_period": "YYYY-12-31",
      "ann_date": null,
      "disclosure_date": null,
      "as_of_date": null,
      "data_unit": "RMB yuan",
      "canonical_unit": "RMB yuan",
      "derived": false,
      "derivation_method": null,
      "confidence": "high",
      "review_status": "auto_accepted",
      "missing_category": null,
      "conflict_status": "none",
      "manual_review_note": ""
    }
  ],
  "summary": {
    "auto_accepted_count": 0,
    "manual_review_required_count": 0,
    "source_conflict_count": 0,
    "unit_unknown_count": 0,
    "period_mismatch_count": 0
  }
}
```

## 9. Relationship With The Ground Truth Fixture

`tests/fixtures/ground_truth/fundamental_ground_truth_v1.json` is the reviewed
benchmark fixture. It should receive only reviewed facts.

The Auto Fact Candidate Generator produces candidates only. Initially it should
not write back to the fixture. A later patch may design a "promote candidate to
fixture" step, but that step must require either:

- `review_status=auto_accepted` after all auto-accept gates pass, or
- explicit human confirmation recorded as a reviewed promotion.

The fixture must not become the interface where users manually search for and
enter most financial data. It is a calibration benchmark for the automated
fact layer.

## 10. Relationship With The Validator

The correct sequence is:

1. Auto candidate generator.
2. Candidate review report.
3. Promote selected `auto_accepted` or human-reviewed fields to the fixture.
4. Validator compares provider / canonical output against the reviewed fixture.

The validator should not be implemented before candidate generation. A
validator may compare only against reviewed fixture fields. It must not treat
unreviewed candidates as truth.

## 11. Relationship With Tushare Primary

Auto fact candidates can inform a future block-level primary-provider design,
but they do not switch provider primary behavior.

If Tushare candidates for `financial_metrics` and `valuation_metrics` are
repeatedly `auto_accepted`, those blocks may become candidates for later
block-level primary review.

Current boundaries:

- `business_composition` still needs type and ratio validation.
- `main_business` needs CNInfo, annual-report, or official-profile support.
- news, commodity prices, and domain evidence cannot be filled by Tushare
  automatically.
- no global primary switch is allowed.
- Tushare is not correct because it is paid; it becomes trusted field by field
  only when source, unit, period, trace, and conflict checks pass.

## 12. Relationship With Final Product Experience

The final user experience should be:

- user enters a stock code or stock pool
- system automatically fetches data
- system automatically judges data quality
- system automatically generates macro / industry / company analysis
- system automatically marks risks, opportunities, evidence gaps, and research
  questions
- user sees `manual_review_required` items only when data quality requires it
- user is not asked to find data or fill tables

This module is the factual data layer for an automated fundamental research
analyst. It is not a standalone manual audit tool.

## 13. Safety / Non-Goals

This stage does not:

- write code
- modify the fixture
- implement a validator
- read `TUSHARE_TOKEN`
- use the network
- call Tushare
- connect MCP
- change provider primary behavior
- auto-merge AkShare and Tushare
- auto-accept drift
- change pipeline, classifier, scoring, readiness, P1.1, HTML, or Dashboard
- write default output, provider raw artifacts, evidence packs, or regression
  expected files
- output trading advice, target prices, position sizing, or portfolio weights

## 14. Roadmap

Recommended sequence:

1. This design document.
2. Implement offline candidate generation from the existing third-smoke
   artifacts.
3. Generate `fact_candidates.json` for `600406`.
4. Design and accept the Candidate Report Review Protocol.
5. Design the review decisions artifact.
6. Implement the review decisions artifact.
7. Convert `manual_review_priority_queue` into review decisions for the
   highest-value fields.
8. Accept the review decisions artifact.
9. Design promote rules.
10. Perform controlled fixture promotion only after promote rules are accepted.
11. Design and implement the validator only after reviewed fixture fields exist.
12. Design any Tushare block-level primary switch separately.
13. Add official parser / CNInfo parser support.
14. Add sidecar evidence designs for commodity prices and domain-specific
   operating evidence.

## 15. External Audit Position

No external audit is required as a mandatory gate for this documentation-only
stage because it does not change code, fixture values, pipeline behavior,
scoring, primary-provider selection, generated output, or regression
expectations, and it does not require a token.

Later patches should use stricter review, and possibly external audit, when
they implement:

- auto-accept logic
- promote-to-fixture logic
- official parser ingestion
- block-level Tushare primary behavior
- any provider merge or fallback decision that changes production output
