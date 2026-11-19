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


## Progress and Acceptance

- Phải cập nhật tiêu chí và checkbox theo thực tế; chỉ đánh dấu `[x]` khi file liên kết có bằng chứng nghiệm thu
- Con hoàn thành tự động hoàn thành cha

## Templates

- Hướng dẫn và quy tắc sử dụng nằm trong `SKILL.md`; file trong `assets/` chỉ chứa mẫu để điền, không kèm các đoạn hướng dẫn.
- Dùng [mẫu ExecPlan](assets/exec-plan.md) cho cấu trúc mốc và [mẫu bằng chứng](assets/acceptance-evidence.md) cho đầu mối theo dõi/nghiệm thu.

## Acceptance evidence

### Tổng hợp

- File bằng chứng là đầu mối tổng hợp; không chép toàn bộ dữ liệu, lịch sử phiên làm việc hoặc plan chi tiết vào đây. Chỉ ghi Đạt khi có bằng chứng đáp ứng tiêu chí nghiệm thu.
- File dữ liệu chi tiết dùng định dạng khác Markdown, phù hợp với dữ liệu: CSV/XLSX cho bảng đối chiếu, JSON cho dữ liệu có cấu trúc lồng nhau, JSONL cho chuỗi sự kiện. Ảnh, PDF hoặc log giữ định dạng gốc khi cần làm bằng chứng. Không đổi đuôi file chỉ để đáp ứng định dạng.

### Decision log

- Chỉ ghi quyết định đã được người vận hành trả lời; câu hỏi chưa được trả lời nằm ở phần việc đang chặn hoặc checkpoint.
- Không bắt buộc có record cụ thể đính kèm. Trọng tâm là quy tắc có thể tái sử dụng, không phải nhật ký xử lý từng record.
- Giữ đúng ý câu trả lời; không biến phê duyệt cho một case thành quyền áp dụng mọi case. Nếu chưa rõ phạm vi tái sử dụng, ghi rõ cần xác nhận trước khi áp dụng sang case khác.
- Không tự bổ sung quyền ghi dữ liệu, bỏ qua kiểm tra hoặc mở rộng sang môi trường khác từ một quyết định có phạm vi hẹp.
- Khi quyết định thay đổi, ghi quyết định thay thế và tham chiếu ID cũ; không âm thầm sửa mất lịch sử.

### Checkpoint

- Tạo checkpoint ở mốc quan trọng, khi kết thúc/chuyển giao một phiên dài, hoặc khi cần tách một plan nhỏ khỏi file tổng hợp; không cần ghi từng thao tác.
- Checkpoint ghi đủ thông tin để tiếp tục công việc: mục tiêu/phạm vi, việc đã làm và kết quả, trạng thái còn dở hoặc điểm đang chặn, plan nhỏ và bước tiếp theo, liên kết bằng chứng cần thiết.
- Có thể dùng Markdown cho checkpoint thiên về diễn giải/plan; dùng định dạng dữ liệu phù hợp nếu checkpoint chủ yếu là bảng hoặc dữ liệu có cấu trúc.
- Quyết định đã được duyệt nằm ở Decision log; checkpoint chỉ tham chiếu ID để tránh lặp và mâu thuẫn.
- Trong file tổng hợp chỉ giữ một dòng tóm tắt và liên kết cho mỗi checkpoint; không nhúng toàn bộ nội dung checkpoint.

