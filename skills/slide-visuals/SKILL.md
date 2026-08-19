---
name: slide-visuals
description: Thiết kế visual-first và animation semantic cho NiceTechChannels HTML slide decks. Dùng khi Agents cần lập visual plan, dựng hoặc polish index.html/style.css, biến script thành scene/đồ hoạ/animation, tránh text-box layouts, copy slide 1 hero template cố định, tham khảo/copy/remix pattern từ template/visual-pattern-gallery cho slide sau, hoặc QA visual density/safezone/motion cho slide.
---

# Slide Visuals

Dùng skill này trước khi sửa `index.html` hoặc `style.css` cho một deck NiceTechChannels. Mục tiêu là biến script thành visual scene có animation mang nghĩa, không chép voiceover thành text card dài.

## 1. Source of truth

`template/visual-pattern-gallery/` là index tham chiếu cho visual/animation. Slide 1 dùng canonical template folder tương ứng, không tự dựng lại.

Trước khi code:

1. Mở `template/visual-pattern-gallery/TEMPLATE_RULES.md`.
2. Slide 1: copy nguyên slide 1 từ canonical template, rồi chỉ thay text/logo/media/source.
3. Slide 2 trở đi: dùng gallery làm tham chiếu; có thể copy, remix hoặc thiết kế scene riêng theo nội dung voiceover.
4. Nếu copy pattern cho slide sau, bắt đầu từ code mẫu rồi sửa theo nội dung.
5. Nếu làm custom slide, vẫn phải đạt typography, color-role, density, safezone và semantic animation.

Nếu có mâu thuẫn, ưu tiên yêu cầu mới nhất của user, `AGENTS.md`, `WORKFLOW.md`, gallery template đang chạy, và kết quả `validate_slide.py`.

## 2. Visual plan bắt buộc

Sau khi `script-90s.txt` final, lưu plan vào `slide/<project>/visual-plan.md` theo `WORKFLOW.md` §3. Trình user bảng gọn 4 cột. **Không đưa ảnh/diagram khó đọc trên phone vào cột Visual** — chỉ custom scene thay thế; asset loại ghi inventory/`Assets excluded`, không liệt kê như option trong plan.

Trước khi code, viết plan ngắn. Slide 1 chỉ cần hero template fields; slide 2 trở đi phải có đủ visual-first gate.

```text
Slide 1
- voice idea:
- source asset:
- template pattern:
- copied from:
- allowed replacements:
- intentional deviations:
- scene:
- semantic animation:
- reveal/state change:
- phone-density fix:

Slide 2+
- voice idea:
- source asset:
- template pattern:
- scene:
- scene primitive:
- creative angle:
- color roles:
- adjacent-slide variation:
- semantic animation:
- motion/animation illustration:
- reveal/state change:
- phone-density fix:
- card/text-box check:
```

Plan slide 2+ chưa đạt nếu: `semantic animation` chỉ là fade/scale/glow/background, thiếu `motion/animation illustration`, hoặc các field `scene primitive`, `creative angle`, `color roles`, `card/text-box check` còn chung chung. Motion phải là minh hoạ có nghĩa trong main visual: nói rõ element nào di chuyển/biến đổi, theo reveal nào, và nó giải thích cơ chế gì.

## 3. Design constraints trước khi code

Thiết kế layout ngay từ đầu để tránh các lỗi này:

