# Animation Components từ workflow-old

File này giữ lại các component/animation hay trong `workflow-old.md` để agent không làm mất thư viện motion cũ. Khi dùng, vẫn phải đổi semantic/text/composition cho đúng script; không copy máy móc.

## 1. Flow Diagram — so sánh trước/sau

```html
<div class="flow-diagram">
  <div class="flow-node flow-old"><i class="fa-solid fa-..."></i><span>Old</span><div class="flow-strike"></div></div>
  <div class="flow-arrow"><i class="fa-solid fa-arrow-right-long"></i></div>
  <div class="flow-node flow-new"><i class="fa-solid fa-..."></i><span>New</span><div class="flow-glow"></div></div>
</div>
```

Animation:
- `.flow-strike`: gạch đỏ xéo / strikethrough.
- `.flow-glow`: pulse xanh quanh trạng thái mới.
- `.flow-arrow`: bounce/sweep qua lại.

Dùng khi: trước/sau, old/new, shift, migration, replacement.

## 2. Mock Terminal — CLI/dev output

```html
<div class="mock-terminal">
  <div class="terminal-bar"><span class="td red"></span><span class="td yellow"></span><span class="td green"></span><span class="terminal-title">terminal</span></div>
  <div class="terminal-body">
    <code class="terminal-line"><span class="t-prompt">$</span> <span class="t-cmd typing-anim">npm install @example/pkg</span></code>
    <code class="terminal-line t-output"><span class="t-success">✓</span> done</code>
  </div>
</div>
```

Animation:
- `.typing-anim`: cursor gõ chữ từ trái sang phải.
- `.t-success`: xanh lá, fade/glow nhẹ.
- Chỉ chạy typing khi parent `.slide-element.visible`.

Dùng khi: CLI, package install, API command, agent executing task, PR/build/test output.

## 3. Model Badge Card — model/tool/service badge

```html
<div class="model-badge-card">
  <div class="model-icon"><i class="fa-solid fa-brain"></i></div>
  <div class="model-info"><span class="model-name">Tên</span><span class="model-provider">Provider</span></div>
  <div class="model-default-tag">DEFAULT</div>
</div>
```

Animation:
- `.model-default-tag`: pulse glow.
- Icon có thể thêm ring/orbit nhẹ.

Dùng khi: giới thiệu model AI, tool, provider, default model, product identity.

## 4. Speed Gauge — tốc độ/hiệu suất

```html
<div class="speed-gauge">
  <div class="gauge-arc"></div>
  <div class="gauge-needle"></div>
  <div class="gauge-center"><i class="fa-solid fa-bolt-lightning"></i></div>
</div>
```

Animation:
- `.gauge-needle`: sweep từ chậm sang nhanh.
- `.gauge-arc`: conic-gradient đỏ → vàng → xanh.

Dùng khi: speed, latency, performance, “nhanh hơn X lần”.

## 5. Performance Compare Bars — benchmark/cost/time

```html
<div class="perf-compare">
  <div class="perf-row">
    <span class="perf-label">Before</span>
    <div class="perf-bar-track"><div class="perf-bar perf-slow"></div></div>
    <span class="perf-time" data-count-to="3.2">0.0s</span>
  </div>
  <div class="perf-row">
    <span class="perf-label">After</span>
    <div class="perf-bar-track"><div class="perf-bar perf-fast"></div></div>
    <span class="perf-time" data-count-to="0.8">0.0s</span>
  </div>
</div>
```

Animation:
- `.perf-slow`: bar grow lớn, đỏ/cam.
- `.perf-fast`: bar grow nhỏ/nhanh, xanh.
- `data-count-to`: dùng `animateCounters()` để đếm số khi reveal.

Dùng khi: before/after speed, model comparison, cost reduction, benchmark.

## 6. CPU/Chip Visual — compute/cache/model internals

```html
<div class="cpu-chip">
  <div class="chip-body">
    <div class="chip-pins left"></div>
    <div class="chip-core"><i class="fa-solid fa-microchip"></i><span>CACHE</span></div>
    <div class="chip-pins right"></div>
  </div>
  <p class="chip-label">Mô tả → <strong>highlight</strong></p>
</div>
```

Animation:
- `.chip-core::after`: scan line dọc chạy liên tục.
- Pins/core glow nhẹ khi reveal.

Dùng khi: cache, compute, model internals, memory, optimization.

## 7. Data Stream — pipeline/data flow

```html
<div class="stream-visual">
  <div class="stream-pipe">
    <div class="stream-data d1"></div>
    <div class="stream-data d2"></div>
    <div class="stream-data d3"></div>
  </div>
  <div class="stream-status"><i class="fa-solid fa-check-circle"></i> Status</div>
  <p class="stream-caption">Mô tả <strong>highlight</strong></p>
</div>
```

Animation:
- 3 data packets chạy từ trái sang phải.
- Stagger khoảng 0.6s.

