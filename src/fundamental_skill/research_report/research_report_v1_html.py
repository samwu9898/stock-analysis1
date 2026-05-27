# -*- coding: utf-8 -*-
"""HTML presentation renderer for Research Report V1.

This module is display-only. It consumes accepted Markdown presentation output
and, optionally, a Research Report V1 structured payload for metadata,
evidence labels, caveats, and source references. It does not call data
providers, read environment variables, access network resources, or mutate the
input artifacts.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
from typing import Any

from .research_report_v1 import (
    ALLOWED_EVIDENCE_LABELS,
    ResearchReportArtifactBoundaryError,
    ResearchReportBuildError,
    _assert_no_secret_like_payload,
    _normalize_code,
)


HTML_OUTPUT_FILENAME = "fundamental_research_report_v1.html"

_TIMESTAMP_RE = re.compile(r"^[A-Za-z0-9T_-]{1,64}$")
_LOCAL_PATH_RE = re.compile(
    r"(?:\b[A-Za-z]:[\\/]+|(?:^|[\s\"'`=])/(?:Users|home|root|tmp|var|etc|mnt|opt)/)",
    flags=re.IGNORECASE,
)
_URL_RE = re.compile(r"\b(?:https?|ftp)://", flags=re.IGNORECASE)
_EXTERNAL_RESOURCE_RE = re.compile(
    r"<\s*(?:script|link|img|iframe|object|embed|source|video|audio)\b|"
    r"@import\b|url\s*\(",
    flags=re.IGNORECASE,
)
_RAW_HTML_RE = re.compile(r"<\s*/?\s*(?:script|img|iframe|object|embed|link|style|meta|html|body|head)\b", flags=re.IGNORECASE)

_TRADING_TERMS_CN = (
    "买入",
    "卖出",
    "持有建议",
    "目标价",
    "仓位",
    "加仓",
    "减仓",
    "止损",
    "技术面交易信号",
    "确定性上涨",
    "必然兑现",
    "强烈推荐",
)
_TRADING_PATTERNS_EN = tuple(
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in (
        r"\bbuy\b",
        r"\bsell\b",
        r"\bhold\s+recommendation\b",
        r"\btarget\s+price\b",
        r"\bposition\s+sizing\b",
        r"\bincrease\s+position\b",
        r"\breduce\s+position\b",
        r"\bstop\s+loss\b",
        r"\btechnical\s+trading\s+signal\b",
        r"\bcertain\s+upside\b",
        r"\binevitable\s+realization\b",
        r"\bstrong\s+recommend\b",
    )
)

_SECTION_ALIASES = {
    "statement": ("重要声明", "important statement", "not-for-trading"),
    "conclusion": ("一句话", "one-sentence", "conclusion"),
    "quick_read": ("投研速读", "quick read", "investment manager quick read"),
    "judgement": ("研究员判断", "analyst judgement"),
    "data_quality": ("数据质量", "data quality", "data-quality"),
    "macro_industry": ("宏观与行业", "macro", "industry logic"),
    "company": ("公司基本面", "company fundamentals"),
    "opportunity": ("机会分析", "opportunity"),
    "risk": ("风险分析", "risk"),
    "evidence_gap": ("证据缺口", "evidence gap"),
    "rebuttal": ("反证条件", "rebuttal", "bear case"),
    "follow_up": ("后续跟踪", "follow-up", "tracking checklist"),
}

_APPENDIX_PROFILE_KEYS = (
    "presentation_profile_id",
    "presentation_profile_selected_by",
    "fallback_reason",
    "profile_selection_warning",
    "profile_id",
)

_SKIP_RECURSIVE_KEYS = {
    "raw",
    "raw_payload",
    "raw_dump",
    "provider_raw",
    "provider_raw_dump",
    "raw_provider_artifacts",
    "raw_provider_payload",
}

_EVIDENCE_LABEL_DESCRIPTIONS = {
    "verified_fact": "Reviewed source or fixture-backed fact already accepted by the report.",
    "auto_accepted_candidate": "Candidate-level evidence; not a reviewed fact.",
    "manual_review_required": "Visible review caveat that still limits conclusion strength.",
    "unsupported_assumption": "Hypothesis or assumption that remains to be verified.",
    "coverage_caveat": "Coverage, source, freshness, or data-quality limitation.",
    "forward_tracking_variable": "Monitoring item; not proof of current realization.",
}


def render_research_report_v1_html(markdown: str, report: dict[str, Any] | None = None) -> str:
    """Render accepted Research Report V1 Markdown as self-contained HTML."""

    if not isinstance(markdown, str) or not markdown.strip():
        raise ResearchReportBuildError("markdown must be a non-empty string")
    if report is not None and not isinstance(report, dict):
        raise ResearchReportBuildError("report must be a dict when provided")

    _assert_no_secret_like_payload(markdown)
    _assert_no_local_path_like_payload(markdown)
    _assert_no_forbidden_trading_terms(markdown)
    _assert_no_dangerous_raw_html(markdown)
    if report is not None:
        _assert_no_secret_like_payload(report)
        _assert_no_local_path_like_payload(report)
        _assert_no_forbidden_trading_terms(report)

    parsed = _parse_markdown(markdown)
    title = parsed.title or _title_from_report(report) or "Research Report V1"
    quick = _build_quick_read(parsed)
    metadata = _metadata_from_report_and_markdown(report, markdown)
    evidence_labels = _collect_evidence_labels(report)
    caveats = _collect_caveats(report)
    source_refs = _source_refs(report)

    html = "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<meta name="referrer" content="no-referrer">',
            f"<title>{escape(title)}</title>",
            "<style>",
            _self_contained_css(),
            "</style>",
            "</head>",
            "<body>",
            '<main class="report-shell">',
            _render_header(title),
            _render_quick_read(quick),
            _render_research_body(markdown),
            _render_technical_appendix(metadata, evidence_labels, caveats, source_refs),
            "</main>",
            "</body>",
            "</html>",
        ]
    )
    _assert_no_secret_like_payload(html)
    _assert_no_local_path_like_payload(html)
    _assert_no_forbidden_trading_terms(html)
    _assert_html_has_no_external_resources(html)
    return html


def write_research_report_v1_html(
    html: str,
    output_root: Path,
    timestamp: str,
    code: str,
) -> Path:
    """Write a rendered HTML report under an explicit artifact root."""

    if not isinstance(html, str) or not html.strip():
        raise ResearchReportBuildError("html must be a non-empty string")

    normalized_code = _normalize_code(str(code))
    timestamp_text = str(timestamp)
    if not _TIMESTAMP_RE.fullmatch(timestamp_text) or ".." in timestamp_text:
        raise ResearchReportArtifactBoundaryError("timestamp contains unsupported path characters")

    _assert_no_secret_like_payload(html)
    _assert_no_local_path_like_payload(html)
    _assert_no_forbidden_trading_terms(html)
    _assert_html_has_no_external_resources(html)

    root = Path(output_root)
    root_resolved = root.resolve(strict=False)
    report_path = root / timestamp_text / normalized_code / HTML_OUTPUT_FILENAME
    report_resolved = report_path.resolve(strict=False)
    try:
        report_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ResearchReportArtifactBoundaryError("html report path escapes output root") from exc
    if report_resolved.name != HTML_OUTPUT_FILENAME or report_resolved.suffix != ".html":
        raise ResearchReportArtifactBoundaryError("writer may only write fundamental_research_report_v1.html")

    report_resolved.parent.mkdir(parents=True, exist_ok=True)
    report_resolved.write_text(html, encoding="utf-8")
    return report_resolved


class _ParsedMarkdown:
    def __init__(self, title: str | None, sections: list[tuple[str, list[str]]]) -> None:
        self.title = title
        self.sections = sections

    def section(self, logical_name: str) -> list[str]:
        aliases = _SECTION_ALIASES[logical_name]
        for heading, lines in self.sections:
            normalized = heading.lower()
            if any(alias.lower() in normalized for alias in aliases):
                return lines
        return []


def _parse_markdown(markdown: str) -> _ParsedMarkdown:
    title: str | None = None
    sections: list[tuple[str, list[str]]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            if title is None:
                title = stripped[2:].strip()
            continue
        if stripped.startswith("## "):
            if current_heading is not None:
                sections.append((current_heading, current_lines))
            current_heading = stripped[3:].strip()
            current_lines = []
            continue
        if current_heading is not None:
            current_lines.append(line)
    if current_heading is not None:
        sections.append((current_heading, current_lines))
    return _ParsedMarkdown(title, sections)


def _build_quick_read(parsed: _ParsedMarkdown) -> dict[str, list[str]]:
    return {
        "statement": _first_content_lines(parsed.section("statement"), limit=2),
        "conclusion": _first_content_lines(parsed.section("conclusion"), limit=1),
        "opportunity": _first_content_lines(parsed.section("opportunity") or parsed.section("quick_read"), limit=3),
        "risk": _first_content_lines(parsed.section("risk"), limit=3),
        "evidence_gap": _first_content_lines(parsed.section("evidence_gap"), limit=3),
        "data_quality": _first_content_lines(parsed.section("data_quality"), limit=3),
        "follow_up": _first_content_lines(parsed.section("follow_up"), limit=6),
    }


def _first_content_lines(lines: list[str], *, limit: int) -> list[str]:
    cleaned: list[str] = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        cleaned.append(_strip_markdown_marker(text))
        if len(cleaned) >= limit:
            break
    return cleaned


def _strip_markdown_marker(text: str) -> str:
    if text.startswith("- [ ] "):
        return text[6:].strip()
    if text.startswith("- [x] ") or text.startswith("- [X] "):
        return text[6:].strip()
    if text.startswith("- "):
        return text[2:].strip()
    return text


def _render_header(title: str) -> str:
    return "\n".join(
        [
            '<header class="report-header">',
            '<p class="eyebrow">Research Report V1 HTML Presentation</p>',
            f"<h1>{escape(title)}</h1>",
            '<p class="notice" data-flag="not_for_trading_advice">'
            "not_for_trading_advice=true · 本报告仅用于基本面研究展示，不构成账户操作或价格判断依据。"
            "</p>",
            "</header>",
        ]
    )


def _render_quick_read(quick: dict[str, list[str]]) -> str:
    cards = (
        ("一句话结论", quick["conclusion"], "summary"),
        ("核心机会", quick["opportunity"], "opportunity"),
        ("核心风险", quick["risk"], "risk"),
        ("最大证据缺口", quick["evidence_gap"], "gap"),
        ("数据质量状态", quick["data_quality"], "quality"),
    )
    card_html = "\n".join(_render_card(title, items, modifier) for title, items, modifier in cards)
    follow_up_items = quick["follow_up"] or ["见 Research Body 中的后续跟踪清单。"]
    return "\n".join(
        [
            '<section id="quick-read" class="quick-read" aria-labelledby="quick-read-title">',
            '<div class="section-heading">',
            '<p class="eyebrow">Investment Manager Quick Read</p>',
            '<h2 id="quick-read-title">投资经理速读区</h2>',
            "</div>",
            '<div class="quick-grid">',
            card_html,
            "</div>",
            '<div class="follow-up-panel" aria-label="后续跟踪清单摘要">',
            "<h3>后续跟踪清单</h3>",
            _render_checklist(follow_up_items),
            "</div>",
            "</section>",
        ]
    )


def _render_card(title: str, items: list[str], modifier: str) -> str:
    body = items or ["见 Research Body 原文。"]
    return "\n".join(
        [
            f'<article class="quick-card quick-card--{escape(modifier, quote=True)}">',
            f"<h3>{escape(title)}</h3>",
            _render_list(body),
            "</article>",
        ]
    )


def _render_research_body(markdown: str) -> str:
    return "\n".join(
        [
            '<section id="research-body" class="research-body" aria-labelledby="research-body-title">',
            '<div class="section-heading">',
            '<p class="eyebrow">Research Body</p>',
            '<h2 id="research-body-title">研究主体区</h2>',
            "</div>",
            '<article class="markdown-body">',
            _markdown_to_html(markdown),
            "</article>",
            "</section>",
        ]
    )


def _render_technical_appendix(
    metadata: list[tuple[str, str]],
    evidence_labels: list[str],
    caveats: list[str],
    source_refs: list[tuple[str, str]],
) -> str:
    metadata_html = _render_metadata(metadata)
    evidence_html = _render_evidence_labels(evidence_labels)
    source_html = _render_source_refs(source_refs)
    caveat_count = len(caveats)
    caveat_items = caveats or ["No structured data-quality caveat supplied; see Research Body for Markdown caveats."]
    return "\n".join(
        [
            '<section id="technical-appendix" class="technical-appendix" aria-labelledby="technical-appendix-title">',
            '<div class="section-heading">',
            '<p class="eyebrow">Technical Appendix</p>',
            '<h2 id="technical-appendix-title">技术附注区</h2>',
            "</div>",
            '<div class="appendix-grid">',
            '<article class="appendix-card">',
            "<h3>presentation profile metadata</h3>",
            metadata_html,
            "</article>",
            '<article class="appendix-card">',
            "<h3>evidence label definitions</h3>",
            evidence_html,
            "</article>",
            '<article class="appendix-card">',
            "<h3>source artifact refs</h3>",
            source_html,
            "</article>",
            '<article class="appendix-card">',
            "<h3>not_for_trading_advice flag</h3>",
            '<p><code>not_for_trading_advice=true</code></p>',
            "</article>",
            "</div>",
            '<details class="caveat-details" open>',
            f"<summary>data-quality caveats visible: {caveat_count}</summary>",
            _render_list(caveat_items),
            "</details>",
            '<div class="boundary-note">',
            "<h3>Evidence Boundary</h3>",
            _render_list(
                [
                    "candidate is not verified fact",
                    "review decision is not fixture promotion",
                    "P1.1 proxy is not operating fact",
                    "industry narrative is not company realization",
                    "unsupported assumption remains to be verified",
                    "forward tracking variable remains a monitoring item",
                ]
            ),
            "</div>",
            "</section>",
        ]
    )


def _markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    list_items: list[str] = []

    def flush_list() -> None:
        if list_items:
            output.append("<ul>")
            output.extend(list_items)
            output.append("</ul>")
            list_items.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_list()
            continue
        if stripped.startswith("### "):
            flush_list()
            output.append(f"<h4>{_inline_markdown(stripped[4:].strip())}</h4>")
            continue
        if stripped.startswith("## "):
            flush_list()
            output.append(f"<h3>{_inline_markdown(stripped[3:].strip())}</h3>")
            continue
        if stripped.startswith("# "):
            flush_list()
            output.append(f"<h2>{_inline_markdown(stripped[2:].strip())}</h2>")
            continue
        if stripped.startswith("- [ ] ") or stripped.startswith("- [x] ") or stripped.startswith("- [X] "):
            checked = " checked" if stripped[3:4].lower() == "x" else ""
            item = stripped[6:].strip()
            list_items.append(
                f'<li class="check-item"><input type="checkbox" disabled{checked}>'
                f"<span>{_inline_markdown(item)}</span></li>"
            )
            continue
        if stripped.startswith("- "):
            list_items.append(f"<li>{_inline_markdown(stripped[2:].strip())}</li>")
            continue
        flush_list()
        output.append(f"<p>{_inline_markdown(stripped)}</p>")
    flush_list()
    return "\n".join(output)


def _inline_markdown(text: str) -> str:
    escaped = escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def _render_list(items: list[str]) -> str:
    if not items:
        return "<p>None supplied.</p>"
    return "<ul>" + "".join(f"<li>{_inline_markdown(str(item))}</li>" for item in items) + "</ul>"


def _render_checklist(items: list[str]) -> str:
    return (
        '<ul class="checklist">'
        + "".join(
            '<li><input type="checkbox" disabled><span>'
            + _inline_markdown(str(item))
            + "</span></li>"
            for item in items
        )
        + "</ul>"
    )


def _render_metadata(metadata: list[tuple[str, str]]) -> str:
    if not metadata:
        return "<p>neutral display shell; profile metadata not supplied.</p>"
    return (
        "<dl>"
        + "".join(f"<dt>{escape(key)}</dt><dd>{escape(value)}</dd>" for key, value in metadata)
        + "</dl>"
    )


def _render_evidence_labels(labels: list[str]) -> str:
    active = labels or ["coverage_caveat"]
    badges = "".join(_evidence_badge(label) for label in active)
    definitions = "".join(
        "<li>"
        + _evidence_badge(label)
        + f"<span>{escape(_EVIDENCE_LABEL_DESCRIPTIONS[label])}</span>"
        + "</li>"
        for label in sorted(ALLOWED_EVIDENCE_LABELS)
    )
    return f'<div class="badge-row">{badges}</div><ul class="definition-list">{definitions}</ul>'


def _evidence_badge(label: str) -> str:
    safe_label = escape(label)
    safe_class = re.sub(r"[^A-Za-z0-9_-]+", "-", label)
    return f'<span class="evidence-badge evidence-badge--{safe_class}" data-evidence-label="{safe_label}">{safe_label}</span>'


def _render_source_refs(refs: list[tuple[str, str]]) -> str:
    if not refs:
        return "<p>No structured source refs supplied; see Markdown body.</p>"
    return (
        "<dl>"
        + "".join(f"<dt>{escape(key)}</dt><dd>{escape(value)}</dd>" for key, value in refs)
        + "</dl>"
    )


def _metadata_from_report_and_markdown(report: dict[str, Any] | None, markdown: str) -> list[tuple[str, str]]:
    metadata: list[tuple[str, str]] = []
    if report:
        presentation = report.get("presentation_profile") or report.get("presentation_profile_metadata") or {}
        if isinstance(presentation, dict):
            for key in _APPENDIX_PROFILE_KEYS:
                if presentation.get(key) not in (None, "", [], {}):
                    metadata.append((key, str(presentation[key])))
        for key in _APPENDIX_PROFILE_KEYS:
            if report.get(key) not in (None, "", [], {}):
                metadata.append((key, str(report[key])))
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:]
        if ":" not in body:
            continue
        key, value = body.split(":", 1)
        key = key.strip()
        if key in _APPENDIX_PROFILE_KEYS:
            metadata.append((key, value.strip().strip("`")))
    return _dedupe_pairs(metadata)


def _source_refs(report: dict[str, Any] | None) -> list[tuple[str, str]]:
    refs = _dict_or_empty(report.get("source_artifact_refs") if report else None)
    output: list[tuple[str, str]] = []
    for key, value in refs.items():
        for item in _as_list(value):
            output.append((str(key), _sanitize_source_ref(str(item))))
    return _dedupe_pairs(output)


def _sanitize_source_ref(value: str) -> str:
    text = value.strip()
    if _LOCAL_PATH_RE.search(text) or re.match(r"^[A-Za-z]:[\\/]", text):
        return "[local_path_removed]"
    if text.startswith(("/", "\\")):
        return "[absolute_path_removed]"
    if _URL_RE.search(text):
        return "[external_url_removed]"
    return text.replace("\\", "/")


def _collect_evidence_labels(report: dict[str, Any] | None) -> list[str]:
    labels: list[str] = []
    for _, key, value in _walk_report_values(report):
        if key == "evidence_label" and isinstance(value, str):
            labels.append(value)
    allowed_ordered = [label for label in labels if label in ALLOWED_EVIDENCE_LABELS]
    return _dedupe_list(allowed_ordered)


def _collect_caveats(report: dict[str, Any] | None) -> list[str]:
    caveats: list[str] = []
    for _, key, value in _walk_report_values(report):
        if key == "caveat" and isinstance(value, str) and value.strip():
            caveats.append(value.strip())
        elif key == "caveats":
            caveats.extend(str(item).strip() for item in _as_list(value) if str(item).strip())
    return _dedupe_list(caveats)[:40]


def _walk_report_values(value: Any, parent_key: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.lower()
            if normalized in _SKIP_RECURSIVE_KEYS or "raw_dump" in normalized or "raw_provider" in normalized:
                continue
            yield value, key_text, child
            yield from _walk_report_values(child, key_text)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_report_values(child, parent_key)


def _title_from_report(report: dict[str, Any] | None) -> str | None:
    if not report:
        return None
    code = str(report.get("code") or "").strip()
    stock = _dict_or_empty(_dict_or_empty(report.get("company_fundamentals")).get("stock"))
    company_name = str(stock.get("stock_name") or "").strip()
    if code and company_name:
        return f"{code} {company_name} 基本面研究报告 V1"
    if code:
        return f"{code} 基本面研究报告 V1"
    return None


def _assert_no_forbidden_trading_terms(value: Any) -> None:
    text = _stringify_for_scan(value)
    for term in _TRADING_TERMS_CN:
        if term in text:
            raise ResearchReportBuildError("rendered HTML contains prohibited investment-action language")
    for pattern in _TRADING_PATTERNS_EN:
        if pattern.search(text):
            raise ResearchReportBuildError("rendered HTML contains prohibited investment-action language")


def _assert_no_local_path_like_payload(value: Any) -> None:
    text = _stringify_for_scan(value)
    if _LOCAL_PATH_RE.search(text):
        raise ResearchReportSecretError("research report HTML contains local path-like data: <masked>")


def _assert_no_dangerous_raw_html(markdown: str) -> None:
    if _RAW_HTML_RE.search(markdown):
        return


def _assert_html_has_no_external_resources(html: str) -> None:
    if _URL_RE.search(html):
        raise ResearchReportBuildError("HTML must not contain external URLs")
    html_without_safe_style = re.sub(r"<style>.*?</style>", "", html, flags=re.IGNORECASE | re.DOTALL)
    if _EXTERNAL_RESOURCE_RE.search(html_without_safe_style):
        raise ResearchReportBuildError("HTML must not load external resources")


def _stringify_for_scan(value: Any) -> str:
    if isinstance(value, dict):
        return "\n".join(f"{key}\n{_stringify_for_scan(child)}" for key, child in value.items())
    if isinstance(value, list):
        return "\n".join(_stringify_for_scan(child) for child in value)
    return "" if value is None else str(value)


def _dedupe_pairs(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    output: list[tuple[str, str]] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _dedupe_list(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, "", {}, ()):
        return []
    return [value]


def _self_contained_css() -> str:
    return """
