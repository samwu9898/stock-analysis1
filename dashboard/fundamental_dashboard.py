# -*- coding: utf-8 -*-
"""Local Streamlit dashboard for Fundamental AI Analyst reports."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.fundamental_skill import dashboard_helpers as helpers
from src.fundamental_skill.real_stock_runner import run_real_stock


OUTPUT_DIR = PROJECT_ROOT / "output"
SUPPORTED_CODES = ("002050", "000426", "300308", "002371", "601899", "603993")


st.set_page_config(page_title="A股基本面 AI 分析看板", layout="wide")


def stock_selector_table_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "股票代码": row.get("stock_code"),
            "公司名称": row.get("stock_name"),
            "AI基本面观点": helpers.ai_view_label(row.get("fundamental_view")),
            "分析框架": helpers.format_strategy_type(row.get("strategy_type")),
            "已有AI报告": row.get("has_ai_report"),
            "已有规则结果": row.get("has_fundamental"),
        }
        for row in rows
    ]


def badge(text: object, kind: str = "neutral") -> str:
    palette = {
        "supportive_for_further_evaluation": ("#e7f6ed", "#166534"),
        "neutral_requires_more_evidence": ("#eef2ff", "#3730a3"),
        "not_supportive": ("#fee2e2", "#991b1b"),
        "insufficient_data": ("#fef3c7", "#92400e"),
        "supportive": ("#e7f6ed", "#166534"),
        "neutral": ("#eef2ff", "#3730a3"),
        "negative": ("#fee2e2", "#991b1b"),
        "high": ("#dcfce7", "#166534"),
        "medium": ("#fef3c7", "#92400e"),
        "low": ("#fee2e2", "#991b1b"),
    }
    bg, fg = palette.get(kind, ("#f3f4f6", "#374151"))
    return (
        f"<span style='display:inline-block;padding:0.2rem 0.55rem;"
        f"border-radius:999px;background:{bg};color:{fg};font-weight:700;"
        f"font-size:0.85rem'>{text or '-'}</span>"
    )


def show_table(rows: list[dict], empty_message: str) -> None:
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info(empty_message)


def render_stock_selector() -> str | None:
    rows = helpers.scan_available_stocks(OUTPUT_DIR)
    codes = [str(row.get("stock_code")) for row in rows if row.get("stock_code")]

    st.subheader("股票选择")
    if rows:
        st.dataframe(
            stock_selector_table_rows(rows),
            use_container_width=True,
            hide_index=True,
        )

    col1, col2 = st.columns([2, 1])
    with col1:
        selected = st.selectbox("选择股票", options=codes) if codes else None
    with col2:
        manual = st.text_input("手动输入股票代码", placeholder="002050")
    normalized = helpers.normalize_stock_code(manual)
    return normalized or selected


def render_pipeline_tools() -> None:
    with st.expander("规则流水线工具", expanded=False):
        st.caption("仅运行既有确定性基本面流水线，不生成 AI 报告。")
        with st.form("run_real_stock_form"):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                code = st.text_input("股票代码", value="002050", placeholder="002050")
            with col2:
                force_refresh = st.checkbox("强制刷新", value=False)
            with col3:
                submitted = st.form_submit_button("运行")

        if not submitted:
            return
        normalized = helpers.normalize_stock_code(code)
        if normalized not in SUPPORTED_CODES:
            st.error("当前看板暂不支持该股票代码。")
            return
        with st.spinner("正在运行既有基本面流水线..."):
            try:
                output_path = OUTPUT_DIR / f"fundamental_{normalized}.json"
                run_real_stock(normalized, output=str(output_path), force_refresh=force_refresh)
            except Exception as exc:
                st.error(f"分析失败：{exc}")
                return
        st.success(f"已保存 output/fundamental_{normalized}.json 和 output/raw_{normalized}.json")


def render_missing_ai_report(stock_code: str, bundle: dict[str, Any]) -> None:
    st.warning("尚未生成 AI 报告。看板不会自动调用 API 生成报告。")
    st.code(
        f"python -m src.fundamental_skill.ai_analyst.runner --code {stock_code} --mode prompt_only",
        language="bash",
    )
    st.write("如需 AI 报告，请先用生成的 prompt 离线创建报告文件。")
    prompt = bundle.get("ai_prompt") or helpers.prompt_preview(stock_code, OUTPUT_DIR)
    if prompt:
        with st.expander("Prompt 预览", expanded=False):
            st.markdown(prompt)
    else:
        st.info("尚未找到 ai_prompt 文件。")


def render_executive_summary(ai_report: dict, fundamental: dict | None, evidence_pack: dict | None) -> None:
    stock = (evidence_pack or {}).get("stock") if isinstance((evidence_pack or {}).get("stock"), dict) else {}
    st.subheader("AI Executive Summary")
    cols = st.columns(6)
    cols[0].metric("stock_code", ai_report.get("stock_code") or "-")
    cols[1].metric("stock_name", ai_report.get("stock_name") or "-")
    cols[2].markdown(badge(stock.get("strategy_type") or (fundamental or {}).get("strategy_type"), "neutral"), unsafe_allow_html=True)
    cols[2].caption("strategy_type")
    cols[3].markdown(badge(ai_report.get("fundamental_view"), str(ai_report.get("fundamental_view"))), unsafe_allow_html=True)
    cols[3].caption("fundamental_view")
    cols[4].markdown(badge((fundamental or {}).get("confidence"), str((fundamental or {}).get("confidence"))), unsafe_allow_html=True)
    cols[4].caption("confidence")
    cols[5].metric("score", (fundamental or {}).get("fundamental_score") if (fundamental or {}).get("fundamental_score") is not None else "-")
    st.write(helpers.clean_ai_report_text(ai_report, "executive_summary", "-") or "-")


def render_fundamental_view(ai_report: dict, fundamental: dict | None) -> None:
    st.subheader("Fundamental View")
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(badge(ai_report.get("fundamental_view"), str(ai_report.get("fundamental_view"))), unsafe_allow_html=True)
    col1.caption("AI fundamental_view")
    col2.markdown(badge((fundamental or {}).get("status"), str((fundamental or {}).get("status"))), unsafe_allow_html=True)
    col2.caption("deterministic status")
    col3.markdown(badge((fundamental or {}).get("confidence"), str((fundamental or {}).get("confidence"))), unsafe_allow_html=True)
    col3.caption("deterministic confidence")
    col4.metric("fundamental_score", (fundamental or {}).get("fundamental_score") if (fundamental or {}).get("fundamental_score") is not None else "-")
    st.write(helpers.clean_ai_report_text(ai_report, "final_summary", "-") or "-")


def render_evidence_classification(ai_report: dict) -> None:
    st.subheader("Evidence Classification")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Supporting**")
        show_table(helpers.evidence_rows(ai_report, "supporting_evidence"), "No supporting evidence.")
    with col2:
        st.markdown("**Limiting**")
        show_table(helpers.evidence_rows(ai_report, "limiting_evidence"), "No limiting evidence.")
    with col3:
        st.markdown("**Unknown / Missing**")
        show_table(helpers.evidence_rows(ai_report, "unknown_or_missing_evidence"), "No unknown evidence.")


def render_analysis_report(ai_report: dict) -> None:
    st.subheader("AI Analysis Report")
    sections = [
        ("Business Analysis", "business_analysis"),
        ("Financial Quality", "financial_quality_analysis"),
        ("Valuation", "valuation_analysis"),
        ("Industry / Cycle", "industry_cycle_analysis"),
        ("Final Summary", "final_summary"),
    ]
    for title, key in sections:
        st.markdown(f"**{title}**")
        st.write(helpers.clean_ai_report_text(ai_report, key, "-") or "-")

    st.markdown("**Risk Analysis**")
    show_table(helpers.as_list(ai_report.get("risk_analysis")), "No risk analysis.")
    st.markdown("**Data Limitations**")
    show_table([{"data_limitation": item} for item in helpers.as_list(ai_report.get("data_limitations"))], "No data limitations.")
    st.markdown("**Invalidation Watch**")
    show_table(helpers.as_list(ai_report.get("invalidation_watch")), "No invalidation watch.")


def render_safety_status(status: dict[str, Any]) -> None:
    st.subheader("Safety / Schema Status")
    cols = st.columns(4)
    cols[0].metric("schema_valid", status.get("schema_valid"))
    cols[1].metric("safety_safe", status.get("safety_safe"))
    cols[2].metric("restricted_terms_count", status.get("restricted_terms_count"))
    cols[3].metric("report_quality_status", status.get("report_quality_status"))
    if not status.get("schema_valid"):
        st.error(f"Schema errors: {status.get('schema_errors')}")
    if not status.get("safety_safe"):
        st.error(f"Restricted terms detected: {status.get('blocked_terms')}")
    if status.get("garbled_text_detected"):
        st.warning("部分 AI 自由文本字段损坏，当前报告使用结构化 evidence fallback 生成。建议重新生成 ai_report JSON。")
        with st.expander("Garbled Text Findings", expanded=False):
            st.json(status.get("garbled_text_findings") or [], expanded=False)


def render_evidence_pack_viewer(evidence_pack: dict | None) -> None:
    with st.expander("审计材料：完整证据包", expanded=False):
        st.markdown("**摘要**")
        show_table([helpers.evidence_pack_summary(evidence_pack)], "No evidence pack summary.")
        st.markdown("**数据来源追踪**")
        show_table(helpers.as_list((evidence_pack or {}).get("source_trace_summary")), "No source trace summary.")
        st.markdown("**缺失字段**")
        show_table(helpers.as_list((evidence_pack or {}).get("missing_fields")), "No missing fields.")
        st.markdown("**数据限制**")
        show_table([{"data_limitation": item} for item in helpers.as_list((evidence_pack or {}).get("data_limitations"))], "No data limitations.")
        with st.expander("完整证据包 JSON", expanded=False):
            st.json(evidence_pack or {}, expanded=False)


def render_raw_data_viewer(fundamental: dict | None, raw: dict | None) -> None:
    with st.expander("审计材料：规则结果与原始数据", expanded=False):
        st.markdown("**历史规则表格**")
        summary = helpers.fundamental_analyst_summary(fundamental)
        if summary:
            st.markdown("**分析师摘要**")
            st.write(summary)
        show_table(helpers.invalidation_condition_rows(fundamental), "No invalidation conditions.")
        show_table(helpers.risk_flag_rows(fundamental), "No risk flags.")
        show_table(helpers.must_track_indicator_rows(fundamental), "No deterministic must-track indicators.")
        show_table([helpers.financial_quality_row(fundamental, raw)], "No financial quality data.")
        show_table([helpers.valuation_row(fundamental, raw)], "No valuation data.")
        show_table(helpers.business_composition_rows(raw, fundamental), "No business composition data.")
        show_table(helpers.commodity_price_rows(raw), "No commodity price data.")

        quality = helpers.data_quality_summary(fundamental, raw)
        st.markdown("**数据质量**")
        show_table(quality["fetch_status"], "No fetch_status available.")
        with st.expander("原始 JSON", expanded=False):
            st.markdown("**规则结果 JSON**")
            st.json(fundamental or {}, expanded=False)
            st.markdown("**原始抓取 JSON**")
            st.json(raw or {}, expanded=False)


def render_top_conclusion(
    ai_report: dict | None,
    fundamental: dict | None,
    evidence_pack: dict | None,
    status: dict[str, Any],
    consistency: dict[str, Any],
) -> None:
    stock = helpers.current_stock_snapshot(fundamental, evidence_pack, ai_report)
    st.subheader("顶部结论区")
    cols = st.columns(4)
    cols[0].metric("股票代码", stock.get("stock_code") or "-")
    cols[1].metric("公司名称", stock.get("stock_name") or "-")
    cols[2].metric("基本面评分", stock.get("fundamental_score") if stock.get("fundamental_score") is not None else "-")
    cols[3].metric("报告质量状态", consistency.get("label") or "-")

    col1, col2 = st.columns(2)
    col1.write(f"分析框架：{helpers.format_strategy_type(stock.get('strategy_type'))}")
    col1.write(f"子类型：{helpers.format_sub_type(stock.get('sub_type'))}")
    col2.write(f"规则基本面状态：{helpers.status_label(stock.get('status'))}")
    col2.write(f"AI基本面观点：{helpers.ai_view_label((ai_report or {}).get('fundamental_view'))}")
    st.write(f"证据置信度：{helpers.confidence_label(stock.get('confidence'))}")
    st.caption(helpers.CONFIDENCE_EXPLANATION)

    checks = st.columns(3)
    checks[0].metric("结构校验", "通过" if status.get("schema_valid") else "未通过")
    checks[1].metric("安全校验", "通过" if status.get("safety_safe") else "未通过")
    checks[2].metric("乱码检测", "命中" if status.get("garbled_text_detected") else "未命中")
    for warning in consistency.get("warnings") or []:
        st.warning(warning)


def render_report_reader(
    ai_report: dict | None,
    fundamental: dict | None,
    evidence_pack: dict | None,
    raw: dict | None,
    status: dict[str, Any],
    consistency: dict[str, Any],
) -> None:
    st.subheader("一句话结论")
    summary = helpers.conclusion_summary(fundamental, ai_report, consistency)
    st.write(summary["primary"])
    if summary.get("ai_auxiliary"):
        st.info(summary["ai_auxiliary"])
    st.caption(helpers.CONFIDENCE_EXPLANATION)

    st.subheader("为什么是这个结论？")
    for item in helpers.why_conclusion_bullets(fundamental, evidence_pack, ai_report):
        st.markdown(f"- {item}")

    st.subheader("证据地图")
    cols = st.columns(3)
    evidence_source = evidence_pack or ai_report or {}
    for col, title, key in [
        (cols[0], "支持证据", "supporting_evidence"),
        (cols[1], "限制因素", "limiting_evidence"),
        (cols[2], "缺失证据", "unknown_or_missing_evidence"),
    ]:
        with col:
            st.markdown(f"**{title}**")
            rows = helpers.evidence_card_rows(evidence_source, key)
            if rows:
                for row in rows[:6]:
                    st.write(row)
            else:
                st.info("暂无结构化条目。")

    st.subheader("风险提示与证据缺口")
    notice = helpers.risk_gap_notice(fundamental, evidence_pack, ai_report)
    if notice:
        st.warning(notice)
        gaps = helpers.high_priority_missing_evidence(evidence_pack, ai_report)
        if gaps:
            show_table(helpers.ai_must_track_rows_cn({"must_track_analysis": gaps}, None), "暂无关键证据缺口。")
        else:
            show_table(helpers.evidence_card_rows(evidence_pack or ai_report, "unknown_or_missing_evidence")[:10], "暂无关键证据缺口。")
    risks = helpers.risk_cards(fundamental, evidence_pack, ai_report)
    show_table(risks[:10], "暂无结构化风险项；请结合证据缺口理解风险尚未被充分识别。")

    st.subheader("必须跟踪指标")
    high_medium = helpers.ai_must_track_rows_cn(ai_report, evidence_pack, include_low=False)
    show_table(high_medium, "暂无 high / medium 优先级指标。")
    low_rows = helpers.ai_must_track_rows_cn(ai_report, evidence_pack, include_low=True)
    low_rows = [row for row in low_rows if row.get("优先级") == "low"]
    with st.expander("低优先级指标", expanded=False):
        show_table(low_rows, "暂无 low 优先级指标。")

    st.subheader("置信度拆解")
    show_table(helpers.confidence_breakdown_rows(ai_report, evidence_pack), "暂无置信度拆解。")

    st.subheader("数据质量与缺口")
    show_table([helpers.data_quality_view(fundamental, evidence_pack, raw, consistency)], "暂无数据质量信息。")


def render_detail(stock_code: str | None) -> None:
    if not stock_code:
        st.info("尚未选择股票。")
        return
    bundle = helpers.load_ai_bundle(stock_code, OUTPUT_DIR)
    ai_report = bundle.get("ai_report")
    evidence_pack = bundle.get("evidence_pack")
    fundamental = bundle.get("fundamental")
    raw = bundle.get("raw")
    status = helpers.ai_report_status(ai_report, bundle.get("ai_report_markdown"))
    consistency = helpers.report_consistency_status(
        ai_report,
        evidence_pack,
        fundamental,
        ai_report_markdown=bundle.get("ai_report_markdown"),
        paths=bundle.get("paths"),
    )

    if ai_report is None:
        render_top_conclusion(ai_report, fundamental, evidence_pack, status, consistency)
        render_missing_ai_report(stock_code, bundle)
        render_report_reader(ai_report, fundamental, evidence_pack, raw, status, consistency)
        render_evidence_pack_viewer(evidence_pack)
        render_raw_data_viewer(fundamental, raw)
        return

    render_top_conclusion(ai_report, fundamental, evidence_pack, status, consistency)
    render_report_reader(ai_report, fundamental, evidence_pack, raw, status, consistency)

    with st.expander("审计材料：AI 报告正文", expanded=False):
        if status.get("garbled_text_detected"):
            st.warning("AI 自由文本损坏，已优先使用结构化证据 fallback。")
        if not status.get("schema_valid"):
            st.error(f"结构校验未通过：{status.get('schema_errors')}")
        if not status.get("safety_safe"):
            st.error(f"安全校验未通过：{status.get('blocked_terms')}")
        if not consistency.get("can_use_ai_body"):
            st.warning("报告过期 / 报告不一致，AI 正文仅作为旧报告审计材料展示。")
        if bundle.get("ai_report_markdown"):
            st.markdown(bundle["ai_report_markdown"])
        else:
            render_analysis_report(ai_report)

    render_evidence_pack_viewer(evidence_pack)
    render_raw_data_viewer(fundamental, raw)


def main() -> None:
    st.title("A股基本面 AI 分析看板")
    st.caption("中文基本面 AI 分析报告阅读器。只读取已有文件，不连接交易账户，不输出交易建议，不自动调用 API。")
    render_pipeline_tools()
    selected_code = render_stock_selector()
    st.divider()
    render_detail(selected_code)


if __name__ == "__main__":
    main()