Dùng khi: non-blocking, streaming, pipeline, API/data movement.

## 8. Core Module Grid — highlight mode

```html
<div class="core-module-grid">
  <div class="core-module highlightable">
    <div class="module-icon"><div class="module-ring"></div><i class="fa-solid fa-box"></i></div>
    <div class="module-info"><span>01</span><p>Tiêu đề</p></div>
  </div>
</div>
```

Mapping:
- Slide phải có `data-mode="highlight"` nếu dùng `.highlightable`.
- Reveal units = `.slide-element` + từng `.highlightable`.

Animation:
- Từ grayscale/low-opacity sang neon active.
- `.module-ring`: xoay liên tục (`spin-ring`) khi highlighted.

Dùng khi: tính năng, modules, capabilities, benefits, checklist tương tác.

## 9. Risk Cards Container — traffic-light cảnh báo

```html
<div class="risk-cards-container">
  <div class="risk-card lightable" data-light-color="red">
    <div class="risk-icon"><i class="fa-solid fa-xmark"></i></div>
    <div class="risk-text"><strong>Rủi ro</strong><span>Mô tả ngắn</span></div>
  </div>
</div>
```

Mapping:
- Slide phải có `data-mode="traffic-light"` nếu dùng `.lightable`.
- Reveal units = `.slide-element` + từng `.lightable`.

Animation:
- `.lit-red` / `.lit-yellow` / `.lit-green`: card nổi lên.
- Icon pulse theo màu (`pulse-red`, tương tự yellow/green).

Dùng khi: rủi ro, tranh cãi, sentiment, red/yellow/green states.

## 10. Floating Chat Bubbles — hội thoại/community

```html
<div class="channel-messages">
  <div class="c-message slide-element scale-in left-msg">
    <div class="msg-avatar discord"><i class="fa-brands fa-discord"></i></div>
    <div class="msg-bubble"><strong>Kênh 1</strong><span>Chi tiết ngắn</span></div>
  </div>
  <div class="c-message slide-element scale-in right-msg">
    <div class="msg-bubble"><strong>Kênh 2</strong><span>Chi tiết ngắn</span></div>
    <div class="msg-avatar telegram"><i class="fa-brands fa-telegram"></i></div>
  </div>
</div>
```

Notes:
- Tiết kiệm chiều dọc tốt hơn stack card.
- CSS bắt buộc: `.c-message { flex-direction: row; }`, `.msg-bubble { text-align: left; }` để tránh bị thừa hưởng layout column/căn giữa từ `.slide-element`.

Dùng khi: community comments, reactions, chat, X/Twitter sentiment.

## 11. Premium Traffic Box — thesis 3 tầng

```html
<div class="premium-traffic-box">
  <div class="traffic-housing">
    <div class="timeline-dot lit-red"></div>
    <div class="timeline-dot lit-yellow"></div>
    <div class="timeline-dot lit-green"></div>
  </div>
  <div class="traffic-content">
    <div class="t-item"><strong>Stage 1</strong><p>Mô tả ngắn</p></div>
    <div class="t-item"><strong>Stage 2</strong><p>Mô tả ngắn</p></div>
    <div class="t-item"><strong>Stage 3</strong><p>Mô tả ngắn</p></div>
  </div>
</div>
```

Dùng khi: câu chuyện có 3 nấc dịch chuyển, ví dụ `API thuê → fine-tune dọc → model riêng`, `rủi ro → thích nghi → lợi thế`.

## 12. Glowing Conclusion — kết luận mood mạnh

```html
<div class="glowing-conclusion">
  <div class="glowing-orb"></div>
  <div class="icon-badge icon-badge-large icon-badge-success"><i class="fa-solid fa-..."></i></div>
  <h2 class="slide-title">Chốt lại</h2>
  <p class="conclusion-text"><strong class="gradient-text">Keyword</strong> + thesis ngắn</p>
</div>
```

Animation:
- `.glowing-orb`: ambient glow/pulse.
- Icon/title fade-up, conclusion shimmer nhẹ.

Dùng khi: verdict, thesis cuối, CTA/follow/source. Nếu kết luận dài hơn 1 câu, để voiceover/subtitle gánh và giữ visual thật gọn.

## CSS animation rules giữ từ workflow-old

- Append CSS custom ở cuối `style.css`.
- Animation phải trigger qua `.slide-element.visible .class-con`, không chạy sẵn trên initial render nếu cần reveal timing.
- Dùng biến theme: `var(--primary)`, `var(--accent)`, `var(--success)`.
- Glassmorphism tốt: `background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(12px);`.
- Neon shadow nên dùng alpha thấp, tránh cháy chữ.
- Nếu animation cần reset khi navigate (bar width, counter), thêm/reset trong `resetElements()` hoặc dùng hook có sẵn như `animateCounters()`.
