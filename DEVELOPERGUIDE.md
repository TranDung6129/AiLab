# Developer Guide: AiLab
**1. Tổng quan kiến trúc**

Vui lòng tham khảo mục **3. Kiến trúc hệ thống** và **Sơ đồ luồng dữ liệu chính** trong file **Đặc tả hệ thống** để có cái nhìn tổng quan.

**Các thành phần cốt lõi:**

* **`SensorManager` (`core/sensor_core.py`):** Quản lý việc thêm, bớt, kết nối, ngắt kết nối các `SensorInstance`. Mỗi `SensorInstance` chạy `GenericSensorWorker` trong một QThread riêng để không chặn luồng UI chính.
* **`GenericSensorWorker` (`core/sensor_core.py`):** Chịu trách nhiệm giao tiếp trực tiếp với phần cứng cảm biến (hoặc giả lập). Nó sử dụng các "device processor" từ `sensor/device_model.py` (ví dụ: `WitDataProcessor`) để phân tích dữ liệu thô.
* **`DataProcessor` (`core/data_processor.py`):** Trung tâm xử lý dữ liệu. Nhận dữ liệu từ `SensorManager`, áp dụng các bước tiền xử lý, tính toán động học (thông qua `KinematicProcessor`), FFT, và lưu trữ kết quả. Cung cấp dữ liệu cho `PlotManager` và các màn hình phân tích.
* **`KinematicProcessor` (`algorithm/kinematic_processor.py`):** Xử lý chính việc chuyển đổi gia tốc thành vận tốc và dịch chuyển. Nó sử dụng các `Integrator` và `Detrender` có thể cấu hình.
* **`MainWindow` (`ui/main_window.py`):** Khởi tạo tất cả các thành phần chính và các màn hình UI (tabs), kết nối các signals/slots giữa chúng.

**2. Hướng dẫn thiết lập môi trường phát triển**

1.  **Clone repository.**
2.  **Tạo và kích hoạt môi trường ảo Python:**
    ```bash
    python -m venv venv
    # Linux/macOS:
    source venv/bin/activate
    # Windows:
    # venv\Scripts\activate
    ```
