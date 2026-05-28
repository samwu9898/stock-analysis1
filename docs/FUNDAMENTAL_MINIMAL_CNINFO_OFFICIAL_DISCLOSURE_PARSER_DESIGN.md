# Fundamental Minimal CNInfo / Official Disclosure Parser Design

Date: 2026-05-28

Stage: Fundamental Skill Minimal CNInfo / Official Disclosure Parser Design.

Status: documentation-only design. This stage does not implement code, change
tests, change fixtures, change pipeline behavior, change scoring / readiness,
change Research Intelligence P1.1, change regression expected files, generate
output, write runtime artifacts, run smoke tests, read `TUSHARE_TOKEN`, use the
network, call CNInfo, call Tushare or AkShare, call any provider, connect MCP,
or provide investment advice.

Latest accepted verification results are quoted, not rerun here:

- targeted tests with retained manifest `251 passed`
- full pytest with retained manifest `899 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

Local-file implementation, the Conservative Period Patch, and the local sample
runtime review have since been accepted. The closeout is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_PARSER_LOCAL_SAMPLE_ACCEPTANCE_SUMMARY.md`.
The real local downloaded official filing sample runtime review has also been
accepted and is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_PARSER_REAL_LOCAL_FILING_ACCEPTANCE_SUMMARY.md`.
Latest accepted parser-stage verification results are quoted, not rerun in the
documentation-only summary: targeted tests `298 passed`, full pytest latest
`946 passed, 1 skipped`, and regression `passed=47 failed=0 total=47`.
The independent business-composition table parser design is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_PARSER_DESIGN.md`.
Its table schema / quality model implementation and caveat-only hardening are
accepted and frozen in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_SCHEMA_ACCEPTANCE_SUMMARY.md`.
The Local Structured Table Reader Design is recorded in
`docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_LOCAL_STRUCTURED_TABLE_READER_DESIGN.md`.
It remains a separate module, not part of the current minimal text parser.

## 1. Design Positioning

The minimal CNInfo / official disclosure parser is future official-evidence
infrastructure. It is not the current runtime default path.

The current accepted default path remains:

```text
offline local artifacts
  -> accepted manifest locator
  -> Research Report V1 HTML / Markdown / JSON
  -> no live provider
  -> no token
  -> no network
  -> no MCP
