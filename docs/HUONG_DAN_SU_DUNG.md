# Hướng dẫn sử dụng Escbase Template 3

Phiên bản: `83.v5.86`

Tài liệu này hướng dẫn từng bước để tạo một video slide 9:16 bằng Escbase Template Web UI: mở project bằng Antigravity IDE, dùng coding agent tạo project slide, kiểm tra mapping, tạo giọng đọc bằng ElevenLabs hoặc Edge TTS, render ra video cuối, rồi upload YouTube/Facebook nếu đã cấu hình.

---

## 1. Bạn sẽ làm được gì?

Sau khi làm theo tài liệu này, bạn có thể:

1. Cài và chạy dashboard Web UI bằng một lệnh.
2. Yêu cầu coding agent tạo một project slide mới theo đúng workflow.
3. Preview slide trong trình duyệt trước khi render.
4. Render video bằng Edge TTS hoặc ElevenLabs.
5. Upload YouTube/Facebook Reels từ Web UI nếu đã cấu hình API.
6. Tìm video cuối tại:

```text
slide/ten-du-an/output/final_video.mp4
```

---

## 2. Chuẩn bị

Bạn cần một máy tính đã tải thư mục project Escbase Template. Phần còn lại cứ để script setup tự kiểm tra và cài những thứ cần thiết.

### Cài Antigravity IDE và mở project

1. Mở trang:

```text
https://antigravity.google/product/antigravity-ide
```

2. Tải và cài Antigravity IDE theo hệ điều hành của bạn.
3. Mở Antigravity.
4. Chọn **Open Folder...** rồi mở thư mục `escbase_template`.
5. Mở Terminal trong Antigravity:
   - macOS: **Terminal → New Terminal**
   - Windows: **Terminal → New Terminal**, chọn PowerShell nếu được hỏi

Antigravity là cách khuyến nghị trong tài liệu này vì vừa mở được workspace, vừa có agent để đọc file, sửa slide và chạy lệnh. Bạn vẫn có thể dùng Claude Code, ChatGPT Codex, OpenClaw, Hermes hoặc agent tương tự nếu quen workflow đó hơn.

Ảnh dưới đây minh hoạ workspace/agent trong Antigravity.

![Chat với agent Antigravity](./assets/huong-dan/antigravity.png)

---

## 3. Cài và chạy Web UI

Mở Terminal trong Antigravity tại thư mục repo.

### macOS/Linux

Ví dụ nếu project nằm ở Desktop:

```bash
cd ~/Desktop/escbase_template
```

Chạy lệnh:

```bash
./install.sh
```

Script này sẽ tự:

1. Tạo `.venv`.
2. Cài Python dependencies.
3. Cài Playwright Chromium.
4. Cài `yt-dlp` để tải video từ X/Twitter hoặc YouTube.
5. Kiểm tra/cài `ffmpeg` và `ffprobe` để xử lý media.
6. Hỏi bạn có muốn cài `bird` để đọc thread X/Twitter không.
7. Chạy Web UI.
8. Tự mở dashboard trong trình duyệt.

Nếu chọn cài `bird`, script sẽ hỏi `auth_token` và `ct0` của X/Twitter. Hai giá trị này là cookie đăng nhập, nên chỉ dùng tài khoản phụ, không gửi vào chat công khai và không chia sẻ file cấu hình/env.

### Windows

Mở **Terminal trong Antigravity** tại thư mục project đã giải nén. Nếu Antigravity hỏi shell, chọn **PowerShell**.

Ví dụ nếu cần tự chuyển thư mục:

```powershell
cd C:\Users\Tin\Desktop\escbase_template
```

Chạy lệnh:

```powershell
.\install.cmd
```

Nếu máy không nhận file `.cmd`, dùng fallback PowerShell. Lệnh này đọc file `install.ps1` trong thư mục hiện tại rồi chạy:

```powershell
powershell -c "gc .\install.ps1 -Raw | iex"
```

Script Windows sẽ tự kiểm tra và xử lý các phần thường gây lỗi:

