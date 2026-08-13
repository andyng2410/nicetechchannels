# Metrics & Proof Patterns

Dùng khi slide cần số liệu, benchmark, bằng chứng, receipt, screenshot, hoặc source artifact.

## 1. Speed gauge

### Dùng khi
- Voiceover nói về tốc độ, latency, “nhanh hơn X lần”.

### Skeleton

```html
<div class="speed-gauge">
  <div class="gauge-arc"></div>
  <div class="gauge-needle"></div>
  <div class="gauge-center"><i class="fa-solid fa-bolt-lightning"></i></div>
</div>
```

### Motion
- Needle sweep khi reveal.
- Arc conic-gradient đỏ → vàng → xanh.

### Repo examples
- `template/openclaw-2026-5-2-release/index.html`
- `template/cursorai-post-2056415413077233983/index.html`
- `slide/anthropic-higher-limits-spacex-compute/index.html`
- `slide/openclaw-rtt-post-2055273947537490422/index.html`

## 2. Performance compare bars

### Dùng khi
- Có nhiều model/tool/cost/time để so sánh.
- Cần đọc nhanh bằng thanh, không phải paragraph.

### Skeleton

```html
<div class="perf-compare">
  <div class="perf-row">
    <span class="perf-label">Before</span>
    <div class="perf-bar-track"><div class="perf-bar perf-slow"></div></div>
    <span class="perf-time" data-count-to="3.2">0.0s</span>
  </div>
</div>
```

### Motion
- Bar grow khi reveal.
- Counter dùng `data-count-to`; kiểm `animateCounters()` và reset state trong `app.js`.

### Repo examples
- `template/escbase-slide-starter/index.html`
- `slide/gemini-3-5-flash/index.html`
- `slide/cursorai-post-2056415413077233983/index.html`

## 3. Metric cards / score grid

### Dùng khi
- Có 2–4 số liệu ngắn.
- Voiceover cần người xem nhớ con số.

### Notes
- Card nên là `number + label`, không mô tả dài.
- Nếu số liệu cần giải thích, để subtitle/voiceover gánh.

### Repo examples
- `slide/gemini-3-5-flash/index.html` (`gemini-metric-grid`, `metric-card`)
- `slide/anthropic-higher-limits-spacex-compute/index.html`
- `slide/heygen-post-2054582965137768817/index.html`

## 4. Proof / receipt / source artifact

### Dùng khi
- Cần “bằng chứng”: ảnh PayPal, tweet, screenshot, source image.
- Voiceover nói “ảnh này”, “bằng chứng”, “receipt”, “source”.

### Pattern
- Một image/source artifact lớn trong safezone.
- Thêm `source-pill` / `x-attribution` nhỏ nếu cần.
- Không phủ nhiều text giải thích lên ảnh; voiceover/subtitle giải thích.

### Repo examples
- `slide/chatgpt21-post-2056869230339821731/index.html` — image proof full visual.
- `slide/chatgpt-finances-post-2055317612687675545/index.html` — receipt/pay visual.
- `slide/openai-demo-thread-2052480800004956323/index.html` — receipt/source demo.
- `slide/claude-bitcoin-wallet-recovery/index.html` — proof/source style.

## 5. CPU/chip / data stream

### Dùng khi
- Voiceover nói về cache, model, compute, memory, data flow.

### Pattern
- `cpu-chip` for model/compute/cache.
- `stream-visual` for non-blocking pipeline/data packets.

### Repo examples
- `template/openclaw-2026-5-2-release/index.html`
- `template/escbase-slide-starter/index.html`
- `slide/ruview-github-trending/index.html`