3.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirements.txt
    pip install pyqtgraph psutil paho-mqtt # Các thư viện này được sử dụng nhưng chưa có trong requirements.txt gốc
    ```
4.  **IDE:** Sử dụng một IDE hỗ trợ Python như VS Code, PyCharm.

**3. Quy trình làm việc và Gỡ lỗi (Debugging)**

* **Điểm bắt đầu:** `main.py` khởi tạo `QApplication` và `MainWindow`.
* **Logging:** Hệ thống sử dụng module `logging` của Python. Các thông điệp log được in ra console và có thể được cấu hình để ghi ra file. Tăng/giảm `level` trong `logging.basicConfig` ở `main.py` để xem chi tiết hơn hoặc ít hơn.
    * Ví dụ, để xem log DEBUG từ một module cụ thể:
        ```python
        # ở đầu file module đó
        import logging
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG) # Hoặc cấu hình ở main.py
        ```
* **Gỡ lỗi GUI:** Sử dụng các công cụ debug của IDE. PyQt6 cũng có một số cơ chế introspect.
* **Kiểm tra dữ liệu:**
    * Sử dụng tab "Quản lý cảm biến" -> "Xem Chi tiết" để xem dữ liệu raw gần nhất mà `GenericSensorWorker` nhận được.
    * Sử dụng tab "Truyền/Nhận dữ liệu" để xem dữ liệu dạng bảng (cả raw và processed) được `DataProcessor` quản lý.
    * Đặt breakpoint trong `DataProcessor.handle_incoming_sensor_data` hoặc trong các phương thức `process_frame` của `KinematicProcessor` để theo dõi quá trình xử lý.
* **Sử dụng Mock Sensor:** Khi không có cảm biến vật lý, sử dụng "mock_sensor" để kiểm tra luồng dữ liệu và các thuật toán xử lý. Dữ liệu mock được tạo trong `sensor/device_model.py:MockDataProcessor`.

**4. Mở rộng Hệ thống**

**4.1. Thêm thuật toán xử lý mới**

* **Bộ lọc (Filter):**
    1.  Vào `algorithm/filters.py`.
    2.  Tạo một class mới kế thừa từ `Filter`.
    3.  Triển khai phương thức `apply(self, data)` để thực hiện logic lọc.
    4.  Trong hàm `create_filter(filter_type, cutoff_freq, fs, order)`, thêm một nhánh `elif` để khởi tạo class lọc mới của bạn dựa trên `filter_type`.
    5.  Cập nhật UI (ví dụ: `ui/settings_screen.py`) để cho phép người dùng chọn bộ lọc mới và cấu hình các tham số của nó. Truyền các tham số này đến `DataProcessor`, sau đó đến `KinematicProcessor` hoặc nơi áp dụng bộ lọc.
* **Phương pháp Tích phân (Integrator):**
    1.  Vào `algorithm/integrator.py`.
    2.  Tạo một class mới kế thừa từ `Integrator`.
    3.  Triển khai phương thức `integrate(self, data_series)`
    4.  Trong hàm `create_integrator(method, dt)`, thêm một nhánh `elif` để khởi tạo integrator mới.
    5.  Cập nhật UI (`ui/settings_screen.py`) để cho phép chọn phương pháp mới. Truyền lựa chọn này đến `DataProcessor` để khởi tạo `KinematicProcessor` với integrator tương ứng.
* **Phương pháp Loại bỏ Trôi (Detrender):**
    1.  Vào `algorithm/detrenders.py`.
    2.  Tạo một class mới kế thừa từ `Detrender`.
    3.  Triển khai phương thức `detrend(self, data, time_vector)`.
    4.  Trong hàm `create_detrender(method, params)`, thêm một nhánh `elif` để khởi tạo detrender mới.
    5.  Cập nhật UI (`ui/settings_screen.py`) để cho phép chọn phương pháp mới và các tham số liên quan. Truyền lựa chọn này đến `DataProcessor` để khởi tạo `KinematicProcessor`.

**4.2. Hỗ trợ loại cảm biến mới**

1.  **Tạo Device Processor (`sensor/device_model.py`):**
    * Tạo một class mới (ví dụ: `MyNewSensorProcessor`) để xử lý dữ liệu thô từ cảm biến.
    * Class này thường sẽ chứa một instance của `DeviceModel` (`self.device = DeviceModel()`).
    * Triển khai một phương thức để xử lý từng byte hoặc gói tin từ cảm biến (ví dụ: `process_byte(self, byte_val)` hoặc `process_packet(self, packet)`). Phương thức này sẽ giải mã dữ liệu và lưu vào `self.device.data` sử dụng `self.device.setDeviceData(key, value)`.
    * Nếu cảm biến yêu cầu cấu hình (ví dụ: data rate), triển khai các phương thức tương ứng.
    * Thuộc tính `is_connected` và `connection_error` nên được cập nhật.
2.  **Cập nhật `GenericSensorWorker` (`core/sensor_core.py`):**
    * Trong phương thức `run()`:
        * Thêm một khối `elif` cho `protocol` và/hoặc `sensor_type` của cảm biến mới.
        * Khởi tạo instance của `MyNewSensorProcessor`.
        * Viết logic để kết nối với cảm biến (ví dụ: mở cổng serial mới, kết nối TCP/IP).
        * Trong vòng lặp `while self._running_flag_from_manager:`, đọc dữ liệu từ cảm biến và truyền cho phương thức `process_byte/process_packet` của `MyNewSensorProcessor`.
        * Emit tín hiệu `newData` với `current_data = self.sensor_processor_internal.device.data.copy()`.
        * Xử lý ngắt kết nối và dọn dẹp tài nguyên.
    * Cập nhật logic tính `expected_dt` nếu cần.
3.  **Cập nhật UI để thêm cảm biến (`ui/sensor_management_screen.py:AddSensorDialog`):**
    * Thêm `sensor_type` mới vào `self.sensor_type_combo.addItems(...)`.
    * Trong `_update_connection_fields()`, nếu giao thức kết nối đặc biệt, thêm logic để hiển thị các trường input cần thiết.
    * Trong `_update_specific_config_fields()`, thêm các trường input cho cấu hình đặc thù của loại cảm biến mới.
    * Trong `get_sensor_config()`, đảm bảo rằng tất cả các thông tin cấu hình cần thiết cho cảm biến mới được thu thập và trả về.
4.  **Cập nhật `DataProcessor` (`core/data_processor.py`):**
    * Trong `handle_incoming_sensor_data()`:
        * Điều chỉnh logic xác định `_dt` (delta time) dựa trên `sensor_type` hoặc cấu hình của cảm biến mới.
        * Nếu cảm biến mới yêu cầu xử lý dữ liệu thô đặc biệt (ví dụ: chuyển đổi đơn vị khác, loại bỏ offset khác), thêm logic tương ứng trước khi đưa vào `KinematicProcessor`.
5.  **(Tùy chọn) Cập nhật `DEFAULT_SENSOR_DATA_KEYS` (trong `ui/data_hub_screen.py`):**
    * Nếu muốn Data Hub tự động hiển thị các cột dữ liệu mặc định cho loại cảm biến mới, thêm một entry vào `DEFAULT_SENSOR_DATA_KEYS`.

**4.3. Thêm công cụ phân tích mới**

1.  **Tạo hàm phân tích (trong `analysis/`):**
    * Tạo một file Python mới trong `analysis/` (ví dụ: `my_new_analysis_tools.py`) hoặc thêm hàm vào file hiện có.
    * Hàm phân tích nên nhận `data_dict` (dictionary các `np.ndarray`) và các `params` cần thiết.
    * Trả về kết quả phân tích ở định dạng phù hợp để hiển thị.
    * Cập nhật `analysis/__init__.py` để export hàm mới.
2.  **Cập nhật `AnalysisWorker` (`ui/advanced_analysis_screen.py` hoặc `ui/multi_sensor_analysis_screen.py`):**
    * Thêm một nhánh `elif` trong phương thức `run()` để gọi hàm phân tích mới của bạn dựa trên `self.analysis_type`.
3.  **Cập nhật Giao diện Người dùng:**
    * **Đối với Phân tích Một Cảm biến (`AdvancedAnalysisScreenWidget`):**
        * Thêm một tab mới vào `self.analysis_tabs`.
        * Thiết kế UI cho tab đó để hiển thị kết quả (ví dụ: sử dụng `QTableWidget`, `pg.PlotWidget`).
        * Cập nhật `TAB_ANALYSIS_TYPE_MAP` để ánh xạ tên tab với `analysis_type` mới.
        * Trong `handle_analysis_result()`, thêm logic để hiển thị kết quả cho loại phân tích mới.
        * Nếu cần tham số đầu vào từ người dùng, thêm các widget vào panel điều khiển bên trái.
    * **Đối với Phân tích Đa Cảm biến (`MultiSensorAnalysisScreenWidget`):**
        * Thêm một lựa chọn mới vào `self.analysis_type_combo`.
        * Thêm một tab mới vào `self.analysis_results_tabs` để hiển thị kết quả.
        * Trong `run_analysis()`, thêm logic để gọi `AnalysisWorker` (hoặc xử lý trực tiếp) cho loại phân tích mới và hiển thị kết quả lên tab tương ứng.
        * Nếu cần, thêm các widget cấu hình vào `self.analysis_options_widget` khi loại phân tích mới được chọn.

**5. Cấu trúc các lớp dữ liệu chính**

* **Dữ liệu thô từ cảm biến (output của `DeviceProcessor`):**
    * Một dictionary Python, ví dụ: `{'AccX': 0.1, 'AccY': 0.05, 'AccZ': 9.8, ...}`. Các key nên nhất quán.
* **Dữ liệu trong `DataProcessor._sensor_data_store[sensor_id]`:**
    * `'time_data'`: `np.array`
    * `'raw_acc'`: `{'x': np.array, 'y': np.array, 'z': np.array}` (sau khi chuyển đơn vị và tiền xử lý cơ bản)
    * `'processed_acc'`, `'processed_vel'`, `'processed_disp'`: Tương tự, chứa kết quả từ `KinematicProcessor`.
    * `'fft_plot_data'`: `{'x': {'freq': np.array, 'amp': np.array}, ...}`
* **Dữ liệu cho PlotManager (`DataProcessor.get_plot_data_for_sensor()`):**
    * Một dictionary chứa các `np.array` hoặc dictionary con tương tự như trên, sẵn sàng cho việc vẽ đồ thị.

**6. Các thành phần quan trọng và tương tác**

* **Signal/Slot trong PyQt6:** Hệ thống sử dụng nhiều cơ chế signal/slot để giao tiếp giữa các thành phần (ví dụ: `SensorManager` emit `sensorDataReceived`, `MainWindow` bắt và chuyển cho `DataProcessor`).
* **Threading (`QThread`):** `GenericSensorWorker` chạy trong `QThread` riêng để không làm đóng băng UI. `AnalysisWorker` cũng dùng `QThread`.
* **`pyqtgraph`:** Được sử dụng cho tất cả các đồ thị.
* **`numpy` và `scipy`:** Nền tảng cho hầu hết các phép toán số và xử lý tín hiệu.

**7. Coding Conventions và Best Practices**

* **PEP 8:** Tuân thủ hướng dẫn về style code của Python.
* **Đặt tên:** Sử dụng tên biến, hàm, class rõ ràng và mang tính mô tả (tiếng Anh).
* **Comments & Docstrings:**
    * Viết docstring cho các module, class, và hàm public để giải thích mục đích, tham số, và giá trị trả về.
    * Sử dụng comment trong code để giải thích các đoạn logic phức tạp.
* **Quản lý ngoại lệ (Exception Handling):** Sử dụng `try...except` để xử lý các lỗi tiềm ẩn một cách hợp lý, đặc biệt là khi giao tiếp với phần cứng hoặc thực hiện các phép toán phức tạp. Log lỗi chi tiết.
* **Tách biệt chức năng (Separation of Concerns):** Duy trì sự tách biệt rõ ràng giữa UI, logic nghiệp vụ (core processing), và thuật toán.
* **Tránh Hardcoding:** Sử dụng hằng số, biến cấu hình thay vì giá trị hardcode trực tiếp trong logic.
* **Tối ưu hóa (Khi cần thiết):** Đối với các phần xử lý thời gian thực, chú ý đến hiệu năng. Sử dụng `numpy` hiệu quả. Cân nhắc `numba` hoặc `cython` cho các vòng lặp tính toán cực kỳ nặng nếu `numpy` không đủ (hiện tại chưa cần).