```

The parser's purpose is to gradually upgrade the current evidence boundary from
provider / artifact source labeling toward official disclosure evidence review.
It should read future already-downloaded or explicitly authorized official
filing text, extract a small number of high-value official fields, and produce
auditable fact candidates for later accepted processes.

The parser should support:

- `L1_official_disclosure` evidence-tier candidates;
- freshness / staleness trigger discovery;
- official-source `main_business` evidence;
- official business-composition wording and values;
- later management-guidance and delivery-rate tracking;
- later A-share-specific risk evidence framework.

The parser is not:

- a live provider default path;
- a Tushare replacement;
- a full disclosure-understanding system;
- a trading advice system;
- a target-price system;
- fixture promotion;
- a validator;
- Dashboard;
- Batch runner.

## 2. V1 Minimal Scope

V1 is intentionally narrow. It designs only the minimum official fields needed
to make later official-evidence review possible. It does not parse every
announcement type and does not promise complete PDF table extraction.

### A. Periodic Report Basics

V1 should represent:

- annual report;
- semiannual report;
- quarterly report;
- report period;
- disclosure date.

Minimum field examples:

- `document_type`
- `report_period`
- `disclosure_date`
- `source_document_id`
- `source_section`
- `source_page_or_anchor`

### B. Official Main Business Description

V1 should extract official wording for:

- `main_business_official_text`;
- source document;
- page, section, or anchor when available;
- extraction confidence;
- evidence tier candidate: `L1_official_disclosure`.

The extracted text remains a candidate until the parser confidence, source
location, and review process are accepted. It must not automatically overwrite
provider `main_business`, fixtures, scoring, readiness, P1.1, or reports.

### C. Business Composition

V1 should extract only directly disclosed business-composition fields:

- period;
- classification type, such as by product, region, or industry;
- segment name;
- revenue;
- revenue ratio;
- gross margin if directly disclosed;
- denominator / total revenue scope;
- unit;
- source location.

Required interpretation boundary:

- Revenue ratio must identify its denominator when possible.
- Gross margin should be marked as direct-disclosure only unless a later design
  explicitly allows derivation.
- Segment names should preserve official wording and avoid forced mapping into
  strategy-specific labels at parse time.
- Missing period, classification type, denominator, or unit must be recorded as
  a caveat, not inferred silently.
- Structured numeric business-composition extraction is delegated to the
  independent future table parser design. The current text parser must remain
  conservative.
- The accepted real local TXT filing review only detects business-composition
  regions with caveats. It does not extract revenue, cost, gross margin,
  revenue ratio, YoY, or segment values from copied PDF text because row /
  column alignment is unreliable without a separate table parser.

### D. Earnings Preannouncement / Flash / Guidance

V1 should model a minimal guidance record:

- guidance type;
- expected revenue, profit, or range if directly disclosed;
- guidance period;
- disclosure date;
- later actual result link placeholder.

The later actual result link is a placeholder only. V1 does not implement a
management guidance delivery-rate tracker.

### E. A-Share-Specific Risk Triggers

V1 should detect or model trigger candidates for:

- regulatory inquiry;
- regulatory penalty;
- shareholder reduction;
- share pledge risk;
- major contract / order announcement;
- major asset restructuring;
- related-party transaction;
- litigation / arbitration;
- auditor opinion change.

These are risk evidence / follow-up triggers only. They are not trading
signals, buy / sell indicators, target-price inputs, or position-sizing inputs.

## 3. Evidence Tier Design

Official parser output should support an explicit evidence-tier vocabulary:

| evidence tier | Meaning |
| --- | --- |
| `L1_official_disclosure` | CNInfo / exchange / company official filing text with source document and location. |
| `L2_multi_source_consistent` | Multiple market data providers agree on a field after source and period review. |
| `L3_single_source_candidate` | One provider or unreviewed artifact candidate. |
| `L4_unsupported_or_missing` | Hypothesis, unsupported claim, or missing evidence. |

Rules:

- Manifest / freshness status is not the same thing as evidence tier.
- The CNInfo / official parser can produce `L1_official_disclosure` candidates.
- `L1_official_disclosure` still requires parser confidence and source
  location.
- `L1_official_disclosure` does not automatically write fixtures.
- `L1_official_disclosure` does not automatically change scoring.
- `L1_official_disclosure` does not automatically change Research Intelligence
  P1.1.
- `L1_official_disclosure` does not automatically overwrite provider output.
- Research Report V1 may cite accepted L1 facts as stronger sources in a later
  accepted integration stage.

Evidence tier should travel with each extracted fact, not only with the source
document. One document can contain high-confidence fields, low-confidence
fields, and unparseable sections at the same time.

## 4. Parser Artifact Design

Future parser output should be isolated under:

```text
output/official_disclosures/<timestamp>/<code>/official_disclosure_facts.json
```

This is a runtime artifact. It must remain outside fixtures and regression
expected files unless a later accepted design creates a sanitized example.

Top-level schema:

```json
{
  "version": "official_disclosure_facts.v1",
  "code": "600406",
  "company_name": "",
  "created_at": "2026-05-28T00:00:00+08:00",
  "parser_version": "minimal_official_disclosure_parser.v1",
  "source_documents": [],
  "extracted_facts": [],
  "extraction_warnings": [],
  "data_quality_caveats": [],
  "not_for_trading_advice": true
}
```

Schema invariant: `not_for_trading_advice=true`.

`source_documents[]` should include at least:

```json
{
  "source_document_id": "doc_001",
  "document_type": "annual_report",
  "title": "",
  "report_period": "",
  "disclosure_date": "",
  "source_origin": "local_downloaded_official_disclosure",
  "source_uri_or_path": "",
  "sha256": "",
  "text_extraction_method": "",
  "text_extraction_quality": "",
  "caveats": []
}
```

Each `extracted_facts[]` item should include at least:

```json
{
  "fact_id": "fact_001",
  "field_path": "basic_info.main_business_official_text",
  "value": "",
  "unit": null,
  "period": "",
  "source_document_id": "doc_001",
  "source_section": "",
  "source_page_or_anchor": "",
  "evidence_tier": "L1_official_disclosure",
  "extraction_confidence": "medium",
  "needs_human_review": true,
  "caveats": []
}
```

Recommended confidence vocabulary:

- `high`: direct text or table value with clear source location and low
  ambiguity;
- `medium`: direct text or table value with minor location, formatting, or
  section ambiguity;
- `low`: weak parse, uncertain section, missing denominator, missing unit, or
  text-extraction caveat.

Recommended document types:

- `annual_report`
- `semiannual_report`
- `quarterly_report`
- `earnings_preannouncement`
- `earnings_flash`
- `guidance_or_operating_update`
- `major_contract_or_order`
- `regulatory_inquiry`
- `regulatory_penalty`
- `shareholder_reduction`
- `share_pledge`
- `major_asset_restructuring`
- `related_party_transaction`
- `litigation_arbitration`
- `auditor_opinion_change`
- `other_official_disclosure`

## 5. Relationship To Existing Artifact Chain

`official_disclosure_facts.json` is a future input to the fact-candidate chain.
It is not a direct replacement for provider artifacts or accepted report
artifacts.

Allowed future relationships:

- It can help the candidate generator create L1 official fact candidates.
- It can help review decisions reduce manual-review burden.
- It can help Research Report V1 strengthen data-quality assessment.
- It can help freshness manifest logic identify staleness triggers.
- It can provide official source locations for main business and business
  composition.
- It can provide risk-trigger evidence for later A-share-specific risk
  sections.

Forbidden direct effects:

- It must not directly write fixtures.
- It must not directly update the accepted artifact manifest.
- It must not directly change Research Report V1 output.
- It must not directly change provider primary behavior.
- It must not automatically merge provider data.
- It must not change scoring, readiness, P1.1, or regression expected files.

Future conceptual flow:

```text
local downloaded official filing text
  -> minimal official disclosure parser
  -> official_disclosure_facts.json
  -> fact_candidates.json candidate generation
  -> candidate_review_decisions.json
  -> accepted process
  -> possible L1 usage by reports / freshness policy
