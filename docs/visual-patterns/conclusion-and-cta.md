# Conclusion & CTA Patterns

Dùng cho slide cuối, verdict, thesis, hoặc nguồn/CTA.

## 1. Glowing conclusion

### Dùng khi
- Câu kết là một thesis ngắn, cần mood mạnh.

### Skeleton

```html
<div class="glowing-conclusion">
  <div class="glowing-orb"></div>
  <div class="icon-badge icon-badge-large icon-badge-success"><i class="fa-solid fa-check"></i></div>
  <h2 class="slide-title">Chốt lại</h2>
  <p class="conclusion-text"><strong class="gradient-text">Keyword</strong> + thesis ngắn</p>
</div>
```

### Notes
- Nếu câu kết dài, để voiceover/subtitle nói; visual chỉ giữ keyword/thesis ngắn.
- Thường gộp icon + title + conclusion vào 1 `.slide-element`.

### Repo examples
- `template/openclaw-2026-5-2-release/index.html`
- `template/cursorai-post-2056415413077233983/index.html`
- `template/escbase-slide-starter/index.html`

## 2. Final lockup

### Dùng khi
- Muốn kết thúc bằng biểu tượng/logo/source/CTA gọn.

### Pattern
- `final-lockup`, `conclusion-box`, `source-tag`, `follow-tag`.
- CTA/source có thể là reveal riêng nếu script có câu riêng.

### Repo examples
- `slide/browser-to-api-skill-demo/index.html`
- `slide/cloakbrowser-github-trending/index.html`
- `template/stripe-treasury-launch/index.html`

## 3. Source tag / attribution

### Dùng khi
- Cần hiện nguồn ngắn ở cuối hoặc dưới media.

### Notes
- Source tag không thay thế `source/source.md`.
- Không để link dài chiếm canvas; dùng label ngắn như `Nguồn: Google Blog`.

### Repo examples
- `template/pixelle-video-ai-short-video-engine/index.html`
- `template/stripe-treasury-launch/index.html`
- `slide/arc-post-2053852639943852178/index.html`
