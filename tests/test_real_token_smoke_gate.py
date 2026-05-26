# -*- coding: utf-8 -*-

import os
import subprocess

import pytest

from src.fundamental_skill.data_providers.real_token_smoke_gate import (
    RealTokenSmokeGate,
    RealTokenSmokeGateError,
    assert_snapshot_unchanged,
    snapshot_default_outputs,
    snapshot_reports,
)


TIMESTAMP = "20260526T120000"


def _fake_secret():
    return "Mm1Nn2Bb3Vv4Cc5" + "Xx6Zz7Aa8Ss9Dd0" + "Ff1Gg2Hh3Jj4Kk5"


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docs").mkdir()
    (repo / "tests").mkdir()
    (repo / "src").mkdir()
    (repo / "docs" / "safe.md").write_text("safe provider smoke notes\n", encoding="utf-8")
    _git(repo, "init")
    _git(repo, "add", "docs/safe.md")
    return repo


def _gate(repo, *, secret=None):
    return RealTokenSmokeGate(
        repo_root=repo,
        output_dir="output/provider_comparison",
        timestamp=TIMESTAMP,
        codes=["600406"],
        secret_refs=(secret,) if secret else (),
    )


def test_precheck_fails_on_token_in_tracked_file(tmp_path):
    repo = _init_repo(tmp_path)
    secret = _fake_secret()
    leak = repo / "src" / "leak.py"
    leak.write_text("ERROR = 'token=" + secret + "'\n", encoding="utf-8")
    _git(repo, "add", "src/leak.py")

    with pytest.raises(RealTokenSmokeGateError) as exc_info:
        _gate(repo, secret=secret).precheck(
            real_token_smoke=True,
            provider_transport="sdk",
            output_dir_explicit=True,
        )

    assert secret not in str(exc_info.value)
    assert "<masked>" in str(exc_info.value) or "secret-like data blocked" in str(exc_info.value)


