# Flow & Comparison Patterns

Dùng khi voiceover nói về chuyển dịch, trước/sau, quy trình, pipeline, hoặc tool flow.

## 1. Flow diagram

### Dùng khi
- Có thay đổi rõ `old -> new`.
- Có hai trạng thái đối lập: thủ công/tự động, chậm/nhanh, rời rạc/tích hợp.

### Không dùng khi
- Voiceover chỉ nêu một fact đơn lẻ.
- Slide cần bằng chứng/source artifact hơn là metaphor.

### Skeleton

```html
<div class="flow-diagram">
  <div class="flow-node flow-old"><i class="fa-solid fa-box"></i><span>Old</span><div class="flow-strike"></div></div>
  <div class="flow-arrow"><i class="fa-solid fa-arrow-right-long"></i></div>
  <div class="flow-node flow-new"><i class="fa-solid fa-bolt"></i><span>New</span><div class="flow-glow"></div></div>
</div>
```

### Motion
- `.flow-strike`: gạch đỏ/xéo để thể hiện cái cũ bị loại.
- `.flow-arrow`: arrow sweep/bounce.
- `.flow-glow`: pulse quanh node mới.

### Repo examples
- `template/openclaw-2026-5-2-release/index.html`
- `template/cursorai-post-2056415413077233983/index.html`
- `template/escbase-slide-starter/index.html`

## 2. Workflow / pipeline grid

### Dùng khi
- Câu thoại kể nhiều bước: tìm việc → làm PR → review → payout.
- Cần thấy thứ tự mà không nhồi chữ.

### Pattern
- `workflow-grid` + `workflow-step`
- `pipeline-step`
- `stream-visual` + data packets

### Motion
- Node sáng lần lượt.
- Arrow/packet chạy qua pipeline.
- Step active nổi lên khi reveal.

### Repo examples
- `template/pixelle-video-ai-short-video-engine/index.html`
- `slide/pixelle-video-ai-short-video-engine/index.html`
- `slide/github-trending-agents/index.html`
- `slide/openai-codex-follow-goals/index.html`

## 3. Mock terminal / dev surface

### Dùng khi
- Voiceover nói về CLI, PR, API, package, command, agent execution.
- Cần cảm giác “dev thật” thay vì card chữ.

### Skeleton

```html
<div class="mock-terminal">
  <div class="terminal-bar"><span class="td red"></span><span class="td yellow"></span><span class="td green"></span><span class="terminal-title">terminal</span></div>
  <div class="terminal-body">
    <code class="terminal-line"><span class="t-prompt">$</span> <span class="t-cmd typing-anim">npm install example</span></code>
    <code class="terminal-line t-output"><span class="t-success">✓</span> done</code>
  </div>
</div>
```

### Motion
- Typing cursor chỉ chạy khi parent `.slide-element.visible`.
- Output fade/scan nhẹ.

### Repo examples
- `template/openclaw-2026-5-2-release/index.html`
- `slide/cli-anything-github-trending/index.html`
- `slide/deepseek-tui-trending-repo/index.html`

## 4. Split panel / two-lane contrast

### Dùng khi
- Một câu có hai mặt: promise vs risk, human vs agent, before vs after.
- Cần tiết kiệm chiều dọc.

### Notes
- Mỗi panel chỉ nên có keyword/metric ngắn.
- Đừng biến mỗi panel thành paragraph.

### Repo examples
- `template/cursorai-post-2056415413077233983/index.html`
- `template/escbase-slide-starter/index.html`
