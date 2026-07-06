# Test Report - Crypto Quest Game

## 1. Mục đích
Báo cáo này ghi nhận kết quả kiểm thử các chức năng chính của trò chơi học mật mã, bao gồm luồng chơi, điểm số, tiến độ, giải thích kiến thức và màn phát hiện lỗi bảo mật.

## 2. Môi trường kiểm thử
- Hệ điều hành: Windows
- Python: 3.13
- Framework: Flask
- Cơ sở dữ liệu: SQLite
- Công cụ kiểm thử: unittest

## 3. Các trường hợp kiểm thử

### TC01 - Đăng ký tài khoản mới
- Mục tiêu: Kiểm tra người dùng có thể đăng ký thành công.
- Kết quả: Thành công.
- Ghi chú: Hệ thống tạo tài khoản mới và lưu vào cơ sở dữ liệu.

### TC02 - Đăng nhập thành công
- Mục tiêu: Kiểm tra đăng nhập bằng tài khoản hợp lệ.
- Kết quả: Thành công.
- Ghi chú: Người dùng được cấp phiên đăng nhập và truy cập trò chơi.

### TC03 - Hoàn thành màn chơi đầu tiên
- Mục tiêu: Kiểm tra màn 1 có thể được hoàn thành đúng.
- Kết quả: Thành công.
- Ghi chú: Điểm tăng và tiến độ được cập nhật.

### TC04 - Nhập đáp án sai
- Mục tiêu: Kiểm tra hệ thống xử lý đáp án sai.
- Kết quả: Thành công.
- Ghi chú: Hệ thống trả về thông báo lỗi và giảm số lần thử.

### TC05 - Kiểm tra tính điểm
- Mục tiêu: Kiểm tra điểm được cộng đúng khi hoàn thành màn chơi.
- Kết quả: Thành công.
- Ghi chú: Điểm được tăng theo mức độ màn chơi.

### TC06 - Kiểm tra lưu tiến độ
- Mục tiêu: Kiểm tra hệ thống ghi nhớ màn chơi hiện tại sau khi đăng nhập lại.
- Kết quả: Thành công.
- Ghi chú: current_level được lưu và phục hồi đúng.

### TC07 - Kiểm tra giải thích kiến thức
- Mục tiêu: Kiểm tra mỗi màn có nội dung giải thích sau khi hoàn thành.
- Kết quả: Thành công.
- Ghi chú: API trả về trường explanation cho màn chơi.

### TC08 - Kiểm tra màn phát hiện lỗi bảo mật
- Mục tiêu: Kiểm tra người chơi có thể nhận biết và chọn đúng lỗi bảo mật ở màn 6 và 7.
- Kết quả: Thành công.
- Ghi chú: Hệ thống chấp nhận đáp án đúng cho các tình huống nonce reuse và replay attack.

## 4. Kết quả chạy test
Đã thực hiện kiểm thử bằng lệnh:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Kết quả:
- Tổng số test: 4
- Trạng thái: Passed
- Ghi chú: Không có lỗi kiểm thử nào.

## 5. Kết luận
Hệ thống hiện tại đã đáp ứng được các luồng kiểm thử cơ bản của trò chơi, bao gồm đăng nhập, giải màn chơi, tính điểm, lưu tiến độ và hiển thị giải thích kiến thức. Tuy nhiên, để phù hợp hơn với yêu cầu bài tập lớn, nên bổ sung thêm các test bảo mật nâng cao như kiểm tra replay, sai khóa, dữ liệu bị sửa đổi và quyền truy cập không hợp lệ.
