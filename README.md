# AiLab

## Giới thiệu

AiLab là một hệ thống thu thập, xử lý, hiển thị và phân tích dữ liệu cảm biến chuyển động (IMU) theo thời gian thực. Hệ thống được thiết kế với kiến trúc module, hỗ trợ các thuật toán xử lý động học (tính toán vận tốc, dịch chuyển từ gia tốc), các bộ lọc tín hiệu linh hoạt (Butterworth high-pass, low-pass), và các phương pháp loại bỏ trôi (detrending) đa dạng như Recursive Least Squares (RLS) và Polynomial Fitting.

Ứng dụng sở hữu giao diện đồ họa người dùng (GUI) trực quan xây dựng bằng PyQt6, hiển thị dữ liệu theo thời gian thực dưới dạng đồ thị (gia tốc, vận tốc, dịch chuyển, phổ tần số FFT). Nó cung cấp các công cụ mạnh mẽ cho cả người dùng cuối muốn theo dõi và ghi lại dữ liệu, lẫn các nhà phát triển và nhà nghiên cứu muốn tùy chỉnh, mở rộng các thuật toán xử lý và phân tích.

**Các tính năng chính:**

* **Thu thập dữ liệu đa cảm biến:** Quản lý và thu thập dữ liệu từ nhiều cảm biến đồng thời (hiện tại hỗ trợ cảm biến WITMOTION IMU qua UART và cảm biến giả lập).
* **Xử lý tín hiệu thời gian thực:**
    * Tính toán động học: Gia tốc -> Vận tốc -> Dịch chuyển.
    * Các phương pháp tích phân: Trapezoidal, Simpson, Rectangular.
    * Loại bỏ trôi (Detrending): RLS, Polynomial, hoặc không sử dụng.
    * Lọc tín hiệu đầu vào: High-pass, Low-pass Butterworth.
    * Phân tích phổ tần số (FFT) thời gian thực.
* **Hiển thị trực quan:**
    * Đồ thị thời gian thực cho gia tốc, vận tốc, dịch chuyển (từng trục X, Y, Z).
    * Đồ thị FFT thời gian thực cho tín hiệu gia tốc (từng trục X, Y, Z).
    * Hiển thị tần số đặc trưng.
* **Quản lý cảm biến:** Giao diện thêm, xóa, kết nối, ngắt kết nối cảm biến. Hiển thị thông tin chi tiết và trạng thái cảm biến.
* **Cấu hình linh hoạt:**
    * Điều chỉnh tần số làm mới đồ thị.
    * Tùy chỉnh các tham số của bộ xử lý động học (kích thước frame, hệ số quên RLS, số frame khởi động).
    * Tùy chỉnh các tham số xử lý tín hiệu nâng cao (bộ lọc đầu vào, phương pháp tích phân, phương pháp detrending và tham số của chúng).
* **Phân tích dữ liệu nâng cao (Offline):**
    * **Phân tích một cảm biến:** Thống kê mô tả, phân tích tương quan, phân tích phân phối (histogram), FFT chi tiết, phát hiện bất thường (Z-score, Moving Average, Sudden Changes).
    * **Phân tích đa cảm biến:** Overlay đồ thị nhiều dòng dữ liệu, phân tích tương quan giữa các dòng dữ liệu, đồ thị chênh lệch.
* **Truyền và Xuất dữ liệu:**
    * Xuất dữ liệu dạng bảng ra file CSV.
    * Truyền dữ liệu (raw/processed) qua MQTT publisher.
* **Theo dõi tài nguyên hệ thống:** Hiển thị đồ thị sử dụng CPU và RAM.
* **Ngôn ngữ:** Ứng dụng hỗ trợ tiếng Việt (chủ yếu trong GUI) và tiếng Anh (trong code).

## Yêu cầu hệ thống

