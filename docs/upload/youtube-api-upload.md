# Hướng dẫn kết nối YouTube API để upload video

Tài liệu này dành cho upload từ Web UI của repo hiện tại. YouTube upload đã được implement trong `web_server.py`; Facebook Reels có hướng dẫn cấu hình riêng.

## 1. Cần chuẩn bị

- Một Google account có quyền upload lên kênh YouTube cần dùng.
- Một Google Cloud project.
- YouTube Data API v3 đã được bật.
- OAuth Client ID dạng Web application.
- File cấu hình local: `config/social-upload.json`.

Không commit `config/social-upload.json` vì file này chứa `client_secret` và OAuth token.

## 2. Tạo Google Cloud project

1. Vào Google Cloud Console: https://console.cloud.google.com/
2. Tạo project mới, hoặc chọn project đang dùng.
![alt text](../assets/upload/image.png)
3. Vào **APIs & Services** → **Library**.
4. Tìm và enable **YouTube Data API v3**.
![alt text](../assets/upload/image-1.png)
![alt text](../assets/upload/image-3.png)
Tài liệu chính thức:
- Upload video: https://developers.google.com/youtube/v3/guides/uploading_a_video
- `videos.insert`: https://developers.google.com/youtube/v3/docs/videos/insert
- OAuth YouTube Data API: https://developers.google.com/youtube/v3/guides/authentication

## 3. Cấu hình OAuth consent screen

1. Vào **APIs & Services** → **OAuth consent screen**. -> Get Started

![alt text](../assets/upload/image-4.png)

2. Điền app name, support email (mail đăng nhập). --> next -->audience chọn External-->contact email (mail đăng nhập) --> continue và finish -->create.



3. Vào lại Audience: mục test user --> add emails --> thêm email của bạn vào **Test users**.


## 4. Tạo OAuth Client ID

1. Vào Client.
2. Chọn Create Client.
3. Application type: **Web application**.
4. Ở phần **Authorized redirect URIs**, thêm:

```text
http://localhost:8765/api/social/youtube/callback
```

Nếu đổi port chạy Web UI thì phải đổi cả:
- Authorized redirect URIs: `http://localhost:<PORT>/api/social/youtube/callback`
- `youtube.redirect_uri` trong `config/social-upload.json`

6. Lưu lại:
   - `Client ID`
   - `Client secret`

## 5. Tạo file config trong repo

Copy file mẫu:

```bash
cp config/social-upload.example.json config/social-upload.json
```

Điền YouTube config:

```json
{
  "youtube": {
    "client_id": "YOUR_GOOGLE_OAUTH_CLIENT_ID",
    "client_secret": "YOUR_GOOGLE_OAUTH_CLIENT_SECRET",
    "redirect_uri": "http://localhost:8765/api/social/youtube/callback"
  }
}
```

Sau khi bấm **Thêm channel** trong Web UI, repo sẽ tự ghi thêm `youtube.channels` và OAuth token vào file này. Không tự share file đó.

## 6. Kết nối trong Web UI

1. Chạy Web UI như bình thường.
2. Vào trang `/upload`.
3. Chọn project đã render xong và có file:

```text
slide/<project>/output/final_video.mp4
```

4. Bấm **Thêm channel**.
5. Đăng nhập đúng Google account có kênh YouTube cần upload.
6. Cho phép scope upload.
7. Quay lại Web UI, chọn:
   - title
   - description
   - privacy: `private`, `unlisted`, hoặc `public`
8. Bấm **Upload YouTube**.

Mặc định metadata trong repo:
- title lấy từ dòng đầu của `script-90s.txt`
- description gồm dòng đầu, nguồn nếu có trong `source/links.txt` hoặc `source/source.md`, và hashtag
- category YouTube: `22`
- `selfDeclaredMadeForKids`: `false`

## 7. Lỗi thường gặp

### Redirect URI mismatch

Kiểm tra URI trong Google Console và `config/social-upload.json` phải giống tuyệt đối:

```text
http://localhost:8765/api/social/youtube/callback
```

### Google không trả `refresh_token`

Thường xảy ra khi account đã từng cấp quyền cho app. Cách xử lý:

1. Vào Google Account → Security → Third-party access.
2. Gỡ quyền app OAuth đó.
3. Bấm **Thêm channel** lại.

Repo đã dùng `access_type=offline` và `prompt=consent` để xin refresh token.

### App đang Testing nên account khác không login được

Thêm email đó vào **Test users**, hoặc publish app và làm verification nếu Google yêu cầu.

### Upload xong nhưng chưa public

Upload Center mặc định chọn `public` để đăng ngay. Nếu đổi sang `private` hoặc `unlisted`, vào YouTube Studio để review/publish. Web UI trả link video và link Studio sau khi upload thành công.
