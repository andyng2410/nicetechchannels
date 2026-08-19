# Changelog

## NiceTechChannels Template 3 — 83.v5.87

### Added

- Thêm mục **Tạo slide mới từ link** trên dashboard: dán link nguồn + chọn style script (Auto/5 style/3 blend), hệ thống tự chạy `codex exec` (Codex CLI, đăng nhập subscription) theo Link Autopilot — thu source, viết script, dựng slide, validate, chụp QA vào `slide/<project>/qa/` rồi dừng; render vẫn thao tác tay. Cấu hình qua `config/agent.json` (mẫu: `config/agent.example.json`).
- Thêm **wizard duyệt 2 bước** cho deck builder tại trang riêng **`/create`** (nút "＋ Tạo slide" trên header dashboard): bước 1 codex thu source + viết 5 bản script theo 5 style, user chọn/sửa từng dòng trên UI rồi chốt; bước 2 build deck với script nguyên văn, duyệt ảnh QA với nút "Yêu cầu sửa" (codex chạy vòng sửa) và "Duyệt deck". Giai đoạn nháp chỉ ghi `slide/<project>/source/` nên project chưa hiện trong danh sách render; wizard dở dang resume được sau khi tải lại trang. Xong wizard thì bấm "Mở màn hình render" để quay về bộ máy render.
- Thêm `deck_host_runner.py`: cầu nối để web UI trong Docker gọi được Codex trên host qua file queue `slide/.deck-runner/`; codex build deck trên host, validate/capture chạy bằng `docker exec` vào container.
- Thêm **cost tracking per slide**: mọi hoạt động quanh deck tự ghi vào `slide/<project>/cost-ledger.jsonl` — token từng lần `codex exec` (drafts/build/revise, parse từ log + rollout `~/.codex/sessions/`), ký tự ElevenLabs/Edge bill thật (cache hit ghi $0), thời gian render, và cả sự kiện xoá `output/` làm mất audio trả phí. Xem báo cáo per-slide (TTS theo ký tự từng dòng, render theo duration, Codex chia đều — revise tính đúng slide được nhắc trong yêu cầu sửa) bằng `python3 cost_report.py slide/<project>`, API `GET /api/costs?project=`, hoặc bảng chi phí trên `/create` sau khi build. Giá cấu hình qua `config/pricing.json` (mẫu: `config/pricing.example.json`); ledger chỉ lưu token/chars/giây thô nên đổi giá là số $ cập nhật hồi tố. Backfill lịch sử cũ: `python3 cost_backfill.py` (gồm cả deck đã render trước khi có tracking — ước từ meta TTS + `final_video.mp4`/`timing.json`, đánh dấu `estimated`).
- Dashboard: bảng project thêm **cột Chi phí** riêng (≈ $ + tokens), ô **lọc theo tên**, dropdown **Đã render/Chưa render**, **sắp xếp** (Mới tạo nhất — mặc định, Cũ nhất, Vừa cập nhật, Tên A-Z) và **phân trang** (8 dự án/trang) phía client. Ngày tạo project ước từ mtime cũ nhất của file gốc (root + `source/`) vì container không đọc được birthtime, hiển thị chip "tạo dd/mm/yyyy" cạnh số slide.
- Thêm **outro slide cố định** vào starter (slide cuối, marker `data-outro`) kèm dòng voiceover outro cố định làm dòng cuối `script-90s.txt`; outro được miễn visual-first gate/adjacent-variation/color-diversity và giữ nguyên giữa các deck. Checkbox Outro ở trang render theo cùng logic Logo/Brand: bỏ tick = cắt outro slide khỏi video (`--skip-outro-slide`), tick không upload = dùng outro slide của deck (`outro.mp4` mẫu bỏ khỏi luồng mặc định), tick + upload = video upload thay thế outro slide. Rule cập nhật trong `WORKFLOW.md` §0, `TEMPLATE_RULES.md`, `SCRIPT_RULES.md`, `skills/slide-visuals`.
- Thêm module **`branding.py`** làm source of truth cho brand kênh (tên, handle, tagline, logo, câu outro): cấu hình qua `config/branding.json` (mẫu: `config/branding.example.json`, gitignore), thiếu file = mặc định NiceTechChannels; `web_server`, `social_upload.metadata`, outro slide đọc từ đây thay vì hardcode tên kênh. Server chạy trong Docker: đổi config phải `docker compose cp` vào container rồi restart.
- `docker-compose.yml` chuyển `slide/` từ volume Docker sang **bind mount `./slide`** để host và container nhìn chung dữ liệu deck (volume `ntc-slides` cũ giữ làm backup); image không còn bake `slide/` vào trong.

