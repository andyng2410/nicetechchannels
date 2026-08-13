# Extra patterns từ `~/Desktop/video_template_gpt5-5`

Các pattern này được rút từ repo cũ `video_template_gpt5-5`. Chỉ dùng làm cảm hứng/biến thể, không copy nguyên nếu không khớp script hoặc safezone hiện tại.

## Nguồn đáng xem nhanh

- `slide/image-to-code-frontend-viral/`: before/after, mock screen, design lab, compare board, feedback ribbon.
- `slide/openai-codex-everyday-work-visual/`: kinetic grid, hero orbit, connector board, workflow grid, risk stack.
- `slide/openclaw-2026-4-29-release/`: hero orbit, connector glow board, traffic-light pole.
- `slide/openclaw-2026-4-26/`: elastic title, logo bounce, timeline, node cards.
- `template/kimi-k2-6/`: title glow/glitch, benefit cards, timeline/quote baseline.

## 1. Kinetic grid / scan panel

### Dùng khi
- Hook/hero cần cảm giác “system đang chạy”.
- Nền cần chuyển động nhẹ nhưng không làm rối visual chính.

### Pattern

```html
<div class="kinetic-grid"></div>
```

Motion:
- `scan-panel`: panel trôi nhẹ lên/xuống, opacity thay đổi.
- `grid-drift`: background grid dịch chéo chậm.

Source:
- `slide/openclaw-2026-4-29-release/style.css`
- `slide/image-to-code-frontend-viral/style.css`

## 2. Hero orbit nâng cấp

### Dùng khi
- Slide 1 cần một hệ sinh thái xoay quanh core: app, tool, model, workflow.

### Pattern

```html
<div class="hero-orbit">
  <div class="orbit-ring ring-a"></div>
  <div class="orbit-ring ring-b"></div>
  <div class="hero-core"><i class="fa-solid fa-terminal"></i></div>
  <span class="orbit-chip chip-slack">Slack</span>
  <span class="orbit-chip chip-docs">Docs</span>
  <span class="orbit-chip chip-sheets">Sheets</span>
</div>
```

Motion:
- `spin`: rings quay ngược chiều nhau.
- `core-pulse`: core thở/glow.
- `bob`: orbit chips nổi nhẹ.

Source:
- `slide/openclaw-2026-4-29-release/index.html`
- `slide/openai-codex-everyday-work-visual/index.html`

## 3. Elastic title / logo bounce

### Dùng khi
- Hook cần cảm giác pop/viral, launch/release, hoặc logo/product identity.

Motion:
- `logo-bounce`: logo nảy nhẹ liên tục.
- `elastic-in`: title rubber-band khi reveal.
- `shimmer-sweep`: ánh sáng quét ngang title.
- `title-glow`: glow một nhịp khi slide active.

Source:
- `slide/openclaw-2026-4-26/style.css`

Notes:
- Dùng tiết chế; elastic title hợp hook/launch, không hợp slide nghiêm túc/rủi ro.

## 4. Connector glow board

### Dùng khi
- Cần show 3 nguồn/kết nối/context đi vào một agent.
- Voiceover nói về app integration, data source, plugin, connector.

### Pattern

```html
<div class="connector-board">
  <div class="connector active"><i class="fa-solid fa-toggle-on"></i><span>Bật/tắt theo nhu cầu</span></div>
  <div class="connector"><i class="fa-solid fa-calendar-day"></i><span>Giới hạn maxPerDay</span></div>
  <div class="connector"><i class="fa-solid fa-heartbeat"></i><span>Heartbeat clamp</span></div>
</div>
```

Motion:
- `connector-glow`: từng connector nổi lên và đổi border glow theo delay.
- `terminal-dot` + `blink`: điểm trạng thái nhấp nháy cho terminal/status line.

Source:
- `slide/openclaw-2026-4-29-release/index.html`
- `slide/openai-codex-everyday-work-visual/index.html`

## 5. Design lab / reference-output visual

### Dùng khi
- Voiceover nói về refine loop, design target, image-to-code, screenshot comparison.
- Muốn visual “reference → output” thay vì card chữ.

### Pattern

```html
<div class="design-lab-visual">
  <div class="lab-frame reference"><span>REFERENCE</span><div class="hero-block"></div><div class="lab-line l1"></div></div>
  <div class="lab-arrow"><i class="fa-solid fa-arrow-right-long"></i></div>
  <div class="lab-frame output"><span>OUTPUT</span><div class="hero-block small"></div><div class="lab-line l3"></div></div>
</div>
```