- Visual chính đủ lớn trên khung `390x693`; không để icon/source artifact/metric quan trọng quá nhỏ.
- Dùng gần hết safezone như canvas thật; dead space lớn là lỗi.
- Text/label quan trọng không dưới khoảng 11-12px; scene title, metric label, node name phải đọc được trên điện thoại.
- Metric lớn không che label; tách label sang vùng riêng hoặc đặt trên/dưới số.
- Slide không được đọc như list text/card; card chỉ dùng khi là artifact có nghĩa.
- Nếu có 2+ box/card không liên quan bằng một cơ chế chung, slide fail. Rewrite thành một integrated scene như benchmark map, MoE router field, reliability gauge, quota gate, decision path, funnel hoặc timeline.
- Canvas text chỉ là label/metric/command/source tag. Không nén narration thành các card.
- Animation phải nằm trong cơ chế chính của scene, không chỉ trang trí.
- Slide 2 trở đi bắt buộc có motion/animation minh hoạ. Static explanatory slide là lỗi, kể cả khi layout đẹp.
- Motion hợp lệ: packet/beam/line route, gauge sweep, bar fill, scanner, token/data stream, branch/merge, unlock gate, timeline advance, chart compare, source video chứng minh workflow. Motion không hợp lệ: fade-in, scale-in, float, shimmer, glow, background particles, hoặc whole-card bob.
- Final state sau khi reveal hết phải tự giải thích được: nhìn ảnh cuối vẫn hiểu ý chính trước khi đọc subtitle.
- Sáng tạo là yêu cầu, không phải bonus: mỗi slide giải thích cần một góc visual riêng thể hiện bằng shape, route, scale, motion hoặc metaphor cụ thể.
- Màu phải có role rõ. Trước khi code, chọn source/system, success/forward, warning/opportunity, risk/attention và neutral/background cho slide.

Nếu plan có nguy cơ vi phạm một lỗi trên, sửa plan trước rồi mới code.

## 4. Chọn mẫu từ gallery

Dùng `template/visual-pattern-gallery/TEMPLATE_RULES.md` làm index chính. Quy tắc nhanh:

- Slide 1 hero: chọn đúng một mẫu hero, copy trước rồi thay nội dung.
- Slide 2 trở đi: dùng gallery như thư viện ý tưởng và code mẫu; khuyến khích sáng tạo scene riêng nếu nội dung cần cách minh hoạ khác.
- Demo/source proof: media thật chiếm phần lớn safezone, full-frame, `object-fit: contain`; frame/container phải khớp aspect ratio của asset hoặc scale media đúng full width trong safezone. Không để lộ pillarbox/letterbox đen từ nền slide, trừ khi black bars nằm trong file gốc hoặc user duyệt rõ. Source tag/chú thích đặt **dưới** khung media — **không overlay** (scan line, badge, caption, gradient) lên ảnh/video. Nếu còn trống thì thêm logo/avatar, metric, keyword hoặc proof chip **bên ngoài** khung media.
- Repo/dev tool: terminal, command, workflow, package flow, file tree, PR/build surface.
- AI/model/benchmark: model badge, leaderboard/chart, token lane, memory bus, compression scene, perf bars.
- Quy trình nhiều bước: pipeline, route, gate, fanout, branch/merge, packet flow.
- Rủi ro/giới hạn: traffic-light, lock/gate, warning state, crossed-out old state.
- Business/social proof: source screenshot, revenue scale, payer path, distribution funnel, evidence lab.
- Kết luận: final lockup/thesis scene, không thêm paragraph dài.

Vary adjacent slides: không dùng hai slide liền nhau trông như cùng một card stack.

Vary shape and palette: hai slide giải thích liền nhau không nên cùng một layout hộp, cùng một mật độ, cùng một palette. Ít nhất một trong ba thứ phải đổi rõ: scene primitive, motion chính, hoặc role color nổi bật.

## 5. Slide 1 rules

Slide 1 có ba nhóm mẫu copyable trong gallery:

- Source-image hero: ảnh/screenshot/source artifact là bằng chứng chính.
- Logo/avatar hero: người, tổ chức, model, product hoặc brand identity là hook.
- GitHub repo hero: repo GitHub hoặc GitHub Trending.

Nguyên tắc bắt buộc:

- Không tự dựng lại slide 1 từ mô tả. Copy nguyên slide 1 từ canonical template folder rồi thay text/logo/media/source.
- Canonical templates: GitHub repo dùng `template/openmontage-github-trending/`; source-image dùng `template/googleaistudio-post-2069450021955592406/`; logo/avatar dùng `template/kimi-moonshot-post-2066467110960959833/` hoặc `template/addyosmani-loop-engineering/`.
- Implementation phải bắt đầu từ DOM/CSS/assets thật của canonical template. Không recreate một layout gần giống bằng mô tả.
- Visual plan phải ghi `copied from`, `allowed replacements`, và `intentional deviations`. Mặc định `intentional deviations: none`.
- Chỉ thay nội dung cần thay; không đổi layout, nền, style hero, hoặc tự làm lại hiệu ứng của mẫu.
- Nếu cần đổi layout/background/style/effect/placement/density của slide 1, ghi deviation trong plan và chờ user duyệt. Không âm thầm chỉnh.
- H1 mặc định dùng shimmer (`title-shimmer` hoặc biến thể tương đương).
- Không áp shimmer lan sang video, source media, logo, metric phụ, hoặc element khác nếu không cần nhấn.
- H1 mặc định giữ cỡ OpenMontage/GitHub repo hero: khoảng `42px` trên khung `390x693`.
- Không tự thu nhỏ H1 chỉ vì title hơi dài; ưu tiên wrap cân đối hoặc mở rộng max-width trong safezone. Chỉ giảm size khi đã kiểm tra và vẫn tràn/overlap.
- Không đưa nhiều metric, demo video, feature grid, hoặc mô tả dài vào slide 1. Stars/demo/proof để slide 2.

## 6. Typography và màu

Lấy `slide/alex-nguyen-ai-apps/` làm chuẩn tham chiếu mặc định cho phone-scale typography và color balance, trừ khi brand/source có hệ màu rõ hơn.

- Các slide sau hook được phép sáng tạo layout/visual, nhưng không được phá chuẩn hard rule: chữ đủ lớn, màu có vai trò rõ, visual chính chiếm gần hết safezone.
- Hero/title chính mặc định khoảng `42px`; metric lớn có thể 42-51px.
- Scene title/kicker quan trọng thường 13-20px.
- Label/node/axis quan trọng nên khoảng 11-15px.
- Body ngắn trong artifact/card nên khoảng 12-15px, line-height thoáng.
- Giữ letter-spacing bằng 0 cho text thường; chỉ dùng spacing nhẹ cho tag/kicker uppercase rất ngắn.
- Dùng màu theo vai trò: cyan cho hệ thống/flow/source; xanh lá cho success/money/forward; cam/vàng cho opportunity/warning; đỏ/magenta cho risk/attention.
- Không để cả deck hoặc contact sheet thành một tone màu. Mỗi nhóm slide nên có palette/role color khác nhau theo nội dung, nhưng vẫn giữ tương phản cao và đọc rõ trên điện thoại.
- Ngoại lệ: slide outro cố định (marker `data-outro`, copy từ starter) được miễn visual-first gate, adjacent-slide variation và color-diversity — giữ nguyên DOM/CSS/copy của starter, không redesign theo deck.
- Visual plan phải ghi `color roles`; DOM/CSS phải thể hiện đúng các role đó, không chỉ đổi màu nền nhẹ.

## 7. Animation semantic

Animation tốt phải làm người xem hiểu cơ chế:

- `scan`: quét layer/source/evidence.
- `route`: đường đi đổi nhánh, packet chạy sang node khác.
- `compress`: khối dữ liệu bị nén, memory/file size đổi trạng thái.
- `compare`: bar/scale/gauge tăng giảm theo số liệu.
- `unlock`: gate/lock mở khi đủ điều kiện.
- `branch/merge`: pipeline tách nhánh rồi nhập kết quả.
- `type`: terminal command gõ thật, output hiện theo reveal.
- `strike`: trạng thái cũ bị gạch, trạng thái mới sáng lên.

Ưu tiên animate child/pseudo-element như `packet`, `scanner`, `fill`, `bar`, `cursor`, `bus`, `gate`, `line`, `token`; không animate cả card/container để giả vờ có motion.

Slide 2 trở đi phải có ít nhất một animation semantic trong main visual. Nếu motion chỉ xảy ra ở transition/reveal entrance, slide chưa đạt. Với media-first slide, video nguồn có thể là motion chính nếu nó chứng minh workflow; nếu chỉ dùng ảnh tĩnh/source proof, thêm motion bên ngoài khung media như chip rail, route, metric fill hoặc pipeline.

## 8. DOM/CSS rules

