# HTML Report Visual Audit Tool Spec

Date: 2026-05-21

Stage: v1 implemented / baseline accepted

This document defines the project-specific visual audit tool for Fundamental HTML Report artifacts. v1 is implemented as a standalone script at `scripts/visual_audit_html_report.py` and the current baseline is accepted for the 002050 internal sample. Future visual-audit work must not modify renderer code, prompt builder code, report schema, report generation logic, deterministic pipeline, classifier, connector, dashboard, tests, regression expected files, or generated output artifacts unless a separate implementation stage explicitly asks for that.

## 1. Tool Positioning

`HTML Report Visual Audit Tool` is a visual acceptance helper for generated local HTML fundamental reports.

It exists because the current HTML Report v2.1 product acceptance flow can inspect DOM and CSS statically, but cannot reliably open and review the generated report visually when browser access is blocked by the client or local security policies.

The tool provides a stable local pipeline:

```text
local HTML report
-> Playwright Chromium opens the file
-> capture desktop first screen
-> capture mobile first screen
-> capture full page
-> write image artifacts and manifest
-> Codex reads screenshots and audits them against the frontend skill
```

This is a screenshot and visual audit tool, not a report renderer.

Current v1 status:

- Script path: `scripts/visual_audit_html_report.py`.
- Output directory pattern: `output/visual_audit/<code>/`.
- 002050 三花智控 visual audit has completed with no horizontal overflow on desktop or mobile.
- `output/visual_audit/` contains generated artifacts and must not be committed.

Allowed responsibilities:

- Open an existing local HTML report in a controlled Chromium session.
- Capture deterministic screenshots for desktop, mobile, and full-page review.
- Emit a manifest describing input, output, viewport, timing, and errors.
- Provide optional notes scaffolding for Codex visual review.
- Help Codex perform product-level visual acceptance from screenshots.

Explicit boundaries:

- It must not modify report HTML content.
- It must not generate a report.
- It must not call OpenAI APIs.
- It must not connect to a trading account.
- It must not output trading advice.
- It must not perform technical analysis.
- It must not change `html_report_renderer.py`.
- It must not change prompt builder behavior.

## 2. Technical Plan

v1 uses Python Playwright.

Setup commands when Playwright / Chromium is not already installed:

```bash
pip install playwright
python -m playwright install chromium
```

Script path:

```text
scripts/visual_audit_html_report.py
```

Rationale:

- Python matches the existing project toolchain.
- Playwright can open local `file://` URLs without relying on the Codex client browser.
- Chromium viewport emulation gives reproducible desktop and mobile screenshots.
- Request interception can prevent external network dependencies from making screenshot capture flaky.
- The script can be kept independent from renderer and report-generation modules.

The script is a standalone CLI utility. It should not import report renderer internals unless a future implementation has a very specific need, which v1 does not.

## 3. CLI Parameter Design

Command:

```bash
python scripts/visual_audit_html_report.py \
  --html output/reports/fundamental_report_002050.html \
  --code 002050 \
  --output-dir output/visual_audit/002050 \
  --desktop-width 1440 \
  --desktop-height 1000 \
  --mobile-width 390 \
  --mobile-height 844
```

Required parameters:

| Parameter | Meaning |
| --- | --- |
| `--html` | Path to the existing local HTML report. |
| `--code` | Stock code used for manifest metadata and default output naming. |
| `--output-dir` | Directory where screenshots and metadata are written. |

Viewport parameters:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `--desktop-width` | `1440` | Desktop viewport width. |
| `--desktop-height` | `1000` | Desktop first-screen viewport height. |
| `--mobile-width` | `390` | Mobile viewport width, aligned with common iPhone portrait review. |
| `--mobile-height` | `844` | Mobile first-screen viewport height. |

Optional parameters:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `--wait-ms` | `1500` | Extra wait after `domcontentloaded` or `networkidle` to let layout settle. |
| `--timeout-ms` | `30000` | Maximum page load and screenshot timeout. |
| `--block-external-network` | `true` | Abort non-local requests so external scripts, fonts, or pixels cannot fail the run. |
| `--notes` | `true` | Emit `visual_audit_notes.md` checklist scaffold. |
| `--overwrite` | `true` | Replace previous artifacts in the output directory. |

Path resolution rules:

- Resolve relative paths from the project root where the command is executed.
- Convert the HTML path to an absolute `file://` URL before opening.
- Fail early if `--html` does not exist or is not a file.
- Create `--output-dir` if missing.

## 4. Output File Design

Recommended output directory:

```text
output/visual_audit/002050/
```

Required files:

| File | Purpose |
| --- | --- |
| `desktop_first_screen.png` | Desktop viewport screenshot at `1440x1000` by default. |
| `mobile_first_screen.png` | Mobile viewport screenshot at `390x844` by default. |
| `full_page.png` | Full-page desktop screenshot for whole-report review. |
| `visual_audit_manifest.json` | Machine-readable run metadata, paths, viewport sizes, status, and errors. |

Optional file:

| File | Purpose |
| --- | --- |
| `visual_audit_notes.md` | Human/Codex checklist scaffold for visual acceptance notes. |

Suggested manifest shape:

```json
{
  "tool": "html_report_visual_audit",
  "version": "v1",
  "code": "002050",
  "html_path": "output/reports/fundamental_report_002050.html",
  "html_url": "file:///absolute/path/to/fundamental_report_002050.html",
  "output_dir": "output/visual_audit/002050",
  "created_at": "2026-05-21T00:00:00+08:00",
  "status": "success",
  "viewports": {
    "desktop": { "width": 1440, "height": 1000 },
    "mobile": { "width": 390, "height": 844 }
  },
  "screenshots": {
    "desktop_first_screen": "desktop_first_screen.png",
    "mobile_first_screen": "mobile_first_screen.png",
    "full_page": "full_page.png"
  },
  "network_policy": {
    "block_external_network": true,
    "blocked_request_count": 0
  },
  "page_metrics": {
    "desktop_scroll_width": 1440,
    "desktop_client_width": 1440,
    "mobile_scroll_width": 390,
    "mobile_client_width": 390,
    "full_page_height": 3600
  },
  "errors": []
}
```

If capture fails, the manifest should still be written when possible:

```json
{
  "status": "failed",
  "errors": [
    {
      "stage": "open_html",
      "message": "HTML file does not exist: output/reports/fundamental_report_002050.html"
    }
  ]
}
```

## 5. Screenshot Requirements

The implementation must capture:

- Desktop first-screen screenshot.
- Mobile first-screen screenshot.
- Desktop full-page screenshot.

Loading and stability requirements:

- Open the HTML through a `file://` URL.
- Wait for at least `domcontentloaded`.
- Prefer waiting for `networkidle` when it does not cause avoidable flakiness.
- Add a short configurable post-load wait, such as `--wait-ms 1500`, for fonts, layout, and theme scripts to settle.
- Use deterministic viewport sizes.
- Use `device_scale_factor=1` unless a future need for high-density output is explicit.

Network isolation requirements:

- The report should be self-contained, but v1 must tolerate unexpected external scripts, fonts, analytics, or image requests.
- Non-local `http://` and `https://` requests should be blocked by default.
- Blocking external requests must not fail the screenshot run.
- The manifest should count or list blocked external requests.
- Local `file://` resources, `data:` URLs, and `blob:` URLs should remain allowed.

Failure handling requirements:

- Missing HTML input should produce a clear error.
- Playwright/browser launch failure should produce a clear error suggesting the Chromium install command.
- Page load timeout should identify the stage and timeout value.
- Screenshot write failure should identify the output path.
- The process exit code should be non-zero on failure.

## 6. Visual Acceptance Dimensions

After screenshots are generated, Codex should read the images and audit them against `docs/skills/FUNDAMENTAL_HTML_REPORT_FRONTEND_SKILL.md`.

Core visual questions:

- Does it look like a professional Chinese fundamental research report?
- Is the Hero visually strong and immediately readable?
- Is the core conclusion prominent enough?
- Can the first screen explain the company's core fundamental thesis?
- Does the page feel overly templated or mechanically assembled?
- Is the visual hierarchy strong across Hero, conclusion, cards, tables, risks, and tracking sections?
- Is the dark research-report theme serious rather than marketing-like or trading-terminal-like?

Responsive and layout checks:

- No horizontal page overflow on desktop.
- No horizontal page overflow on mobile.
- Mobile title and Hero text are not clipped or unreadably compressed.
- Sticky navigation does not occlude key first-screen content.
- Tables scroll inside their own containers on small screens.
- Tables do not expand the whole page width.
- Badges, score bars, cards, and section headings fit their containers.
- Long Chinese text wraps naturally without breaking the composition.
- Full-page screenshot has no obvious blank sections, overlapping blocks, or broken CSS.

