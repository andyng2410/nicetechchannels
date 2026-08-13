# START_HERE

File này là entrypoint cho agent khi cần viết script.

## Thứ tự đọc

1. Đọc file này trước.
2. Đọc `SCRIPT_RULES.md`.
3. Nếu bài thuộc một dạng quen như repo/tool, benchmark/model, demo video, X/source, hoặc phân tích fact-check, đọc `SCRIPT_PATTERNS.md` để chọn trục kể.
4. Nếu user chỉ rõ một giọng viết / persona, đọc `STYLE_INDEX.md`.
5. Từ `STYLE_INDEX.md`, chỉ mở **1 file style phù hợp nhất**. Chỉ mở file thứ hai nếu thật sự cần pha trộn.

## Mục tiêu của thư mục này

- Giúp agent viết script theo kiểu **văn nói tiếng Việt, dễ hiểu, cuốn, không robotic**.
- Giúp agent chọn đúng giọng viết theo từng loại nội dung.
- Giảm chuyện đọc quá nhiều file lan man rồi viết ra một bản script bị loãng.

## Cách dùng đúng

- `SCRIPT_RULES.md` là luật gốc, luôn ưu tiên hơn style cá nhân.
- `SCRIPT_PATTERNS.md` chỉ chọn **dạng câu chuyện**: mở ở đâu, proof đặt ở đâu, slide giữa đi theo trục nào.
- File `style*.md` chỉ dùng để mượn **nhịp, giọng, cấu trúc, CTA, mức độ sắc hay mềm**.
- Không bắt chước mù. Nếu style gốc là crypto/kèo mà bài đang làm là tech explainer, chỉ mượn nhịp nói, không bê nguyên chất liệu CTA/kèo/affiliate.

## Công thức ngắn

- 70%: rõ ý, văn nói, nhịp tốt, mỗi slide một ý
- 30%: màu giọng của người được chọn

## Không làm

- Không đọc toàn bộ mọi file giọng viết rồi trộn bừa.
- Không ưu tiên bắt chước style hơn việc làm rõ ý.
- Không viết như tóm tắt bài báo.
- Không biến script thành văn AI trung tính.
