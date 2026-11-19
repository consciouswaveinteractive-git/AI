---
name: exec-plan
description: Lập, cập nhật và nghiệm thu ExecPlan ngắn gọn cho người và AI cùng đọc; 
---

# ExecPlan

- Tổ chức theo cấu trúc fractal và theo mốc có thể kiểm chứng bằng file bằng chứng với nội dung và format xúc tích ; KHÔNG PHẢI do riêng AI đọc với cấu trúc tùy ý với step by step plan và nhiều file .md khó đọc 

## Structure

- Cấu trúc lặp ở mọi cấp: cha cố nhiều mốc con, drill down vào trong con sẽ thấy nhiều mốc cháu nhỏ hơn, drill down vào mốc cháu sẽ thấy nhiều mốc chắt nhỏ hơn
- Không nhất thiết các mốc cùng cấp đều phải drill down như nhau, nếu có một nhánh phức tạp hơn các nhánh khác thì có thể cân nhắc drill down thêm
- Ở các mốc ở cấp nhỏ nhất cuối cùng sẽ có đúng một link dẫn tới **file bằng chứng** với nội dung và format xúc tích ngắn gọn dễ hiểu cho người đọc.

## Templates

- Hướng dẫn và quy tắc sử dụng nằm trong `SKILL.md`; file trong `assets/` chỉ chứa mẫu để điền, không kèm các đoạn hướng dẫn.
- Dùng [mẫu ExecPlan](assets/exec-plan.md) cho cấu trúc mốc và [mẫu bằng chứng](assets/acceptance-evidence.md) cho đầu mối theo dõi/nghiệm thu.

## Acceptance evidence

### Tiêu chí nghiệm thu

- Nêu rõ phạm vi, điều kiện đạt có thể kiểm chứng và bằng chứng cần đối chiếu; phân biệt hoàn tất xử lý với đã hậu kiểm và được nghiệm thu.
- Tiêu chí phải được xác nhận trước khi dùng để kết luận Đạt; không tự biến tiêu chí đề xuất thành yêu cầu đã được người vận hành duyệt.
- Ví dụ: [tiêu chí nghiệm thu SO production](examples/so-production.md#tiêu-chí-nghiệm-thu) — phần được bổ sung để minh họa, chưa phải tiêu chí đã được duyệt của workflow nguồn.

### Output

- Tổng hợp là báo cáo các file chi tiết dưới dạng xúc tích và dễ đọc cho người
- File output chi tiết dùng định dạng khác Markdown, phù hợp với dữ liệu: CSV/XLSX cho bảng đối chiếu, JSON cho dữ liệu có cấu trúc lồng nhau, JSONL cho chuỗi sự kiện. Ảnh, PDF hoặc log giữ định dạng gốc khi cần làm bằng chứng. Không đổi đuôi file chỉ để đáp ứng định dạng.
- Ví dụ: [bảng tổng hợp SO production](examples/so-production.md#output) — phân loại 235 SO theo trạng thái và tham chiếu dữ liệu JSON chi tiết.

### Decision log

- Chỉ ghi quyết định đã được người vận hành trả lời/quyết định; câu hỏi chưa được trả lời nằm ở phần việc đang chặn hoặc checkpoint.
- Không có record cụ thể đính kèm. Trọng tâm là quy tắc có thể tái sử dụng, không phải nhật ký xử lý từng record.
- Ví dụ: [Decision log SO production](examples/so-production.md#decision-log) — câu hỏi và câu trả lời thực tế; chỉ tái sử dụng trong phạm vi đã được duyệt, không mặc định áp dụng ngoại lệ sang workflow khác.

### Checkpoint

- Tạo checkpoint ở mốc quan trọng, khi kết thúc/chuyển giao một phiên dài, hoặc khi cần tách một plan nhỏ khỏi file tổng hợp; không cần ghi từng thao tác.
- Trong file tổng hợp chỉ giữ một dòng tóm tắt và liên kết cho mỗi checkpoint; không nhúng toàn bộ nội dung checkpoint.
- Ví dụ: [Checkpoint SO production](examples/so-production.md#checkpoint) — tóm tắt tiến độ, điểm dừng và đường dẫn file chi tiết; file gốc nằm trong project nguồn, không được đóng gói cùng ví dụ.

