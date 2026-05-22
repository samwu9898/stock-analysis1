# -*- coding: utf-8 -*-
"""CLI runner for Research Intelligence P1.1 pilot artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .research_intelligence_p1_builder import ResearchIntelligenceP1Builder
from .runner import DEFAULT_OUTPUT_DIR, normalize_stock_code


def _load_json(path: Path, *, required: bool = True) -> dict[str, Any] | None:
    if not path.exists():
        if required:
            raise FileNotFoundError(
                f"Required evidence pack not found: {path}. "
                "Run the evidence-pack stage first or pass --evidence-pack-path."
            )
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _write_markdown(path: Path, question_set: dict[str, Any]) -> None:
    lines = [
        f"# Research Questions P1.1 - {question_set.get('stock_code')}",
        "",
        f"- stock_name: {question_set.get('stock_name') or ''}",
        f"- generated_at: {question_set.get('generated_at')}",
        f"- strategy_type: {question_set.get('strategy_type')}",
        f"- sub_type: {question_set.get('sub_type')}",
        f"- {question_set.get('p1_summary')}",
        "",
        "## Driver Questions",
        "",
    ]
    for item in question_set.get("questions", []):
        lines.extend(
            [
                f"### {item.get('priority')} {item.get('driver_factor')}",
                "",
                f"- layer: {item.get('layer')}",
                f"- question: {item.get('question')}",
                f"- evidence_trigger: {item.get('evidence_trigger')}",
                f"- next_check: {item.get('next_check')}",
                f"- data_availability_status: {item.get('data_availability_status')}",
                f"- confidence_cap: {item.get('confidence_cap')}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_research_intelligence_p1(
    code: str,
    evidence_pack_path: str | Path | None = None,
    p0_pack_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    normalized = normalize_stock_code(code)
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    input_path = Path(evidence_pack_path) if evidence_pack_path else directory / f"evidence_pack_{normalized}.json"
    p0_path = Path(p0_pack_path) if p0_pack_path else directory / f"research_intelligence_{normalized}.json"

    evidence_pack = _load_json(input_path, required=True)
    assert evidence_pack is not None
    p0_pack = _load_json(p0_path, required=False)

    pack_model, qset_model = ResearchIntelligenceP1Builder().build(
        evidence_pack,
        p0_pack,
        source_evidence_pack_path=str(input_path),
        source_p0_pack_path=str(p0_path) if p0_path.exists() else None,
    )
    pack = pack_model.model_dump()
    qset = qset_model.model_dump()

    directory.mkdir(parents=True, exist_ok=True)
    intelligence_path = directory / f"research_intelligence_p1_{normalized}.json"
    questions_path = directory / f"research_questions_p1_{normalized}.json"
    markdown_path = directory / f"research_questions_p1_{normalized}.md"
    qset["source_driver_matrix_path"] = str(intelligence_path)

    intelligence_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    questions_path.write_text(json.dumps(qset, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _write_markdown(markdown_path, qset)
    return {
        "stock_code": normalized,
        "research_intelligence_p1_path": str(intelligence_path),
        "research_questions_p1_path": str(questions_path),
        "research_questions_p1_markdown_path": str(markdown_path),
        "research_intelligence_p1": pack,
        "research_questions_p1": qset,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Research Intelligence P1.1 pilot artifacts.")
    parser.add_argument("--code", required=True, help="6 digit A-share stock code")
    parser.add_argument("--evidence-pack-path", default=None, help="Path to evidence_pack_<code>.json")
    parser.add_argument("--p0-pack-path", default=None, help="Optional path to research_intelligence_<code>.json")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for outputs")
    args = parser.parse_args()

    try:
        result = run_research_intelligence_p1(
            args.code,
            evidence_pack_path=args.evidence_pack_path,
            p0_pack_path=args.p0_pack_path,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        print(str(exc))
        return 1

    print(f"stock_code: {result['stock_code']}")
    print(f"research_intelligence_p1: {result['research_intelligence_p1_path']}")
    print(f"research_questions_p1: {result['research_questions_p1_path']}")
    print(f"research_questions_p1_md: {result['research_questions_p1_markdown_path']}")
    print("mode: research_intelligence_p1_1_pilot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
