# Đánh giá MultiVibe — 29/10/2026

## Kết luận hiện tại

Đủ bằng chứng để tiếp tục thử cô lập; chưa đủ bằng chứng để thay cấu hình Codex đang dùng. Chưa cài Host, chưa dùng tài khoản thật, chưa thay `~/.codex` hoặc QuotaCrew.

Mã nguồn được kiểm tra: `thibautrey/multivibe`, commit `f1430b3d9e847e4c520032875ad253d5e9656864`. Bản phát hành mới nhất lúc kiểm tra: `v0.2.138` (26/10/2026), có gói Windows amd64, SHA256SUMS và tài liệu chữ ký. Commit nhánh chính khác bản phát hành; không coi test nhánh chính là kiểm chứng binary phát hành.

## Bằng chứng

- Có mã nguồn OAuth, lưu tài khoản, proxy Rust và bộ cấu hình/khôi phục Codex.
- `src/oauth-config.ts`: endpoint mặc định là auth.openai.com; cho phép override qua biến môi trường, do đó môi trường thử phải loại bỏ override không được duyệt.
- `src/store.ts`: lưu tài khoản dạng JSON với ghi atomic và chmod 0600; không phải mã hóa token tại chỗ. Windows Host có mã bảo vệ ACL riêng, nhưng chưa kiểm thử ACL của bản đóng gói trên máy này.
- `rust/v1-edge/src/lib.rs`: gặp lỗi HTTP đủ điều kiện thì chặn tạm account/model và thử ứng viên khác trước khi trả stream cho client. Điều này chưa chứng minh phục hồi khi stream đã trả một phần hoặc khi có tool side effect.
- Nhánh WebSocket loại bỏ `previous_response_id`. Phải kiểm chứng hội thoại gửi lịch sử đầy đủ; không được kết luận giữ ngữ cảnh khi client chỉ gửi phần tăng thêm.
- Tích hợp Codex dùng provider Responses riêng có bearer token local và cơ chế restore; chưa chứng minh riêng extension đang cài.

## Kết quả test local

- `core-tests.log`: 27/27 qua: OAuth, token refresh/danh tính, routing policy, credential context, ký update feed. Chỉ dữ liệu giả; không gọi model thật.
- `harness-tests.log`: 22/33 qua. Có lỗi so sánh quyền POSIX (0666 thực tế trên Windows khác 0600 mong đợi), quyền tạo symlink EPERM và giả định executable kiểu Unix. Chạy lại ngoài sandbox vẫn lỗi. Chưa sửa/mute test để báo xanh.
- Git checkout Windows biến symlink `src/workspace-routing-kernel.ts` thành file chứa đường dẫn. Đã materialize nội dung file đích trong checkout thử để chạy test. Đây là thay đổi local của checkout đánh giá.
- Máy có Node v24; không tìm thấy Cargo hoặc Go qua PATH. Chưa chạy bộ test proxy Rust, chưa build Host.

## Phép thử cô lập tiếp theo

1. Đối chiếu source tag v0.2.138 với binary, checksum và chữ ký trước khi chạy gói. Chạy trực tiếp từ thư mục thử, không dùng install.ps1 hoặc đăng ký startup.
2. Dùng home/config/data riêng trong thư mục test; bind loopback cổng riêng 14755/14756, admin/proxy token giả ngẫu nhiên, tắt log body/header. Không mount/read credentials hiện tại. Tắt auto-update và mọi dịch vụ cloud tùy chọn.
3. Hai mock upstream local: A trả quota/429, B trả Responses SSE hợp lệ. Xác nhận retry sang B và không đổi nội dung yêu cầu.
4. Thử ba lượt với nonce và tool call/output giả: trước và sau chuyển A→B phải giữ nonce, tool output, instruction. Thử cả full-history HTTP và delta WebSocket; delta không giữ được ngữ cảnh thì đánh dấu không hỗ trợ, không âm thầm cắt lịch sử.
5. Stream A trả một phần rồi ngắt: không được phát lại tool call đã giao hoặc tự báo hoàn thành. Cả hai account cạn quota phải dừng rõ ràng, không lặp vô hạn.
6. Xác nhận unauthorized bị chặn, token không vào log, Windows ACL chỉ user có quyền dữ liệu thử. Thử dừng/khởi động lại Host và restore config thử đúng byte.
7. Chỉ khi các gate trên đạt mới đăng nhập account thật qua OAuth trong môi trường thử; nghiệm thu request thật rồi mới tính cấu hình extension VS Code. Không dùng hội thoại migration làm thử nghiệm.