1. Tìm hoặc thử cài Python 3.11–3.14.
2. Tạo `.venv` đúng kiểu Windows.
3. Kiểm tra/cài `yt-dlp` bằng `winget`; nếu `winget` lỗi, tự chuyển sang `pip` trong `.venv`.
4. Kiểm tra/cài `ffmpeg` và `ffprobe` bằng `winget`; nếu `winget` lỗi, tự tải gói portable khoảng 72 MB vào `.tools\ffmpeg\bin` và hiện tiến độ tải.
5. Hỏi bạn có muốn cài `bird` để đọc thread X/Twitter không.
6. Kiểm tra/cài Microsoft Visual C++ Redistributable nếu `greenlet/playwright` lỗi DLL.
7. Cài Python dependencies.
8. Kiểm tra Playwright, Edge/Chrome hệ thống và khả năng record video.
9. Chạy Web UI.

Nếu Windows hiện hộp thoại quyền cài đặt hoặc UAC, hãy bấm đồng ý. Nếu vừa cài Visual C++ Runtime mà vẫn lỗi `greenlet DLL`, hãy reboot Windows rồi chạy lại script.

### Link dashboard

Dashboard mặc định:

```text
http://localhost:8765
```

Nếu đã cài môi trường rồi, bạn có thể chạy server bằng:

macOS/Linux:

```bash
python3 web_server.py
```

Windows:

```powershell
.\run.cmd
```

Sau khi cài xong, các lần mở lại server chỉ cần chạy `.\run.cmd`. Lệnh này mở server nhanh bằng môi trường đã cài, tự thêm `.venv\Scripts` và FFmpeg portable vào PATH, không hỏi lại cài `bird`. Chỉ dùng lại `install.cmd` khi cài lần đầu hoặc khi môi trường/dependency bị lỗi.

Muốn dừng server: quay lại Terminal/PowerShell và bấm `Ctrl + C`.

> Nếu phát sinh lỗi cài đặt hoặc lỗi render mà bạn không chắc nguyên nhân, hãy gửi toàn bộ log lỗi trong Terminal/PowerShell cho coding agent bạn đang dùng. Agent có thể đọc log và chỉ đúng bước cần sửa.

---

## 4. Hiểu dashboard Web UI

Dashboard có các khu vực chính:

### Bộ máy render

Khu vực chọn project, chọn audio engine, chỉnh tốc độ audio và bắt đầu render.

ElevenLabs có 2 chế độ:

- **Tải file**: bạn tự tạo file voiceover trên ElevenLabs rồi upload vào Web UI.
- **API**: dán API key và Voice ID vào Web UI để hệ thống tự gọi ElevenLabs.

Các ô API key và Voice ID tự lưu sau khi bạn dán. Nếu API key đã lưu rồi, Web UI sẽ ẩn ô nhập API key để đỡ rối.

### Danh sách slide

Hiển thị các project trong thư mục:

```text
slide/
```

Project mới nhất thường nằm trên đầu.

Mỗi project có các nút thao tác nhanh như chọn project, xem slide, copy script, mở video cuối và xoá output.

### Xem slide

Mở preview slide trong tab mới để kiểm tra chữ, layout, animation và thứ tự reveal.

Link preview có dạng:

```text
http://localhost:8765/slide/ten-du-an/
```

### Mở video

Sau khi render xong, dashboard sẽ hiện nút mở video cuối:

```text
slide/ten-du-an/output/final_video.mp4
```

### Upload YouTube/Facebook

Trang upload nằm tại:

```text
http://localhost:8765/upload
```

Trang này dùng để chọn project đã render xong, kiểm tra metadata và upload video lên YouTube/Facebook Reels nếu bạn đã cấu hình API.

Các điểm mới cần biết:

- Nút **Hướng dẫn YouTube** mở trang cấu hình YouTube OAuth.
- Nút **Hướng dẫn Facebook** mở trang lấy Page ID và Page access token.
- Nút **Thêm Page** mở popup để dán Facebook Page ID và Page access token; Web UI sẽ lưu vào `config/social-upload.json`.
- Nút **Comment source** nằm riêng để upload xong mới comment link nguồn lên Facebook.
- Nút **Upload Public YouTube + Reels** chỉ bật khi YouTube đang `Public` và Facebook đang `Publish now`.

### Tốc độ audio

Có các nút chọn nhanh:

- `1.1`
- `1.15`
- `1.2`
- `1.25`

Nếu chưa biết chọn gì, dùng `1.1` hoặc `1.15`.

### Lưu ý audio cache

Nếu chạy **ElevenLabs trước → Edge TTS sau**, hãy bật **Tạo lại audio cache** để Edge TTS không dùng nhầm file audio cũ.

---

## 5. Prompt mẫu để tạo project slide

