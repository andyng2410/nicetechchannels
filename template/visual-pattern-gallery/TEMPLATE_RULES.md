# Visual Pattern Gallery

Đây là index mẫu cho Escbase slide visuals. Slide 1 phải copy từ canonical template folder tương ứng; các slide sau là mẫu code/visual để tham khảo, có thể copy, remix hoặc thay bằng scene sáng tạo hơn theo nội dung.

## Cách dùng

1. Copy deck mới từ `template/escbase-slide-starter`.
2. Mở `template/visual-pattern-gallery/index.html` và `style.css`.
3. Slide 1: chọn đúng canonical template, copy nguyên slide 1, CSS liên quan, và asset trong `source/` nếu cần.
4. Slide 2 trở đi: tham khảo các mẫu bên dưới; copy/remix khi hợp, hoặc thiết kế scene custom nếu nội dung cần cách minh hoạ khác.
5. Thay text/logo/media/source theo deck mới.
6. Giữ reveal units khớp số câu trong `script-90s.txt`.
7. Chạy `.venv/bin/python validate_slide.py slide/<project> --semantic-report`.

Khi copy visual pattern từ gallery, không xoá hoặc thay thế `preview-assets/bgm/meta.mp3` đã copy từ starter.

Không copy toàn bộ voiceover vào text box. Canvas chỉ giữ keyword, metric, label ngắn, source tag hoặc artifact có nghĩa.

## Slide 1 fixed hero templates

- `visual-gallery:source-image-hero`: copy từ `template/googleaistudio-post-2069450021955592406/` khi ảnh/screenshot/source artifact là bằng chứng chính.
- `visual-gallery:product-logo-hero`: copy từ `template/kimi-moonshot-post-2066467110960959833/` khi model, product hoặc brand là hook.
- `visual-gallery:avatar-person-hero`: copy từ `template/addyosmani-loop-engineering/` khi tác giả/source identity là hook.
- `visual-gallery:github-repo-hero`: copy từ `template/openmontage-github-trending/` cho repo GitHub hoặc GitHub Trending.

Slide 1 chỉ thay nội dung cần thay; không đổi layout, nền, style hero, hoặc tự làm lại hiệu ứng của mẫu.

## Later-slide visual references

- Slide 5 `visual-gallery:media-first-frame`: demo/media-first frame. Dùng cho video, screenshot hoặc source media local full-frame.
- Slide 6 `visual-gallery:performance-bars`: performance compare bars. Dùng cho benchmark, latency, cost, score.
- Slide 7 `visual-gallery:flow-diagram`: flow diagram. Dùng cho old-to-new, gate, packet routing, state shift.
- Slide 8 `visual-gallery:speed-gauge`: speed gauge. Dùng cho tốc độ, throughput, latency, progress.
- Slide 9 `visual-gallery:chip-scan`: CPU/chip scan. Dùng cho model internals, cache, memory, optimization.
- Slide 10 `visual-gallery:data-stream`: data stream. Dùng cho API streaming, pipeline, packet movement.
- Slide 11 `visual-gallery:mock-terminal`: mock terminal. Dùng cho CLI, install, build, test output, dev tool proof.
- Slide 12 `visual-gallery:workflow-grid`: workflow grid. Dùng cho quy trình nhiều bước.
- Slide 13 `visual-gallery:highlight-mode`: highlight mode. Dùng khi cần nhấn lần lượt các module trong cùng một scene.
- Slide 14 `visual-gallery:risk-cards`: risk cards / traffic-light. Dùng cho risk, unknown, upside hoặc reaction.
- Slide 15 `visual-gallery:traffic-light-pole`: traffic-light pole. Dùng khi muốn tín hiệu đỏ/vàng/xanh thật rõ.
- Slide 16 `visual-gallery:chat-bubbles`: chat bubbles. Dùng cho community reaction, Q&A, builder response.
- Slide 17 `visual-gallery:revenue-balance`: revenue balance. Dùng khi hai số liệu tạo nghịch lý đáng nhớ.
- Slide 18 `visual-gallery:final-lockup`: final lockup. Dùng cho kết luận, thesis hoặc CTA/source cuối.

## Hard visual standards

Các slide sau hook được phép sáng tạo, nhưng phải giữ:

- Dùng safezone `100px 28px 200px` như canvas thật.
- Visual chính phải đủ lớn; không để scene lọt thỏm giữa slide.
- Media source/demo phải match aspect ratio hoặc full width safezone; không để pillarbox/letterbox đen do frame sai tỉ lệ, trừ khi black bars nằm trong file gốc hoặc user duyệt rõ.
- Text/label quan trọng tối thiểu khoảng 11-12px.
- Scene title/kicker nên khoảng 13-20px.
- Metric chính nên khoảng 42-51px.
- Bố cục và màu tham chiếu `slide/alex-nguyen-ai-apps/`: chữ lớn, rõ, nhiều màu có vai trò, visual chiếm full safezone.

## Slide 1 cố định

- Headline H1 mặc định dùng cỡ OpenMontage: khoảng `42px` trên khung `390x693`.
- H1 mặc định shimmer.
- Không shimmer video, source image, logo, metric phụ.
- Nếu title dài, ưu tiên wrap cân đối hoặc mở rộng max-width trong safezone; chỉ giảm size khi vẫn tràn/overlap.
- Slide 1 không chứa nhiều proof/metric/demo; đẩy các phần đó sang slide 2.

## Animation

Các slide giải thích sau hook cần animation semantic trong cơ chế chính:

- scanner chạy qua layer
- packet chạy trên route
- bar/fill/gauge đổi trạng thái
- terminal typing/output hiện thật
- traffic light bật theo reveal
- old state bị gạch, new state sáng lên

Background particles, shimmer, glow, fade, float, hoặc whole-card motion không được tính là animation semantic chính.
