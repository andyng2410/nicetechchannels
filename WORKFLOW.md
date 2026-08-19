# Quy trình dựng NiceTechChannels slide

Đây là workflow chính thức cho agent khi dựng hoặc sửa NiceTechChannels slide. Nếu có mâu thuẫn, ưu tiên yêu cầu mới nhất của user, rule mới hơn/cụ thể hơn, `AGENTS.md`, starter hiện tại, và kết quả `validate_slide.py`.

## 0. Defaults

- Deck mới copy từ `template/nicetechchannels-slide-starter`.
- Starter có sẵn **outro slide cố định** (slide cuối, marker `data-outro`): giữ nguyên DOM/CSS/copy/animation của nó, và dòng CUỐI của `script-90s.txt` phải là nguyên văn câu outro (chi tiết trong `TEMPLATE_RULES.md` của starter). Outro được miễn visual-first gate, adjacent-slide variation và color-diversity — nó cố tình giống nhau ở mọi deck. Checkbox Outro ở trang render theo cùng logic với Logo/Brand: bỏ tick = không có outro (deck có outro slide sẽ bị CẮT khỏi video qua `--skip-outro-slide`); tick không upload = dùng outro slide của deck (deck cũ chưa có outro slide thì không nối gì — `outro.mp4` mẫu đã bỏ khỏi luồng mặc định); tick + upload file = video upload THAY THẾ outro slide. Tên kênh/tagline trong outro, handle overlay, logo và câu voiceover outro lấy theo `config/branding.json` nếu có (mặc định NiceTechChannels; câu outro tự sinh theo tên trừ khi đặt `outro_line`; field `logo` trỏ tới file logo thay thế — copy vào deck GHI ĐÈ `logo-nicetechchannels.ico`, giữ nguyên tên file). Source of truth trong code là module `branding.py`, không hardcode tên kênh chỗ khác. Server chạy trong Docker: sau khi sửa config phải `docker compose cp config/branding.json nicetechchannels:/app/config/` rồi restart container (config/ trong container là volume giữ OAuth token, KHÔNG bind mount đè).
- Không start `web_server.py` trừ khi user yêu cầu.
- Dùng `.venv/bin/python` cho Python.
- Giữ starter defaults: grid off, `backgroundFx: "particles"`, subtitle `fontSize: 18`, `bottom: 172`, `maxLines: 1`, BGM custom `preview-assets/bgm/meta.mp3`.
- Khi tạo deck mới, phải copy cả file `preview-assets/bgm/meta.mp3` từ starter. Không chỉ copy đường dẫn trong `preview-settings.json`/`app.js`; thiếu file BGM là lỗi bàn giao.
- Video demo/source khi chèn vào slide mặc định phải tắt âm (`muted`) để không đè voiceover và BGM. Chỉ bật audio gốc khi âm thanh là nội dung chính và user duyệt rõ; nếu bật audio gốc thì tránh để BGM đè.
- Safezone dọc: `padding: 100px 28px 200px`; không đặt text/metric/CTA quan trọng ngoài vùng này.
- Ảnh/video nguồn phải dùng file local, giữ trọn frame và đúng tỷ lệ (`object-fit: contain`). Container/frame phải khớp aspect ratio của asset hoặc scale media đúng full width trong safezone; không để lộ nền/viền đen hai bên hoặc trên dưới, trừ khi black bars đã nằm trong file gốc hoặc user duyệt rõ. Chỉ crop khi user yêu cầu rõ.
- **Tie-breaker media-first:** khi ảnh/video nguồn là proof chính, ưu tiên đọc rõ trên khung `390×693` trước khi lấp đầy safezone. Cho media chiếm **full width safezone** khi có thể; không thu nhỏ media chỉ để nhét thêm text/visual phụ.
- **Không overlay lên ảnh/video nguồn:** không scan line, badge, caption, chip, gradient hay pseudo-element che lên khung media. Chú thích nguồn (`Source: @…`, `demo ×N`…) đặt **dưới** ảnh/video, không chồng lên. Semantic animation trên slide media-first dùng element **ngoài** khung (chip rail, metric, pipeline…) — không scrim/animate trực tiếp lên media.
- Nếu ảnh/video đã chiếm nhiều safezone khiến visual reveal khác nhỏ hoặc khó hiểu, tách reveal: reveal ảnh giữ media rõ ràng, reveal sau ẩn ảnh và dùng full safezone cho custom scene/animation minh họa.
- Nếu preview vẫn hiện starter, kiểm tra server/source root bằng `/api/health` và HTML đang serve trước khi sửa cache/server.