## NiceTechChannels Template 3 — 83.v5.86

Release này tập trung vào workflow tự động hơn, visual đẹp và giàu chuyển động hơn, QA chặt hơn, cùng trải nghiệm cài đặt/upload gọn hơn.

### Added

- Thêm **Link Autopilot**: khi user gửi link làm nguồn slide, agent tự thu source, chọn narrative, viết script, tạo visual plan `AUTO-APPROVED`, dựng deck, validate, capture và tự sửa đến khi đủ điều kiện bàn giao.
- Thêm `capture_slides.py` để chụp toàn bộ slide ở khung `390x693`, hiện đủ reveal và ẩn panel phục vụ visual QA.
- Thêm visual-first gate cho slide 2 trở đi: bắt buộc xác định scene primitive, creative angle, role màu, khác biệt với slide liền trước và motion/animation minh hoạ trong visual chính.
- Thêm copy proof cho slide 1 trong `visual-plan.md`: `Copied from`, `Allowed replacements` và `Intentional deviations`.
- Thêm release checklist có bước backup ZIP cũ theo ngày/giờ trước khi đóng gói bản mới.

### Changed

- Chuẩn hoá tên script cài đặt/chạy ngắn và dễ nhớ hơn: `install.sh`, `install.cmd`, `install.ps1` và `run.cmd`; cập nhật README/hướng dẫn theo các lệnh mới.
- Tối ưu toàn bộ workflow dựng slide để visual lớn, rõ trên điện thoại, nhiều animation semantic và ít phụ thuộc vào text box/card.
- Slide 1 phải copy trực tiếp canonical hero template; mọi thay đổi layout, background, typography, placement hoặc effect phải được ghi rõ và duyệt.
- Slide giải thích phải có chuyển động mang nghĩa trong visual chính; fade, glow, shimmer, background particle hoặc whole-card motion không còn được tính là animation đạt chuẩn.
- Tăng yêu cầu đa dạng shape, palette và role màu giữa các slide; contact sheet một tone màu hoặc lặp cùng box layout được xem là lỗi QA.
- Source image/video ưu tiên full-frame, đúng aspect ratio và full safezone width khi cần; tránh pillarbox/letterbox do frame sai tỷ lệ.
- Media-first slide ưu tiên khả năng đọc ở `390x693`; nếu media chiếm nhiều safezone, tách reveal sau thành custom scene thay vì thu nhỏ proof.
- Cấm overlay scan line, badge, caption, chip, gradient hoặc pseudo-element lên source media; source attribution đặt dưới frame.
- Demo/source video được `muted` mặc định để không đè voiceover/BGM; chỉ bật audio gốc khi đó là nội dung chính và user duyệt.
- Đưa subtitle mặc định từ `bottom: 152` lên `bottom: 172` để cân lại vùng hiển thị.
- Siết source workflow cho X/Twitter: dùng `bird read --json-full`, ưu tiên media của chính tác giả, lưu asset local và kiểm file type thật trước khi dùng.
- Siết script workflow: một câu tương ứng một reveal, hạn chế câu dài và không dùng dấu `—` trong script để TTS đọc tự nhiên hơn.
- Upload Center mặc định YouTube `Public` và Facebook `PUBLISHED`; metadata tự sinh title tối đa 90 ký tự, hashtag/tag theo nội dung và tự đồng bộ khi script mới hơn hoặc còn TODO.
- Render UI mặc định `720x1280` để giảm tải máy và hạn chế lỗi crop trên màn hình/virtual screen thấp; `1080x1920` vẫn là tuỳ chọn nét hơn.
- Đồng bộ các rule mới trong `AGENTS.md`, `CLAUDE.md`, `WORKFLOW.md`, `script-writing/` và các skill liên quan.
- Bump version repo và tên gói phát hành từ `83.v4.86` lên `83.v5.86`.