```

## 6. Freshness / Staleness Trigger Relationship

The official parser can later support trigger discovery for:

- annual report trigger;
- semiannual report trigger;
- quarterly report trigger;
- earnings preannouncement;
- earnings flash;
- management guidance;
- major contract / order;
- shareholder reduction;
- regulatory inquiry / penalty;
- auditor opinion change.

Rules:

- This V1 design-only stage does not check the network.
- Future implementation may first read only local downloaded filings.
- Live CNInfo fetch requires a separate design, permission boundary, and
  acceptance cycle.
- Trigger discovery does not automatically mean a Research Report V1 artifact
  is stale.
- Whether a trigger changes freshness status requires policy judgment.
- A trigger may update manifest freshness only after the accepted process.
- The manifest remains the accepted artifact locator, not the trigger detector.

Example trigger record:

```json
{
  "trigger_type": "annual_report",
  "trigger_date": "2026-04-30",
  "related_period": "2025A",
  "source_document_id": "doc_001",
  "policy_effect": "review_required",
  "automatic_stale": false,
  "caveats": []
}
```

## 7. A-Share-Specific Risk Mapping

Minimal risk trigger mapping:

| official trigger | risk bucket |
| --- | --- |
| shareholder reduction | `shareholder_behavior_risk` |
| share pledge | `pledge_liquidity_risk` |
| regulatory inquiry / penalty | `regulatory_risk` |
| related-party transaction | `related_party_risk` |
| litigation / arbitration | `legal_risk` |
| major contract / order announcement | `order_realization_followup` |
| major asset restructuring | `business_structure_change_risk` |
| auditor opinion change | `accounting_quality_risk` |

Rules:

- These mappings create risk evidence / follow-up triggers only.
- They are not trading signals.
- They do not imply direction, timing, price target, or position advice.
- Major contract / order announcements require later realization follow-up;
  announcement text alone is not revenue, cash collection, margin, or delivery
  proof.
- Regulatory inquiry and penalty triggers require source-location preservation
  and careful wording because severity and remediation status can differ.

## 8. Safety / Non-Goals

This stage and the future V1 parser boundary must not:

- read `TUSHARE_TOKEN`;
- use the network;
- call CNInfo;
- call Tushare;
- call AkShare;
- call any provider;
- connect MCP;
- write `output/` during design-only work;
- submit runtime artifacts;
- write fixtures;
- change scoring, readiness, P1.1, or regression expected files;
- automatically update the accepted manifest;
- output buy / sell advice;
- output target prices;
- output position sizing;
- output technical trading signals;
- perform full OCR;
- parse every PDF table;
- promise 100 percent field accuracy.

Future implementation must keep token, provider, network, MCP, output, fixture,
manifest, and scoring boundaries explicit in command flags and review notes.

## 9. Roadmap

Accepted sequence:

1. Minimal CNInfo / official disclosure parser design.
2. Parser schema / local-file reader implementation.
3. Conservative Period Patch.
4. Local sample runtime review using
   `output/official_disclosures/local_samples/600406_annual_report_sample.txt`.
5. Ignored runtime artifact generation and validation at
   `output/official_disclosures/20260528_194020/600406/official_disclosure_facts.json`.
6. Real local downloaded official filing sample runtime review using
   `output/official_disclosures/local_real_samples/600406_2025_semiannual_report_real.txt`.
7. Ignored real local filing runtime artifact validation at
   `output/official_disclosures/20260528T125521Z/600406/official_disclosure_facts.json`.
8. Official Disclosure Business Composition Table Parser Design recorded in
   `docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_PARSER_DESIGN.md`.
9. Business Composition Table Schema / Quality Model implementation and
   caveat-only hardening accepted in
   `docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_SCHEMA_ACCEPTANCE_SUMMARY.md`.
10. Local Structured Table Reader Design recorded in
    `docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_LOCAL_STRUCTURED_TABLE_READER_DESIGN.md`.

Historical recommended next sequence:

1. CSV reader schema / implementation for the independent table parser.
2. One local CSV structured sample runtime review.
3. Local HTML table reader design / implementation.
4. DOCX table reader design / implementation.
5. Table quality integration runtime review.
6. Add table facts to `official_disclosure_facts.json` only after table
   quality, source location, row / column alignment, units, denominators, and
   total checks are explicit.
7. Add L1 evidence tier handling only after a separate accepted integration
   design.
8. Add candidate generator integration only after a separate accepted
   integration design.
9. Add Research Report V1 integration only after a separate accepted
   integration design.
10. Add freshness trigger integration only after separate policy acceptance.
11. Later PDF table extraction design.
12. Later live CNInfo fetch design.
13. Later management guidance tracker.

Implementation should start with local files only. Any live CNInfo fetch, MCP
connector, token handling, provider use, fixture promotion, validator, report
rewrite, batch, or Dashboard behavior requires a separate design and acceptance
stage.

The accepted local sample and real local filing runtimes do not change this
boundary. The first used local official-style sample text. The second used a
user-prepared real local TXT copied or converted from the official `600406`
2025 semiannual report PDF. Neither used live CNInfo, providers, tokens,
network, or MCP. The real local filing review validated the schema /
local-file reader / conservative extractor / business-composition section
detection with caveat / writer / reader / validator loop only. It does not make
L1 official disclosure facts eligible for direct candidate-generator or
Research Report V1 use.

## 10. Table Facts To Official Disclosure Facts Integration Design Sync

The table facts -> `official_disclosure_facts.json` integration design is now
recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_TABLE_FACTS_TO_OFFICIAL_DISCLOSURE_FACTS_INTEGRATION_DESIGN.md
```

