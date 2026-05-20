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
    "stable_growth": ("电网", "变压器", "特高压", "输配电", "电网自动化"),
}


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
        scores: dict[str, int] = defaultdict(int)
        evidence_by_type: dict[str, list[ClassificationEvidence]] = defaultdict(list)
        matched_source_types: dict[str, set[str]] = defaultdict(set)

        for strategy_type, rule in self.rules.items():
            if strategy_type == "unknown":
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

    def _apply_conflict_rules(self, scores: dict[str, int], text_sources: dict[str, str]) -> dict[str, int]:
        combined_core_text = " ".join(
            [text_sources.get("stock_name", ""), text_sources.get("main_business", ""), text_sources.get("industry", "")]
        )
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