### Fixed

- Giảm lỗi visual nhỏ, dead space, chữ khó đọc trên điện thoại, card stack lặp lại, palette một màu và slide giải thích chỉ có animation trang trí.
- Giảm lỗi source media bị méo, crop sai, overlay che nội dung hoặc xuất hiện viền đen do container không khớp tỷ lệ.
- Giảm tình trạng metadata cũ/TODO không đồng bộ với `script-90s.txt`.
- Bổ sung kiểm tra slide 1 so với canonical template, contact-sheet color/squint pass và motion pass trước khi bàn giao.

### Removed / Cleaned up

- Bỏ yêu cầu agent tự tạo hoặc viết tay `upload-metadata.json`; Upload Center/server tự sinh khi cần.
- Xoá `upload-metadata.json` placeholder khỏi `template/nicetechchannels-slide-starter`.
- Loại bỏ hướng dựng slide giải thích bằng các stack text card và animation chỉ để trang trí.

## NiceTechChannels Template 3 — 83.v4.86

Release này cập nhật tài liệu vận hành theo workflow hiện tại: ưu tiên Antigravity IDE cho setup ban đầu, bổ sung hướng dẫn chọn coding agent/model mạnh, cập nhật Web UI ElevenLabs/Upload Center, và xuất lại bản PDF hướng dẫn sử dụng.

### Added

- Thêm minh hoạ chat với agent Antigravity trong tài liệu hướng dẫn.
- Thêm minh hoạ chat với Codex trong tài liệu hướng dẫn.
- Thêm gợi ý chọn coding agent/model mạnh:
  - Antigravity: Opus 4.6 hoặc Gemini Pro 3.1.
  - Codex: GPT-5.5 xhigh, chế độ standard.
  - Cursor: Composer 2.5.
  - Claude Code: Opus 4.8.
- Thêm hướng dẫn mới cho Web UI ElevenLabs API, Voice ID, Upload Center, YouTube/Facebook guide, Facebook Page popup, và nút comment source.
- Thêm `template/visual-pattern-gallery/` vào bản ZIP như thư viện template visual/animation cho agent.

### Changed

- Cập nhật hướng dẫn setup ban đầu sang Antigravity IDE và link tải chính thức.
- Rút gọn phần chuẩn bị để người dùng dựa vào script setup tự kiểm tra/cài dependency.
- Cập nhật mô tả `setup_and_run.sh` và `setup_and_run_windows.ps1` theo workflow mới: `yt-dlp`, `ffmpeg/ffprobe`, `bird` tuỳ chọn, và cảnh báo cookie X/Twitter.
- Đưa phần Agent-ready workflow xuống cuối tài liệu.
- Cập nhật bản PDF `HUONG_DAN_SU_DUNG.pdf` từ tài liệu markdown mới.
- Đổi tên file workflow chính thành `WORKFLOW.md` và cập nhật reference trong agent/docs/skill.
- Bản ZIP giữ nguyên danh sách `slide/` đã duyệt; chỉ cập nhật docs/rules và thêm template mới đã duyệt.

### Removed / Cleaned up

- Bỏ các mục hướng dẫn cũ đã trùng README hoặc phù hợp hơn cho coding agent tự xử lý.
- Bỏ phần mô tả workflow cũ gây dài và dễ lệch với Web UI hiện tại.

## NiceTechChannels Template 3 — 83.v3.86

Release này nâng cấp NiceTechChannels Template 3 từ bộ template render video slide thành một workflow hoàn chỉnh hơn: tạo slide bằng coding/remote agent, preview, validate, render voiceover, và upload video lên YouTube/Facebook Reels từ Web UI.

### Added

- Thêm **Upload Center** tại `/upload` để chọn video đã render, kiểm tra metadata, và upload lên YouTube/Facebook Reels.
- Thêm YouTube OAuth flow, chọn active channel, tạo metadata upload, và upload video lên YouTube từ Web UI.
- Thêm Facebook Reels/Page upload bằng `page_id` và Page access token trong `config/social-upload.json`.
- Thêm module `social_upload/` để tách riêng logic YouTube/Facebook upload, metadata, config, HTTP helper, và trạng thái kết nối.
- Thêm file mẫu `config/social-upload.example.json`.
- Thêm tài liệu cấu hình social upload:
  - `docs/upload/youtube-api-upload.md`
  - `docs/upload/facebook-api-upload.md`
  - `docs/upload/tiktok-api-upload.md`