Copy prompt dưới đây và thay phần `[DÁN URL HOẶC NỘI DUNG]` bằng link bài viết, tweet thread, nội dung tin tức hoặc ý tưởng video của bạn.

```text
Đọc kỹ WORKFLOW.md và tạo một project slide mới từ nội dung sau:

[DÁN URL HOẶC NỘI DUNG Ở ĐÂY]
```

Nếu muốn chốt kịch bản trước (trường hợp cho Coding Agent chạy full quyền)

```text
Cho mình các lựa chọn script từ nội dung sau 

[DÁN URL HOẶC NỘI DUNG Ở ĐÂY]
```

Chọn coding agent/model mạnh để tạo:

- Antigravity: Opus 4.6 hoặc Gemini Pro 3.1.
- Codex: GPT-5.5 xhigh, chế độ standard.
- Cursor: Composer 2.5.
- Claude Code: Opus 4.8.

Ảnh minh hoạ chat với agent Antigravity:

![Chat với agent Antigravity](./assets/huong-dan/antigravity.png)

Ảnh minh hoạ chat với Codex:

![Chat với Codex](./assets/huong-dan/codex-agent-chat.svg)

---

## 6. Render bằng Edge TTS

Edge TTS là cách dễ nhất để render draft nhanh.

Các bước:

1. Trong dashboard, chọn project cần render.
2. Chọn tab **Edge TTS**.
3. Giữ voice mặc định `vi-VN-HoaiMyNeural` nếu chưa biết đổi.
4. Chọn tốc độ, ví dụ `1.1` hoặc `1.15`.
5. Nếu vừa render ElevenLabs trước đó, bật **Tạo lại audio cache**.
6. Bấm **Bắt đầu render**.
7. Chờ đến khi dashboard báo hoàn tất.

Video cuối nằm tại:

```text
slide/ten-du-an/output/final_video.mp4
```

---

## 7. Render bằng ElevenLabs

ElevenLabs cho giọng đọc tự nhiên hơn, phù hợp bản production.

Bạn có 2 cách dùng ElevenLabs:

- **Tải file**: tạo audio trên ElevenLabs trước, tải file về máy rồi upload vào Web UI.
- **API**: dán ElevenLabs API key và Voice ID vào Web UI để hệ thống tự tạo voiceover.

Trang hướng dẫn trong Web UI:

```text
http://localhost:8765/elevenlabs-guide
```

### 7.1. Tạo audio bằng ElevenLabs trên iPhone

Trước khi mở dashboard để render, hãy tạo sẵn file voiceover đầy đủ bằng app ElevenLabs trên iPhone.

Mở file script trên máy tính:

```text
slide/ten-du-an/script-90s.txt
```

Copy toàn bộ nội dung script rồi chuyển sang iPhone nếu cần. Có thể chuyển bằng AirDrop, Notes, Zalo, Telegram, email hoặc cách nào tiện nhất.

Các ảnh dưới đây minh hoạ cách tạo giọng đọc bằng app ElevenLabs trên iPhone.

### Bước 1 — Cài và mở app ElevenLabs

Tìm app **ElevenLabs: AI Voice Generator** trên App Store, sau đó bấm **Mở**.

![Cài và mở app ElevenLabs](./assets/huong-dan/1.PNG)

### Bước 2 — Chọn Text to speech

Ở màn hình Home, chọn mục **Text to speech**.

![Chọn Text to speech](./assets/huong-dan/2.jpeg)

### Bước 3 — Dán script vào Text to Speech

Trong màn hình **Text to Speech**, dán toàn bộ nội dung từ `script-90s.txt` vào ô nhập text.

Nếu app đang chọn sẵn giọng **Nhật - Narrative & Compelling**, bạn có thể dùng luôn. Nếu chưa đúng giọng, bấm vào phần chọn voice để đổi.

![Dán script vào Text to Speech](./assets/huong-dan/3.PNG)

### Bước 4 — Chọn giọng Nhật

Tìm từ khoá:

```text
nhật
```

Chọn giọng:

```text
Nhật - Narrative & Compelling
```

Sau đó bấm **Select voice**.

![Chọn giọng Nhật](./assets/huong-dan/4.PNG)

### Bước 5 — Chọn model và stability

Trong phần Settings:

- Model: **Eleven v3**
- Stability: **Natural**

Sau đó bấm **Save**.

![Cài model và stability](./assets/huong-dan/5.PNG)

