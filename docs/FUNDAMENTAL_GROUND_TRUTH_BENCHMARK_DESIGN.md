# Fundamental Ground Truth Benchmark Design

Date: 2026-05-27

Stage: Fundamental Skill Ground Truth Benchmark Design Documentation Patch.

Status: design-only. This patch does not implement validator code, does not add
ground-truth fixtures, does not modify tests, config, pipeline, classifier,
scoring / readiness, Research Intelligence P1.1, HTML / Dashboard, runtime
output, regression expected files, or provider-primary behavior.

Latest accepted project baseline referenced by this design:

- `pytest`: `648 passed, 1 skipped`
- regression suite: `passed=47 failed=0 total=47`

No pytest or regression run is required for this documentation-only stage.

## 1. Current Problem Definition

The current verification system proves important engineering properties, but it
does not yet prove that every surfaced fundamental field is factually correct.

Current verification coverage:

- `pytest` proves code paths, edge cases, schema behavior, safety gates,
  provider boundaries, token-safety behavior, and deterministic module
  contracts.
- The regression suite proves output stability against frozen fixtures and
  expectations.
- Provider comparison proves AkShare / Tushare differences under a
  provider-separated comparison path.
- Phase 4 explainability proves that score / confidence drift can be surfaced
  for human review without automatic merge or drift acceptance.

Current non-coverage:

- There is no human-reviewed factual benchmark that independently verifies the
  canonical values in `basic_info`, `financial_metrics`, `valuation_metrics`,
  and `business_composition`.
- If the AkShare baseline is wrong, the current regression suite may only prove
  that the same wrong value is reproduced stably.
- Provider comparison can show that AkShare and Tushare disagree, but it cannot
  by itself decide which source is factually correct.
- A stable canonical pipeline output is not the same thing as a verified
  financial fact.

Ground Truth Benchmark target:

- Verify selected factual fields against manually reviewed source references.
- Keep the benchmark separate from investment judgement.
- Produce audit evidence about field correctness, source, period, unit, and
  missingness category.
- Provide a later basis for provider mapping fixes and block-level primary
  design.

Ground Truth Benchmark non-target:

- It must not output buy / sell advice, target prices, position sizing, or any
  trading recommendation.
- It must not change scoring logic, classifier logic, readiness logic, P1.1
  support scope, HTML / Dashboard behavior, or regression expected files.
- It must not treat Tushare as ground truth merely because it is paid or
  structured.

## 2. V1 Sample Pool Design

V1 should start with 8 to 12 manually reviewed stocks. The target size is 12
samples: six Phase 4 comparison / narrative-hint samples, two P1.1 validation /
boundary samples from accepted project history, and four broader validation /
caveat samples.

