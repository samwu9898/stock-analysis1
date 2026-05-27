# -*- coding: utf-8 -*-
"""Chinese Markdown presentation layer for Research Report V1.

This module is presentation-only. It consumes an already-built Research Report
V1 payload, selects an auditable presentation profile, and renders Markdown.
It does not call data providers, read environment variables, alter evidence
labels, or mutate the input report.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
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
    "002371": "北方华创",
    "002050": "三花智控",
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
    "auto_accepted_candidate": "候选可用字段",
    "manual_review_required": "需人工复核",
    "unsupported_assumption": "待验证假设",
    "coverage_caveat": "覆盖缺口",
    "forward_tracking_variable": "后续跟踪变量",
    "verified_fact": "已确认事实",
}

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

_FORBIDDEN_MARKDOWN_TERMS = (
    "买入",
    "卖出",
    "持有建议",
    "目标价",
    "仓位",
    "加仓",
    "减仓",
    "清仓",
    "止损",
    "止盈",
    "技术面交易信号",
    "K线",
    "确定性上涨",
    "必然兑现",
    "强烈推荐",
    "verified_fact",
    "已核验事实",
    "经复核事实",
)

_GENERIC_PROFILE_ID = "generic_fundamental_report"


@dataclass(frozen=True)
class ResearchReportPresentationProfile:
    """Presentation-only language and ordering profile."""

    profile_id: str
    display_name: str
    applicable_codes: tuple[str, ...]
    strategy_types: tuple[str, ...]
    keywords: tuple[str, ...]
    opportunity_paths: tuple[tuple[str, str], ...]
    risk_paths: tuple[tuple[str, str], ...]
    industry_transmission_paths: tuple[str, ...]
    follow_up_variables: tuple[str, ...]
    unsupported_claims: tuple[str, ...]
    evidence_gap_focus: tuple[str, ...]
    forbidden_terms_when_not_selected: tuple[str, ...] = ()


PRESENTATION_PROFILE_REGISTRY: dict[str, ResearchReportPresentationProfile] = {
    "stable_growth_grid_equipment": ResearchReportPresentationProfile(
        profile_id="stable_growth_grid_equipment",
        display_name="稳定增长 / 电网设备",
        applicable_codes=("600406",),
        strategy_types=("stable_growth",),
        keywords=(
            "电网投资",
            "国网 / 南网",
            "特高压",
            "配网",
            "数字电网",
            "电力自动化",
            "继电保护",
            "调度系统",
            "电力信息通信",
            "应收账款",
            "经营现金流",
            "合同负债",
        ),
        opportunity_paths=(
            ("grid_investment_cycle", "电网投资与招标"),
            ("digital_grid", "数字电网 / 调度 / 信息通信"),
            ("uhv_and_distribution_grid", "特高压 / 配网"),
            ("power_automation_and_relay_protection", "电力自动化 / 继电保护"),
            ("stable_operating_quality_candidate", "经营质量候选支撑"),
        ),
        risk_paths=(
            ("receivables_and_cashflow_risk", "应收账款与经营现金流"),
            ("tender_cadence_risk", "招标与订单兑现"),
            ("gross_margin_pressure", "毛利率压力"),
            ("contract_liabilities_visibility_risk", "合同负债与订单可见度"),
            ("business_composition_scope_risk", "主营构成口径"),
            ("valuation_date_risk", "估值数据日期"),
        ),
        industry_transmission_paths=(
            "电网投资与招标先影响需求入口，再通过公司订单、交付、收入、毛利率和回款验证。",
            "数字电网、调度系统和信息通信只能作为待验证方向，需公司产品线、订单或收入证据支撑。",
            "特高压 / 配网是项目节奏变量，不自动等于公司收入兑现。",
        ),
        follow_up_variables=(
            "国网 / 南网招标节奏",
            "特高压 / 配网项目进度",
            "数字电网、调度系统、信息通信相关披露",
            "应收账款、经营现金流、合同负债、毛利率、ROE、资本开支",
            "估值数据日期和业务构成口径变化",
        ),
        unsupported_claims=(
            "不能把电网投资直接写成公司订单或收入兑现。",
            "不能把国网 / 南网招标节奏直接写成公司确定性增长。",
            "不能把合同负债直接写成 backlog。",
            "不能把单期经营现金流改善写成长周期现金流稳定。",
            "不能把主营构成衍生提示写成官方主营业务事实。",
        ),
        evidence_gap_focus=(
            "招标、订单、收入、毛利率、现金流之间的公司级传导证据",
            "主营构成期间、分类口径、收入占比和分母口径",
            "主营业务官方来源",
            "估值数据日期与报告日期一致性",
        ),
        forbidden_terms_when_not_selected=("电网投资", "国网 / 南网", "特高压", "配网", "数字电网", "电力自动化"),
    ),
    "semiconductor_equipment_cycle": ResearchReportPresentationProfile(
        profile_id="semiconductor_equipment_cycle",
        display_name="半导体周期 / 设备",
        applicable_codes=("002371",),
        strategy_types=("semiconductor_cycle",),
        keywords=(
            "半导体设备",
            "晶圆厂资本开支",
            "国产替代",
            "设备订单",
            "存货",
            "研发投入",
            "毛利率",
            "客户验证",
            "产线扩张",
            "周期波动",
        ),
        opportunity_paths=(
            ("domestic_fab_capex", "国内晶圆厂 capex"),
            ("localization_and_tool_adoption", "国产替代和设备导入"),
            ("rd_conversion", "研发投入转化"),
            ("orders_inventory_contract_liabilities_validation", "订单 / 存货 / 合同负债验证"),
            ("product_mix_and_margin_improvement", "产品结构和毛利率改善"),
        ),
        risk_paths=(
            ("semiconductor_cycle_downturn", "半导体周期下行"),
            ("order_realization_shortfall", "订单兑现不及预期"),
            ("inventory_revenue_mismatch", "存货和收入错配"),
            ("rd_conversion_failure", "研发投入无法转化"),
            ("gross_margin_pressure", "毛利率压力"),
            ("customer_validation_gap", "客户验证不足"),
            ("capex_cadence_slowdown", "capex 节奏放缓"),
        ),
        industry_transmission_paths=(
            "国内晶圆厂 capex 是行业需求入口，但必须再验证公司设备订单、交付、验收、收入确认和回款。",
            "国产替代和设备导入是研究假设，不能直接写成公司收入兑现。",
            "研发投入需要产品进展、客户验证和商业化收入证据，不能直接写成技术壁垒。",
        ),
        follow_up_variables=(
            "国内晶圆厂资本开支节奏",
            "设备订单、合同负债、存货、收入确认和回款",
            "研发投入、研发费用率、产品导入和客户验证进度",
            "毛利率、产品结构、资本开支、经营现金流",
            "半导体周期、产线扩张和客户扩产节奏",
        ),
        unsupported_claims=(
            "不能把国产替代叙事直接写成收入兑现。",
            "不能把研发投入直接写成技术壁垒。",
            "不能把库存变化直接写成需求强弱。",
            "不能把 capex 直接写成订单。",
            "不能把客户验证、导入或认证直接写成批量收入。",
            "不能把合同负债直接写成 backlog。",
        ),
        evidence_gap_focus=(
            "设备订单、交付、验收、收入确认和回款之间的公司级证据",
            "研发投入对应产品进展、客户导入和商业化收入证据",
            "存货构成、周转、跌价风险和收入错配证据",
            "晶圆厂 capex 到公司订单的传导证据",
        ),
        forbidden_terms_when_not_selected=("半导体设备", "晶圆厂 capex", "晶圆厂资本开支", "国产替代", "设备订单"),
    ),
    "advanced_manufacturing_thermal_management": ResearchReportPresentationProfile(
        profile_id="advanced_manufacturing_thermal_management",
        display_name="先进制造 / 热管理",
        applicable_codes=("002050",),
        strategy_types=("advanced_manufacturing_growth",),
        keywords=(
            "热管理",
            "制冷控制",
            "汽车零部件",
            "新能源车",
            "机器人 / 新业务",
            "客户结构",
            "毛利率",
            "存货",
            "应收账款",
            "资本开支",
            "新业务收入占比",
        ),
        opportunity_paths=(
            ("nev_thermal_management", "新能源车热管理"),
            ("refrigeration_control_base", "制冷控制基本盘"),
            ("customer_and_product_mix_upgrade", "客户和产品结构升级"),
            ("new_business_optionality", "新业务可选项"),
            ("margin_and_operating_quality_candidate", "毛利率和经营质量候选支撑"),
        ),
        risk_paths=(
            ("auto_demand_volatility", "汽车需求波动"),
            ("customer_concentration", "客户集中度"),
            ("new_business_realization_shortfall", "新业务兑现不足"),
            ("gross_margin_pressure", "毛利率压力"),
            ("inventory_receivable_capex_expansion_risk", "存货 / 应收 / capex 扩张风险"),
            ("new_business_revenue_share_gap", "新业务收入占比证据不足"),
        ),
        industry_transmission_paths=(
            "新能源车热管理需要收入、订单、客户、毛利率和回款证据验证。",
            "制冷控制基本盘应独立观察收入稳定性、毛利率和现金流，不能代理新业务兑现。",
            "机器人 / 新业务只能作为可选项，需收入占比、订单、客户、量产、交付和收款证据。",
        ),
        follow_up_variables=(
            "新能源车销量和热管理单车价值量相关披露",
            "制冷控制业务收入、毛利率和现金流",
            "客户结构、产品结构、新业务收入占比",
            "存货、应收账款、资本开支、经营现金流、ROE",
            "机器人 / 新业务订单、客户、量产、交付和收入确认",
        ),
        unsupported_claims=(
            "不能把机器人概念直接写成已兑现收入。",
            "不能把新业务叙事直接写成利润增长。",
            "不能把客户传闻写成已确认事实。",
            "不能把行业空间直接写成公司确定性。",
            "不能把定点、认证或客户导入直接写成批量收入。",
            "不能把制冷控制和汽车热管理数据代理为机器人业务兑现。",
        ),
        evidence_gap_focus=(
            "新能源车热管理收入、订单、客户、毛利率和回款证据",
            "制冷控制基本盘的收入稳定性、毛利率和现金流证据",
            "机器人 / 新业务的收入占比、订单、客户、量产、交付和收款证据",
            "客户集中度、客户结构升级和产品结构改善证据",
            "存货、应收、资本开支扩张是否与收入和现金流匹配",
        ),
        forbidden_terms_when_not_selected=("热管理", "制冷控制", "汽车零部件", "新能源车", "机器人 / 新业务", "新业务收入占比"),
    ),
    _GENERIC_PROFILE_ID: ResearchReportPresentationProfile(
        profile_id=_GENERIC_PROFILE_ID,
        display_name="通用基本面报告",
        applicable_codes=(),
        strategy_types=(),
        keywords=("财务质量", "估值", "主营构成", "数据质量", "风险", "证据缺口"),
        opportunity_paths=(
            ("financial_quality", "财务质量验证"),
            ("valuation_context", "估值口径检查"),
            ("business_composition_review", "主营构成复核"),
            ("data_quality_completion", "数据质量补全"),
        ),
        risk_paths=(
            ("data_quality_risk", "数据质量风险"),
            ("valuation_date_risk", "估值数据日期"),
            ("business_composition_scope_risk", "主营构成口径"),
            ("cashflow_and_receivable_risk", "现金流与应收风险"),
        ),
        industry_transmission_paths=(
            "当前无法可靠选择行业 profile，因此只保留通用基本面阅读框架。",
            "报告优先检查财务质量、估值口径、主营构成、数据质量、风险和证据缺口。",
        ),
        follow_up_variables=(
            "收入、净利润、毛利率、ROE、经营现金流",
            "应收账款、存货、合同负债、资本开支",
            "PE、PB、总市值和估值数据日期",
            "主营构成期间、分类口径、收入占比和官方主营业务来源",
            "需要人工复核的证据缺口",
        ),
        unsupported_claims=(
            "无法可靠识别 profile 时，不写行业专属强判断。",
            "不把主题词、新闻词或关键词命中写成行业框架。",
            "不为了显得具体而套用错误行业语言。",
        ),
        evidence_gap_focus=(
            "财务质量字段可信度",
            "估值日期和口径",
            "主营构成缺口",
            "数据质量和人工复核事项",
        ),
    ),
}


def select_presentation_profile(report: dict[str, Any]) -> dict[str, Any]:
    """Select a presentation profile and return auditable metadata.

    The returned dict contains the profile fields plus these metadata keys:
    ``presentation_profile_id``, ``presentation_profile_selected_by``,
    ``fallback_reason``, and ``profile_selection_warning``.
    """

    code = _normalize_code(str(report.get("code", "")))
    code_profile = _profile_for_code(code)
    strategy_value, strategy_source = _primary_strategy(report)
    strategy_profile = _profile_for_strategy(strategy_value)
    evidence_strategy = _first_text(
        report.get("evidence_pack_strategy_type"),
        _get_nested(report, ("evidence_pack", "strategy_type")),
    )
    p1_strategy = _first_text(
        report.get("p1_strategy_type"),
        _get_nested(report, ("research_intelligence_p1", "strategy_type")),
        _get_nested(report, ("research_intelligence_p1", "strategy_type_expected")),
    )
    evidence_profile = _profile_for_strategy(evidence_strategy) or _profile_for_strategy(p1_strategy)

    warning: str | None = None
    fallback_reason: str | None = None
    selected_by: str
    profile: ResearchReportPresentationProfile

    if strategy_profile and code_profile and strategy_profile.profile_id != code_profile.profile_id:
        profile = PRESENTATION_PROFILE_REGISTRY[_GENERIC_PROFILE_ID]
        selected_by = "fallback"
        warning = "classifier_code_profile_conflict"
        fallback_reason = (
            f"classifier/code conflict: {strategy_source}={strategy_value}, "
            f"code_whitelist={code_profile.profile_id}"
        )
    elif strategy_profile:
        profile = strategy_profile
        selected_by = strategy_source or "classifier_result"
    elif code_profile:
        profile = code_profile
        selected_by = "code_whitelist"
    elif evidence_profile:
        profile = evidence_profile
        selected_by = "evidence_pack_or_p1_strategy"
    else:
        profile = PRESENTATION_PROFILE_REGISTRY[_GENERIC_PROFILE_ID]
        selected_by = "fallback"
        fallback_reason = "no reliable strategy_type, code whitelist, evidence_pack, or P1.1 strategy match"

    result = asdict(profile)
    result.update(
        {
            "presentation_profile_id": profile.profile_id,
            "presentation_profile_selected_by": selected_by,
            "fallback_reason": fallback_reason,
            "profile_selection_warning": warning,
            "strategy_type_expected": _first_text(report.get("strategy_type_expected")),
            "classifier_strategy_type": strategy_value,
            "code_whitelist_match": code_profile.profile_id if code_profile else None,
            "evidence_pack_strategy_type": evidence_strategy,
            "p1_strategy_type": p1_strategy,
        }
    )
    return result


def render_research_report_v1_markdown(report: dict[str, Any]) -> str:
    """Render an accepted Research Report V1 payload as Chinese Markdown."""

    _assert_report_payload(report)
    _assert_no_secret_like_payload(report)

    code = _normalize_code(str(report.get("code", "")))
    company_name = _company_name(report, code)
    profile_selection = select_presentation_profile(report)
    profile = PRESENTATION_PROFILE_REGISTRY[str(profile_selection["presentation_profile_id"])]
    metrics = _metrics_by_field(report)
    quality = _dict_or_empty(report.get("data_quality_assessment"))

    lines: list[str] = [
        f"# {code} {company_name} 基本面研究报告 V1",
        "",
        "## 重要声明",
        "- 本报告仅用于基本面研究，不构成交易建议。",
        "- 本报告不提供价格预测、配置比例或技术面信号。",
        "- 所有判断都必须服从 evidence label、数据质量说明和证据缺口。",
        "",
        "## Presentation Profile",
        f"- presentation_profile_id: `{profile_selection['presentation_profile_id']}`",
        f"- presentation_profile_selected_by: `{profile_selection['presentation_profile_selected_by']}`",
        f"- fallback_reason: `{profile_selection.get('fallback_reason') or 'none'}`",
        f"- profile_selection_warning: `{profile_selection.get('profile_selection_warning') or 'none'}`",
        "",
        "## 一句话结论",
        _one_sentence_conclusion(company_name, profile, profile_selection),
        "",
        "## 投研速读",
        f"- 展示框架：{profile.display_name}。",
        f"- 行业关键词：{_join(profile.keywords)}。",
        f"- 机会排序：{_join(_path_titles(profile.opportunity_paths))}。",
        f"- 风险排序：{_join(_path_titles(profile.risk_paths))}。",
        "- 当前报告只把行业逻辑写成研究框架和后续验证路径，不写成公司已经兑现的事实。",
        "",
        "## 研究员判断",
        _research_judgement(company_name, profile),
        "",
        "## 数据质量说明",
    ]
    lines.extend(_render_data_quality(quality))
    lines.extend(["", "## 宏观与行业逻辑"])
    lines.extend(f"- {item}" for item in profile.industry_transmission_paths)
    lines.extend(["", "## 公司基本面"])
    lines.extend(_render_company_fundamentals(metrics, quality))
    lines.extend(["", "## 机会分析"])
    lines.extend(_render_profile_paths(profile.opportunity_paths, report.get("opportunity_analysis")))
    lines.extend(["", "## 风险分析"])
    lines.extend(_render_profile_paths(profile.risk_paths, report.get("risk_analysis")))
    lines.extend(["", "## 证据缺口"])
    lines.extend(_render_evidence_gaps(report, profile))
    lines.extend(["", "## 反证条件"])
    lines.extend(_render_rebuttal_conditions(report, profile))
    lines.extend(["", "## 后续跟踪清单"])
    lines.extend(f"- [ ] {item}" for item in profile.follow_up_variables)

    markdown = "\n".join(lines).rstrip() + "\n"
    _assert_no_nonselected_profile_terms(markdown, profile.profile_id)
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


def _one_sentence_conclusion(
    company_name: str,
    profile: ResearchReportPresentationProfile,
    selection: dict[str, Any],
) -> str:
    if profile.profile_id == _GENERIC_PROFILE_ID:
        return (
            f"{company_name} 当前无法可靠选择行业展示 profile，报告应先保留为通用基本面框架，"
            "重点检查财务质量、估值、主营构成、数据质量、风险和证据缺口。"
        )
    warning = selection.get("profile_selection_warning")
    warning_text = "；profile selection 存在冲突，已使用 fallback" if warning else ""
    return (
        f"{company_name} 当前适用 `{profile.profile_id}` 展示框架，报告应围绕"
        f"{_join(profile.keywords[:4])}组织研究语言，但所有机会都必须继续通过公司级证据验证{warning_text}。"
    )


def _research_judgement(company_name: str, profile: ResearchReportPresentationProfile) -> str:
    if profile.profile_id == _GENERIC_PROFILE_ID:
        return (
            f"{company_name} 的行业展示框架暂不强行归类；当前判断只适合形成财务质量、估值口径、"
            "主营构成和数据缺口清单。"
        )
    return (
        f"{company_name} 可以按“{profile.display_name}”展示框架阅读，但 profile 只决定表达顺序和行业语言，"
        "不改变 evidence label，不把候选字段写成已确认事实，也不把行业叙事写成公司兑现。"
    )


def _render_data_quality(quality: dict[str, Any]) -> list[str]:
    auto_fields = _as_list(quality.get("auto_accepted_core_fields"))
    manual_fields = _as_list(quality.get("manual_review_required_fields"))
    valuation = _dict_or_empty(quality.get("valuation_as_of_date_status"))
    business = _dict_or_empty(quality.get("business_composition_status"))
    main_business = _dict_or_empty(quality.get("main_business_status"))

    return [
        f"- 候选可用字段：{_field_names(auto_fields)}。这些字段可用于基础研究观察，但不是已确认事实。",
        f"- 需人工复核字段：{_field_names(manual_fields)}。这些缺口会限制强结论。",
        f"- 估值数据日期：{_display_or_unavailable(valuation.get('as_of_date'))}，PE、PB、总市值必须按同日口径阅读。",
        (
            "- 主营构成："
            f"期间={_join_or_unavailable(business.get('periods_observed'))}；"
            f"分类口径覆盖={_coverage_text(business.get('classification_type_coverage'))}；"
            f"收入占比覆盖={_coverage_text(business.get('revenue_ratio_coverage'))}。"
        ),
        f"- 主营业务官方来源：{_status_text(main_business.get('status'))}。",
        "- 数据质量 caveat 必须保留；profile 不能隐藏复核缺口，也不能把候选字段升级为已确认事实。",
    ]


def _render_company_fundamentals(metrics: dict[str, dict[str, Any]], quality: dict[str, Any]) -> list[str]:
    del quality
    field_order = (
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
    )
    lines = []
    for field_path in field_order:
        metric = metrics.get(field_path, {})
        lines.append(
            f"- {_field_label(field_path)}：{_format_metric_value(metric, field_path)}"
            f"（证据等级：{_evidence_text(metric.get('evidence_label'))}）。"
        )
    lines.append("- 合同负债只能作为订单可见度线索，不等于 backlog。")
    lines.append("- 资本开支只能作为投入节奏线索，不等于订单、产能释放、收入或增长兑现。")
    return lines


def _render_profile_paths(paths: tuple[tuple[str, str], ...], source_items: Any) -> list[str]:
    by_title = _items_by_title(source_items)
    lines = []
    for index, (path_id, title) in enumerate(paths, start=1):
        evidence = _evidence_text(by_title.get(path_id, {}).get("evidence_label"))
        lines.append(f"{index}. **{title}**：按 profile 排序展示；证据等级：{evidence}。")
    return lines


def _render_evidence_gaps(report: dict[str, Any], profile: ResearchReportPresentationProfile) -> list[str]:
    lines = [f"- profile 重点：{item}。" for item in profile.evidence_gap_focus]
    for gap in _as_list(report.get("evidence_gaps")):
        if not isinstance(gap, dict):
            continue
        field = _field_label(str(gap.get("field_path") or ""))
        status = _status_text(gap.get("status"))
        evidence = _evidence_text(gap.get("evidence_label"))
        lines.append(f"- {field}：{status}；证据等级：{evidence}。")
    return lines or ["- 当前 artifact 未提供可直接展示的证据缺口。"]


def _render_rebuttal_conditions(report: dict[str, Any], profile: ResearchReportPresentationProfile) -> list[str]:
    del report
    return [f"- {claim}" for claim in profile.unsupported_claims]


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
    unit = metric.get("canonical_unit") or metric.get("unit")
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


def _field_names(items: list[Any]) -> str:
    names = [
        _field_label(str(item.get("field_path") or ""))
        for item in items
        if isinstance(item, dict) and item.get("field_path")
    ]
    return "、".join(names) if names else "当前 artifact 未提供可直接展示字段"


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


def _primary_strategy(report: dict[str, Any]) -> tuple[str | None, str | None]:
    expected = _first_text(report.get("strategy_type_expected"))
    if expected:
        return expected, "strategy_type_expected"
    classifier = _first_text(
        _get_nested(report, ("classifier_result", "strategy_type")),
        _get_nested(report, ("company_fundamentals", "stock", "strategy_type")),
        report.get("strategy_type"),
    )
    if classifier:
        return classifier, "classifier_result"
    return None, None


def _profile_for_code(code: str) -> ResearchReportPresentationProfile | None:
    for profile in PRESENTATION_PROFILE_REGISTRY.values():
        if code in profile.applicable_codes:
            return profile
    return None


def _profile_for_strategy(strategy: str | None) -> ResearchReportPresentationProfile | None:
    if not strategy:
        return None
    matches = [
        profile
        for profile in PRESENTATION_PROFILE_REGISTRY.values()
        if strategy in profile.strategy_types
    ]
    return matches[0] if len(matches) == 1 else None


def _path_titles(paths: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    return tuple(title for _, title in paths)


def _evidence_text(label: Any) -> str:
    text = str(label or "")
    if text == "verified_fact":
        return "已确认事实"
    return _EVIDENCE_CN.get(text, "覆盖缺口")


def _status_text(status: Any) -> str:
    if status in (None, "", [], {}):
        return "当前 artifact 未提供可直接展示状态"
    translations = {
        "same_date_candidate_metadata_available": "同日候选元数据可用",
        "missing_or_mismatched": "缺失或日期不一致",
        "manual_review_required": "需人工复核",
        "official_source_gap": "缺少官方来源支撑",
        "review_facing_caveat": "复核提示项",
    }
    return translations.get(str(status), str(status))


def _coverage_text(value: Any) -> str:
    data = _dict_or_empty(value)
    if not data:
        return "当前 artifact 未提供可直接展示覆盖率"
    available = data.get("available_count")
    total = data.get("candidate_count")
    ratio = data.get("coverage_ratio")
    numeric = _to_float(ratio)
    ratio_text = f"{numeric * 100:.1f}%" if numeric is not None else "当前 artifact 未提供可直接展示覆盖率"
    if available is not None and total is not None:
        return f"{available}/{total}（{ratio_text}）"
    return ratio_text


def _join_or_unavailable(value: Any) -> str:
    values = [str(item) for item in _as_list(value) if item not in (None, "")]
    return "、".join(values) if values else "当前 artifact 未提供可直接展示内容"


def _display_or_unavailable(value: Any) -> str:
    if value in (None, "", [], {}):
        return "当前 artifact 未提供可直接展示内容"
    return str(value)


def _join(values: Any) -> str:
    items = [str(item) for item in values if item not in (None, "")]
    return "、".join(items) if items else "当前 artifact 未提供可直接展示内容"


def _first_text(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _get_nested(value: Any, path: tuple[str, ...]) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


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
            raise ResearchReportBuildError("rendered markdown contains forbidden trading advice or fact-promotion term")


def _assert_no_nonselected_profile_terms(markdown: str, selected_profile_id: str) -> None:
    for profile_id, profile in PRESENTATION_PROFILE_REGISTRY.items():
        if profile_id in {selected_profile_id, _GENERIC_PROFILE_ID}:
            continue
        for term in profile.forbidden_terms_when_not_selected:
            if term and term in markdown:
                raise ResearchReportBuildError("rendered markdown contains non-selected profile-specific term")
