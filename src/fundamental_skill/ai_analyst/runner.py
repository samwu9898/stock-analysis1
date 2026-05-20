# -*- coding: utf-8 -*-
"""CLI runner for the prompt-only Fundamental AI Analyst Layer v1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .evidence_pack import EvidencePackBuilder
from .prompt_builder import PromptBuilder


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"


def normalize_stock_code(code: Any) -> str:
    digits = "".join(ch for ch in str(code or "") if ch.isdigit())
    if len(digits) < 6:
        raise ValueError("stock code must contain 6 digits")
    return digits[-6:]


def run_prompt_only(code: str, output_dir: str | Path | None = None) -> dict[str, Any]:
    normalized = normalize_stock_code(code)
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    fundamental_path = directory / f"fundamental_{normalized}.json"
    raw_path = directory / f"raw_{normalized}.json"
    evidence_path = directory / f"evidence_pack_{normalized}.json"
    prompt_path = directory / f"ai_prompt_{normalized}.md"

    if not fundamental_path.exists() or not raw_path.exists():
        missing = [str(path) for path in (fundamental_path, raw_path) if not path.exists()]
        raise FileNotFoundError(
            "Required fundamental/raw JSON files are missing. "
            "Run src.fundamental_skill.real_stock_runner first. Missing: "
            + ", ".join(missing)
        )

    builder = EvidencePackBuilder()
    evidence_pack = builder.build_from_files(fundamental_path, raw_path)
    prompt = PromptBuilder().build(evidence_pack)

    directory.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence_pack, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    prompt_path.write_text(prompt, encoding="utf-8")
    return {
        "stock_code": normalized,
        "evidence_pack_path": str(evidence_path),
        "prompt_path": str(prompt_path),
        "evidence_pack": evidence_pack,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Fundamental AI Analyst evidence pack and prompt.")
    parser.add_argument("--code", required=True, help="6 digit A-share stock code")
    parser.add_argument("--mode", default="prompt_only", choices=["prompt_only", "api"], help="v1 supports prompt_only")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory containing raw/fundamental JSON")
    args = parser.parse_args()

    if args.mode == "api":
        print("API mode not implemented in v1; use prompt_only")
        return 0

    try:
        result = run_prompt_only(args.code, output_dir=args.output_dir)
    except Exception as exc:
        print(str(exc))
        return 1

    print(f"stock_code: {result['stock_code']}")
    print(f"evidence_pack: {result['evidence_pack_path']}")
    print(f"ai_prompt: {result['prompt_path']}")
    print("mode: prompt_only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
