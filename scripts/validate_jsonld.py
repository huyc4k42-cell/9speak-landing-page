#!/usr/bin/env python3
"""
scripts/validate_jsonld.py — Kiểm tra mọi block <script type="application/ld+json">
trong các file HTML parse được bằng JSON.

Chạy:
    python3 scripts/validate_jsonld.py
Exit code 0 nếu mọi block hợp lệ, 1 nếu có lỗi.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_FILES = sorted(ROOT.glob("*.html"))

JSONLD_PATTERN = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def main() -> int:
    errors = 0
    total = 0
    for path in HTML_FILES:
        content = path.read_text(encoding="utf-8")
        matches = JSONLD_PATTERN.findall(content)
        for i, raw in enumerate(matches, start=1):
            total += 1
            try:
                json.loads(raw.strip())
            except json.JSONDecodeError as e:
                errors += 1
                print(f"✗ {path.name} block #{i}: {e}", file=sys.stderr)
        if matches:
            print(f"✓ {path.name}: {len(matches)} block JSON-LD hợp lệ")
    print(f"\nTổng: {total} block, {errors} lỗi")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
