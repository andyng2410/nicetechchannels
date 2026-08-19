# SCRIPT_RULES

Luật gốc để agent viết script cho NiceTechChannels.

## 0. Cách đọc thư mục này

- Luôn đọc `START_HERE.md` trước.
- File này là luật gốc.
- Nếu cần bắt chước một giọng cụ thể, đọc `STYLE_INDEX.md` rồi chỉ mở file giọng phù hợp nhất.
- Style cá nhân không được override luật gốc trong file này.

## 1. Job to be done

- Viết lại nội dung cho người xem Việt **hiểu nhanh, nghe cuốn, xem hết**.
- Script phải nghe như đang kể lại cho người khác nghe, không phải đang đọc note.
- Ai muốn đào sâu thì họ tự đọc source tiếp; script không cần nhồi hết mọi fact vào một chỗ.
- Với video, bài viết, thread, hoặc website nguồn: viết trực tiếp về chủ đề chính. Source là bằng chứng để dựng câu chuyện, không phải cái cớ để mở bằng `bài này nói` hay `video này nói`.
- Script không kể chuyện nội bộ sản xuất như đã tải file bằng gì, lưu source ở đâu, workflow yêu cầu gì, slide này dùng reveal nào, phụ đề đang nói gì, hay agent đã xử lý ra sao. Những thứ đó chỉ để trong note/source, không đưa vào lời đọc.
- Các dòng nội dung KHÔNG chứa CTA đăng ký kênh/theo dõi kênh: dòng outro cố định do hệ thống quản lý (starter/wizard tự thêm làm dòng cuối `script-90s.txt`, map vào slide outro `data-outro`) và không tính vào nội dung script.

## 2. Hook

- Câu đầu tiên phải nói rõ chuyện gì đang thay đổi, hoặc vì sao người xem nên dừng lại.
- Ưu tiên câu ngắn, dễ hiểu ngay, tránh chơi chữ.
- Hook tốt là hook mà người nghe hiểu chủ đề chỉ sau 1 nhịp.
- Slide 1 mặc định là **1 câu, 1 reveal**. Đừng dùng slide 1 để giải thích cơ chế, bối cảnh dài, hoặc nhồi đủ bằng chứng.
- Độ dài tốt thường khoảng 12-26 từ. Có thể dài hơn nếu hook cần một phép so sánh/demo cụ thể, nhưng nếu câu phải ôm quá 2 số liệu, 2 mệnh đề phụ, hoặc nhiều dấu phẩy, hãy đẩy phần chứng minh sang slide 2.
- Công thức slide 1 nên là: **đối tượng chính + chuyện mới/kết quả lạ + lý do đáng xem**.
- Với repo/tool: nói tên repo/tool sớm và gắn ngay lợi ích hoặc nỗi đau cụ thể.
- Với benchmark/model: mở bằng kết quả, thứ hạng, so sánh, hoặc cú lệch đáng chú ý; phần cần lưu ý để sau.
- Với demo/video: mở bằng điều người xem sắp thấy, rồi cho demo/proof xuất hiện ngay sau hook. Không giải thích hậu trường ở slide 1.
- Với bài phân tích/tài chính/xã hội: mở bằng góc ngược kỳ vọng hoặc lớp giá trị bị bỏ lỡ.
- Tránh mở bằng meta-framing như `video này nói`, `bài này nói về`, `hôm nay mình sẽ`, `dành cho ai chưa biết`, hoặc kể lại nguồn trước khi nói chuyện chính.
- Text trên màn hình slide 1 có thể chỉ là brand/model/repo/title ngắn; voiceover mới là hook. Không bắt canvas phải chép nguyên câu hook.

## 3. Nhịp câu

- Mỗi câu chỉ gánh 1 ý.
- Trộn câu ngắn với câu vừa phải; tránh 4-5 câu đều nhau như đọc note.
- Đọc thành tiếng để test. Câu nào vấp miệng thì viết lại.
- Nếu một câu chỉ đúng trên giấy mà nghe đọc không trôi, bỏ câu đó.
- Không dùng dấu gạch ngang dài `—` trong script. Dùng dấu phẩy, dấu hai chấm, hoặc tách câu để TTS đọc tự nhiên hơn.

