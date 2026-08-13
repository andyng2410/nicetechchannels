---
name: source-assets
description: Thu thập và chuẩn hóa source cho slide từ nguồn ngoài như website, GitHub, Facebook, YouTube, blog, paper, model card, repo, landing page hoặc bài viết. Dùng khi Codex cần lưu text/facts cùng visual assets như ảnh, logo/avatar, thumbnail/poster, video, screenshot và viết source/source.md trước khi dựng script hoặc slide DOM.
---

Dùng skill này trước khi viết `script-90s.txt` hoặc sửa DOM/CSS cho deck lấy từ nguồn ngoài. Mục tiêu là làm `slide/<project>/source/` đủ giàu để dựng visual, không chỉ đủ text để viết script.

## Quy tắc chính

- Tạo `slide/<project>/source/` trước.
- Lưu text/facts và visual assets local: ảnh trong bài, logo/avatar tác giả hoặc tổ chức, thumbnail/poster, video, screenshot, chart, repo/social proof.
- Nếu nguồn có video, thử tải bằng `yt-dlp` đã có sẵn trước. Chỉ dùng browser/curl/screenshot/workaround khi `yt-dlp` fail, nguồn không được hỗ trợ, hoặc user yêu cầu cách khác.
- Nếu nguồn có nhiều video/ảnh, lưu và đặt tên theo đúng thứ tự xuất hiện trong thread/bài viết/source (`video-01`, `video-02`, `image-01`...), vì slide sẽ chèn theo order này.
- Không hotlink media trong slide. Slide HTML phải dùng file local trong `source/` hoặc `assets/`.
- Giữ URL gốc trong `links.txt` để trace lại nguồn.
- Viết `source/source.md` trước script/DOM; file này là inventory để agent dựng visual.
- Nếu asset cần cho visual nhưng chưa tải/capture được, ghi blocker rõ trong `source/source.md`.
- Kiểm tra file type thật của logo/media trước khi inventory (`file <path>` hoặc mở xem): file `.svg` ruột ICO/binary sẽ vỡ ảnh trong DOM, logo fill đen sẽ chìm trên nền tối. Lỗi này chỉ lộ ở screenshot nên phải bắt từ bước source.
- Claim về tiền/quota/promo (pricing, usage limit, cửa sổ miễn phí…) phải đọc trang gốc help center/blog — không chỉ tweet — và ghi cơ chế vào `source.md`: ai được dùng, cái gì vẫn trừ quota, trả thêm khi nào, sau deadline thì sao.

## Cấu trúc source

```text
slide/<project>/source/
  source.md
  links.txt
  article.txt / article.html / transcript.txt
  author-avatar.<ext>
  org-logo.<ext>
  image-01.<ext>
  screenshot-01.<ext>
  poster-01.<ext>
  video-01.<ext>
```

Có thể dùng `source/media/` hoặc `source/screenshots/` nếu nhiều asset, nhưng `source/source.md` phải ghi đường dẫn local cụ thể.

## Theo loại nguồn

- Website/blog/article: lưu URL, title, tác giả/ngày nếu có, text chính (`article.txt` hoặc `article.html`), ảnh trong bài, logo site/tổ chức, social preview/OG image nếu hữu ích.
- GitHub/repo: lưu README hoặc docs chính, repo URL, stars/license nếu cần, owner/org avatar/logo, screenshots/demo GIF/video, release/tag hoặc benchmark artifact liên quan.
- YouTube/video: lưu video hoặc đoạn cần dùng, thumbnail/poster, transcript nếu có hoặc tự transcribe khi cần, channel avatar/logo nếu phù hợp.
- Facebook/Reel/social video: lưu video local, poster/thumbnail, caption/text, author/page avatar/logo nếu dùng làm source proof.
- Paper/model card/benchmark: lưu PDF/HTML/text, chart/table/screenshot quan trọng, logo tổ chức/model, link dataset/leaderboard nếu có.
- Landing page/product site: lưu hero screenshot, logo/icon, demo video, product screenshot, pricing/feature proof nếu cần cho câu chuyện.
- **X/Twitter:** dùng skill `x-sources` trước. Luôn chạy `bird thread` + `bird read --json-full`; tải ảnh post chính từ `pbs.twimg.com/media/` trong `tweet-full.json` (X Article thường không lộ qua `bird thread` text). Reply media = bỏ qua trừ khi user yêu cầu.

