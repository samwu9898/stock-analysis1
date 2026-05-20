#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check important project files for UTF-8 and obvious garbled Chinese text.

This script is intentionally read-only. It does not modify source files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TARGET_FILES = [
    "README.md",
    "SKILL.md",
    "stock_full_report.py",
    "src/data_fetcher.py",
    "src/analyzer.py",
    "src/html_renderer.py",
]

GARBLED_PATTERNS = [
    re.compile(r"[ÃÂ][\x80-\xbfA-Za-z0-9]{1,}"),
    re.compile(r"(?:锛|绔|涓|鑲|鍒|鏁|鐢|馃|鈥|鈫|瀹|勬|傛|湡|棰|煡|姣|庢|忚|攢|搳|敤){2,}"),
    re.compile(r"(?:\ufffd){1,}"),
]


def find_suspicious_text(text: str) -> list[str]:
    samples: list[str] = []
    for pattern in GARBLED_PATTERNS:
        for match in pattern.finditer(text):
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 40)
            sample = text[start:end].replace("\r", "\\r").replace("\n", "\\n")
            samples.append(sample)
            if len(samples) >= 5:
                return samples
    return samples


def inspect_file(relative_path: str) -> dict:
    path = PROJECT_ROOT / relative_path
    result = {
        "file_path": relative_path,
        "can_decode_utf8": False,
        "suspicious_garbled_text_count": 0,
        "sample_suspicious_text": [],
    }

    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        result["error"] = "file_not_found"
        return result

    try:
        text = raw.decode("utf-8")
        result["can_decode_utf8"] = True
    except UnicodeDecodeError as exc:
        result["decode_error"] = str(exc)
        text = raw.decode("utf-8", errors="replace")

    suspicious_samples = find_suspicious_text(text)
    suspicious_count = 0
    for pattern in GARBLED_PATTERNS:
        suspicious_count += len(pattern.findall(text))

    result["suspicious_garbled_text_count"] = suspicious_count
    result["sample_suspicious_text"] = suspicious_samples[:3]
    return result


def main() -> int:
    results = [inspect_file(path) for path in TARGET_FILES]
    print(json.dumps(results, ensure_ascii=False, indent=2))

    has_issues = any(
        (not item["can_decode_utf8"]) or item["suspicious_garbled_text_count"] > 0
        for item in results
    )
    return 1 if has_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
