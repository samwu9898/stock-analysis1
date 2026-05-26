# -*- coding: utf-8 -*-

import hashlib
import json
import os
import subprocess
import uuid

import pytest

from src.fundamental_skill.data_providers.real_token_smoke_gate import (
    RealTokenSmokeGate,
    RealTokenSmokeGateError,
    assert_snapshot_unchanged,
    snapshot_default_outputs,
    snapshot_reports,
)


TIMESTAMP = "20260526T120000"
SAFE_FAKE_TOKEN = "FAKE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
SAFE_TEST_TOKEN = "TEST_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"
SAFE_EXAMPLE_TOKEN = "EXAMPLE_TOKEN_FOR_TESTING_ONLY__NOT_REAL__XYZ_1234567890"


def _realistic_token_like():
    return "Z9" + uuid.uuid4().hex + "a" + uuid.uuid4().hex


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _commit_all(repo, message="test snapshot"):
    return _git(
        repo,
        "-c",
        "user.name=Codex Tests",
        "-c",
        "user.email=codex-tests@example.invalid",
        "commit",
        "--allow-empty",
        "-m",
        message,
    )


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docs").mkdir()
    (repo / "tests").mkdir()
    (repo / "src").mkdir()
    (repo / "docs" / "safe.md").write_text("safe provider smoke notes\n", encoding="utf-8")
    _git(repo, "init")
    _git(repo, "add", "docs/safe.md")
    _commit_all(repo, "initial safe docs")
    return repo


def _gate(repo, *, secret=None):
    return RealTokenSmokeGate(
        repo_root=repo,
        output_dir="output/provider_comparison",
        timestamp=TIMESTAMP,
        codes=["600406"],
        secret_refs=(secret,) if secret else (),
    )


