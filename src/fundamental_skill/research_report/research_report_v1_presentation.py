# -*- coding: utf-8 -*-
"""Chinese Markdown presentation layer for Research Report V1."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from .research_report_v1 import (
    ResearchReportArtifactBoundaryError,
    ResearchReportBuildError,
    _assert_no_secret_like_payload,
    _assert_report_payload,
    _normalize_code,
)


MARKDOWN_OUTPUT_FILENAME = "fundamental_research_report_v1.md"

_TIMESTAMP_RE = re.compile(r"^[A-Za-z0-9T_-]{1,64}$")

_COMPANY_NAME_OVERRIDES = {
    "600406": "国电南瑞",
}

_FIELD_CN = {
    "financial_metrics.revenue": "收入",
    "financial_metrics.net_profit": "净利润",
    "financial_metrics.gross_margin": "毛利率",
    "financial_metrics.roe": "ROE",
    "financial_metrics.operating_cashflow": "经营现金流",
    "financial_metrics.accounts_receivable": "应收账款",
    "financial_metrics.inventory": "存货",
    "financial_metrics.contract_liabilities": "合同负债",
    "financial_metrics.capex": "资本开支",
    "valuation_metrics.pe_ttm": "PE",
    "valuation_metrics.pb": "PB",
    "valuation_metrics.market_cap": "总市值",
    "valuation_metrics.as_of_date": "估值数据日期",
    "business_composition.period": "主营构成期间",
    "business_composition.classification_type": "主营构成分类口径",
    "business_composition.revenue_ratio": "主营构成收入占比",
    "basic_info.main_business": "主营业务官方来源",
    "score_confidence_explainability.score_drift": "评分与置信度差异",
}

_EVIDENCE_CN = {
    "auto_accepted_candidate": "候选可信字段",
    "manual_review_required": "需人工复核",
    "unsupported_assumption": "待验证假设",
    "coverage_caveat": "覆盖缺口",
    "forward_tracking_variable": "后续跟踪变量",
    "verified_fact": "经复核事实",
}

_OPPORTUNITY_CN = {
    "grid_investment_cycle": "电网投资与国网/南网招标",
    "digital_grid": "数字电网",
    "uhv_and_distribution_grid": "特高压与配网建设",
    "power_automation_and_relay_protection": "电力自动化、继电保护、调度系统与电力信息通信",
    "stable_operating_quality_candidate": "经营质量候选支撑",
}

_RISK_CN = {
    "tender_cadence_risk": "招标节奏风险",
    "order_realization_risk": "订单兑现风险",
    "receivables_and_cashflow_risk": "应收账款与经营现金流风险",
    "gross_margin_pressure": "毛利率压力",
    "contract_liabilities_visibility_risk": "合同负债可见度风险",
    "business_composition_scope_risk": "主营构成口径风险",
    "valuation_date_risk": "估值日期风险",
    "data_quality_risk": "数据质量风险",
}

_FOLLOW_UP_CN = {
    "grid_investment_amount": "跟踪电网投资金额及项目节奏",
    "state_grid_and_csg_tenders": "跟踪国网 / 南网招标数据",
    "uhv_distribution_grid_project_cadence": "跟踪特高压与配网项目节奏",
    "digital_grid_policy_and_tender_conversion": "跟踪数字电网政策进展与招标转化",
    "accounts_receivable_turnover": "跟踪应收账款周转与回款质量",
    "operating_cashflow": "跟踪经营现金流相对收入和利润的变化",
    "contract_liabilities": "跟踪合同负债对订单可见度的提示作用",
    "gross_margin": "跟踪毛利率的价格、成本与产品结构压力",
    "business_composition": "跟踪主营构成的期间、分类口径和收入占比口径",
    "valuation_as_of_date": "跟踪估值数据日期的新鲜度",
    "pe_pb_market_cap_same_date_refresh": "同日刷新 PE、PB 与总市值",
}

_FORBIDDEN_MARKDOWN_TERMS = (
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

_MONEY_FIELDS = {
    "financial_metrics.revenue",
    "financial_metrics.net_profit",
    "financial_metrics.operating_cashflow",
    "financial_metrics.accounts_receivable",
    "financial_metrics.inventory",
    "financial_metrics.contract_liabilities",
    "financial_metrics.capex",
    "valuation_metrics.market_cap",
}


def render_research_report_v1_markdown(report: dict[str, Any]) -> str:
    """Render an accepted Research Report V1 payload as Chinese Markdown."""

    _assert_report_payload(report)
    _assert_no_secret_like_payload(report)
    code = _normalize_code(str(report.get("code", "")))
    company_name = _company_name(report, code)
    metrics = _metrics_by_field(report)
    quality = _dict_or_empty(report.get("data_quality_assessment"))

    lines: list[str] = [
        f"# {code} {company_name} 基本面研究报告 V1",
        "",
        "## 重要声明",
        "- 本报告仅用于基本面研究分析，不是买卖建议。",
        "- 本报告不提供价格目标。",
        "- 本报告不提供配置比例建议。",
        "- 本报告不包含短线交易判断。",
        "",
        "## 一句话结论",
        (
            f"{company_name}当前可以放在电网设备和电力自动化研究框架下讨论，收入、净利润、毛利率、ROE与估值指标"
            "具备候选级支撑，但这些字段仍不能等同于经人工复核的最终事实。"
        ),
        (
            "最大机会来自电网投资、国网 / 南网招标、特高压、配网和数字电网建设对调度系统、继电保护、"
            "电力信息通信等方向的需求牵引。"
        ),
        (
            "最大风险在于招标节奏、订单兑现、应收账款与经营现金流背离，以及合同负债能否持续提供订单可见度。"
        ),
        (
            "最大证据缺口是主营构成口径不清、主营业务仍缺官方来源支撑，估值数据日期也需要保持同日刷新。"
        ),
        "",
        "## 投研速读",
        (
            "- 核心机会：电网投资与国网 / 南网招标是最重要的需求路径，特高压、配网、数字电网、电力自动化、"
            "继电保护、调度系统和电力信息通信构成后续验证方向。"
        ),
        (
            "- 核心风险：行业景气不能自动转化为公司收入，需重点观察订单兑现、应收账款、经营现金流、合同负债"
            "和毛利率。"
        ),
        (
            "- 数据可信度：财务和估值字段主要是候选可信字段；主营构成、主营业务官方来源和评分/置信度差异仍有"
            "需人工复核或覆盖缺口。"
        ),
        (
            "- 下一步重点跟踪：国网 / 南网招标、特高压与配网项目节奏、数字电网招标转化、同日估值刷新、"
            "主营构成口径修正和现金回款质量。"
        ),
        "",
        "## 研究员判断",
        (
            f"当前证据支持将{code} {company_name}作为电网设备、电力自动化和数字电网相关公司的基本面研究样本，"
            "但暂不支持把行业政策和项目节奏直接写成公司已经兑现的收入或利润。"
        ),
        (
            "财务侧可以先围绕收入、净利润、毛利率、ROE、经营现金流、应收账款、存货、合同负债和资本开支建立观察框架；"
            "估值侧可以阅读 PE、PB 与总市值，但必须同时说明估值数据日期。"
        ),
        (
            "结论强度目前受三处限制：主营构成口径不清、主营业务缺少官方来源确认、评分/置信度差异只能作为只读提示。"
            "因此本报告更适合作为研究初稿和后续核验清单，而不是最终投资结论。"
        ),
        "",
        "## 数据质量说明",
    ]

    lines.extend(_render_data_quality(quality))
    lines.extend(
        [
            "",
            "## 宏观与行业逻辑",
            (
                "- 电网投资：这是国电南瑞电网设备研究框架中的核心需求路径，但只应作为后续跟踪变量，不能直接写成公司收入兑现。"
            ),
            (
                "- 国网 / 南网招标：招标节奏影响订单线索和收入转化节奏，需要与公司订单、回款和合同负债交叉验证。"
            ),
            (
                "- 特高压：特高压项目节奏可能带来电网自动化、继电保护、调度系统和信息通信需求，但仍需要公司层面证据。"
            ),
            (
                "- 配网：配网升级与新型电力系统建设相关，是需求路径之一，后续应跟踪项目节奏和中标信息。"
            ),
            (
                "- 数字电网：数字电网代表长期方向，但当前只能写成待验证假设，需要产品线、订单或分部收入支撑。"
            ),
            (
                "- 电力自动化、继电保护、调度系统、电力信息通信：这些方向与国电南瑞研究画像高度相关，"
                "但官方主营业务文本和主营构成仍需补强。"
            ),
            "",
            "## 公司基本面",
        ]
    )
    lines.extend(_render_company_fundamentals(metrics, quality))
    lines.extend(["", "## 机会分析"])
    lines.extend(_render_opportunities(report))
    lines.extend(["", "## 风险分析"])
    lines.extend(_render_risks(report, metrics))
    lines.extend(["", "## 证据缺口"])
    lines.extend(_render_evidence_gaps(report))
    lines.extend(["", "## 反证条件"])
    lines.extend(_render_rebuttal_conditions(report))
    lines.extend(["", "## 后续跟踪清单"])
    lines.extend(_render_follow_up_checklist(report))

    markdown = "\n".join(lines).rstrip() + "\n"
    _assert_no_forbidden_markdown_terms(markdown)
    _assert_no_secret_like_payload(markdown)
    return markdown


def write_research_report_v1_markdown(report: dict[str, Any], output_root: Path, timestamp: str) -> Path:
    """Write the rendered Markdown report under an explicit artifact root."""

    markdown = render_research_report_v1_markdown(report)
    code = _normalize_code(str(report.get("code", "")))
    timestamp_text = str(timestamp)
    if not _TIMESTAMP_RE.fullmatch(timestamp_text) or ".." in timestamp_text:
        raise ResearchReportArtifactBoundaryError("timestamp contains unsupported path characters")

    root = Path(output_root)
    root_resolved = root.resolve(strict=False)
    report_path = root / timestamp_text / code / MARKDOWN_OUTPUT_FILENAME
    report_resolved = report_path.resolve(strict=False)
    try:
        report_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ResearchReportArtifactBoundaryError("markdown report path escapes output root") from exc
    if report_resolved.name != MARKDOWN_OUTPUT_FILENAME or report_resolved.suffix != ".md":
        raise ResearchReportArtifactBoundaryError("writer may only write fundamental_research_report_v1.md")

    _assert_no_secret_like_payload(markdown)
    report_resolved.parent.mkdir(parents=True, exist_ok=True)
    report_resolved.write_text(markdown, encoding="utf-8")
    return report_resolved


def _render_data_quality(quality: dict[str, Any]) -> list[str]:
    auto_fields = _as_list(quality.get("auto_accepted_core_fields"))
    review_fields = _as_list(quality.get("manual_review_required_fields"))
    valuation = _dict_or_empty(quality.get("valuation_as_of_date_status"))
    business = _dict_or_empty(quality.get("business_composition_status"))
    main_business = _dict_or_empty(quality.get("main_business_status"))
    score_status = _dict_or_empty(quality.get("score_confidence_explainability_status"))

    return [
        f"- 候选可信字段：{_field_summary(auto_fields)}。这些字段可用于研究讨论，但不等同于经人工复核的最终事实。",
        f"- 需人工复核：{_field_names(review_fields)}。复核决定只记录工作流状态，不代表写入基准样本。",
        (
            f"- 估值数据日期：{_display_or_unavailable(valuation.get('as_of_date'))}"
            f"（{_evidence_text(valuation.get('evidence_label'))}；PE、PB 与总市值需要保持同日口径）。"
        ),
        (
            "- 主营构成："
            f"期间={_join_or_unavailable(business.get('periods_observed'))}；"
            f"分类口径覆盖={_coverage_text(business.get('classification_type_coverage'))}；"
            f"收入占比覆盖={_coverage_text(business.get('revenue_ratio_coverage'))}。"
            "当前结论仍受期间、分类口径、收入占比分母和来源覆盖限制。"
        ),
        (
            f"- 主营业务官方来源缺口：{_status_text(main_business.get('status'))}。"
            "不能把非官方文本或最大分部提示直接作为公司主营业务定论。"
        ),
        (
            f"- 评分/置信度提示：{_score_summary_text(score_status)}。"
            "本展示层只转述只读提示，不重算评分、不调整置信度。"
        ),
    ]


def _render_company_fundamentals(metrics: dict[str, dict[str, Any]], quality: dict[str, Any]) -> list[str]:
    fields = [
        "financial_metrics.revenue",
        "financial_metrics.net_profit",
        "financial_metrics.gross_margin",
        "financial_metrics.roe",
        "financial_metrics.operating_cashflow",
        "financial_metrics.accounts_receivable",
        "financial_metrics.inventory",
        "financial_metrics.contract_liabilities",
        "financial_metrics.capex",
        "valuation_metrics.pe_ttm",
        "valuation_metrics.pb",
        "valuation_metrics.market_cap",
    ]
    lines = [_metric_line(field, metrics.get(field, {})) for field in fields]
    valuation = _dict_or_empty(quality.get("valuation_as_of_date_status"))
    business = _dict_or_empty(quality.get("business_composition_status"))
    lines.append(
        f"- 估值数据日期：{_display_or_unavailable(valuation.get('as_of_date'))}（估值指标需同日刷新）。"
    )
    lines.append(
        "- 主营构成缺口：主营构成口径不清，"
        f"当前可见期间为{_join_or_unavailable(business.get('periods_observed'))}，"
        "分类口径和收入占比分母仍需官方口径确认。"
    )
    return lines


def _render_opportunities(report: dict[str, Any]) -> list[str]:
    by_title = _items_by_title(report.get("opportunity_analysis"))
    fallback_order = [
        "grid_investment_cycle",
        "digital_grid",
        "uhv_and_distribution_grid",
        "power_automation_and_relay_protection",
        "stable_operating_quality_candidate",
    ]
    templates = {
        "grid_investment_cycle": "当前证据支持把电网投资和国网 / 南网招标作为需求路径跟踪，仍需中标、订单、收入和回款验证。",
        "digital_grid": "数字电网是重要机会方向，但现阶段属于待验证假设，需要产品线、订单或分部收入证据。",
        "uhv_and_distribution_grid": "特高压与配网建设提供项目节奏线索，可作为后续跟踪变量，不应自动写成收入兑现。",
        "power_automation_and_relay_protection": "电力自动化、继电保护、调度系统和电力信息通信与公司画像相关，但主营业务官方来源和主营构成仍需补强。",
        "stable_operating_quality_candidate": "收入、净利润、毛利率、ROE和现金流等候选字段可用于检验经营质量，但仍需跨期确认。",
    }
    lines = []
    for index, title in enumerate(fallback_order, start=1):
        item = by_title.get(title, {})
        lines.append(
            f"{index}. **{_OPPORTUNITY_CN[title]}**：{templates[title]}（证据等级：{_evidence_text(item.get('evidence_label'))}）"
        )
    return lines


def _render_risks(report: dict[str, Any], metrics: dict[str, dict[str, Any]]) -> list[str]:
    by_title = _items_by_title(report.get("risk_analysis"))
    receivables = _format_metric_value(metrics.get("financial_metrics.accounts_receivable", {}), "financial_metrics.accounts_receivable")
    cashflow = _format_metric_value(metrics.get("financial_metrics.operating_cashflow", {}), "financial_metrics.operating_cashflow")
    contract = _format_metric_value(metrics.get("financial_metrics.contract_liabilities", {}), "financial_metrics.contract_liabilities")
    templates = {
        "tender_cadence_risk": "国网 / 南网招标节奏若放缓，会削弱电网设备需求路径。",
        "order_realization_risk": "行业需求若无法转化为公司订单、收入和回款，机会判断会下降。",
        "receivables_and_cashflow_risk": f"应收账款为{receivables}，经营现金流为{cashflow}，二者相对收入和利润的背离需要重点跟踪。",
        "gross_margin_pressure": "毛利率若受价格、成本或产品结构影响而压缩，会削弱经营质量判断。",
        "contract_liabilities_visibility_risk": f"合同负债为{contract}，若后续下降或无法支撑收入可见度，需要下调结论强度。",
        "business_composition_scope_risk": "主营构成期间、分类口径和收入占比分母不清，会限制分部结论。",
        "valuation_date_risk": "PE、PB和总市值若不是同日刷新，估值解释力会变弱。",
        "data_quality_risk": "候选字段、人工复核、评分/置信度和覆盖缺口共同限制当前报告强度。",
    }
    return [
        f"- **{_RISK_CN[title]}**：{text}（证据等级：{_evidence_text(by_title.get(title, {}).get('evidence_label'))}）"
        for title, text in templates.items()
    ]


def _render_evidence_gaps(report: dict[str, Any]) -> list[str]:
    gaps = _as_list(report.get("evidence_gaps"))
    if not gaps:
        return ["- 当前 artifact 未提供可直接展示数值。"]
    lines = []
    for gap in gaps:
        if not isinstance(gap, dict):
            continue
        field = _field_label(str(gap.get("field_path") or ""))
        status = _status_text(gap.get("status"))
        evidence = _evidence_text(gap.get("evidence_label"))
        lines.append(f"- {field}：{status}（证据等级：{evidence}），需要补充后才能增强结论。")
    return lines or ["- 当前 artifact 未提供可直接展示数值。"]


def _render_rebuttal_conditions(report: dict[str, Any]) -> list[str]:
    by_title = _items_by_title(report.get("rebuttal_conditions"))
    templates = {
        "revenue_growth_slowdown": "如果收入增速明显放缓，则会削弱当前判断。",
        "operating_cashflow_deterioration": "如果经营现金流继续弱于利润或收入，则会削弱当前判断。",
        "receivables_grow_faster_than_revenue": "如果应收账款增速快于收入且回款质量下降，则会削弱当前判断。",
        "contract_liabilities_decline": "如果合同负债下降或不能支撑后续收入可见度，则会削弱当前判断。",
        "gross_margin_compression": "如果毛利率跨期压缩，则会削弱当前判断。",
        "grid_tender_rhythm_weakens": "如果国网 / 南网招标节奏转弱，则会削弱当前判断。",
        "project_cadence_falls_short": "如果特高压、配网或数字电网项目节奏不及预期，则会削弱当前判断。",
        "business_composition_does_not_support_exposure": "如果经复核的主营构成不能支持电网设备和电力自动化暴露，则会削弱当前判断。",
        "valuation_date_stale_or_mismatched": "如果估值数据日期陈旧或 PE、PB、总市值日期不一致，则会削弱当前判断。",
    }
    lines = []
    for title, text in templates.items():
        evidence = _evidence_text(by_title.get(title, {}).get("evidence_label"))
        lines.append(f"- {text}（证据等级：{evidence}）")
    return lines


def _render_follow_up_checklist(report: dict[str, Any]) -> list[str]:
    variables = _as_list(report.get("follow_up_variables"))
    names = [item.get("variable") for item in variables if isinstance(item, dict)]
    if not names:
        names = list(_FOLLOW_UP_CN)
    lines = []
    seen = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        lines.append(f"- [ ] {_FOLLOW_UP_CN.get(str(name), str(name))}")
    return lines


def _metric_line(field_path: str, metric: dict[str, Any]) -> str:
    value = _format_metric_value(metric, field_path)
    evidence = _evidence_text(metric.get("evidence_label"))
    period = _metric_period_text(metric)
    return f"- {_field_label(field_path)}：{value}（{evidence}{period}）"


def _metric_period_text(metric: dict[str, Any]) -> str:
    report_period = metric.get("report_period")
    as_of_date = metric.get("as_of_date")
    if as_of_date:
        return f"，估值数据日期 {as_of_date}"
    if report_period:
        return f"，报告期 {report_period}"
    return ""


def _metrics_by_field(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    company = _dict_or_empty(report.get("company_fundamentals"))
    metrics: dict[str, dict[str, Any]] = {}
    for section in ("financial_metrics", "valuation_metrics"):
        for item in _as_list(company.get(section)):
            if isinstance(item, dict) and item.get("field_path"):
                metrics[str(item["field_path"])] = item
    return metrics


def _format_metric_value(metric: dict[str, Any], field_path: str) -> str:
    if not metric:
        return "当前 artifact 未提供可直接展示数值"
    value = metric.get("value")
    unit = metric.get("canonical_unit")
    display = metric.get("display_value")
    if value is None and display not in (None, ""):
        return _translate_display_value(display, field_path)
    if value is None:
        return "当前 artifact 未提供可直接展示数值"
    numeric = _to_float(value)
    if numeric is None:
        return str(value)
    if field_path in _MONEY_FIELDS or unit == "RMB yuan":
        return f"{numeric / 100_000_000:.2f}亿元"
    if unit == "percentage_point":
        return f"{numeric:.2f}%"
    if unit == "multiple" or field_path in {"valuation_metrics.pe_ttm", "valuation_metrics.pb"}:
        return f"{numeric:.2f}倍"
    return f"{numeric:.2f}"


def _field_summary(items: list[Any]) -> str:
    parts = []
    for item in items:
        if not isinstance(item, dict):
            continue
        field_path = str(item.get("field_path") or "")
        value = _format_metric_value(item, field_path)
        parts.append(f"{_field_label(field_path)}（{value}）")
    return "、".join(parts) if parts else "当前 artifact 未提供可直接展示数值"


def _field_names(items: list[Any]) -> str:
    names = [
        _field_label(str(item.get("field_path") or ""))
        for item in items
        if isinstance(item, dict) and item.get("field_path")
    ]
    return "、".join(names) if names else "当前 artifact 未提供可直接展示数值"


def _field_label(field_path: str) -> str:
    normalized = re.sub(r"business_composition\[\d+\]\.", "business_composition.", field_path)
    return _FIELD_CN.get(normalized, normalized or "未命名字段")


def _company_name(report: dict[str, Any], code: str) -> str:
    if code in _COMPANY_NAME_OVERRIDES:
        return _COMPANY_NAME_OVERRIDES[code]
    stock = _dict_or_empty(_dict_or_empty(report.get("company_fundamentals")).get("stock"))
    name = stock.get("stock_name")
    return str(name) if name else "未命名公司"


def _items_by_title(value: Any) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("title")): item
        for item in _as_list(value)
        if isinstance(item, dict) and item.get("title")
    }


def _evidence_text(label: Any) -> str:
    return _EVIDENCE_CN.get(str(label), "覆盖缺口")


def _status_text(status: Any) -> str:
    if status in (None, "", [], {}):
        return "当前 artifact 未提供可直接展示数值"
    status_text = str(status)
    translations = {
        "same_date_candidate_metadata_available": "同日候选元数据可用",
        "missing_or_mismatched": "缺失或日期不一致",
        "manual_review_required": "需人工复核",
        "official_source_gap": "缺少官方来源支撑",
        "review_facing_caveat": "复核提示项",
    }
    return translations.get(status_text, status_text)


def _coverage_text(value: Any) -> str:
    data = _dict_or_empty(value)
    if not data:
        return "当前 artifact 未提供可直接展示数值"
    available = data.get("available_count")
    total = data.get("candidate_count")
    ratio = data.get("coverage_ratio")
    if ratio is not None:
        numeric = _to_float(ratio)
        ratio_text = f"{numeric * 100:.1f}%" if numeric is not None else str(ratio)
    else:
        ratio_text = "当前 artifact 未提供可直接展示数值"
    if available is not None and total is not None:
        return f"{available}/{total}（{ratio_text}）"
    return ratio_text


def _score_summary_text(score_status: dict[str, Any]) -> str:
    score_summary = _dict_or_empty(score_status.get("score_summary"))
    confidence_summary = _dict_or_empty(score_status.get("confidence_summary"))
    score_delta = score_summary.get("score_delta")
    confidence_delta = confidence_summary.get("confidence_delta")
    pieces = []
    if score_delta is not None:
        pieces.append(f"评分差异 {score_delta}")
    if confidence_delta is not None:
        pieces.append(f"置信度差异 {confidence_delta}")
    return "；".join(pieces) if pieces else "当前 artifact 未提供可直接展示数值"


def _join_or_unavailable(value: Any) -> str:
    values = [str(item) for item in _as_list(value) if item not in (None, "")]
    return "、".join(values) if values else "当前 artifact 未提供可直接展示数值"


def _display_or_unavailable(value: Any) -> str:
    if value in (None, "", [], {}):
        return "当前 artifact 未提供可直接展示数值"
    return str(value)


def _translate_display_value(value: Any, field_path: str) -> str:
    text = str(value)
    numeric = _to_float(text.replace(",", "").rstrip("xX%"))
    if numeric is None:
        return text
    if field_path in _MONEY_FIELDS:
        return f"{numeric / 100_000_000:.2f}亿元"
    if text.endswith("%"):
        return f"{numeric:.2f}%"
    if text.endswith(("x", "X")):
        return f"{numeric:.2f}倍"
    return text


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _assert_no_forbidden_markdown_terms(markdown: str) -> None:
    for term in _FORBIDDEN_MARKDOWN_TERMS:
        if term in markdown:
            raise ResearchReportBuildError("rendered markdown contains forbidden trading advice term")
