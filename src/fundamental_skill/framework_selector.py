# -*- coding: utf-8 -*-
"""Select fundamental analysis framework templates by strategy type."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .classification_schema import FundamentalFramework, StockClassificationResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FRAMEWORK_CONFIG = PROJECT_ROOT / "config" / "industry_frameworks.yaml"


class FrameworkSelector:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else DEFAULT_FRAMEWORK_CONFIG
        self._frameworks = self._load_frameworks()

    def get_framework(self, strategy_type: str) -> FundamentalFramework:
        payload = self._frameworks.get(strategy_type) or self._frameworks["unknown"]
        return FundamentalFramework(strategy_type=payload["strategy_type"], **payload["data"])

    def select(self, classification: StockClassificationResult) -> FundamentalFramework:
        return self.get_framework(classification.strategy_type)

    def _load_frameworks(self) -> dict[str, dict[str, Any]]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        frameworks: dict[str, dict[str, Any]] = {}
        for strategy_type, data in raw.items():
            frameworks[strategy_type] = {"strategy_type": strategy_type, "data": data or {}}
        if "unknown" not in frameworks:
            raise ValueError("industry framework config must include unknown")
        return frameworks
