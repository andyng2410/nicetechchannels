---
name: x-sources
description: Trích xuất X/Twitter thread, đọc post chính bằng bird read --json-full để lấy ảnh X Article/media nhúng, và tải/capture media từ X bằng bird, yt-dlp, browser/cookies để chuẩn bị source cho slide. Dùng cho X/Twitter URL, thread, X Article, tweet screenshot, X video hoặc bài X cần dựng script/deck; sau khi lấy X-specific data, dùng source-assets để hoàn tất source folder và visual asset inventory.
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

Dùng skill này cho phần đặc thù của X/Twitter. Với checklist source chung như `source/source.md`, avatar/logo/ảnh/video inventory, media handling và gate trước script/DOM, dùng thêm skill `source-assets`.

## Công cụ

- `bird`: trích xuất text/thread từ X; **`bird read --json-full` bắt buộc** để lấy media nhúng (X Article, ảnh inline) mà `bird thread` text thường bỏ sót.
- `yt-dlp`: tải video X hoặc nguồn media được hỗ trợ. Nếu source có video, luôn thử `yt-dlp` trước; chỉ fallback khi `yt-dlp` fail hoặc nguồn không hỗ trợ.
- `ffmpeg`: normalize/remux video khi cần.
- Browser/screenshot/curl: capture ảnh, avatar, logo, thumbnail hoặc poster khi không có URL tải trực tiếp.

Kiểm tra:

```bash
command -v bird
command -v yt-dlp
command -v ffmpeg
```

Nếu thiếu `bird`, cài theo hướng dẫn hiện tại tại:

```text
https://bird.fast/
```

Nếu thiếu `yt-dlp`, ưu tiên Homebrew trên macOS:

```bash
brew install yt-dlp
```

Hoặc:

```bash
python3 -m pip install --user -U yt-dlp
```

Không tự chế workaround nếu môi trường thiếu quyền, thiếu package manager hoặc không có network; báo blocker rõ.

## Bootstrap

- macOS: chạy `./install.sh`; script kiểm tra/cài `yt-dlp`, `ffmpeg`, rồi hỏi có muốn bật hỗ trợ X trước khi cài/cấu hình `bird`.
- Windows: chạy `.\install.cmd`; nếu bị chặn, dùng `powershell -c "gc .\install.ps1 -Raw | iex"`.
- Khi cấu hình `bird`, setup có thể yêu cầu user copy `auth_token` và `ct0` từ x.com. Đây là cookie đăng nhập nhạy cảm; khuyên user dùng tài khoản X phụ.

## Quy trình X

1. Tạo `slide/<project>/source/`.
2. Lưu raw thread **và** metadata post chính:

```bash
mkdir -p "slide/<project>/source"
URL="https://x.com/user/status/id"

bird thread "$URL" > "slide/<project>/source/thread.txt"
bird read "$URL" --json > "slide/<project>/source/tweet.json"
bird read "$URL" --json-full > "slide/<project>/source/tweet-full.json"
```

3. Đọc `source/thread.txt` + `tweet.json`; trích link, repo, blog, paper, model card, benchmark từ **chính tác giả post/thread**.
4. Ghi mỗi URL quan trọng do tác giả chia sẻ vào `source/links.txt`.
5. **Tải media post chính** từ `tweet-full.json` (xem mục dưới) — không chỉ dựa vào `bird thread`.
6. Tải/capture media từ link tác giả chia sẻ (HTML artifact, blog, demo page…); screenshot/curl nếu không có file ảnh trực tiếp.
7. Thêm author avatar, org/product logo, thumbnail/poster nếu cần.
8. Sau khi xong phần X-specific, dùng checklist của `source-assets` để hoàn tất `source/source.md` và visual asset inventory.

Không quyết định hook/script/DOM trước khi đã đọc thread, **mở/kiểm tra ảnh post chính**, xem media link ngoài, và biết asset nào dùng được.

## Đọc post chính: bird read --json-full

**Pitfall quan trọng:** `bird thread` (text) chỉ hiện `🖼️` khi tweet/reply **có media attachment trực tiếp**. Với **X Article** (long-form) hoặc post có ảnh minh họa nhúng trong article body:

- `bird thread` thường **không liệt kê** các ảnh đó.
- `bird read --json` có thể trả `media: none` dù bài vẫn có nhiều illustration.
- `bird read --json-full` mới có URL đầy đủ trong raw API (`pbs.twimg.com/media/...`, `pbs.twimg.com/profile_images/...`).

Luôn chạy cả ba lệnh ở bước 2. Coi `tweet-full.json` là nguồn truth cho media post chính.

### Trích URL media từ tweet-full.json

```bash
python3 - <<'PY'
import json, re
from pathlib import Path

p = Path("slide/<project>/source/tweet-full.json")
raw = p.read_text()
data = json.loads(raw)

# Metadata nhanh
article = data.get("article")
if isinstance(article, dict):
    print("article.title:", article.get("title"))
    print("article.preview:", (article.get("previewText") or "")[:120], "...")

# Media URLs trong raw response
urls = sorted(set(re.findall(r"https://pbs\.twimg\.com/[^\"\\]+", raw)))
for u in urls:
    print(u)
PY
```

