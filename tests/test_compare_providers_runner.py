# -*- coding: utf-8 -*-

import json
from pathlib import Path

from src.fundamental_skill.data_providers.compare_providers import (
    ProviderComparisonError,
    build_provider_output_bundle,
    main,
    run_provider_comparison,
)
from src.fundamental_skill.data_providers.fake_provider import FakeDataProvider


def _fake_secret():
    return "Qq1Ww2Ee3Rr4Tt5" + "Yy6Uu7Ii8Oo9Pp0" + "Aa2Ss3Dd4Ff5Gg6"


def test_cli_default_dry_run_plans_only_and_does_not_write(tmp_path, capsys):
    output_dir = tmp_path / "output" / "provider_comparison"

    exit_code = main([
        "--codes",
        "600406,002050",
        "--providers",
        "akshare,tushare",
        "--output-dir",
        str(output_dir),
        "--dry-run",
    ])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["dry_run"] is True
    assert payload["provider_execution"] == "not_run"
    assert "600406" in payload["codes"]
    assert not output_dir.exists()


def test_real_token_flag_without_provider_transport_fails_closed(tmp_path, capsys):
    exit_code = main([
        "--codes",
        "600406",
        "--output-dir",
        "output/provider_comparison",
        "--real-token-smoke",
    ])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--real-token-smoke requires --provider-transport" in captured.out


def test_provider_transport_without_real_token_smoke_fails_closed(capsys):
    exit_code = main([
        "--codes",
        "600406",
        "--output-dir",
        "output/provider_comparison",
        "--provider-transport",
        "sdk",
    ])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--provider-transport requires --real-token-smoke" in captured.out


def test_reserved_provider_transports_fail_closed(capsys):
    for transport in ("http", "mcp-local"):
        exit_code = main([
            "--codes",
            "600406",
            "--output-dir",
            "output/provider_comparison",
            "--real-token-smoke",
            "--provider-transport",
            transport,
        ])
        captured = capsys.readouterr()
        assert exit_code == 2
        assert "reserved for future implementation" in captured.out


def test_token_cli_argument_is_rejected_without_echoing_value(capsys):
    fake_secret = _fake_secret()

    exit_code = main([
        "--codes",
        "600406",
        "--token",
        fake_secret,
    ])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--token CLI parameter is not allowed" in captured.out
    assert fake_secret not in captured.out


def test_real_token_sdk_path_missing_token_fails_before_sdk_call():
    calls = {"sdk": 0}

    def sdk_factory():
        calls["sdk"] += 1
        raise AssertionError("SDK factory must not be called without token")

    try:
        run_provider_comparison(
            codes=["600406"],
            output_dir="output/provider_comparison",
            real_token_smoke=True,
            provider_transport="sdk",
            token_reader=lambda: None,
            sdk_factory=sdk_factory,
        )
    except ProviderComparisonError as exc:
        assert "requires a local TUSHARE_TOKEN" in str(exc)
    else:
        raise AssertionError("expected ProviderComparisonError")

    assert calls["sdk"] == 0


def test_dry_run_does_not_read_real_token_or_require_ci_secret(tmp_path):
    calls = {"token_reader": 0}

    def token_reader():
        calls["token_reader"] += 1
        return _fake_secret()

    result = run_provider_comparison(
        codes=["600406"],
        output_dir=tmp_path / "output" / "provider_comparison",
        token_reader=token_reader,
    )

    assert result["dry_run"] is True
    assert calls["token_reader"] == 0


def test_include_p1_default_off_and_can_plan_only(tmp_path):
    default_result = run_provider_comparison(
        codes=["002050"],
        output_dir=tmp_path / "output" / "provider_comparison",
        timestamp="default",
    )
    p1_result = run_provider_comparison(
        codes=["002050"],
        output_dir=tmp_path / "output" / "provider_comparison",
        timestamp="p1",
        include_p1=True,
    )

    assert default_result["include_p1"] is False
    assert "akshare_research_questions_p1.json" not in default_result["codes"]["002050"]["artifacts"]
    assert p1_result["include_p1"] is True
    assert p1_result["include_p1_execution"] == "planned_only"
    assert "akshare_research_questions_p1.json" in p1_result["codes"]["002050"]["artifacts"]


def test_provider_separated_fake_outputs_write_only_comparison_artifacts(tmp_path):
    output_dir = tmp_path / "output" / "provider_comparison"
    providers = {
        "akshare": FakeDataProvider(name="akshare", stock_name="AkShare Fake"),
        "tushare": FakeDataProvider(name="tushare", stock_name="Tushare Fake"),
    }

    result = run_provider_comparison(
        codes=["600406"],
        output_dir=output_dir,
        timestamp="phase4",
        provider_instances=providers,
        dry_run=True,
        run_pipeline=True,
    )

    code_dir = output_dir / "phase4" / "600406"
    assert result["provider_execution"] == "injected"
    assert result["wrote_artifacts"] is True
    assert (code_dir / "akshare_raw.json").exists()
    assert (code_dir / "tushare_raw.json").exists()
    assert (code_dir / "akshare_fundamental.json").exists()
    assert (code_dir / "tushare_fundamental.json").exists()
    assert (code_dir / "akshare_evidence_pack.json").exists()
    assert (code_dir / "tushare_evidence_pack.json").exists()
    assert (code_dir / "diff_report.json").exists()
    assert (code_dir / "diff_report.md").exists()
    assert not (tmp_path / "output" / "raw_600406.json").exists()
    assert not (tmp_path / "output" / "fundamental_600406.json").exists()
    assert not (tmp_path / "output" / "evidence_pack_600406.json").exists()
    assert not (tmp_path / "output" / "reports").exists()
    assert providers["akshare"].calls == [{"stock_code": "600406", "force_refresh": False}]
    assert providers["tushare"].calls == [{"stock_code": "600406", "force_refresh": False}]


def test_build_provider_output_bundle_can_skip_pipeline_for_raw_level_comparison():
    provider = FakeDataProvider(name="akshare", stock_name="Raw Only")

    bundle = build_provider_output_bundle(provider, "002837", run_pipeline=False)

    assert bundle.provider_name == "akshare"
    assert bundle.raw["meta"]["data_source"] == "akshare"
    assert bundle.fundamental["status"] == "not_run"
    assert bundle.evidence_pack["stock"]["status"] == "not_run"


def test_run_provider_comparison_requires_injected_both_providers(tmp_path):
    try:
        run_provider_comparison(
            codes=["600406"],
            output_dir=tmp_path / "output" / "provider_comparison",
            provider_instances={"akshare": FakeDataProvider(name="akshare")},
        )
    except ProviderComparisonError as exc:
        assert "missing injected provider" in str(exc)
    else:
        raise AssertionError("expected ProviderComparisonError")


def test_static_safety_terms_absent_from_new_runner_source():
    source = Path("src/fundamental_skill/data_providers/compare_providers.py").read_text(encoding="utf-8").lower()

    forbidden = [
        "api." + "tushare." + "pro",
        "requ" + "ests",
        "htt" + "px",
        "url" + "lib",
        "." + "env",
        "provider=auto primary",
    ]
    for term in forbidden:
        assert term not in source
