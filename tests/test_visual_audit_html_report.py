# -*- coding: utf-8 -*-

import json
from pathlib import Path

from scripts.visual_audit_html_report import (
    DEFAULT_DESKTOP_HEIGHT,
    DEFAULT_DESKTOP_WIDTH,
    DEFAULT_MOBILE_HEIGHT,
    DEFAULT_MOBILE_WIDTH,
    DEFAULT_TIMEOUT_MS,
    DEFAULT_WAIT_MS,
    Viewport,
    build_manifest,
    build_output_paths,
    main,
    parse_args,
    validate_html_path,
    write_manifest,
)


def test_cli_argument_parsing_defaults():
    args = parse_args(["--html", "report.html", "--code", "002050"])

    assert args.html == "report.html"
    assert args.code == "002050"
    assert args.output_dir is None
    assert args.desktop_width == DEFAULT_DESKTOP_WIDTH
    assert args.desktop_height == DEFAULT_DESKTOP_HEIGHT
    assert args.mobile_width == DEFAULT_MOBILE_WIDTH
    assert args.mobile_height == DEFAULT_MOBILE_HEIGHT
    assert args.wait_ms == DEFAULT_WAIT_MS
    assert args.timeout_ms == DEFAULT_TIMEOUT_MS
    assert args.block_external_network is True
    assert args.notes is None


def test_cli_argument_parsing_overrides():
    args = parse_args(
        [
            "--html",
            "report.html",
            "--code",
            "002050",
            "--output-dir",
            "out",
            "--desktop-width",
            "1200",
            "--desktop-height",
            "900",
            "--mobile-width",
            "375",
            "--mobile-height",
            "812",
            "--wait-ms",
            "10",
            "--timeout-ms",
            "2000",
            "--block-external-network",
            "false",
            "--notes",
            "initial note",
        ]
    )

    assert args.output_dir == "out"
    assert args.desktop_width == 1200
    assert args.desktop_height == 900
    assert args.mobile_width == 375
    assert args.mobile_height == 812
    assert args.wait_ms == 10
    assert args.timeout_ms == 2000
    assert args.block_external_network is False
    assert args.notes == "initial note"


def test_output_path_construction_defaults_to_code_directory(tmp_path):
    paths = build_output_paths("002050", cwd=tmp_path)

    assert paths.output_dir == tmp_path / "output" / "visual_audit" / "002050"
    assert paths.desktop_first_screen == paths.output_dir / "desktop_first_screen.png"
    assert paths.mobile_first_screen == paths.output_dir / "mobile_first_screen.png"
    assert paths.full_page == paths.output_dir / "full_page.png"
    assert paths.manifest == paths.output_dir / "visual_audit_manifest.json"
    assert paths.notes == paths.output_dir / "visual_audit_notes.md"


def test_output_path_construction_uses_explicit_directory(tmp_path):
    paths = build_output_paths("002050", tmp_path / "custom")

    assert paths.output_dir == tmp_path / "custom"
    assert paths.screenshots["desktop_first_screen"].name == "desktop_first_screen.png"


def test_manifest_write_contains_required_fields(tmp_path):
    html_path = tmp_path / "report.html"
    html_path.write_text("<!doctype html><html></html>", encoding="utf-8")
    paths = build_output_paths("002050", tmp_path / "audit")
    manifest = build_manifest(
        html_path=html_path,
        code="002050",
        output_paths=paths,
        desktop_viewport=Viewport(1440, 1000),
        mobile_viewport=Viewport(390, 844),
        block_external_network=True,
        success=True,
        generated_at="2026-05-21T00:00:00+00:00",
        blocked_requests=["https://example.invalid/a.js"],
        page_metrics={"desktop": {"clientWidth": 1440}},
    )

    write_manifest(paths.manifest, manifest)
    payload = json.loads(paths.manifest.read_text(encoding="utf-8"))

    assert payload["html_path"] == str(html_path)
    assert payload["html_file_uri"] == html_path.as_uri()
    assert payload["code"] == "002050"
    assert payload["generated_at"] == "2026-05-21T00:00:00+00:00"
    assert payload["desktop_viewport"] == {"width": 1440, "height": 1000}
    assert payload["mobile_viewport"] == {"width": 390, "height": 844}
    assert payload["screenshot_paths"]["full_page"].endswith("full_page.png")
    assert payload["block_external_network"] is True
    assert payload["success"] is True
    assert payload["error"] is None
    assert payload["tool_version"] == "v1"
    assert payload["network_policy"]["blocked_request_count"] == 1


def test_validate_html_path_missing_reports_clear_error(tmp_path):
    missing = tmp_path / "missing.html"

    try:
        validate_html_path(str(missing))
    except Exception as exc:
        message = str(exc)
    else:
        message = ""

    assert "HTML file does not exist" in message
    assert str(missing) in message


def test_missing_html_cli_writes_failed_manifest(tmp_path, capsys):
    missing = tmp_path / "missing.html"
    output_dir = tmp_path / "audit"

    exit_code = main(["--html", str(missing), "--code", "002050", "--output-dir", str(output_dir)])
    captured = capsys.readouterr()
    manifest_path = output_dir / "visual_audit_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert "HTML file does not exist" in captured.err
    assert payload["success"] is False
    assert payload["status"] == "failed"
    assert payload["error"]["stage"] == "validate_html"
    assert "HTML file does not exist" in payload["error"]["message"]


def test_html_path_validation_accepts_existing_file(tmp_path):
    html_path = tmp_path / "report.html"
    html_path.write_text("<html></html>", encoding="utf-8")

    assert validate_html_path(str(html_path)) == Path(html_path).resolve()