| Code | Name | Why Selected | Expected Strategy Type | Role | Primary Field Focus | AkShare / Tushare Comparison Fit | P1.1 Deep Validation Fit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `600406` | 国电南瑞 | Accepted Stable Growth first-version positive sample; important grid-equipment baseline. | `stable_growth` | positive | `basic_info`, `financial_metrics`, `valuation_metrics`, business-composition ratio and main-business gap. | High; Phase 4 narrative hints already flag main-business and business-ratio gaps. | High; accepted P1.1 positive sample. |
| `002050` | 三花智控 | Accepted Advanced Manufacturing first-version positive sample; covers auto thermal management, refrigeration, and emerging-business evidence boundaries. | `advanced_manufacturing_growth` | positive | segment revenue, segment ratio, gross margin, R&D, capex, receivables, valuation. | High; useful for checking whether Tushare improves financial / valuation fields while composition remains constrained. | High; accepted P1.1 positive sample, but robotics/new-business claims still require conservative evidence. |
| `002371` | 北方华创 | Accepted Semiconductor first-version positive sample; equipment-cycle and domestic-substitution narratives require factual field discipline. | `semiconductor_cycle` | positive | R&D expense and ratio, inventory, capex, revenue growth, gross margin, business segment fields. | High; Phase 4 hints distinguish available financial inputs from business-text / ratio gaps. | High; accepted P1.1 positive sample. |
| `603259` | 药明康德 | CXO representative; generic fundamentals cannot prove backlog, geography, or utilization. | `life_science_cxo_services` | positive / caveat | revenue, profit, margins, OCF, receivables, contract liabilities, overseas / segment composition if available. | High; useful for identifying generic-provider limits versus official disclosure. | Medium-high; P1.1 CXO supported, but domain evidence should remain conservative. |
| `000426` | 兴业银锡 | Resource Swing first implementation; commodity context must remain sidecar and not a provider merge. | `resource_swing` | positive / caveat | revenue, profit, OCF, debt, inventory, business composition, commodity-exposure composition. | High; Phase 4 score / confidence drift highlighted sidecar boundary. | High for `resource_swing + 000426`; do not generalize to `resource_core`. |
| `002837` | 英维克 | AI datacenter cooling / liquid-cooling infrastructure sample; generic fundamentals do not prove liquid-cooling realization. | `ai_datacenter_infrastructure` | positive / caveat | cooling-related business composition, liquid-cooling revenue share if disclosed, orders/customer evidence metadata, financials, valuation. | High; Tushare-only view is expected to miss domain evidence. | High; accepted AI datacenter P1.1 coverage sample, with explicit missing-domain-evidence policy. |
| `002028` | 思源电气 | Stable Growth boundary / validation sample; should not be promoted into first-version positive support. | `stable_growth` | boundary / validation | stable-growth field quality: OCF, receivables, ROE, capex, contract liabilities, business composition. | Medium-high; useful to test whether factual fields support conservative boundary handling. | Medium; validation only, not first-version positive support. |
| `601689` | 拓普集团 | Advanced Manufacturing boundary sample; classifier may recognize the strategy, but P1.1 should remain unsupported for this sample. | `advanced_manufacturing_growth` | boundary / validation | business segments, large-customer / robotics exposure fields if disclosed, receivables, inventory, capex, valuation. | High; known data caveat on news does not affect fundamental-field benchmark. | Medium; validation / boundary only, not first-version support. |
| `300442` | 润泽科技 | AI datacenter operator sample from accepted validation history; complements `002837` cooling subtype. | `ai_datacenter_infrastructure` | validation | revenue, capex, depreciation-related fields if available, OCF, debt, cabinet / MW / utilization source metadata as future sidecar notes. | Medium; generic providers may cover financials but not operator KPIs. | Medium-high; accepted AI datacenter sample, useful later for deep validation after field benchmark. |
| `601698` | 中国卫通 | Satellite communication infrastructure positive sample; asset-heavy infrastructure fields stress capex / OCF interpretation. | `satellite_communication_infrastructure` | validation | financials, business composition, capex, OCF, depreciation-related future fields, valuation. | Medium; basic financial and valuation fields fit comparison, satellite operating KPIs likely need official reports. | Medium-high; accepted satellite P1.1 sample. |
| `601899` | 紫金矿业 | Resource Core representative; intentionally not covered by Resource first implementation. | `resource_core` | caveat / excluded for P1.1 V1 | revenue, profit, OCF, debt, inventory, capex, dividend-yield context, multi-resource composition. | Medium-high; financial / valuation comparison useful, commodity and reserve data need sidecar or annual report. | Low for current P1.1; use only after `resource_core` design acceptance. |
| `300308` | 中际旭创 | Right-trend growth / AI optical module boundary; should not be forced into semiconductor or AI datacenter infrastructure. | `right_trend_growth` | boundary / excluded from current P1.1 slices | revenue growth, margins, inventory, receivables, capex, valuation, business segment evidence. | Medium-high; financial / valuation fields useful, domain evidence not covered by generic providers. | Low-medium; useful as controversial / boundary case, not accepted P1.1 support. |

V1 sampling principles:

- Keep the sample set small enough for manual source review.
- Include positive samples only where existing project history already accepted
  the strategy slice.
- Include boundary and caveat samples to prevent the benchmark from becoming a
  success-only sample set.
- Do not expand P1.1 support merely because a stock is included in ground-truth
  field validation.

## 3. V1 Ground Truth Field List

The benchmark should verify canonical factual fields first. Domain-specific
operating evidence can be recorded as a missingness note or future sidecar
candidate, but should not enter V1 financial ground truth unless it is clearly
available from official disclosure.

### `basic_info`

- `stock_code`
- `stock_name`
- `industry`
- `listing_date`
- `main_business`: include when a reliable source is available; otherwise mark
  `unavailable` with `source_not_disclosed` or `source limitation`.

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