* **Python:** >= 3.9 (khuyến nghị Python 3.11)
* **Hệ điều hành:** Linux, Windows, hoặc macOS (chưa kiểm thử kỹ trên macOS)
* **Các thư viện Python:** Xem chi tiết trong file `requirements.txt`. Các thư viện chính bao gồm:
    * `PyQt6>=6.0.0`
    * `numpy>=1.21.0`
    * `scipy>=1.7.0`
    * `pyserial>=3.5`
    * `pyqtgraph` (được import trong code, nên thêm vào `requirements.txt`)
    * `psutil` (được import trong code, nên thêm vào `requirements.txt`)
    * `paho-mqtt` (được import trong code, nên thêm vào `requirements.txt`)
* **Cổng kết nối cảm biến:** Ví dụ: Cổng USB/UART cho cảm biến IMU.

## Hướng dẫn cài đặt

1.  **Clone repository:**
    ```bash
    git clone <repo_url>
    cd AiLab
    ```
2.  **Tạo môi trường ảo (khuyến nghị):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Trên Linux/macOS
    # venv\Scripts\activate  # Trên Windows
    ```
3.  **Cài đặt thư viện phụ thuộc:**
    ```bash
    pip install -r requirements.txt
    # Có thể cần cài đặt thêm: pip install pyqtgraph psutil paho-mqtt
    ```
4.  **Kết nối cảm biến IMU** (nếu có). Đảm bảo driver cho cổng COM/USB đã được cài đặt.
5.  **Chạy ứng dụng:**
    ```bash
    python3 main.py
    ```

## Hướng dẫn sử dụng cho Người dùng cuối 🧑‍🔬

1.  **Tab "Quản lý cảm biến":**
    * **Thêm cảm biến:** Nhấn "Thêm Cảm biến Mới".
        * Đặt tên, chọn loại cảm biến (ví dụ: `wit_motion_imu`, `mock_sensor`).
        * Chọn giao thức (ví dụ: UART cho WITMOTION).
        * Điền thông tin kết nối (cổng COM, tốc độ baud).
        * Cấu hình các thông số đặc thù của cảm biến nếu có (ví dụ: WIT Data Rate).
        * Nhấn "OK".
    * **Kết nối/Ngắt kết nối:** Sử dụng nút "Nối"/"Ngắt" trong bảng danh sách cảm biến hoặc từ menu chuột phải.
    * **Xem chi tiết:** Click đúp hoặc chuột phải -> "Xem Chi tiết" để xem thông tin cấu hình và dữ liệu raw gần nhất của cảm biến.
    * **Xóa cảm biến:** Chọn cảm biến và dùng menu chuột phải -> "Xóa Cảm biến" hoặc nút "Xóa Cảm biến Không Hoạt động".

2.  **Tab "Hiển thị đồ thị":**
    * **Chọn cảm biến:** Chọn cảm biến từ menu dropdown để hiển thị dữ liệu.
    * **Xem dữ liệu:** Dữ liệu gia tốc, vận tốc, dịch chuyển (theo 3 trục X, Y, Z) và phổ tần số (FFT của gia tốc) sẽ được hiển thị theo thời gian thực.
    * **Tần số đặc trưng:** Hiển thị các tần số chính từ FFT.
    * **Tùy chỉnh đồ thị:** (Hiện tại placeholder) Cho phép thay đổi màu sắc các đường đồ thị.

3.  **Tab "Thiết lập":**
    * **Tốc độ làm mới đồ thị:** Chọn tần số cập nhật cho các đồ thị ở tab "Hiển thị đồ thị".
    * **Cấu hình Bộ xử lý Động học & Xử lý Tín hiệu Nâng cao:**
        * Các cài đặt này áp dụng cho **cảm biến đang được chọn ở tab "Hiển thị đồ thị"**.
        * **Bộ xử lý Động học:** Điều chỉnh `Kích thước Frame Mẫu`, `Bội số Frame Tính toán`, `Hệ số Quên RLS` (nếu dùng RLS detrending), `Số Frame Khởi động`.
        * **Xử lý Tín hiệu Nâng cao:**
            * `Bộ lọc Gia tốc Đầu vào`: Chọn `None`, `High-pass`, hoặc `Low-pass`. Cấu hình `Tần số cắt` và `Bậc lọc`.
            * `Phương pháp Tích phân`: Hiện tại hỗ trợ `Trapezoidal`.
            * `Phương pháp Loại bỏ Xu hướng`: Chọn `RLS Filter` (mặc định cho `KinematicProcessor`), `None`. (Polynomial có thể được cấu hình nếu `KinematicProcessor` được mở rộng để chọn `PolynomialDetrender` từ `detrenders.py`).
        * Nhấn **"Áp dụng Tất cả Cài đặt..."** để lưu thay đổi cho cảm biến hiện tại. Dữ liệu của cảm biến đó sẽ được reset và xử lý lại với tham số mới.

4.  **Tab "Phân tích chuyên sâu" (Một cảm biến):**
    * Chọn cảm biến từ tab "Hiển thị đồ thị" trước.
    * **Thêm/Sửa Trường Phân tích:** Chọn các dòng dữ liệu (ví dụ: AccX, VelY, DispZ, RawAccX\_for\_fft) bạn muốn phân tích.
    * **Số điểm phân tích:** Chọn số lượng điểm dữ liệu gần nhất để tải vào phân tích.
    * **Tải và Phân tích Dữ liệu:** Nút này sẽ lấy snapshot dữ liệu hiện tại của cảm biến đang được chọn ở tab "Hiển thị đồ thị".
    * **Các tab phân tích con:**
        * `Thống kê Mô tả`: Mean, Median, Std Dev, Min, Max, Variance.
        * `Phân tích Tương quan`: Ma trận và heatmap tương quan giữa các trường đã chọn.
        * `Phân tích Phân phối`: Histogram cho từng trường dữ liệu.
        * `FFT Chi tiết`: Đồ thị FFT cho trường dữ liệu gia tốc thô đã chọn.
        * `Phân tích Bất thường`: Phát hiện điểm bất thường (Z-score, Moving Average, Sudden Changes).

5.  **Tab "Phân tích đa cảm biến":**
    * **Chọn Cảm biến và Trường Dữ liệu:** Từ cây danh sách, chọn (check) các trường dữ liệu từ nhiều cảm biến khác nhau (chỉ các cảm biến đang kết nối mới hiển thị).
    * **Cấu hình Phân tích:**
        * `Loại Phân tích`: Chọn `Overlay Đồ thị`, `Phân tích Tương quan`, hoặc `Đồ thị Chênh lệch`.
        * `Số điểm dữ liệu/stream`: Số điểm dữ liệu gần nhất từ mỗi stream đã chọn.
        * Nếu là `Đồ thị Chênh lệch`, chọn Stream A và Stream B từ các stream đã check ở trên.
    * **Chạy Phân tích:** Thực hiện phân tích và hiển thị kết quả ở tab tương ứng.

6.  **Tab "Truyền/Nhận dữ liệu":**
    * **Hiển thị Dữ liệu Dạng Bảng:**
        * Chọn cảm biến (hoặc tất cả) để xem dữ liệu dạng bảng. Dữ liệu bao gồm timestamp, sensor ID, và các giá trị raw/processed.
        * Nhấn "Cập nhật Bảng" để cấu hình lại các cột dựa trên lựa chọn cảm biến và loại dữ liệu (raw/processed) được chọn trong phần MQTT.
        * "Xuất ra CSV": Lưu dữ liệu đang hiển thị trong bảng ra file CSV.
    * **Truyền Dữ liệu qua MQTT (Publisher):**
        * Cấu hình thông tin MQTT Broker (địa chỉ, cổng, client ID, user/pass nếu có).
        * Nhập tiền tố Topic (ví dụ: `sensor/data/`). Topic cuối cùng sẽ là `tiền_tố/sensor_id`.
        * Chọn loại dữ liệu muốn gửi: "Gửi Dữ liệu Thô" và/hoặc "Gửi Dữ liệu Đã Xử lý".
        * Nhấn "Kết nối MQTT". Sau khi kết nối thành công, dữ liệu từ các cảm biến đang hoạt động sẽ được gửi đi.
        * Xem log MQTT để theo dõi trạng thái và tin nhắn đã gửi.
    * **Cài đặt Hiệu suất:**
        * `Tần suất cập nhật`: Tần suất làm mới bảng dữ liệu.
        * `Số dòng hiển thị tối đa`: Giới hạn số dòng trong bảng dữ liệu để tối ưu hiệu năng.

## Hướng dẫn cho Developer 👨‍💻

### Cấu trúc thư mục/code:

* `main.py`: Điểm khởi động ứng dụng.
* `core/`: Logic xử lý chính của ứng dụng.
    * `sensor_core.py`: Quản lý kết nối, giao tiếp và luồng dữ liệu từ các cảm biến (`SensorManager`, `SensorInstance`, `GenericSensorWorker`).
    * `data_processor.py`: Xử lý dữ liệu thô từ cảm biến, áp dụng các thuật toán động học, lọc, FFT. Quản lý dữ liệu cho từng cảm biến.
    * `plot_manager.py`: Quản lý việc cập nhật đồ thị trên giao diện.
* `algorithm/`: Các thuật toán xử lý tín hiệu và tính toán động học.
    * `kinematic_processor.py`: Module chính xử lý động học, tích hợp gia tốc thành vận tốc và dịch chuyển, áp dụng detrending.
    * `integrator.py`: Các phương pháp tích phân số (Trapezoidal, Simpson, Rectangular).
    * `filters.py`: Các bộ lọc tín hiệu (High-pass, Low-pass Butterworth).
    * `detrenders.py`: Các phương pháp loại bỏ trôi (RLS, Polynomial).
    * `rls_filter.py`: Một class `RLSFilter` khác (có thể là phiên bản cũ hơn hoặc cho mục đích khác, `KinematicProcessor` sử dụng `detrenders.RLSDetrender`).
    * `rls_flt_disp.py`: Dường như là một module cũ/thử nghiệm cho tích hợp RLS.
* `sensor/`: Các module liên quan đến việc xử lý dữ liệu đặc thù của từng loại cảm biến.
    * `device_model.py`: Định nghĩa `WitDataProcessor` để xử lý dữ liệu từ cảm biến WITMOTION và `MockDataProcessor` để giả lập dữ liệu.
* `ui/`: Các thành phần giao diện người dùng (PyQt6).
    * `main_window.py`: Cửa sổ chính của ứng dụng, chứa các tab.
    * `display_screen.py`: Tab hiển thị đồ thị thời gian thực.
    * `sensor_management_screen.py`: Tab quản lý cảm biến.
    * `settings_screen.py`: Tab cấu hình tham số xử lý.
    * `advanced_analysis_screen.py`: Tab phân tích dữ liệu chuyên sâu cho một cảm biến.
    * `multi_sensor_analysis_screen.py`: Tab phân tích dữ liệu từ nhiều cảm biến.
    * `data_hub_screen.py`: Tab hiển thị dữ liệu bảng và truyền MQTT.
* `analysis/`: Các công cụ phân tích dữ liệu.
    * `statistical_tools.py`: Thống kê mô tả, ma trận tương quan, histogram.
    * `spectral_tools.py`: Tính toán FFT, tìm tần số đặc trưng.
    * `anomaly_detection_tools.py`: Các hàm phát hiện bất thường.
* `workers/`: (Dường như là thư mục cũ)
    * `sensor_worker.py`: Phiên bản cũ hơn của luồng xử lý cảm biến, logic hiện tại nằm trong `core/sensor_core.py`.
* `resources/`: (Được đề cập trong README gốc, nhưng không có file nào được cung cấp) Icon, file cấu hình, v.v.

### Mở rộng thuật toán

Tham khảo hướng dẫn trong `README.md` gốc. Cơ bản:

* **Thêm bộ lọc mới:** Tạo class mới trong `algorithm/filters.py` kế thừa `Filter`, triển khai `apply()`, và đăng ký trong `create_filter()`.
* **Thêm phương pháp tích phân:** Tạo class mới trong `algorithm/integrator.py` kế thừa `Integrator`, triển khai `integrate()`, và đăng ký trong `create_integrator()`.
* **Thêm phương pháp detrending:** Tạo class mới trong `algorithm/detrenders.py` kế thừa `Detrender`, triển khai `detrend()`, và đăng ký trong `create_detrender()`.
* **Thêm tham số UI:** Sửa file UI tương ứng trong `ui/` (ví dụ: `ui/settings_screen.py`) và cập nhật logic truyền tham số vào `DataProcessor` hoặc `KinematicProcessor`.

### Mở rộng hỗ trợ cảm biến mới

1.  **Tạo Data Processor mới (trong `sensor/`):**
    * Nếu cảm biến có giao thức riêng, tạo một class tương tự `WitDataProcessor` để phân tích dữ liệu thô từ cảm biến đó. Class này nên có phương thức `process_byte(byte_val)` hoặc tương đương để xử lý từng byte/gói tin và cập nhật dữ liệu vào `self.device.data` (một instance của `DeviceModel`).
    * Implement các hàm cần thiết như `configure_data_rate` nếu cảm biến hỗ trợ.
2.  **Cập nhật `GenericSensorWorker` (trong `core/sensor_core.py`):**
    * Thêm logic trong `run()` để khởi tạo và sử dụng Data Processor mới của bạn dựa trên `sensor_type` hoặc `protocol` từ `config`.
    * Xử lý việc đọc dữ liệu từ cổng (serial, network, etc.) và truyền cho Data Processor của cảm biến.
3.  **Cập nhật `AddSensorDialog` (trong `ui/sensor_management_screen.py`):**
    * Thêm `sensor_type` mới vào `self.sensor_type_combo`.
    * Trong `_update_specific_config_fields()`, thêm các trường cấu hình đặc thù cho loại cảm biến mới (nếu có).
    * Trong `get_sensor_config()`, đảm bảo lấy đúng các giá trị cấu hình này.
4.  **Cập nhật `DataProcessor` (trong `core/data_processor.py`):**
    * Trong `handle_incoming_sensor_data()`, điều chỉnh logic lấy `_dt` và xử lý dữ liệu (ví dụ: chuyển đổi đơn vị, loại bỏ offset) cho `sensor_type` mới nếu cần. WITMOTION IMU có xử lý đặc biệt cho `accZ_ms2` (trừ 1.0G).
5.  **(Tùy chọn) Cập nhật `DEFAULT_SENSOR_DATA_KEYS` (trong `ui/data_hub_screen.py`):**
    * Thêm key mặc định cho loại cảm biến mới để DataHub có thể hiển thị cột mặc định.

### Quy ước code

* Tuân thủ PEP8.
* Đặt tên biến, hàm, class rõ ràng, sử dụng tiếng Anh.
* Sử dụng logging (module `logging` của Python) để ghi lại các thông tin quan trọng, warning, error.
* Tách biệt rõ ràng giữa logic xử lý dữ liệu (`core/`, `algorithm/`, `sensor/`) và giao diện người dùng (`ui/`).
* Đảm bảo tính tương thích ngược (backward compatibility) khi có thể trong quá trình mở rộng.
* Viết docstring cho các hàm và class quan trọng.

## Đóng góp & Liên hệ

* Đóng góp rất được hoan nghênh! Vui lòng tạo pull request hoặc issue trên repository Github của dự án.
* Liên hệ: `dung2002lca1@gmail.com`
* Tác giả: Aitogy R&D Team
