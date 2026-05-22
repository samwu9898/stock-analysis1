# -*- coding: utf-8 -*-
"""Render Fundamental HTML Report JSON to a self-contained Chinese HTML file."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .html_report_schema import validate_fundamental_html_report


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT_DIR = PROJECT_ROOT / "output" / "reports"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _e(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, default=str)
    return html.escape(str(value), quote=True)


def _display(value: Any) -> str:
    if isinstance(value, dict):
        if value.get("display_value") not in (None, ""):
            return str(value.get("display_value"))
        if value.get("raw_value") not in (None, ""):
            return str(value.get("raw_value"))
    return "-" if value in (None, "") else str(value)


def _badge(text: Any, kind: str = "neutral") -> str:
    return f'<span class="badge badge-{kind}">{_e(text)}</span>'


def _list(items: Any) -> str:
    rows = [f"<li>{_e(item)}</li>" for item in _as_list(items) if item not in (None, "")]
    return "<ul>" + "".join(rows or ["<li>-</li>"]) + "</ul>"


def _table(rows: Any) -> str:
    rows = [row for row in _as_list(rows) if isinstance(row, dict)]
    if not rows:
        return '<p class="muted">暂无可展示的结构化表格数据。</p>'
    headers: list[str] = []
    for row in rows:
        for key in row:
            if key not in headers:
                headers.append(str(key))
    head = "".join(f"<th>{_e(key)}</th>" for key in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{_e(_display(row.get(key)))}</td>" for key in headers)
        body_rows.append(f"<tr>{cells}</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


def _risk_list(title: str, items: Any, kind: str) -> str:
    rows = [f'<div class="risk-line"><span>{_e(item)}</span>{_badge(kind, "risk")}</div>' for item in _as_list(items)]
    body = "".join(rows) if rows else '<p class="muted">暂无明确披露。</p>'
    return f'<div class="risk-card"><h3>{_e(title)}</h3>{body}</div>'


def _section(section_id: str, title: str, body: str) -> str:
    return f'<section id="{section_id}" class="card"><h2>{_e(title)}</h2>{body}</section>'


def _scenario_card(scenario: dict[str, Any], tone: str) -> str:
    return f"""
    <article class="scenario scenario-{tone}">
      <h3>{_e(scenario.get("scenario_name"))}</h3>
      <p>{_e(scenario.get("impact_on_fundamentals"))}</p>
      <h4>核心假设</h4>{_list(scenario.get("fundamental_assumptions"))}
      <h4>关键变量</h4>{_list(scenario.get("key_variables"))}
      <div class="scenario-foot">{_badge("证据强度：" + str(scenario.get("evidence_strength") or "-"), tone)}</div>
    </article>
    """


def _tags(items: Any) -> str:
    tags = [_e(item) for item in _as_list(items) if item not in (None, "")]
    return '<div class="tag-row">' + "".join(f'<span class="hero-tag">{tag}</span>' for tag in tags) + "</div>" if tags else ""


def _score_percent(score: Any, max_score: Any) -> int:
    try:
        score_value = float(score)
        max_value = float(max_score or 10)
    except (TypeError, ValueError):
        return 0
    if max_value <= 0:
        return 0
    return max(0, min(100, int(score_value / max_value * 100)))


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _pressure_tone(text: Any) -> str:
    normalized = str(text or "").lower()
    if any(token in normalized for token in ("承压", "偏高", "为负", "下降", "下滑", "缺失", "missing", "weak", "low")):
        return "high"
    if any(token in normalized for token in ("待验证", "复核", "一般", "中等", "medium", "partial")):
        return "medium"
    if any(token in normalized for token in ("健康", "改善", "稳定", "充足", "strong", "high")):
        return "low"
    return "medium"


def _pressure_label(tone: str) -> str:
    return {"high": "压力较高", "medium": "需要复核", "low": "相对稳健"}.get(tone, "需要复核")


def _pressure_lane(title: str, detail: Any, tone: str | None = None) -> str:
    tone = tone or _pressure_tone(detail)
    width = {"high": 86, "medium": 58, "low": 34}.get(tone, 58)
    return f"""
    <article class="pressure-lane pressure-{tone}">
      <div class="pressure-head"><strong>{_e(title)}</strong>{_badge(_pressure_label(tone), tone)}</div>
      <div class="pressure-track"><i style="width:{width}%"></i></div>
      <p>{_e(detail)}</p>
    </article>
    """


def _meta_item(label: str, value: Any, kind: str = "neutral") -> str:
    return f'<div class="strip-item"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _hero_summary_strip(meta: dict[str, Any], score: Any) -> str:
    return f"""
    <div class="summary-strip">
      {_meta_item("基本面状态", meta.get("status"))}
      {_meta_item("证据置信度", meta.get("confidence"))}
      <div class="strip-item score-strip">
        <span>基本面评分</span><strong>{_e(score)}</strong>
        <div class="scorebar"><i></i></div>
      </div>
      {_meta_item("分析框架", meta.get("strategy_type_label"))}
      {_meta_item("子类型", meta.get("sub_type_label") or "不适用")}
      {_meta_item("边界", "纯基本面")}
    </div>
    """


def _hero_block(
    report: dict[str, Any],
    meta: dict[str, Any],
    core: dict[str, Any],
    research_anchor: dict[str, Any],
    question: dict[str, Any],
    score: Any,
) -> str:
    thesis = _first_text(research_anchor.get("main_thesis"), question.get("main_question"), core.get("title"))
    conflict = _first_text(research_anchor.get("key_conflict"), question.get("key_conflict"))
    boundary = _first_text(meta.get("data_quality_status"), core.get("evidence_confidence_explanation"))
    return f"""
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-kicker">
          <span>基本面研报</span>
          <span>{_e(meta.get("generated_at"))}</span>
        </div>
        {_tags(report.get("hero_tags"))}
        <div class="hero-layout">
          <div class="hero-main">
            <h1>{_e(meta.get("stock_code"))} {_e(meta.get("stock_name"))}</h1>
            <p class="hero-subtitle">{_e(core.get("title") or "基本面分析报告")}</p>
            <p class="hero-thesis">{_e(thesis)}</p>
          </div>
          <aside class="hero-aside">
            <div class="aside-label">关键判断</div>
            <p>{_e(core.get("summary"))}</p>
          </aside>
        </div>
        {_hero_summary_strip(meta, score)}
        <div class="hero-evidence">
          <div><span>核心矛盾</span><p>{_e(conflict)}</p></div>
          <div><span>证据边界</span><p>{_e(boundary)}</p></div>
        </div>
      </div>
    </section>
    """


def _editorial_conclusion(core: dict[str, Any], research_anchor: dict[str, Any], question: dict[str, Any]) -> str:
    proven = research_anchor.get("what_is_proven") or core.get("supporting_points")
    unproven = research_anchor.get("what_is_unproven") or core.get("limiting_points")
    review = core.get("must_track_points") or question.get("what_would_confirm")
    conflict = _first_text(research_anchor.get("key_conflict"), question.get("key_conflict"))
    return f"""
    <section id="conclusion" class="card editorial-conclusion">
      <div class="section-eyebrow">核心结论</div>
      <h2>{_e(core.get("title") or "核心结论")}</h2>
      <p class="lead-judgment">{_e(core.get("summary"))}</p>
      <div class="conflict-callout"><span>主矛盾</span><p>{_e(conflict)}</p></div>
      <div class="evidence-grid">
        <article class="evidence-card proven"><span>01</span><h3>已证明</h3>{_list(proven)}</article>
        <article class="evidence-card unproven"><span>02</span><h3>待验证</h3>{_list(unproven)}</article>
        <article class="evidence-card review"><span>03</span><h3>关键复核</h3>{_list(review)}</article>
      </div>
      <p class="confidence-note">{_e(core.get("evidence_confidence_explanation"))}</p>
    </section>
    """


def _financial_quality_panel(financial: dict[str, Any]) -> str:
    diagnosis_tone = _pressure_tone(financial.get("final_diagnosis") or financial.get("diagnosis_level"))
    return f"""
    <div class="financial-diagnosis">
      <div class="diagnosis-summary pressure-{diagnosis_tone}">
        <span>诊断等级</span>
        <strong>{_e(financial.get("diagnosis_level"))}</strong>
        <p>{_e(financial.get("final_diagnosis"))}</p>
      </div>
      <div class="pressure-grid">
        {_pressure_lane("收入质量", financial.get("revenue_quality"))}
        {_pressure_lane("利润质量", financial.get("profit_quality"))}
        {_pressure_lane("现金流质量", financial.get("cashflow_quality"))}
        {_pressure_lane("应收压力", financial.get("receivables_pressure"))}
        {_pressure_lane("存货压力", financial.get("inventory_pressure"))}
        {_pressure_lane("capex 压力", financial.get("capex_pressure"))}
        {_pressure_lane("合同负债", financial.get("contract_liabilities_interpretation"))}
        {_pressure_lane("自由现金流", financial.get("free_cashflow_interpretation"))}
      </div>
    </div>
    """


def _quality_score_cards(breakdown: dict[str, Any]) -> str:
    labels = [
        ("industry_position", "行业位置"),
        ("business_quality", "业务质量"),
        ("growth_realization", "成长兑现"),
        ("financial_quality", "财务质量"),
        ("valuation_explainability", "估值可解释性"),
        ("risk_identifiability", "风险可识别性"),
    ]
    cards = []
    for key, fallback_label in labels:
        item = breakdown.get(key) if isinstance(breakdown, dict) else {}
        if not isinstance(item, dict):
            item = {}
        score = item.get("score")
        max_score = item.get("max_score") or 10
        width = _score_percent(score, max_score)
        cards.append(
            f"""
            <article class="quality-score">
              <div class="quality-head"><strong>{_e(item.get("label") or fallback_label)}</strong><span>{_e(score if score is not None else "-")}/{_e(max_score)}</span></div>
              <div class="scorebar compact"><i style="width:{width}%"></i></div>
              <p>{_e(item.get("explanation") or "缺少评分解释，无法形成强判断。")}</p>
              <h4>证据基础</h4>{_list(item.get("evidence_basis"))}
            </article>
            """
        )
    return '<div class="quality-grid">' + "".join(cards) + "</div>"


def _value_chain_map(chain: dict[str, Any]) -> str:
    if not isinstance(chain, dict):
        chain = {}
    return f"""
    <div class="chain-map">
      <div class="chain-node"><span>上游</span><strong>{_e(chain.get("upstream") or "待验证")}</strong></div>
      <div class="chain-arrow">→</div>
      <div class="chain-node company"><span>公司位置</span><strong>{_e(chain.get("company_role") or "待验证")}</strong></div>
      <div class="chain-arrow">→</div>
      <div class="chain-node"><span>下游</span><strong>{_e(chain.get("downstream") or "待验证")}</strong></div>
    </div>
    <div class="two-col">
      <div class="mini"><h3>利润来源</h3><p>{_e(chain.get("profit_source") or "待验证")}</p></div>
      <div class="mini"><h3>关键瓶颈</h3>{_list(chain.get("key_bottlenecks"))}</div>
      <div class="mini"><h3>尚未证明的壁垒</h3>{_list(chain.get("unproven_moats"))}</div>
    </div>
    """


def _financial_caveats(caveats: Any) -> str:
    rows = []
    for item in _as_list(caveats):
        if not isinstance(item, dict):
            continue
        rows.append(
            f"""
            <article class="mini caveat">
              <h3>{_e(item.get("ratio_name"))}</h3>
              <p>{_e(item.get("caveat"))}</p>
              <p>{_badge("解释强度：" + str(item.get("interpretation_strength") or "弱"), "neutral")}</p>
              <h4>后续需要</h4>{_list(item.get("required_follow_up_data"))}
            </article>
            """
        )
    if not rows:
        return '<p class="muted">财务比例口径提示缺失；涉及存量/期间数混合比例时不能形成强结论。</p>'
    return '<div class="three-col">' + "".join(rows) + "</div>"


def _tracking_groups(groups: Any) -> str:
    cards = []
    for group in _as_list(groups):
        if not isinstance(group, dict):
            continue
        items = [item for item in _as_list(group.get("items")) if isinstance(item, dict)]
        rows = "".join(
            f"""
            <tr>
              <td>{_e(item.get("indicator"))}</td>
              <td>{_e(item.get("frequency"))}</td>
              <td>{_e(item.get("why_it_matters"))}</td>
              <td>{_e(item.get("trigger_for_review"))}</td>
            </tr>
            """
            for item in items
        )
        cards.append(
            f"""
            <article class="mini tracking-group">
              <h3>{_e(group.get("group_name"))}</h3>
              <div class="table-wrap compact-table"><table><thead><tr><th>指标</th><th>频率</th><th>为什么重要</th><th>复核触发</th></tr></thead><tbody>{rows or '<tr><td colspan="4">-</td></tr>'}</tbody></table></div>
            </article>
            """
        )
    if not cards:
        return '<p class="muted">分层跟踪计划缺失，请回到财报、公告/订单、行业/政策和风险复核四类线索补齐。</p>'
    return '<div class="tracking-grid">' + "".join(cards) + "</div>"


def _must_track_table(items: Any) -> str:
    rows = []
    for item in _as_list(items):
        if not isinstance(item, dict):
            continue
        rows.append(
            f"""
            <tr>
              <td>{_e(item.get("indicator"))}</td>
              <td>{_e(item.get("priority"))}</td>
              <td>{_e(item.get("current_status"))}</td>
              <td>{_e(item.get("why_it_matters"))}</td>
              <td>{_e(item.get("next_evidence_needed"))}</td>
            </tr>
            """
        )
    return f'<div class="table-wrap"><table><thead><tr><th>指标</th><th>优先级</th><th>当前状态</th><th>为什么重要</th><th>下一步证据</th></tr></thead><tbody>{"".join(rows) or "<tr><td colspan=\"5\">-</td></tr>"}</tbody></table></div>'


def render_fundamental_html_report(report: dict[str, Any]) -> str:
    validation = validate_fundamental_html_report(report)
    if not validation["valid"]:
        errors = _e(validation.get("schema_errors"))
        raise ValueError(f"Fundamental HTML report validation failed: {errors}")
    report = validation["report"]

    meta = report["report_meta"]
    core = report["core_conclusion"]
    financial = report["financial_quality_diagnosis"]
    valuation = report["valuation_explanation"]
    scenarios = report["fundamental_scenario_analysis"]
    risks = report["risk_analysis"]
    quality = report["data_quality_and_unknowns"]
    research_anchor = report.get("research_anchor") or {}
    quality_breakdown = report.get("quality_score_breakdown") or {}
    value_chain_v21 = report.get("value_chain_map") or {}
    elasticity = report.get("elasticity_formula") or {}
    score = meta.get("fundamental_score")
    score_width = max(0, min(100, int(float(score)))) if isinstance(score, (int, float)) else 0

    nav = [
        ("核心结论", "conclusion"),
        ("公司画像", "profile"),
        ("业务构成", "business"),
        ("财务质量", "financial"),
        ("研究主线", "anchor"),
        ("六维评分", "quality-score"),
        ("估值解释", "valuation"),
        ("核心命题", "question"),
        ("产业链图谱", "chain-map"),
        ("弹性公式", "elasticity"),
        ("情景分析", "scenario"),
        ("风险分析", "risk"),
        ("分层跟踪", "tracking-plan"),
        ("数据质量", "quality"),
    ]
    nav_html = "".join(f'<a href="#{target}">{label}</a>' for label, target in nav)

    business = report["business_composition_analysis"]
    profile = report["company_profile"]
    updates = report["recent_fundamental_updates"]
    question = report["core_fundamental_question"]
    cycle = report["industry_cycle_positioning"]
    chain = report["value_chain_and_business_model"]
    peer = report["peer_comparison"]

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(meta.get("stock_code"))} {_e(meta.get("stock_name"))} 基本面分析报告</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg:#0c0f15; --panel:#171b24; --panel-2:#1f2530; --text:#edf1f7; --muted:#98a2b3;
      --line:#2f3745; --gold:#d7b56d; --gold-2:#f1d58f; --risk:#e68b6a; --ok:#78c6a3;
      --shadow:0 18px 50px rgba(0,0,0,.28);
    }}
    body.light {{
      color-scheme: light;
      --bg:#f6f3ed; --panel:#ffffff; --panel-2:#f1eee7; --text:#17202c; --muted:#667085;
      --line:#ddd6c9; --gold:#8f6b24; --gold-2:#b88a2f; --risk:#b85c38; --ok:#2d7a5f;
      --shadow:0 14px 34px rgba(30,37,48,.12);
    }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; max-width:100%; overflow-x:hidden; }}
    body {{ margin:0; max-width:100%; overflow-x:hidden; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif; line-height:1.7; letter-spacing:0; }}
    a {{ color:inherit; text-decoration:none; }}
    body, main, header, footer, section, article, div, p, h1, h2, h3, h4, li, strong, td, th {{ overflow-wrap:anywhere; word-break:break-word; }}
    .topbar {{ position:sticky; top:0; z-index:20; display:flex; align-items:center; gap:18px; width:100%; min-width:0; max-width:100%; overflow:hidden; padding:12px 28px; background:color-mix(in srgb,var(--bg) 88%,transparent); border-bottom:1px solid var(--line); backdrop-filter:blur(12px); }}
    .brand {{ flex:0 0 auto; font-weight:700; color:var(--gold-2); white-space:nowrap; }}
    nav {{ display:flex; gap:12px; overflow-x:auto; overflow-y:hidden; flex:1 1 auto; min-width:0; max-width:100%; -webkit-overflow-scrolling:touch; }}
    nav a {{ color:var(--muted); font-size:14px; white-space:nowrap; padding:5px 0; }}
    nav a:hover {{ color:var(--gold-2); }}
    .theme-btn {{ flex:0 0 auto; border:1px solid var(--line); background:var(--panel-2); color:var(--text); border-radius:6px; padding:7px 10px; cursor:pointer; }}
    .hero {{ max-width:100%; overflow:hidden; padding:34px 28px 22px; background:radial-gradient(circle at 18% 0%, rgba(215,181,109,.18), transparent 34%), linear-gradient(180deg,color-mix(in srgb,var(--panel) 32%,var(--bg)),var(--bg)); border-bottom:1px solid color-mix(in srgb,var(--gold) 28%,var(--line)); }}
    .hero-inner {{ width:100%; max-width:1180px; min-width:0; margin:0 auto; }}
    .hero-kicker {{ display:flex; justify-content:space-between; gap:14px; color:var(--gold-2); font-size:13px; margin-bottom:14px; }}
    .hero-layout {{ display:grid; grid-template-columns:minmax(0,1.35fr) minmax(280px,.65fr); gap:22px; align-items:stretch; }}
    .hero h1 {{ margin:0 0 6px; font-size:46px; line-height:1.08; letter-spacing:0; overflow-wrap:anywhere; word-break:break-word; }}
    .hero p {{ color:var(--muted); margin:0; }}
    .hero-subtitle {{ max-width:920px; font-size:22px; color:var(--text); font-weight:750; }}
    .hero-thesis {{ max-width:900px; margin-top:14px !important; font-size:16px; }}
    .hero-aside {{ min-width:0; max-width:100%; border:1px solid color-mix(in srgb,var(--gold) 42%,var(--line)); border-radius:8px; padding:16px; background:color-mix(in srgb,var(--gold) 8%,var(--panel)); box-shadow:var(--shadow); }}
    .aside-label {{ color:var(--gold-2); font-size:13px; font-weight:700; margin-bottom:8px; }}
    .hero-aside p {{ color:var(--text); font-size:15px; line-height:1.75; }}
    .tag-row {{ display:flex; flex-wrap:wrap; min-width:0; max-width:100%; gap:8px; margin:0 0 18px; }}
    .hero-tag {{ display:inline-flex; align-items:center; max-width:100%; min-height:28px; padding:3px 10px; border:1px solid color-mix(in srgb,var(--gold) 55%,var(--line)); border-radius:999px; color:var(--gold-2); background:color-mix(in srgb,var(--gold) 10%,transparent); font-size:13px; white-space:normal; }}
    .summary-strip {{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:8px; margin-top:18px; padding:10px; border:1px solid var(--line); border-radius:8px; background:color-mix(in srgb,var(--panel) 82%,transparent); }}
    .strip-item {{ min-width:0; border-right:1px solid var(--line); padding:4px 10px; }}
    .strip-item:last-child {{ border-right:0; }}
    .strip-item span {{ display:block; color:var(--muted); font-size:12px; }}
    .strip-item strong {{ display:block; margin:2px 0 4px; font-size:15px; line-height:1.35; }}
    .score-strip .scorebar {{ height:7px; margin-top:6px; }}
    .hero-evidence {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:12px; margin-top:12px; }}
    .hero-evidence div {{ min-width:0; border:1px solid var(--line); border-radius:8px; padding:12px 14px; background:color-mix(in srgb,var(--panel-2) 72%,transparent); }}
    .hero-evidence span {{ display:block; color:var(--gold-2); font-size:13px; font-weight:700; margin-bottom:4px; }}
    .hero-evidence p {{ font-size:14px; }}
    .meta-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); min-width:0; max-width:100%; gap:12px; margin-top:28px; }}
    .metric {{ min-width:0; max-width:100%; background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; box-shadow:var(--shadow); }}
    .metric span {{ display:block; color:var(--muted); font-size:13px; }}
    .metric strong {{ display:block; margin-top:4px; font-size:18px; }}
    .scorebar {{ width:100%; max-width:100%; min-width:0; height:10px; background:var(--panel-2); border-radius:999px; overflow:hidden; margin-top:10px; border:1px solid var(--line); }}
    .scorebar i {{ display:block; width:{score_width}%; height:100%; background:linear-gradient(90deg,var(--gold),var(--gold-2)); }}
    main {{ width:100%; max-width:1180px; min-width:0; margin:0 auto; padding:18px 28px 48px; }}
    .card {{ min-width:0; max-width:100%; background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:24px; margin:18px 0; box-shadow:var(--shadow); }}
    .card > *, .mini > *, .metric > *, .scenario > *, .risk-card > *, .quality-score > *, .chain-node > *, .pressure-lane > *, .evidence-card > * {{ min-width:0; max-width:100%; }}
    .highlight {{ border-color:color-mix(in srgb,var(--gold) 55%,var(--line)); background:linear-gradient(135deg,color-mix(in srgb,var(--gold) 12%,var(--panel)),var(--panel)); }}
    .editorial-conclusion {{ border-color:color-mix(in srgb,var(--gold) 58%,var(--line)); background:linear-gradient(135deg,color-mix(in srgb,var(--gold) 14%,var(--panel)),var(--panel)); }}
    .section-eyebrow {{ display:inline-flex; color:var(--bg); background:var(--gold-2); border-radius:999px; padding:2px 10px; font-size:12px; font-weight:800; margin-bottom:12px; }}
    .lead-judgment {{ font-size:17px; color:var(--text); margin-bottom:16px; }}
    .conflict-callout {{ border-left:3px solid var(--gold-2); background:color-mix(in srgb,var(--panel-2) 82%,transparent); padding:12px 14px; border-radius:6px; margin-bottom:16px; }}
    .conflict-callout span {{ display:block; color:var(--gold-2); font-size:13px; font-weight:700; margin-bottom:4px; }}
    .evidence-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
    .evidence-card {{ min-width:0; background:var(--panel-2); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .evidence-card > span {{ display:inline-flex; color:var(--gold-2); font-size:12px; font-weight:800; margin-bottom:6px; }}
    .evidence-card.proven {{ border-color:color-mix(in srgb,var(--ok) 40%,var(--line)); }}
    .evidence-card.unproven {{ border-color:color-mix(in srgb,var(--gold) 45%,var(--line)); }}
    .evidence-card.review {{ border-color:color-mix(in srgb,var(--risk) 35%,var(--line)); }}
    .confidence-note {{ color:var(--muted); border-top:1px solid var(--line); padding-top:12px; margin-top:14px; }}
    h2 {{ margin:0 0 16px; font-size:24px; }}
    h3 {{ margin:0 0 10px; font-size:18px; }}
    h4 {{ margin:14px 0 6px; font-size:14px; color:var(--gold-2); }}
    .muted {{ color:var(--muted); }}
    .two-col {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); min-width:0; max-width:100%; gap:16px; }}
    .three-col {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }}
    .financial-diagnosis {{ display:grid; grid-template-columns:minmax(240px,.34fr) minmax(0,.66fr); gap:16px; }}
    .diagnosis-summary {{ min-width:0; border:1px solid var(--line); border-radius:8px; padding:18px; background:var(--panel-2); }}
    .diagnosis-summary span {{ display:block; color:var(--muted); font-size:13px; }}
    .diagnosis-summary strong {{ display:block; color:var(--gold-2); font-size:28px; line-height:1.2; margin:4px 0 10px; }}
    .pressure-grid {{ min-width:0; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }}
    .pressure-lane {{ min-width:0; max-width:100%; border:1px solid var(--line); border-radius:8px; padding:12px; background:var(--panel-2); }}
    .pressure-head {{ display:flex; align-items:center; justify-content:space-between; gap:8px; }}
    .pressure-track {{ height:7px; margin:9px 0; border-radius:999px; overflow:hidden; background:color-mix(in srgb,var(--line) 55%,transparent); }}
    .pressure-track i {{ display:block; height:100%; border-radius:999px; background:var(--gold-2); }}
    .pressure-lane p {{ font-size:13px; color:var(--muted); }}
    .pressure-high .pressure-track i {{ background:var(--risk); }}
    .pressure-medium .pressure-track i {{ background:var(--gold-2); }}
    .pressure-low .pressure-track i {{ background:var(--ok); }}
    .badge-high {{ border-color:var(--risk); color:var(--risk); }}
    .badge-medium {{ border-color:var(--gold); color:var(--gold-2); }}
    .badge-low {{ border-color:var(--ok); color:var(--ok); }}
    .quality-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }}
    .three-col, .quality-grid, .scenario-grid, .risk-grid, .tracking-grid, .chain-map {{ min-width:0; max-width:100%; }}
    .quality-score {{ min-width:0; max-width:100%; background:var(--panel-2); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .quality-head {{ display:flex; align-items:center; justify-content:space-between; gap:10px; }}
    .scorebar.compact {{ height:8px; margin:10px 0; }}
    .chain-map {{ display:grid; grid-template-columns:minmax(0,1fr) auto minmax(0,1.1fr) auto minmax(0,1fr); align-items:stretch; gap:10px; margin-bottom:16px; }}
    .chain-node {{ min-width:0; max-width:100%; border:1px solid var(--line); background:var(--panel-2); border-radius:8px; padding:16px; min-height:104px; }}
    .chain-node.company {{ border-color:color-mix(in srgb,var(--gold) 60%,var(--line)); background:color-mix(in srgb,var(--gold) 10%,var(--panel-2)); }}
    .chain-node span {{ display:block; color:var(--muted); font-size:13px; margin-bottom:6px; }}
    .chain-node strong {{ display:block; font-size:16px; }}
    .chain-arrow {{ color:var(--gold-2); align-self:center; font-size:22px; }}
    .tracking-grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:14px; }}
    .compact-table table {{ min-width:560px; }}
    .mini {{ min-width:0; max-width:100%; background:var(--panel-2); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .formula {{ max-width:100%; overflow-x:auto; font-family:"Microsoft YaHei",Arial,sans-serif; font-size:20px; color:var(--gold-2); padding:14px 16px; border:1px solid color-mix(in srgb,var(--gold) 45%,var(--line)); border-radius:8px; background:color-mix(in srgb,var(--gold) 8%,var(--panel-2)); }}
    .badge {{ display:inline-flex; align-items:center; max-width:100%; min-height:24px; padding:2px 9px; border:1px solid var(--line); border-radius:999px; font-size:12px; color:var(--text); background:var(--panel-2); white-space:normal; }}
    .badge-neutral {{ border-color:var(--gold); color:var(--gold-2); }}
    .badge-risk {{ border-color:var(--risk); color:var(--risk); }}
    .badge-optimistic {{ border-color:var(--ok); color:var(--ok); }}
    .badge-base {{ border-color:var(--gold); color:var(--gold-2); }}
    .badge-downside {{ border-color:var(--risk); color:var(--risk); }}
    ul {{ padding-left:20px; margin:8px 0 0; }}
    .table-wrap {{ width:100%; min-width:0; max-width:100%; overflow-x:auto; overflow-y:hidden; border:1px solid var(--line); border-radius:8px; }}
    table {{ width:100%; max-width:none; border-collapse:collapse; min-width:760px; }}
    th,td {{ padding:11px 12px; border-bottom:1px solid var(--line); vertical-align:top; text-align:left; }}
    th {{ background:var(--panel-2); color:var(--gold-2); font-weight:650; }}
    tr:hover td {{ background:color-mix(in srgb,var(--panel-2) 55%,transparent); }}
    .scenario-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }}
    .scenario {{ min-width:0; max-width:100%; border:1px solid var(--line); border-radius:8px; padding:18px; background:var(--panel-2); }}
    .scenario-optimistic {{ border-color:color-mix(in srgb,var(--ok) 50%,var(--line)); }}
    .scenario-base {{ border-color:color-mix(in srgb,var(--gold) 55%,var(--line)); }}
    .scenario-downside {{ border-color:color-mix(in srgb,var(--risk) 55%,var(--line)); }}
    .risk-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }}
    .risk-card {{ min-width:0; max-width:100%; background:var(--panel-2); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .risk-line {{ display:flex; align-items:flex-start; justify-content:space-between; gap:10px; padding:8px 0; border-top:1px solid var(--line); }}
    .risk-line span {{ min-width:0; }}
    svg {{ max-width:100%; height:auto; }}
    footer {{ width:100%; min-width:0; border-top:1px solid var(--line); padding:24px 28px 40px; color:var(--muted); max-width:1180px; margin:0 auto; }}
    @media (max-width:900px) {{ .hero-layout,.hero-evidence,.financial-diagnosis,.pressure-grid,.evidence-grid,.meta-grid,.two-col,.three-col,.scenario-grid,.risk-grid,.quality-grid,.tracking-grid,.chain-map {{ grid-template-columns:1fr; }} .summary-strip {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .strip-item {{ border-right:0; border-bottom:1px solid var(--line); }} .strip-item:nth-last-child(-n+2) {{ border-bottom:0; }} .chain-arrow {{ display:none; }} .hero {{ padding-top:24px; padding-bottom:16px; }} .hero h1 {{ font-size:34px; }} .hero-subtitle {{ font-size:19px; }} .hero-thesis {{ font-size:15px; }} .hero-aside p {{ font-size:14px; }} .topbar {{ padding:10px 16px; }} table {{ min-width:640px; }} .compact-table table {{ min-width:520px; }} main,.hero {{ padding-left:16px; padding-right:16px; }} }}
    @media (max-width:520px) {{ .summary-strip {{ grid-template-columns:1fr 1fr; gap:6px; padding:8px; }} .strip-item {{ padding:4px 6px; }} .strip-item strong {{ font-size:14px; }} .hero-kicker {{ flex-direction:column; gap:2px; }} .hero h1 {{ font-size:30px; }} .hero-aside {{ padding:12px; }} .hero-evidence div {{ padding:10px; }} .card {{ padding:18px; }} }}
  </style>
</head>
<body>
  <header class="topbar"><div class="brand">基本面研报</div><nav>{nav_html}</nav><button class="theme-btn" type="button" onclick="document.body.classList.toggle('light')">主题</button></header>
  {_hero_block(report, meta, core, research_anchor, question, score)}
  <main>
    {_editorial_conclusion(core, research_anchor, question)}
    {_section("profile", "公司画像", f'<div class="two-col"><div class="mini"><h3>主营业务</h3><p>{_e(profile.get("main_business"))}</p><h3>业务锚点</h3><p>{_e(profile.get("core_business_anchor"))}</p></div><div class="mini"><h3>框架身份</h3><p>{_e(profile.get("framework_identity"))}</p><h3>公司属性</h3><p>{_e(profile.get("ownership_or_company_nature"))}</p></div></div><h3>业务分部</h3>{_table(profile.get("business_segments"))}')}
    {_section("updates", "近期基本面动态", f'<div class="two-col"><div class="mini"><h3>财务更新</h3><p>{_e(updates.get("financial_update"))}</p></div><div class="mini"><h3>业务更新</h3><p>{_e(updates.get("business_update"))}</p></div><div class="mini"><h3>政策与行业</h3><p>{_e(updates.get("policy_or_industry_update"))}</p></div><div class="mini"><h3>新闻可用性</h3><p>{_e(updates.get("unavailable_news_note") or "新闻源不可用；不补写未经验证的近期事件。")}</p></div></div>')}
    {_section("business", "业务构成分析", f'{_table(business.get("segment_table"))}<div class="three-col"><div class="mini"><h3>核心业务</h3><p>{_e(business.get("core_segment"))}</p></div><div class="mini"><h3>拖累业务</h3><p>{_e(business.get("drag_segment"))}</p></div><div class="mini"><h3>成长弹性来源</h3><p>{_e(business.get("growth_optional_segment"))}</p></div></div><p>{_e(business.get("analysis"))}</p>')}
    {_section("financial", "财务质量诊断", _financial_quality_panel(financial))}
    {_section("ratio-caveats", "财务比例口径提示", _financial_caveats(report.get("financial_ratio_caveats")))}
    {_section("anchor", "研究主线 / 核心矛盾", f'<div class="two-col"><div class="mini"><h3>研究主线</h3><p>{_e(research_anchor.get("main_thesis"))}</p><h3>当前阶段</h3><p>{_e(research_anchor.get("current_stage"))}</p></div><div class="mini"><h3>核心矛盾</h3><p>{_e(research_anchor.get("key_conflict"))}</p></div><div class="mini"><h3>已被证明</h3>{_list(research_anchor.get("what_is_proven"))}</div><div class="mini"><h3>尚未证明</h3>{_list(research_anchor.get("what_is_unproven"))}</div></div>')}
    {_section("quality-score", "六维质量评分", _quality_score_cards(quality_breakdown))}
    {_section("valuation", "估值解释", f'{_table(valuation.get("valuation_metrics"))}<p>{_e(valuation.get("valuation_interpretation"))}</p><p>{_badge(valuation.get("peer_benchmark_status"), "neutral")}</p><div class="two-col"><div class="mini"><h3>需要证明的基本面</h3>{_list(valuation.get("what_must_be_proven_to_justify_valuation"))}</div><div class="mini"><h3>无法判断事项</h3>{_list(valuation.get("cannot_determine_items"))}</div></div>')}
    {_section("question", "核心基本面命题", f'<div class="two-col"><div class="mini"><h3>主问题</h3><p>{_e(question.get("main_question"))}</p><h3>关键矛盾</h3><p>{_e(question.get("key_conflict"))}</p></div><div class="mini"><h3>确认条件</h3>{_list(question.get("what_would_confirm"))}<h3>削弱条件</h3>{_list(question.get("what_would_invalidate"))}</div></div>')}
    {_section("cycle", "行业周期定位", f'<div class="two-col"><div class="mini"><h3>周期阶段</h3><p>{_e(cycle.get("cycle_stage"))}</p><h3>政策或需求背景</h3><p>{_e(cycle.get("policy_or_demand_background"))}</p></div><div class="mini"><h3>证据强度</h3><p>{_e(cycle.get("evidence_strength"))}</p><h3>缺失证据</h3>{_list(cycle.get("missing_evidence"))}</div></div>')}
    {_section("chain", "产业链与商业模式", f'<div class="two-col"><div class="mini"><h3>上游</h3><p>{_e(chain.get("upstream"))}</p><h3>下游</h3><p>{_e(chain.get("downstream"))}</p><h3>客户结构</h3><p>{_e(chain.get("customer_structure"))}</p></div><div class="mini"><h3>盈利方式</h3><p>{_e(chain.get("how_company_makes_money"))}</p><h3>利润率来源</h3><p>{_e(chain.get("margin_source"))}</p></div></div><div class="two-col"><div class="mini"><h3>已披露壁垒线索</h3>{_list(chain.get("moat_claims"))}</div><div class="mini"><h3>尚未证明的壁垒</h3>{_list(chain.get("unproven_moats"))}</div></div>')}
    {_section("chain-map", "产业链图谱", _value_chain_map(value_chain_v21))}
    {_section("elasticity", "基本面弹性公式", f'<div class="mini"><h3>{_e(elasticity.get("formula_title") or "基本面弹性")}</h3><div class="formula">{_e(elasticity.get("formula_text") or "利润弹性 = 收入增长 × 毛利率稳定性 × 费用率控制")}</div><h3>关键变量</h3>{_list(elasticity.get("key_variables"))}<h3>解释</h3><p>{_e(elasticity.get("interpretation"))}</p><h3>数据限制</h3>{_list(elasticity.get("data_limitations"))}</div>')}
    <section id="scenario" class="card"><h2>基本面情景分析</h2><div class="scenario-grid">{_scenario_card(scenarios.get("optimistic_case", {}), "optimistic")}{_scenario_card(scenarios.get("base_case", {}), "base")}{_scenario_card(scenarios.get("downside_case", {}), "downside")}</div></section>
    {_section("peer", "同业对比", f'<p>{_badge(peer.get("peer_benchmark_status"), "neutral")}</p>{_table(peer.get("comparison_table"))}<p>{_e(peer.get("interpretation"))}</p><p class="muted">{_e(peer.get("peer_data_missing_note"))}</p>')}
    <section id="risk" class="card"><h2>风险分析</h2><div class="risk-grid">{_risk_list("业务风险", risks.get("business_risks"), "业务")}{_risk_list("财务风险", risks.get("financial_risks"), "财务")}{_risk_list("行业风险", risks.get("industry_risks"), "行业")}{_risk_list("政策风险", risks.get("policy_risks"), "政策")}{_risk_list("数据缺口风险", risks.get("data_gap_risks"), "数据")}</div></section>
    {_section("tracking-plan", "分层跟踪计划", _tracking_groups(report.get("tracking_plan_groups")))}
    {_section("track", "必须跟踪指标", _must_track_table([item for item in report.get("must_track_indicators", [])]))}
    {_section("review", "后续基本面复核条件", _table([item for item in report.get("follow_up_review_conditions", [])]))}
    {_section("quality", "数据质量与未知项", f'<div class="two-col"><div class="mini"><h3>可用数据</h3>{_list(quality.get("available_data"))}<h3>缺失数据</h3>{_list(quality.get("missing_data"))}</div><div class="mini"><h3>Proxy 字段</h3>{_list(quality.get("proxy_fields"))}<h3>无法判断</h3>{_list(quality.get("cannot_determine"))}</div></div><h3>来源限制</h3>{_list(quality.get("source_limitations"))}')}
  </main>
  <footer>
    <strong>安全边界：</strong>{_e(report["safety_boundary"].get("statement"))}
  </footer>
</body>
</html>
"""


def write_fundamental_html_report(report: dict[str, Any], output_path: str | Path) -> str:
    html_text = render_fundamental_html_report(report)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")
    return html_text


def render_from_json_file(input_path: str | Path, output_path: str | Path | None = None) -> str:
    path = Path(input_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    target = Path(output_path) if output_path else path.with_suffix(".html")
    return write_fundamental_html_report(payload, target)
