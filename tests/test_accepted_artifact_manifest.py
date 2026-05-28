# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import subprocess
from pathlib import Path

import pytest

import src.fundamental_skill.research_report.accepted_manifest as manifest_module
from src.fundamental_skill.research_report.accepted_manifest import (
    DEFAULT_MANIFEST_RELATIVE_PATH,
    MANIFEST_VERSION,
    ManifestEntryNotFoundError,
    ManifestHashMismatchError,
    ManifestPathBoundaryError,
    ManifestValidationError,
    build_accepted_manifest,
    build_freshness_warning,
    compute_file_sha256,
    get_freshness_status,
    get_manifest_entry,
    is_manifest_entry_usable_by_default,
    read_accepted_manifest,
    validate_accepted_manifest,
    validate_manifest_entry,
    verify_manifest_entry_hashes,
    write_accepted_manifest,
)


_REPO_ROOT = Path(__file__).resolve().parents[1]
_REAL_MANIFEST_PATH = _REPO_ROOT / "output" / "research_reports" / "accepted_manifest.json"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_real_manifest_state() -> dict[str, object]:
    if not _REAL_MANIFEST_PATH.exists():
        return {"exists": False}

    stat = _REAL_MANIFEST_PATH.stat()
    return {
        "exists": True,
        "sha256": _file_sha256(_REAL_MANIFEST_PATH),
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def assert_real_manifest_unchanged(snapshot: dict[str, object]) -> None:
    if not snapshot["exists"]:
        assert not _REAL_MANIFEST_PATH.exists()
    else:
        stat = _REAL_MANIFEST_PATH.stat()
        assert _file_sha256(_REAL_MANIFEST_PATH) == snapshot["sha256"]
        assert stat.st_mtime_ns == snapshot["mtime_ns"]
        assert stat.st_size == snapshot["size"]

    result = subprocess.run(
        ["git", "ls-files", "output"],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.splitlines() == []


def _sha(value: str) -> str:
    return value * 64


def _superseded_record(artifact_type: str, path: str, replacement_path: str) -> dict:
    return {
        "artifact_type": artifact_type,
        "path": path,
        "sha256": _sha("a"),
        "superseded_reason": "professional_voice_regeneration",
        "superseded_at": "2026-05-28T12:55:18+08:00",
        "replacement_path": replacement_path,
    }


def _entry(*, code: str = "002371", status: str = "current", hashes: dict | None = None) -> dict:
    html = "output/research_reports/20260528T125518/002371/fundamental_research_report_v1.html"
    markdown = "output/research_reports/20260528T125518/002371/fundamental_research_report_v1.md"
    json_path = "output/research_reports/20260527T220148/002371/fundamental_research_report_v1.json"
    return {
        "code": code,
        "company_name": "北方华创",
        "report_type": "fundamental_research_report_v1",
        "presentation_profile": "semiconductor_equipment_cycle",
        "accepted_artifacts": {
            "html": html,
            "markdown": markdown,
            "json": json_path,
        },
        "artifact_hashes": hashes
        or {
            "html_sha256": _sha("1"),
            "markdown_sha256": _sha("2"),
            "json_sha256": _sha("3"),
        },
        "acceptance": {
            "accepted_at": "2026-05-28T12:55:18+08:00",
            "accepted_stage": "cli_runtime_acceptance",
            "accepted_by": "human_or_codex_review",
            "acceptance_notes": [],
        },
        "freshness": {
            "freshness_status": status,
            "source_data_period": "2024A/2025Q1 local artifacts",
            "financial_report_period": "2024A",
            "valuation_as_of_date": "2026-05-27",
            "report_generated_at": "2026-05-28T12:55:18+08:00",
            "accepted_at": "2026-05-28T12:55:18+08:00",
            "valid_until": "2026-06-30",
            "last_freshness_check_at": "2026-05-28T12:55:18+08:00",
            "freshness_reason": "accepted CLI runtime baseline",
            "staleness_triggers": [],
            "manual_override": None,
        },
        "lineage": {
            "supersedes": [
                _superseded_record(
                    "markdown",
                    "output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md",
                    markdown,
                ),
                _superseded_record(
                    "html",
                    "output/research_reports/20260528T090024/002371/fundamental_research_report_v1.html",
                    html,
                ),
            ],
            "superseded_by": None,
            "source_artifacts": [],
        },
        "safety": {
            "not_for_trading_advice": True,
            "no_token": True,
            "no_provider_call": True,
        },
    }


def _manifest(*, entries: list[dict] | None = None) -> dict:
    return build_accepted_manifest(
        entries if entries is not None else [_entry()],
        created_at="2026-05-28T00:00:00+08:00",
        updated_at="2026-05-28T00:00:00+08:00",
    )


def test_build_manifest_top_level_schema():
    payload = _manifest()

    assert payload["version"] == MANIFEST_VERSION
    assert payload["created_at"] == "2026-05-28T00:00:00+08:00"
    assert payload["updated_at"] == "2026-05-28T00:00:00+08:00"
    assert payload["manifest_scope"] == "research_report_v1"
    assert isinstance(payload["entries"], list)
    assert DEFAULT_MANIFEST_RELATIVE_PATH == "output/research_reports/accepted_manifest.json"


def test_validate_valid_manifest():
    validate_accepted_manifest(_manifest())


def test_reject_invalid_version():
    payload = _manifest()
    payload["version"] = "accepted_artifact_manifest.v0"

    with pytest.raises(ManifestValidationError):
        validate_accepted_manifest(payload)


def test_reject_duplicate_code():
    with pytest.raises(ManifestValidationError):
        build_accepted_manifest([_entry(), _entry()])


def test_reject_invalid_code():
    entry = _entry(code="2371")

    with pytest.raises(ManifestValidationError):
        validate_manifest_entry(entry)


def test_reject_missing_accepted_artifact_fields():
    entry = _entry()
    del entry["accepted_artifacts"]["html"]

    with pytest.raises(ManifestValidationError):
        validate_manifest_entry(entry)


def test_reject_absolute_artifact_path():
    entry = _entry()
    entry["accepted_artifacts"]["html"] = "C:/Users/Admin/output/research_reports/report.html"

    with pytest.raises(ManifestPathBoundaryError):
        validate_manifest_entry(entry)


def test_reject_path_traversal():
    entry = _entry()
    entry["accepted_artifacts"]["html"] = "output/research_reports/../escape.html"

    with pytest.raises(ManifestPathBoundaryError):
        validate_manifest_entry(entry)


def test_reject_artifact_path_outside_research_reports():
    entry = _entry()
    entry["accepted_artifacts"]["html"] = "output/provider_comparison/20260528/002371/report.html"

    with pytest.raises(ManifestPathBoundaryError):
        validate_manifest_entry(entry)


def test_reject_invalid_freshness_status():
    entry = _entry(status="fresh")

    with pytest.raises(ManifestValidationError):
        validate_manifest_entry(entry)


@pytest.mark.parametrize("flag", ["not_for_trading_advice", "no_token", "no_provider_call"])
def test_reject_safety_flags_false(flag):
    entry = _entry()
    entry["safety"][flag] = False

    with pytest.raises(ManifestValidationError):
        validate_manifest_entry(entry)


@pytest.mark.parametrize("key", ["buy", "sell", "target_price", "position", "portfolio_weight"])
def test_reject_forbidden_recommendation_keys(key):
    entry = _entry()
    entry["freshness"][key] = "forbidden"

    with pytest.raises(ManifestValidationError):
        validate_manifest_entry(entry)


@pytest.mark.parametrize("hash_key", ["html_sha256", "markdown_sha256", "json_sha256"])
@pytest.mark.parametrize(
    "bad_value",
    [
        "",
        None,
        "abc",
        "g" * 64,
        "token=A9abcdefABCDEF1234567890abcdefABCDEF1234567890z",
        "Bearer A9abcdefABCDEF1234567890abcdefABCDEF1234567890z",
    ],
)
def test_reject_invalid_artifact_hashes(hash_key, bad_value):
    entry = _entry()
    entry["artifact_hashes"][hash_key] = bad_value

    with pytest.raises(ManifestValidationError):
        validate_manifest_entry(entry)


def test_uppercase_and_mixed_case_artifact_hashes_accepted():
    entry = _entry()
    entry["artifact_hashes"] = {
        "html_sha256": "A" * 64,
        "markdown_sha256": "abcdef1234567890ABCDEF1234567890abcdef1234567890ABCDEF1234567890",
        "json_sha256": "F" * 64,
    }

    validate_manifest_entry(entry)


def test_get_entry_by_code():
    entry = get_manifest_entry(_manifest(), "002371")

    assert entry["company_name"] == "北方华创"


def test_missing_entry_raises():
    with pytest.raises(ManifestEntryNotFoundError):
        get_manifest_entry(_manifest(), "600406")


def test_freshness_current_usable_no_warning():
    entry = _entry(status="current")

    assert get_freshness_status(entry) == "current"
    assert is_manifest_entry_usable_by_default(entry) is True
    assert build_freshness_warning(entry) is None


def test_freshness_unknown_usable_with_warning():
    entry = _entry(status="unknown")

    assert is_manifest_entry_usable_by_default(entry) is True
    assert "freshness_status=unknown" in (build_freshness_warning(entry) or "")


def test_freshness_stale_usable_with_warning():
    entry = _entry(status="stale")

    assert is_manifest_entry_usable_by_default(entry) is True
    assert "freshness_status=stale" in (build_freshness_warning(entry) or "")


def test_superseded_not_usable():
    entry = _entry(status="superseded")

    assert is_manifest_entry_usable_by_default(entry) is False
    assert "not the accepted baseline" in (build_freshness_warning(entry) or "")


def test_invalidated_not_usable_fail_closed_warning():
    entry = _entry(status="invalidated")

    assert is_manifest_entry_usable_by_default(entry) is False
    assert "must not be used" in (build_freshness_warning(entry) or "")


def test_mixed_timestamp_002371_accepted_bundle_valid():
    entry = _entry()
    validate_manifest_entry(entry)

    assert "20260528T125518" in entry["accepted_artifacts"]["html"]
    assert "20260528T125518" in entry["accepted_artifacts"]["markdown"]
    assert "20260527T220148" in entry["accepted_artifacts"]["json"]


def test_lineage_supersedes_old_artifact_records():
    entry = _entry()

    supersedes = entry["lineage"]["supersedes"]
    assert {item["artifact_type"] for item in supersedes} == {"markdown", "html"}
    assert supersedes[0]["path"] == "output/research_reports/20260527T220148/002371/fundamental_research_report_v1.md"
    assert supersedes[1]["path"] == "output/research_reports/20260528T090024/002371/fundamental_research_report_v1.html"
    for item in supersedes:
        assert {"artifact_type", "path", "sha256", "superseded_reason", "superseded_at", "replacement_path"} <= set(item)


def test_missing_lineage_supersedes_sha256_rejected():
    entry = _entry()
    del entry["lineage"]["supersedes"][0]["sha256"]

    with pytest.raises(ManifestValidationError):
        validate_manifest_entry(entry)


@pytest.mark.parametrize("value", [None, ""])
def test_lineage_supersedes_empty_sha256_accepted(value):
    entry = _entry()
    entry["lineage"]["supersedes"][0]["sha256"] = value

    validate_manifest_entry(entry)


@pytest.mark.parametrize(
    "bad_value",
    [
        "abc",
        "z" * 64,
        "token=A9abcdefABCDEF1234567890abcdefABCDEF1234567890z",
        "Bearer A9abcdefABCDEF1234567890abcdefABCDEF1234567890z",
    ],
)
def test_invalid_non_empty_lineage_supersedes_sha256_rejected(bad_value):
    entry = _entry()
    entry["lineage"]["supersedes"][0]["sha256"] = bad_value

    with pytest.raises(ManifestValidationError):
        validate_manifest_entry(entry)


def _write_fake_artifacts(tmp_path: Path, entry: dict) -> dict:
    hashes = {}
    for kind, hash_key, text in (
        ("html", "html_sha256", "<html>accepted</html>"),
        ("markdown", "markdown_sha256", "# accepted"),
        ("json", "json_sha256", '{"accepted": true}'),
    ):
        artifact_path = tmp_path / entry["accepted_artifacts"][kind]
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(text, encoding="utf-8")
        hashes[hash_key] = compute_file_sha256(artifact_path)
    return hashes


def test_compute_and_verify_sha256_success(tmp_path):
    entry = _entry()
    entry["artifact_hashes"] = _write_fake_artifacts(tmp_path, entry)

    verify_manifest_entry_hashes(entry, repo_root=tmp_path)


def test_verify_hash_mismatch_fails(tmp_path):
    entry = _entry()
    entry["artifact_hashes"] = _write_fake_artifacts(tmp_path, entry)
    entry["artifact_hashes"]["html_sha256"] = _sha("f")

    with pytest.raises(ManifestHashMismatchError):
        verify_manifest_entry_hashes(entry, repo_root=tmp_path)


def test_verify_missing_file_fails(tmp_path):
    entry = _entry()

    with pytest.raises(ManifestHashMismatchError):
        verify_manifest_entry_hashes(entry, repo_root=tmp_path)


def test_writer_writes_only_tmpdir(tmp_path):
    payload = _manifest()
    manifest_path = tmp_path / "accepted_manifest.json"

    written = write_accepted_manifest(payload, manifest_path)

    assert written == manifest_path.resolve(strict=False)
    assert json.loads(written.read_text(encoding="utf-8")) == payload
    assert sorted(item.name for item in tmp_path.iterdir()) == ["accepted_manifest.json"]


def test_writer_blocks_path_traversal(tmp_path):
    payload = _manifest()

    with pytest.raises(ManifestPathBoundaryError):
        write_accepted_manifest(payload, tmp_path / ".." / "accepted_manifest.json")


@pytest.mark.parametrize(
    "bad_value",
    [
        "token=A9abcdefABCDEF1234567890abcdefABCDEF1234567890z",
        "Bearer A9abcdefABCDEF1234567890abcdefABCDEF1234567890z",
        "mcp://local-secret-endpoint",
        "load path/to/.env.local",
        "C:\\Users\\Example\\secrets\\credential.txt",
    ],
)
def test_writer_secret_scan_blocks_sensitive_values_without_leaking(tmp_path, bad_value):
    payload = _manifest()
    payload["entries"][0]["freshness"]["freshness_reason"] = bad_value

    with pytest.raises(ManifestValidationError) as exc_info:
        write_accepted_manifest(payload, tmp_path / "accepted_manifest.json")

    message = str(exc_info.value)
    assert "<masked>" in message
    assert bad_value not in message


@pytest.mark.parametrize("key", ["TUSHARE_TOKEN", "api_key", "access_token"])
def test_token_like_dict_key_blocked_without_leaking_raw_secret(tmp_path, key):
    secret = "A9abcdefABCDEF1234567890abcdefABCDEF1234567890z"
    payload = _manifest()
    payload["entries"][0]["freshness"][key] = secret

    with pytest.raises(ManifestValidationError) as exc_info:
        write_accepted_manifest(payload, tmp_path / "accepted_manifest.json")

    message = str(exc_info.value)
    assert "<masked>" in message
    assert secret not in message


def test_reader_roundtrip(tmp_path):
    payload = _manifest()
    path = write_accepted_manifest(payload, tmp_path / "accepted_manifest.json")

    assert read_accepted_manifest(path) == payload


def test_no_real_output_path_writes(tmp_path):
    real_manifest_snapshot = snapshot_real_manifest_state()
    payload = _manifest()
    path = write_accepted_manifest(payload, tmp_path / "accepted_manifest.json")

    assert path.is_file()
    assert_real_manifest_unchanged(real_manifest_snapshot)


def test_accepted_manifest_module_has_no_provider_env_network_mcp_or_runner_imports():
    source = inspect.getsource(manifest_module)

    assert "data_providers" not in source
    assert "tushare_provider" not in source
    assert "akshare_provider" not in source
    assert "provider_router" not in source
    assert "import os" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "requests" not in source
    assert "socket" not in source
    assert "urllib" not in source
    assert "subprocess" not in source
    assert "list_mcp" not in source
    assert "mcp__" not in source
    assert "real_stock_runner" not in source
    assert "generate_report" not in source
    assert "orchestration" not in source
