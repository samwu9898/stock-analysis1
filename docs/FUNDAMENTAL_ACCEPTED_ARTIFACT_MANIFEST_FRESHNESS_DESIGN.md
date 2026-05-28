# Fundamental Accepted Artifact Manifest + Freshness Model Design

Date: 2026-05-28

Stage: Fundamental Skill Accepted Artifact Manifest + Freshness Model Design.

Status: design accepted, accepted manifest module accepted, manifest-first
locator hardening accepted, runtime-aware test boundary accepted, retained
runtime manifest review accepted, and manifest locator runtime baseline frozen
for `600406`, `002371`, and `002050`. This documentation sync does not
implement code, change tests, change fixtures, change pipeline behavior, change
scoring / readiness, change Research Intelligence P1.1, change regression
expected files, generate output, write runtime artifacts, run smoke tests, read
`TUSHARE_TOKEN`, use the network, call Tushare or AkShare, connect MCP, or
provide investment advice.

Latest accepted verification results are quoted, not rerun here:

- targeted tests with retained manifest `251 passed`
- full pytest with retained manifest `899 passed, 1 skipped`
- regression `passed=47 failed=0 total=47`

Manifest locator runtime acceptance closeout is recorded in
`docs/FUNDAMENTAL_ACCEPTED_MANIFEST_LOCATOR_RUNTIME_ACCEPTANCE_SUMMARY.md`.
Minimal CNInfo / official disclosure parser design is recorded in
`docs/FUNDAMENTAL_MINIMAL_CNINFO_OFFICIAL_DISCLOSURE_PARSER_DESIGN.md`.
The retained ignored runtime manifest is
`output/research_reports/accepted_manifest.json` with SHA256
`C1F97162A59DE113CD4C9F1A9531AEC3A915A3D6F09365098201234E6F5BEB7F`, size
`7678`, and mtime UTC `2026-05-28 10:17:55`.

## 1. Design Goal

The accepted artifact manifest is the future primary source of truth for
locating user-facing Research Report V1 artifacts. It exists to remove the
current risk that a locator chooses a stale or superseded runtime artifact only
because it has the latest timestamp.

Required design properties:

- The accepted manifest is the locator's preferred truth source.
- User-facing artifact selection must no longer rely only on timestamp latest.
- The manifest records the currently accepted HTML, Markdown, and JSON artifacts
  for each stock.
- The manifest records superseded artifacts and lineage.
- The manifest records freshness / staleness as first-class metadata.
- The manifest is not a fixture.
- The manifest does not promote any evidence label.
- The manifest does not change report conclusions.
- The manifest does not change scoring, P1.1, readiness, or regression
  expected files.
- The manifest does not call providers, use the network, or read tokens.

The manifest records acceptance and freshness. It is not a fact verifier, not a
CNInfo parser, not a validator, not a fixture promotion mechanism, and not a
report rewrite path.

## 2. Manifest Path Design

Two runtime path variants are available.

Option A, single repository-level runtime manifest:

```text
output/research_reports/accepted_manifest.json
```

Benefits:

- One file is simple for locator, CLI, batch, and dashboard reads.
- It can represent mixed timestamp bundles across HTML, Markdown, and JSON.
- It can record cross-stock lineage and manifest-level metadata.
- It is easy to hash, audit, and secret scan before write.

Costs:

- Concurrent writes need file-level locking in future implementation.
- The file can grow as accepted stocks increase.

Option B, per-code runtime manifests:

```text
output/research_reports/accepted_manifests/<code>.json
```

Benefits:

- Smaller files and less contention for future batch generation.
- Easier manual inspection for one stock.

Costs:

- Locator and dashboard must scan or fan out across many files.
- Manifest-level consistency is harder.
- Cross-stock acceptance snapshots need an additional index.

V1 recommendation: use the single repository-level runtime manifest at:

```text
output/research_reports/accepted_manifest.json
```

V1 can later add per-code materialized views only if batch/dashboard scale
requires them. The canonical accepted source should remain one manifest unless
a future design explicitly changes that decision.

Path and write boundaries:

- Runtime manifest stays under ignored `output/`.
- Runtime manifest must not enter git.
- Runtime manifest must not be written as a fixture.
- Runtime manifest must not be written as regression expected data.
- A sanitized example fixture may be designed later, but this stage does not
  create one.
- Manifest path handling must reject path traversal, absolute paths outside the
  repository, symlinks that escape the allowed output root, and malformed stock
  codes.
- Future writer must secret scan the full manifest payload before writing.