Valuation fields must include an as-of date because they are market-date
sensitive.

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

Business-composition rows should preserve the source classification group.
Ratios must not be derived across different groups or periods.

### Provider / Source Metadata

Every checked field or row should be traceable to source metadata:

- `source_name`
- `source_url_or_doc_ref`
- `report_period`
- `disclosure_date` / `ann_date`
- `data_unit`
- `canonical_unit`
- `manual_review_note`
- `confidence_of_ground_truth`

Recommended confidence values:

- `high`: official report / announcement with clear period and unit.
- `medium`: reliable structured source with clear period and unit, manually
  checked for plausibility.
- `low`: value is plausible but source, unit, period, or mapping has caveats.
- `unavailable`: no reliable value found for this benchmark version.

## 4. Reliable Source Priority

AkShare and Tushare are provider outputs to be evaluated. They should not be
treated as the ground truth by default.

Source priority:

1. Company annual report, semiannual report, quarterly report, or original
   disclosure document.
2. Exchange or CNInfo announcement record.
3. Tushare paid API as a high-confidence structured reference when period,
   unit, and endpoint semantics are recorded.
4. Wind / Choice / iFind exports if the user later performs a manual export and
   the benchmark stores only reviewed field values and source references.
5. AkShare as public aggregation reference.
6. News articles or third-party webpages; these are not financial ground truth
   for V1.

Policy notes:

- Tushare can be a strong structured source, but the benchmark must still
  record source, endpoint / document reference, period, ann_date, and units.
- AkShare must not be the only source of a ground-truth financial value.
- `business_composition` should prefer annual reports / announcements or a
  reliable structured interface with clear type / period semantics.
- News and domain-evidence items should not enter the first-version financial
  ground truth. They should be handled later through a separate sidecar
  benchmark.

## 5. Tolerance Design

The benchmark should compare normalized canonical values, not raw provider
strings.

Amount fields:

- Convert units before comparison.
- Default pass threshold: relative error `<= 1%`.
- Add an absolute-error floor for small values, for example
  `max(1% relative, 1,000,000 RMB)` for large-company RMB amounts, or a
  field-specific floor documented in the fixture.
- `market_cap` must explicitly declare whether source units are RMB yuan,
  thousand RMB, ten-thousand RMB, hundred-million RMB, or another unit. RMB yuan
  and ten-thousand RMB must never be mixed silently.

Ratio fields:

- Default pass threshold: `<= 0.5pct` for stable financial ratios when source
  units are clear.
- Allow `<= 1pct` when source definitions differ slightly, for example
  weighted ROE versus diluted ROE, or gross-margin rounding in segment tables.
- `business_composition.revenue_ratio` default threshold:
  `<= 0.5pct`; allow `<= 1pct` for rounded annual-report tables.

Valuation fields:

- Valuation fields are trade-date sensitive.
- `pe_ttm`, `pb`, `ps`, `market_cap`, and `dividend_yield` should be compared
  only against the same as-of date where possible.
- If provider outputs use different trade dates, use a wider threshold and mark
  `period_mismatch` / `as_of_date_mismatch`, not a factual failure by default.

Text fields:

- Exact match is unrealistic for `industry`, `main_business`, and segment names.
- Use normalized text comparison plus manual judgement.
- Normalize whitespace, punctuation, full-width / half-width variants,
  simplified variants where appropriate, and common suffixes such as company
  legal-form wording.
- Retain the reviewer note explaining accepted text equivalence.

Missing field categories:

- `provider_missing`: provider does not supply the field, but source ground
  truth exists.
- `source_not_disclosed`: no reliable public source disclosure was found.
- `mapping_missing`: source/provider appears to have the value, but canonical
  mapping does not expose it.
- `unit_unknown`: source or provider unit cannot be established.
- `period_mismatch`: provider and ground-truth periods are not comparable.
- `manual_review_required`: value may be comparable, but semantics require
  human review.

## 6. Benchmark Data File Design

No data file is created in this stage.

Recommended future path:

```text
tests/fixtures/ground_truth/fundamental_ground_truth_v1.json
```

Alternative future path if the benchmark is operated as an audit dataset rather
than a test fixture:

```text
data/ground_truth/fundamental_ground_truth_v1.json
```

Git policy:

