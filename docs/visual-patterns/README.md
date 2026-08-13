# Visual Pattern Library

Thư viện này gom các visual/animation đẹp từ `workflow-old.md`, `template/`, và các deck trong `slide/`. Workflow chính chỉ giữ nguyên tắc; pattern chi tiết nằm ở đây để agent đọc khi dựng visual.

## Cách dùng bắt buộc

Trước khi sửa `index.html` / `style.css`, lập **visual plan** ngắn cho từng slide:

```text
Slide 1: pattern + lý do
Slide 2: pattern + lý do
...
```

Với mỗi reveal, hỏi theo thứ tự:

1. Câu voiceover này nói ý gì?
2. Pattern nào diễn đạt đúng ý nhất?
3. Có cần chữ không, hay icon/metric/media đã đủ?
4. Reveal có khớp semantic 1:1 với câu thoại không?
5. Có đang giữ safezone bottom gap >= 200px không?

## Luật sáng tạo cho mỗi deck

- Không copy máy móc một layout chỉ vì nó đẹp.
- Mỗi deck nên có **ít nhất một visual twist riêng**: biến thể layout, chuyển động, metaphor, hoặc composition mới phù hợp source.
- Có thể reuse component có sẵn, nhưng phải đổi semantic/text/motion cho đúng câu chuyện.
- Tránh lặp cùng một stack card qua nhiều slide. Nếu 2 slide liên tiếp trông giống nhau, slide sau phải đổi pattern hoặc composition.
- Nếu pattern không diễn đạt đúng voiceover, custom component mới ở cuối `style.css`.

## Scene-first thay vì card-first

Với slide giải thích sau hook, bắt đầu từ **một scene minh hoạ trung tâm**, không bắt đầu từ danh sách text box.

1. Chọn metaphor đúng ý: router, pipeline, orbit, terminal station, timeline, signal, assembly, hoặc before/after.
2. Cho visual chính chiếm phần lớn safezone; chỉ giữ keyword hoặc nhãn ngắn trên canvas.
3. Mỗi reveal phải làm scene thay đổi: packet chạy, node sáng, icon bay ra, lock mở, stream ghép lại, hoặc trạng thái cũ bị gạch.
4. Chỉ dùng card khi card là artifact có nghĩa như terminal, metric, source proof, risk warning, hoặc pipeline node.
5. Sau khi reveal hết, chụp slide ở `390x693` và kiểm tra xem người xem có hiểu visual chính trước khi đọc subtitle hay không.

## Nhóm pattern

- `animation-components.md`: 12 component/animation gốc giữ lại từ `workflow-old.md`.
- `flow-and-comparison.md`: trước/sau, workflow, pipeline, terminal, split lane.
- `metrics-and-proof.md`: số liệu, benchmark, proof, screenshot, receipt, source artifact.
- `risk-and-reactions.md`: rủi ro, phản ứng cộng đồng, traffic-light, caveat stack.
- `demo-and-media.md`: demo video, app/browser/phone frame, source media local.
- `conclusion-and-cta.md`: verdict, thesis cuối, source/CTA.
- `source-gallery.md`: ví dụ file/template đáng xem trong repo.
- `external-gpt5-5-patterns.md`: pattern hay từ `~/Desktop/video_template_gpt5-5`.

## Pattern selection nhanh

| Ý voiceover | Pattern nên thử |
| --- | --- |
| Trước → sau | `flow-diagram`, `split-panel`, before/after cards |
| Quy trình nhiều bước | `workflow-grid`, `pipeline-step`, `stream-visual` |
| CLI / dev tool | `mock-terminal`, `terminal-card`, `webui-frame` |
| Tốc độ / cost / benchmark | `speed-gauge`, `perf-compare`, `metric-card` |
| Bằng chứng / ảnh nguồn | `source-pill`, `proof-frame`, screenshot/media card |
| Rủi ro / tranh cãi | `traffic-light`, `risk-cards-container`, `caveat-card` |
| Comment/community | `channel-messages`, chat/tweet bubbles |
| Hook lớn | `hero-orbit`, radial hero, kinetic title |
| Kết luận | `glowing-conclusion`, `final-lockup`, `source-tag` |
