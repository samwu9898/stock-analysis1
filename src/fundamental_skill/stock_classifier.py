# -*- coding: utf-8 -*-
"""Deterministic rule-based stock classifier for fundamental_skill."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from .classification_schema import ClassificationEvidence, StockClassificationResult
from .data_adapter import FundamentalDataAdapter
from .framework_selector import FrameworkSelector
from .raw_schema import NormalizedFundamentalInput


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLASSIFICATION_CONFIG = PROJECT_ROOT / "config" / "strategy_classification.yaml"

SOURCE_WEIGHTS = {
    "stock_name": 40,
    "industry": 28,
    "main_business": 28,
    "business_composition": 22,
    "news": 10,
    "raw_blocks": 8,
}

CORE_TIEBREAKERS = {
    "resource_core": ("紫金矿业", "多矿种", "全球矿业", "资源龙头", "大型矿企"),
    "resource_swing": ("兴业银锡", "银", "锡", "稀土", "单一商品", "弹性"),
    "semiconductor_cycle": ("半导体", "芯片", "晶圆", "存储", "国产替代", "刻蚀", "光刻"),
    "right_trend_growth": ("光模块", "PCB", "AI服务器", "液冷", "数据中心", "CPO"),
    "advanced_manufacturing_growth": (
        "三花智控",
        "拓普集团",
        "汇川技术",
        "汽车热管理",
        "热管理",
        "制冷控制",
        "机器人",
        "机器人执行器",
        "执行器",
        "减速器",
        "谐波减速器",
        "伺服",
        "工业自动化",
        "精密制造",
        "汽车零部件",
        "新能源车",
        "特斯拉",
        "人形机器人",
        "关节模组",
        "高端制造",
    ),
    "satellite_communication_infrastructure": (
        "电信、广播电视和卫星传输服务",
        "卫星空间段运营",
        "卫星传输服务",
        "卫星通信服务",
        "广播电视和卫星传输服务",
        "转发器",
        "带宽资源",
        "轨位资源",
        "频段资源",
    ),
    "stable_growth": ("电网", "变压器", "特高压", "输配电", "电网自动化"),
}

SATELLITE_NEGATIVE_KEYWORDS = (
    "遥感数据服务",
    "遥感软件",
    "测控地面系统集成",
    "卫星制造",
    "整星研制",
    "火箭制造",
    "导航芯片",
    "北斗芯片",
    "军工电子终端",
    "通信设备制造",
    "低空经济",
    "无人机",
)

SATELLITE_STRONG_CORE_KEYWORDS = (
    "电信、广播电视和卫星传输服务",
    "卫星空间段运营",
    "卫星传输服务",
    "卫星通信服务",
)

LOW_ALTITUDE_STRATEGY = "low_altitude_economy_infrastructure"
LOW_ALTITUDE_AVIATION_SUBTYPE = "aviation_operations_service"
LOW_ALTITUDE_AIRSPACE_SUBTYPE = "airspace_platform_system"
LIFE_SCIENCE_CXO_STRATEGY = "life_science_cxo_services"
LIFE_SCIENCE_CXO_INTEGRATED_SUBTYPE = "integrated_cxo_platform"
LIFE_SCIENCE_CXO_CDMO_SUBTYPE = "cdmo_manufacturing_services"
LIFE_SCIENCE_CXO_CLINICAL_SUBTYPE = "clinical_cro_services"
AI_DATACENTER_STRATEGY = "ai_datacenter_infrastructure"
AI_DATACENTER_OPERATOR_SUBTYPE = "datacenter_operator"
AI_DATACENTER_POWER_SUBTYPE = "power_ups_infrastructure"
AI_DATACENTER_COOLING_SUBTYPE = "cooling_liquid_cooling_infrastructure"

LOW_ALTITUDE_AVIATION_PRIMARY = (
    "\u901a\u822a\u8fd0\u8425",
    "\u4f4e\u7a7a\u98de\u884c\u670d\u52a1",
    "\u901a\u822a\u8fd0\u8f93",
    "\u822a\u7a7a\u5e94\u6025\u6551\u63f4",
    "general aviation operation",
    "low-altitude flight service",
    "general aviation transportation",
    "aviation emergency rescue",
)
LOW_ALTITUDE_AVIATION_PROOF = (
    "\u6536\u5165",
    "\u8fd0\u8425\u5c0f\u65f6",
    "\u98de\u884c\u67b6\u6b21",
    "\u673a\u961f",
    "\u5ba2\u6237\u5408\u540c",
    "revenue",
    "operating hours",
    "flight sorties",
    "fleet",
    "customer contract",
)
LOW_ALTITUDE_AIRSPACE_PRIMARY = (
    "\u7a7a\u4e2d\u4ea4\u901a\u7ba1\u7406",
    "\u7a7a\u7ba1\u7cfb\u7edf",
    "\u4f4e\u7a7a\u8c03\u5ea6",
    "\u4f4e\u7a7a\u8fd0\u884c\u5e73\u53f0",
    "\u6307\u6325\u8c03\u5ea6\u5e73\u53f0",
    "air traffic management",
    "air traffic control system",
    "low-altitude dispatch",
    "low-altitude operation platform",
    "command dispatch platform",
)
LOW_ALTITUDE_AIRSPACE_PROOF = (
    "\u5408\u540c",
    "\u9879\u76ee\u9a8c\u6536",
    "\u5ba2\u6237",
    "\u6536\u5165",
    "\u5e73\u53f0\u4ea4\u4ed8",
    "contract",
    "project acceptance",
    "customer",
    "revenue",
    "platform delivery",
)
LOW_ALTITUDE_RELATED_SEGMENT_KEYWORDS = (
    "\u4f4e\u7a7a",
    "\u901a\u822a",
    "\u901a\u822a\u8fd0\u8f93",
    "\u901a\u822a\u8fd0\u8425",
    "\u7a7a\u4e2d\u4ea4\u901a\u7ba1\u7406",
    "\u7a7a\u7ba1",
    "\u6307\u6325\u8c03\u5ea6",
)
LOW_ALTITUDE_BOUNDARY_KEYWORDS = (
    "\u65e0\u4eba\u673a",
    "\u65e0\u4eba\u673a\u6574\u673a",
    "\u5de5\u4e1a\u65e0\u4eba\u673a",
    "eVTOL",
    "evtol",
    "\u98de\u884c\u6c7d\u8f66",
    "\u901a\u822a\u98de\u673a\u5236\u9020",
    "\u98de\u673a\u5236\u9020",
    "\u822a\u7a7a\u53d1\u52a8\u673a",
    "\u53d1\u52a8\u673a",
    "\u822a\u7a7a\u96f6\u90e8\u4ef6",
    "\u6c7d\u8f66\u96f6\u90e8\u4ef6",
    "\u9065\u611f",
    "\u6d4b\u7ed8",
    "\u519b\u5de5",
    "\u519b\u5de5\u7535\u5b50",
    "\u6c11\u822a\u673a\u573a",
    "\u822a\u7a7a\u79df\u8d41",
    "\u822a\u7a7a\u91d1\u878d",
)
LOW_ALTITUDE_TRADITIONAL_SEGMENT_KEYWORDS = (
    "\u6c7d\u8f66\u96f6\u90e8\u4ef6",
    "\u822a\u7a7a\u53d1\u52a8\u673a",
    "\u53d1\u52a8\u673a",
    "\u65e0\u4eba\u673a",
    "\u519b\u5de5",
    "\u6750\u6599",
    "\u7535\u6c60",
    "\u4f20\u611f\u5668",
    "\u98de\u673a\u5236\u9020",
    "\u901a\u822a\u98de\u673a\u5236\u9020",
    "\u9065\u611f",
    "\u6d4b\u7ed8",
    "\u822a\u7a7a\u79df\u8d41",
    "\u6c11\u822a\u673a\u573a",
)

LIFE_SCIENCE_CXO_PRIMARY = (
    "CRO",
    "CDMO",
    "CXO",
    "CMC",
    "clinical CRO",
    "preclinical",
    "drug discovery",
    "contract research",
    "contract development",
    "clinical trial service",
    "SMO",
    "pharmaceutical outsourcing",
    "drug R&D outsourcing",
    "\u4e34\u5e8a\u7814\u7a76\u5916\u5305",
    "\u4e34\u5e8a CRO",
    "\u7814\u53d1\u5916\u5305",
    "\u836f\u7269\u53d1\u73b0\u670d\u52a1",
    "\u533b\u836f\u7814\u53d1\u751f\u4ea7\u5916\u5305",
    "\u533b\u836f\u5916\u5305\u670d\u52a1",
    "\u5408\u540c\u7814\u7a76\u7ec4\u7ec7",
    "\u5408\u540c\u5f00\u53d1\u751f\u4ea7\u7ec4\u7ec7",
    "\u4e34\u5e8a\u8bd5\u9a8c\u670d\u52a1",
    "\u836f\u7269\u53d1\u73b0",
    "\u4e34\u5e8a\u524d\u7814\u7a76",
    "\u5de5\u827a\u5f00\u53d1",
    "\u5546\u4e1a\u5316\u751f\u4ea7\u670d\u52a1",
)
LIFE_SCIENCE_CXO_PROOF = (
    "revenue",
    "revenue share",
    "order",
    "contract liabilities",
    "capacity",
    "clinical project",
    "main business",
    "business composition",
    "segment revenue",
    "\u6536\u5165\u5360\u6bd4",
    "\u8ba2\u5355",
    "\u5408\u540c\u8d1f\u503a",
    "\u4ea7\u80fd",
    "\u4e34\u5e8a\u9879\u76ee",
    "\u4e3b\u8425\u4e1a\u52a1",
    "\u4e3b\u8425\u6784\u6210",
    "\u6536\u5165",
    "\u5206\u90e8\u6536\u5165",
)
LIFE_SCIENCE_CXO_SEGMENT_KEYWORDS = (
    "CRO",
    "CDMO",
    "CXO",
    "CMC",
    "clinical trial",
    "drug discovery",
    "outsourcing",
    "\u4e34\u5e8a\u7814\u7a76",
    "\u4e34\u5e8a CRO",
    "\u4e34\u5e8a\u8bd5\u9a8c",
    "\u836f\u7269\u53d1\u73b0",
    "\u533b\u836f\u5916\u5305",
    "\u533b\u836f\u7814\u53d1\u751f\u4ea7\u5916\u5305",
    "\u5408\u540c\u7814\u7a76",
    "\u5408\u540c\u5f00\u53d1\u751f\u4ea7",
    "\u5de5\u827a\u5f00\u53d1",
    "\u5546\u4e1a\u5316\u751f\u4ea7",
)
LIFE_SCIENCE_PHARMA_PRODUCT_SEGMENT_KEYWORDS = (
    "API",
    "active pharmaceutical ingredient",
    "formulation",
    "finished drug",
    "pharmaceutical sales",
    "\u539f\u6599\u836f",
    "\u5236\u5242",
    "\u836f\u54c1\u9500\u552e",
    "\u4eff\u5236\u836f",
    "\u521b\u65b0\u836f",
)
LIFE_SCIENCE_CXO_NEGATIVE_KEYWORDS = (
    "self-owned pipeline",
    "innovative drug pipeline",
    "API sales",
    "formulation sales",
    "medical device",
    "pharmaceutical distribution",
    "TCM",
    "consumer healthcare",
    "hospital",
    "general testing",
    "AI drug discovery",
    "software license",
    "SaaS",
    "technology license",
    "\u81ea\u6709\u521b\u65b0\u836f",
    "\u65b0\u836f\u7ba1\u7ebf",
    "\u521b\u65b0\u836f\u7814\u53d1",
    "\u539f\u6599\u836f\u9500\u552e",
    "\u5236\u5242\u9500\u552e",
    "\u533b\u7597\u5668\u68b0",
    "\u533b\u836f\u6d41\u901a",
    "\u4e2d\u836f",
    "\u6d88\u8d39\u533b\u7597",
    "\u533b\u9662",
    "\u901a\u7528\u68c0\u9a8c\u68c0\u6d4b",
    "\u8f6f\u4ef6\u8bb8\u53ef",
    "\u6280\u672f\u6388\u6743",
)
LIFE_SCIENCE_CXO_SUBTYPE_KEYWORDS = {
    LIFE_SCIENCE_CXO_INTEGRATED_SUBTYPE: (
        "integrated",
        "drug discovery",
        "preclinical",
        "CMC",
        "CDMO",
        "\u4e00\u4f53\u5316",
        "\u836f\u7269\u53d1\u73b0",
        "\u4e34\u5e8a\u524d",
        "\u5de5\u827a\u5f00\u53d1",
    ),
    LIFE_SCIENCE_CXO_CDMO_SUBTYPE: (
        "CDMO",
        "CMC",
        "commercial manufacturing",
        "manufacturing outsourcing",
        "\u5546\u4e1a\u5316\u751f\u4ea7",
        "\u5de5\u827a\u5f00\u53d1",
        "\u751f\u4ea7\u5916\u5305",
    ),
    LIFE_SCIENCE_CXO_CLINICAL_SUBTYPE: (
        "clinical CRO",
        "clinical trial",
        "SMO",
        "data statistics",
        "\u4e34\u5e8a CRO",
        "\u4e34\u5e8a\u8bd5\u9a8c",
        "\u4e34\u5e8a\u7814\u7a76",
        "\u6570\u636e\u7edf\u8ba1",
    ),
}
LIFE_SCIENCE_CXO_KNOWN_POSITIVES = {
    "603259": LIFE_SCIENCE_CXO_INTEGRATED_SUBTYPE,
    "300759": LIFE_SCIENCE_CXO_INTEGRATED_SUBTYPE,
    "002821": LIFE_SCIENCE_CXO_CDMO_SUBTYPE,
    "300363": LIFE_SCIENCE_CXO_CDMO_SUBTYPE,
    "300347": LIFE_SCIENCE_CXO_CLINICAL_SUBTYPE,
}
LIFE_SCIENCE_CXO_KNOWN_NEGATIVES = {"600276", "600521", "000739", "300760", "300012", "600196"}

AI_DATACENTER_DATACENTER_TERMS = (
    "data center",
    "datacenter",
    "IDC",
    "AIDC",
    "\u6570\u636e\u4e2d\u5fc3",
    "\u667a\u7b97\u4e2d\u5fc3",
    "\u7b97\u529b\u4e2d\u5fc3",
)
AI_DATACENTER_INFRA_TERMS = (
    "liquid cooling",
    "precision thermal",
    "precision cooling",
    "UPS",
    "uninterruptible power",
    "cabinet",
    "rack-up",
    "PUE",
    "MW",
    "\u6db2\u51b7",
    "\u7cbe\u5bc6\u6e29\u63a7",
    "\u7cbe\u5bc6\u7a7a\u8c03",
    "\u51b7\u5374",
    "\u4e0d\u95f4\u65ad\u7535\u6e90",
    "\u673a\u67dc",
    "\u4e0a\u67b6\u7387",
    "\u5229\u7528\u7387",
)
AI_DATACENTER_PROOF_TERMS = (
    "revenue",
    "revenue share",
    "segment revenue",
    "order",
    "contract",
    "customer",
    "operation",
    "delivery",
    "asset",
    "\u6536\u5165",
    "\u6536\u5165\u5360\u6bd4",
    "\u5206\u90e8\u6536\u5165",
    "\u8ba2\u5355",
    "\u5408\u540c",
    "\u5ba2\u6237",
    "\u8fd0\u8425",
    "\u4ea4\u4ed8",
    "\u8d44\u4ea7",
)
AI_DATACENTER_NEGATIVE_TERMS = (
    "self-built data center",
    "EPC",
    "construction",
    "defense",
    "military",
    "optical module",
    "CPO",
    "PCB",
    "server OEM",
    "server whole machine",
    "chip",
    "semiconductor",
    "\u81ea\u5efa\u6570\u636e\u4e2d\u5fc3",
    "EPC\u603b\u5305",
    "\u5efa\u7b51\u65bd\u5de5",
    "\u519b\u5de5",
    "\u56fd\u9632",
    "\u5149\u6a21\u5757",
    "\u670d\u52a1\u5668\u6574\u673a",
    "\u82af\u7247",
    "\u534a\u5bfc\u4f53",
)
AI_DATACENTER_OPERATOR_TERMS = (
    "IDC",
    "AIDC",
    "hosting",
    "colocation",
    "cabinet",
    "MW",
    "rack-up",
    "PUE",
    "\u6570\u636e\u4e2d\u5fc3\u8fd0\u8425",
    "\u673a\u67dc",
    "\u4e0a\u67b6\u7387",
    "\u5229\u7528\u7387",
)
AI_DATACENTER_POWER_TERMS = (
    "UPS",
    "uninterruptible power",
    "power distribution",
    "power infrastructure",
    "\u7535\u6e90",
    "\u914d\u7535",
    "\u4f9b\u7535",
    "\u4e0d\u95f4\u65ad\u7535\u6e90",
)
AI_DATACENTER_COOLING_TERMS = (
    "liquid cooling",
    "precision thermal",
    "precision air conditioning",
    "cooling",
    "\u6db2\u51b7",
    "\u7cbe\u5bc6\u6e29\u63a7",
    "\u7cbe\u5bc6\u7a7a\u8c03",
    "\u51b7\u5374",
    "\u6e29\u63a7",
)
AI_DATACENTER_STORAGE_PV_TERMS = (
    "energy storage",
    "photovoltaic",
    "PV",
    "\u50a8\u80fd",
    "\u5149\u4f0f",
    "\u65b0\u80fd\u6e90",
)
AI_DATACENTER_HVAC_TERMS = (
    "HVAC",
    "industrial air conditioning",
    "\u5de5\u4e1a\u7a7a\u8c03",
    "\u5546\u7528\u7a7a\u8c03",
    "\u666e\u901a\u7a7a\u8c03",
)
AI_DATACENTER_KNOWN_POSITIVES = {
    "300442": AI_DATACENTER_OPERATOR_SUBTYPE,
    "002837": AI_DATACENTER_COOLING_SUBTYPE,
}
AI_DATACENTER_KNOWN_BOUNDARIES = {
    "002335": AI_DATACENTER_POWER_SUBTYPE,
    "002518": AI_DATACENTER_POWER_SUBTYPE,
    "301018": AI_DATACENTER_COOLING_SUBTYPE,
}
AI_DATACENTER_KNOWN_NEGATIVES = {"300308", "300476", "000063", "002230"}


def _safe_json(value: Any, limit: int = 8000) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        text = str(value)
    return text[:limit]


def _score_to_confidence(score: int, strategy_type: str) -> str:
    if strategy_type == "unknown":
        return "low"
    if score >= 75:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


class StockClassifier:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else DEFAULT_CLASSIFICATION_CONFIG
        self.rules = self._load_rules()

    def classify(self, normalized: NormalizedFundamentalInput) -> StockClassificationResult:
        missing_fields = list(normalized.missing_fields)
        warnings = list(normalized.adapter_warnings)

        if self._is_severely_missing(normalized):
            missing_fields.append("classification_core_fields")
            return StockClassificationResult(
                stock_code=normalized.stock_code,
                stock_name=normalized.stock_name,
                strategy_type="unknown",
                confidence="low",
                confidence_score=20,
                reasons=["核心分类字段缺失，无法稳定识别股票基本面类型。"],
                evidence=[],
                alternative_types=[],
                missing_fields=sorted(set(missing_fields)),
                warnings=warnings,
            )

        text_sources = self._collect_text_sources(normalized)
        low_altitude_result = self._classify_low_altitude(normalized, text_sources, missing_fields, warnings)
        if low_altitude_result is not None:
            return low_altitude_result
        life_science_cxo_result = self._classify_life_science_cxo(normalized, text_sources, missing_fields, warnings)
        if life_science_cxo_result is not None:
            return life_science_cxo_result
        ai_datacenter_result = self._classify_ai_datacenter(normalized, text_sources, missing_fields, warnings)
        if ai_datacenter_result is not None:
            return ai_datacenter_result

        scores: dict[str, int] = defaultdict(int)
        evidence_by_type: dict[str, list[ClassificationEvidence]] = defaultdict(list)
        matched_source_types: dict[str, set[str]] = defaultdict(set)

        for strategy_type, rule in self.rules.items():
            if strategy_type in {"unknown", AI_DATACENTER_STRATEGY}:
                continue
            examples = rule.get("examples", []) or []
            keywords = rule.get("keywords", []) or []
            for source_field, text in text_sources.items():
                if not text:
                    continue
                weight = SOURCE_WEIGHTS[source_field]
                for example in examples:
                    if example and example in text:
                        score = weight + (20 if source_field == "stock_name" else 8)
                        scores[strategy_type] += score
                        matched_source_types[strategy_type].add(source_field)
                        evidence_by_type[strategy_type].append(
                            ClassificationEvidence(
                                source_field=source_field,
                                matched_value=example,
                                matched_rule=f"{strategy_type}.examples",
                                weight=score,
                                explanation=f"{source_field} 命中核心样例 {example}",
                            )
                        )
                for keyword in keywords:
                    if keyword and keyword in text:
                        scores[strategy_type] += weight
                        matched_source_types[strategy_type].add(source_field)
                        evidence_by_type[strategy_type].append(
                            ClassificationEvidence(
                                source_field=source_field,
                                matched_value=keyword,
                                matched_rule=f"{strategy_type}.keywords",
                                weight=weight,
                                explanation=f"{source_field} 命中关键词 {keyword}",
                            )
                        )

        if "紫金矿业" in " ".join(text_sources.values()):
            scores["resource_core"] += 120

        if not scores:
            return StockClassificationResult(
                stock_code=normalized.stock_code,
                stock_name=normalized.stock_name,
                strategy_type="unknown",
                confidence="low",
                confidence_score=25,
                reasons=["规则关键词命中不足，分类为 unknown。"],
                evidence=[],
                alternative_types=[],
                missing_fields=sorted(set(missing_fields)),
                warnings=warnings,
            )

        scores = self._apply_conflict_rules(scores, text_sources)
        scores = defaultdict(int, {key: value for key, value in scores.items() if value > 0})
        if not scores:
            return StockClassificationResult(
                stock_code=normalized.stock_code,
                stock_name=normalized.stock_name,
                strategy_type="unknown",
                confidence="low",
                confidence_score=25,
                reasons=["规则关键词命中不足，分类为 unknown。"],
                evidence=[],
                alternative_types=[],
                missing_fields=sorted(set(missing_fields)),
                warnings=warnings,
            )
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        selected_type, raw_score = sorted_scores[0]
        alternative_types = [
            item_type for item_type, score in sorted_scores[1:] if score >= 20
        ][:3]

        only_news = matched_source_types[selected_type] <= {"news", "raw_blocks"} and "news" in matched_source_types[selected_type]
        confidence_score = min(100, raw_score)
        if only_news:
            confidence_score = min(confidence_score, 74)
            warnings.append("news_only_match_confidence_capped")

        if selected_type == "theme_only" and not normalized.financial_metrics:
            confidence_score = min(max(confidence_score, 50), 74)

        if selected_type == "satellite_communication_infrastructure":
            core_text = self._core_text(text_sources)
            if not any(term in core_text for term in SATELLITE_STRONG_CORE_KEYWORDS):
                confidence_score = min(confidence_score, 74)
                warnings.append("satellite_core_business_not_strongly_confirmed_confidence_capped")

        confidence = _score_to_confidence(confidence_score, selected_type)
        reasons = [
            f"规则得分最高类型为 {selected_type}，得分 {confidence_score}。",
            self.rules.get(selected_type, {}).get("description", ""),
        ]
        if alternative_types:
            reasons.append(f"存在其他命中类型：{', '.join(alternative_types)}。")
        if only_news:
            reasons.append("仅新闻或原始文本命中，置信度不提升到 high。")

        return StockClassificationResult(
            stock_code=normalized.stock_code,
            stock_name=normalized.stock_name,
            strategy_type=selected_type,
            confidence=confidence,
            confidence_score=confidence_score,
            reasons=[reason for reason in reasons if reason],
            evidence=evidence_by_type[selected_type],
            alternative_types=alternative_types,
            missing_fields=sorted(set(missing_fields)),
            warnings=sorted(set(warnings)),
        )

    def _load_rules(self) -> dict[str, Any]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _collect_text_sources(self, normalized: NormalizedFundamentalInput) -> dict[str, str]:
        business_segments = []
        if normalized.business_composition:
            for segment in normalized.business_composition.segments:
                business_segments.append(_safe_json(segment, limit=1000))
        news_text = " ".join(
            " ".join(filter(None, [item.title, item.summary or ""])) for item in normalized.latest_news
        )
        return {
            "stock_name": normalized.stock_name or "",
            "industry": normalized.basic_info.industry or "",
            "main_business": normalized.basic_info.main_business or "",
            "business_composition": " ".join(business_segments),
            "news": news_text,
            "raw_blocks": _safe_json(normalized.raw_blocks),
        }

    def _is_severely_missing(self, normalized: NormalizedFundamentalInput) -> bool:
        if "unknown_raw_structure" in normalized.missing_fields:
            return True
        basic = normalized.basic_info
        has_identity = bool(normalized.stock_name and normalized.stock_code != "UNKNOWN")
        has_business = bool(basic.industry or basic.main_business or normalized.business_composition)
        has_text_news = bool(normalized.latest_news)
        return not has_identity and not has_business and not has_text_news

    def _core_text(self, text_sources: dict[str, str]) -> str:
        return " ".join(
            [
                text_sources.get("stock_name", ""),
                text_sources.get("main_business", ""),
                text_sources.get("industry", ""),
                text_sources.get("business_composition", ""),
            ]
        )

    def _classify_low_altitude(
        self,
        normalized: NormalizedFundamentalInput,
        text_sources: dict[str, str],
        missing_fields: list[str],
        warnings: list[str],
    ) -> StockClassificationResult | None:
        core_text = self._core_text(text_sources)
        all_text = " ".join(text_sources.values())
        aviation_core = self._has_any(core_text, LOW_ALTITUDE_AVIATION_PRIMARY)
        aviation_proof = self._has_any(all_text, LOW_ALTITUDE_AVIATION_PROOF)
        airspace_core = self._has_any(core_text, LOW_ALTITUDE_AIRSPACE_PRIMARY)
        airspace_proof = self._has_any(all_text, LOW_ALTITUDE_AIRSPACE_PROOF)

        subtype = None
        rule_name = ""
        matched_value = ""
        if airspace_core and airspace_proof:
            subtype = LOW_ALTITUDE_AIRSPACE_SUBTYPE
            rule_name = "low_altitude.tier1.airspace_platform_system"
            matched_value = self._first_hit(core_text, LOW_ALTITUDE_AIRSPACE_PRIMARY) or "airspace_platform_system"
        elif aviation_core and aviation_proof:
            subtype = LOW_ALTITUDE_AVIATION_SUBTYPE
            rule_name = "low_altitude.tier1.aviation_operations_service"
            matched_value = self._first_hit(core_text, LOW_ALTITUDE_AVIATION_PRIMARY) or "aviation_operations_service"

        positive_share = self._segment_share(normalized, LOW_ALTITUDE_RELATED_SEGMENT_KEYWORDS)
        traditional_share = self._segment_share(normalized, LOW_ALTITUDE_TRADITIONAL_SEGMENT_KEYWORDS)
        boundary_hit = self._first_hit(core_text, LOW_ALTITUDE_BOUNDARY_KEYWORDS)
        if subtype:
            if traditional_share is not None and traditional_share > 0.60 and not airspace_core:
                return self._low_altitude_boundary_result(
                    normalized,
                    missing_fields,
                    warnings,
                    boundary_hit or "traditional core segment >60%",
                    "traditional_core_segment_boundary_check",
                )
            if positive_share is not None and positive_share < 0.20 and not (aviation_proof or airspace_proof):
                return self._low_altitude_boundary_result(
                    normalized,
                    missing_fields,
                    warnings,
                    "low altitude related segment share <20%",
                    "low_altitude_revenue_share_below_threshold",
                )
            score = 62 if positive_share is not None and positive_share >= 0.20 else 55
            if boundary_hit:
                score = min(score, 58)
                warnings.append("low_altitude_boundary_keyword_present_confidence_capped")
            evidence = [
                ClassificationEvidence(
                    source_field="core_business_text",
                    matched_value=matched_value,
                    matched_rule=rule_name,
                    weight=45,
                    explanation="Tier-1 AND logic matched low-altitude infrastructure/service core text plus revenue/contract/asset/operation evidence.",
                )
            ]
            if positive_share is not None:
                evidence.append(
                    ClassificationEvidence(
                        source_field="business_composition",
                        matched_value=f"related_revenue_share={positive_share:.2%}",
                        matched_rule="low_altitude.revenue_share_boundary",
                        weight=17,
                        explanation="Business composition includes low-altitude/general-aviation/airspace related revenue share.",
                    )
                )
            reasons = [
                f"classified as {LOW_ALTITUDE_STRATEGY} with sub_type={subtype} by Tier-1 AND logic.",
                "This framework covers infrastructure/operation service only, not low-altitude concept exposure or aircraft/drone manufacturing.",
            ]
            if subtype == LOW_ALTITUDE_AVIATION_SUBTYPE:
                reasons.append("Aviation operations service requires fleet, operating hours, flight sorties, safety and regulatory evidence before high confidence.")
            else:
                reasons.append("Airspace platform system requires contract amount, project acceptance, customer structure and collection evidence before high confidence.")
            return StockClassificationResult(
                stock_code=normalized.stock_code,
                stock_name=normalized.stock_name,
                strategy_type=LOW_ALTITUDE_STRATEGY,
                sub_type=subtype,
                confidence=_score_to_confidence(score, LOW_ALTITUDE_STRATEGY),
                confidence_score=score,
                reasons=reasons,
                evidence=evidence,
                alternative_types=[],
                missing_fields=sorted(set(missing_fields)),
                warnings=sorted(set(warnings)),
            )

        boundary_reason = boundary_hit
        if boundary_reason is None and traditional_share is not None and traditional_share > 0.60:
            boundary_reason = "traditional core segment >60%"
        if boundary_reason and self._is_low_altitude_boundary_context(core_text, all_text):
            strategy_type = "theme_only" if self._has_low_altitude_theme(all_text) else "unknown"
            score = 35 if strategy_type == "theme_only" else 25
            return self._low_altitude_boundary_result(
                normalized,
                missing_fields,
                warnings,
                boundary_reason,
                "low_altitude.boundary_exclusion",
                strategy_type=strategy_type,
                score=score,
            )
        if self._has_any(core_text, ("\u6469\u6258\u8f66\u53d1\u52a8\u673a", "\u53d1\u52a8\u673a\u53ca\u96f6\u914d\u4ef6", "\u673a\u68b0\u5236\u9020\u4e1a")):
            return self._low_altitude_boundary_result(
                normalized,
                missing_fields,
                warnings,
                "engine/mechanical parts boundary exclusion",
                "low_altitude.engine_mechanical_boundary_exclusion",
                strategy_type="unknown",
                score=25,
            )
        if self._has_low_altitude_theme(all_text):
            return StockClassificationResult(
                stock_code=normalized.stock_code,
                stock_name=normalized.stock_name,
                strategy_type="theme_only",
                confidence="low",
                confidence_score=35,
                reasons=[
                    "Low-altitude theme appeared, but Tier-1 AND evidence for infrastructure/operation service was not met.",
                    "Defaulted to theme_only instead of applying low-altitude infrastructure framework.",
                ],
                evidence=[
                    ClassificationEvidence(
                        source_field="text_sources",
                        matched_value="low-altitude theme without Tier-1 evidence",
                        matched_rule="low_altitude.theme_only_guard",
                        weight=20,
                        explanation="Theme words alone are not operating revenue, contract, asset, operation volume or project acceptance evidence.",
                    )
                ],
                alternative_types=[],
                missing_fields=sorted(set(missing_fields)),
                warnings=sorted(set(warnings + ["low_altitude_theme_only_guard_applied"])),
            )
        return None

    def _low_altitude_boundary_result(
        self,
        normalized: NormalizedFundamentalInput,
        missing_fields: list[str],
        warnings: list[str],
        boundary_reason: str,
        matched_rule: str,
        strategy_type: str = "unknown",
        score: int = 25,
    ) -> StockClassificationResult:
        return StockClassificationResult(
            stock_code=normalized.stock_code,
            stock_name=normalized.stock_name,
            strategy_type=strategy_type,
            confidence=_score_to_confidence(score, strategy_type),
            confidence_score=score,
            reasons=[
                f"Low-altitude boundary exclusion applied: {boundary_reason}.",
                "The company was not routed into low_altitude_economy_infrastructure because manufacturing, component, airport, finance, military, remote-sensing, or theme-only evidence is outside v1 scope.",
            ],
            evidence=[
                ClassificationEvidence(
                    source_field="core_business_text",
                    matched_value=str(boundary_reason),
                    matched_rule=matched_rule,
                    weight=20,
                    explanation="Boundary guard prevents low-altitude theme contamination from falling into unrelated frameworks.",
                )
            ],
            alternative_types=[],
            missing_fields=sorted(set(missing_fields)),
            warnings=sorted(set(warnings + ["low_altitude_boundary_exclusion_applied"])),
        )

    def _classify_life_science_cxo(
        self,
        normalized: NormalizedFundamentalInput,
        text_sources: dict[str, str],
        missing_fields: list[str],
        warnings: list[str],
    ) -> StockClassificationResult | None:
        core_text = self._core_text(text_sources)
        all_text = " ".join(text_sources.values())
        code = "".join(ch for ch in str(normalized.stock_code) if ch.isdigit()).zfill(6)[-6:]
        cxo_core = self._has_any(core_text, LIFE_SCIENCE_CXO_PRIMARY)
        cxo_any = self._has_any(all_text, LIFE_SCIENCE_CXO_PRIMARY)
        proof_any = self._has_any(all_text, LIFE_SCIENCE_CXO_PROOF)
        cxo_share = self._segment_share(normalized, LIFE_SCIENCE_CXO_SEGMENT_KEYWORDS)
        pharma_product_share = self._segment_share(normalized, LIFE_SCIENCE_PHARMA_PRODUCT_SEGMENT_KEYWORDS)
        negative_hit = self._first_hit(core_text, LIFE_SCIENCE_CXO_NEGATIVE_KEYWORDS)
        known_subtype = LIFE_SCIENCE_CXO_KNOWN_POSITIVES.get(code)

        if code in LIFE_SCIENCE_CXO_KNOWN_NEGATIVES and (cxo_any or negative_hit):
            return self._life_science_cxo_boundary_result(
                normalized,
                missing_fields,
                warnings,
                negative_hit or "known negative/boundary sample",
                "life_science_cxo.known_negative_boundary",
            )

        if (
            not known_subtype
            and pharma_product_share is not None
            and pharma_product_share > 0.60
            and (cxo_share is None or cxo_share < 0.50)
        ):
            return self._life_science_cxo_boundary_result(
                normalized,
                missing_fields,
                warnings,
                "API/formulation/drug-product revenue share >60% without independently confirmed CXO service revenue",
                "life_science_cxo.api_formulation_boundary",
            )

        if negative_hit and not known_subtype and (cxo_share is None or cxo_share < 0.50):
            if cxo_any:
                return self._life_science_cxo_boundary_result(
                    normalized,
                    missing_fields,
                    warnings,
                    negative_hit,
                    "life_science_cxo.negative_boundary",
                    strategy_type="theme_only" if not cxo_core else "unknown",
                    score=35 if not cxo_core else 25,
                )
            return None

        should_classify = False
        if cxo_share is not None and cxo_share >= 0.50 and cxo_core and proof_any:
            should_classify = True
        elif known_subtype and cxo_core and proof_any:
            should_classify = True
        elif cxo_share is not None and 0.30 <= cxo_share < 0.50 and cxo_core and proof_any:
            warnings.append("life_science_cxo_revenue_share_boundary_check_confidence_capped")
            should_classify = True
        elif known_subtype and (normalized.financial_metrics or normalized.business_composition):
            warnings.append("life_science_cxo_known_positive_sample_code_fallback_confidence_capped")
            should_classify = True

        if should_classify:
            subtype = known_subtype or self._infer_life_science_cxo_subtype(all_text)
            if subtype is None:
                subtype = LIFE_SCIENCE_CXO_INTEGRATED_SUBTYPE
                warnings.append("life_science_cxo_sub_type_unconfirmed_confidence_capped")
            score = 62 if cxo_share is not None and cxo_share >= 0.50 else 55
            if known_subtype and not (cxo_core and proof_any):
                score = min(score, 50)
            if cxo_share is None or cxo_share < 0.50:
                score = min(score, 58)
                warnings.append("life_science_cxo_revenue_share_not_fully_confirmed_confidence_capped")
            if code == "300363":
                warnings.append("high_volatility_cdmo_sample_one_off_order_caution")
                score = min(score, 58)
            evidence = [
                ClassificationEvidence(
                    source_field="core_business_text",
                    matched_value=self._first_hit(core_text, LIFE_SCIENCE_CXO_PRIMARY) or LIFE_SCIENCE_CXO_STRATEGY,
                    matched_rule="life_science_cxo.tier1.and_logic",
                    weight=45,
                    explanation="Tier-1 AND logic matched CXO/CRO/CDMO/CMC service text plus revenue/order/contract/capacity/project/business evidence.",
                )
            ]
            if cxo_share is not None:
                evidence.append(
                    ClassificationEvidence(
                        source_field="business_composition",
                        matched_value=f"cxo_related_revenue_share={cxo_share:.2%}",
                        matched_rule="life_science_cxo.revenue_share_threshold",
                        weight=17,
                        explanation="Business composition supports CXO/CRO/CDMO related revenue share. Revenue share proves business structure, not order quality.",
                    )
                )
            reasons = [
                f"classified as {LIFE_SCIENCE_CXO_STRATEGY} with sub_type={subtype} by conservative Tier-1 AND logic.",
                "This framework covers life-science R&D/manufacturing outsourcing services, not self-owned innovative drug pipelines, ordinary pharma manufacturing, devices, distribution, TCM or theme-only news.",
                "Backlog, new orders, customer concentration, overseas exposure, capacity utilization and clinical project progress remain confidence-gating evidence.",
            ]
            return StockClassificationResult(
                stock_code=normalized.stock_code,
                stock_name=normalized.stock_name,
                strategy_type=LIFE_SCIENCE_CXO_STRATEGY,
                sub_type=subtype,
                confidence=_score_to_confidence(score, LIFE_SCIENCE_CXO_STRATEGY),
                confidence_score=score,
                reasons=reasons,
                evidence=evidence,
                alternative_types=[],
                missing_fields=sorted(set(missing_fields)),
                warnings=sorted(set(warnings)),
            )

        if cxo_any:
            return StockClassificationResult(
                stock_code=normalized.stock_code,
                stock_name=normalized.stock_name,
                strategy_type="theme_only",
                confidence="low",
                confidence_score=35,
                reasons=[
                    "CXO/CRO/CDMO theme appeared, but revenue-share and core-business Tier-1 evidence were not sufficient.",
                    "Defaulted to theme_only instead of applying life_science_cxo_services.",
                ],
                evidence=[
                    ClassificationEvidence(
                        source_field="text_sources",
                        matched_value="CXO/CRO/CDMO theme without revenue-share/core-business support",
                        matched_rule="life_science_cxo.theme_only_guard",
                        weight=20,
                        explanation="Concept words, R&D cooperation news or outsourcing references alone are not CXO service revenue evidence.",
                    )
                ],
                alternative_types=[],
                missing_fields=sorted(set(missing_fields)),
                warnings=sorted(set(warnings + ["life_science_cxo_theme_only_guard_applied"])),
            )
        return None

    def _infer_life_science_cxo_subtype(self, text: str) -> str | None:
        if self._has_any(text, LIFE_SCIENCE_CXO_SUBTYPE_KEYWORDS[LIFE_SCIENCE_CXO_CLINICAL_SUBTYPE]):
            return LIFE_SCIENCE_CXO_CLINICAL_SUBTYPE
        if self._has_any(text, LIFE_SCIENCE_CXO_SUBTYPE_KEYWORDS[LIFE_SCIENCE_CXO_CDMO_SUBTYPE]):
            if not self._has_any(text, ("drug discovery", "\u836f\u7269\u53d1\u73b0", "preclinical", "\u4e34\u5e8a\u524d")):
                return LIFE_SCIENCE_CXO_CDMO_SUBTYPE
        if self._has_any(text, LIFE_SCIENCE_CXO_SUBTYPE_KEYWORDS[LIFE_SCIENCE_CXO_INTEGRATED_SUBTYPE]):
            return LIFE_SCIENCE_CXO_INTEGRATED_SUBTYPE
        return None

    def _life_science_cxo_boundary_result(
        self,
        normalized: NormalizedFundamentalInput,
        missing_fields: list[str],
        warnings: list[str],
        boundary_reason: str,
        matched_rule: str,
        strategy_type: str = "unknown",
        score: int = 25,
    ) -> StockClassificationResult:
        return StockClassificationResult(
            stock_code=normalized.stock_code,
            stock_name=normalized.stock_name,
            strategy_type=strategy_type,
            confidence=_score_to_confidence(score, strategy_type),
            confidence_score=score,
            reasons=[
                f"Life-science CXO boundary exclusion applied: {boundary_reason}.",
                "The company was not routed into life_science_cxo_services because v1 requires confirmed outsourcing-service business exposure, not pipeline, product manufacturing, device, distribution, testing, software or news-only evidence.",
            ],
            evidence=[
                ClassificationEvidence(
                    source_field="core_business_text",
                    matched_value=str(boundary_reason),
                    matched_rule=matched_rule,
                    weight=20,
                    explanation="Boundary guard prevents CXO concept or adjacent healthcare exposure from contaminating the life-science outsourcing service framework.",
                )
            ],
            alternative_types=[],
            missing_fields=sorted(set(missing_fields)),
            warnings=sorted(set(warnings + ["life_science_cxo_boundary_exclusion_applied"])),
        )

    def _classify_ai_datacenter(
        self,
        normalized: NormalizedFundamentalInput,
        text_sources: dict[str, str],
        missing_fields: list[str],
        warnings: list[str],
    ) -> StockClassificationResult | None:
        core_text = self._core_text(text_sources)
        all_text = " ".join(text_sources.values())
        code = "".join(ch for ch in str(normalized.stock_code) if ch.isdigit()).zfill(6)[-6:]

        datacenter_any = self._has_any(all_text, AI_DATACENTER_DATACENTER_TERMS)
        infra_any = self._has_any(all_text, AI_DATACENTER_INFRA_TERMS)
        proof_any = self._has_any(all_text, AI_DATACENTER_PROOF_TERMS)
        negative_hit = self._first_hit(core_text, AI_DATACENTER_NEGATIVE_TERMS) or self._first_hit(
            all_text, AI_DATACENTER_NEGATIVE_TERMS
        )
        known_subtype = AI_DATACENTER_KNOWN_POSITIVES.get(code) or AI_DATACENTER_KNOWN_BOUNDARIES.get(code)

        if code in AI_DATACENTER_KNOWN_NEGATIVES and (datacenter_any or infra_any):
            warnings.append("ai_datacenter_known_negative_exclusion_applied")
            return None
        if negative_hit and not known_subtype:
            if datacenter_any and not any(
                scores_term in all_text
                for scores_term in ("revenue", "\u6536\u5165", "order", "\u8ba2\u5355", "customer", "\u5ba2\u6237")
            ):
                return StockClassificationResult(
                    stock_code=normalized.stock_code,
                    stock_name=normalized.stock_name,
                    strategy_type="theme_only",
                    confidence="low",
                    confidence_score=35,
                    reasons=[
                        "AI datacenter wording appeared, but negative supply-chain or self-built/EPC boundary terms prevent routing to ai_datacenter_infrastructure.",
                        "PCB, optical modules, server OEMs, chips, semiconductors, self-built datacenters and EPC/construction are outside this v1 framework.",
                    ],
                    evidence=[
                        ClassificationEvidence(
                            source_field="core_business_text",
                            matched_value=negative_hit,
                            matched_rule="ai_datacenter.negative_boundary",
                            weight=20,
                            explanation="Boundary guard prevents AI datacenter theme wording from absorbing excluded supply-chain or construction models.",
                        )
                    ],
                    alternative_types=[],
                    missing_fields=sorted(set(missing_fields)),
                    warnings=sorted(set(warnings + ["ai_datacenter_boundary_exclusion_applied"])),
                )
            return None

        revenue_share = self._ai_datacenter_segment_share(normalized)
        has_specific_evidence = revenue_share is not None or self._has_any(
            all_text,
            (
                "datacenter order",
                "data center order",
                "datacenter customer",
                "data center customer",
                "customer contract",
                "IDC asset",
                "cabinet",
                "MW",
                "\u6570\u636e\u4e2d\u5fc3\u8ba2\u5355",
                "\u6570\u636e\u4e2d\u5fc3\u5ba2\u6237",
                "\u5ba2\u6237\u5408\u540c",
                "\u673a\u67dc",
            ),
        )
        tier1 = datacenter_any and infra_any and proof_any and not negative_hit
        known_with_foundation = (
            known_subtype is not None
            and bool(normalized.financial_metrics or normalized.business_composition)
        )

        if tier1 and (has_specific_evidence or known_subtype is not None):
            subtype = known_subtype or self._infer_ai_datacenter_subtype(all_text)
            if subtype is None:
                warnings.append("ai_datacenter_sub_type_unconfirmed_confidence_capped")
                return self._ai_datacenter_theme_only_result(
                    normalized,
                    missing_fields,
                    warnings,
                    "Tier-1 text matched but no formal v1 sub_type could be verified.",
                )
            score = 62 if revenue_share is not None else 55
            if code in AI_DATACENTER_KNOWN_BOUNDARIES:
                score = min(score, 50)
                warnings.append("ai_datacenter_known_boundary_sample_confidence_capped")
            if subtype == AI_DATACENTER_POWER_SUBTYPE and (
                self._has_any(all_text, AI_DATACENTER_STORAGE_PV_TERMS) or code in {"002335", "002518"}
            ):
                score = min(score, 50)
                warnings.append("ai_datacenter_power_storage_pv_boundary_confidence_capped")
            if subtype == AI_DATACENTER_COOLING_SUBTYPE and (
                self._has_any(all_text, AI_DATACENTER_HVAC_TERMS) or code == "301018"
            ):
                score = min(score, 55)
                warnings.append("ai_datacenter_cooling_hvac_boundary_confidence_capped")
            evidence = [
                ClassificationEvidence(
                    source_field="text_sources",
                    matched_value=self._first_hit(all_text, AI_DATACENTER_DATACENTER_TERMS) or AI_DATACENTER_STRATEGY,
                    matched_rule="ai_datacenter.tier1.and_logic",
                    weight=45,
                    explanation="Tier-1 AND logic matched datacenter + infrastructure metric/product + revenue/order/customer/operation/delivery evidence, with exclusion guard applied.",
                )
            ]
            if revenue_share is not None:
                evidence.append(
                    ClassificationEvidence(
                        source_field="business_composition",
                        matched_value=f"ai_datacenter_related_revenue_share={revenue_share:.2%}",
                        matched_rule="ai_datacenter.revenue_share_evidence",
                        weight=15,
                        explanation="Business composition supports datacenter-related segment exposure. It does not prove order realization, utilization or customer capex conversion.",
                    )
                )
            return StockClassificationResult(
                stock_code=normalized.stock_code,
                stock_name=normalized.stock_name,
                strategy_type=AI_DATACENTER_STRATEGY,
                sub_type=subtype,
                confidence=_score_to_confidence(score, AI_DATACENTER_STRATEGY),
                confidence_score=score,
                reasons=[
                    f"classified as {AI_DATACENTER_STRATEGY} with sub_type={subtype} by conservative Tier-1 AND logic.",
                    "This framework covers IDC/AIDC operation, datacenter power/UPS/distribution, and datacenter cooling/liquid-cooling infrastructure only.",
                    "Theme wording, capex, contract liabilities and customer capex expectations are not treated as confirmed order or revenue realization.",
                ],
                evidence=evidence,
                alternative_types=["right_trend_growth"],
                missing_fields=sorted(set(missing_fields)),
                warnings=sorted(set(warnings)),
            )

        if known_with_foundation:
            subtype = known_subtype
            score = 50
            warnings.append("ai_datacenter_known_sample_requires_manual_evidence_confidence_capped")
            if code in AI_DATACENTER_KNOWN_BOUNDARIES:
                score = 45
            return StockClassificationResult(
                stock_code=normalized.stock_code,
                stock_name=normalized.stock_name,
                strategy_type=AI_DATACENTER_STRATEGY,
                sub_type=subtype,
                confidence=_score_to_confidence(score, AI_DATACENTER_STRATEGY),
                confidence_score=score,
                reasons=[
                    f"Known v1 ai_datacenter_infrastructure sample routed with sub_type={subtype}, but confidence is capped because full Tier-1 evidence is incomplete.",
                    "Business composition and sub-type operating/order/customer evidence remain required before stronger conclusions.",
                ],
                evidence=[
                    ClassificationEvidence(
                        source_field="stock_code",
                        matched_value=code,
                        matched_rule="ai_datacenter.known_sample_boundary_fallback",
                        weight=30,
                        explanation="Known v1 sample fallback preserves routing while keeping confidence conservative.",
                    )
                ],
                alternative_types=["right_trend_growth"],
                missing_fields=sorted(set(missing_fields)),
                warnings=sorted(set(warnings)),
            )

        if datacenter_any:
            return self._ai_datacenter_theme_only_result(
                normalized,
                missing_fields,
                warnings,
                "AI datacenter theme appeared, but Tier-1 AND evidence and confirmable revenue/order/customer/asset/operation proof were not sufficient.",
            )
        return None

    def _infer_ai_datacenter_subtype(self, text: str) -> str | None:
        if self._has_any(text, AI_DATACENTER_POWER_TERMS):
            return AI_DATACENTER_POWER_SUBTYPE
        if self._has_any(text, AI_DATACENTER_COOLING_TERMS):
            return AI_DATACENTER_COOLING_SUBTYPE
        if self._has_any(text, AI_DATACENTER_OPERATOR_TERMS):
            return AI_DATACENTER_OPERATOR_SUBTYPE
        return None

    def _ai_datacenter_segment_share(self, normalized: NormalizedFundamentalInput) -> float | None:
        return self._segment_share(
            normalized,
            AI_DATACENTER_DATACENTER_TERMS
            + AI_DATACENTER_OPERATOR_TERMS
            + AI_DATACENTER_POWER_TERMS
            + AI_DATACENTER_COOLING_TERMS,
        )

    def _ai_datacenter_theme_only_result(
        self,
        normalized: NormalizedFundamentalInput,
        missing_fields: list[str],
        warnings: list[str],
        reason: str,
    ) -> StockClassificationResult:
        return StockClassificationResult(
            stock_code=normalized.stock_code,
            stock_name=normalized.stock_name,
            strategy_type="theme_only",
            confidence="low",
            confidence_score=35,
            reasons=[
                reason,
                "Defaulted to theme_only instead of applying ai_datacenter_infrastructure; v1 requires datacenter revenue/order/customer/asset/operation evidence.",
            ],
            evidence=[
                ClassificationEvidence(
                    source_field="text_sources",
                    matched_value="AI datacenter theme without sufficient v1 evidence",
                    matched_rule="ai_datacenter.theme_only_guard",
                    weight=20,
                    explanation="Theme words alone are not revenue, order, customer, delivery, utilization or operating evidence.",
                )
            ],
            alternative_types=[],
            missing_fields=sorted(set(missing_fields)),
            warnings=sorted(set(warnings + ["ai_datacenter_theme_only_guard_applied"])),
        )

    def _has_any(self, text: str, terms: tuple[str, ...]) -> bool:
        lower = text.lower()
        return any(term and term.lower() in lower for term in terms)

    def _first_hit(self, text: str, terms: tuple[str, ...]) -> str | None:
        lower = text.lower()
        for term in terms:
            if term and term.lower() in lower:
                return term
        return None

    def _has_low_altitude_theme(self, text: str) -> bool:
        return self._has_any(text, ("\u4f4e\u7a7a\u7ecf\u6d4e", "\u4f4e\u7a7a", "low-altitude economy"))

    def _is_low_altitude_boundary_context(self, core_text: str, all_text: str) -> bool:
        return self._has_low_altitude_theme(all_text) or self._has_any(
            core_text,
            (
                "\u901a\u822a",
                "\u65e0\u4eba\u673a",
                "eVTOL",
                "evtol",
                "\u98de\u884c\u6c7d\u8f66",
                "\u822a\u7a7a\u53d1\u52a8\u673a",
                "\u822a\u7a7a\u96f6\u90e8\u4ef6",
                "\u9065\u611f",
                "\u6d4b\u7ed8",
                "\u519b\u5de5",
            ),
        )

    def _segment_share(
        self, normalized: NormalizedFundamentalInput, keywords: tuple[str, ...]
    ) -> float | None:
        if not normalized.business_composition:
            return None
        best: float | None = None
        for segment in normalized.business_composition.segments:
            if not isinstance(segment, dict):
                continue
            text = _safe_json(segment, limit=2000).lower()
            if not any(keyword.lower() in text for keyword in keywords):
                continue
            value = self._ratio_value(segment.get("revenue_ratio"))
            if value is None:
                continue
            best = value if best is None else max(best, value)
        return best

    def _ratio_value(self, value: Any) -> float | None:
        if isinstance(value, dict):
            value = value.get("raw_value", value.get("value"))
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number > 1 and number <= 100:
            number = number / 100
        return number

    def _apply_conflict_rules(self, scores: dict[str, int], text_sources: dict[str, str]) -> dict[str, int]:
        combined_core_text = self._core_text(text_sources)
        all_text = " ".join(text_sources.values())

        if "紫金矿业" in all_text:
            scores["resource_core"] += 120
        if any(term in all_text for term in ("全球矿业", "多矿种", "资源龙头", "大型矿企")):
            scores["resource_core"] += 35

        if scores.get("resource_swing", 0) and scores.get("resource_core", 0):
            if any(term in combined_core_text for term in CORE_TIEBREAKERS["resource_core"]):
                scores["resource_core"] += 35
            if any(term in combined_core_text for term in CORE_TIEBREAKERS["resource_swing"]):
                scores["resource_swing"] += 25

        if scores.get("right_trend_growth", 0) and scores.get("semiconductor_cycle", 0):
            if any(term in all_text for term in CORE_TIEBREAKERS["semiconductor_cycle"]):
                scores["semiconductor_cycle"] += 35
            if any(term in all_text for term in CORE_TIEBREAKERS["right_trend_growth"]):
                scores["right_trend_growth"] += 25

        if scores.get("semiconductor_cycle", 0) and any(
            term in combined_core_text
            for term in ("通信设备制造", "军用通信终端", "导航芯片", "北斗芯片", "军工电子终端")
        ):
            scores["semiconductor_cycle"] = 0

        if scores.get("right_trend_growth", 0) and scores.get("advanced_manufacturing_growth", 0):
            if any(term in all_text for term in CORE_TIEBREAKERS["advanced_manufacturing_growth"]):
                scores["advanced_manufacturing_growth"] += 40
            if any(term in all_text for term in CORE_TIEBREAKERS["right_trend_growth"]):
                scores["right_trend_growth"] += 35

        if scores.get("stable_growth", 0) and scores.get("right_trend_growth", 0):
            if any(term in all_text for term in CORE_TIEBREAKERS["stable_growth"]):
                scores["stable_growth"] += 35
            if any(term in all_text for term in CORE_TIEBREAKERS["right_trend_growth"]):
                scores["right_trend_growth"] += 25

        if scores.get("stable_growth", 0) and scores.get("advanced_manufacturing_growth", 0):
            if any(term in all_text for term in CORE_TIEBREAKERS["stable_growth"]):
                scores["stable_growth"] += 35
            if any(term in all_text for term in CORE_TIEBREAKERS["advanced_manufacturing_growth"]):
                scores["advanced_manufacturing_growth"] += 40

        if scores.get("satellite_communication_infrastructure", 0):
            core_negative_hits = [term for term in SATELLITE_NEGATIVE_KEYWORDS if term in combined_core_text]
            if core_negative_hits:
                scores["satellite_communication_infrastructure"] = 0
                if any(term in all_text for term in ("概念", "题材", "互动平台", "商业航天")):
                    scores["theme_only"] += 20
            elif any(term in combined_core_text for term in SATELLITE_STRONG_CORE_KEYWORDS):
                scores["satellite_communication_infrastructure"] += 45
            elif "中国卫通" in combined_core_text:
                scores["satellite_communication_infrastructure"] += 45

        return scores


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify normalized fundamental input and show framework.")
    parser.add_argument("--input", required=True, help="Path to raw or normalized fixture JSON")
    args = parser.parse_args()

    adapter = FundamentalDataAdapter()
    normalized = adapter.from_file(args.input)
    classification = StockClassifier().classify(normalized)
    framework = FrameworkSelector().select(classification)

    print(f"stock_code: {classification.stock_code}")
    print(f"stock_name: {classification.stock_name}")
    print(f"strategy_type: {classification.strategy_type}")
    print(f"confidence: {classification.confidence}")
    print(f"confidence_score: {classification.confidence_score}")
    print(f"reasons: {classification.reasons}")
    print(f"alternative_types: {classification.alternative_types}")
    print(f"missing_fields: {classification.missing_fields}")
    print(f"framework.display_name: {framework.display_name}")
    print(f"framework.required_focus: {framework.required_focus}")
    print(f"framework.must_track_indicators: {framework.must_track_indicators}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