- Giữ starter runtime và safezone của project.
- Slide 1 phải copy từ canonical template, không tự dựng lại.
- Slide 1 QA phải so screenshot với canonical template đã copy. Unapproved deviation về layout, background, typography, hero density, placement hoặc effects là lỗi.
- Slide 2 trở đi không bắt buộc copy gallery; nếu copy thì bắt đầu từ code mẫu, nếu custom thì tập trung vào visual/animation phù hợp nội dung.
- Slide 2 trở đi phải implement visual-first gate đã ghi trong visual plan, nhất là motion/animation illustration. Khi code xong, motion đó phải chạy trong preview, không chỉ tồn tại trên mô tả.
- Mỗi reveal phải khớp một câu trong `script-90s.txt`.
- Text canvas chỉ giữ keyword, metric, command, label ngắn, source tag hoặc artifact label.
- Ảnh/video nguồn: frame/container phải theo đúng aspect ratio asset hoặc full width safezone để không lộ viền đen hai bên/trên dưới; không overlay lên khung media; `source tag` / chú thích nguồn luôn nằm dưới media, không chồng lên.
- Video demo/source khi embed mặc định phải `muted` để không đè voiceover/BGM; chỉ bật audio gốc khi user duyệt rõ vì âm thanh là nội dung chính.
- Card chỉ dùng khi là artifact có nghĩa: terminal, source proof, metric, warning, pipeline node.
- Trước khi handoff, tự làm squint test: nếu nhìn nhỏ mà slide giống danh sách hộp chữ hơn là một scene/cơ chế, sửa lại.
- Append CSS custom ở cuối `style.css`; đặt tên class theo deck để tránh đụng runtime.
- Với `data-mode="highlight"`, reveal units = `.slide-element` + `.highlightable`.
- Với `data-mode="traffic-light"`, reveal units = `.slide-element` + `.lightable`.
- Nếu dùng counter/progress/bar dynamic, kiểm tra reset state trong `app.js`.
- Starter `.slide-element` mặc định xếp dọc/căn giữa. Scene cần hàng ngang bên trong một `.slide-element` (timeline node, cặp nút, icon + text) phải override rõ: `.deck-content .slide-element.deck-row { display: flex !important; flex-direction: row !important; }` — không override thì element âm thầm xếp dọc.
- Budget chiều cao: safezone thực ~393px, validator đo union các `.slide-element` (heading ngoài `.slide-element` vẫn đẩy nội dung xuống). Slide 3 reveal nhắm tổng nội dung ≤ ~380px; scene head nên gộp kicker + title một hàng ngang.
- Trạng thái cuối theo reveal muộn hơn (strike node cũ khi node mới bật…) dùng `:has()`: `.deck-scene:has(.node-late.visible) .node-early { … }`.
- Validate sớm sau 1-2 slide đầu, đừng dựng hết deck mới chạy lần đầu.

## 9. Phone-first QA

Sau khi code:

1. Chạy `.venv/bin/python validate_slide.py slide/<project> --semantic-report`.
2. Chụp tất cả slide bằng `.venv/bin/python capture_slides.py slide/<project>` (390x693, reveal hết, side panels đã ẩn); ảnh ra `/tmp/nicetechchannels-qa/<project>/`. Mở xem từng ảnh, trừ khi user nói không cần.
3. Slide 1 copy pass: so với canonical template, chỉ chấp nhận replacement đã ghi trong plan; unapproved layout/background/style/effect deviation phải sửa.
4. Xem preview động vài giây cho các slide giải thích.
5. Fix trước khi bàn giao: visual nhỏ, dead space, label dưới 11-12px, overlap, ảnh vỡ/logo chìm nền, black bars/pillarbox/letterbox do frame media sai tỉ lệ, slide giống list text/card, deck một tone màu, animation chỉ trang trí, final state không rõ.
6. Motion/animation pass: slide 2 trở đi phải có motion minh hoạ trong main visual; nếu chỉ có fade/reveal/background motion, sửa trước khi bàn giao.
7. Contact-sheet pass: adjacent explanatory slides phải khác nhau về scene primitive hoặc role color; nếu cả deck đọc như một palette hoặc một kiểu box layout, sửa trước khi bàn giao.

Khi báo kết quả, nói rõ validate/mapping/safezone/semantic motion đã kiểm chưa. Nếu bỏ qua bước nào, nói thẳng.