def test_staged_diff_token_hit_fails_closed(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    secret = _fake_secret()
    staged = repo / "docs" / "staged.md"
    staged.write_text("credential=" + secret + "\n", encoding="utf-8")
    _git(repo, "add", "docs/staged.md")
    gate = _gate(repo, secret=secret)
    monkeypatch.setattr(gate, "_scan_repo_tracked_files", lambda: None)

    with pytest.raises(RealTokenSmokeGateError) as exc_info:
        gate.precheck(real_token_smoke=True, provider_transport="sdk", output_dir_explicit=True)

    assert "staged_diff" in str(exc_info.value)
    assert secret not in str(exc_info.value)


def test_payload_write_is_blocked_on_token_leak(tmp_path):
    repo = _init_repo(tmp_path)
    secret = _fake_secret()
    gate = _gate(repo, secret=secret)

    with pytest.raises(RealTokenSmokeGateError) as exc_info:
        gate.write_json_artifact(code="600406", artifact_name="akshare_raw.json", payload={"error": "token=" + secret})

    assert secret not in str(exc_info.value)
    assert not (repo / "output" / "provider_comparison" / TIMESTAMP).exists()


def test_diff_report_write_blocks_token_like_names_values_notes_and_metadata(tmp_path):
    repo = _init_repo(tmp_path)
    secret = _fake_secret()
    gate = _gate(repo, secret=secret)
    report = {
        "code": "600406",
        "diff_items": [
            {
                "category": "expected_provider_difference",
                "field_path": "raw.metadata.Auth" + secret,
                "akshare_value": "safe",
                "tushare_value": "credential=" + secret,
                "severity": "review",
                "review_required": True,
                "note": "provider note token=" + secret,
                "metadata": {"auth": secret},
            }
        ],
        "automatic_acceptance": False,
    }

    with pytest.raises(RealTokenSmokeGateError) as exc_info:
        gate.write_diff_report(code="600406", report=report, markdown="# safe\n")

    assert secret not in str(exc_info.value)
    assert not (repo / "output" / "provider_comparison" / TIMESTAMP).exists()


def test_reports_baseline_snapshot_detects_path_and_sha_change(tmp_path):
    repo = tmp_path / "repo"
    reports = repo / "output" / "reports"
    reports.mkdir(parents=True)
    report = reports / "baseline.txt"
    report.write_text("before\n", encoding="utf-8")
    baseline = snapshot_reports(repo)

    report.write_text("after\n", encoding="utf-8")

    with pytest.raises(RealTokenSmokeGateError):
        assert_snapshot_unchanged(snapshot_reports(repo), baseline)


def test_default_output_baseline_snapshot_detects_path_and_sha_change(tmp_path):
    repo = tmp_path / "repo"
    output = repo / "output"
    output.mkdir(parents=True)
    raw = output / "raw_600406.json"
    raw.write_text('{"before": true}\n', encoding="utf-8")
    baseline = snapshot_default_outputs(repo)

    raw.write_text('{"after": true}\n', encoding="utf-8")

    with pytest.raises(RealTokenSmokeGateError):
        assert_snapshot_unchanged(snapshot_default_outputs(repo), baseline)


def test_postcheck_accepts_unchanged_reports_and_default_output(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "output" / "reports").mkdir(parents=True)
    (repo / "output" / "reports" / "report.txt").write_text("stable\n", encoding="utf-8")
    (repo / "output" / "raw_600406.json").write_text('{"stable": true}\n', encoding="utf-8")
    gate = _gate(repo)
    precheck = gate.precheck(real_token_smoke=True, provider_transport="sdk", output_dir_explicit=True)

    gate.postcheck(precheck)

    assert (repo / "output" / "reports" / "report.txt").read_text(encoding="utf-8") == "stable\n"
    assert (repo / "output" / "raw_600406.json").read_text(encoding="utf-8") == '{"stable": true}\n'


def test_cleanup_refuses_provider_comparison_parent_reports_and_non_timestamp(tmp_path):
    repo = _init_repo(tmp_path)
    gate = _gate(repo)
    comparison_root = repo / "output" / "provider_comparison"
    reports = repo / "output" / "reports"
    non_timestamp = comparison_root / "not_timestamp"
    comparison_root.mkdir(parents=True)
    reports.mkdir(parents=True)
    non_timestamp.mkdir(parents=True)

    for target in (comparison_root, reports, non_timestamp):
        with pytest.raises(RealTokenSmokeGateError):
            gate.cleanup_timestamp_dir(target, sanitized_reason="blocked")

    assert comparison_root.exists()
    assert reports.exists()
    assert non_timestamp.exists()


def test_cleanup_deletes_only_strict_timestamp_directory(tmp_path):
    repo = _init_repo(tmp_path)
    gate = _gate(repo)
    timestamp_dir = repo / "output" / "provider_comparison" / TIMESTAMP
    reports = repo / "output" / "reports"
    timestamp_dir.mkdir(parents=True)
    reports.mkdir(parents=True)
    (timestamp_dir / "marker.txt").write_text("delete me\n", encoding="utf-8")
    (reports / "keep.txt").write_text("keep\n", encoding="utf-8")

    gate.cleanup_timestamp_dir(timestamp_dir, sanitized_reason="unit test blocker")

    assert not timestamp_dir.exists()
    assert reports.exists()
    assert (reports / "keep.txt").exists()


def test_artifact_path_rejects_path_traversal(tmp_path):
    repo = _init_repo(tmp_path)
    gate = _gate(repo)

    with pytest.raises(RealTokenSmokeGateError):
        gate.artifact_path(code="600406", artifact_name="../diff_report.json")


def test_artifact_path_rejects_symlink_traversal(tmp_path):
    repo = _init_repo(tmp_path)
    gate = _gate(repo)
    timestamp_dir = repo / "output" / "provider_comparison" / TIMESTAMP
    outside = tmp_path / "outside"
    timestamp_dir.mkdir(parents=True)
    outside.mkdir()
    link = timestamp_dir / "600406"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is not available in this environment")

    with pytest.raises(RealTokenSmokeGateError):
        gate.artifact_path(code="600406", artifact_name="diff_report.json")