def _line_hash(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def _write_allowlist(repo, entries):
    config_dir = repo / "config"
    config_dir.mkdir(exist_ok=True)
    path = config_dir / "token_leak_allowlist.yaml"
    path.write_text(json.dumps({"entries": entries}, indent=2), encoding="utf-8")
    _git(repo, "add", "config/token_leak_allowlist.yaml")
    return path


def _valid_allowlist_entry(*, path: str, line: str, category: str = "doc_example"):
    return {
        "path": path,
        "line_content_hash": _line_hash(line),
        "reason": "irreducible external fixture retained for scanner test coverage",
        "category": category,
        "owner": "data-provider-gate",
        "review_date": "2026-05-26",
        "expiry": "2099-01-01",
    }


def _assert_secret_not_rendered(secret: str, text: str) -> None:
    if secret in text:
        raise AssertionError("secret-like value was rendered")


def test_precheck_fails_on_token_in_tracked_file(tmp_path):
    repo = _init_repo(tmp_path)
    secret = _realistic_token_like()
    leak = repo / "src" / "leak.py"
    leak.write_text("ERROR = 'token=" + secret + "'\n", encoding="utf-8")
    _git(repo, "add", "src/leak.py")

    with pytest.raises(RealTokenSmokeGateError) as exc_info:
        _gate(repo, secret=secret).precheck(
            real_token_smoke=True,
            provider_transport="sdk",
            output_dir_explicit=True,
        )

    _assert_secret_not_rendered(secret, str(exc_info.value))
    assert "<masked>" in str(exc_info.value) or "secret-like data blocked" in str(exc_info.value)


def test_staged_diff_token_hit_fails_closed(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    secret = _realistic_token_like()
    staged = repo / "docs" / "staged.md"
    staged.write_text("credential=" + secret + "\n", encoding="utf-8")
    _git(repo, "add", "docs/staged.md")
    gate = _gate(repo, secret=secret)
    monkeypatch.setattr(gate, "_scan_repo_tracked_files", lambda: None)

    with pytest.raises(RealTokenSmokeGateError) as exc_info:
        gate.precheck(real_token_smoke=True, provider_transport="sdk", output_dir_explicit=True)

    assert "staged_diff" in str(exc_info.value)
    _assert_secret_not_rendered(secret, str(exc_info.value))


def test_rewritten_readme_doc_entry_does_not_block_precheck(tmp_path):
    repo = _init_repo(tmp_path)
    readme = repo / "README.md"
    readme.write_text(
        "- Research Intelligence Framework v1 spec: P0 design, artifact boundary, and roadmap.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "README.md")
    _commit_all(repo, "add rewritten readme entry")

    precheck = _gate(repo).precheck(real_token_smoke=True, provider_transport="sdk", output_dir_explicit=True)

    assert precheck.repo_root == repo.resolve()


def test_prefixed_fake_tokens_in_tests_do_not_block_tracked_scan(tmp_path):
    repo = _init_repo(tmp_path)
    fixture = repo / "tests" / "fake_tokens.py"
    fixture.write_text(
        "\n".join(
            [
                f'TUSHARE_TOKEN = "{SAFE_FAKE_TOKEN}"',
                f'API_KEY = "{SAFE_TEST_TOKEN}"',
                f'CREDENTIAL = "{SAFE_EXAMPLE_TOKEN}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", "tests/fake_tokens.py")
    _commit_all(repo, "add fake token fixtures")

    precheck = _gate(repo).precheck(real_token_smoke=True, provider_transport="sdk", output_dir_explicit=True)

    assert precheck.codes == ("600406",)


def test_safe_doc_placeholders_do_not_block_tracked_scan(tmp_path):
    repo = _init_repo(tmp_path)
    doc = repo / "docs" / "placeholders.md"
    doc.write_text(
        "\n".join(
            [
                "Use token=<YOUR_TOKEN> in local-only examples.",
                "Use TUSHARE_TOKEN=<TUSHARE_TOKEN> as the environment placeholder.",
                "A sanitized header may read Authorization: Bearer <REDACTED>.",
                "A local pattern example may read mcp?token=<TUSHARE_TOKEN>.",
                "The scanner finding name token_like_value is safe prose.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", "docs/placeholders.md")
    _commit_all(repo, "add safe placeholders")

    precheck = _gate(repo).precheck(real_token_smoke=True, provider_transport="sdk", output_dir_explicit=True)

    assert precheck.timestamp == TIMESTAMP


def test_docs_realistic_long_token_like_value_still_blocks(tmp_path):
    repo = _init_repo(tmp_path)
    secret = _realistic_token_like()
    doc = repo / "docs" / "leak.md"
    doc.write_text("The example must not contain token=" + secret + "\n", encoding="utf-8")
    _git(repo, "add", "docs/leak.md")

    with pytest.raises(RealTokenSmokeGateError) as exc_info:
        _gate(repo).precheck(real_token_smoke=True, provider_transport="sdk", output_dir_explicit=True)

    _assert_secret_not_rendered(secret, str(exc_info.value))


def test_allowlist_valid_doc_entry_allows_irreducible_fixture_line(tmp_path):
    repo = _init_repo(tmp_path)
    secret = _realistic_token_like()
    line = "External immutable fixture example token=" + secret
    doc = repo / "docs" / "fixture.md"
    doc.write_text(line + "\n", encoding="utf-8")
    _write_allowlist(repo, [_valid_allowlist_entry(path="docs/fixture.md", line=line)])
    _git(repo, "add", "docs/fixture.md")
    _commit_all(repo, "add allowlisted fixture")

    precheck = _gate(repo).precheck(real_token_smoke=True, provider_transport="sdk", output_dir_explicit=True)

    assert precheck.output_dir == (repo / "output" / "provider_comparison").resolve(strict=False)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda entry: {**entry, "path": "docs/*.md"},
        lambda entry: {**entry, "path": "src/leak.py"},
        lambda entry: {**entry, "expiry": "2000-01-01"},
        lambda entry: {key: value for key, value in entry.items() if key != "reason"},
        lambda entry: {key: value for key, value in entry.items() if key != "expiry"},
    ],
)
def test_allowlist_invalid_entries_fail_closed(tmp_path, mutate):
    repo = _init_repo(tmp_path)
    line = "safe line"
    entry = mutate(_valid_allowlist_entry(path="docs/fixture.md", line=line))
    _write_allowlist(repo, [entry])

    with pytest.raises(RealTokenSmokeGateError) as exc_info:
        _gate(repo).precheck(real_token_smoke=True, provider_transport="sdk", output_dir_explicit=True)

    assert "token_allowlist" in str(exc_info.value)


def test_payload_write_is_blocked_on_token_leak(tmp_path):
    repo = _init_repo(tmp_path)
    secret = _realistic_token_like()
    gate = _gate(repo, secret=secret)

    with pytest.raises(RealTokenSmokeGateError) as exc_info:
        gate.write_json_artifact(code="600406", artifact_name="akshare_raw.json", payload={"error": "token=" + secret})

    _assert_secret_not_rendered(secret, str(exc_info.value))
    assert not (repo / "output" / "provider_comparison" / TIMESTAMP).exists()


def test_target_output_artifact_token_like_value_blocks_precheck(tmp_path):
    repo = _init_repo(tmp_path)
    secret = _realistic_token_like()
    artifact = repo / "output" / "provider_comparison" / "20260525T120000" / "600406" / "diff_report.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("provider note token=" + secret + "\n", encoding="utf-8")

    with pytest.raises(RealTokenSmokeGateError) as exc_info:
        _gate(repo).precheck(real_token_smoke=True, provider_transport="sdk", output_dir_explicit=True)

    _assert_secret_not_rendered(secret, str(exc_info.value))


def test_diff_report_write_blocks_token_like_names_values_notes_and_metadata(tmp_path):
    repo = _init_repo(tmp_path)
    secret = _realistic_token_like()
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

    _assert_secret_not_rendered(secret, str(exc_info.value))
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
