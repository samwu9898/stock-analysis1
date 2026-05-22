# -*- coding: utf-8 -*-
"""CLI runner for Research Intelligence P0 artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .research_intelligence_builder import ResearchIntelligenceBuilder
from .runner import DEFAULT_OUTPUT_DIR, normalize_stock_code


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required evidence pack not found: {path}. "
            "Run: python -m src.fundamental_skill.ai_analyst.runner --code <code> --mode prompt_only"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _write_markdown(path: Path, question_set: dict[str, Any]) -> None:
    lines = [
        f"# Research Questions P0 - {question_set.get('stock_code')}",
        "",
        f"- stock_name: {question_set.get('stock_name') or ''}",
        f"- generated_at: {question_set.get('generated_at')}",
        f"- {question_set.get('p0_summary')}",
        f"- {question_set.get('p1_summary')}",
        f"- {question_set.get('p2_summary')}",
        "",
        "## Questions",
        "",
    ]
    for item in question_set.get("questions", []):
        lines.extend([
            f"### {item.get('priority')} {item.get('question_id')}",
            "",
            f"- question: {item.get('question')}",
            f"- evidence_trigger: {item.get('evidence_trigger')}",
            f"- trigger_rule_id: {item.get('trigger_rule_id')}",
            f"- suggested_recipient: {item.get('suggested_recipient')}",
            f"- evidence_gap: {item.get('evidence_gap')}",
            f"- confidence_cap: {item.get('confidence_cap')}",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def run_research_intelligence(
    code: str,
    evidence_pack_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    normalized = normalize_stock_code(code)
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    input_path = Path(evidence_pack_path) if evidence_pack_path else directory / f"evidence_pack_{normalized}.json"
    evidence_pack = _load_json(input_path)

    pack_model, qset_model = ResearchIntelligenceBuilder().build(evidence_pack)
    pack = pack_model.model_dump()
    qset = qset_model.model_dump()

    directory.mkdir(parents=True, exist_ok=True)
    intelligence_path = directory / f"research_intelligence_{normalized}.json"
    questions_path = directory / f"research_questions_{normalized}.json"
    markdown_path = directory / f"research_questions_{normalized}.md"
    intelligence_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    questions_path.write_text(json.dumps(qset, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _write_markdown(markdown_path, qset)
    return {
        "stock_code": normalized,
        "research_intelligence_path": str(intelligence_path),
        "research_questions_path": str(questions_path),
        "research_questions_markdown_path": str(markdown_path),
        "research_intelligence": pack,
        "research_questions": qset,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Research Intelligence P0 artifacts from an evidence pack.")
    parser.add_argument("--code", required=True, help="6 digit A-share stock code")
    parser.add_argument("--evidence-pack-path", default=None, help="Path to evidence_pack_<code>.json")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for outputs")
    args = parser.parse_args()

    try:
        result = run_research_intelligence(
            args.code,
            evidence_pack_path=args.evidence_pack_path,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        print(str(exc))
        return 1

    print(f"stock_code: {result['stock_code']}")
    print(f"research_intelligence: {result['research_intelligence_path']}")
    print(f"research_questions: {result['research_questions_path']}")
    print(f"research_questions_md: {result['research_questions_markdown_path']}")
    print("mode: research_intelligence_p0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