## 3. Manifest Schema

Top-level schema:

```json
{
  "version": "accepted_artifact_manifest.v1",
  "created_at": "2026-05-28T00:00:00+08:00",
  "updated_at": "2026-05-28T00:00:00+08:00",
  "manifest_scope": "research_report_v1",
  "entries": []
}
```

Entry schema:

```json
{
  "code": "002371",
  "company_name": "北方华创",
  "report_type": "fundamental_research_report_v1",
  "presentation_profile": "semiconductor_equipment_cycle",
  "accepted_artifacts": {
    "html": "output/research_reports/20260528T125518/002371/fundamental_research_report_v1.html",
    "markdown": "output/research_reports/20260528T125518/002371/fundamental_research_report_v1.md",
    "json": "output/research_reports/20260527T220148/002371/fundamental_research_report_v1.json"
  },
  "artifact_hashes": {
    "html_sha256": "...",
    "markdown_sha256": "...",
    "json_sha256": "..."
  },
  "acceptance": {
    "accepted_at": "2026-05-28T12:55:18+08:00",
    "accepted_stage": "cli_runtime_acceptance",
    "accepted_by": "human_or_codex_review",
    "acceptance_notes": []
  },
  "freshness": {
    "freshness_status": "current",
    "source_data_period": "...",
    "financial_report_period": "...",
    "valuation_as_of_date": "...",
    "report_generated_at": "...",
    "accepted_at": "2026-05-28T12:55:18+08:00",
    "valid_until": "...",
    "last_freshness_check_at": "...",
    "freshness_reason": "...",
    "staleness_triggers": [],
    "manual_override": null
  },
  "lineage": {
    "supersedes": [],
    "superseded_by": null,
    "source_artifacts": []
  },
  "safety": {
    "not_for_trading_advice": true,
    "no_token": true,
    "no_provider_call": true
  }
}
```

The schema intentionally supports mixed timestamp accepted bundles. HTML and
Markdown may be regenerated from an older accepted JSON artifact without
requiring JSON regeneration.

`lineage.supersedes` should store superseded artifact records, not only opaque
strings. Each future record should include artifact type, path, sha256 when
available, superseded reason, superseded at, and replacement path. This is what
allows the manifest to remember old user-facing artifacts without treating them
as the accepted baseline.

## 4. Freshness Status Model

| status | Meaning | Locator default use | CLI warning | HTML generation | Must stop | Manual confirmation |
| --- | --- | --- | --- | --- | --- | --- |
| `current` | Freshness metadata says the accepted artifact is suitable for default user-facing reuse. | Yes. | No warning required. | Allowed when local inputs exist. | No. | No. |
| `unknown` | Freshness metadata is absent, incomplete, or not recently checked. | Yes, with warning. | Required. | Allowed, but warning must be preserved. | No. | Recommended for acceptance updates. |
| `stale` | A known trigger or age rule says the artifact may be outdated. The report may still be accepted, but must not be returned silently. | Yes in V1 with warning; future policy may fail closed. | Required and explicit. | Allowed only if the output carries the stale warning. | No in V1. | Recommended. |
| `superseded` | A newer accepted artifact replaced this artifact for user-facing baseline use. | No. | Required if referenced. | Not as accepted baseline. | No, unless requested as accepted. | Required to restore. |
| `invalidated` | Artifact failed an acceptance, safety, hash, lineage, or material correctness check. | No. | Required if referenced. | No accepted HTML output. | Yes. | Required to unblock. |

Freshness is separate from correctness. A stale report is not automatically
wrong; it is a report that should not be used without a visible warning.

## 5. Freshness Metadata

Each accepted entry must model:

- `source_data_period`
- `financial_report_period`
- `valuation_as_of_date`
- `report_generated_at`
- `accepted_at`
- `valid_until`
- `last_freshness_check_at`
- `freshness_status`
- `freshness_reason`
- `staleness_triggers`
- `manual_override`

Rules:

- `valuation_as_of_date` must not be hidden when it differs from report date or
  report generation time.
- Old financial report periods must be disclosed.
- An artifact can remain accepted while its freshness status becomes `stale`.
- `stale` does not mean the report is wrong. It means the report should not be
  used silently as a fresh baseline.
- `manual_override` must include actor, timestamp, reason, previous status, new
  status, and expiry if it is ever used.

## 6. A-share Staleness Triggers

V1 offline manifest can record and manually annotate triggers. It must not
network-check them.

Core A-share triggers:

- annual report
- semiannual report
- quarterly report
- earnings preannouncement
- earnings flash
- management guidance
- major contract / order announcement
- significant business change
- major asset restructuring
- M&A
- equity incentive
- shareholder reduction
- controlling shareholder change
- share pledge risk
- regulatory inquiry
- regulatory penalty
- related-party transaction
- litigation / arbitration
- accounting policy change
- auditor opinion change
- industry policy shock
- stock suspension / resumption
- provider data refresh
- official disclosure parser update

Future automatic detection requires official disclosure sources for most
issuer-specific events. Annual, semiannual, quarterly reports, earnings
preannouncements, earnings flashes, major contracts, restructurings, M&A,
equity incentives, shareholder changes, share pledges, regulatory inquiries,
penalties, related-party transactions, litigation, accounting policy changes,
auditor opinion changes, and suspension / resumption should be detected by a
future CNInfo / official disclosure parser. Provider data refresh can be
detected by future provider artifact metadata. Official parser updates can be
detected by parser version metadata. V1 does not perform any of those checks.

## 7. Locator Behavior

Accepted locator rules:

1. Read the accepted manifest first.
2. If a manifest entry exists and `freshness_status=current`, use the manifest
   artifact.
3. If `freshness_status=unknown`, use the manifest artifact but include a
   warning in the response.
4. If `freshness_status=stale`, return a visible warning by default; a future
   policy may fail closed.
5. If `freshness_status=superseded` or `invalidated`, do not use the artifact as
   a user-facing accepted baseline.
6. If the manifest is missing, fall back to the current timestamp locator only
   with `manifest_missing_warning`.
7. If a manifest path points to a missing file or the hash does not match, fail
   closed.
8. If the manifest conflicts with the latest timestamp artifact, the manifest
   wins, and the output includes a conflict warning.
9. If a user explicitly asks for the latest experimental artifact, it must be
   labelled as not the accepted baseline.

The timestamp locator becomes a fallback and diagnostic path, not the primary
accepted baseline selector.

## 8. CLI Behavior

Accepted CLI behavior:

- CLI locates accepted artifacts through the manifest first.
- CLI stdout displays freshness status.
- CLI stdout displays freshness warnings.
- CLI stdout must not hide `stale` or `unknown`.
- Missing manifest produces a warning.
- Stale artifact status does not automatically regenerate a report.
- CLI cannot check freshness through the network.
- CLI cannot read tokens.
- CLI cannot call providers.
- CLI cannot automatically upgrade to live provider mode.

Recommended stdout fields:

- `freshness_status`
- `freshness_warning`
- `accepted_at`
- `valuation_as_of_date`
- `source_data_period`

## 9. `002371` Superseded Case

The `002371` runtime incident is the concrete design motivation.

Superseded artifacts:

- old Markdown:
  `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md`
- old HTML:
  `output/research_reports/20260528T090024/002371/fundamental_research_report_v1.html`

New accepted presentation artifacts:

- new accepted Markdown:
  `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.md`
- new accepted HTML:
  `output/research_reports/20260528T125518/002371/fundamental_research_report_v1.html`

Accepted JSON remains:

- `output/research_reports/20260527T220148/002371/fundamental_research_report_v1.json`

Design implications:

- Old Markdown / HTML were superseded by professional-voice regenerated
  artifacts.
- Timestamp latest alone is not enough for accepted artifact selection.
- Accepted manifest prevents future wrong selection.
- JSON can remain older when the presentation artifacts were regenerated from
  it.
- Lineage must support mixed timestamp accepted bundles.

## 10. Relation To Evidence Tier / CNInfo

The freshness model is not official fact verification. It records freshness
metadata for accepted artifacts.

Relationship:

- CNInfo / official parser can later improve automatic staleness trigger
  detection.
- Official source integration can later support L1 evidence tier.
- Minimal CNInfo / official disclosure parser design is now documented in
  `docs/FUNDAMENTAL_MINIMAL_CNINFO_OFFICIAL_DISCLOSURE_PARSER_DESIGN.md`.
- The official parser may produce future `L1_official_disclosure` candidates
  with source document, source section, source page / anchor, parser
  confidence, and caveats.
- Current V1 manifest only records accepted artifacts and freshness metadata.
- Manifest is not a CNInfo parser.
- Manifest is not a validator.
- Manifest is not fixture promotion.
- Manifest does not upgrade evidence labels.
- Manifest / freshness status is not evidence tier.
- Official parser trigger discovery does not automatically make an accepted
  report stale; any manifest freshness update still requires accepted policy
  judgment.

## 11. Relation To Batch / Dashboard

