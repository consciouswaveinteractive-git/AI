---
name: exec-plan
description: Lập, cập nhật, tiếp quản và nghiệm thu ExecPlan ngắn gọn theo mốc có thể kiểm chứng. Dùng khi tạo hoặc sửa ExecPlan, acceptance evidence; khi tiếp tục/chuyển giao phiên hoặc đối chiếu bằng chứng để kết luận trạng thái mốc.
---

# ExecPlan

- Tổ chức theo cấu trúc fractal và mốc có thể kiểm chứng, không biến cây mốc thành nhật ký thao tác step by step.
- Viết xúc tích ngắn gọn cho cả người và AI cùng đọc

## Structure

- Mốc cha có các mốc con; nhánh phức tạp có thể chia nhỏ hơn các nhánh khác.
- Mỗi mốc lá có đúng một liên kết tới file bằng chứng. Giữ hướng dẫn cập nhật evidence ngoài cây mốc.


## Templates và nguồn quy tắc

- Dùng [mẫu ExecPlan](assets/exec-plan.md) cho cây mốc và [mẫu bằng chứng](assets/acceptance-evidence.md) cho theo dõi/nghiệm thu.
- `SKILL.md` là nguồn quy tắc gốc. Template evidence chứa cấu trúc và chỉ dẫn cập nhật ngắn; sao chép cả chỉ dẫn khi tạo file, giữ lại khi cập nhật. Không chép toàn bộ skill vào mỗi evidence.
- Chỉ thay placeholder bằng dữ liệu thực tế. Mục chưa có dữ liệu ghi “-”.
- Giữ bốn mục evidence theo thứ tự: `Tiêu chí nghiệm thu`, `Output`, `Decision log`, `Checkpoint`. Giữ các cột bắt buộc của Decision log và Checkpoint; Output linh hoạt theo nghiệp vụ.
- Xem [ví dụ migration lịch sử](references/acceptance-evidence-example-1.md)



## Acceptance evidence

### Tiêu chí nghiệm thu

- AI đề xuất cho người dùng duyệt tối đa 2 tiêu chí
- Mỗi tiêu chí nêu phạm vi, điều kiện đạt có thể kiểm chứng


### Output

- Gắn link output. 
- Chọn output format phù hợp với các tiêu chí


### Decision log

- Mục đích: giúp agent đỡ hỏi những câu hỏi một cách lặp lại. Khi agent hỏi lặp lại, điều đó chứng tỏ có cách làm chưa thực sự thông minh và cần thay đổi
- Giữ ba cột: `STT`, `Câu hỏi AI đã hỏi`, `Câu trả lời của người vận hành`.
- Chỉ ghi câu hỏi AI thực sự đã hỏi người và câu trả lời/quyết định người trả lời
- Diễn đạt thành quy tắc tái sử dụng, không đính kèm ID hoặc nhật ký xử lý từng record




