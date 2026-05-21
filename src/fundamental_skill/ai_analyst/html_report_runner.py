# -*- coding: utf-8 -*-
"""CLI runner for Fundamental HTML Report Generator v1."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .evidence_pack import EvidencePackBuilder
from .html_report_prompt_builder import HtmlReportPromptBuilder
from .html_report_renderer import write_fundamental_html_report
from .html_report_schema import schema_example, validate_fundamental_html_report


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_REPORT_DIR = DEFAULT_OUTPUT_DIR / "reports"


STRATEGY_LABELS = {
    "resource_swing": "资源弹性",
    "resource_core": "资源核心",
    "right_trend_growth": "高景气成长",
    "semiconductor_cycle": "半导体周期",
    "stable_growth": "稳健成长",
    "advanced_manufacturing_growth": "高端制造成长",
    "satellite_communication_infrastructure": "卫星通信基础设施",
    "low_altitude_economy_infrastructure": "低空经济基础设施 / 运营服务",
    "life_science_cxo_services": "CXO 医药外包服务",
    "ai_datacenter_infrastructure": "AI 数据中心基础设施",
    "theme_only": "题材型",
    "unknown": "未知 / 暂无法归类",
}

SUB_TYPE_LABELS = {
    "aviation_operations_service": "通航 / 低空飞行运营服务",
    "airspace_platform_system": "空域平台 / 调度系统",
    "integrated_cxo_platform": "综合 CXO 平台",
    "cdmo_manufacturing_services": "CDMO 生产制造服务",
    "clinical_cro_services": "临床 CRO 服务",
    "datacenter_operator": "数据中心运营商",
    "power_ups_infrastructure": "电力 / UPS 基础设施",
    "cooling_liquid_cooling_infrastructure": "冷却 / 液冷基础设施",
}


def normalize_stock_code(code: Any) -> str:
    digits = "".join(ch for ch in str(code or "") if ch.isdigit())
    if len(digits) < 6:
        raise ValueError("stock code must contain 6 digits")
    return digits[-6:]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def run_prompt_only(code: str, output_dir: str | Path | None = None) -> dict[str, Any]:
    normalized = normalize_stock_code(code)
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    report_dir = directory / "reports"
    fundamental_path = directory / f"fundamental_{normalized}.json"
    raw_path = directory / f"raw_{normalized}.json"
    evidence_path = directory / f"evidence_pack_{normalized}.json"
    prompt_path = report_dir / f"fundamental_report_prompt_{normalized}.md"

    if not fundamental_path.exists() or not raw_path.exists():
        missing = [str(path) for path in (fundamental_path, raw_path) if not path.exists()]
        raise FileNotFoundError(
            "Required fundamental/raw JSON files are missing. Run src.fundamental_skill.real_stock_runner first. Missing: "
            + ", ".join(missing)
        )

    report_dir.mkdir(parents=True, exist_ok=True)
    evidence_pack = EvidencePackBuilder().build_from_files(fundamental_path, raw_path)
    evidence_path.write_text(json.dumps(evidence_pack, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    prompt = HtmlReportPromptBuilder().build(evidence_pack)
    prompt_path.write_text(prompt, encoding="utf-8")
    return {"stock_code": normalized, "prompt_path": str(prompt_path), "evidence_pack_path": str(evidence_path)}


def run_render_existing(code: str, output_dir: str | Path | None = None) -> dict[str, Any]:
    normalized = normalize_stock_code(code)
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    report_dir = directory / "reports"
    json_path = report_dir / f"fundamental_report_{normalized}.json"
    html_path = report_dir / f"fundamental_report_{normalized}.html"
    report = _load_json(json_path)
    validation = validate_fundamental_html_report(report)
    if not validation["valid"]:
        raise ValueError(f"Invalid FundamentalHtmlReport JSON: {validation['schema_errors']}")
    write_fundamental_html_report(report, html_path)
    return {"stock_code": normalized, "input_path": str(json_path), "html_path": str(html_path)}


def run_skeleton(code: str, output_dir: str | Path | None = None) -> dict[str, Any]:
    normalized = normalize_stock_code(code)
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    report_dir = directory / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    evidence_path = directory / f"evidence_pack_{normalized}.json"
    evidence_pack = json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.exists() else {}
    stock = evidence_pack.get("stock") if isinstance(evidence_pack.get("stock"), dict) else {}

    report = schema_example()
    report["report_meta"].update(
        {
            "stock_code": normalized,
            "stock_name": stock.get("name") or "",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "strategy_type": stock.get("strategy_type") or "unknown",
            "strategy_type_label": STRATEGY_LABELS.get(str(stock.get("strategy_type") or "unknown"), "未知 / 暂无法归类"),
            "sub_type": stock.get("sub_type") or "",
            "sub_type_label": SUB_TYPE_LABELS.get(str(stock.get("sub_type") or ""), "不适用"),
            "status": "skeleton",
            "confidence": "skeleton",
            "fundamental_score": None,
            "data_quality_status": "skeleton，仅用于渲染测试",
        }
    )
    report["core_conclusion"].update(
        {
            "title": "Skeleton 渲染样例，不是正式 AI 分析报告",
            "summary": "本文件仅用于验证 HTML 渲染链路；没有形成正式研究结论，也没有补充任何 evidence pack 之外的判断。",
            "supporting_points": ["Skeleton 不代表正式分析。"],
            "limiting_points": ["缺少正式 AI 结构化分析 JSON。"],
            "must_track_points": ["请先基于 prompt 生成正式 FundamentalHtmlReport JSON。"],
            "evidence_confidence_explanation": "Skeleton 模式不评估证据置信度。",
        }
    )
    report["hero_tags"] = ["Skeleton", "仅验证渲染", "非正式报告"]
    report["research_anchor"].update(
        {
            "main_thesis": "Skeleton 模式不生成正式研究主线。",
            "key_conflict": "Skeleton 模式只验证 HTML 结构，不形成基本面矛盾判断。",
            "current_stage": "skeleton",
            "what_is_proven": ["渲染链路可执行。"],
            "what_is_unproven": ["未生成正式 AI 结构化分析 JSON。"],
        }
    )
    report["company_profile"]["main_business"] = "Skeleton 模式未生成公司画像。"
    report["recent_fundamental_updates"]["unavailable_news_note"] = "Skeleton 模式不读取或编造新闻。"
    report["business_composition_analysis"]["analysis"] = "Skeleton 模式不判断业务构成。"
    report["financial_quality_diagnosis"]["final_diagnosis"] = "Skeleton 模式不诊断财务质量。"
    report["valuation_explanation"]["valuation_interpretation"] = "Skeleton 模式不解释估值。"
    report["core_fundamental_question"]["main_question"] = "Skeleton 模式不设定正式基本面命题。"
    report["industry_cycle_positioning"]["cycle_stage"] = "Skeleton 模式无法判断。"
    report["value_chain_and_business_model"]["how_company_makes_money"] = "Skeleton 模式不分析商业模式。"
    report["value_chain_map"].update(
        {
            "upstream": "Skeleton 模式待验证",
            "company_role": "Skeleton 模式待验证",
            "downstream": "Skeleton 模式待验证",
            "profit_source": "Skeleton 模式不分析利润来源。",
            "unproven_moats": ["Skeleton 模式不验证壁垒。"],
            "key_bottlenecks": ["缺少正式 AI 结构化分析 JSON。"],
        }
    )
    report["elasticity_formula"].update(
        {
            "formula_title": "Skeleton 基本面弹性占位",
            "formula_text": "利润弹性 = 收入增长 × 毛利率稳定性 × 费用率控制",
            "key_variables": ["收入", "毛利率", "费用率", "经营现金流", "capex"],
            "interpretation": "Skeleton 模式只展示公式卡片，不形成正式判断。",
            "data_limitations": ["缺少正式 AI 结构化分析 JSON。"],
        }
    )
    for key in ("optimistic_case", "base_case", "downside_case"):
        report["fundamental_scenario_analysis"][key]["impact_on_fundamentals"] = "Skeleton 模式不生成正式情景判断。"
        report["fundamental_scenario_analysis"][key]["evidence_strength"] = "skeleton"
    report["peer_comparison"]["interpretation"] = "Skeleton 模式不做同业对比。"
    report["risk_analysis"]["data_gap_risks"] = ["Skeleton 模式缺少正式 AI 分析 JSON。"]
    report["must_track_indicators"] = [
        {
            "indicator": "正式 FundamentalHtmlReport JSON",
            "priority": "high",
            "current_status": "missing",
            "why_it_matters": "没有正式 JSON 时只能验证渲染，不能形成研究报告。",
            "next_evidence_needed": "使用 prompt 生成结构化报告 JSON。",
            "current_value": None,
        }
    ]
    report["tracking_plan_groups"] = [
        {
            "group_name": "财报跟踪",
            "items": [
                {
                    "indicator": "正式 FundamentalHtmlReport JSON",
                    "frequency": "生成正式报告前",
                    "why_it_matters": "Skeleton 不能冒充正式报告。",
                    "trigger_for_review": "补齐正式 JSON 后重新渲染。",
                }
            ],
        },
        {"group_name": "公告/订单跟踪", "items": []},
        {"group_name": "行业/政策跟踪", "items": []},
        {"group_name": "风险复核", "items": []},
    ]
    report["data_quality_and_unknowns"]["cannot_determine"] = ["Skeleton 模式不能作为正式基本面结论。"]

    json_path = report_dir / f"fundamental_report_{normalized}.json"
    html_path = report_dir / f"fundamental_report_{normalized}.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    write_fundamental_html_report(report, html_path)
    return {"stock_code": normalized, "json_path": str(json_path), "html_path": str(html_path), "skeleton_warning": True}


def main() -> int:
    parser = argparse.ArgumentParser(description="Fundamental HTML Report Generator v1.")
    parser.add_argument("--code", required=True, help="6 digit A-share stock code")
    parser.add_argument("--mode", required=True, choices=["prompt_only", "render_existing", "skeleton"])
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory containing output files")
    args = parser.parse_args()

    try:
        if args.mode == "prompt_only":
            result = run_prompt_only(args.code, args.output_dir)
            print(f"stock_code: {result['stock_code']}")
            print(f"html_report_prompt: {result['prompt_path']}")
            print(f"evidence_pack: {result['evidence_pack_path']}")
        elif args.mode == "render_existing":
            result = run_render_existing(args.code, args.output_dir)
            print(f"stock_code: {result['stock_code']}")
            print(f"html_report: {result['html_path']}")
        else:
            result = run_skeleton(args.code, args.output_dir)
            print("skeleton warning: this is not a formal AI analysis report")
            print(f"stock_code: {result['stock_code']}")
            print(f"html_report_json: {result['json_path']}")
            print(f"html_report: {result['html_path']}")
    except Exception as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