### Link Autopilot

Khi user gửi một hoặc nhiều đường link để làm nội dung slide, hoặc chỉ gửi link mà không nêu mục đích khác, mặc định coi đó là yêu cầu **dựng slide hoàn chỉnh**. Không dừng lại để hỏi chọn tone, duyệt script hay duyệt visual plan.

Trước khi làm, agent phải đọc kỹ toàn bộ `WORKFLOW.md` và các skill/rule được workflow gọi tới. Sau đó tự chạy trọn luồng:

1. Đọc source gốc và tạo project slug phù hợp.
2. Thu source bằng `source-assets`; nếu là X/Twitter thì chạy `x-sources` trước. Lưu facts, visual assets local và inventory `source/source.md`.
3. Tự chọn một narrative và tone có bằng chứng tốt nhất; viết thẳng `script-90s.txt`, không đưa 5 bản để user chọn.
4. Tạo `visual-plan.md`, ghi `Status: AUTO-APPROVED`, tự chốt mapping và visual theo visual-first gate.
5. Copy starter/canonical hero, dựng đủ DOM/CSS/animation và đồng bộ script/config theo workflow.
6. Chạy validator, capture toàn bộ slide/reveal, xem ảnh và preview động, tự sửa cho đến khi các gate bàn giao PASS.
7. Chỉ báo user khi đã có deck hoàn chỉnh và bằng chứng QA; không biến bước duyệt script/visual thành điểm dừng.

Link Autopilot không kích hoạt nếu user nói rõ mục đích khác như chỉ tóm tắt, phân tích hoặc lưu source. Chỉ dừng hỏi khi source không truy cập được, thiếu dữ kiện làm thay đổi bản chất câu chuyện, hoặc có quyết định rủi ro cao về claim, quyền dùng asset, chi phí hay hành động không thể hoàn tác. Không tự tạo audio trả phí hoặc dùng ElevenLabs `--force`.

Chế độ này cũng được dashboard kích hoạt headless qua `codex exec` (mục "Tạo slide mới từ link"): khi chạy từ dashboard, QA capture ghi vào `slide/<project>/qa/` và tuyệt đối không render video — user duyệt ảnh QA rồi tự bấm render.

## 1. Source trước

Trước khi viết script hoặc sửa DOM cho source bên ngoài:

1. Tạo `slide/<project>/source/`.
2. Với mọi nguồn ngoài, dùng `source-assets`; lưu source gốc, link, facts chính, visual assets local, và `source/source.md` inventory.
3. Với X/Twitter, dùng thêm `x-sources`: `bird thread` + **`bird read --json-full`** (tải ảnh post/article từ `tweet-full.json`), rồi hoàn tất bằng checklist `source-assets`.
4. Nếu nguồn có nhiều video liên quan từ cùng tác giả/thread, tải và review đủ video cần dùng.

`source/source.md` phải phân biệt fact từ nguồn với góc nhìn/bình luận, đồng thời liệt kê từng visual asset: đường dẫn local, URL gốc nếu có, nội dung asset, và slide/ý nên dùng.

Hai check bắt buộc khi thu source:

- **Asset phải render được:** kiểm tra file type thật của logo/media (`file <path>` hoặc mở xem) trước khi đưa vào plan/DOM. File `.svg` nhưng ruột là ICO/binary, logo fill đen trên nền tối… là lỗi chỉ lộ ra ở screenshot — bắt sớm từ bước source.
- **Claim tiền/quota/promo phải đọc trang gốc:** với pricing, usage limit, khuyến mãi, cửa sổ miễn phí… phải mở đúng trang help center/blog gốc (không chỉ tweet) và ghi **cơ chế** vào `source.md`: ai được dùng, cái gì vẫn trừ quota, trả thêm khi nào, sau deadline thì sao.

## 2. Script chốt trước DOM

Trước khi viết hoặc sửa `script-90s.txt`, đọc:

- `script-writing/START_HERE.md`
- `script-writing/SCRIPT_RULES.md`
- `script-writing/STYLE_INDEX.md`
- style files liên quan nếu cần chọn tone

