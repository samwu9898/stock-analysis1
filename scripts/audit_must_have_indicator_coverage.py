"""Audit must-have fundamental indicator coverage from existing output files.

This script is intentionally read-only:
- reads output/evidence_pack_<code>.json and output/fundamental_<code>.json
- does not call AkShare
- does not use the network
- does not write or mutate pipeline outputs
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_CODES = ("002050", "000426", "300308", "002371", "601899", "603993")

MUST_HAVE: dict[str, list[str]] = {
    "resource_swing": [
        "核心商品价格",
        "主营矿种收入占比",
        "毛利率",
        "经营现金流",
        "资本开支",
        "产量 / 成本",
        "资产负债率",
        "存货",
        "应收账款",
    ],
    "resource_core": [
        "核心商品价格",
        "主营矿种收入占比",
        "毛利率",
        "经营现金流",
        "资本开支",
        "产量 / 成本",
        "资产负债率",
        "存货",
        "应收账款",
    ],
    "advanced_manufacturing_growth": [
        "收入增速",
        "利润增速",
        "毛利率",
        "经营现金流",
        "应收账款",
        "存货",
        "研发费用率",
        "新业务收入 / 订单",
        "大客户收入占比",
        "海外收入占比",
    ],
    "semiconductor_cycle": [
        "收入增速",
        "毛利率",
        "存货",
        "订单 / 合同负债",
        "研发费用率",
        "资本开支",
        "国产替代收入证据",
        "应收账款",
        "估值分位",
    ],
    "right_trend_growth": [
        "收入增速",
        "利润增速",
        "毛利率",
        "经营现金流",
        "订单持续性",
        "客户资本开支",
        "估值消化能力",
        "客户集中度",
    ],
}

PRIORITY = {
    "核心商品价格": "high",
    "主营矿种收入占比": "high",
    "毛利率": "high",
    "经营现金流": "high",
    "收入增速": "high",
    "利润增速": "high",
    "订单持续性": "high",
    "订单 / 合同负债": "high",
    "国产替代收入证据": "high",
    "新业务收入 / 订单": "high",
    "大客户收入占比": "high",
    "客户集中度": "high",
    "产量 / 成本": "medium",
    "资本开支": "medium",
    "客户资本开支": "medium",
    "估值消化能力": "medium",
    "估值分位": "medium",
    "资产负债率": "medium",
    "存货": "medium",
    "应收账款": "medium",
    "研发费用率": "medium",
    "海外收入占比": "medium",
}

DIFFICULTY = {
    "收入增速": "easy",
    "利润增速": "easy",
    "毛利率": "easy",
    "经营现金流": "easy",
    "资产负债率": "easy",
    "存货": "easy",
    "应收账款": "easy",
    "研发费用率": "easy",
    "资本开支": "medium",
    "估值分位": "medium",
    "估值消化能力": "medium",
    "核心商品价格": "medium",
    "主营矿种收入占比": "medium",
    "海外收入占比": "medium",
    "订单 / 合同负债": "medium",
    "产量 / 成本": "hard",
    "新业务收入 / 订单": "hard",
    "大客户收入占比": "hard",
    "客户集中度": "hard",
    "订单持续性": "hard",
    "客户资本开支": "hard",
    "国产替代收入证据": "hard",
}

SUGGESTED_SOURCE = {
    "收入增速": "AkShare 财务摘要 / stock_financial_abstract",
    "利润增速": "AkShare 财务摘要 / stock_financial_abstract",
    "毛利率": "AkShare 财务摘要 / stock_financial_abstract",
    "经营现金流": "AkShare 财务摘要 / stock_financial_abstract",
    "资产负债率": "AkShare 财务摘要 / stock_financial_abstract",
    "存货": "AkShare 资产负债表金额字段，避免使用周转率代理",
    "应收账款": "AkShare 资产负债表金额字段，避免使用周转率代理",
    "研发费用率": "AkShare 利润表研发费用 + 营业收入",
    "资本开支": "AkShare 现金流量表购建固定资产等现金流出",
    "订单 / 合同负债": "AkShare 资产负债表合同负债；订单需公告 / 年报文本",
    "估值分位": "历史估值序列，本地计算分位",
    "估值消化能力": "估值字段 + 增速字段 + 同业或历史分位，仅作基本面解释",
    "核心商品价格": "ExternalCommodityPriceConnector；钴、钼需稳定国内公开源",
    "主营矿种收入占比": "AkShare 主营构成 / stock_zygc_em",
    "海外收入占比": "AkShare 主营构成地区分类 / stock_zygc_em",
    "产量 / 成本": "公告 / 年报文本 / 人工录入，部分成本可来自主营构成",
    "新业务收入 / 订单": "公告 / 年报文本 / 研报 / 人工录入",
    "大客户收入占比": "年报客户集中度披露 / 人工录入",
    "客户集中度": "年报客户集中度披露 / 人工录入",
    "订单持续性": "公告 / 年报订单披露 / 研报 / 人工录入",
    "客户资本开支": "客户公告、财报、行业数据或人工维护",
    "国产替代收入证据": "公告 / 年报文本 / 研报 / 人工录入",
}

IMPACT = {
    "核心商品价格": "资源股周期判断的外部变量不足，报告难以验证商品价格环境。",
    "主营矿种收入占比": "无法确认收入暴露，资源股和制造业分部判断会变弱。",
    "毛利率": "产品结构、成本和定价能力缺少核心验证。",
    "经营现金流": "利润质量和兑现质量缺少核心验证。",
    "资本开支": "扩产周期、产能释放和自由现金流压力不足以判断。",
    "产量 / 成本": "资源股成本曲线和量价弹性不足以判断。",
    "资产负债率": "财务杠杆和周期压力识别会变弱。",
    "存货": "库存周期、减值压力和供需错配不足以判断。",
    "应收账款": "收入质量、回款压力和客户议价变化不足以判断。",
    "收入增速": "成长或景气兑现缺少基础验证。",
    "利润增速": "盈利弹性和费用吸收能力缺少基础验证。",
    "研发费用率": "技术投入强度和国产替代持续性不足以判断。",
    "新业务收入 / 订单": "新业务兑现无法与预期区分，AI 报告容易停留在概念描述。",
    "大客户收入占比": "客户依赖和需求稳定性无法量化。",
    "海外收入占比": "全球需求和外部环境暴露无法量化。",
    "订单 / 合同负债": "半导体设备周期位置和未来收入可见度不足以判断。",
    "国产替代收入证据": "国产替代逻辑无法从收入或客户验证层面落地。",
    "估值分位": "只能列 PE/PB/PS，难以判断估值语境。",
    "订单持续性": "高景气是否可持续缺少关键证据。",
    "客户资本开支": "需求侧景气依赖无法验证。",
    "估值消化能力": "估值与成长兑现之间的解释会偏弱。",
    "客户集中度": "订单波动和单一客户依赖风险无法量化。",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def metric_value(metrics: dict[str, Any], key: str) -> Any:
    value = metrics.get(key)
    if isinstance(value, dict):
        return value.get("display_value") or value.get("raw_value")
    return value


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def source_date(evidence: dict[str, Any], block_name: str) -> Any:
    for trace in evidence.get("source_trace_summary", []):
        if trace.get("block_name") == block_name:
            return trace.get("latest_period")
    if block_name == "financial_indicator":
        return evidence.get("financial_metrics", {}).get("period")
    if block_name == "valuation":
        return evidence.get("valuation_metrics", {}).get("period")
    return None


def segment_summary(evidence: dict[str, Any], keywords: tuple[str, ...] = ()) -> str | None:
    segments = evidence.get("business_composition") or []
    picked = []
    for item in segments:
        name = str(item.get("segment_name") or "")
        if keywords and not any(k in name for k in keywords):
            continue
        ratio = item.get("revenue_ratio")
        display = ratio.get("display_value") if isinstance(ratio, dict) else ratio
        if display:
            picked.append(f"{name} {display}")
    return "; ".join(picked[:6]) if picked else None


def overseas_summary(evidence: dict[str, Any]) -> str | None:
    return segment_summary(evidence, ("海外", "国外", "境外"))


def commodity_summary(evidence: dict[str, Any]) -> str | None:
    rows = evidence.get("commodity_prices") or []
    if not rows:
        return None
    return "; ".join(
        f"{row.get('commodity_name_cn') or row.get('commodity_name')} {row.get('price')} ({row.get('date')})"
        for row in rows
    )


def missing_fields(evidence: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for item in evidence.get("missing_fields") or []:
        if isinstance(item, str):
            values.add(item)
        elif isinstance(item, dict) and item.get("field"):
            values.add(str(item["field"]))
    for row in evidence.get("confidence_basis", {}).get("missing_fields", []):
        field = row.get("field")
        if field:
            values.add(field)
    return values


def build_row(evidence: dict[str, Any], fundamental: dict[str, Any], indicator: str) -> dict[str, Any]:
    metrics = evidence.get("financial_metrics") or {}
    valuation = evidence.get("valuation_metrics") or {}
    missing = missing_fields(evidence)
    status = "missing"
    value: Any = None
    source = "missing"
    date = None
    reason = "existing evidence pack has no dedicated field for this indicator"

    financial_map = {
        "收入增速": "revenue_yoy",
        "利润增速": "net_profit_yoy",
        "毛利率": "gross_margin",
        "经营现金流": "operating_cashflow",
        "资产负债率": "debt_to_asset",
        "存货": "inventory",
        "应收账款": "accounts_receivable",
    }
    if indicator in financial_map:
        key = financial_map[indicator]
        value = metric_value(metrics, key)
        source = "financial_indicator"
        date = source_date(evidence, "financial_indicator")
        if has_value(value):
            status = "available"
            reason = ""
        else:
            reason = f"financial_metrics.{key} is null or absent in current evidence pack"

    elif indicator == "核心商品价格":
        value = commodity_summary(evidence)
        source = "commodity_prices"
        date = source_date(evidence, "commodity_prices")
        has_prices = has_value(value)
        missing_commodities = sorted(f for f in missing if f.startswith("external.commodity_prices."))
        if has_prices and missing_commodities:
            status = "partial"
            reason = "some required commodities are missing: " + ", ".join(missing_commodities)
        elif has_prices:
            status = "available"
            reason = ""
        else:
            reason = "no commodity_prices block for this stock"

    elif indicator == "主营矿种收入占比":
        value = segment_summary(evidence, ("矿", "铜", "钴", "钼", "金", "银", "锡", "锌", "铅", "铌"))
        source = "business_composition"
        date = source_date(evidence, "business_composition")
        if has_value(value):
            status = "available"
            reason = ""
        elif evidence.get("business_composition"):
            status = "partial"
            value = segment_summary(evidence)
            reason = "business composition exists but mineral exposure is not explicit"
        else:
            reason = "business_composition is missing"

    elif indicator == "海外收入占比":
        value = overseas_summary(evidence)
        source = "business_composition"
        date = source_date(evidence, "business_composition")
        if has_value(value):
            status = "available"
            reason = ""
        elif evidence.get("business_composition"):
            status = "partial"
            reason = "business composition exists but no overseas / foreign region segment was found"
        else:
            reason = "business_composition is missing"

    elif indicator == "产量 / 成本":
        value = segment_summary(evidence, ("矿", "铜", "钴", "钼", "金", "银", "锡", "锌", "铅", "铌"))
        source = "business_composition"
        date = source_date(evidence, "business_composition")
        if has_value(value):
            status = "partial"
            reason = "segment cost or gross margin exists, but production volume and unit cost are not available"
        else:
            reason = "no production volume, unit cost, or usable segment cost evidence"

    elif indicator == "估值消化能力":
        pe = valuation.get("pe_ttm")
        revenue_yoy = metric_value(metrics, "revenue_yoy")
        net_profit_yoy = metric_value(metrics, "net_profit_yoy")
        source = "valuation + financial_indicator"
        date = source_date(evidence, "valuation")
        if has_value(pe) and (has_value(revenue_yoy) or has_value(net_profit_yoy)):
            status = "partial"
            value = f"PE TTM {pe}; revenue_yoy {revenue_yoy}; net_profit_yoy {net_profit_yoy}"
            reason = "valuation and growth fields exist, but no historical percentile or peer context"
        elif has_value(pe):
            status = "partial"
            value = f"PE TTM {pe}"
            reason = "valuation exists but growth validation is incomplete"
        else:
            reason = "valuation_metrics.pe_ttm is absent"

    elif indicator == "估值分位":
        source = "valuation"
        date = source_date(evidence, "valuation")
        pe = valuation.get("pe_ttm")
        if has_value(pe):
            status = "partial"
            value = f"PE TTM {pe}"
            reason = "point-in-time valuation exists, but historical valuation percentile is absent"
        else:
            reason = "valuation metrics are absent"

    elif indicator == "新业务收入 / 订单":
        value = segment_summary(evidence, ("汽车", "机器人", "新业务", "执行器"))
        source = "business_composition / missing"
        date = source_date(evidence, "business_composition")
        if has_value(value):
            status = "partial"
            reason = "business segment evidence exists, but new-business revenue split and order evidence are absent"
        else:
            reason = "no new-business revenue or order field in evidence pack"

    elif indicator == "订单 / 合同负债":
        contract_liability = metric_value(metrics, "contract_liabilities")
        source = "missing"
        if has_value(contract_liability):
            status = "partial"
            value = contract_liability
            source = "financial_indicator"
            date = source_date(evidence, "financial_indicator")
            reason = "contract liability exists, but explicit order evidence is absent"
        else:
            reason = "no order backlog or contract liability field in evidence pack"

    elif indicator in {
        "研发费用率",
        "资本开支",
        "大客户收入占比",
        "订单持续性",
        "客户资本开支",
        "客户集中度",
        "国产替代收入证据",
    }:
        reason = f"{indicator} is not represented as a structured field in current evidence pack"

    return {
        "stock_code": evidence["stock"]["code"],
        "stock_name": evidence["stock"]["name"],
        "strategy_type": evidence["stock"]["strategy_type"],
        "indicator_name": indicator,
        "coverage_status": status,
        "current_value": value,
        "source": source,
        "source_date": date,
        "missing_reason": reason,
        "impact_on_analysis": IMPACT[indicator],
        "priority": PRIORITY[indicator],
        "implementation_difficulty": DIFFICULTY[indicator],
        "suggested_data_source": SUGGESTED_SOURCE[indicator],
    }


def coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    score_map = {"available": 1.0, "partial": 0.5, "missing": 0.0}
    total = len(rows)
    effective = sum(score_map[row["coverage_status"]] for row in rows)
    strict = sum(1 for row in rows if row["coverage_status"] == "available")
    return {
        "total": total,
        "available": strict,
        "partial": sum(1 for row in rows if row["coverage_status"] == "partial"),
        "missing": sum(1 for row in rows if row["coverage_status"] == "missing"),
        "strict_coverage": round(strict / total, 4) if total else 0,
        "effective_coverage": round(effective / total, 4) if total else 0,
    }


def run_audit(root: Path, codes: tuple[str, ...]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    missing_files: list[str] = []
    for code in codes:
        evidence_path = root / "output" / f"evidence_pack_{code}.json"
        fundamental_path = root / "output" / f"fundamental_{code}.json"
        for path in (evidence_path, fundamental_path):
            if not path.exists():
                missing_files.append(str(path))
        if missing_files:
            continue
        evidence = load_json(evidence_path)
        fundamental = load_json(fundamental_path)
        strategy_type = evidence["stock"]["strategy_type"]
        for indicator in MUST_HAVE.get(strategy_type, []):
            rows.append(build_row(evidence, fundamental, indicator))

    if missing_files:
        raise FileNotFoundError(
            "Missing required output files. Please run the runner first:\n"
            + "\n".join(sorted(missing_files))
        )

    by_stock = defaultdict(list)
    by_strategy = defaultdict(list)
    for row in rows:
        by_stock[row["stock_code"]].append(row)
        by_strategy[row["strategy_type"]].append(row)

    high_missing = Counter(
        row["indicator_name"]
        for row in rows
        if row["priority"] == "high" and row["coverage_status"] in {"missing", "partial"}
    )

    return {
        "rows": rows,
        "summary": {
            "overall": coverage(rows),
            "by_stock": {key: coverage(value) for key, value in sorted(by_stock.items())},
            "by_strategy_type": {key: coverage(value) for key, value in sorted(by_strategy.items())},
            "high_priority_gap_ranking": high_missing.most_common(),
        },
    }


def print_markdown(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("# Must-Have Indicator Coverage Audit")
    print()
    print("## Overall")
    print(json.dumps(summary["overall"], ensure_ascii=False))
    print()
    print("## By Stock")
    for code, item in summary["by_stock"].items():
        print(f"- {code}: {json.dumps(item, ensure_ascii=False)}")
    print()
    print("## By Strategy Type")
    for strategy_type, item in summary["by_strategy_type"].items():
        print(f"- {strategy_type}: {json.dumps(item, ensure_ascii=False)}")
    print()
    print("## High Priority Gap Ranking")
    for name, count in summary["high_priority_gap_ranking"]:
        print(f"- {name}: {count}")
    print()
    print("## Detail Rows")
    headers = [
        "stock_code",
        "stock_name",
        "strategy_type",
        "indicator_name",
        "coverage_status",
        "source",
        "source_date",
        "priority",
        "implementation_difficulty",
    ]
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in result["rows"]:
        print("| " + " | ".join(str(row.get(header) or "") for header in headers) + " |")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root; default is current directory")
    parser.add_argument("--codes", nargs="*", default=list(DEFAULT_CODES))
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()

    result = run_audit(Path(args.root), tuple(args.codes))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_markdown(result)


if __name__ == "__main__":
    main()
