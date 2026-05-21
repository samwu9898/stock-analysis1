# -*- coding: utf-8 -*-
"""Capture visual audit screenshots for an existing local HTML report.

This script is intentionally independent from the report renderer and pipeline.
It opens a local HTML file with Playwright Chromium, captures deterministic
desktop/mobile screenshots, and writes a manifest for later visual acceptance.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


TOOL_VERSION = "v1"
DEFAULT_DESKTOP_WIDTH = 1440
DEFAULT_DESKTOP_HEIGHT = 1000
DEFAULT_MOBILE_WIDTH = 390
DEFAULT_MOBILE_HEIGHT = 844
DEFAULT_WAIT_MS = 1000
DEFAULT_TIMEOUT_MS = 15000

SCREENSHOT_FILENAMES = {
    "desktop_first_screen": "desktop_first_screen.png",
    "mobile_first_screen": "mobile_first_screen.png",
    "full_page": "full_page.png",
}


@dataclass(frozen=True)
class Viewport:
    width: int
    height: int

    def as_dict(self) -> dict[str, int]:
        return {"width": self.width, "height": self.height}


@dataclass(frozen=True)
class OutputPaths:
    output_dir: Path
    desktop_first_screen: Path
    mobile_first_screen: Path
    full_page: Path
    manifest: Path
    notes: Path

    @property
    def screenshots(self) -> dict[str, Path]:
        return {
            "desktop_first_screen": self.desktop_first_screen,
            "mobile_first_screen": self.mobile_first_screen,
            "full_page": self.full_page,
        }


class VisualAuditError(RuntimeError):
    """A user-facing visual audit failure with stage context."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.message = message


def parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected boolean value, got: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture desktop, mobile, and full-page screenshots for a local HTML report."
    )
    parser.add_argument("--html", required=True, help="Path to the existing local HTML report.")
    parser.add_argument("--code", required=True, help="Stock code for metadata and default output naming.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for screenshots and manifest. Defaults to output/visual_audit/<code>.",
    )
    parser.add_argument("--desktop-width", type=int, default=DEFAULT_DESKTOP_WIDTH)
    parser.add_argument("--desktop-height", type=int, default=DEFAULT_DESKTOP_HEIGHT)
    parser.add_argument("--mobile-width", type=int, default=DEFAULT_MOBILE_WIDTH)
    parser.add_argument("--mobile-height", type=int, default=DEFAULT_MOBILE_HEIGHT)
    parser.add_argument("--wait-ms", type=int, default=DEFAULT_WAIT_MS)
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS)
    parser.add_argument("--block-external-network", type=parse_bool, default=True)
    parser.add_argument(
        "--notes",
        nargs="?",
        const="",
        default=None,
        help="Write visual_audit_notes.md. Optional value is appended as initial notes.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_positive_dimension("--desktop-width", args.desktop_width)
    validate_positive_dimension("--desktop-height", args.desktop_height)
    validate_positive_dimension("--mobile-width", args.mobile_width)
    validate_positive_dimension("--mobile-height", args.mobile_height)
    validate_non_negative("--wait-ms", args.wait_ms)
    validate_positive_dimension("--timeout-ms", args.timeout_ms)
    return args


def validate_positive_dimension(name: str, value: int) -> None:
    if value <= 0:
        raise argparse.ArgumentTypeError(f"{name} must be greater than 0.")


def validate_non_negative(name: str, value: int) -> None:
    if value < 0:
        raise argparse.ArgumentTypeError(f"{name} must be greater than or equal to 0.")


def resolve_path(path_text: str, cwd: Path | None = None) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = (cwd or Path.cwd()) / path
    return path.resolve()


def validate_html_path(path_text: str, cwd: Path | None = None) -> Path:
    path = resolve_path(path_text, cwd=cwd)
    if not path.exists():
        raise VisualAuditError("validate_html", f"HTML file does not exist: {path}")
    if not path.is_file():
        raise VisualAuditError("validate_html", f"HTML path is not a file: {path}")
    return path


def build_output_paths(code: str, output_dir: str | Path | None = None, cwd: Path | None = None) -> OutputPaths:
    if output_dir is None:
        base = (cwd or Path.cwd()) / "output" / "visual_audit" / code
    else:
        base = Path(output_dir)
        if not base.is_absolute():
            base = (cwd or Path.cwd()) / base
    base = base.resolve()
    return OutputPaths(
        output_dir=base,
        desktop_first_screen=base / SCREENSHOT_FILENAMES["desktop_first_screen"],
        mobile_first_screen=base / SCREENSHOT_FILENAMES["mobile_first_screen"],
        full_page=base / SCREENSHOT_FILENAMES["full_page"],
        manifest=base / "visual_audit_manifest.json",
        notes=base / "visual_audit_notes.md",
    )


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_manifest(
    *,
    html_path: Path,
    code: str,
    output_paths: OutputPaths,
    desktop_viewport: Viewport,
    mobile_viewport: Viewport,
    block_external_network: bool,
    success: bool,
    error: dict[str, str] | None = None,
    generated_at: str | None = None,
    blocked_requests: list[str] | None = None,
    page_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timestamp = generated_at or utc_timestamp()
    screenshot_paths = {key: str(path) for key, path in output_paths.screenshots.items()}
    errors = [error] if error else []
    return {
        "tool": "html_report_visual_audit",
        "tool_version": TOOL_VERSION,
        "version": TOOL_VERSION,
        "code": code,
        "html_path": str(html_path),
        "html_file_uri": html_path.as_uri(),
        "html_url": html_path.as_uri(),
        "output_dir": str(output_paths.output_dir),
        "generated_at": timestamp,
        "created_at": timestamp,
        "desktop_viewport": desktop_viewport.as_dict(),
        "mobile_viewport": mobile_viewport.as_dict(),
        "viewports": {
            "desktop": desktop_viewport.as_dict(),
            "mobile": mobile_viewport.as_dict(),
        },
        "screenshot_paths": screenshot_paths,
        "screenshots": {key: path.name for key, path in output_paths.screenshots.items()},
        "block_external_network": block_external_network,
        "network_policy": {
            "block_external_network": block_external_network,
            "blocked_request_count": len(blocked_requests or []),
            "blocked_requests": blocked_requests or [],
        },
        "success": success,
        "status": "success" if success else "failed",
        "error": error,
        "errors": errors,
        "page_metrics": page_metrics or {},
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def write_notes(path: Path, code: str, initial_notes: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    notes = [
        f"# HTML Report Visual Audit Notes - {code}",
        "",
        "## Screenshot Checklist",
        "",
        "- Desktop first screen reviewed:",
        "- Mobile first screen reviewed:",
        "- Full-page layout reviewed:",
        "- Horizontal overflow checked:",
        "- Broken layout or blank sections checked:",
        "- Content boundary checked:",
        "",
        "## Notes",
        "",
        initial_notes or "",
        "",
    ]
    path.write_text("\n".join(notes), encoding="utf-8")


def is_allowed_network_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme in {"file", "data", "blob", "about"}:
        return True
    if parsed.scheme not in {"http", "https"}:
        return True
    host = (parsed.hostname or "").lower()
    return host in {"localhost", "127.0.0.1", "::1"} or host.startswith("127.")


def install_network_blocker(context: Any, blocked_requests: list[str]) -> None:
    def handle_route(route: Any) -> None:
        request = route.request
        url = request.url
        if is_allowed_network_url(url):
            route.continue_()
            return
        blocked_requests.append(url)
        route.abort()

    context.route("**/*", handle_route)


def wait_for_page_ready(page: Any, timeout_ms: int, wait_ms: int) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        # External requests may be blocked or a static file may never become
        # perfectly idle. The required domcontentloaded wait already happened.
        pass
    if wait_ms:
        page.wait_for_timeout(wait_ms)


def collect_page_metrics(page: Any) -> dict[str, int]:
    metrics = page.evaluate(
        """() => ({
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
            scrollHeight: document.documentElement.scrollHeight,
            clientHeight: document.documentElement.clientHeight,
            bodyScrollWidth: document.body ? document.body.scrollWidth : 0,
            bodyClientWidth: document.body ? document.body.clientWidth : 0
        })"""
    )
    return {str(key): int(value) for key, value in metrics.items()}


def capture_screenshots(
    *,
    html_file_uri: str,
    output_paths: OutputPaths,
    desktop_viewport: Viewport,
    mobile_viewport: Viewport,
    wait_ms: int,
    timeout_ms: int,
    block_external_network: bool,
) -> tuple[list[str], dict[str, Any]]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise VisualAuditError(
            "import_playwright",
            "Python Playwright is not installed. Install it with: pip install playwright; "
            "python -m playwright install chromium",
        ) from exc

    blocked_requests: list[str] = []
    page_metrics: dict[str, Any] = {}

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                desktop_context = browser.new_context(
                    viewport=desktop_viewport.as_dict(),
                    device_scale_factor=1,
                )
                if block_external_network:
                    install_network_blocker(desktop_context, blocked_requests)
                desktop_page = desktop_context.new_page()
                desktop_page.set_default_timeout(timeout_ms)
                desktop_page.goto(html_file_uri, wait_until="domcontentloaded", timeout=timeout_ms)
                wait_for_page_ready(desktop_page, timeout_ms, wait_ms)
                desktop_page.screenshot(path=str(output_paths.desktop_first_screen), full_page=False, timeout=timeout_ms)
                page_metrics["desktop"] = collect_page_metrics(desktop_page)
                desktop_page.screenshot(path=str(output_paths.full_page), full_page=True, timeout=timeout_ms)
                page_metrics["full_page"] = collect_page_metrics(desktop_page)
                desktop_context.close()

                mobile_context = browser.new_context(
                    viewport=mobile_viewport.as_dict(),
                    device_scale_factor=1,
                    is_mobile=True,
                    has_touch=True,
                )
                if block_external_network:
                    install_network_blocker(mobile_context, blocked_requests)
                mobile_page = mobile_context.new_page()
                mobile_page.set_default_timeout(timeout_ms)
                mobile_page.goto(html_file_uri, wait_until="domcontentloaded", timeout=timeout_ms)
                wait_for_page_ready(mobile_page, timeout_ms, wait_ms)
                mobile_page.screenshot(path=str(output_paths.mobile_first_screen), full_page=False, timeout=timeout_ms)
                page_metrics["mobile"] = collect_page_metrics(mobile_page)
                mobile_context.close()
            finally:
                browser.close()
    except PlaywrightTimeoutError as exc:
        raise VisualAuditError("capture", f"Playwright timed out after {timeout_ms} ms: {exc}") from exc
    except Exception as exc:
        detail = str(exc)
        if "Executable doesn't exist" in detail or "BrowserType.launch" in detail:
            detail = (
                f"{detail}\nChromium may not be installed. Run: "
                "python -m playwright install chromium"
            )
        raise VisualAuditError("capture", detail) from exc

    return blocked_requests, page_metrics


def run_visual_audit(args: argparse.Namespace) -> int:
    output_paths = build_output_paths(args.code, args.output_dir)
    output_paths.output_dir.mkdir(parents=True, exist_ok=True)
    desktop_viewport = Viewport(args.desktop_width, args.desktop_height)
    mobile_viewport = Viewport(args.mobile_width, args.mobile_height)
    html_path = resolve_path(args.html)

    try:
        html_path = validate_html_path(args.html)
        blocked_requests, page_metrics = capture_screenshots(
            html_file_uri=html_path.as_uri(),
            output_paths=output_paths,
            desktop_viewport=desktop_viewport,
            mobile_viewport=mobile_viewport,
            wait_ms=args.wait_ms,
            timeout_ms=args.timeout_ms,
            block_external_network=args.block_external_network,
        )
        manifest = build_manifest(
            html_path=html_path,
            code=args.code,
            output_paths=output_paths,
            desktop_viewport=desktop_viewport,
            mobile_viewport=mobile_viewport,
            block_external_network=args.block_external_network,
            success=True,
            blocked_requests=blocked_requests,
            page_metrics=page_metrics,
        )
        write_manifest(output_paths.manifest, manifest)
        if args.notes is not None:
            write_notes(output_paths.notes, args.code, args.notes)
        print(f"Visual audit screenshots written to: {output_paths.output_dir}")
        print(f"Manifest: {output_paths.manifest}")
        return 0
    except VisualAuditError as exc:
        error = {"stage": exc.stage, "message": exc.message}
        manifest = build_manifest(
            html_path=html_path,
            code=args.code,
            output_paths=output_paths,
            desktop_viewport=desktop_viewport,
            mobile_viewport=mobile_viewport,
            block_external_network=args.block_external_network,
            success=False,
            error=error,
        )
        write_manifest(output_paths.manifest, manifest)
        print(f"Visual audit failed at {exc.stage}: {exc.message}", file=sys.stderr)
        print(f"Manifest: {output_paths.manifest}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive CLI diagnostics
        error = {"stage": "unexpected", "message": f"{exc}\n{traceback.format_exc()}"}
        manifest = build_manifest(
            html_path=html_path,
            code=args.code,
            output_paths=output_paths,
            desktop_viewport=desktop_viewport,
            mobile_viewport=mobile_viewport,
            block_external_network=args.block_external_network,
            success=False,
            error=error,
        )
        write_manifest(output_paths.manifest, manifest)
        print(f"Visual audit failed unexpectedly: {exc}", file=sys.stderr)
        print(f"Manifest: {output_paths.manifest}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except argparse.ArgumentTypeError as exc:
        print(f"Invalid argument: {exc}", file=sys.stderr)
        return 2
    return run_visual_audit(args)


if __name__ == "__main__":
    raise SystemExit(main())
