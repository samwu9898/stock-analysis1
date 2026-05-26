# -*- coding: utf-8 -*-
"""Isolated artifact paths and writers for provider comparison dry-runs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


BASE_ARTIFACT_NAMES: tuple[str, ...] = (
    "akshare_raw.json",
    "tushare_raw.json",
    "akshare_fundamental.json",
    "tushare_fundamental.json",
    "akshare_evidence_pack.json",
    "tushare_evidence_pack.json",
    "diff_report.json",
    "diff_report.md",
)

P1_ARTIFACT_NAMES: tuple[str, ...] = (
    "akshare_research_questions_p1.json",
    "tushare_research_questions_p1.json",
    "akshare_research_intelligence_p1.json",
    "tushare_research_intelligence_p1.json",
)


class ComparisonArtifactError(RuntimeError):
    """Artifact boundary failure for comparison-only writes."""


@dataclass(frozen=True)
class CodeComparisonArtifacts:
    """Artifact paths for a single stock code."""

    code: str
    code_dir: Path
    paths: dict[str, Path]


@dataclass(frozen=True)
class ComparisonArtifactPlan:
    """Timestamp-scoped comparison artifact plan."""

    output_dir: Path
    timestamp: str
    timestamp_dir: Path
    codes: dict[str, CodeComparisonArtifacts]
    include_p1: bool = False


def default_comparison_timestamp() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def normalize_stock_code(stock_code: str) -> str:
    digits = "".join(ch for ch in str(stock_code) if ch.isdigit())
    if len(digits) >= 6:
        return digits[-6:]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", str(stock_code)):
        raise ComparisonArtifactError("stock code contains unsupported path characters")
    return str(stock_code)


def plan_comparison_artifacts(
    codes: Iterable[str],
    *,
    output_dir: str | Path = "output/provider_comparison",
    timestamp: str | None = None,
    include_p1: bool = False,
) -> ComparisonArtifactPlan:
    """Return provider-separated artifact paths without touching the filesystem."""

    out = Path(output_dir)
    ts = timestamp or default_comparison_timestamp()
    timestamp_dir = out / ts
    names = BASE_ARTIFACT_NAMES + (P1_ARTIFACT_NAMES if include_p1 else ())
    code_plans: dict[str, CodeComparisonArtifacts] = {}
    for code_value in codes:
        code = normalize_stock_code(code_value)
        code_dir = timestamp_dir / code
        paths = {name: code_dir / name for name in names}
        for path in paths.values():
            ensure_comparison_artifact_path(path, timestamp_dir=timestamp_dir)
        code_plans[code] = CodeComparisonArtifacts(code=code, code_dir=code_dir, paths=paths)
    return ComparisonArtifactPlan(
        output_dir=out,
        timestamp=ts,
        timestamp_dir=timestamp_dir,
        codes=code_plans,
        include_p1=include_p1,
    )


def ensure_comparison_artifact_path(path: Path, *, timestamp_dir: Path) -> None:
    """Fail if a path would escape the timestamp comparison directory."""

    resolved_path = path.resolve(strict=False)
    resolved_root = timestamp_dir.resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ComparisonArtifactError("comparison artifact path escapes timestamp directory") from exc

    if _is_forbidden_production_output(path):
        raise ComparisonArtifactError("comparison artifact path points at forbidden production output")


def write_json_artifact(
    plan: ComparisonArtifactPlan,
    code: str,
    artifact_name: str,
    payload: Any,
) -> Path:
    """Write one planned JSON artifact inside the isolated comparison directory."""

    path = _planned_path(plan, code, artifact_name)
    if path.suffix.lower() != ".json":
        raise ComparisonArtifactError("write_json_artifact requires a .json artifact")
    ensure_comparison_artifact_path(path, timestamp_dir=plan.timestamp_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def write_text_artifact(
    plan: ComparisonArtifactPlan,
    code: str,
    artifact_name: str,
    text: str,
) -> Path:
    """Write one planned text artifact inside the isolated comparison directory."""

    path = _planned_path(plan, code, artifact_name)
    ensure_comparison_artifact_path(path, timestamp_dir=plan.timestamp_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _planned_path(plan: ComparisonArtifactPlan, code: str, artifact_name: str) -> Path:
    normalized = normalize_stock_code(code)
    try:
        code_plan = plan.codes[normalized]
    except KeyError as exc:
        raise ComparisonArtifactError(f"code {normalized!r} is not in artifact plan") from exc
    try:
        return code_plan.paths[artifact_name]
    except KeyError as exc:
        raise ComparisonArtifactError(f"artifact {artifact_name!r} is not in artifact plan") from exc


def _is_forbidden_production_output(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    name = path.name.lower()
    if "output" in parts and "reports" in parts:
        return True
    return bool(re.fullmatch(r"(raw|fundamental|evidence_pack)_\d{6}\.json", name))
