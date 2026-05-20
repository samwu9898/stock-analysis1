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


st.set_page_config(page_title="A-Share Fundamental AI Analyst Dashboard", layout="wide")


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

    st.subheader("Stock")
    if rows:
        st.dataframe(
            [
                {
                    "stock_code": row.get("stock_code"),
                    "stock_name": row.get("stock_name"),
                    "fundamental_view": row.get("fundamental_view"),
                    "strategy_type": row.get("strategy_type"),
                    "has_ai_report": row.get("has_ai_report"),
                    "has_fundamental": row.get("has_fundamental"),
                }
                for row in rows
            ],
            use_container_width=True,
            hide_index=True,
        )

    col1, col2 = st.columns([2, 1])
    with col1:
        selected = st.selectbox("Select stock", options=codes) if codes else None
    with col2:
        manual = st.text_input("Manual stock_code", placeholder="002050")
    normalized = helpers.normalize_stock_code(manual)
    return normalized or selected


def render_pipeline_tools() -> None:
    with st.expander("Pipeline Tools", expanded=False):
        st.caption("Runs the existing deterministic fundamental pipeline only. It does not generate AI reports.")
        with st.form("run_real_stock_form"):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                code = st.text_input("Stock code", value="002050", placeholder="002050")
            with col2:
                force_refresh = st.checkbox("force_refresh", value=False)
            with col3:
                submitted = st.form_submit_button("Run")

        if not submitted:
            return
        normalized = helpers.normalize_stock_code(code)
        if normalized not in SUPPORTED_CODES:
            st.error("Unsupported stock code for this dashboard.")
            return
        with st.spinner("Running existing fundamental pipeline..."):
            try:
                output_path = OUTPUT_DIR / f"fundamental_{normalized}.json"
                run_real_stock(normalized, output=str(output_path), force_refresh=force_refresh)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return
        st.success(f"Saved output/fundamental_{normalized}.json and output/raw_{normalized}.json")


def render_missing_ai_report(stock_code: str, bundle: dict[str, Any]) -> None:
    st.warning("尚未生成 AI report")
    st.code(
        f"python -m src.fundamental_skill.ai_analyst.runner --code {stock_code} --mode prompt_only",
        language="bash",
    )
    st.write("Then use Codex / GPT-5.5 with the generated prompt to create the AI report files.")
    prompt = bundle.get("ai_prompt") or helpers.prompt_preview(stock_code, OUTPUT_DIR)
    if prompt:
        with st.expander("Prompt Preview", expanded=False):
            st.markdown(prompt)
    else:
        st.info("No ai_prompt file found yet.")


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
    with st.expander("Evidence Pack Viewer", expanded=False):
        st.markdown("**Summary**")
        show_table([helpers.evidence_pack_summary(evidence_pack)], "No evidence pack summary.")
        st.markdown("**source_trace_summary**")
        show_table(helpers.as_list((evidence_pack or {}).get("source_trace_summary")), "No source trace summary.")
        st.markdown("**missing_fields**")
        show_table(helpers.as_list((evidence_pack or {}).get("missing_fields")), "No missing fields.")
        st.markdown("**data_limitations**")
        show_table([{"data_limitation": item} for item in helpers.as_list((evidence_pack or {}).get("data_limitations"))], "No data limitations.")
        with st.expander("Full evidence_pack JSON", expanded=False):
            st.json(evidence_pack or {}, expanded=False)


def render_raw_data_viewer(fundamental: dict | None, raw: dict | None) -> None:
    with st.expander("Evidence / Raw Data", expanded=False):
        st.markdown("**Legacy Fundamental Tables**")
        show_table(helpers.risk_flag_rows(fundamental), "No risk flags.")
        show_table(helpers.must_track_indicator_rows(fundamental), "No deterministic must-track indicators.")
        show_table([helpers.financial_quality_row(fundamental, raw)], "No financial quality data.")
        show_table([helpers.valuation_row(fundamental, raw)], "No valuation data.")
        show_table(helpers.business_composition_rows(raw, fundamental), "No business composition data.")
        show_table(helpers.commodity_price_rows(raw), "No commodity price data.")

        quality = helpers.data_quality_summary(fundamental, raw)
        st.markdown("**Data Quality**")
        show_table(quality["fetch_status"], "No fetch_status available.")
        with st.expander("Raw JSON", expanded=False):
            st.markdown("**fundamental JSON**")
            st.json(fundamental or {}, expanded=False)
            st.markdown("**raw JSON**")
            st.json(raw or {}, expanded=False)


def render_detail(stock_code: str | None) -> None:
    if not stock_code:
        st.info("No stock selected.")
        return
    bundle = helpers.load_ai_bundle(stock_code, OUTPUT_DIR)
    ai_report = bundle.get("ai_report")
    evidence_pack = bundle.get("evidence_pack")
    fundamental = bundle.get("fundamental")
    raw = bundle.get("raw")

    if ai_report is None:
        render_missing_ai_report(stock_code, bundle)
        render_evidence_pack_viewer(evidence_pack)
        render_raw_data_viewer(fundamental, raw)
        return

    status = helpers.ai_report_status(ai_report, bundle.get("ai_report_markdown"))
    render_executive_summary(ai_report, fundamental, evidence_pack)
    render_safety_status(status)
    render_fundamental_view(ai_report, fundamental)
    st.subheader("Confidence Breakdown")
    show_table(helpers.confidence_breakdown_rows(ai_report, evidence_pack), "No confidence breakdown.")
    render_evidence_classification(ai_report)

    st.subheader("Must Track Indicators")
    show_table(helpers.ai_must_track_rows(ai_report, evidence_pack), "No must-track indicators.")

    if status.get("garbled_text_detected") and bundle.get("ai_report_markdown"):
        st.subheader("AI Report Markdown Fallback")
        st.markdown(bundle["ai_report_markdown"])
    elif status.get("can_display_body"):
        render_analysis_report(ai_report)
        if bundle.get("ai_report_markdown"):
            with st.expander("AI Report Markdown", expanded=False):
                st.markdown(bundle["ai_report_markdown"])
    else:
        st.warning("AI report body is hidden because schema, safety, or quality checks failed.")

    render_evidence_pack_viewer(evidence_pack)
    render_raw_data_viewer(fundamental, raw)


def main() -> None:
    st.title("A-Share Fundamental AI Analyst Dashboard")
    st.caption("AI Report Viewer / Auditor. This page reads existing files and does not call model APIs.")
    render_pipeline_tools()
    selected_code = render_stock_selector()
    st.divider()
    render_detail(selected_code)


if __name__ == "__main__":
    main()