Nếu user chưa chốt script/tone, đưa thường 5 bản `script-90s` đầy đủ để chọn. Khi user chọn, chốt final vào `script-90s.txt` trước khi dựng DOM/CSS. Riêng Link Autopilot, agent tự chọn một bản và viết thẳng file.

**Ngoài Link Autopilot, trình script cho user bằng bảng gọn** — không paste block text dài nếu có thể tránh:

Chọn tone (5 bản):

| Bản | Style | Hook (slide 1) |
| --- | --- | --- |
| 1 | … | … |
| … | … | … |

Chốt script (1 bản):

| Slide | Voiceover | Reveals |
| --- | --- | ---: |
| 1 | … | 1 |
| 2 | … | n |

Quy tắc bảng script:
- **Voiceover:** paste đúng lời sẽ vào `script-90s.txt` (1 dòng script = 1 ô).
- **Reveals:** số câu trong dòng = số reveal.
- Sau khi user chốt, ghi file `script-90s.txt`; bảng trong chat chỉ để duyệt nhanh. Link Autopilot viết file trực tiếp.
- Không cần tạo hoặc viết tay `upload-metadata.json` khi dựng deck; Upload Center/server sẽ tự sinh metadata khi cần.
- Không tạo, sửa tay hay xoá `cost-ledger.jsonl` trong project; hệ thống tự ghi chi phí (token Codex, ký tự TTS, thời gian render) vào đó — xem báo cáo bằng `python3 cost_report.py slide/<project>`.

**Khi user yêu cầu chốt script và visual plan một hướng** (`chốt script và visual`, `gửi qua đây mình chốt`, `chốt lại và gửi qua đây`, hoặc tương đương):

- Response đầu tiên phải paste **cả hai bảng trong chat** để user xem ngay:
  1. `Slide | Voiceover | Reveals`
  2. `Slide | Nội dung voice | Reveals | Visual`
- Dù agent chỉ chọn một hướng narrative đề xuất, vẫn phải trình đủ hai bảng để user duyệt.
- Không chỉ ghi file, không chỉ nói đã chốt, và không bắt đầu DOM/CSS trước khi user approve, trừ Link Autopilot hoặc khi user nói rõ `làm luôn`, `tự chốt`, hoặc bỏ qua review.
- Nếu user đang đọc trên điện thoại, giữ bảng gọn: voiceover đúng lời nhưng không thêm giải thích dài ngoài bảng.

Script chuẩn:

- Mỗi dòng = 1 slide.
- Số câu trong dòng = số reveal units.
- Slide 1: một câu hook vừa, mạnh, hiểu ngay.
- Các slide giải thích: thường 3-4 câu ngắn/vừa; câu đầu là visual beat ngắn.
- Không nén mọi ý thành một câu dài chỉ để dễ mapping.
- Giọng Việt tự nhiên, không robotic. Giữ tiếng Anh cho tên riêng/thuật ngữ khi dịch ra khó hiểu hơn.
- Không dùng dấu gạch ngang dài `—` trong `script-90s.txt` hoặc `slideScripts`; dùng dấu phẩy, dấu hai chấm, hoặc tách câu ngắn để TTS đọc tự nhiên hơn.
- **Câu về tiền/quota/promo phải tự giải thích cơ chế:** nói rõ ai trả gì, cái gì vẫn trừ quota, hết hạn thì sao. Không dùng "miễn phí" / "không tính thêm" trần nếu thực tế vẫn trừ quota — người xem sẽ hiểu nhầm thành bonus. Nếu một câu phải ôm cả điều kiện lẫn ngoại lệ, tách thành 2-3 câu ngắn theo nhịp: luật mặc định → cửa sổ promo → hết promo thì sao.

## 3. Visual plan chốt trước DOM

Sau khi `script-90s.txt` đã final, **trước** khi sửa `index.html`/`style.css`:

1. Đọc `skills/slide-visuals/SKILL.md`.
2. Tạo hoặc cập nhật `slide/<project>/visual-plan.md`.
3. Trình user **chốt visual plan** trước khi code slide; với Link Autopilot, tự đánh dấu `AUTO-APPROVED` và đi tiếp.

Không bắt đầu DOM/CSS cho deck mới hoặc deck đổi script lớn cho đến khi user chốt plan — trừ Link Autopilot hoặc khi user yêu cầu bỏ qua bước này.

`visual-plan.md` là bản mapping DOM/reveal để user duyệt, hoặc để agent tự chốt trong Link Autopilot.

Mỗi slide phải có:

