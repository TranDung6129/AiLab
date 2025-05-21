# BaseRealTimeDisplacement

## Giới thiệu
BaseRealTimeDisplacement là một hệ thống thu thập, xử lý và hiển thị dữ liệu cảm biến chuyển động (IMU) theo thời gian thực, hỗ trợ các thuật toán xử lý động học, lọc tín hiệu, và các phương pháp loại bỏ trôi (detrending) linh hoạt. Ứng dụng có giao diện đồ họa (GUI) sử dụng PyQt6, phù hợp cho cả người dùng cuối lẫn nhà phát triển muốn mở rộng thuật toán.

## Yêu cầu hệ thống
- Python >= 3.9 (khuyến nghị Python 3.11)
- Hệ điều hành: Linux, Windows, hoặc macOS
- Các thư viện Python: xem `requirements.txt`
- Cổng kết nối cảm biến (ví dụ: USB/UART cho IMU)

## Hướng dẫn cài đặt
1. **Clone repository:**
   ```bash
   git clone <repo_url>
   cd BaseRealTimeDisplacement
   ```
2. **Cài đặt thư viện phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Kết nối cảm biến IMU** (nếu có).
4. **Chạy ứng dụng:**
   ```bash
   python3 main.py
   ```

## Hướng dẫn sử dụng cho người dùng cuối
- **Kết nối cảm biến:** Chọn cổng và loại cảm biến trong giao diện, nhấn "Kết nối".
- **Xem dữ liệu:** Dữ liệu gia tốc, vận tốc, dịch chuyển và phổ tần số sẽ được hiển thị theo thời gian thực.
- **Cấu hình thuật toán:** Vào mục "Cài đặt" để chọn phương pháp tích phân (Trapezoidal, Simpson, Rectangular), phương pháp detrending (RLS, Polynomial, None), và các tham số lọc tín hiệu (High-pass, Low-pass, cutoff, order).
- **Lưu/Phân tích dữ liệu:** Có thể lưu dữ liệu hoặc xuất báo cáo phân tích.
- **Ngôn ngữ:** Ứng dụng hỗ trợ tiếng Việt và tiếng Anh.

## Hướng dẫn cho Developer
### Cấu trúc thư mục/code:
- `main.py`: Điểm khởi động ứng dụng.
- `core/`: Xử lý dữ liệu, quản lý cảm biến, logic chính.
  - `data_processor.py`: Quản lý dữ liệu, cập nhật tham số, xử lý tín hiệu.
- `algorithm/`: Các thuật toán xử lý tín hiệu, động học.
  - `kinematic_processor.py`: Xử lý động học, tích hợp và detrending.
  - `integrator.py`: Các phương pháp tích phân.
  - `filters.py`: Các bộ lọc tín hiệu (High-pass, Low-pass, ...).
  - `detrenders.py`: Các phương pháp loại bỏ trôi (RLS, Polynomial, ...).
- `ui/`: Giao diện người dùng (PyQt6), các màn hình, widget.
- `resources/`: Icon, file cấu hình, v.v.

### Mở rộng thuật toán
- **Thêm bộ lọc mới:** Tạo class mới trong `algorithm/filters.py` kế thừa `Filter`, đăng ký qua `create_filter()`.
- **Thêm phương pháp tích phân:** Tạo class mới trong `algorithm/integrator.py` kế thừa `Integrator`, đăng ký qua `create_integrator()`.
- **Thêm phương pháp detrending:** Tạo class mới trong `algorithm/detrenders.py` kế thừa `Detrender`, đăng ký qua `create_detrender()`.
- **Thêm tham số UI:** Sửa `ui/settings_screen.py` và truyền tham số vào `DataProcessor`.

### Quy ước code
- Tuân thủ PEP8, đặt tên rõ ràng, logging đầy đủ.
- Tách biệt rõ giữa xử lý dữ liệu (core/algorithm) và giao diện (ui/).
- Đảm bảo backward compatibility khi mở rộng.

## Đóng góp & Liên hệ
- Đóng góp qua pull request hoặc issue trên Github.
- Liên hệ: [your_email@example.com]
- Tác giả: Aitogy Team
