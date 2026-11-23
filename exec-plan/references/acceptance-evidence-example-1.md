# Ví dụ Acceptance evidence

> **Chỉ dẫn — giữ lại khi cập nhật:** Giữ bốn mục theo thứ tự, các cột bảng bắt buộc và chỉ dẫn. Chỉ điền dữ liệu thực tế; mục chưa có dữ liệu ghi “-”. Quy tắc gốc: [SKILL.md](https://github.com/consciouswaveinteractive-git/AI/blob/main/exec-plan/SKILL.md).


## Tiêu chí nghiệm thu

> AI đề xuất tối đa 2 tiêu chí để người dùng duyệt. Mỗi tiêu chí nêu phạm vi và điều kiện đạt có thể kiểm chứng.

- Các Sale order lines có trường "deliverd qty" và "invoiced qty" giống như hệ thống cũ
- Các Sale Order, Stock move, Invoice có ngày giống như thế thống cũ

## Output

> Format output phù hợp với các tiêu chí




## Decision log

> Chỉ ghi hỏi/đáp thực tế, thành quy tắc tái sử dụng trong đúng phạm vi câu trả lời; giữ căn cứ có thể truy hồi, dẫn chiếu ngắn trong ô khi cần. Không ghi ID/nhật ký từng record. Câu hỏi chưa trả lời đặt ở phần đang chặn trong Checkpoint. Chưa có dữ liệu thì thay bảng mẫu bằng “-”.


| STT | Câu hỏi AI đã hỏi | Câu trả lời của người vận hành |
|---|---|---|
| 01 | confirm SO tự sinh chuỗi PICK → PACK → DELIVERY đang mở trên V19 không? | Không, trên v19 confirm SO chỉ sinh PICK thôi |
| 02 | sử dụng tài khoản native của sản phẩm v19 hay sử dụng tài khoản giống v14 | Native |
| 03 | không tìm thấy saleperson và saleteam đích | tìm saleperson theo tên login, ignore saleteam |
| 04 | nên lưu ánh xạ sale order, sale order line, stock move,stock move line riêng lẻ hay trong cùng một file? | cùng một file cho mỗi SO/change-set |
| 05 | không tìm thấy ánh xạ delivery address? | dùng khách hàng chính |
| 06 | không tìm external ID của lot đích | dùng tên lot |
| 07 | cảnh báo lot hết hạn | ignore |
| 08 | thiếu tồn để xuất | cấp tồn tạm |
| 09 | UoM của sản phẩm nguồn và đích khác nhau | ignore |
| 10 | Nghi ngờ valuation giá vốn và accounting thày đổi bất thường | ignore |
| 11 | Held: reservation method khác gate. | ignore |
| 12 | không tìm thấy ánh xạ product | check `.agents\long-workflow\py-oct-26-31\planning\master-mapping-evidence.md`, nếu vẫn ko thấy thì tạo trên v19 |
| 13 | base-price rule không cho phép base_price ≤ 0 và is_free = False | đổi cờ is_free |
| 14 | không tìm thấy ánh xạ invoice address hoặc delivery address | dùng contact cha chính |