| Trường | Nội dung |
| --- | --- |
| Voice (tóm) | Ý chính của dòng script tương ứng |
| Reveals | Số câu = số reveal unit |
| Source asset | File local dùng trên canvas, hoặc `custom scene` |
| Scene | Mô tả ngắn layout chính trong safezone |
| Semantic animation | Động từ có nghĩa (`route`, `unlock`, `fill`, `compare`…) — không chỉ fade/glow |
| Reveal ↔ câu | Câu nào kích hoạt element/state nào |
| Phone-density | Custom thay thế nếu asset gốc khó đọc phone |

Slide 1 thêm:

| Trường | Nội dung |
| --- | --- |
| Slide 1 template | Canonical hero nào (source-image / logo / GitHub repo) |
| Slide 1 copied from | Đường dẫn canonical template thật đã copy DOM/CSS/assets |
| Allowed replacements | Chỉ các phần được thay: text, logo/avatar/media/source, và asset path tương ứng |
| Intentional deviations | `none` nếu không có; mọi đổi layout/background/style/effect phải ghi rõ để user duyệt |

Slide 2 trở đi phải thêm:

| Trường | Nội dung |
| --- | --- |
| Scene primitive | Dạng scene chính: `map`, `route/path`, `gauge`, `field`, `orbit`, `gate`, `timeline`, `funnel`, `terminal/source proof`... |
| Creative angle | Cách visual biến ý thành cơ chế/hình ảnh riêng, không chỉ xếp lại lời đọc thành box |
| Color roles | Vai trò màu chính: source/system, success/forward, warning/opportunity, risk/attention, neutral/background |
| Adjacent-slide variation | Slide này khác slide trước ở shape, motion hoặc palette thế nào |
| Motion/animation illustration | Element nào di chuyển/biến đổi, theo reveal nào, để người xem hiểu cơ chế gì |
| Card/text-box check | Nếu có 2+ box/card, nói rõ đó là artifact gì; nếu chỉ là narration card thì phải đổi thành scene |

**Rule phone-first khi lập plan:** asset nào preview/thumbnail ở khung `390×693` mà chữ nhỏ, diagram dày, banner ngang phải thu nhỏ quá mức, hoặc chi tiết không đọc được trên điện thoại → **không đưa vào cột Visual của bảng plan**. Chỉ dùng `Custom …` thay thế. Asset loại vẫn có thể lưu trong `source/` + ghi ở `source/source.md` inventory, nhưng không xuất hiện như lựa chọn visual trong plan.

**Visual-first gate cho slide 2 trở đi (trừ slide outro `data-outro` — giữ nguyên từ starter, không cần gate):** trước DOM/CSS, mỗi slide phải pass đủ 4 ý: scene primitive cụ thể, motion/animation minh hoạ trong main visual, role màu + khác slide liền trước, và anti text-box/card-stack. Định nghĩa chi tiết và ví dụ nằm trong `skills/slide-visuals/SKILL.md`; nếu plan fail gate nào thì sửa plan trước khi code.

Cuối file thêm:

- **Assets loại:** diagram/banner blog quá nhỏ, hotlink, video chưa tải local…
- **Gallery tham chiếu:** pattern copy/remix từ `template/visual-pattern-gallery/` nếu có
- **Trạng thái:** `DRAFT` → user chốt → `APPROVED`; Link Autopilot dùng `AUTO-APPROVED`

Ngoài Link Autopilot, khi báo cho user, **ưu tiên bảng gọn** trong chat để chốt nhanh; lưu chi tiết đầy đủ trong `visual-plan.md`. User sửa plan thì cập nhật file trước, rồi mới code DOM.

**Bảng chốt nhanh (bắt buộc paste cho user, trừ Link Autopilot):**

| Slide | Nội dung voice | Reveals | Visual |
| --- | --- | ---: | --- |
| 1 | … | 1 | asset hoặc custom — ghi ngắn |
| 2 | … | n | … |

Quy tắc bảng:
- **Nội dung voice:** 1 cụm ngắn, không paste cả câu script.
- **Visual:** chỉ asset **đọc được trên phone** hoặc `Custom …`. Không liệt kê diagram/banner khó xem rồi ghi “không dùng” — loại hẳn khỏi cột Visual.
- Footnote **Đã loại khỏi plan (phone):** liệt kê file không dùng + lý do ngắn (optional, 1 dòng).
- User reply `chốt visual plan` / sửa ô nào → cập nhật `visual-plan.md` + đổi Status `APPROVED` rồi mới DOM. Với Link Autopilot, agent tự chốt `AUTO-APPROVED` và không dừng ở bảng này.

