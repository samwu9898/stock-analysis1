# -*- coding: utf-8 -*-
"""Dry-run provider comparison runner for Phase 4.

The CLI is plan-only by default. Real-provider execution is available only to
callers that inject provider instances directly; this module does not read
environment variables, local MCP config, or credentials.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..ai_analyst.evidence_pack import EvidencePackBuilder
from ..pipeline import FundamentalSkillPipeline
from .akshare_provider import AkShareProvider
from .base import DataProvider
from .comparison_artifacts import (
    ComparisonArtifactPlan,
    plan_comparison_artifacts,
    write_json_artifact,
    write_text_artifact,
)
from .diff_classifier import build_diff_report, render_diff_report_markdown
from .real_token_smoke_gate import (
    RealTokenSmokeGate,
    RealTokenSmokeGateError,
    validate_real_token_smoke_flags,
)
from .schemas import raw_has_canonical_shape
from .token_leak_scanner import assert_no_token_leaks
from .token_safety import sanitize_text
from .tushare_client import TushareClient
from .tushare_provider import TushareProvider
from .tushare_sdk_transport import TushareSdkTransport, TushareSdkTransportError


DEFAULT_PROVIDERS: tuple[str, str] = ("akshare", "tushare")


class ProviderComparisonError(RuntimeError):
    """Safe comparison runner failure."""


@dataclass(frozen=True)
class ProviderOutputBundle:
    provider_name: str
    raw: dict[str, Any]
    fundamental: dict[str, Any]
    evidence_pack: dict[str, Any]


def build_provider_output_bundle(
    provider: DataProvider,
    code: str,
    *,
    run_pipeline: bool = True,
    force_refresh: bool = False,
) -> ProviderOutputBundle:
    """Build raw / fundamental / evidence artifacts in memory for one provider."""

    raw = provider.fetch_to_raw_json(code, force_refresh=force_refresh)
    if not raw_has_canonical_shape(raw):
        raise ProviderComparisonError(f"provider {provider.name!r} returned non-canonical raw shape")
    assert_no_token_leaks(raw, context=f"{provider.name} raw")

    if run_pipeline:
        result = FundamentalSkillPipeline().analyze_from_dict(raw)
        fundamental = result.model_dump()
        evidence_pack = EvidencePackBuilder().build(fundamental, raw)
    else:
        fundamental = {
            "stock_code": raw.get("meta", {}).get("code") or code,
            "stock_name": raw.get("meta", {}).get("stock_name"),
            "strategy_type": None,
            "sub_type": None,
            "status": "not_run",
            "confidence": "not_run",
            "fundamental_score": None,
            "missing_fields": _raw_missing_fields(raw),
        }
        evidence_pack = {
            "stock": {
                "code": fundamental["stock_code"],
                "name": fundamental["stock_name"],
                "strategy_type": None,
                "sub_type": None,
                "status": "not_run",
                "confidence": "not_run",
                "fundamental_score": None,
            },
            "basic_info": _first_row(raw, "basic_info"),
            "financial_metrics": _first_row(raw, "financial_indicator"),
            "valuation_metrics": _first_row(raw, "valuation"),
            "business_composition": raw.get("blocks", {}).get("business_composition", []),
            "missing_fields": [{"field": field} for field in _raw_missing_fields(raw)],
            "source_trace_summary": [],
        }

    assert_no_token_leaks(fundamental, context=f"{provider.name} fundamental")
    assert_no_token_leaks(evidence_pack, context=f"{provider.name} evidence_pack")
    return ProviderOutputBundle(
        provider_name=provider.name,
        raw=raw,
        fundamental=fundamental,
        evidence_pack=evidence_pack,
    )


def run_provider_comparison(
    *,
    codes: Sequence[str],
    providers: Sequence[str] = DEFAULT_PROVIDERS,
    output_dir: str | Path = "output/provider_comparison",
    dry_run: bool = True,
    include_p1: bool = False,
    real_token_smoke: bool = False,
    provider_transport: str | None = None,
    provider_instances: Mapping[str, DataProvider] | None = None,
    timestamp: str | None = None,
    write_artifacts: bool = True,
    run_pipeline: bool = True,
    output_dir_explicit: bool = True,
    token_reader: Callable[[], str | None] | None = None,
    sdk_factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Run a Phase 4 comparison with injected providers or return a plan-only dry-run."""

    provider_names = tuple(str(provider).strip().lower() for provider in providers)
    if provider_names != DEFAULT_PROVIDERS:
        raise ProviderComparisonError("Phase 4 minimal supports only akshare,tushare comparison order")
    try:
        validate_real_token_smoke_flags(
            real_token_smoke=real_token_smoke,
            provider_transport=provider_transport,
            output_dir=output_dir,
            output_dir_explicit=output_dir_explicit,
            codes=codes,
            repo_root=_repo_root(),
        )
    except RealTokenSmokeGateError as exc:
        raise ProviderComparisonError(str(exc)) from None

    if real_token_smoke:
        return _run_real_token_smoke_comparison(
            codes=codes,
            providers=provider_names,
            output_dir=output_dir,
            provider_transport=provider_transport,
            provider_instances=provider_instances,
            timestamp=timestamp,
            write_artifacts=write_artifacts,
            run_pipeline=run_pipeline,
            output_dir_explicit=output_dir_explicit,
            token_reader=token_reader,
            sdk_factory=sdk_factory,
        )

    plan = plan_comparison_artifacts(
        codes,
        output_dir=output_dir,
        timestamp=timestamp,
        include_p1=include_p1,
    )
    response: dict[str, Any] = {
        "mode": "dry_run" if dry_run else "comparison",
        "dry_run": dry_run,
        "include_p1": include_p1,
        "include_p1_execution": "planned_only" if include_p1 else "off",
        "real_token_smoke": False,
        "artifact_root": str(plan.timestamp_dir),
        "codes": {},
        "wrote_artifacts": False,
        "provider_execution": "not_run",
    }
    for code, code_plan in plan.codes.items():
        response["codes"][code] = {
            "code_dir": str(code_plan.code_dir),
            "artifacts": {name: str(path) for name, path in code_plan.paths.items()},
        }

    if not provider_instances:
        return response

    missing = [name for name in DEFAULT_PROVIDERS if name not in provider_instances]
    if missing:
        raise ProviderComparisonError(f"missing injected provider(s): {', '.join(missing)}")

    response["provider_execution"] = "injected"
    response["wrote_artifacts"] = bool(write_artifacts)
    for code in plan.codes:
        akshare_bundle = build_provider_output_bundle(provider_instances["akshare"], code, run_pipeline=run_pipeline)
        tushare_bundle = build_provider_output_bundle(provider_instances["tushare"], code, run_pipeline=run_pipeline)
        report = build_diff_report(
            code=code,
            akshare_raw=akshare_bundle.raw,
            tushare_raw=tushare_bundle.raw,
            akshare_fundamental=akshare_bundle.fundamental,
            tushare_fundamental=tushare_bundle.fundamental,
            akshare_evidence_pack=akshare_bundle.evidence_pack,
            tushare_evidence_pack=tushare_bundle.evidence_pack,
        )
        markdown = render_diff_report_markdown(report)
        assert_no_token_leaks(report, context=f"{code} diff_report")
        assert_no_token_leaks(markdown, context=f"{code} diff_report.md")

        if write_artifacts:
            _write_provider_artifacts(plan, code, akshare_bundle, tushare_bundle, report, markdown)
        response["codes"][code]["summary"] = report["summary"]

    return response