This design extends the future parser artifact assembly contract while keeping
the minimal parser boundary unchanged:

- `extracted_facts[]` remains the unified fact list;
- table facts use the `business_composition.*` namespace;
- optional `source_tables[]` preserves normalized table trace;
- optional `table_caveats[]` preserves table-level caveats and failed gates;
- table facts remain caveated L1 official disclosure candidates, not reviewed
  facts;
- `not_for_trading_advice=true` remains mandatory;
- no verified fact is generated;
- candidate generator implementation remains later work;
- Research Report V1 integration remains later work.

The current retained CSV table facts runtime artifact is:

```text
output/official_disclosures/20260529T002922/600406/csv_table_facts_review.json
```

Current next recommended stage:

```text
Table facts -> official_disclosure_facts integration implementation
```

The implementation stage should remain local-only, fail-closed, and separate
from live CNInfo, providers, tokens, network, MCP, fixtures, accepted
manifests, candidate generation, Research Report V1, scoring, P1.1,
regression expected files, and trading advice.

## 11. Documentation Sync Notes

This design should be referenced by:

- `docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_PARSER_DESIGN.md`
- `docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_BUSINESS_COMPOSITION_TABLE_SCHEMA_ACCEPTANCE_SUMMARY.md`
- `docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_LOCAL_STRUCTURED_TABLE_READER_DESIGN.md`
- `docs/FUNDAMENTAL_ACCEPTED_ARTIFACT_MANIFEST_FRESHNESS_DESIGN.md`
- `docs/FUNDAMENTAL_RESEARCH_REPORT_V1_DESIGN.md`
- `docs/PROJECT_CONTEXT_HANDOFF.md`
- `docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_PARSER_LOCAL_SAMPLE_ACCEPTANCE_SUMMARY.md`
- `docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_PARSER_REAL_LOCAL_FILING_ACCEPTANCE_SUMMARY.md`