## Giới hạn

Đây là đánh giá có phạm vi, không phải kiểm toán bảo mật đầy đủ. Bằng chứng 27 test qua không thay thế bài thử failover proxy hoặc nghiệm thu tự động hoàn toàn trên VS Code.

## Kết quả Linux container — 29/10/2026

Docker Desktop đã được khởi động. Dùng image Rust bookworm digest `sha256:e9da6f6c3ed5095fd5d33bf7cdf309830a178a8147888f1b2f76d5769bd9306c`, source mount read-only, giới hạn 4 CPU/4 GB, cache build ở Docker volume riêng. Không mount tài khoản thật. Các container test dùng --rm và đã kết thúc; Docker Desktop vẫn chạy.

Đã thêm module test riêng `operator_failover_tests.rs` vào checkout đánh giá, không sửa hành vi proxy:

- **PASS:** A trả 429/quota → B nhận cùng nội dung; lượt kế tiếp bảo toàn instruction, nonce, tool call và tool output khi client gửi đầy đủ lịch sử. Request thiếu xác thực không tới upstream; khi cả hai account cạn quota, dừng với 429 và không lặp vô hạn. Đây là mock HTTP, không phải nghiệm thu model/extension thật hoặc stream bị ngắt giữa chừng.
- **FAIL:** WebSocket lượt 2 chỉ gửi phần mới cùng previous_response_id. Upstream không nhận previous_response_id lẫn nonce từ lượt 1. Phép thử giữ ngữ cảnh thất bại; không được nghiệm thu WebSocket delta.
- **PASS:** Ba regression test upstream có sẵn: `native_failed_sse_preserves_payload_and_marks_both_traces_as_errors`, `upstream_sender_retries_transient_errors_but_not_quota`, `native_session_affinity_is_isolated_by_application`. Chạy offline trong container network none với upstream loopback.

Log: `linux-acceptance.log` (1 pass/1 fail có chủ đích giữ nguyên lỗi) và `linux-regression.log` (3 test pass). Mã được build là commit main ghi ở đầu báo cáo, không phải binary Windows v0.2.138.

