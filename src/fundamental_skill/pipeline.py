# -*- coding: utf-8 -*-
"""Facade for running the complete deterministic fundamental_skill pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .analysis_context_builder import AnalysisContextBuilder
from .data_adapter import FundamentalDataAdapter
from .data_readiness_planner import DataReadinessPlanner
from .framework_selector import FrameworkSelector
from .result_assembler import FundamentalResultAssembler
from .schema import FundamentalAnalysisResult
from .scoring_engine import FundamentalScoringEngine
from .stock_classifier import StockClassifier
from .validators import assert_valid_result


class FundamentalSkillPipeline:
    """Single entry point for raw JSON -> FundamentalAnalysisResult."""

    def __init__(self) -> None:
        self.adapter = FundamentalDataAdapter()
        self.classifier = StockClassifier()
        self.framework_selector = FrameworkSelector()
        self.readiness_planner = DataReadinessPlanner()
        self.context_builder = AnalysisContextBuilder()
        self.scoring_engine = FundamentalScoringEngine()
        self.result_assembler = FundamentalResultAssembler()
        self.last_trace: dict[str, Any] | None = None

    def analyze_from_file(
        self,
        raw_data_path: str,
        user_thesis: str | None = None,
        output_path: str | None = None,
    ) -> FundamentalAnalysisResult:
        try:
            normalized = self.adapter.from_file(raw_data_path)
        except Exception as exc:  # pragma: no cover - defensive context wrapper
            raise RuntimeError(f"FundamentalSkillPipeline failed at data_adapter.from_file: {exc}") from exc
        return self._run_from_normalized(normalized, user_thesis=user_thesis, output_path=output_path)

    def analyze_from_dict(
        self,
        raw_data: dict,
        user_thesis: str | None = None,
        output_path: str | None = None,
    ) -> FundamentalAnalysisResult:
        try:
            normalized = self.adapter.from_dict(raw_data)
        except Exception as exc:  # pragma: no cover - defensive context wrapper
            raise RuntimeError(f"FundamentalSkillPipeline failed at data_adapter.from_dict: {exc}") from exc
        return self._run_from_normalized(normalized, user_thesis=user_thesis, output_path=output_path)

    def _run_from_normalized(
        self,
        normalized,
        user_thesis: str | None,
        output_path: str | None,
    ) -> FundamentalAnalysisResult:
        try:
            classification = self.classifier.classify(normalized)
        except Exception as exc:
            raise RuntimeError(f"FundamentalSkillPipeline failed at StockClassifier: {exc}") from exc

        try:
            framework = self.framework_selector.select(classification)
        except Exception as exc:
            raise RuntimeError(f"FundamentalSkillPipeline failed at FrameworkSelector: {exc}") from exc

        try:
            readiness = self.readiness_planner.plan(normalized, classification, framework)
        except Exception as exc:
            raise RuntimeError(f"FundamentalSkillPipeline failed at DataReadinessPlanner: {exc}") from exc

        try:
            context = self.context_builder.build(normalized, classification, framework, readiness)
        except Exception as exc:
            raise RuntimeError(f"FundamentalSkillPipeline failed at AnalysisContextBuilder: {exc}") from exc

        try:
            scoring = self.scoring_engine.score(normalized, classification, framework, readiness, context)
        except Exception as exc:
            raise RuntimeError(f"FundamentalSkillPipeline failed at FundamentalScoringEngine: {exc}") from exc

        try:
            result = self.result_assembler.assemble(
                normalized,
                classification,
                framework,
                readiness,
                context,
                scoring,
                user_thesis=user_thesis,
            )
            assert_valid_result(result)
        except Exception as exc:
            raise RuntimeError(f"FundamentalSkillPipeline failed at FundamentalResultAssembler: {exc}") from exc

        self.last_trace = self._build_trace(
            normalized=normalized,
            classification=classification,
            readiness=readiness,
            context=context,
            scoring=scoring,
            result=result,
        )

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

        return result

    def _build_trace(self, normalized, classification, readiness, context, scoring, result) -> dict[str, Any]:
        warnings = []
        warnings.extend(normalized.adapter_warnings)
        warnings.extend(classification.warnings)
        warnings.extend(readiness.confidence_penalty_reasons)
        warnings.extend(context.context_warnings)
        warnings.extend(scoring.scoring_warnings)
        return {
            "stock_code": result.stock_code,
            "stock_name": result.stock_name,
            "strategy_type": classification.strategy_type,
            "classification_confidence": classification.confidence,
            "readiness_score": readiness.readiness_score,
            "readiness_level": readiness.readiness_level,
            "context_quality": context.overall_context_quality,
            "max_overall_confidence": context.max_overall_confidence,
            "weighted_total_score": scoring.weighted_total_score,
            "score_confidence": scoring.score_confidence,
            "final_status": result.status,
            "final_confidence": result.confidence,
            "final_score": result.fundamental_score,
            "warnings": list(dict.fromkeys(warnings)),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic fundamental_skill pipeline.")
    parser.add_argument("--input", required=True, help="Path to raw JSON")
    parser.add_argument("--output", required=False, help="Optional output JSON path")
    parser.add_argument("--user-thesis", required=False, default=None, help="Optional user thesis text")
    args = parser.parse_args()

    pipeline = FundamentalSkillPipeline()
    result = pipeline.analyze_from_file(args.input, user_thesis=args.user_thesis, output_path=args.output)
    trace = pipeline.last_trace or {}

    print(f"stock_code: {result.stock_code}")
    print(f"stock_name: {result.stock_name}")
    print(f"strategy_type: {result.strategy_type}")
    print(f"status: {result.status}")
    print(f"confidence: {result.confidence}")
    print(f"fundamental_score: {result.fundamental_score}")
    print(f"readiness_level: {trace.get('readiness_level')}")
    print(f"context_quality: {trace.get('context_quality')}")
    print(f"score_confidence: {trace.get('score_confidence')}")
    print(f"risk_flags count: {len(result.risk_flags)}")
    print(f"must_track_indicators count: {len(result.must_track_indicators)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