:root {
  color-scheme: light;
  --bg: #f6f7f9;
  --panel: #ffffff;
  --ink: #1f2933;
  --muted: #667085;
  --line: #d9dee7;
  --accent: #365a8c;
  --accent-soft: #e7eef8;
  --risk-soft: #f3e9e5;
  --gap-soft: #f3f0df;
  --quality-soft: #e8f1ec;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", sans-serif;
  line-height: 1.62;
}
.report-shell {
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 24px 56px;
}
.report-header,
.quick-read,
.research-body,
.technical-appendix {
  margin-bottom: 24px;
}
.report-header {
  padding: 30px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.report-header h1 {
  margin: 6px 0 14px;
  font-size: 30px;
  line-height: 1.24;
}
.eyebrow {
  margin: 0 0 6px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0;
}
.notice {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fafbfc;
  color: var(--muted);
}
.section-heading {
  margin-bottom: 12px;
}
.section-heading h2 {
  margin: 0;
  font-size: 22px;
}
.quick-grid,
.appendix-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}
.quick-card,
.appendix-card,
.follow-up-panel,
.markdown-body,
.caveat-details,
.boundary-note {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
}
.quick-card h3,
.appendix-card h3,
.follow-up-panel h3,
.boundary-note h3 {
  margin: 0 0 10px;
  font-size: 16px;
}
.quick-card--summary { border-top: 4px solid var(--accent); }
.quick-card--opportunity { background: var(--accent-soft); }
.quick-card--risk { background: var(--risk-soft); }
.quick-card--gap { background: var(--gap-soft); }
.quick-card--quality { background: var(--quality-soft); }
ul {
  margin: 0;
  padding-left: 20px;
}
li + li { margin-top: 6px; }
.follow-up-panel { margin-top: 12px; }
.checklist,
.markdown-body ul {
  list-style: none;
  padding-left: 0;
}
.checklist li,
.check-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
input[type="checkbox"] {
  margin-top: 6px;
  accent-color: var(--accent);
}
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin: 18px 0 8px;
}
.markdown-body p {
  margin: 8px 0;
}
.evidence-badge {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  margin: 0 6px 6px 0;
  padding: 2px 8px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #f9fafb;
  font-size: 12px;
  color: #344054;
}
.definition-list {
  list-style: none;
  padding-left: 0;
}
.definition-list li {
  margin-top: 8px;
}
dl {
  display: grid;
  grid-template-columns: minmax(120px, 0.45fr) 1fr;
  gap: 6px 10px;
  margin: 0;
}
dt {
  color: var(--muted);
  font-weight: 700;
}
dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.caveat-details {
  margin-top: 12px;
}
.caveat-details summary {
  cursor: default;
  font-weight: 700;
}
.boundary-note {
  margin-top: 12px;
}
code {
  padding: 1px 5px;
  border-radius: 4px;
  background: #eef2f6;
}
@media (max-width: 720px) {
  .report-shell { padding: 20px 14px 40px; }
  .report-header { padding: 20px; }
  .report-header h1 { font-size: 24px; }
  dl { grid-template-columns: 1fr; }
}
""".strip()
