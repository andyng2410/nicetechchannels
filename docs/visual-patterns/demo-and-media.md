# Demo & Media Patterns

Dùng khi source có video demo, screenshot, app/browser surface, phone UI, hoặc source media cần xuất hiện trực tiếp.

## 1. Demo video reveal

### Dùng khi
- Demo là phần quan trọng, cần người xem thấy sản phẩm chạy.

### Rule
- Video dùng file local trong project, không hotlink.
- Nếu video là một reveal, đặt trong một `.slide-element` riêng.
- Không autoplay trước khi reveal.
- Khi reset/chuyển slide, pause và đưa `currentTime = 0` nếu có logic custom.
- Nếu video có audio meaningful, ưu tiên audio gốc và tránh BGM đè.

### Repo examples
- `slide/gemini-3-5-flash/index.html` (`gemini-video-frame`)
- `slide/browser-to-api-skill-demo/index.html` (`demo-frame`)
- `slide/openai-demo-thread-2052480800004956323/index.html`
- `template/stripe-treasury-launch/index.html`

## 2. Browser / app / Web UI frame

### Dùng khi
- Voiceover nói về web app, dashboard, browser, AI Studio, tool UI.

### Pattern
- `webui-frame`, `browser-frame`, top bar dots, URL/title pill.
- Nên dùng screenshot/media thật nếu source có.

### Repo examples
- `template/escbase-slide-starter/index.html` (`webui-frame`)
- `slide/gemini-3-5-flash/index.html` (`gemini-demo-flow`, `gemini-video-frame`)
- `slide/google-ai-studio-demo-2052453828272812310/index.html`
- `slide/damngruz-post-2053610962297782371/index.html`

## 3. Phone/social post frame

### Dùng khi
- Source là X/Twitter, mobile screenshot, app social UI.

### Pattern
- Phone frame + post/tweet card + tiny source attribution.
- Text inside post should be short; don't recreate a full screenshot as text if an image source exists.

### Repo examples
- `slide/google-post-2054263720629457058/index.html`
- `slide/googlebook-post-2054270454467121187/index.html`
- `slide/openaidevs-post-2053161503470366881/index.html`

## 4. Media-first full visual

### Dùng khi
- Một screenshot/image is the point.
- Voiceover explains the artifact.

### Notes
- Make media large and clean inside safezone.
- Avoid adding old cards around it unless they add new information.

### Repo examples
- `slide/chatgpt21-post-2056869230339821731/index.html`
- `slide/claude-bitcoin-wallet-recovery/index.html`
