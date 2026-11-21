# Bản sửa preview timeline — 13/11/2026

- Source: `https://github.com/YangYu10410/opencode-desktop-timeline`, commit `1fd894c7aa22a35c62a360fce467c35f2360cac7`, version `0.1.2`.
- Bản trước đang dùng: npm `0.1.1`. CSS cũ đặt nền `var(--oc-bg, #fff)` nhưng không ghép màu chữ theo theme; chữ sáng trên nền trắng khiến preview trông gần như trống.
- Source upstream 0.1.2 đã dùng theme token V2 và fallback `Canvas`/`CanvasText`.
- Sửa local trong `src/gui.tsx`: thêm `box-sizing`, giới hạn card theo chiều rộng viewport, cho tin nhắn dài/URL dài xuống hàng.
- Đã build lại `gui-experimental.cjs`, không chỉnh `app.asar` và không sửa npm cache.

## Cấu hình

- Trong `C:/Users/admin/.config/opencode/opencode.jsonc`, chỉ thay entry npm của timeline bằng `E:/opencode learn/plugins/opencode-desktop-timeline`.
- Backup trước khi sửa: `C:/Users/admin/.config/opencode/opencode.jsonc.bak-timeline-preview-20261113`.
- OpenCode theo dõi thay đổi config. Nếu cửa sổ còn giữ GUI bundle cũ, reload cửa sổ desktop bằng `Ctrl+R`; không cần restart background service chỉ để áp dụng config.
- Hoàn tác riêng plugin: thay entry local về `opencode-desktop-timeline`; không ghi đè toàn bộ config bằng backup nếu có thay đổi mới khác.

## Kiểm tra

- `npm ci --ignore-scripts --no-audit --no-fund`: đạt.
- `npm run build`: đạt. Vite cảnh báo `outDir` trùng root là cấu hình có sẵn của upstream.
- `node --check gui-experimental.cjs`: đạt.
- Browser Chromium trong OpenCode: fixture **16/16 tổ hợp đạt**, gồm light/dark × viewport 320/1280 px × font 14/20 px × có/không có theme token V2.
- Mỗi tổ hợp kiểm tra: card nằm trong viewport, không tràn ngang, tin nhắn dài xuống hàng, màu nền/chữ khác nhau, card cuộn được.
- Chạy fixture: `node tests/preview-server.mjs`; mở `http://127.0.0.1:14879`, chạy expression trong `tests/preview-browser.js` qua DevTools hoặc browser.evaluate.
- Fixture chỉ dùng dữ liệu giả. Chưa xác nhận lại hover và click-to-jump trên hội thoại thực sau khi cửa sổ desktop reload.
