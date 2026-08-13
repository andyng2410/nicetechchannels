# SCRIPT_PATTERNS

File này chọn **dạng câu chuyện** cho script. Dùng sau `SCRIPT_RULES.md`, trước khi mượn style.

Style trả lời câu hỏi: nói bằng giọng nào.
Pattern trả lời câu hỏi: kể theo đường nào để người xem hiểu và muốn xem tiếp.

## 1. Khung deck mặc định

- Slide 1: hook một câu, nói thẳng chuyện đáng xem nhất.
- Slide 2: proof, demo, source artifact, hoặc visual beat đầu tiên. Đừng để người xem chờ quá lâu mới thấy bằng chứng.
- Slide giữa: cơ chế, ví dụ, số liệu, rủi ro, hoặc cách dùng.
- Slide cuối: tóm lại, cảnh báo, hoặc góc nhìn để nhớ. Không chốt bằng khẩu hiệu rỗng.

## 2. Repo/tool GitHub

Dùng khi nguồn chính là repo, launch, GitHub trending, CLI, framework, app dev tool.

- Slide 1: tên repo/tool + lợi ích hoặc nỗi đau rõ.
- Slide 2: bằng chứng đáng tin: trending, demo, screenshot, README artifact, hoặc câu lệnh chạy được.
- Slide 3: workflow chính của tool.
- Slide 4: điểm khác biệt so với cách cũ.
- Slide 5: giới hạn thật: setup, license, API key, platform, độ chín, hoặc thứ chưa nên kỳ vọng.
- Slide 6: nên thử khi nào, bỏ qua khi nào.

Tránh biến script thành tóm tắt README. Người xem cần biết tool này thay đổi thao tác nào trong đời thật.

## 3. Benchmark/model/X

Dùng khi nguồn là X post, benchmark, AI model, leaderboard, paper, release note.

- Slide 1: kết quả lạ nhất: thứ hạng, so sánh, local/runtime, chi phí, hoặc cú lệch kỳ vọng.
- Slide 2: đưa chart, bảng, demo, hoặc artifact gốc để chứng minh.
- Slide 3: benchmark đang đo gì, vì sao đáng tin hoặc đáng nghi.
- Slide 4: cơ chế hoặc trade-off giúp kết quả đó xảy ra.
- Slide 5: điểm cần lưu ý: dữ liệu, quantization, phần cứng, prompt, benchmark gaming, hoặc khoảng cách với frontier model.
- Slide 6: tóm lại thực dụng: nên dùng để làm gì ngay bây giờ.

Nếu có nhiều model/tên riêng, slide 1 chỉ giữ những tên cần tạo tương phản. Phần giải thích để sau.

## 4. Demo/video source

Dùng khi nguồn có clip demo, screen recording, product video, hoặc video tác giả chia sẻ.

- Slide 1: nói điều người xem sắp thấy, không kể hậu trường tải video hay xử lý file.
- Slide 2: cho demo chạy sớm, đủ lâu để người xem thấy kết quả.
- Slide 3: gọi tên điều vừa xảy ra trong demo.
- Slide 4: giải thích cơ chế hoặc workflow.
- Slide 5: nói giới hạn, điều kiện chạy, hoặc điểm cần kiểm chứng.
- Slide 6: tóm lại ngắn, gắn với use case thật.

Nếu demo đã tự nói được nhiều, script chỉ cần dẫn nhịp và chốt ý. Đừng lặp lại từng chữ đang hiện trên màn hình.

Không nói các chi tiết hậu trường như clip được tải bằng công cụ nào, đã cắt bao nhiêu giây, lưu ở thư mục nào, hoặc slide đang loop ra sao.

## 5. External video/fact-check

Dùng khi lấy ý từ YouTube, Facebook, bài báo, website, hoặc clip cần kiểm chứng.

- Slide 1: mở bằng chủ thể và nghịch lý, không mở bằng `video này nói`.
- Slide 2: nêu claim phổ biến hoặc khoảnh khắc nguồn khiến câu chuyện đáng chú ý.
- Slide 3: đưa primary source hoặc số liệu thật.
- Slide 4: giải thích vì sao người xem dễ hiểu sai.
- Slide 5: phần đúng, phần sai, phần chưa đủ dữ kiện.
- Slide 6: chốt bằng cách nhìn cân bằng.

Source là bằng chứng, không phải nhân vật chính, trừ khi câu chuyện thật sự là về tác giả hoặc phản ứng của cộng đồng.

## 6. Product/update/API

Dùng khi có tính năng mới, API mới, pricing mới, workflow mới.

- Slide 1: chuyện vừa đổi và vì sao nó đáng quan tâm.
- Slide 2: demo hoặc proof của thay đổi.
- Slide 3: trước đây phải làm thế nào.
- Slide 4: bây giờ thao tác nào được rút ngắn hoặc mở ra.
- Slide 5: điều kiện dùng thật: plan, region, model, quota, SDK, hoặc migration.
- Slide 6: ai nên dùng ngay, ai nên chờ.

Đừng để script thành changelog. Luôn dịch update thành hệ quả với người dùng.

## 7. Hook tốt và hook lỗi

Hook tốt:

- `GLM 5.2 vừa thành model open-source số một trên benchmark DeepSWE của Datacurve.`
- `Google AI Studio giờ build được Android app từ prompt.`
- `Palmier Pro đang biến video editor thành nơi agent thật sự làm việc.`

Hook lỗi:

- `Trong video này mình sẽ nói về một công cụ mới...`
- `Bài này đang chia sẻ một thread khá hay về...`
- `Dành cho ai chưa biết thì hôm nay có một repo...`
- `Mình thấy cái này cũng thú vị nên làm thử một video...`

Sửa hook lỗi bằng cách bỏ lớp meta, đưa chủ thể thật lên đầu câu, rồi gắn ngay kết quả hoặc mâu thuẫn.
