# Risk & Reaction Patterns

Dùng khi voiceover nói về rủi ro, trade-off, phản ứng cộng đồng, tranh cãi, caveat, hoặc nhiều trạng thái đỏ/vàng/xanh.

## 1. Traffic-light mode

### Dùng khi
- Có 3 trạng thái: risk / unknown / upside.
- Có phản ứng community cần phân loại.

### DOM rule
- `.slide` phải có `data-mode="traffic-light"`.
- Reveal units = 1 `.slide-element` + từng `.lightable`.

### Pattern

```html
<div class="risk-cards-container">
  <div class="risk-card lightable" data-light-color="red">...</div>
  <div class="risk-card lightable" data-light-color="yellow">...</div>
  <div class="risk-card lightable" data-light-color="green">...</div>
</div>
```

### Repo examples
- `template/openclaw-2026-5-2-release/index.html`
- `template/escbase-slide-starter/index.html`
- `slide/gemini-3-5/index.html`
- `slide/browser-to-api-skill-demo/index.html`

## 2. Risk cards / caveat stack

### Dùng khi
- Không cần traffic-light interaction nhưng cần show caveats.
- Voiceover có 2–3 điều kiện hoặc cảnh báo.

### Notes
- Mỗi card chỉ nên có label ngắn + icon.
- Nếu card text dài hơn 2 dòng, rút gọn hoặc đẩy xuống subtitle.

### Repo examples
- `slide/browser-to-api-skill-demo/index.html` (`caveat-row`, `caveat-card`)
- `slide/googlechrome-post-2052795698626633745/index.html`
- `slide/claude-bitcoin-wallet-recovery/index.html`

## 3. Community reaction bubbles

### Dùng khi
- Source là X/Twitter/comment thread.
- Cần thể hiện sentiment: nghi ngờ, khoe kết quả, phản biện.

### Pattern
- `channel-messages`, chat bubbles, tweet-like cards.
- Bubbles nên tiết kiệm chữ, mỗi bubble 1 ý.

### Repo examples
- `template/chatgpt21-post-2053933298263462330/index.html`
- `slide/chatgpt21-post-2053933298263462330/index.html`
- `slide/gpt55-instant-chatgpt-memory-personalization/index.html`

## 4. Premium traffic box / staged thesis

### Dùng khi
- Voiceover có 3 nấc chuyển dịch hoặc 3 tầng kết luận.
- Cần cảm giác strategic, không chỉ warning.

### Repo examples
- `template/cursorai-post-2056415413077233983/index.html`
- `template/stripe-treasury-launch/index.html`
- `slide/openclaw-rtt-post-2055273947537490422/index.html`
