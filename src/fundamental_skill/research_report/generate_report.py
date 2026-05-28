# -*- coding: utf-8 -*-
"""CLI wrapper for accepted offline single-stock report orchestration."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any, TextIO

from .orchestration import (
    ReportArtifactError,
    ReportRequestError,
    format_orchestration_response,
    normalize_report_request,
    run_single_stock_report_orchestration,
)


SUCCESS_EXIT_CODE = 0
INVALID_REQUEST_EXIT_CODE = 2
MISSING_LOCAL_ARTIFACTS_EXIT_CODE = 3
SAFETY_BOUNDARY_EXIT_CODE = 4
UNSUPPORTED_ARGUMENT_EXIT_CODE = 5

_SUPPORTED_FORMATS = {"json", "markdown", "html", "all"}
_SUPPORTED_DATA_MODES = {"offline_local_artifacts", "local_provider_comparison"}
_SAFETY_ARG_FRAGMENTS = ("live", "provider", "network", "token", "mcp")
_OFFLINE_ORCHESTRATION_DATA_MODE = "offline_local_artifacts"
_IMPORTANT_STATEMENT = "本报告仅用于基本面研究，不构成买卖建议，不包含目标价、仓位或技术面交易信号。"


class _CliArgumentError(ValueError):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # pragma: no cover - exercised through main
        raise _CliArgumentError(message)


def main(argv: list[str] | None = None, *, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    """Run the offline report command wrapper."""

    out = stdout or sys.stdout
    err = stderr or sys.stderr

    try:
        args, unknown_args = _parse_args(argv)
    except _CliArgumentError as exc:
        print(_format_cli_error("失败_invalid_request", f"参数解析失败：{exc}"), file=out)
        return INVALID_REQUEST_EXIT_CODE

    if unknown_args:
        status = "失败_safety_boundary" if _asks_for_safety_boundary(unknown_args) else "失败_unsupported_argument"
        code = SAFETY_BOUNDARY_EXIT_CODE if status == "失败_safety_boundary" else UNSUPPORTED_ARGUMENT_EXIT_CODE
        print(_format_cli_error(status, f"不支持的参数组合：{' '.join(unknown_args)}"), file=out)
        return code

    validation_error = _validate_args(args)
    if validation_error:
        status, message, exit_code = validation_error
        print(_format_cli_error(status, message), file=out)
        return exit_code

    try:
        request = normalize_report_request(
            code=args.code,
            company_name=args.company_name,
            output_format=args.output_format,
            data_mode=_OFFLINE_ORCHESTRATION_DATA_MODE,
        )
        result = run_single_stock_report_orchestration(
            request,
            output_root=Path(args.output_root),
            provider_comparison_root=_provider_comparison_root(args),
            timestamp=args.timestamp,
        )
        response = format_orchestration_response(result)
    except ReportRequestError as exc:
        print(_format_cli_error("失败_invalid_request", str(exc)), file=out)
        return INVALID_REQUEST_EXIT_CODE
    except ReportArtifactError as exc:
        print(_format_cli_error("失败_safety_boundary", str(exc)), file=out)
        return SAFETY_BOUNDARY_EXIT_CODE
    except ValueError as exc:
        print(_format_cli_error("失败_invalid_request", str(exc)), file=out)
        return INVALID_REQUEST_EXIT_CODE
    except RuntimeError as exc:
        print(_format_cli_error("失败_safety_boundary", str(exc)), file=out)
        return SAFETY_BOUNDARY_EXIT_CODE

    if _missing_local_artifacts(result):
        print(f"status: 未生成_missing_local_artifacts\n{response}", file=out)
        return MISSING_LOCAL_ARTIFACTS_EXIT_CODE
    if _invalid_manifest(result):
        print(f"status: failed_invalid_manifest\n{response}", file=out)
        return SAFETY_BOUNDARY_EXIT_CODE

    print(response, file=out)
    err.flush()
    return SUCCESS_EXIT_CODE


def _parse_args(argv: list[str] | None) -> tuple[argparse.Namespace, list[str]]:
    parser = _ArgumentParser(
        prog="python -m src.fundamental_skill.research_report.generate_report",
        add_help=True,
        allow_abbrev=False,
    )
    parser.add_argument("--code")
    parser.add_argument("--company-name")
    parser.add_argument("--format", dest="output_format", default="html")
    parser.add_argument("--data-mode", default="offline_local_artifacts")
    parser.add_argument("--provider-comparison-root")
    parser.add_argument("--output-root", default="output/research_reports")
    parser.add_argument("--timestamp")
    parser.add_argument("--no-network", action="store_true", default=True)
    parser.add_argument("--no-token-read", action="store_true", default=True)
    parser.add_argument("--not-for-trading-advice", action="store_true", default=True)
    parser.add_argument("--strict-evidence-boundary", action="store_true", default=True)
    return parser.parse_known_args(argv)


def _validate_args(args: argparse.Namespace) -> tuple[str, str, int] | None:
    if not args.code and not args.company_name:
        return (
            "失败_invalid_request",
            "缺少目标标的：请提供 --code 或 --company-name。",
            INVALID_REQUEST_EXIT_CODE,
        )

    output_format = str(args.output_format or "").lower()
    if output_format not in _SUPPORTED_FORMATS:
        return (
            "失败_unsupported_argument",
            "--format 仅支持 json、markdown、html 或 all。",
            UNSUPPORTED_ARGUMENT_EXIT_CODE,
        )
    args.output_format = output_format

    data_mode = str(args.data_mode or "")
    if data_mode not in _SUPPORTED_DATA_MODES:
        if _asks_for_safety_boundary([data_mode]):
            return (
                "失败_safety_boundary",
                "当前 CLI 仅支持本地 artifact 模式，不支持实时数据、令牌、网络或外部连接。",
                SAFETY_BOUNDARY_EXIT_CODE,
            )
        return (
            "失败_unsupported_argument",
            "--data-mode 仅支持 offline_local_artifacts 或 local_provider_comparison。",
            UNSUPPORTED_ARGUMENT_EXIT_CODE,
        )
    args.data_mode = data_mode

    if args.provider_comparison_root and data_mode != "local_provider_comparison":
        return (
            "失败_unsupported_argument",
            "--provider-comparison-root 仅可与 --data-mode local_provider_comparison 一起使用。",
            UNSUPPORTED_ARGUMENT_EXIT_CODE,
        )

    if not (args.no_network and args.no_token_read and args.not_for_trading_advice and args.strict_evidence_boundary):
        return (
            "失败_safety_boundary",
            "安全边界必须保持 no-network、no-token-read、not-for-trading-advice 和 strict-evidence-boundary。",
            SAFETY_BOUNDARY_EXIT_CODE,
        )

    return None


def _provider_comparison_root(args: argparse.Namespace) -> Path | None:
    if args.data_mode != "local_provider_comparison" or not args.provider_comparison_root:
        return None
    return Path(args.provider_comparison_root)


def _asks_for_safety_boundary(values: list[str]) -> bool:
    normalized = " ".join(str(value).lower() for value in values)
    return any(fragment in normalized for fragment in _SAFETY_ARG_FRAGMENTS)


def _missing_local_artifacts(result: dict[str, Any]) -> bool:
    return str(result.get("status") or "") in {
        "failed_missing_artifacts",
        "未生成_missing_local_artifacts",
    }


def _invalid_manifest(result: dict[str, Any]) -> bool:
    return str(result.get("status") or "") == "failed_invalid_manifest"


def _format_cli_error(status: str, message: str, missing_artifacts: list[str] | None = None) -> str:
    lines = [
        f"status: {status}",
        "HTML path: 未生成",
        "Markdown path: 未生成",
        "JSON path: 未生成",
        "",
        f"中文摘要: {message}",
        "最大机会: 未生成",
        "最大风险: 未生成",
        "最大证据缺口: 未生成",
        "数据质量状态: 未生成",
    ]
    if missing_artifacts:
        lines.extend(["", "缺少的本地 artifacts：", *[f"- {item}" for item in missing_artifacts]])
    lines.extend(["", f"重要声明: {_IMPORTANT_STATEMENT}"])
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