Motion:
- `orb-sweep`: radial light sweep trong frame.
- Output frame lệch nhẹ xuống để tạo chiều sâu.

Source:
- `slide/image-to-code-frontend-viral/index.html`
- `slide/image-to-code-frontend-viral/style.css`

## 6. Before/after + mock screen

### Dùng khi
- Cần nói “đừng làm thế này, hãy làm thế kia”.
- Cần minh hoạ visual target/mockup mà không cần screenshot thật.

Patterns:

```html
<div class="before-after"><div class="bad">modern?</div><i class="fa-solid fa-arrow-right-long"></i><div class="good">target</div></div>
```

```html
<div class="mock-screen"><div class="mock-art"></div><div class="mock-line w1"></div><div class="mock-line w2"></div></div>
```

Motion:
- `orb-sweep` trong `.mock-art`.
- Có thể thêm bar/line reveal khi parent visible.

Source:
- `slide/image-to-code-frontend-viral/index.html`

## 7. Compare board + feedback ribbon

### Dùng khi
- Voiceover nói về inspect/refine/fix loop.
- Cần biến “feedback cụ thể” thành visual chứ không chỉ text card.

Patterns:

```html
<div class="compare-board">
  <div class="compare-card target"><span>reference</span><strong>spacing + hierarchy</strong></div>
  <div class="compare-card shot"><span>screenshot</span><strong>lệch ở đâu?</strong></div>
  <div class="compare-connector"></div>
</div>
```

```html
<div class="feedback-ribbon"><i class="fa-solid fa-pen-nib"></i><span>Feedback cụ thể rồi sửa tiếp.</span></div>
```

Source:
- `slide/image-to-code-frontend-viral/index.html`

## 8. Traffic-light pole

### Dùng khi
- Cần traffic-light thật sự có hình dạng đèn giao thông, không chỉ risk cards.
- Voiceover có 3 trạng thái đỏ/vàng/xanh rõ ràng.

### Pattern

```html
<div class="traffic-light-pole">
  <div class="traffic-light-housing">
    <div class="traffic-light-lamp"><div class="timeline-dot lightable" data-light-color="red"></div></div>
    <div class="traffic-light-lamp"><div class="timeline-dot lightable" data-light-color="yellow"></div></div>
    <div class="traffic-light-lamp"><div class="timeline-dot lightable" data-light-color="green"></div></div>
  </div>
  <div class="traffic-light-labels">
    <div class="traffic-label traffic-label-red"><p><strong>Risk</strong> mô tả ngắn.</p></div>
    <div class="traffic-label traffic-label-yellow"><p><strong>Unknown</strong> mô tả ngắn.</p></div>
    <div class="traffic-label traffic-label-green"><p><strong>Upside</strong> mô tả ngắn.</p></div>
  </div>
</div>
```

Mapping:
- Slide dùng `data-mode="traffic-light"`.
- Mỗi dot vẫn là `.lightable`; label tương ứng phải khớp câu voiceover.

Source:
- `slide/openclaw-2026-4-29-release/index.html`

## 9. Timeline với pulse dot

### Dùng khi
- Câu chuyện có tiến trình cũ → giữa → mới.
- Muốn tiết kiệm chiều ngang hơn traffic-light pole.

Motion:
- `pulse-dot`: dot tương lai/phần đang chú ý nở vòng glow.
- Vertical line nối các item.

Source:
- `slide/openclaw-2026-4-26/index.html`

## 10. Section strip / scoped generation

### Dùng khi
- Voiceover nói về chia nhỏ workflow: Hero / About / CTA, Step A/B/C.
- Cần một visual cực gọn cho “scope nhỏ”.

Pattern:

```html
<div class="section-strip"><span>Hero</span><span>About</span><span>CTA</span></div>
```

Source:
- `slide/image-to-code-frontend-viral/index.html`

## Những animation nên cân nhắc import vào starter/pattern docs

- `elastic-in`: tốt cho hook/launch.
- `connector-glow`: tốt cho integration/workflow slides.
- `grid-drift` / `scan-panel`: tốt cho nền hero/system.
- `orb-sweep`: tốt cho mockup/proof/design frame.
- `traffic-light-pole`: biến thể đẹp hơn risk cards khi cần visual rõ.