def main(argv: Sequence[str] | None = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    if _contains_token_cli_arg(raw_argv):
        print("provider_comparison_error: --token CLI parameter is not allowed")
        return 2

    parser = argparse.ArgumentParser(description="Plan isolated AkShare/Tushare comparison artifacts.")
    parser.add_argument("--codes", required=True, help="Comma-separated 6 digit A-share stock codes")
    parser.add_argument("--providers", default="akshare,tushare", help="Provider order; Phase 4 minimal supports akshare,tushare")
    parser.add_argument("--output-dir", default="output/provider_comparison", help="Isolated comparison output directory")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Plan-only by default")
    parser.add_argument("--include-p1", action="store_true", help="Plan P1.1 artifact paths only; no P1.1 execution in Phase 4 minimal")
    parser.add_argument("--real-token-smoke", action="store_true", help="Enable local-only real-token smoke gate")
    parser.add_argument("--provider-transport", help="Real-token smoke transport; only sdk is executable")
    try:
        args, unknown = parser.parse_known_args(argv)
    except SystemExit:
        print("provider_comparison_error: invalid provider comparison arguments")
        return 2
    if unknown:
        print("provider_comparison_error: invalid or unsupported CLI argument")
        return 2

    try:
        result = run_provider_comparison(
            codes=_split_csv(args.codes),
            providers=_split_csv(args.providers),
            output_dir=args.output_dir,
            dry_run=True,
            include_p1=args.include_p1,
            real_token_smoke=args.real_token_smoke,
            provider_transport=args.provider_transport,
            provider_instances=None,
            output_dir_explicit=_output_dir_was_explicit(raw_argv),
        )
    except ProviderComparisonError as exc:
        print(f"provider_comparison_error: {exc}")
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _write_provider_artifacts(
    plan: ComparisonArtifactPlan,
    code: str,
    akshare_bundle: ProviderOutputBundle,
    tushare_bundle: ProviderOutputBundle,
    report: Mapping[str, Any],
    markdown: str,
    *,
    gate: RealTokenSmokeGate | None = None,
) -> None:
    if gate is not None:
        gate.write_json_artifact(code=code, artifact_name="akshare_raw.json", payload=akshare_bundle.raw)
        gate.write_json_artifact(code=code, artifact_name="tushare_raw.json", payload=tushare_bundle.raw)
        gate.write_json_artifact(code=code, artifact_name="akshare_fundamental.json", payload=akshare_bundle.fundamental)
        gate.write_json_artifact(code=code, artifact_name="tushare_fundamental.json", payload=tushare_bundle.fundamental)
        gate.write_json_artifact(code=code, artifact_name="akshare_evidence_pack.json", payload=akshare_bundle.evidence_pack)
        gate.write_json_artifact(code=code, artifact_name="tushare_evidence_pack.json", payload=tushare_bundle.evidence_pack)
        gate.write_diff_report(code=code, report=report, markdown=markdown)
        return
    write_json_artifact(plan, code, "akshare_raw.json", akshare_bundle.raw)
    write_json_artifact(plan, code, "tushare_raw.json", tushare_bundle.raw)
    write_json_artifact(plan, code, "akshare_fundamental.json", akshare_bundle.fundamental)
    write_json_artifact(plan, code, "tushare_fundamental.json", tushare_bundle.fundamental)
    write_json_artifact(plan, code, "akshare_evidence_pack.json", akshare_bundle.evidence_pack)
    write_json_artifact(plan, code, "tushare_evidence_pack.json", tushare_bundle.evidence_pack)
    write_json_artifact(plan, code, "diff_report.json", report)
    write_text_artifact(plan, code, "diff_report.md", markdown)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _run_real_token_smoke_comparison(
    *,
    codes: Sequence[str],
    providers: Sequence[str],
    output_dir: str | Path,
    provider_transport: str | None,
    provider_instances: Mapping[str, DataProvider] | None,
    timestamp: str | None,
    write_artifacts: bool,
    run_pipeline: bool,
    output_dir_explicit: bool,
    token_reader: Callable[[], str | None] | None,
    sdk_factory: Callable[[], Any] | None,
) -> dict[str, Any]:
    del providers
    gate = RealTokenSmokeGate(
        repo_root=_repo_root(),
        output_dir=output_dir,
        timestamp=timestamp,
        codes=codes,
    )
    token: str | None = None
    precheck = None
    try:
        token = (token_reader or _read_tushare_token_from_env)()
        if not token:
            raise ProviderComparisonError("real-token smoke requires a local TUSHARE_TOKEN; no provider call was made")
        gate.secret_refs = (token,)
        precheck = gate.precheck(
            real_token_smoke=True,
            provider_transport=provider_transport,
            output_dir_explicit=output_dir_explicit,
        )
        active_providers = provider_instances or _build_real_token_smoke_providers(token=token, sdk_factory=sdk_factory, timestamp=gate.timestamp)
        missing = [name for name in DEFAULT_PROVIDERS if name not in active_providers]
        if missing:
            raise ProviderComparisonError(f"missing injected provider(s): {', '.join(missing)}")

        plan = plan_comparison_artifacts(
            codes,
            output_dir=output_dir,
            timestamp=gate.timestamp,
            include_p1=False,
        )
        response: dict[str, Any] = {
            "mode": "real_token_smoke",
            "dry_run": False,
            "include_p1": False,
            "include_p1_execution": "off",
            "real_token_smoke": True,
            "provider_transport": "sdk",
            "artifact_root": str(plan.timestamp_dir),
            "codes": {},
            "wrote_artifacts": bool(write_artifacts),
            "provider_execution": "local_sdk_smoke",
        }
        for code, code_plan in plan.codes.items():
            response["codes"][code] = {
                "code_dir": str(code_plan.code_dir),
                "artifacts": {name: str(path) for name, path in code_plan.paths.items()},
            }

            akshare_bundle = build_provider_output_bundle(active_providers["akshare"], code, run_pipeline=run_pipeline)
            tushare_bundle = build_provider_output_bundle(active_providers["tushare"], code, run_pipeline=run_pipeline)
            report = build_diff_report(
                code=code,
                akshare_raw=akshare_bundle.raw,
                tushare_raw=tushare_bundle.raw,
                akshare_fundamental=akshare_bundle.fundamental,
                tushare_fundamental=tushare_bundle.fundamental,
                akshare_evidence_pack=akshare_bundle.evidence_pack,
                tushare_evidence_pack=tushare_bundle.evidence_pack,
            )
            markdown = render_diff_report_markdown(report)
            gate.assert_diff_report_safe(report, markdown)
            if write_artifacts:
                _write_provider_artifacts(plan, code, akshare_bundle, tushare_bundle, report, markdown, gate=gate)
            response["codes"][code]["summary"] = report["summary"]

        gate.postcheck(precheck, cleanup_on_blocker=True)
        return response
    except ProviderComparisonError:
        if precheck is not None:
            _cleanup_real_token_timestamp(gate, "provider comparison failed")
        raise
    except (RealTokenSmokeGateError, TushareSdkTransportError) as exc:
        if precheck is not None:
            _cleanup_real_token_timestamp(gate, exc)
        raise ProviderComparisonError(sanitize_text(exc, secrets=(token,))) from None
    except Exception as exc:
        if precheck is not None:
            _cleanup_real_token_timestamp(gate, type(exc).__name__)
        raise ProviderComparisonError(sanitize_text(type(exc).__name__, secrets=(token,))) from None
    finally:
        token = None


def _build_real_token_smoke_providers(
    *,
    token: str,
    sdk_factory: Callable[[], Any] | None,
    timestamp: str,
) -> Mapping[str, DataProvider]:
    transport = TushareSdkTransport(token=token, sdk_factory=sdk_factory, timestamp=timestamp)
    return {
        "akshare": AkShareProvider(),
        "tushare": TushareProvider(client=TushareClient(transport=transport), token_available=True),
    }


def _cleanup_real_token_timestamp(gate: RealTokenSmokeGate, reason: object) -> None:
    if gate.timestamp_dir.exists():
        gate.cleanup_timestamp_dir(gate.timestamp_dir, sanitized_reason=reason)


def _read_tushare_token_from_env() -> str | None:
    return getattr(os, "environ").get("TUSHARE_TOKEN")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _contains_token_cli_arg(argv: Sequence[str] | None) -> bool:
    if argv is None:
        return False
    return any(item == "--token" or str(item).startswith("--token=") for item in argv)


def _output_dir_was_explicit(argv: Sequence[str] | None) -> bool:
    if argv is None:
        return True
    return any(item == "--output-dir" or str(item).startswith("--output-dir=") for item in argv)


def _raw_missing_fields(raw: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    status = raw.get("fetch_status")
    if not isinstance(status, Mapping):
        return missing
    for item in status.values():
        if isinstance(item, Mapping):
            fields = item.get("missing_fields") or []
            if isinstance(fields, list):
                missing.extend(str(field) for field in fields)
    return sorted(set(missing))


def _first_row(raw: Mapping[str, Any], block_name: str) -> dict[str, Any]:
    blocks = raw.get("blocks")
    if not isinstance(blocks, Mapping):
        return {}
    rows = blocks.get(block_name)
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return {}


if __name__ == "__main__":
    raise SystemExit(main())
