# AGENTS.md — Quy cách làm việc với AI trên repo 9speak landing

Tài liệu này áp dụng cho mọi agent (Claude, Cursor, Copilot, v.v.) khi tương tác với repo.
Mục tiêu: giữ chất lượng cao, không phá nội dung đang chạy, có thể audit từng thay đổi.

---

## 1. Nguyên tắc nội dung (BẮT BUỘC)

- **KHÔNG** được tự ý thêm, bớt, đổi nội dung văn bản hiển thị trên trang (heading, paragraph, label, button text, FAQ, blog, testimonial, pricing tier name, v.v.)
- **KHÔNG** được tự ý thêm/bớt section, card, item hiển thị
- **CHỈ ĐƯỢC** chỉnh:
  - Markup ẩn: `<meta>`, `<link rel="canonical">`, `<script type="application/ld+json">`
  - Attributes ẩn: `alt`, `title`, `aria-*`, `rel`, `loading`, `decoding`, `width/height`
  - Sửa lỗi cú pháp HTML/CSS/JS hiện có (typo, thẻ đóng sai, selector sai)
  - CSS responsive / breakpoint / tap target
  - Sửa `href` đang trỏ sai (vd `#` → `index.html`) — nhưng không đổi text hiển thị
  - JS: event tracking, dataLayer push, UTM injection, hydration
- Khi nghi ngờ chạm vào text hiển thị → **DỪNG, hỏi user trước**
- Nội dung trong `data.json` (FAQ, blog) là nguồn sự thật — không sửa khi không được yêu cầu

---

## 2. Quy trình branching

- **KHÔNG** commit trực tiếp vào `main`
- Mỗi nhóm thay đổi → 1 branch, đặt tên theo conventional:
  - `feat/<scope>-<desc>` — tính năng mới (vd. tracking, schema)
  - `fix/<scope>-<desc>` — sửa bug
  - `chore/<desc>` — config/docs
  - `perf/<scope>-<desc>` — tối ưu performance
  - `style/<scope>-<desc>` — CSS thuần
- Một branch chỉ làm một nhóm việc logic (không gộp tracking + fix bug + SEO vào cùng branch)
- Sau khi merge xong → xoá branch local

```bash
git checkout main && git pull
git checkout -b fix/index-html-typos
# ... làm việc ...
# verify (mục 4)
git add <specific files>
git commit -m "fix(index): xoá ký tự thừa và thẻ </div> hỏng"
git checkout main
git merge --no-ff fix/index-html-typos
git branch -d fix/index-html-typos
```

---

## 3. Commit message

Theo Conventional Commits (tiếng Việt):

```
<type>(<scope>): <mô tả ngắn>

[Body tuỳ chọn — giải thích "vì sao", không lặp "làm gì"]
```

- **Type**: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`
- **Scope**: `index`, `blog`, `faq`, `contact`, `privacy`, `seo`, `schema`, `tracking`, `mobile`, `links`, `build`
- Tiêu đề ≤72 ký tự, viết thường trừ tên riêng/file
- Co-author footer khi do AI tạo:
  ```
  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  ```

Ví dụ tốt:
- `fix(index): xoá ký tự S thừa ở section testimonials và sửa </diSSv>`
- `feat(seo): thêm canonical, OG, twitter card cho 6 trang`
- `feat(schema): thêm JSON-LD FAQPage cho index và faq`
- `perf(index): thay base64 logo footer bằng <img src>`

---

## 4. Verification trước khi merge (BẮT BUỘC)

Mỗi branch trước khi merge vào `main` phải pass **tất cả** các check sau:

### 4.1. HTML hợp lệ
```bash
# Nếu chưa có tidy: brew install tidy-html5
tidy -q -e -utf8 index.html blog.html blog-detail.html faq.html contact.html privacy.html
```
- Không có error (warning có thể chấp nhận, ghi lại trong commit body)

### 4.2. JSON hợp lệ
```bash
python3 -m json.tool data.json > /dev/null
```

### 4.3. JSON-LD parse được
Mọi block `<script type="application/ld+json">` phải `JSON.parse()` thành công:
```bash
python3 scripts/validate_jsonld.py   # script kèm theo repo (Phase 4)
```

### 4.4. Không thay đổi nội dung hiển thị
- So sánh số từ visible text giữa branch và main:
```bash
python3 scripts/count_visible_text.py main HEAD
```
- Output phải bằng 0 cho diff "text added/removed"

### 4.5. Dev server không lỗi console
```bash
python3 -m http.server 8000
# Mở: localhost:8000/index.html, blog.html, faq.html, contact.html, privacy.html, blog-detail.html?id=1
# Kiểm tra DevTools Console: 0 error, 0 warning lạ
```

### 4.6. (Nếu chỉnh CSS mobile) Screenshot 3 breakpoint
- 360px (mobile nhỏ)
- 768px (tablet)
- 1280px (desktop)

---

## 5. Merge

- Chỉ merge sau khi Phase 4 pass đủ
- Dùng `git merge --no-ff <branch>` để giữ commit graph rõ ràng
- **KHÔNG** dùng `--no-verify`, `--force`, `--amend` (trừ khi user yêu cầu rõ)
- Sau merge: xoá branch local

---

## 6. Khi gặp blocker

- KHÔNG bypass hook, KHÔNG force push
- KHÔNG xoá file/thư mục không hiểu (có thể là work-in-progress của user)
- Báo lại user + đề xuất hướng giải quyết

---

## 7. Stack & cấu trúc repo

- HTML/CSS/JS thuần, không framework
- `index.html` — landing chính (chứa CSS inline lớn)
- `blog.html`, `faq.html`, `blog-detail.html` — render động qua `fetch('data.json')`
- `contact.html`, `privacy.html` — tĩnh
- `shared.css` — design system dùng chung cho các trang phụ
- `data.json` — nguồn sự thật cho FAQ + blog
- `scripts/` — (Phase 4+) các script Python build/validate
- Không có build step bắt buộc cho production; nhưng có pre-render script tuỳ chọn cho SEO

---

## 8. Checklist nhanh cho mỗi PR

```
[ ] Đã checkout branch riêng, không commit lên main trực tiếp
[ ] Không đổi text hiển thị (verify script 4.4)
[ ] HTML tidy 0 error (4.1)
[ ] data.json valid (4.2)
[ ] JSON-LD valid (4.3)
[ ] Console không lỗi (4.5)
[ ] Commit message theo Conventional Commits
[ ] Đã merge --no-ff và xoá branch local
```
