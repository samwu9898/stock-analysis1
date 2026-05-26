# -*- coding: utf-8 -*-
"""Safety gate for local-only real-token provider smoke runs.

This module contains only guardrails: CLI validation, token-leak scans, artifact
path enforcement, protected-output snapshots, and cleanup safety. It does not
read credentials, read MCP config, connect MCP, or call provider SDKs.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from .comparison_artifacts import BASE_ARTIFACT_NAMES, P1_ARTIFACT_NAMES, default_comparison_timestamp
from .token_leak_scanner import (
    SOURCE_CODE_TOKEN_LEAK_POLICY,
    STRICT_TOKEN_LEAK_POLICY,
    TRACKED_DOCS_TOKEN_LEAK_POLICY,
    TRACKED_TESTS_TOKEN_LEAK_POLICY,
    TokenLeakError,
    TokenLeakScanPolicy,
    assert_no_token_leaks,
    scan_for_token_leaks,
)
from .token_safety import sanitize_text


TIMESTAMP_RE = re.compile(r"^\d{8}T\d{6}$")
CODE_RE = re.compile(r"^\d{6}$")
ALLOWED_TRANSPORTS = {"sdk"}
RESERVED_TRANSPORTS = {"http", "mcp-local"}
ALLOWED_ARTIFACT_NAMES = frozenset(BASE_ARTIFACT_NAMES + P1_ARTIFACT_NAMES)
SCAN_TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".md",
    ".py",
    ".rst",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
ALLOWLIST_DEFAULT_PATH = "config/token_leak_allowlist.yaml"
ALLOWLIST_REQUIRED_FIELDS = frozenset(
    {"path", "line_content_hash", "reason", "category", "owner", "review_date", "expiry"}
)
ALLOWLIST_CATEGORIES = frozenset({"doc_example", "test_fixture"})
ALLOWLIST_FORBIDDEN_PREFIXES = ("src/", "output/", "artifact/", "artifacts/", "logs/")


class RealTokenSmokeGateError(RuntimeError):
    """Sanitized real-token smoke gate blocker."""

    def __init__(self, gate_name: str, reason: object) -> None:
        self.gate_name = _safe_label(gate_name)
        self.reason = _sanitize_reason(reason)
        super().__init__(f"real-token smoke gate blocked: gate={self.gate_name} reason={self.reason}")


@dataclass(frozen=True)
class BaselineSnapshot:
    name: str
    files: Mapping[str, str]


@dataclass(frozen=True)
class RealTokenSmokePrecheck:
    repo_root: Path
    output_dir: Path
    timestamp: str
    timestamp_dir: Path
    codes: tuple[str, ...]
    reports_snapshot: BaselineSnapshot
    default_output_snapshot: BaselineSnapshot


@dataclass(frozen=True)
class TokenLeakAllowlistEntry:
    path: str
    line_content_hash: str
    reason: str
    category: str
    owner: str
    review_date: str
    expiry: str


@dataclass(frozen=True)
class TokenLeakAllowlist:
    entries: Mapping[tuple[str, str], TokenLeakAllowlistEntry]

    @classmethod
    def load(cls, repo_root: Path, allowlist_path: Path | None) -> "TokenLeakAllowlist":
        if allowlist_path is None or not allowlist_path.exists():
            return cls({})
        data = _read_allowlist_data(allowlist_path)
        if isinstance(data, MappingABC):
            raw_entries = data.get("entries", ())
        elif isinstance(data, list):
            raw_entries = data
        else:
            raise RealTokenSmokeGateError("token_allowlist", "allowlist must be a list or contain entries")
        today = date.today()
        entries: dict[tuple[str, str], TokenLeakAllowlistEntry] = {}
        for raw_entry in raw_entries:
            entry = _validate_allowlist_entry(raw_entry, today=today)
            entries[(entry.path, entry.line_content_hash)] = entry
        return cls(entries)

    def allows(self, *, rel_path: str, line_content_hash: str) -> bool:
        return (rel_path, line_content_hash) in self.entries


class RealTokenSmokeGate:
    """Precheck / runtime / postcheck helper for the real-token smoke path."""

    def __init__(
        self,
        *,
        repo_root: str | Path,
        output_dir: str | Path = "output/provider_comparison",
        timestamp: str | None = None,
        codes: Sequence[str] = (),
        secret_refs: Iterable[str | None] | None = None,
        allowlist_path: str | Path | None = ALLOWLIST_DEFAULT_PATH,
    ) -> None:
        self.repo_root = Path(repo_root).resolve(strict=False)
        self.output_dir = _repo_path(self.repo_root, output_dir)
        self.timestamp = timestamp or default_comparison_timestamp()
        self.codes = tuple(str(code) for code in codes)
        self.secret_refs = tuple(secret for secret in (secret_refs or ()) if secret)
        self.allowlist_path = _repo_path(self.repo_root, allowlist_path) if allowlist_path is not None else None
        self._token_allowlist: TokenLeakAllowlist | None = None
        self.blockers: list[str] = []

    @property
    def expected_output_dir(self) -> Path:
        return (self.repo_root / "output" / "provider_comparison").resolve(strict=False)

    @property
    def timestamp_dir(self) -> Path:
        return self.output_dir / self.timestamp

    def precheck(
        self,
        *,
        real_token_smoke: bool,
        provider_transport: str | None,
        output_dir_explicit: bool,
    ) -> RealTokenSmokePrecheck:
        """Run all static gates before any credential read or provider call."""

        validate_real_token_smoke_flags(
            real_token_smoke=real_token_smoke,
            provider_transport=provider_transport,
            output_dir=self.output_dir,
            output_dir_explicit=output_dir_explicit,
            codes=self.codes,
            repo_root=self.repo_root,
        )
        self._validate_timestamp()
        self._validate_codes()
        self._scan_repo_tracked_files()
        self._scan_staged_diff()
        self._scan_docs_tests_source()
        self._scan_target_output_dir()

        return RealTokenSmokePrecheck(
            repo_root=self.repo_root,
            output_dir=self.output_dir,
            timestamp=self.timestamp,
            timestamp_dir=self.timestamp_dir,
            codes=self.codes,
            reports_snapshot=snapshot_reports(self.repo_root),
            default_output_snapshot=snapshot_default_outputs(self.repo_root),
        )

    def scan_payload_before_write(self, payload: Any, *, context: str) -> None:
        try:
            assert_no_token_leaks(payload, context=context, secret_refs=self.secret_refs)
        except TokenLeakError as exc:
            self._block("runtime_payload_scan", exc)

    def assert_diff_report_safe(self, report: Mapping[str, Any], markdown: str | None = None) -> None:
        self.scan_payload_before_write(report, context="diff_report")
        if markdown is not None:
            self.scan_payload_before_write(markdown, context="diff_report.md")

    def artifact_path(self, *, code: str, artifact_name: str) -> Path:
        self._validate_output_dir()
        self._validate_timestamp()
        normalized_code = _validate_code(code)
        if artifact_name not in ALLOWED_ARTIFACT_NAMES:
            self._block("artifact_name", "artifact name is not allowlisted")
        timestamp_dir = self.timestamp_dir
        if timestamp_dir.exists() and timestamp_dir.is_symlink():
            self._block("artifact_path", "timestamp directory may not be a symlink")
        path = timestamp_dir / normalized_code / artifact_name
        _ensure_inside_resolved(path, timestamp_dir)
        return path

    def write_json_artifact(self, *, code: str, artifact_name: str, payload: Any) -> Path:
        if not artifact_name.endswith(".json"):
            self._block("artifact_name", "JSON artifact must use .json extension")
        self.scan_payload_before_write(payload, context=artifact_name)
        path = self.artifact_path(code=code, artifact_name=artifact_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return path

    def write_text_artifact(self, *, code: str, artifact_name: str, text: str) -> Path:
        self.scan_payload_before_write(text, context=artifact_name)
        path = self.artifact_path(code=code, artifact_name=artifact_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_diff_report(self, *, code: str, report: Mapping[str, Any], markdown: str) -> tuple[Path, Path]:
        self.assert_diff_report_safe(report, markdown)
        json_path = self.write_json_artifact(code=code, artifact_name="diff_report.json", payload=report)
        md_path = self.write_text_artifact(code=code, artifact_name="diff_report.md", text=markdown)
        return json_path, md_path

    def postcheck(self, precheck: RealTokenSmokePrecheck, *, cleanup_on_blocker: bool = True) -> None:
        """Run leak and protected-output checks after a smoke attempt."""

        try:
            self._scan_generated_artifacts()
            self._scan_git_diff()
            assert_snapshot_unchanged(snapshot_reports(self.repo_root), precheck.reports_snapshot)
            assert_snapshot_unchanged(snapshot_default_outputs(self.repo_root), precheck.default_output_snapshot)
            self._assert_comparison_artifacts_not_git_tracked_or_staged()
        except RealTokenSmokeGateError as exc:
            if cleanup_on_blocker:
                self.cleanup_timestamp_dir(self.timestamp_dir, sanitized_reason=exc.reason)
            raise

    def cleanup_timestamp_dir(self, target: str | Path, *, sanitized_reason: object = "") -> None:
        target_path = _repo_path(self.repo_root, target)
        comparison_root = self.expected_output_dir
        resolved_target = target_path.resolve(strict=False)
        if target_path.is_symlink():
            self._block("cleanup", "cleanup target may not be a symlink")
        if resolved_target.parent != comparison_root:
            self._block("cleanup", "cleanup target is not a direct timestamp directory")
        if not TIMESTAMP_RE.fullmatch(resolved_target.name):
            self._block("cleanup", "cleanup target name is not a strict timestamp")
        if not target_path.is_dir():
            self._block("cleanup", "cleanup target is not a directory")
        if resolved_target == comparison_root:
            self._block("cleanup", "cleanup target may not be provider_comparison")
        reason = _sanitize_reason(sanitized_reason)
        self.blockers.append(f"cleanup:{reason}")
        shutil.rmtree(resolved_target)

    def _validate_output_dir(self) -> None:
        if self.output_dir.resolve(strict=False) != self.expected_output_dir:
            self._block("artifact_boundary", "output directory must be repo output/provider_comparison")

    def _validate_timestamp(self) -> None:
        if not TIMESTAMP_RE.fullmatch(self.timestamp):
            self._block("timestamp", "timestamp must use YYYYMMDDTHHMMSS")

    def _validate_codes(self) -> None:
        if not self.codes:
            self._block("cli_flags", "sample code list is required")
        for code in self.codes:
            _validate_code(code)

    def _scan_repo_tracked_files(self) -> None:
        allowlist = self._load_token_allowlist()
        for rel_path in self._git_lines("ls-files"):
            normalized_rel = rel_path.replace("\\", "/")
            if normalized_rel.endswith(".mcp.json"):
                continue
            path = self.repo_root / rel_path
            self._scan_file(
                path,
                context=f"tracked_file:{_safe_relpath(path, self.repo_root)}",
                policy=_policy_for_relpath(normalized_rel),
                rel_path=normalized_rel,
                allowlist=allowlist if _allowlist_allowed_for_relpath(normalized_rel) else None,
            )

    def _scan_staged_diff(self) -> None:
        diff_text = self._git_text("diff", "--cached", "--no-ext-diff", "--")
        self._scan_text(diff_text, context="staged_diff")

    def _scan_docs_tests_source(self) -> None:
        allowlist = self._load_token_allowlist()
        for dirname in ("docs", "tests", "src"):
            root = self.repo_root / dirname
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in SCAN_TEXT_SUFFIXES:
                    rel_path = _safe_relpath(path, self.repo_root)
                    self._scan_file(
                        path,
                        context=f"{dirname}_source:{rel_path}",
                        policy=_policy_for_relpath(rel_path),
                        rel_path=rel_path,
                        allowlist=allowlist if _allowlist_allowed_for_relpath(rel_path) else None,
                    )

    def _scan_target_output_dir(self) -> None:
        if not self.output_dir.exists():
            return
        for path in self.output_dir.rglob("*"):
            if path.is_file():
                self._scan_file(path, context=f"target_output:{_safe_relpath(path, self.repo_root)}")

    def _scan_generated_artifacts(self) -> None:
        if not self.timestamp_dir.exists():
            return
        for path in self.timestamp_dir.rglob("*"):
            if path.is_file():
                _ensure_inside_resolved(path, self.timestamp_dir)
                self._scan_file(path, context=f"generated_artifact:{_safe_relpath(path, self.repo_root)}")

    def _scan_git_diff(self) -> None:
        self._scan_text(self._git_text("diff", "--no-ext-diff", "--"), context="git_diff")
        self._scan_text(self._git_text("diff", "--cached", "--no-ext-diff", "--"), context="git_staged_diff")

    def _assert_comparison_artifacts_not_git_tracked_or_staged(self) -> None:
        tracked = self._git_lines("ls-files", "--", "output/provider_comparison")
        staged = self._git_lines("diff", "--cached", "--name-only", "--", "output/provider_comparison")
        if tracked:
            self._block("postcheck_git_tracking", "comparison artifacts must not be tracked")
        if staged:
            self._block("postcheck_git_tracking", "comparison artifacts must not be staged")

    def _scan_file(
        self,
        path: Path,
        *,
        context: str,
        policy: TokenLeakScanPolicy = STRICT_TOKEN_LEAK_POLICY,
        rel_path: str | None = None,
        allowlist: TokenLeakAllowlist | None = None,
    ) -> None:
        if not path.exists() or not path.is_file():
            return
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            self._block("file_scan", exc)
        for line_number, line in enumerate(text.splitlines(), start=1):
            result = scan_for_token_leaks(line, secret_refs=self.secret_refs, policy=policy)
            if result.ok:
                continue
            line_hash = _sha256_text(line)
            if rel_path and allowlist and allowlist.allows(rel_path=rel_path, line_content_hash=line_hash):
                continue
            self._block("token_scan", f"{context}:{line_number} contains secret-like data: {result}")

    def _scan_text(self, text: str, *, context: str) -> None:
        result = scan_for_token_leaks(text, secret_refs=self.secret_refs)
        if not result.ok:
            self._block("token_scan", f"{context} contains secret-like data: {result}")

    def _load_token_allowlist(self) -> TokenLeakAllowlist:
        if self._token_allowlist is None:
            try:
                self._token_allowlist = TokenLeakAllowlist.load(self.repo_root, self.allowlist_path)
            except RealTokenSmokeGateError:
                raise
            except Exception as exc:  # pragma: no cover - defensive fail-closed path
                self._block("token_allowlist", type(exc).__name__)
        return self._token_allowlist

    def _git_lines(self, *args: str) -> list[str]:
        text = self._git_text(*args)
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _git_text(self, *args: str) -> str:
        try:
            completed = subprocess.run(
                ["git", *args],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            self._block("git_precheck", type(exc).__name__)
        return completed.stdout

    def _block(self, gate_name: str, reason: object) -> None:
        safe_reason = _sanitize_reason(reason, secret_refs=self.secret_refs)
        self.blockers.append(f"{_safe_label(gate_name)}:{safe_reason}")
        raise RealTokenSmokeGateError(gate_name, safe_reason)


def validate_real_token_smoke_flags(
    *,
    real_token_smoke: bool,
    provider_transport: str | None,
    output_dir: str | Path,
    output_dir_explicit: bool,
    codes: Sequence[str],
    repo_root: str | Path,
) -> None:
    transport = str(provider_transport).strip().lower() if provider_transport else None
    if transport and not real_token_smoke:
        raise RealTokenSmokeGateError("cli_flags", "--provider-transport requires --real-token-smoke")
    if not real_token_smoke:
        return
    if not transport:
        raise RealTokenSmokeGateError("cli_flags", "--real-token-smoke requires --provider-transport")
    if transport in RESERVED_TRANSPORTS:
        raise RealTokenSmokeGateError("cli_flags", "provider transport is reserved for future implementation")
    if transport not in ALLOWED_TRANSPORTS:
        raise RealTokenSmokeGateError("cli_flags", "provider transport is not supported")
    if not output_dir_explicit:
        raise RealTokenSmokeGateError("cli_flags", "--output-dir output/provider_comparison is required")
    root = Path(repo_root).resolve(strict=False)
    out = _repo_path(root, output_dir)
    if out.resolve(strict=False) != (root / "output" / "provider_comparison").resolve(strict=False):
        raise RealTokenSmokeGateError("cli_flags", "--output-dir must be output/provider_comparison")
    if not codes:
        raise RealTokenSmokeGateError("cli_flags", "sample code list is required")
    for code in codes:
        _validate_code(code)


def snapshot_reports(repo_root: str | Path) -> BaselineSnapshot:
    root = Path(repo_root).resolve(strict=False)
    return BaselineSnapshot("output/reports", _snapshot_paths(root, [root / "output" / "reports"]))


def snapshot_default_outputs(repo_root: str | Path) -> BaselineSnapshot:
    root = Path(repo_root).resolve(strict=False)
    output = root / "output"
    paths = [
        *output.glob("raw_*"),
        *output.glob("fundamental_*"),
        *output.glob("evidence_pack_*"),
    ]
    return BaselineSnapshot("default_output", _snapshot_paths(root, paths))


def assert_snapshot_unchanged(current: BaselineSnapshot, baseline: BaselineSnapshot) -> None:
    if dict(current.files) != dict(baseline.files):
        raise RealTokenSmokeGateError(baseline.name, "protected output path set or SHA-256 hash changed")


def sanitize_gate_exception(exc: BaseException, *, gate_name: str = "real_token_smoke") -> RealTokenSmokeGateError:
    return RealTokenSmokeGateError(gate_name, type(exc).__name__)


def _snapshot_paths(repo_root: Path, roots: Iterable[Path]) -> dict[str, str]:
    files: dict[str, str] = {}
    for root in roots:
        if not root.exists():
            continue
        candidates = root.rglob("*") if root.is_dir() else (root,)
        for path in candidates:
            if not path.is_file():
                continue
            rel = _safe_relpath(path, repo_root)
            files[rel] = _sha256(path)
    return dict(sorted(files.items()))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_allowlist_data(path: Path) -> object:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RealTokenSmokeGateError("token_allowlist", "allowlist file could not be read") from exc
    if not text.strip():
        return []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RealTokenSmokeGateError("token_allowlist", "allowlist YAML parser is unavailable") from exc
    try:
        return yaml.safe_load(text) or []
    except Exception as exc:  # pragma: no cover - parser-specific errors vary
        raise RealTokenSmokeGateError("token_allowlist", "allowlist file could not be parsed") from exc


def _validate_allowlist_entry(raw_entry: object, *, today: date) -> TokenLeakAllowlistEntry:
    if not isinstance(raw_entry, MappingABC):
        raise RealTokenSmokeGateError("token_allowlist", "allowlist entry must be a mapping")
    missing = ALLOWLIST_REQUIRED_FIELDS - set(raw_entry)
    if missing:
        raise RealTokenSmokeGateError("token_allowlist", "allowlist entry is missing required fields")
    path = _validate_allowlist_path(raw_entry["path"])
    line_hash = str(raw_entry["line_content_hash"]).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", line_hash):
        raise RealTokenSmokeGateError("token_allowlist", "allowlist line hash must be SHA-256")
    category = str(raw_entry["category"]).strip()
    if category not in ALLOWLIST_CATEGORIES:
        raise RealTokenSmokeGateError("token_allowlist", "allowlist category is not supported")
    if category == "doc_example" and not path.startswith("docs/"):
        raise RealTokenSmokeGateError("token_allowlist", "doc_example allowlist path must be under docs")
    if category == "test_fixture" and not path.startswith("tests/"):
        raise RealTokenSmokeGateError("token_allowlist", "test_fixture allowlist path must be under tests")
    reason = str(raw_entry["reason"]).strip()
    owner = str(raw_entry["owner"]).strip()
    review_date = str(raw_entry["review_date"]).strip()
    expiry = str(raw_entry["expiry"]).strip()
    if not reason:
        raise RealTokenSmokeGateError("token_allowlist", "allowlist reason is required")
    if not owner:
        raise RealTokenSmokeGateError("token_allowlist", "allowlist owner is required")
    _parse_allowlist_date(review_date, field_name="review_date")
    expiry_date = _parse_allowlist_date(expiry, field_name="expiry")
    if expiry_date < today:
        raise RealTokenSmokeGateError("token_allowlist", "allowlist entry has expired")
    return TokenLeakAllowlistEntry(
        path=path,
        line_content_hash=line_hash,
        reason=reason,
        category=category,
        owner=owner,
        review_date=review_date,
        expiry=expiry,
    )


def _validate_allowlist_path(value: object) -> str:
    raw_path = str(value).strip()
    if not raw_path or raw_path != str(value):
        raise RealTokenSmokeGateError("token_allowlist", "allowlist path must be exact")
    if "\\" in raw_path or any(char in raw_path for char in "*?[]"):
        raise RealTokenSmokeGateError("token_allowlist", "allowlist path may not use wildcard syntax")
    rel = PurePosixPath(raw_path)
    if rel.is_absolute() or any(part in ("", ".", "..") for part in rel.parts):
        raise RealTokenSmokeGateError("token_allowlist", "allowlist path must be a relative repo path")
    normalized = rel.as_posix()
    if normalized != raw_path:
        raise RealTokenSmokeGateError("token_allowlist", "allowlist path must be normalized")
    if raw_path.startswith(ALLOWLIST_FORBIDDEN_PREFIXES):
        raise RealTokenSmokeGateError("token_allowlist", "allowlist path is forbidden")
    if not _allowlist_allowed_for_relpath(raw_path):
        raise RealTokenSmokeGateError("token_allowlist", "allowlist path must be under docs or tests")
    return raw_path


def _parse_allowlist_date(value: str, *, field_name: str) -> date:
    if not value:
        raise RealTokenSmokeGateError("token_allowlist", f"allowlist {field_name} is required")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RealTokenSmokeGateError("token_allowlist", f"allowlist {field_name} must be YYYY-MM-DD") from exc


def _policy_for_relpath(rel_path: str) -> TokenLeakScanPolicy:
    normalized = rel_path.replace("\\", "/")
    if normalized == "README.md" or normalized.startswith("docs/"):
        return TRACKED_DOCS_TOKEN_LEAK_POLICY
    if normalized.startswith("tests/"):
        return TRACKED_TESTS_TOKEN_LEAK_POLICY
    if normalized.startswith("src/") or normalized.startswith("scripts/") or normalized.endswith(".py"):
        return SOURCE_CODE_TOKEN_LEAK_POLICY
    return STRICT_TOKEN_LEAK_POLICY


def _allowlist_allowed_for_relpath(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    return normalized.startswith("docs/") or normalized.startswith("tests/")


def _validate_code(code: str) -> str:
    text = str(code)
    if not CODE_RE.fullmatch(text):
        raise RealTokenSmokeGateError("stock_code", "stock code must be exactly six digits")
    return text


def _ensure_inside_resolved(path: Path, timestamp_dir: Path) -> None:
    resolved_path = path.resolve(strict=False)
    resolved_root = timestamp_dir.resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RealTokenSmokeGateError("artifact_path", "artifact path escapes timestamp directory") from exc


def _repo_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def _safe_relpath(path: Path, repo_root: Path) -> str:
    try:
        rel = path.resolve(strict=False).relative_to(repo_root.resolve(strict=False))
        return rel.as_posix()
    except ValueError:
        return "<outside_repo>"


def _sanitize_reason(reason: object, *, secret_refs: Iterable[str | None] | None = None) -> str:
    text = sanitize_text(reason, secrets=secret_refs)
    if scan_for_token_leaks(text, secret_refs=secret_refs).ok:
        return text
    return "secret-like data blocked"


def _safe_label(value: object) -> str:
    text = sanitize_text(value)
    if scan_for_token_leaks(text).ok and re.fullmatch(r"[A-Za-z0-9_.:-]+", text):
        return text
    return "sanitized"