Mẫu file đầy đủ (`visual-plan.md`):

```markdown
# Visual plan — <project>

Status: DRAFT | APPROVED | AUTO-APPROVED
Script: script-90s.txt (Style …)
Slide 1 template: template/googleaistudio-post-… (source-image hero)

## Slide 1
- Voice: …
- Reveals: 1
- Asset: source/image-00-hero.png
- Scene: fixed canonical hero, chỉ thay text/logo/media/source
- Copied from: template/googleaistudio-post-…
- Allowed replacements: text, logo/media/source asset path
- Intentional deviations: none
- Semantic animation: hiệu ứng hero có sẵn trong template
- Reveal map: C1 → …
- Phone-density: không nhét proof/metric dày vào hero

## Slide 2
- Voice: …
- Reveals: …
- Source asset: …
- Scene: …
- Scene primitive: …
- Creative angle: …
- Color roles: …
- Adjacent-slide variation: …
- Semantic animation: …
- Motion/animation illustration: …
- Reveal map: C1 → …
- Phone-density: …
- Card/text-box check: …

## Assets excluded (phone)
- source/image-03-….png — flowchart chữ nhỏ; thay bằng custom pipeline
```

## 4. Làm visual

Trước khi sửa `index.html`/`style.css`, visual plan phải là `APPROVED` hoặc `AUTO-APPROVED` (Bước 3). Implement theo plan đã chốt; nếu lệch plan phải cập nhật file và báo user trước khi handoff.

`slide-visuals` là source of truth cho visual rules và QA; `template/visual-pattern-gallery/` là index tham chiếu cho mẫu hero, typography, density, màu, và animation.