- Thêm ElevenLabs API TTS qua `config/tts.example.json` và dependency `elevenlabs>=2.0.0`.
- Thêm package `tts/` để tách riêng Edge TTS, ElevenLabs TTS, và helper timing/audio dùng chung.
- Thêm khả năng upload file audio ElevenLabs trực tiếp từ Web UI để render production video.
- Thêm API/UI cho preview settings, upload BGM preview, sync script, xoá output, reveal output, chọn source folder, và cancel render job.
- Thêm validate nâng cao với `--semantic-report` để rà mapping giữa câu voiceover và reveal visual.
- Thêm safe-zone check bằng Playwright trong `validate_slide.py`, giúp phát hiện layout tràn vùng TikTok trước khi render.
- Thêm `template/nicetechchannels-slide-starter` làm starter template chính cho project slide mới.
- Thêm bộ tài liệu agent-ready:
  - `WORKFLOW.md`
  - `script-writing/START_HERE.md`
  - `script-writing/SCRIPT_RULES.md`
  - `script-writing/STYLE_INDEX.md`
  - `script-writing/style1.md` đến `style5.md`
  - `docs/visual-patterns/`
- Thêm hướng dẫn cho remote agent điều khiển từ mobile/điện thoại để agent có thể tạo slide, validate, render, và upload thay người dùng.
- Thêm bản PDF hướng dẫn sử dụng mới: `HUONG_DAN_SU_DUNG.pdf`.

### Changed

- Đổi branding tài liệu từ tên template cũ sang **NiceTechChannels Template 3**.
- Cập nhật hướng dẫn cài đặt sang **VS Code + Terminal** thay vì phụ thuộc Antigravity Terminal/Editor.
- Giữ Antigravity như một lựa chọn coding agent minh hoạ, cùng với Claude Code, ChatGPT Codex, OpenClaw, Hermes hoặc agent tương tự.
- Chuẩn hoá hướng dẫn macOS/Linux và setup script dùng `python3`.
- Cải tiến `setup_and_run.sh` để tìm Python 3.11–3.14, tự tạo `.venv`, xử lý `.venv` hỏng, cài dependencies, cài Playwright Chromium, rồi chạy Web UI.
- Cải tiến README với hướng dẫn cài đặt, dashboard, render, validate, TTS, ElevenLabs, và social upload rõ ràng hơn.
- Refactor flow TTS/render để hỗ trợ cả Edge TTS draft, ElevenLabs API TTS, và ElevenLabs audio upload.
- Cải thiện subtitle timing, karaoke/word-level alignment, audio padding, và render timing cho slide có media/video demo.
- Cập nhật `validate_slide.py` để đọc preview settings, bỏ qua deleted slides, kiểm semantic mapping, và kiểm safe-zone layout.
- Cập nhật Web UI render/dashboard với nhiều endpoint và trạng thái rõ hơn cho workflow preview/render/upload.
- Cập nhật tài liệu hướng dẫn sử dụng với workflow mới, bao gồm VS Code, coding agent, ElevenLabs iPhone workflow, và Upload Center.

### Fixed

- Sửa wording cũ khiến người dùng hiểu nhầm bắt buộc phải dùng Antigravity để cài/chạy project.
- Sửa sự mơ hồ giữa lệnh `python` và `python3` trên macOS/Linux.
- Sửa typo workflow cũ bằng cách thay `worfklow.md` bằng `WORKFLOW.md`.
- Giảm rủi ro Edge TTS dùng nhầm audio cache cũ sau khi đã render bằng ElevenLabs.
- Tăng khả năng phát hiện lỗi mapping script/slide và lỗi layout tràn safe zone trước khi render.

### Removed / Cleaned up

- Không còn dùng file workflow typo `worfklow.md`.
- Không còn phụ thuộc vào một số đường dẫn BGM cũ ở root/template cũ.
- Tài liệu không còn xem Antigravity là editor/terminal bắt buộc.
