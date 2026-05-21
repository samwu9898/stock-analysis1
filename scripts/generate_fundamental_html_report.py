# -*- coding: utf-8 -*-
"""Workflow wrapper for formal Fundamental HTML report generation.

The wrapper prepares all local evidence and prompts, but deliberately never
calls an OpenAI API and never fabricates a skeleton report as a formal report.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.fundamental_skill.ai_analyst import html_report_runner
from src.fundamental_skill.ai_analyst import runner as ai_analyst_runner
from src.fundamental_skill.ai_analyst.html_report_runner import normalize_stock_code
from src.fundamental_skill.real_stock_runner import run_real_stock


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_REPORT_DIRNAME = "reports"
DEFAULT_VISUAL_AUDIT_DIRNAME = "visual_audit"


def _output_dir(output_dir: str | Path | None = None) -> Path:
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    if not directory.is_absolute():
        directory = PROJECT_ROOT / directory
    return directory


def formal_report_json_path(code: str, output_dir: str | Path | None = None) -> Path:
    normalized = normalize_stock_code(code)
    return _output_dir(output_dir) / DEFAULT_REPORT_DIRNAME / f"fundamental_report_{normalized}.json"


def formal_report_html_path(code: str, output_dir: str | Path | None = None) -> Path:
    normalized = normalize_stock_code(code)
    return _output_dir(output_dir) / DEFAULT_REPORT_DIRNAME / f"fundamental_report_{normalized}.html"


def next_task_path(code: str, output_dir: str | Path | None = None) -> Path:
    normalized = normalize_stock_code(code)
    return _output_dir(output_dir) / DEFAULT_REPORT_DIRNAME / f"fundamental_report_next_task_{normalized}.md"


def visual_audit_output_dir(code: str, output_dir: str | Path | None = None) -> Path:
    normalized = normalize_stock_code(code)
    return _output_dir(output_dir) / DEFAULT_VISUAL_AUDIT_DIRNAME / normalized


def build_next_task_instructions(
    *,
    code: str,
    ai_prompt_path: str | Path,
    html_prompt_path: str | Path,
    formal_json_path: str | Path,
    formal_html_path: str | Path,
    output_dir: str | Path | None = None,
) -> str:
    """Return the short task users can give Codex/GPT after preparation."""

    normalized = normalize_stock_code(code)
    render_command = (
        "python scripts/generate_fundamental_html_report.py "
        f"--code {normalized} --mode render_existing --visual-audit"
    )
    if output_dir:
        render_command += f" --output-dir {Path(output_dir)}"

    return "\n".join(
        [
            f"# Formal Fundamental HTML Report JSON Task - {normalized}",
            "",
            "请基于已生成的 HTML report prompt 生成正式 FundamentalHtmlReport JSON。",
            "",
            f"- AI analyst prompt: `{Path(ai_prompt_path)}`",
            f"- HTML report prompt: `{Path(html_prompt_path)}`",
            f"- JSON 保存路径: `{Path(formal_json_path)}`",
            f"- HTML 输出路径: `{Path(formal_html_path)}`",
            "",
            "硬性要求：",
            "",
            "- 只输出并保存一个符合 `fundamental_html_report.v1` schema 的 JSON 对象。",
            "- 不自动调用 OpenAI API；由 Codex/GPT 在当前会话中基于 prompt 完成正式 JSON。",
            "- 不要 Markdown 包裹，不要解释性前后缀，不要 skeleton。",
            "- 只基于 prompt/evidence pack 中的事实、source trace、derived observation 和 missing evidence。",
            "- 缺数据必须写“无法判断”或“不足以判断”，不得编造订单、客户、份额、排名、产能释放或 peer percentile。",
            "- 不得输出交易建议、目标价、仓位、技术面、K线、买卖时机、止损止盈或价格执行依据。",
            "- `valuation_explanation` 只能解释估值可理解性和限制，不能写目标价。",
            "- `fundamental_scenario_analysis` 只能写基本面情景，不能写股价或交易动作。",
            "",
            "生成并保存正式 JSON 后运行：",
            "",
            f"```bash\n{render_command}\n```",
            "",
            "渲染后必须检查 visual audit 产物，并人工确认桌面首屏、移动首屏、全页截图没有遮挡、空白、错位、横向溢出或安全边界越界。",
        ]
    )


def run_prepare(
    code: str,
    *,
    output_dir: str | Path | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    normalized = normalize_stock_code(code)
    directory = _output_dir(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    fundamental_path = directory / f"fundamental_{normalized}.json"
    raw_path = directory / f"raw_{normalized}.json"

    _raw_json, fundamental_result = run_real_stock(
        normalized,
        output=str(fundamental_path),
        force_refresh=force_refresh,
    )
    ai_result = ai_analyst_runner.run_prompt_only(normalized, output_dir=directory)
    html_prompt_result = html_report_runner.run_prompt_only(normalized, output_dir=directory)

    formal_json = formal_report_json_path(normalized, directory)
    formal_html = formal_report_html_path(normalized, directory)
    task_path = next_task_path(normalized, directory)
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_text = build_next_task_instructions(
        code=normalized,
        ai_prompt_path=ai_result["prompt_path"],
        html_prompt_path=html_prompt_result["prompt_path"],
        formal_json_path=formal_json,
        formal_html_path=formal_html,
        output_dir=output_dir,
    )
    task_path.write_text(task_text, encoding="utf-8")

    return {
        "stock_code": normalized,
        "stock_name": getattr(fundamental_result, "stock_name", None),
        "fundamental_path": str(fundamental_path),
        "raw_path": str(raw_path),
        "evidence_pack_path": str(ai_result["evidence_pack_path"]),
        "ai_prompt_path": str(ai_result["prompt_path"]),
        "html_prompt_path": str(html_prompt_result["prompt_path"]),
        "formal_json_path": str(formal_json),
        "formal_html_path": str(formal_html),
        "next_task_path": str(task_path),
        "next_task": task_text,
    }


def run_render_existing(
    code: str,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    normalized = normalize_stock_code(code)
    directory = _output_dir(output_dir)
    return html_report_runner.run_render_existing(normalized, output_dir=directory)


def run_visual_audit(
    code: str,
    *,
    output_dir: str | Path | None = None,
) -> int:
    normalized = normalize_stock_code(code)
    html_path = formal_report_html_path(normalized, output_dir)
    audit_dir = visual_audit_output_dir(normalized, output_dir)

    from scripts.visual_audit_html_report import main as visual_audit_main

    return visual_audit_main(
        [
            "--html",
            str(html_path),
            "--code",
            normalized,
            "--output-dir",
            str(audit_dir),
            "--notes",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, render, and visually audit formal Fundamental HTML reports."
    )
    parser.add_argument("--code", required=True, help="6 digit A-share stock code")
    parser.add_argument(
        "--mode",
        default="prepare",
        choices=["prepare", "render_existing", "visual_audit"],
        help="prepare builds prompts; render_existing renders saved formal JSON; visual_audit audits saved formal HTML.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Workflow output directory. Defaults to project output/.",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="In prepare mode, ignore connector cache and fetch fresh public data.",
    )
    parser.add_argument(
        "--visual-audit",
        action="store_true",
        help="After render_existing, capture desktop/mobile/full-page screenshots.",
    )
    return parser


def _print_prepare_result(result: dict[str, Any]) -> None:
    print(f"stock_code: {result['stock_code']}")
    if result.get("stock_name"):
        print(f"stock_name: {result['stock_name']}")
    print(f"fundamental_json: {result['fundamental_path']}")
    print(f"raw_json: {result['raw_path']}")
    print(f"evidence_pack: {result['evidence_pack_path']}")
    print(f"ai_prompt: {result['ai_prompt_path']}")
    print(f"html_report_prompt: {result['html_prompt_path']}")
    print(f"formal_json_expected: {result['formal_json_path']}")
    print(f"formal_html_expected: {result['formal_html_path']}")
    print(f"next_task: {result['next_task_path']}")
    print("")
    print(result["next_task"])


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.mode == "prepare":
            result = run_prepare(args.code, output_dir=args.output_dir, force_refresh=args.force_refresh)
            _print_prepare_result(result)
            if args.visual_audit:
                print("visual_audit skipped: prepare mode has no formal HTML yet; render first with --mode render_existing")
            return 0

        if args.mode == "render_existing":
            result = run_render_existing(args.code, output_dir=args.output_dir)
            print(f"stock_code: {result['stock_code']}")
            print(f"html_report: {result['html_path']}")
            if args.visual_audit:
                return run_visual_audit(args.code, output_dir=args.output_dir)
            return 0

        return run_visual_audit(args.code, output_dir=args.output_dir)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
