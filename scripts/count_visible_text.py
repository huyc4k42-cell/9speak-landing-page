#!/usr/bin/env python3
"""
scripts/count_visible_text.py — So sánh "visible text" của HTML giữa 2 git ref.

Mục đích: đảm bảo PR không đổi nội dung hiển thị (chỉ đổi markup/meta).

Cách hoạt động:
- Với mỗi *.html, strip <script>, <style>, comment, tag
- Đếm từ (split theo whitespace)
- So sánh tổng số từ giữa ref A và ref B

Chạy:
    python3 scripts/count_visible_text.py <ref_a> <ref_b>
    python3 scripts/count_visible_text.py main HEAD
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TAG_PATTERN = re.compile(r"<[^>]+>")
SCRIPT_STYLE_PATTERN = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)


def visible_text(html: str) -> str:
    html = SCRIPT_STYLE_PATTERN.sub(" ", html)
    html = COMMENT_PATTERN.sub(" ", html)
    html = TAG_PATTERN.sub(" ", html)
    return re.sub(r"\s+", " ", html).strip()


def word_count(text: str) -> int:
    return len([w for w in text.split() if w])


def file_at_ref(ref: str, path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    ref_a, ref_b = sys.argv[1], sys.argv[2]

    html_files = sorted(p.name for p in ROOT.glob("*.html"))
    total_diff = 0
    for name in html_files:
        a = file_at_ref(ref_a, name)
        b = file_at_ref(ref_b, name)
        if a is None and b is None:
            continue
        wa = word_count(visible_text(a)) if a else 0
        wb = word_count(visible_text(b)) if b else 0
        delta = wb - wa
        marker = "  OK" if delta == 0 else f"  Δ={delta:+d}"
        print(f"{name:24s} {wa:5d} → {wb:5d}{marker}")
        total_diff += abs(delta)

    print(f"\nTổng chênh lệch từ tuyệt đối: {total_diff}")
    return 0 if total_diff == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