- A small manually curated benchmark may be committed to git.
- It must not contain real tokens, MCP URLs, local secret paths, or private
  connection strings.
- It must not contain large raw paid-source exports.
- It may contain manually reviewed field values, source names, source document
  references, units, periods, and reviewer notes.
- If source copyright is uncertain, store only field values and source
  references, not long source text excerpts.

Recommended JSON shape:

```json
{
  "version": "fundamental_ground_truth.v1",
  "created_at": "2026-05-27",
  "scope": {
    "benchmark_type": "manual_field_ground_truth",
    "not_for_trading_advice": true,
    "does_not_modify_scoring": true
  },
  "samples": [
    {
      "code": "600406",
      "name": "国电南瑞",
      "strategy_type_expected": "stable_growth",
      "sample_role": "positive",
      "fields": {
        "basic_info": {
          "stock_code": {
            "value": "600406",
            "source_ref": "src_annual_report_2025",
            "confidence_of_ground_truth": "high"
          },
          "main_business": {
            "value": null,
            "missing_category": "source_not_disclosed",
            "manual_review_note": "Use official report text only if manually reviewed."
          }
        },
        "financial_metrics": {
          "period": "YYYY-12-31",
          "revenue": {
            "value": null,
            "data_unit": "RMB yuan",
            "canonical_unit": "RMB yuan",
            "source_ref": "src_annual_report_2025",
            "confidence_of_ground_truth": "high"
          }
        },
        "valuation_metrics": {
          "as_of_date": "YYYY-MM-DD",
          "market_cap": {
            "value": null,
            "data_unit": "RMB yuan",
            "canonical_unit": "RMB yuan",
            "source_ref": "src_daily_basic_YYYYMMDD",
            "confidence_of_ground_truth": "medium"
          }
        },
        "business_composition": [
          {
            "period": "YYYY",
            "classification_type": "by_product",
            "segment_name": "example segment",
            "revenue": null,
            "revenue_ratio": null,
            "gross_margin": null,
            "cost": null,
            "profit": null,
            "profit_ratio": null,
            "source_ref": "src_annual_report_2025",
            "confidence_of_ground_truth": "high"
          }
        ]
      },
      "source_refs": {
        "src_annual_report_2025": {
          "source_name": "company annual report",
          "source_url_or_doc_ref": "official disclosure document reference",
          "report_period": "YYYY",
          "disclosure_date": "YYYY-MM-DD",
          "ann_date": "YYYY-MM-DD",
          "source_priority": 1
        },
        "src_daily_basic_YYYYMMDD": {
          "source_name": "structured valuation source",
          "source_url_or_doc_ref": "endpoint/date reference",
          "report_period": "YYYY-MM-DD",
          "disclosure_date": null,
          "ann_date": null,
          "source_priority": 3
        }
      },
      "tolerance": {
        "amount_relative_pct": 1.0,
        "amount_absolute_floor_rmb": 1000000,
        "ratio_pct_point": 0.5,
        "business_revenue_ratio_pct_point": 0.5,
        "valuation_policy": "same_trade_date_required_or_mark_period_mismatch",
        "text_policy": "normalized_text_plus_manual_judgement"
      },
      "manual_review_notes": [
        "No investment recommendation is encoded in this fixture."
      ],
      "audit_status": "draft_manual_review_required"
    }
  ]
}
```

Suggested `audit_status` values:

- `draft_manual_review_required`
- `reviewed_ready_for_validator`
- `source_conflict_manual_review_required`
- `blocked_source_limitation`
- `deprecated_replaced_by_new_period`

## 7. Future Validator Design

The validator is not implemented in this stage.

Future validator inputs:

- Ground truth JSON.
- Provider raw / fundamental / evidence-pack artifacts.
- AkShare canonical output.
- Tushare canonical output.
- Final pipeline output.

Future validator outputs:

- passed fields
- failed fields
- missing fields
- unit mismatch
- period mismatch
- source mismatch
- manual review required
- provider-specific comparison summary
- canonical pipeline correctness summary

Validator rules:

- It must not modify production output.
- It must not modify regression expected files.
- It must not write back to canonical provider fields.
- It may run as a new test or an independent audit script.
- Initial implementation should be an independent script, not mandatory CI,
  because the human-labelled dataset will still be small and evolving.