- Slide 1 implementation phải bắt đầu bằng cách copy DOM/CSS/assets từ canonical template thật. Không recreate lại bằng mô tả hoặc viết một hero "giống giống".
- Slide 1 copy nguyên slide 1 từ canonical template phù hợp, rồi chỉ thay text/logo/media/source. Không tự dựng lại, không đổi layout/nền/style/effect của hero.
- Canonical slide 1: GitHub repo dùng `template/openmontage-github-trending/`; source-image dùng `template/googleaistudio-post-2069450021955592406/`; logo/avatar dùng `template/kimi-moonshot-post-2066467110960959833/` hoặc `template/addyosmani-loop-engineering/`.
- Trước khi sửa nội dung slide 1, ghi rõ trong `visual-plan.md`: `Copied from`, `Allowed replacements`, và `Intentional deviations`. Mặc định `Intentional deviations: none`; mọi deviation phải được user duyệt trước khi handoff.
- Khi QA slide 1, so screenshot với canonical template tương ứng. Unapproved deviation về layout, background, typography, orbit/card placement, animation/effect, hoặc hero density là lỗi dù nội dung đúng.
- Slide 2 trở đi dùng gallery để tham khảo, copy/remix, hoặc thiết kế scene riêng theo nội dung. Implement đúng visual-first gate đã chốt trong `visual-plan.md`; nếu đổi primitive/motion/palette/card logic khi code, cập nhật plan và báo user trước handoff.
- Copy visual pattern từ gallery không được thay thế hoặc xoá `preview-assets/bgm/meta.mp3` đã copy từ starter.
- Mỗi slide có `<div class="slide-bg slide-bg-N"></div>`.
- Slide thường: reveal units = số `.slide-element`.
- `data-mode="highlight"`: reveal units = `.slide-element` + `.highlightable`.
- `data-mode="traffic-light"`: reveal units = `.slide-element` + `.lightable`.
- Mỗi reveal phải khớp semantic với câu voiceover tương ứng.
- Slide 1 headline mặc định giữ cỡ OpenMontage/GitHub repo hero khoảng `42px` trên khung `390x693`; chỉ giảm khi title thật sự tràn/overlap sau khi kiểm tra.
- Typography/color/density mặc định theo `template/visual-pattern-gallery/` và chuẩn Alex: chữ lớn dễ đọc, màu có vai trò rõ, visual chính chiếm gần hết safezone. Chữ nhỏ, màu một nốt, hoặc safezone rỗng là lỗi phải sửa.
- Visual phải đa dạng màu có chủ đích trên toàn deck. Tránh để contact sheet đọc như một tone màu; dùng các màu theo vai trò rõ ràng như source/system, success/forward, warning/opportunity, risk/attention, và đổi hue giữa các nhóm slide khi nội dung đổi.
- Các slide sau hook vẫn phải tuân thủ cứng: chữ đủ lớn trên điện thoại, màu phân vai rõ, visual chiếm gần hết safezone, và animation semantic nằm trong cơ chế chính của scene. Static/fade-only explanatory slides là lỗi. Với slide media-first, áp dụng tie-breaker ở phần Defaults: media rõ trước, scene minh họa tách reveal sau nếu cần.
- Vì đã có phụ đề, hạn chế chữ trên canvas: dùng label/metric/prompt ngắn, icon, source artifact và motion có nghĩa. Có thể gộp nhiều phần visual trong một reveal rồi cho xuất hiện/chạy tuần tự trong cùng safezone thay vì rải thành cụm nhỏ rời rạc.
- Trước khi xem là xong DOM, tự làm squint test trên slide: nếu ấn tượng đầu tiên là stack/grid text box thay vì một cơ chế, route, comparison hoặc state change, slide fail dù validator PASS.
- Append CSS custom ở cuối `style.css`.
- Với animation semantic, ưu tiên animate child/pseudo-element (`packet`, `scanner`, `fill`, `curve`, `bus`, `cursor`) thay vì animate cả card/container.
- Dùng biến theme (`--primary`, `--accent`, `--success`) khi hợp lý.
- Nếu dùng counter/progress động, kiểm tra reset state trong `app.js`.
- **Starter `.slide-element` mặc định layout dọc/căn giữa.** Custom scene cần hàng ngang bên trong một `.slide-element` (timeline node, cặp nút, icon + text) phải override rõ: `.x-content .slide-element.x-row { display: flex !important; flex-direction: row !important; }`. Không override thì element sẽ âm thầm xếp dọc — lỗi chỉ thấy ở screenshot.
- **Budget chiều cao khi thiết kế:** safezone thực chỉ ~393px; validator đo union các `.slide-element` (heading ngoài `.slide-element` vẫn chiếm chỗ đẩy nội dung xuống). Slide 3 reveal nên nhắm tổng nội dung ≤ ~380px từ đầu; scene head nên gộp kicker + title một hàng ngang để tiết kiệm dọc.
- Validate sớm ngay sau khi dựng xong 1-2 slide đầu, đừng đợi dựng hết deck mới chạy lần đầu.

## 5. Validate và QA

Chạy bắt buộc:

```bash
.venv/bin/python validate_slide.py slide/<project> --semantic-report
```

Không bàn giao bằng `--skip-safezone`.

Sau PASS, chụp QA bằng helper có sẵn (đã ẩn side panels, bật đủ reveal/highlight/light):

```bash
.venv/bin/python capture_slides.py slide/<project>
# ảnh ra /tmp/nicetechchannels-qa/<project>/slideN.png
```

Mở từng ảnh và kiểm tra:

- mapping script/slide/reveal đúng
- safezone PASS
- slide 1 copy check: screenshot giữ đúng layout/background/style/effect của canonical template; mọi deviation phải có trong `visual-plan.md` và đã được user duyệt
- không overlap, text đọc được trên điện thoại
- ảnh/video nguồn không bị overlay/caption chồng lên khung media, không lộ viền đen do container sai tỉ lệ
- visual không quá nhỏ, không rỗng giữa slide
- deck không bị một-tone màu; các nhóm slide có palette/role color khác nhau nhưng vẫn đọc rõ
- không giống danh sách card/text box
- contact-sheet squint/color pass: nhìn nhỏ vẫn thấy mỗi slide là một scene khác nhau, không phải lặp lại card stack hoặc một palette đơn điệu
- outro slide (`data-outro`): giữ nguyên từ starter là PASS — outro giống hệt giữa các deck và lệch palette với phần nội dung KHÔNG phải lỗi, đừng "sửa" nó
- motion/animation pass: xem preview động slide 2 trở đi; mỗi slide phải có motion minh hoạ trong main visual, không chỉ fade/reveal/background/shimmer/glow/float
- xem preview động vài giây cho các slide giải thích

Khi báo xong cho user, ghi rõ: validate PASS, mapping PASS, safezone PASS, semantic 1:1 đã rà.