The current accepted runtime baseline remains unchanged:

- Research Report V1 JSON / Markdown / HTML chain accepted.
- Single-stock offline CLI baseline frozen.
- Accepted manifest module accepted.
- Manifest-first locator hardening accepted.
- Retained runtime manifest review accepted.
- Manifest locator runtime baseline frozen.
- Retained ignored runtime manifest:
  `output/research_reports/accepted_manifest.json`.
- Default path remains offline local artifacts / no live provider / no token /
  no network / no MCP.
- Business-composition table parser design is recorded; table schema / quality
  model implementation and caveat-only hardening are accepted and frozen.
- Local Structured Table Reader Design is recorded; no reader implementation is
  accepted yet.
- No business-composition table reader or writer is implemented yet.
- Live CNInfo is not implemented.
- PDF table parser is not implemented.
- DOCX / HTML / CSV / Excel table readers are not implemented.
- Candidate generator integration is not implemented.
- L1 official disclosure integration is not implemented.
- Research Report V1 integration is not implemented.

## 12. Official Disclosure Facts With Tables Runtime Acceptance Sync

The minimal official disclosure payload can now be assembled with retained CSV
table facts in a runtime-review-only path after source-document alignment. The
accepted closeout is recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_FACTS_WITH_TABLES_RUNTIME_ACCEPTANCE_SUMMARY.md
```

Runtime acceptance record:

- base payload:
  `output/official_disclosures/20260528T125521Z/600406/official_disclosure_facts.json`;
- aligned source document id:
  `600406_2025_semiannual_report_real`;
- integrated runtime artifact:
  `output/official_disclosures/20260528T173612Z/600406/official_disclosure_facts_with_tables_review.json`;
- base `source_documents=1`;
- base `extracted_facts=1`;
- integrated `extracted_facts=7`;
- `source_tables=1`, `table_caveats=4`,
  `table_conversion_warnings=4`;
- `source_documents` remained 1;
- no verified fact.

Parser boundary remains conservative:

- table facts are runtime-review-only caveated L1 official disclosure
  candidates;
- explicit `source_document_id` alignment is mandatory;
- source lineage mismatch must fail closed;
- no automatic source id rewriting;
- no candidate generator implementation yet;
- no Research Report V1 integration yet;
- no live CNInfo, provider call, token read, network, MCP, fixture promotion,
  or accepted manifest update.

Historical next recommended official-disclosure stage, now recorded in a
separate design:

```text
official_disclosure_facts -> candidate generator integration design
```

## 13. Official Disclosure Facts To Candidate Generator Design Sync

The official disclosure facts -> candidate generator integration design is now
recorded in:

```text
docs/FUNDAMENTAL_OFFICIAL_DISCLOSURE_FACTS_TO_CANDIDATE_GENERATOR_INTEGRATION_DESIGN.md
```

Parser relationship:

- `official_disclosure_facts.json` remains a local official-disclosure parser
  artifact;
- future candidate generation may read `source_documents[]`,
  `extracted_facts[]`, `source_tables[]`, `table_caveats[]`,
  `table_conversion_warnings[]`, `extraction_warnings[]`, and
  `data_quality_caveats[]`;
- official text facts and table facts are both candidate sources;
- `L1_official_disclosure`, source location, extraction confidence, caveats,
  and human-review requirements must be preserved;
- official candidates do not overwrite provider candidates;
- no official candidate becomes a `verified_fact`.

Current parser boundary remains unchanged:

- no live CNInfo;
- no provider call;
- no token read;
- no network;
- no MCP;
- no fixture promotion;
- no accepted manifest update;
- no Research Report V1 integration.

Next recommended stage:

```text
official_disclosure_facts -> candidate generator integration implementation
```