Sau khi tạo xong voiceover, tải file audio về điện thoại.

Tiếp theo, chuyển file audio từ điện thoại sang máy tính. Có thể dùng:

- AirDrop.
- iCloud Drive.
- Google Drive.
- Zalo, Telegram hoặc email.

Đặt file audio ở nơi dễ tìm, ví dụ:

```text
Desktop/voiceover.mp3
```

### 7.2. Render trong Web UI bằng file audio đã chuyển vào máy tính

Sau khi file audio đã nằm trên máy tính:

1. Quay lại dashboard.
2. Chọn project cần render.
3. Chọn tab **ElevenLabs**.
4. Chọn chế độ **Tải file**.
5. Upload file audio vừa chuyển từ điện thoại sang máy tính.
6. Chọn tốc độ audio.
7. Bấm **Bắt đầu render**.

### 7.3. Render bằng ElevenLabs API

Cách này tiện hơn nếu bạn muốn Web UI tự tạo voiceover.

1. Mở dashboard.
2. Chọn project cần render.
3. Chọn tab **ElevenLabs**.
4. Chọn chế độ **API**.
5. Nếu chưa lưu API key, dán ElevenLabs API key vào ô **ElevenLabs API key**. Web UI sẽ tự lưu vào `config/tts.json`.
6. Mở **Cài đặt nâng cao**, dán **Voice ID** nếu muốn đổi giọng. Web UI cũng tự lưu Voice ID.
7. Chọn tốc độ audio.
8. Bấm **Bắt đầu render**.

Trong trang hướng dẫn ElevenLabs có link mở dashboard, link nạp credit, link tạo API key và link Voice Library đã search sẵn giọng “Nhật”.

Lưu ý: ElevenLabs API tốn credit. Nên nạp ít để test trước, ví dụ 5 đô, rồi render thử một project ngắn trước khi dùng thường xuyên.

---

## 8. Trong lúc render

Trong khi render:

- Không đóng Terminal/PowerShell đang chạy server.
- Không tắt máy.
- Theo dõi trạng thái trên dashboard.
- Nếu render lâu, chờ đến khi dashboard báo hoàn tất hoặc thất bại.

Nếu thành công, video cuối nằm tại:

```text
slide/ten-du-an/output/final_video.mp4
```

---

## 9. Upload YouTube/Facebook Reels (tuỳ chọn)

Sau khi video đã render xong, bạn có thể upload từ Web UI:

1. Mở:

```text
http://localhost:8765/upload
```

2. Chọn project có file:

```text
slide/ten-du-an/output/final_video.mp4
```

3. Kiểm tra title, caption, description, source comment và trạng thái upload.
4. Bấm nút upload tương ứng.

Các trang hướng dẫn cấu hình:

```text
http://localhost:8765/upload-guide/youtube
http://localhost:8765/upload-guide/facebook
```

Bạn cũng có thể đọc file tài liệu gốc:

- YouTube: `docs/upload/youtube-api-upload.md`.
- Facebook Reels/Page: `docs/upload/facebook-api-upload.md`.

Lưu ý:

- File `config/social-upload.json` chứa token/API secret, không chia sẻ và không commit.
- YouTube có nút **Thêm channel** trong Web UI để đăng nhập OAuth, sau đó có thể chọn channel đã kết nối.
- Facebook có nút **Thêm Page** để dán Page ID và Page access token. Token được lưu vào `config/social-upload.json` và không hiện lại trên UI.
- Facebook caption không chứa source link. Source link được tách sang ô **Source comment**, và chỉ comment được sau khi upload ở trạng thái `PUBLISHED`.
- Mặc định Upload Center để YouTube `Public` và Facebook `Publish now`; chỉ đổi sang `Private`/`Draft` khi thật sự muốn duyệt trước.
- Nút **Upload Public YouTube + Reels** cần YouTube `Public` và Facebook `Publish now`.

---

## 10. Lỗi thường gặp

### Không mở được dashboard

Kiểm tra Terminal/PowerShell có đang chạy server không.

Nếu chưa chạy, dùng:

macOS/Linux:

```bash
./install.sh
```

Nếu đã cài rồi, chỉ chạy server:

```bash
python3 web_server.py
```

Windows PowerShell:

```powershell
.\run.cmd
```

Nếu `run.cmd` báo chưa có `.venv` hoặc render lỗi do thiếu dependency, chạy lại `install.cmd` để sửa môi trường.