Batch and dashboard should depend on the accepted manifest.

Design relationship:

- Batch should use manifest-located accepted artifacts for each stock.
- Dashboard should display freshness status by default.
- Dashboard may sort or filter by `freshness_status` and
  `research_completeness`.
- Dashboard must not rank stocks by buy / sell action.
- Dashboard must not sort by target price or implied upside.
- Manifest is prerequisite infrastructure for batch/dashboard, not a trading
  signal engine.

## 12. Relation To Live Tushare

Live Tushare provider mode remains later work. Manifest and freshness come
first.

Rules:

- Live provider mode is post-manifest work.
- Manifest/freshness hardening precedes live provider.
- New artifacts generated by a live provider must pass acceptance before the
  manifest is updated.
- Live provider output must not directly overwrite the accepted manifest.
- Token work, MCP work, and provider calls are not part of this stage.

## 13. Safety / Non-Goals

This stage must not:

- read `TUSHARE_TOKEN`;
- use the network;
- call Tushare;
- call AkShare;
- call any provider;
- connect MCP;
- write `output/`;
- submit runtime artifacts;
- write fixtures;
- change scoring, P1.1, readiness, or regression expected files;
- change evidence labels;
- output investment advice;
- implement live provider mode;
- implement a CNInfo parser;
- implement dashboard;
- implement batch.

## 14. Roadmap

Completed sequence:

1. Manifest + freshness design.
2. Manifest schema / writer / reader implementation.
3. Locator hardening: orchestration / CLI read manifest first.
4. `600406` / `002371` / `002050` manifest runtime generation.
5. Manifest locator runtime acceptance.

Next recommended sequence:

1. Submit the manifest locator runtime acceptance summary documentation patch.
2. Minimal CNInfo / official disclosure parser design.
3. Parser schema / local-file reader implementation.
4. One local downloaded filing sample for main-business and
   business-composition extraction.
5. Feed accepted official facts into candidate generator and evidence-tier
   handling through a separate design / acceptance cycle.
6. Start batch / dashboard design only after manifest closeout, and make it
   depend on manifest-located artifacts.
7. Keep live Tushare provider, live CNInfo fetch, token, MCP, and smoke work
   later.

## 15. Runtime acceptance summary addendum

The retained runtime manifest scenario is accepted. The real ignored manifest
remains at `output/research_reports/accepted_manifest.json`, is ignored by
`.gitignore`, is not tracked, is not staged, and `git ls-files output` remains
empty.

The manifest contains three current entries:

- `600406` / 国电南瑞.
- `002371` / 北方华创.
- `002050` / 三花智控.

Manifest validation passed through `read_accepted_manifest`,
`validate_accepted_manifest`, and `verify_manifest_entry_hashes`. All accepted
artifacts exist and all hashes match. The `002371` mixed timestamp bundle is
the accepted baseline: HTML / Markdown under `20260528T125518`, JSON under
`20260527T220148`, with old Markdown
`output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md`
and old HTML
`output/research_reports/20260528T090024/002371/fundamental_research_report_v1.html`
kept only as superseded lineage.

Runtime-aware tests no longer require the real manifest to be absent. When the
real manifest exists, tests assert that hash, mtime, and size remain unchanged;
when it is absent, tests assert that they do not create it. The tests write
only tmpdir and keep runtime output untracked.

## 16. Minimal CNInfo / Official Disclosure Parser Addendum

Minimal CNInfo / official disclosure parser design is recorded in
`docs/FUNDAMENTAL_MINIMAL_CNINFO_OFFICIAL_DISCLOSURE_PARSER_DESIGN.md`.

Design implications for the manifest / freshness model:

- Future official parser output is a runtime candidate artifact at
  `output/official_disclosures/<timestamp>/<code>/official_disclosure_facts.json`.
- The artifact may help identify annual, semiannual, quarterly, earnings
  preannouncement, earnings flash, management guidance, major contract,
  shareholder reduction, regulatory inquiry / penalty, and auditor-opinion
  triggers.
- Trigger discovery is not the same thing as an automatic stale decision.
- Official parser facts may become L1 evidence candidates only with source
  document, source location, confidence, and caveats.
- Official parser output must not directly update the accepted manifest.
- Official parser output must not write fixtures, change scoring / readiness,
  change P1.1, change regression expected files, change provider primary
  behavior, or merge provider data.

Next recommended step after this documentation patch is parser schema /
local-file reader implementation, still local-file first and still no live
CNInfo fetch unless a separate design / permission boundary is accepted.