Content boundary checks visible from screenshots:

- No trading advice remains.
- No buy/sell language remains.
- No target price module remains.
- No position sizing, stop-loss, take-profit, or execution checklist remains.
- No K-line, moving average, volume chart, or technical-analysis module remains.
- Valuation content appears as fundamental explanation, not action guidance.
- Must-track indicators are framed as fundamental review variables, not trading triggers.

Chinese report quality checks:

- User-visible report layer text is Chinese.
- Section names are localized and research-oriented.
- Data quality, missing evidence, and inability-to-judge items are visible.
- Evidence confidence is framed as evidence coverage, not optimism.
- Safety boundary is visible in the report, especially near the end.

## 7. Out Of Scope

The implementation must not include:

- HTML renderer changes.
- Report generation.
- Prompt builder changes.
- Schema changes.
- OpenAI API integration.
- Trading account integration.
- Trading recommendations.
- Target prices.
- Position or execution advice.
- K-line or technical-analysis capture logic.
- A dashboard integration.
- Automatic repair of visual problems.

The tool may reveal renderer issues through screenshots, but it must not fix them directly.

## 8. v1 Implementation Scope

Implemented files:

```text
scripts/visual_audit_html_report.py
docs/HTML_REPORT_VISUAL_AUDIT_TOOL_SPEC.md
```

Implemented test coverage includes:

```text
tests/test_visual_audit_html_report.py
```

The v1 script:

- Parses the CLI arguments above.
- Validates the HTML input path.
- Creates the output directory.
- Launches Chromium through Playwright.
- Blocks external network requests by default.
- Opens the HTML as `file://`.
- Captures desktop first-screen, mobile first-screen, and desktop full-page screenshots.
- Collects basic page metrics such as `scrollWidth`, `clientWidth`, and full-page height.
- Writes `visual_audit_manifest.json`.
- Optionally writes `visual_audit_notes.md`.
- Returns a non-zero exit code on failure.

Test coverage:

- CLI argument parsing.
- Missing HTML path returns failure and writes/prints a clear error.
- Minimal local HTML produces the three screenshot files and manifest.
- Local HTML containing an external script still screenshots successfully with external requests blocked.
- Manifest includes viewport sizes, screenshot names, status, and page metrics.

Manual acceptance command:

```bash
python scripts/visual_audit_html_report.py \
  --html output/reports/fundamental_report_002050.html \
  --code 002050 \
  --output-dir output/visual_audit/002050
```

Manual acceptance artifacts:

```text
output/visual_audit/002050/desktop_first_screen.png
output/visual_audit/002050/mobile_first_screen.png
output/visual_audit/002050/full_page.png
output/visual_audit/002050/visual_audit_manifest.json
```

## 9. v1 Acceptance Criteria

Implementation baseline is accepted when:

- The tool runs from the project root with the recommended CLI command.
- It works on `output/reports/fundamental_report_002050.html` when that file exists.
- It writes all required screenshot files.
- It writes a manifest with success/failure status and useful diagnostics.
- It blocks external network requests without failing the capture.
- Desktop first-screen screenshot is exactly the requested desktop viewport size.
- Mobile first-screen screenshot is exactly the requested mobile viewport size.
- Full-page screenshot captures the full report height.
- Missing input and browser-install problems produce clear errors.
- The tool remains independent from renderer, prompt builder, report generation, OpenAI API calls, trading accounts, and technical-analysis logic.

Product acceptance is acceptable when Codex can then inspect the screenshots and answer the visual acceptance checklist in Section 6 with concrete observations.

Current accepted baseline:

- `002050` 三花智控 has completed visual audit against the generated HTML report.
- Desktop and mobile manifest metrics show no horizontal page overflow.
- Generated artifacts live under `output/visual_audit/002050/` and should remain out of git.

## 10. Recommendation

Use v1 as the baseline visual acceptance tool for local Fundamental HTML Report artifacts. Future report refinements should start from concrete user feedback or screenshot findings; the visual-audit tool itself should remain independent from renderer, prompt builder, schema, pipeline, dashboard, trading-account integration, and technical-analysis logic.