## `links.txt`

Ghi mỗi URL một dòng. Dùng comment ngắn nếu cần:

```text
https://example.com/article
https://github.com/org/repo
https://www.youtube.com/watch?v=...
# logo source: https://example.com/brand
```

## `source/source.md`

Tối thiểu phải có:

```markdown
# Source analysis

## Nguồn gốc
- URL:
- Tác giả/tổ chức:
- Ngày:

## Facts từ nguồn
- ...

## Bình luận/góc nhìn
- ...

## Visual assets
| Local path | URL gốc | Nội dung | Gợi ý dùng trong slide |
| --- | --- | --- | --- |
| source/author-avatar.png | ... | Avatar tác giả | Source proof / hook |
| source/org-logo.svg | ... | Logo tổ chức/sản phẩm | Hero / brand lockup |
| source/video-01.mp4 | ... | Demo video | Demo slide |

Khi inventory, đánh dấu asset **khó đọc trên phone** (diagram dày, banner chữ nhỏ…) ở cột gợi ý — các asset đó **không** đưa vào `visual-plan.md`; lúc lập plan dùng custom scene thay thế.

## Media notes
- Tóm tắt nội dung ảnh/video, timestamp đáng chú ý, số liệu/quote nhìn thấy được.

## Blockers
- Asset chưa lấy được, lý do, và fallback nếu cần.
```

Phân biệt rõ fact từ nguồn với bình luận, sentiment cộng đồng, hoặc nhận định của mình.

## Media handling

- Giữ order source khi đặt tên và inventory media. `source/source.md` phải nói rõ `video-01` là video nào trong thread/bài viết, tiếp theo là `video-02`, v.v.
- Với video từ YouTube/Facebook/X/website hoặc nguồn được hỗ trợ, ưu tiên:

```bash
yt-dlp -f "bv*+ba/b" --merge-output-format mp4 \
  -o "slide/<project>/source/video-%(id)s.%(ext)s" \
  "<video-url>"
```

- Nếu `yt-dlp` fail, ghi lỗi/nguyên nhân ngắn vào `source/source.md`, rồi mới thử browser cookies, download URL trực tiếp, screen capture, hoặc cách fallback phù hợp.
- Ảnh/video đưa vào slide phải giữ trọn frame, đúng tỷ lệ, không méo. Dùng `object-fit: contain` khi embed.
- Không crop để lấp đầy slide trừ khi user yêu cầu rõ.
- Nếu media giữ đúng tỷ lệ nên còn trống safezone, ghi gợi ý visual hỗ trợ vào `source/source.md`: logo/avatar, source label, thứ tự, metric, keyword, caption ngắn hoặc proof chip.
- Khi embed video demo/source vào slide, mặc định tắt âm (`muted`) để không đè voiceover và BGM deck. Chỉ giữ audio gốc khi âm thanh là nội dung chính và user duyệt rõ; nếu bật audio gốc thì tránh để BGM đè.
- Nếu demo cần “thở”, kéo dài script/timing thay vì chỉ nhồi video vào slide.

## Gate trước script/DOM

Chỉ chuyển sang script hoặc DOM khi đã có:

- `source/links.txt`
- `source/source.md`
- text/facts đủ để viết script
- visual assets local đủ để dựng ít nhất hero/source proof/demo/visual chính
- blockers được ghi rõ nếu thiếu asset quan trọng