Tài liệu chính thức Codex có tùy chọn `model_providers.<id>.supports_websockets` (https://learn.chatgpt.com/docs/config-file/config-reference). Hướng tiếp tục là kiểm chứng custom provider dùng HTTP/SSE (`supports_websockets=false`) trong home riêng, không suy ra từ test HTTP rằng extension hiện tại chắc chắn gửi đầy đủ lịch sử. Chưa thay cấu hình thật, chưa dùng token thật, chưa có nghiệm thu tự động hoàn toàn.

## Lần thử HTTP/SSE bổ sung

Đã thêm `http_sse_quota_failover_preserves_history_and_delivers_completion` vào module test: A trả 429, B trả event delta/completed, client phải nhận completion đúng một lần và request sau phải bảo toàn toàn bộ lịch sử cùng tool output. Chỉ thay test, không sửa logic proxy.

Đã gọi container `multivibe-http-sse-tests` với network none và mount source read-only. Ở lần kiểm tra này cả `docker run` và `docker ps/logs` đều chờ không trả kết quả; file `http-sse.log` chưa có nội dung. Tiến trình Docker backend và CLI vẫn tồn tại. **Trạng thái chưa rõ, không được coi container đã chạy/đã dừng hoặc bài test đã đạt.** Không tự khởi động lại Docker vì có thể ảnh hưởng tiến trình khác. Khi daemon đáp ứng trở lại, kiểm tra container theo tên trước khi chạy lại; không tạo thêm bản chạy trùng.

### Kết quả sau khởi động lại Docker

Người dùng xác nhận không dùng Docker cho công việc khác và cho phép khởi động lại. `docker desktop restart` hoàn tất; server trả version 28.0.4. Lần chạy treo trước kết thúc bằng lỗi Docker API 500; kiểm tra không còn container theo tên trước khi chạy lại.

Chạy lại `operator_failover_tests::http_sse` trong container network none: **1 passed, 0 failed, TEST_EXIT=0**, thời gian test 0.03 giây (không tính build). Log `http-sse.log` đã được thay bằng lần chạy thành công.

Đã kiểm chứng với upstream giả: A trả 429 → B trả SSE; client đọc hết body, nhận mock output và completion đúng một lần; lượt 2 giữ đầy đủ instruction/input/tool output; request không auth bị chặn; mọi account hết quota trả 429 hữu hạn. Không phải kiểm chứng model nhớ ngữ cảnh thật, delta WebSocket, ngắt stream giữa chừng, hoặc extension VS Code. Chưa dùng tài khoản thật, chưa sửa cấu hình Codex chính. Hướng HTTP/SSE qua proxy đạt gate giả lập và cần gate client thực tế trong home riêng.

## Client Codex thực tế qua HTTP/SSE — PASS

Runner: `client_acceptance.py`. Kết quả: `client-run-20261029-062120/result.json`; request upstream giả và stdout/stderr hai lượt được lưu cùng thư mục. Client chính thức đi kèm extension 26.1021.22027 (engine 0.164.0-alpha.11.1), home/config và workspace trống riêng. Provider `mock_multivibe`, `supports_websockets=false`, retry client bằng 0, sandbox read-only, không tool call. Không dùng token thật hoặc nạp config home chính.

1. Lượt đầu account A trả SSE, client exit 0 và nhận MOCK_ACK_729.
2. Resume bằng đúng thread ID; A trả usage_limit_reached/429, proxy chuyển B; client exit 0.
3. Chính xác ba request inference: A, A lỗi, B. Input của A lỗi và B giống nhau; request B có NONCE_CLIENT_729 từ user lượt đầu và MOCK_ACK_729 từ assistant lượt đầu. Không có thao tác reload hoặc gửi lại prompt thủ công giữa hai lần thử.
4. Container `multivibe-client-acceptance` được stop theo tên trong finally và dùng --rm; mock HTTP server đã shutdown.

Giới hạn: chứng minh client truyền và bảo toàn transcript, không phải model thật nhớ ngữ cảnh. Chưa kiểm thử OAuth/account thực, UI extension VS Code, kế thừa thread đang tồn tại thuộc provider openai, compact context hoặc ngắt stream giữa chừng. Chưa triển khai vào cấu hình thật. Không được gọi đây là nghiệm thu tự động hoàn toàn cho VS Code.

## Dashboard đăng nhập thử local

Đã khởi động control plane Node của gói Windows tại 127.0.0.1:1456, dữ liệu riêng tại `%LOCALAPPDATA%/MultiVibe-Codex-Pilot`. ACL thư mục được giới hạn SID user hiện tại và SYSTEM. Token local được tạo riêng, không xuất ra chat/log; mật khẩu dashboard trong `admin-password.txt`. Home tích hợp harness riêng `isolated-home`, không phải ~/.codex thật. Anonymous usage sharing đã tắt trong store khởi tạo, không bật Sentry hoặc community benchmarks.

Docker tạo gateway lại timeout; không coi lệnh run timeout là chắc chắn không có container. Chưa nghiệm thu gateway Docker đó. Dashboard hiện được phục vụ bởi `login_gateway.py` tại **http://localhost:1455**, bind chỉ 127.0.0.1. Gateway có mật khẩu local, cookie HttpOnly/SameSite Strict, kiểm tra Host/Origin; mọi inference /v1 và internal đều trả 503. Chỉ dùng để thêm account qua giao diện OAuth upstream, không kết nối Codex chính. Đây là gateway tạm tự viết, không phải binary MultiVibe chính thức.

Kiểm tra thực tế: GET /admin/session chưa auth trả authenticated=false; POST /admin/session mật khẩu đúng trả 200; GET /admin/accounts có cookie trả 200; homepage và /auth/callback trả 200. Chưa bắt đầu OAuth thật hoặc khẳng định callback đã trao đổi token thành công. User cần tự đăng nhập OpenAI. Không bấm Connect/Repair Codex trong pilot.

Các tiến trình Node/control plane và Python/login gateway được giữ chạy để user đăng nhập. PID riêng lưu trong `control.pid` và `login-gateway.pid` trong thư mục dữ liệu private. Không có startup task được đăng ký. Cần đối chiếu PID/executable trước khi dừng tiến trình; không kill mọi Node/Python trên máy.

## Quota và yêu cầu model thật — PASS

User đã tự đăng nhập 3 tài khoản; xác minh ba upstream account ID riêng biệt và có token refresh. Không ghi token vào báo cáo. Đã gọi API refresh quota qua backend pilot; cả ba trả quota, không báo cần đăng nhập lại. Snapshot tại lần kiểm tra: usedPercent primary 99, 100 và 57 (giá trị thay đổi theo thời gian); không coi quotaStatus=available là đủ để chọn account khi usedPercent=100.

Docker engine lỗi API 500 trở lại; đã restart với ủy quyền phiên trước, kiểm tra container smoke chưa tồn tại. `real_model_smoke.py` chạy proxy trên cổng host 127.0.0.1:14755, dữ liệu account chỉ đưa qua stdin vào tmpfs /data, không mount thư mục credential user vào container; chỉ account có usedPercent<95 được bật trong snapshot thử, không thay trạng thái store gốc. Token local truyền qua biến môi trường, không qua command line. Không gọi reset/credits endpoint.

Kết quả `real-smoke-result.json`: model gpt-5.6-sol, completed=true, failed_event=false, exact_expected_text=true, output `PILOT_OK_729`. Một request ngắn thật qua HTTP/SSE. Container được stop trong finally và dùng --rm. Chưa thử failover giữa account thật, chưa nghiệm thu client Codex trên account thật, chưa nghiệm thu VS Code; config chính không thay đổi.

## Client Codex + model thật hai lượt — PASS

Đã chạy `real_model_smoke.py --client` với helper `real_client_probe.py`. Kết quả tổng hợp `real-client-result.json`; private run tại `%LOCALAPPDATA%/MultiVibe-Codex-Pilot/real-client-20261029-064149` có home, workspace, transcript và diagnostics riêng. Không chép credential thật vào repo. Config pilot chứa bearer local trong thư mục private đã đặt ACL.

- Model gpt-5.6-sol, HTTP/SSE, supports_websockets=false, client retry=0, sandbox read-only.
- Lượt đầu ghi nhớ mã ngẫu nhiên và trả đúng ACK.
- Resume đúng thread ID, lượt sau nhắc lại chính xác mã mà prompt lượt sau không chứa mã đó.
- first_reply_correct=true, second_reply_exact_nonce=true, same_thread=true. Không ghi nhận command_execution hoặc mcp_tool_call.
- Hai lượt gọi model thật; chưa ép quota account thật để thử failover, chưa nghiệm thu migration/hội thoại provider openai cũ hoặc UI extension VS Code. Cấu hình Codex chính không đổi.
- Container smoke dừng trong finally và dùng --rm. Không triển khai daemon proxy inference lâu dài sau test.

## Failover với hai credential thật, lỗi quota chủ động — CHƯA ĐẠT

Đã thêm relay kiểm thử `quota_fault_relay.py` và callback trước resume. Relay chỉ nhận request có bearer của snapshot account được duyệt, forward đúng /backend-api/codex tới chatgpt.com; không ghi token. Sau lượt 1, relay trả HTTP429 mô phỏng cho account đã dùng. Không cố đốt quota và không dùng hội thoại migration.

Hai lần thử: lượt 1 thành công nhưng resume báo quota exceeded. Lần có trace đầy đủ ghi trong `real-failover-result.json`: chỉ account_index=2 gọi upstream 200, sau đó account_index=2 nhận injected_quota=true; **không có request inference tới account dự phòng**. Đây không phải chứng cứ account đích thực tế từ chối request.

Nguyên nhân phù hợp mã nguồn: select_accounts tạo effective_pool bằng cách bỏ tài khoản dùng >=90% quota 5 giờ nếu còn ứng viên dưới 90%. Snapshot thật có 99%,100%,~69%; do đó pool ban đầu chỉ còn một account. Khi account đó nhận429, vòng retry không có ứng viên kế tiếp trong pool đã lọc. Không được tự giả mạo usage của account thật để báo pass. Cần thử lại sau khi tối thiểu hai account có usedPercent<90, hoặc thay đổi/chứng minh policy fallback trong fork riêng. Chưa triển khai cấu hình chính.

### Kiểm tra lại sau chờ — 29/10/2026

Quota primary mới: usedPercent 81,0,100 (còn 19%,100%,0%). Docker ban đầu lỗi500, không gửi inference; đã restart và xác minh trước khi thử lại.

Lần chạy real-client-20261029-074437: hai lượt cùng thread, hai credential khác nhau index1 và index0 đều trả HTTP200. Không có lỗi429 mô phỏng được ghi nhận vì account đã đổi trước khi relay chặn account lượt1. Client có turn.completed nhưng không có agent_message để kiểm chứng ACK/nonce; first_reply_correct=false và second_reply_exact_nonce=false. Do đó **chưa nghiệm thu failover**, không coi HTTP200 và cùng thread là giữ ngữ cảnh thành công. Cần điều tra relay/SSE trước khi chạy thêm để tránh tiêu hao quota không cần thiết. Config chính không đổi.

## Kiểm tra gói Windows thực tế (29/10/2026)

- Đã tải gói `multivibe-host_0.2.138_windows_amd64.zip`, kích thước 210797524 byte. SHA256 `ef2d54ea85ec77f97dc82448858f65747c30ae451a05d333410796b784c8ca9f` khớp digest GitHub. Chưa xác minh chữ ký độc lập.
- Lệnh `multivibe-host.exe version` thực tế trả `0.2.138`.
- Manifest trong gói khai báo sourceCommit `74a9a06db205d8ceb7f77dc28cec4fb540424f97`, khác commit tag đã lấy `9fdbbd390c767a820bdc96a88ab062213667a6b6`; không được coi hai source là hoàn toàn đồng nhất.
- Danh mục ZIP và manifest đều không có binary `multivibe-v1-edge.exe`. File `app/dist/config.js` trong chính ZIP đặt `MULTIVIBE_CONTROL_PLANE = true` cố định: Node chỉ quản trị, không cung cấp proxy inference.
- Mã Host ở tag v0.2.138 chỉ khởi chạy Node trên Windows và trả về; chỉ nhánh macOS mới khởi chạy Rust edge. Đây là blocker cụ thể cho bài thử inference bằng gói Windows phát hành, không phải kết luận failover đã chạy rồi thất bại.
- Chi tiết manifest lưu tại `package-check.json`. Chưa chạy install.ps1, chưa thêm startup, chưa chép tài khoản hay thay cấu hình Codex thật.
- Docker CLI có trên máy nhưng daemon Linux không chạy; WSL chỉ liệt kê `docker-desktop`, không có distro phát triển độc lập. Máy chưa có Cargo/Go trên PATH.
- Bài thử A trả 429 → B tiếp tục và kiểm thử ngữ cảnh chưa thực hiện được. Cách tiếp tục cần môi trường build Rust/Windows hoặc Linux container chạy được; không đủ điều kiện triển khai ngay từ ZIP hiện tại.

## Bản sửa Content-Type — kiểm chứng offline 02/11/2026

Trạng thái: **đã kiểm chứng offline bằng mock, chưa chạy lại failover tài khoản thật** vì quota chưa đạt cổng hai tài khoản.

- `quota_fault_relay.py`: chỉ gửi `Content-Type` khi upstream thực sự có header; bổ sung forward `Content-Encoding` nếu có (trước đó bị bỏ, có thể làm hỏng body nén). Thêm override `CHATGPT_UPSTREAM` (mặc định vẫn là `https://chatgpt.com`) để test bằng mock; hành vi thật không đổi.
- `relay_header_check.py` (mới, chỉ dùng token giả, không gọi upstream thật): **PASS** — upstream không có `Content-Type` thì relay giữ nguyên việc thiếu header; chèn 429 quota cho account đầu; account thứ hai nhận 200; upstream có `text/event-stream` thì header được forward; bearer lạ bị 403.
- `client_acceptance.py --omit-content-type` (mới thêm cờ, mặc định giữ nguyên): **PASS** — tái hiện đúng chế độ lỗi cũ (upstream SSE thiếu `Content-Type`), client vẫn nhận `agent_message` `MOCK_ACK_729` ở cả hai lượt, failover A→429→B, cùng thread, history được bảo toàn, 0 tool call. Run: `client-run-20261102-161542`. Đây là mock, không thay cho model thật.
- Đọc source `v1-edge/src/lib.rs`: khi client stream và upstream thiếu `Content-Type`, provider `openai` đi nhánh `can_stream_without_content_type` (dòng ~6859) và edge tự gắn `text/event-stream`; đúng với giả thuyết lỗi trước đó.
- `check_real_quota.py` được sửa để không in email/token/id, chỉ in index, phần trăm quota, headroom và cổng failover.
- `start_pilot_control.py` (mới): chỉ khởi động Node control plane cổng 1456 (không Docker, không inference) để refresh quota; dùng lại dữ liệu pilot và ACL sẵn có.

Quota thật lúc 16:14 02/11 (Asia/Bangkok): cả ba account đều `primary` 100%; `secondary` 47/46/58. Reset cửa sổ 5 giờ: account 2 lúc 16:15, account 0 lúc 19:09, account 1 lúc 20:15 cùng ngày. Vì vậy **chưa có hai account đủ headroom**, không chạy `real_model_smoke.py --client --failover`. Sớm nhất đạt cổng là sau 19:09 khi account 0 reset (account 2 + account 0).

Đã khởi động Docker Desktop 28.0.4, xác nhận không còn container `multivibe-*`; control plane và login gateway tạm đã dừng, các cổng 1455/1456/14755/14757 trống. Docker Desktop vẫn chạy. Không thay cấu hình Codex chính.

## Failover tài khoản thật + client Codex — PASS 02/11/2026

Chạy `real_model_smoke.py --client --failover` lúc 20:08 (Asia/Bangkok), model `gpt-5.6-sol`, HTTP/SSE, `supports_websockets=false`, client retry 0, sandbox read-only, home/workspace riêng. Quota trước khi chạy: primary 0/100/33, secondary 47/46/63 → harness chỉ bật account 0 và 2 (account 1 còn 100% cửa sổ 5 giờ).

Trace trong `real-failover-result.json` (bản cũ giữ tại `real-failover-result-20261029.json`):

1. Lượt 1 → account 0, upstream 200, có `response.output_item.done` kiểu `message`/`output_text`; `Content-Type` của upstream là `null` (đúng nhánh lỗi cũ, nay stream native).
2. Chuyển tiếp → account 0 nhận 429 giả lập (`injected_quota=true`).
3. Lượt resume → account 2, upstream 200, có `message`/`output_text`; `Content-Type` cũng `null`.

Kết quả client trong `real-client-20261102-200850/result.json`: `first_reply_correct=true` (ACK), `second_reply_exact_nonce=true`, `same_thread=true`, `tools_requested=false`, không có `command_execution`/`mcp_tool_call`. Quét 14 file log/result cùng thư mục private: **không** chứa access token/refresh token thật.

Đây là **PASS cho failover CLI với hai tài khoản thật qua HTTP/SSE**, gồm cả trường hợp upstream thiếu `Content-Type`. Vẫn **chưa** phải nghiệm thu extension VS Code, chưa thử quota cạn tự nhiên (dùng 429 mô phỏng), chưa thử stream đứt giữa chừng hoặc migration hội thoại provider `openai`.

### Sự cố Docker gặp phải

Docker Desktop 4.40.0 crash lặp lại với `com.docker.build: exit status 1`. Nguyên nhân: tiến trình `com.docker.build` còn sót từ phiên trước (zombie từ 16:15). Đã xử lý bằng cách kill toàn bộ process docker còn sót → `wsl --shutdown` → mở lại Docker Desktop; engine lên lại 28.0.4. Nếu tái diễn, làm đúng thứ tự này trước khi nghĩ đến reset factory. Ổ C: chỉ còn ~6.7 GB trống, cần theo dõi.

## Thử extension VS Code — CHƯA CHẠY ĐƯỢC (hạ tầng), 02/11/2026

Mục tiêu: chạy Codex extension trong một instance VS Code cô lập (`CODEX_HOME` riêng + `--user-data-dir` riêng), trỏ provider `pilot_multivibe` vào proxy tại `127.0.0.1:14755`, rồi thử quota interruption giữa hai lượt trong cùng hội thoại.

Đã chuẩn bị:

- `vscode_failover_service.py`: dựng edge Rust trong Docker cổng 14755 + relay 14757, chạy dài hạn; chỉ chèn 429 sau khi có file `arm-failover` (do người vận hành tạo đúng trước lượt 2), ghi `events.json`/`meta.json`.
- Home cô lập `%LOCALAPPDATA%\MultiVibe-Codex-Pilot\vscode-home-20261102-222932` với `config.toml` dùng provider riêng, bearer local, `supports_websockets=false`, retry 0, sandbox read-only.
- Workspace/profile cô lập cùng timestamp. Kế hoạch chạy: `CODEX_HOME=<home>` → `Code.exe --user-data-dir <profile> --disable-workspace-trust --new-window <workspace>`.
- Đọc source extension 26.1021.22027: extension tôn trọng `process.env.CODEX_HOME` (hàm `resolveCodexHome`) và chỉ spawn `codex app-server` với cờ feature, không ép provider — nên `config.toml` riêng có khả năng được dùng.

**Blocker:** Docker Desktop 4.40 treo lại sau idle; `docker` treo, rồi cả `wsl -l -v` cũng treo. Không thể chạy container edge. Đã thử kill process Docker + `wsl --shutdown` + relaunch nhưng WSL VM vẫn kẹt. Cần stop/start `WslService` bằng quyền admin hoặc reboot Windows. **Chưa từng mở instance VS Code thử nghiệm, chưa có kết quả UI.** Không thay đổi `~/.codex/config.toml`, `auth.json` hay cấu hình VS Code chính.

Bước tiếp theo khi hạ tầng ổn: reboot (hoặc admin reset WSL) → chạy `vscode_failover_service.py --failover` → mở instance VS Code cô lập → gửi prompt 1, xác nhận ACK → tạo file `arm-failover` → gửi prompt 2 trong cùng hội thoại, kiểm tra nonce và event đổi account. Cân nhắc giải phóng ổ C trước (chỉ còn ~6.7 GB).

## Failover tài khoản thật trên OpenCode — PASS, 04/11/2026

User chuyển từ VS Code sang OpenCode. Client: OpenCode `v2.2.5` (desktop CLI `opencode-cli.exe`), chạy `opencode run --standalone --format json` trong môi trường cô lập:

- `XDG_CONFIG_HOME`/`XDG_DATA_HOME`/`XDG_STATE_HOME`/`XDG_CACHE_HOME` trỏ vào `%LOCALAPPDATA%\MultiVibe-Codex-Pilot\opencode-pilot-20261104-095341`, không dùng config/DB của OpenCode chính.
- Provider `pilot_multivibe`, package `@opencode/ai/providers/openai-compatible/responses`, `baseURL=http://127.0.0.1:14755/v1`, model `gpt-5.6-sol`, credential lấy từ env `PILOT_PROXY_KEY` (không ghi vào config).
- Proxy: edge Rust trong Docker + relay quota, account 0/1/2 đều đủ headroom lúc kiểm tra (primary 0%, secondary 47/46/92).

Kết quả:

1. Lượt 1: reply đúng `ACK`, session `ses_e5b85d800ffeNJnPE43DnMWBGd`; upstream 200 trên account 1.
2. Tạo tiêu đề phiên (request phụ của OpenCode): account 1, 200; client abort sau khi nhận output (chỉ là traceback `ConnectionAbortedError` phía relay, đã thêm vào danh sách lỗi bỏ qua).
3. Lượt 2 dùng `--session` cũ: account 1 nhận 429 giả lập → edge chuyển **account 0**, upstream 200.
4. Reply lượt 2 đúng chính xác nonce `PILOT_OC_C3811E65`; cùng session; 0 tool event ở cả hai lượt.
5. Quét 9 file JSONL/log/state: không chứa access token/refresh token thật.
6. Không thay đổi config/DB OpenCode chính, không thay `~/.codex`.

Đây là **PASS cho OpenCode CLI với tài khoản thật**, cùng cơ chế HTTP/SSE + 429 mô phỏng. Chưa phải nghiệm thu TUI OpenCode dùng hằng ngày (cần cấu hình provider vào config chính và một proxy chạy thường trực), chưa thử quota cạn tự nhiên hay stream đứt giữa chừng.

### Cấu hình dùng thường trực trên OpenCode desktop — 04/11/2026

User dùng desktop app (GUI), nên đã cấu hình provider vào config chính:

- `~/.config/opencode/opencode.jsonc`: thêm provider `pilot_multivibe` (package `@opencode/ai/providers/openai-compatible/responses`, `baseURL=http://127.0.0.1:14755/v1`), model `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-5.3-codex`. Không đổi model mặc định, không đổi plugin hiện có.
- Backup: `opencode.jsonc.bak-20261104-102319`.
- Credential: `settings.apiKey = {file:...\MultiVibe-Codex-Pilot\proxy-key.txt}` — chỉ là bearer nội bộ của proxy, không phải token tài khoản OpenAI; file nằm trong thư mục pilot đã giới hạn ACL.
- Proxy thường trực: `opencode_proxy.py start|stop|status` (container `multivibe-opencode-proxy`, cổng 14755, **không có relay/429 giả lập** — chỉ failover khi upstream thật báo hết quota). Thêm `start --account N` để ghim một tài khoản (chỉ account đó được bật trong snapshot; **mất failover** cho tới khi chạy `start` không kèm `--account`). Snapshot account ghi tại `opencode-accounts.json` trong thư mục pilot (chứa token, không commit); trạng thái ghim ở `opencode-proxy-state.json`.
- Kiểm chứng: `opencode models` từ service dùng chung (desktop app) đã liệt kê `pilot_multivibe/*`; chạy `opencode run --standalone` bằng config thật **không có env** trả `PILOT_READY` (xác nhận `{file:}` hoạt động); gọi tool `read` đọc file thành công rồi trả lời đúng nội dung → tool call hoạt động qua proxy.

Lưu ý vận hành: Docker Desktop 4.40 trên máy này hay trả 500 sau idle. Khi đó kill toàn bộ process docker → `wsl --shutdown` → mở lại Docker Desktop → `python opencode_proxy.py start`. Rollback: chuyển model về model cũ trong app, hoặc khôi phục file backup (provider là block thêm vào, không ghi đè provider khác). Chưa thử quota cạn tự nhiên trên desktop app.

Cập nhật 04/11 trưa: user thêm tài khoản thứ 4 (`thanhsally.1994@gmail.com`) qua OAuth pilot. Store còn 4 account; snapshot của proxy được tạo lại và chạy **auto 4 tài khoản** (không ghim). Thứ tự ưu tiên theo quota tuần còn lại: #4 (88%) → #2 (54%) → #1 (53%) → #3 (8%). `start --account N` vẫn dùng để ghim khi cần.

## Tự động chuyển theo ngưỡng quota 5 giờ — 04/11/2026

User chốt chính sách: giữ tài khoản đang dùng cho tới khi quota 5 giờ còn **≤10%**, sau đó chuyển sang tài khoản đủ điều kiện có **quota tuần còn nhiều nhất**; mỗi lần chuyển phải **thông báo trong session**.

Kiến trúc mới (thay cho `opencode_proxy.py` khi cần tự động):

- `pilot_router.py` — HTTP router giữa edge Rust và `chatgpt.com`. Edge vẫn xác thực client, chuẩn hoá request, nhưng router **ghi đè Authorization** bằng token của tài khoản đang active. Router giữ active cho tới khi `primary_left <= 10`, hoặc upstream trả 429 quota (chuyển ngay + thử lại request một lần với account khác). Chọn ứng viên: `primary_left > 10`, `weekly_left > 0`, `enabled`, không `reauthRequired`; ưu tiên `weekly_left` lớn nhất.
- `pilot_service.py` — start/stop/status: Node control plane (1456), refresh quota mỗi 60 giây, router 14757, edge container `multivibe-pilot-edge` (14755), snapshot `pilot-accounts.json`. Chạy detached, PID ở `pilot-service.pid`, trạng thái ở `pilot-service-state.json`.
- `pilot-switch-events.jsonl` — log sự kiện chuyển (account cũ/mới, lý do, quota 5 giờ/tuần). Không chứa token.
- Plugin OpenCode `plugins/pilot-switch-notifier` — poll file sự kiện, tìm session đang dùng provider `pilot_multivibe`, gửi **synthetic message** vào session (không tạo lượt gọi model). Đã thêm vào `~/.config/opencode/opencode.jsonc`; backup `opencode.jsonc.bak-20261104-143710`.
- `quota_cards.py` — in quota dạng thẻ tiến trình, đánh số 1..N.

Kiểm chứng ngày 04/11:

- Unit test chính sách (`router_policy_test.py` trong `%TEMP%`): chọn đúng account nhiều quota tuần nhất; khi active còn 5% 5 giờ thì chuyển sang account weekly 60%; event `threshold` đúng; `quota_error_switch` chọn lại account weekly 90%. **PASS**.
- End-to-end qua OpenCode CLI + config thật: request `PILOT_FINAL_OK`, router ghi `account: 4, status: 200`. **PASS**.
- Plugin: session pilot tạm, chèn event thử → synthetic message `🔄 Đã chuyển tài khoản #4 → #1...` xuất hiện trong session; session test đã xoá. **PASS**.
- Chưa chờ quota thật tụt qua ngưỡng 10% để chứng kiến chuyển thật; chưa thử 429 giữa stream; `/goal` chỉ được đảm bảo chuyển giữa các lần gọi model, không đảm bảo nếu quota cạn giữa một stream đang chạy.

Vận hành: `python pilot_service.py start|status|stop`. Nếu Docker trả 500 sau idle: kill process docker → `wsl --shutdown` → mở Docker → start lại. `opencode_proxy.py` cũ không có router/auto-switch; chỉ dùng khi cần proxy tối giản.

Cập nhật 04/11 chiều: chính sách đã chạy thật qua service detached (`pid` trong `pilot-service.pid`), router active #4, quota 5 giờ 78%, tuần 87%; account #4 được dùng cho request kiểm tra cuối.