- After the fixture is stable, consider optional CI / manual gate mode.
- A failing provider field should produce an audit report first; it should not
  automatically update baseline values.

Recommended validator report sections:

- sample summary by code and strategy type
- field-level comparison table
- unit-normalization log
- period / as-of-date compatibility table
- missingness categories
- provider ranking by block, not global provider ranking
- canonical pipeline correctness summary
- recommended human-review items

## 8. Relationship With Existing Regression

Regression remains necessary and should not be replaced.

Relationship:

- Regression suite prevents unreviewed output drift.
- Ground Truth Benchmark verifies factual correctness of selected canonical
  fields.
- The two systems are complementary.
- Ground Truth Benchmark should not be mixed directly into the existing
  regression expected files.
- Do not change regression expected files merely because Tushare appears more
  credible than AkShare.
- First generate a benchmark report, then decide whether a provider mapping,
  canonical baseline, or regression expectation needs a separate reviewed patch.

Important distinction:

- Regression answer: "Did the output change?"
- Ground truth answer: "Is this field factually correct for this period, unit,
  and source?"

## 9. Relationship With Tushare Primary Switch

This benchmark is a prerequisite for primary-provider decisions, but it is not
itself a switch.

Decision logic:

- If Tushare is clearly more correct than AkShare for `financial_indicator` and
  `valuation` against ground truth, it may enter a block-level primary design.
- If `business_composition` still lacks reliable `revenue_ratio`,
  `profit_ratio`, or `classification_type`, do not switch that block.
- If `main_business` remains better supported by CNInfo / annual reports, do
  not derive it from largest segment rows.
- If news, commodity, or domain evidence is not covered, keep it in sidecar /
  future provider design.
- Do not switch global primary provider based on a small benchmark.

Recommended block-level primary candidates:

- `financial_indicator`: Tushare candidate after ground-truth pass.
- `valuation`: Tushare candidate after same-date / same-unit validation.
- `basic_identity`: Tushare candidate for code, name, listing date, and
  industry after manual checks.
- `main_business`: CNInfo / annual report / future provider candidate.
- `business_composition`: pending ratio / type validation.
- `news`: future news / announcement provider.
- `commodity_prices`: independent sidecar.
- `domain_evidence`: sidecar / annual report / announcement.

No automatic AkShare / Tushare merge is allowed. Any provider switch must be a
separate design, implementation, acceptance, and regression-review cycle.

## 10. Relationship With P1.1 Deep Validation

Ground truth field validation should come before P1.1 research-quality
validation.

Sequence:

- Ground Truth Benchmark first validates whether canonical fields are factually
  correct.
- P1.1 deep validation then evaluates whether the research questions and
  driver matrices use available evidence properly.
- P1.1 quality should not be judged while key factual fields are unverified.

Future P1.1 expansion sampling rule:

- choose one strong case
- choose one weak / problem case
- choose one controversial / boundary case

This stage does not implement P1.1 deep validation and does not expand P1.1
industry support.

## 11. Explicit Non-Goals For This Stage

This stage does not:

- change code
- write benchmark data files
- run real smoke
- read `TUSHARE_TOKEN`
- use the network
- call Tushare
- connect MCP
- modify regression expected files
- switch Tushare primary
- automatically merge AkShare and Tushare
- automatically accept drift
- expand P1.1 industry support
- implement sidecar data
- implement technical skill
- connect trading accounts
- output investment advice, buy / sell advice, target prices, or position sizing

## 12. Roadmap

Recommended sequence:

1. This design document.
2. Ground Truth Benchmark schema / fixture implementation.
3. Manual entry for a small number of samples.
4. Ground truth validator script.
5. Benchmark report for AkShare / Tushare / canonical output.
6. Tushare block-level primary design.
7. P1.1 deep validation.
8. `fina_mainbz type=P/D/I` ratio derivation.
9. Sidecar data availability design.

## 13. Delivery Checklist For This Patch

This documentation patch should leave the repository in a design-only state:

- New design document added under `docs/`.
- Optional handoff / migration docs may be synchronized to reference the new
  design and next step.
- No validator code added.
- No ground-truth fixture added.
- No test, config, pipeline, classifier, scoring / readiness, P1.1, HTML /
  Dashboard, output, or regression expected file changed.
- No token or MCP URL written.
- No smoke, Tushare call, token read, network access, or MCP connection
  performed.
