#!/usr/bin/env python3
"""
scripts/build.py — Pre-render dữ liệu data.json vào HTML tĩnh.

Mục đích: crawler/LLM không chạy JS vẫn đọc được content blog/FAQ.
JS hydration vẫn chạy bình thường (filter, accordion, v.v.).

Marker convention trong file HTML:
    <!-- BUILD:BLOG_GRID_START -->
    ...nội dung được tự sinh, đừng sửa tay...
    <!-- BUILD:BLOG_GRID_END -->

Chạy:
    python3 scripts/build.py
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data.json"


def load_data() -> dict:
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def render_blog_grid(blog: list[dict]) -> str:
    """Sinh các blog card cho blog.html."""
    parts: list[str] = []
    for index, post in enumerate(blog):
        mod = index % 3
        delay = "" if mod == 0 else (" reveal-delay-1" if mod == 1 else " reveal-delay-2")
        parts.append(
            f'      <a href="blog-detail.html?id={html.escape(str(post["id"]))}" '
            f'class="blog-card reveal{delay}" data-cat="{html.escape(post["cat"])}">\n'
            f'        <div class="blog-card-img">{html.escape(post["icon"])}</div>\n'
            f'        <div class="blog-card-body">\n'
            f'          <span class="blog-cat">{html.escape(post["catName"])}</span>\n'
            f'          <h3>{html.escape(post["title"])}</h3>\n'
            f'          <p>{html.escape(post["excerpt"])}</p>\n'
            f'          <div class="blog-meta"><span>📅 {html.escape(post["date"])}</span>'
            f'<span>⏱ {html.escape(post["read"])}</span></div>\n'
            f'        </div>\n'
            f'      </a>'
        )
    return "\n".join(parts)


def render_faq_groups(faq: list[dict]) -> str:
    """Sinh các nhóm FAQ cho faq.html."""
    parts: list[str] = []
    for group_index, group in enumerate(faq):
        gid = html.escape(group["id"])
        title = html.escape(group["title"])
        parts.append(f'      <div class="faq-group reveal" id="{gid}">')
        parts.append(f'        <div class="faq-group-title">{title}</div>')
        for item_idx, item in enumerate(group["items"]):
            is_open = " open" if (group_index == 0 and item_idx == 0) else ""
            q = html.escape(item["q"])
            # giữ nguyên HTML trong answer (có thể chứa <a>, <strong>)
            a = item["a"]
            parts.append(f'        <div class="faq-item{is_open}">')
            parts.append(
                f'          <div class="faq-question"><span>{q}</span>'
                f'<span class="faq-icon"><svg viewBox="0 0 14 14">'
                f'<path d="M7 0v14M0 7h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
                f'</svg></span></div>'
            )
            parts.append(f'          <div class="faq-answer"><p>{a}</p></div>')
            parts.append("        </div>")
        parts.append("      </div>")
    return "\n".join(parts)


def render_faq_jsonld(faq: list[dict]) -> str:
    """JSON-LD FAQPage tổng hợp toàn bộ Q&A."""
    questions = []
    for group in faq:
        for item in group["items"]:
            # text plain (strip HTML) cho schema
            plain_answer = re.sub(r"<[^>]+>", "", item["a"]).strip()
            questions.append(
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": plain_answer,
                    },
                }
            )
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": questions,
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def render_blog_itemlist_jsonld(blog: list[dict]) -> str:
    """JSON-LD ItemList cho blog.html."""
    items = []
    for i, post in enumerate(blog, start=1):
        items.append(
            {
                "@type": "ListItem",
                "position": i,
                "url": f"https://9speak.vn/blog-detail.html?id={post['id']}",
                "name": post["title"],
            }
        )
    schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": items,
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def inject(html_text: str, marker: str, content: str) -> str:
    """Thay khối giữa <!-- BUILD:{marker}_START --> và <!-- BUILD:{marker}_END -->."""
    pattern = re.compile(
        rf"(<!--\s*BUILD:{marker}_START\s*-->).*?(<!--\s*BUILD:{marker}_END\s*-->)",
        re.DOTALL,
    )
    if not pattern.search(html_text):
        raise RuntimeError(f"Không tìm thấy marker BUILD:{marker} trong HTML")
    replacement = f"\\1\n{content}\n      \\2"
    return pattern.sub(replacement, html_text)


def build_blog(data: dict) -> None:
    target = ROOT / "blog.html"
    text = target.read_text(encoding="utf-8")
    text = inject(text, "BLOG_GRID", render_blog_grid(data["blog"]))
    text = inject(text, "BLOG_JSONLD",
                  f'<script type="application/ld+json">\n{render_blog_itemlist_jsonld(data["blog"])}\n</script>')
    target.write_text(text, encoding="utf-8")
    print(f"✓ Built {target.name}")


def build_faq(data: dict) -> None:
    target = ROOT / "faq.html"
    text = target.read_text(encoding="utf-8")
    text = inject(text, "FAQ_GROUPS", render_faq_groups(data["faq"]))
    text = inject(text, "FAQ_JSONLD",
                  f'<script type="application/ld+json">\n{render_faq_jsonld(data["faq"])}\n</script>')
    target.write_text(text, encoding="utf-8")
    print(f"✓ Built {target.name}")


def main() -> int:
    data = load_data()
    build_blog(data)
    build_faq(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