Mở đúng link:

```text
http://localhost:8765
```

### Không thấy project mới

Kiểm tra:

- Project có nằm trong `slide/ten-du-an` không.
- Project có `index.html` không.
- Đã bấm **Làm mới** trên dashboard chưa.

### Render bị lệch audio/hình

Nguyên nhân thường là mapping script/slide hoặc audio cache bị lệch.

Cách xử lý:

1. Gửi tên project và mô tả lỗi cho coding agent đang dùng.
2. Yêu cầu agent kiểm tra lại mapping, preview và render.
3. Nếu dùng Edge TTS sau ElevenLabs, bật **Tạo lại audio cache**.

### Windows báo lỗi khi cài hoặc render

Các lỗi Windows thường gặp và cách xử lý nhanh:

- **`greenlet DLL load failed`**: thường thiếu Microsoft Visual C++ Redistributable. Chạy lại `install.cmd`; nếu script vừa cài runtime, reboot Windows rồi chạy lại.
- **Không thấy `ffmpeg` hoặc `ffprobe`**: chạy lại setup. Nếu `winget` lỗi, bản setup mới sẽ tự tải gói FFmpeg portable khoảng 72 MB vào `.tools\ffmpeg\bin`, có thanh tiến độ và không cần quyền admin.
- **Không thấy `yt-dlp`**: chạy lại setup. Nếu `winget` lỗi, bản setup mới sẽ tự cài bằng `pip` trong `.venv`. Có thể kiểm tra trực tiếp bằng `.\.venv\Scripts\yt-dlp.exe --version`.
- **`bird` chưa đăng nhập X/Twitter**: cần đủ `auth_token` và `ct0`. Chạy lại setup, chọn cài `bird`, rồi dán 2 giá trị cookie theo hướng dẫn. Nên dùng tài khoản phụ.
- **Playwright tải Chromium bị timeout**: thường do mạng. Bản mới ưu tiên dùng Edge/Chrome hệ thống; nếu vẫn lỗi, chạy lại khi mạng ổn hoặc cài Microsoft Edge/Google Chrome.
- **Lỗi chữ/emoji trong console**: chạy bằng script Windows mới vì script đã bật UTF-8 cho Python.

Lệnh kiểm tra nhanh:

```powershell
where python
where ffmpeg
where ffprobe
where yt-dlp
.\.venv\Scripts\python.exe -c "import greenlet; import playwright.async_api; print('OK')"
```

Nếu vẫn lỗi, copy nguyên phần log lỗi và hỏi coding agent bạn đang dùng. Đừng chỉ gửi dòng “exit code 1”, vì cần vài dòng phía trên `Traceback` để biết lỗi nằm ở TTS, FFmpeg hay Playwright.


### Muốn render lại sạch

Trên dashboard, bấm nút **Xoá** ở project để xoá thư mục:

```text
output/
```

Sau đó render lại.

---

## 11. Ghi nhớ nhanh

macOS/Linux:

```bash
# Cài và chạy tất cả
./install.sh

# Nếu đã cài rồi, chỉ chạy server
python3 web_server.py
```

Windows PowerShell:

```powershell
# Cài và chạy tất cả
.\install.cmd

# Chạy lại server/render UI
.\run.cmd
```

```text
Dashboard:
http://localhost:8765

Trang upload:
http://localhost:8765/upload

Thư mục project:
slide/ten-du-an

Workflow tạo slide:
WORKFLOW.md

File video cuối:
slide/ten-du-an/output/final_video.mp4
```

---

## 12. Agent-ready workflow

Nếu bạn đang dùng các remote agent điều khiển từ mobile/điện thoại như OpenClaw, Claude Code, ChatGPT Codex, Hermes, Antigravity hoặc agent tương tự, bạn có thể ra lệnh để agent tự làm video, render và upload thay bạn:

- đọc source/nội dung đầu vào
- dùng `bird` để đọc thread X/Twitter nếu nguồn là link X
- dùng `yt-dlp` để tải video từ X/Twitter hoặc YouTube nếu bài có demo video
- dùng `ffmpeg` khi cần remux/normalize media
- tạo project slide trong `slide/ten-du-an`
- viết `script-90s.txt`
- dựng DOM/CSS/JS theo workflow
- validate slide
- render video
- chuẩn bị hoặc upload YouTube/Facebook nếu API đã cấu hình
