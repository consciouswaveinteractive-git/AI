# <Mốc được theo dõi/nghiệm thu>

## 1. Tổng hợp

- **Trạng thái:** <Chưa thực hiện / Đang thực hiện / Bị chặn / Đạt / Chưa đạt>.
- **Phạm vi:** <Đối tượng, công việc và tiêu chí nghiệm thu chính>.

| Kết quả/trạng thái | Số lượng hoặc kết luận |
|---|---|
| <Nhóm kết quả cần theo dõi> | <Số lượng/kết luận có thể kiểm chứng> |

- **Chi tiết:** [<Tên dữ liệu chi tiết>](<đường-dẫn-file-chi-tiết>).
- **Việc tiếp theo hoặc điểm đang chặn:** <Tóm tắt ngắn; dẫn tới checkpoint nếu cần>.
- File này là đầu mối tổng hợp; không chép toàn bộ dữ liệu, lịch sử phiên làm việc hoặc plan chi tiết vào đây. Chỉ ghi Đạt khi có bằng chứng đáp ứng tiêu chí nghiệm thu.
- File dữ liệu chi tiết dùng định dạng khác Markdown, phù hợp với dữ liệu: CSV/XLSX cho bảng đối chiếu, JSON cho dữ liệu có cấu trúc lồng nhau, JSONL cho chuỗi sự kiện. Ảnh, PDF hoặc log giữ định dạng gốc khi cần làm bằng chứng. Không đổi đuôi file chỉ để đáp ứng định dạng.

## 2. Decision log

| ID | Câu hỏi AI đã hỏi | Câu trả lời của người vận hành | Quy tắc áp dụng cho case tương tự | Phạm vi, điều kiện và ngoại lệ |
|---|---|---|---|---|
| D-001 | <Câu hỏi thực tế> | <Câu trả lời đã nhận; không tự suy diễn> | <Nếu gặp tình huống X thì xử lý Y> | <Áp dụng ở đâu, khi nào phải hỏi lại> |

- Chỉ ghi quyết định đã được người vận hành trả lời; câu hỏi chưa được trả lời nằm ở phần việc đang chặn hoặc checkpoint.
- Không bắt buộc có record cụ thể đính kèm. Trọng tâm là quy tắc có thể tái sử dụng, không phải nhật ký xử lý từng record.
- Giữ đúng ý câu trả lời; không biến phê duyệt cho một case thành quyền áp dụng mọi case. Nếu chưa rõ phạm vi tái sử dụng, ghi rõ cần xác nhận trước khi áp dụng sang case khác.
- Không tự bổ sung quyền ghi dữ liệu, bỏ qua kiểm tra hoặc mở rộng sang môi trường khác từ một quyết định có phạm vi hẹp.
- Khi quyết định thay đổi, ghi quyết định thay thế và tham chiếu ID cũ; không âm thầm sửa mất lịch sử.

## 3. Checkpoint

| Thời điểm/mốc | Thông tin chính | File chi tiết |
|---|---|---|
| <Ngày giờ hoặc tên mốc> | <Tiến độ, kết quả quan trọng, điểm dừng hoặc plan nhỏ> | [<Tên checkpoint>](<đường-dẫn-checkpoint>) |

- Tạo checkpoint ở mốc quan trọng, khi kết thúc/chuyển giao một phiên dài, hoặc khi cần tách một plan nhỏ khỏi file tổng hợp; không cần ghi từng thao tác.
- Checkpoint ghi đủ thông tin để tiếp tục công việc: mục tiêu/phạm vi, việc đã làm và kết quả, trạng thái còn dở hoặc điểm đang chặn, plan nhỏ và bước tiếp theo, liên kết bằng chứng cần thiết.
- Có thể dùng Markdown cho checkpoint thiên về diễn giải/plan; dùng định dạng dữ liệu phù hợp nếu checkpoint chủ yếu là bảng hoặc dữ liệu có cấu trúc.
- Quyết định đã được duyệt nằm ở Decision log; checkpoint chỉ tham chiếu ID để tránh lặp và mâu thuẫn.
- Trong file tổng hợp chỉ giữ một dòng tóm tắt và liên kết cho mỗi checkpoint; không nhúng toàn bộ nội dung checkpoint.
