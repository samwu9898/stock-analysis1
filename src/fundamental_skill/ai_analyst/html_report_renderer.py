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
    score = meta.get("fundamental_score")
    score_width = max(0, min(100, int(float(score)))) if isinstance(score, (int, float)) else 0

    nav = [
        ("核心结论", "conclusion"),
        ("公司画像", "profile"),
        ("业务构成", "business"),
        ("财务质量", "financial"),
        ("估值解释", "valuation"),
        ("核心命题", "question"),
        ("产业链", "chain"),
        ("情景分析", "scenario"),
        ("风险分析", "risk"),
        ("跟踪指标", "track"),
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
    html {{ scroll-behavior:smooth; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif; line-height:1.7; letter-spacing:0; }}
    a {{ color:inherit; text-decoration:none; }}
    .topbar {{ position:sticky; top:0; z-index:20; display:flex; align-items:center; gap:18px; padding:12px 28px; background:color-mix(in srgb,var(--bg) 88%,transparent); border-bottom:1px solid var(--line); backdrop-filter:blur(12px); }}
    .brand {{ font-weight:700; color:var(--gold-2); white-space:nowrap; }}
    nav {{ display:flex; gap:12px; overflow-x:auto; flex:1; }}
    nav a {{ color:var(--muted); font-size:14px; white-space:nowrap; padding:5px 0; }}
    nav a:hover {{ color:var(--gold-2); }}
    .theme-btn {{ border:1px solid var(--line); background:var(--panel-2); color:var(--text); border-radius:6px; padding:7px 10px; cursor:pointer; }}
    .hero {{ padding:54px 28px 30px; background:radial-gradient(circle at 20% 0%, rgba(215,181,109,.18), transparent 34%), var(--bg); }}
    .hero-inner {{ max-width:1180px; margin:0 auto; }}
    .hero h1 {{ margin:0 0 12px; font-size:42px; line-height:1.15; letter-spacing:0; }}
    .hero p {{ max-width:880px; color:var(--muted); margin:0; }}
    .meta-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-top:28px; }}
    .metric {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; box-shadow:var(--shadow); }}
    .metric span {{ display:block; color:var(--muted); font-size:13px; }}
    .metric strong {{ display:block; margin-top:4px; font-size:18px; }}
    .scorebar {{ height:10px; background:var(--panel-2); border-radius:999px; overflow:hidden; margin-top:10px; border:1px solid var(--line); }}
    .scorebar i {{ display:block; width:{score_width}%; height:100%; background:linear-gradient(90deg,var(--gold),var(--gold-2)); }}
    main {{ max-width:1180px; margin:0 auto; padding:18px 28px 48px; }}
    .card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:24px; margin:18px 0; box-shadow:var(--shadow); }}
    .highlight {{ border-color:color-mix(in srgb,var(--gold) 55%,var(--line)); background:linear-gradient(135deg,color-mix(in srgb,var(--gold) 12%,var(--panel)),var(--panel)); }}
    h2 {{ margin:0 0 16px; font-size:24px; }}
    h3 {{ margin:0 0 10px; font-size:18px; }}
    h4 {{ margin:14px 0 6px; font-size:14px; color:var(--gold-2); }}
    .muted {{ color:var(--muted); }}
    .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
    .three-col {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }}
    .mini {{ background:var(--panel-2); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .badge {{ display:inline-flex; align-items:center; min-height:24px; padding:2px 9px; border:1px solid var(--line); border-radius:999px; font-size:12px; color:var(--text); background:var(--panel-2); }}
    .badge-neutral {{ border-color:var(--gold); color:var(--gold-2); }}
    .badge-risk {{ border-color:var(--risk); color:var(--risk); }}
    .badge-optimistic {{ border-color:var(--ok); color:var(--ok); }}
    .badge-base {{ border-color:var(--gold); color:var(--gold-2); }}
    .badge-downside {{ border-color:var(--risk); color:var(--risk); }}
    ul {{ padding-left:20px; margin:8px 0 0; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:8px; }}
    table {{ width:100%; border-collapse:collapse; min-width:760px; }}
    th,td {{ padding:11px 12px; border-bottom:1px solid var(--line); vertical-align:top; text-align:left; }}
    th {{ background:var(--panel-2); color:var(--gold-2); font-weight:650; }}
    tr:hover td {{ background:color-mix(in srgb,var(--panel-2) 55%,transparent); }}
    .scenario-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }}
    .scenario {{ border:1px solid var(--line); border-radius:8px; padding:18px; background:var(--panel-2); }}
    .scenario-optimistic {{ border-color:color-mix(in srgb,var(--ok) 50%,var(--line)); }}
    .scenario-base {{ border-color:color-mix(in srgb,var(--gold) 55%,var(--line)); }}
    .scenario-downside {{ border-color:color-mix(in srgb,var(--risk) 55%,var(--line)); }}
    .risk-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }}
    .risk-card {{ background:var(--panel-2); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .risk-line {{ display:flex; align-items:flex-start; justify-content:space-between; gap:10px; padding:8px 0; border-top:1px solid var(--line); }}
    footer {{ border-top:1px solid var(--line); padding:24px 28px 40px; color:var(--muted); max-width:1180px; margin:0 auto; }}
    @media (max-width:900px) {{ .meta-grid,.two-col,.three-col,.scenario-grid,.risk-grid {{ grid-template-columns:1fr; }} .hero h1 {{ font-size:32px; }} .topbar {{ padding:10px 16px; }} main,.hero {{ padding-left:16px; padding-right:16px; }} }}
  </style>
</head>
<body>
  <header class="topbar"><div class="brand">基本面研报</div><nav>{nav_html}</nav><button class="theme-btn" type="button" onclick="document.body.classList.toggle('light')">主题</button></header>
  <section class="hero">
    <div class="hero-inner">
      <h1>{_e(meta.get("stock_code"))} {_e(meta.get("stock_name"))} 基本面分析报告</h1>
      <p>{_e(core.get("summary"))}</p>
      <div class="meta-grid">
        <div class="metric"><span>分析框架</span><strong>{_e(meta.get("strategy_type_label"))}</strong></div>
        <div class="metric"><span>基本面状态</span><strong>{_e(meta.get("status"))}</strong></div>
        <div class="metric"><span>证据置信度</span><strong>{_e(meta.get("confidence"))}</strong></div>
        <div class="metric"><span>基本面评分</span><strong>{_e(score)}</strong><div class="scorebar"><i></i></div></div>
        <div class="metric"><span>子类型</span><strong>{_e(meta.get("sub_type_label") or "不适用")}</strong></div>
        <div class="metric"><span>数据质量</span><strong>{_e(meta.get("data_quality_status"))}</strong></div>
        <div class="metric"><span>生成时间</span><strong>{_e(meta.get("generated_at"))}</strong></div>
        <div class="metric"><span>边界</span><strong>纯基本面</strong></div>
      </div>
    </div>
  </section>
  <main>
    <section id="conclusion" class="card highlight">
      <h2>{_e(core.get("title") or "核心结论")}</h2>
      <p>{_e(core.get("summary"))}</p>
      <div class="three-col">
        <div class="mini"><h3>支持证据</h3>{_list(core.get("supporting_points"))}</div>
        <div class="mini"><h3>限制因素</h3>{_list(core.get("limiting_points"))}</div>
        <div class="mini"><h3>必须跟踪</h3>{_list(core.get("must_track_points"))}</div>
      </div>
      <p class="muted">{_e(core.get("evidence_confidence_explanation"))}</p>
    </section>
    {_section("profile", "公司画像", f'<div class="two-col"><div class="mini"><h3>主营业务</h3><p>{_e(profile.get("main_business"))}</p><h3>业务锚点</h3><p>{_e(profile.get("core_business_anchor"))}</p></div><div class="mini"><h3>框架身份</h3><p>{_e(profile.get("framework_identity"))}</p><h3>公司属性</h3><p>{_e(profile.get("ownership_or_company_nature"))}</p></div></div><h3>业务分部</h3>{_table(profile.get("business_segments"))}')}
    {_section("updates", "近期基本面动态", f'<div class="two-col"><div class="mini"><h3>财务更新</h3><p>{_e(updates.get("financial_update"))}</p></div><div class="mini"><h3>业务更新</h3><p>{_e(updates.get("business_update"))}</p></div><div class="mini"><h3>政策与行业</h3><p>{_e(updates.get("policy_or_industry_update"))}</p></div><div class="mini"><h3>新闻可用性</h3><p>{_e(updates.get("unavailable_news_note"))}</p></div></div>')}
    {_section("business", "业务构成分析", f'{_table(business.get("segment_table"))}<div class="three-col"><div class="mini"><h3>核心业务</h3><p>{_e(business.get("core_segment"))}</p></div><div class="mini"><h3>拖累业务</h3><p>{_e(business.get("drag_segment"))}</p></div><div class="mini"><h3>成长弹性来源</h3><p>{_e(business.get("growth_optional_segment"))}</p></div></div><p>{_e(business.get("analysis"))}</p>')}
    {_section("financial", "财务质量诊断", f'<div class="two-col"><div class="mini"><h3>收入质量</h3><p>{_e(financial.get("revenue_quality"))}</p><h3>利润质量</h3><p>{_e(financial.get("profit_quality"))}</p><h3>现金流质量</h3><p>{_e(financial.get("cashflow_quality"))}</p></div><div class="mini"><h3>诊断等级</h3>{_badge(financial.get("diagnosis_level"), "neutral")}<p>{_e(financial.get("final_diagnosis"))}</p></div></div><div class="three-col"><div class="mini"><h3>应收压力</h3><p>{_e(financial.get("receivables_pressure"))}</p></div><div class="mini"><h3>存货压力</h3><p>{_e(financial.get("inventory_pressure"))}</p></div><div class="mini"><h3>合同负债解释</h3><p>{_e(financial.get("contract_liabilities_interpretation"))}</p></div><div class="mini"><h3>资本开支压力</h3><p>{_e(financial.get("capex_pressure"))}</p></div><div class="mini"><h3>自由现金流</h3><p>{_e(financial.get("free_cashflow_interpretation"))}</p></div></div>')}
    {_section("valuation", "估值解释", f'{_table(valuation.get("valuation_metrics"))}<p>{_e(valuation.get("valuation_interpretation"))}</p><p>{_badge(valuation.get("peer_benchmark_status"), "neutral")}</p><div class="two-col"><div class="mini"><h3>需要证明的基本面</h3>{_list(valuation.get("what_must_be_proven_to_justify_valuation"))}</div><div class="mini"><h3>无法判断事项</h3>{_list(valuation.get("cannot_determine_items"))}</div></div>')}
    {_section("question", "核心基本面命题", f'<div class="two-col"><div class="mini"><h3>主问题</h3><p>{_e(question.get("main_question"))}</p><h3>关键矛盾</h3><p>{_e(question.get("key_conflict"))}</p></div><div class="mini"><h3>确认条件</h3>{_list(question.get("what_would_confirm"))}<h3>削弱条件</h3>{_list(question.get("what_would_invalidate"))}</div></div>')}
    {_section("cycle", "行业周期定位", f'<div class="two-col"><div class="mini"><h3>周期阶段</h3><p>{_e(cycle.get("cycle_stage"))}</p><h3>政策或需求背景</h3><p>{_e(cycle.get("policy_or_demand_background"))}</p></div><div class="mini"><h3>证据强度</h3><p>{_e(cycle.get("evidence_strength"))}</p><h3>缺失证据</h3>{_list(cycle.get("missing_evidence"))}</div></div>')}
    {_section("chain", "产业链与商业模式", f'<div class="two-col"><div class="mini"><h3>上游</h3><p>{_e(chain.get("upstream"))}</p><h3>下游</h3><p>{_e(chain.get("downstream"))}</p><h3>客户结构</h3><p>{_e(chain.get("customer_structure"))}</p></div><div class="mini"><h3>盈利方式</h3><p>{_e(chain.get("how_company_makes_money"))}</p><h3>利润率来源</h3><p>{_e(chain.get("margin_source"))}</p></div></div><div class="two-col"><div class="mini"><h3>已披露壁垒线索</h3>{_list(chain.get("moat_claims"))}</div><div class="mini"><h3>尚未证明的壁垒</h3>{_list(chain.get("unproven_moats"))}</div></div>')}
    <section id="scenario" class="card"><h2>基本面情景分析</h2><div class="scenario-grid">{_scenario_card(scenarios.get("optimistic_case", {}), "optimistic")}{_scenario_card(scenarios.get("base_case", {}), "base")}{_scenario_card(scenarios.get("downside_case", {}), "downside")}</div></section>
    {_section("peer", "同业对比", f'<p>{_badge(peer.get("peer_benchmark_status"), "neutral")}</p>{_table(peer.get("comparison_table"))}<p>{_e(peer.get("interpretation"))}</p><p class="muted">{_e(peer.get("peer_data_missing_note"))}</p>')}
    <section id="risk" class="card"><h2>风险分析</h2><div class="risk-grid">{_risk_list("业务风险", risks.get("business_risks"), "业务")}{_risk_list("财务风险", risks.get("financial_risks"), "财务")}{_risk_list("行业风险", risks.get("industry_risks"), "行业")}{_risk_list("政策风险", risks.get("policy_risks"), "政策")}{_risk_list("数据缺口风险", risks.get("data_gap_risks"), "数据")}</div></section>
    {_section("track", "必须跟踪指标", _table([item for item in report.get("must_track_indicators", [])]))}
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