Phân loại URL:

| Pattern | Ý nghĩa | Dùng cho deck? |
| --- | --- | --- |
| `pbs.twimg.com/media/*.jpg` (hoặc png/webp) | Ảnh post/article/video thumb | **Có** — tải local, đặt tên theo thứ tự |
| `pbs.twimg.com/profile_images/*` | Avatar tác giả | Có — `author-avatar.jpg` |
| `pbs.twimg.com/profile_banners/*` | Banner profile | Thường bỏ qua trừ khi cần |
| `🖼️` trong `thread.txt` từ **reply người khác** | Media comment | **Không** — trừ khi user yêu cầu |

### Tải ảnh post chính

```bash
mkdir -p "slide/<project>/source/article-media"

# Ví dụ: tải từng URL media post (bỏ profile_banners nếu không cần)
curl -fsSL "https://pbs.twimg.com/media/EXAMPLE.jpg" \
  -o "slide/<project>/source/article-media/x-image-01.jpg"

# Đặt alias semantic sau khi mở xem nội dung:
# article-map-vs-territory.jpg, article-four-quadrants.jpg, ...
```

Quy tắc đặt tên:

- Giữ file gốc trong `article-media/` hoặc `x-image-01.jpg`, `x-image-02.jpg` theo thứ tự xuất hiện trong JSON.
- Thêm bản copy/alias semantic nếu nội dung rõ (`article-cover.jpg`, `article-diagram-01.jpg`).
- Ghi **cả URL gốc và mô tả nội dung** vào `source/source.md` sau khi mở từng ảnh (`file <path>` hoặc preview).

### Video / ảnh attachment trực tiếp trên tweet

Nếu post có video hoặc ảnh đính kèm (không phải article inline):

1. Kiểm tra `tweet.json` / `tweet-full.json` và dòng `🖼️` trong thread **của chính tác giả post gốc**.
2. Tải video bằng `yt-dlp` (mục dưới).
3. Tải ảnh bằng `curl` từ URL `pbs.twimg.com/media/...`.

### Link ngoài X trong post

Post thường link tới HTML artifact, blog, demo gallery. `bird` chỉ cho URL — agent phải:

1. Mở/tải trang link (curl, browser, Playwright screenshot).
2. Nếu trang là HTML artifact không có file `.jpg` riêng → **screenshot từng demo/page** cần dùng.
3. Ghi URL demo vào `links.txt`; screenshot vào `source/demo-*.png` hoặc `screenshot-*.png`.

## Tải video X

Ưu tiên tải bằng `yt-dlp` đã cài sẵn:

```bash
yt-dlp -f "bv*+ba/b" --merge-output-format mp4 \
  -o "slide/<project>/source/x-%(id)s.%(ext)s" \
  "https://x.com/user/status/id"
```

Nếu X cần cookie trình duyệt và user đã đồng ý dùng cookie local:

```bash
yt-dlp --cookies-from-browser chrome \
  -f "bv*+ba/b" --merge-output-format mp4 \
  -o "slide/<project>/source/x-%(id)s.%(ext)s" \
  "https://x.com/user/status/id"
```

Nếu `yt-dlp` vẫn fail, ghi lỗi/nguyên nhân vào `source/source.md` hoặc note tạm trong `links.txt`, rồi mới thử browser capture, media URL trực tiếp, hoặc fallback khác.

Normalize video nếu cần embed ổn trong slide:

```bash
ffmpeg -i "input-file" -c:v libx264 -crf 23 -preset medium \
  -c:a aac -b:a 128k -movflags +faststart "slide/<project>/source/demo.mp4" -y
```

## X media notes

- **`bird thread` alone is not enough.** Luôn kết hợp `bird read --json-full` để không bỏ sót ảnh X Article.
- Chỉ lấy media từ tác giả thread/post và media từ link mà tác giả chia sẻ. Không tải/capture media từ bình luận, reply, quote hoặc người dùng khác để đưa vào visual, trừ khi user yêu cầu rõ — kể cả khi `bird thread` hiện `🖼️` ở reply.
- Reply/comment của người dùng khác chỉ dùng để nắm sentiment, disagreement hoặc câu hỏi lặp lại; ghi nhãn là bình luận/opinion nếu đưa vào `source/source.md`.
- Nếu thread có nhiều video/ảnh từ tác giả, tải hoặc capture đủ asset cần cho deck, không chỉ asset đầu tiên. Giữ đúng thứ tự xuất hiện bằng tên như `x-video-01`, `x-video-02`, hoặc ghi order rõ trong `source/source.md`.
- Nếu tweet nhắc thương hiệu/sản phẩm/tổ chức, lưu logo/mark chính thức hoặc avatar/profile phù hợp để dùng làm visual.
- Không hotlink X media trong slide HTML; dùng file local trong `source/` hoặc `assets/`.
- Không tải private/paywalled/login-only content nếu user chưa cho phép rõ.

Nếu skill được gọi kèm argument, coi `$ARGUMENTS` là source URL hoặc task:

```text
$ARGUMENTS
```