## 4. Một slide, một ý lớn

- Mỗi slide chỉ giữ 1 ý trung tâm.
- Các câu sau chỉ làm rõ, đưa ví dụ, hoặc nói hệ quả của ý đó.
- Nếu 1 slide phải giải thích quá nhiều, tách thêm slide.
- Đừng tham nhét vì càng nhét càng giảm độ nhớ.

## 5. Giọng văn

- Viết như đang nói chuyện, không viết như đọc bài phân tích.
- Cho phép từ nối tự nhiên như `ngặt nỗi`, `cơ mà`, `nghĩa là`, `thành ra`, `mất ăn`, nếu hợp ngữ cảnh.
- Tránh mở đầu theo kiểu giáo trình: `Tức là`, `Nó là`, `Một bình luận nói rất đúng`.
- Mặc định ưu tiên tiếng Việt; chỉ giữ tiếng Anh khi nó thật sự là thuật ngữ hoặc tên riêng cần giữ.

## 6. Từ vựng

- Tiếng Việt là mặc định.
- Chỉ giữ tiếng Anh cho tên riêng và thuật ngữ khó thay thế: `AI`, `agent`, `Claude Code`, `Telegram`, `For You`, `terminal`.
- Các từ phổ thông như `viral`, `engagement`, `follower`, `like` ưu tiên đổi sang tiếng Việt nếu không mất nghĩa.
- Không để lọt các từ nháp hoặc từ đánh dấu nội bộ vào voiceover. Khi đọc thành tiếng, đổi sang cách nói tự nhiên như `điểm cần lưu ý`, `giới hạn`, `mặt trái`, `tóm lại`, hoặc `chốt lại`.
- Nếu có thể nói một cách bình dân hơn mà không mất ý, chọn cách đó.

## 7. Cấu trúc để dễ cuốn

- Ưu tiên `vấn đề -> vì sao quan trọng -> cách dùng đúng`.
- Slide 1 mở hook.
- Slide 2 nên nhanh chóng đưa proof/demo/source artifact hoặc nhịp visual đầu tiên. Nếu slide 1 hứa có demo, slide 2 hoặc chính visual slide 1 phải cho thấy demo ngay.
- Các slide giữa đi vào cơ chế, ví dụ, số liệu, điểm cần lưu ý và cách áp dụng.
- Slide cuối chốt bằng cảnh báo hoặc góc nhìn, không chốt bằng khẩu hiệu rỗng.

## 8. Rule cho nội dung social

- Đừng chỉ tối ưu cho `like`; ưu tiên nội dung kéo được phản hồi thật và tạo lý do để người lạ muốn theo dõi tiếp.
- Nếu dùng câu hỏi, câu hỏi đó phải mở ra suy nghĩ hoặc trải nghiệm thật, không phải câu mồi một chữ.
- Nội dung nên có phần thưởng cho người đọc hết: một ý mới, một ví dụ đắt, hoặc một góc nhìn đáng nhớ.
- Giữ giọng viết và trục chủ đề đủ nhất quán để người xem nhận ra `đây là kiểu của bạn`.
- Tránh bait-and-switch, lạc chủ đề, hoặc văn phong quá giống mẫu AI chung chung.

## 9. Cách mượn style đúng

- Mượn `nhịp`, `màu giọng`, `độ sắc`, `độ mềm`, `cách chốt`.
- Không bê nguyên CTA, slang niche, hay cấu trúc post nếu ngữ cảnh không hợp.
- Nếu topic là tech explainer mà style gốc là crypto, chỉ mượn độ móc và nhịp, không bê nguyên "kèo", "airdrop", "join".

## 10. Checklist trước khi chốt script

- Hook đã rõ ngay chưa?
- Mỗi slide có đúng 1 ý lớn chưa?
- Đọc lên có trôi miệng chưa?
- Có câu nào nghe như AI đang tóm tắt không?
- Còn dấu `—` nào trong script hoặc `slideScripts` không?
- Có chỗ nào quá nhiều tiếng Anh không?
- Có câu nào lộ chuyện nội bộ như source folder, workflow, slide/reveal, phụ đề, tải file, hoặc cách agent làm việc không?
- Style đang phục vụ nội dung hay đang lấn át nội dung?
