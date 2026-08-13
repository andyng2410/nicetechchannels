# Source analysis

## Nguồn chính

- X: https://x.com/GoogleResearch/status/2062982001850974257
- Tác giả: Google Research
- Ngày đăng: 5/6/2026
- Bài chính thức: https://research.google/blog/unlocking-dependable-responses-with-gemini-enterprise-agent-platforms-agentic-rag/

## Điểm chính từ Google

- Google Research và Google Cloud giới thiệu Agentic RAG cho Gemini Enterprise Agent Platform.
- RAG thông thường thường tìm một lần, nên dễ trả lời thiếu khi dữ liệu nằm ở nhiều tài liệu hoặc nhiều hệ thống.
- Quy trình mới dùng nhiều agent: Root Agent điều phối, Planner lập kế hoạch, Query Rewriter viết lại truy vấn, RAG Agent tìm dữ liệu và Synthesis Agent tạo câu trả lời.
- Thành phần khác biệt là Sufficient Context Agent. Agent này kiểm tra các đoạn dữ liệu, bản nháp và phần còn thiếu trước khi cho phép tạo câu trả lời cuối.
- Nếu dữ liệu chưa đủ, hệ thống ghi rõ phần còn thiếu, viết lại truy vấn và tìm tiếp.
- Google công bố độ chính xác trên các bộ dữ liệu factuality tăng tối đa 34% so với RAG thông thường.
- Trên FramesQA gồm 824 câu hỏi và 2.676 tài liệu PDF, cấu hình cross-corpus chọn giữa bốn kho dữ liệu đạt 90,1% câu trả lời đúng.
- Độ trễ trung bình của cấu hình single-corpus và cross-corpus chênh lệch trong khoảng 3%.
- Tính năng hiện ở public preview trong Gemini Enterprise Agent Platform.

## Video

- File local: `x-2062981484861140992.mp4`
- Thời lượng: 21,466 giây.
- Video minh họa luồng từ câu hỏi người dùng tới Root Agent, Planner và Query Rewriter, tìm kiếm trên Docs, MCPs và Code, kiểm tra đủ ngữ cảnh, lặp lại nếu còn thiếu rồi mới chuyển sang Synthesis Agent.

## Phản ứng cộng đồng

- Phản ứng tích cực tập trung vào khả năng tự tìm thêm ngữ cảnh thay vì dừng sau lượt tìm đầu.
- Câu hỏi lặp lại nhiều nhất là độ trễ khi phải tìm qua nhiều bước. Bài chính thức cho biết single-corpus và cross-corpus chênh lệch trung bình trong khoảng 3%, nhưng không công bố thời gian tuyệt đối.
- Một số người hỏi benchmark, khả năng dùng công cụ retrieval bên ngoài và mã nguồn.
- Có ý kiến cho rằng RBAC và quyền truy cập dữ liệu mới là trở ngại lớn hơn RAG trong doanh nghiệp.

## Lưu ý

- Đây là tính năng public preview trên nền tảng doanh nghiệp của Google, không phải thông báo phát hành một repo open source.
- Các số 34%, 90,1% và 3% là kết quả Google công bố trong thiết lập thử nghiệm của họ.
