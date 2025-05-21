# ui/sensor_management_screen.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QTableWidget, QTableWidgetItem,
                           QComboBox, QLineEdit, QFormLayout, QMessageBox,
                           QGroupBox, QDialog, QDialogButtonBox, QHeaderView,
                           QSpacerItem, QSizePolicy, QGridLayout, QTextEdit,
                           QMenu, QSplitter)
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QSize, QModelIndex
from PyQt6.QtGui import QIcon, QAction

import logging
import psutil
import json
import uuid
import pyqtgraph as pg
import serial.tools.list_ports

logger = logging.getLogger(__name__)

# --- Dialog Chi tiết Cảm biến (SensorDetailDialog) ---
class SensorDetailDialog(QDialog):
    def __init__(self, sensor_info, sensor_data_raw, parent=None):
        super().__init__(parent)
        sensor_name = sensor_info.get('config', {}).get('name', sensor_info.get('id', 'N/A'))
        self.setWindowTitle(f"Chi tiết Cảm biến: {sensor_name}")
        self.setMinimumSize(550, 450)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.addRow("ID Cảm biến:", QLabel(str(sensor_info.get('id', 'N/A'))))
        form_layout.addRow("Tên Cảm biến:", QLabel(str(sensor_name)))
        form_layout.addRow("Loại Cảm biến:", QLabel(str(sensor_info.get('type', 'N/A'))))
        form_layout.addRow("Trạng thái:", QLabel("Đã kết nối" if sensor_info.get('connected') else "Chưa kết nối"))
        
        config = sensor_info.get('config', {})
        form_layout.addRow("Giao thức:", QLabel(str(config.get('protocol', 'N/A'))))
        
        # Display primary connection resource
        resource_label = "N/A"
        protocol = config.get('protocol')
        if protocol == "UART":
            resource_label = f"{config.get('port', 'N/A')} @ {config.get('baudrate', 'N/A')} baud"
        elif protocol in ["TCP/IP", "UDP"]:
            address = config.get('address')
            if address and isinstance(address, (list, tuple)) and len(address) == 2:
                resource_label = f"{address[0]}:{address[1]}"
            else:
                resource_label = str(address) if address else "N/A"
        elif protocol == "Bluetooth":
            resource_label = f"MAC: {config.get('mac_address', 'N/A')}"
        elif protocol == "Mock":
            resource_label = "Dữ liệu giả lập"
            
        form_layout.addRow("Cổng/Địa chỉ Tài nguyên:", QLabel(resource_label))
        
        for key, value in config.items():
            if key not in ['protocol', 'port', 'baudrate', 'address', 'mac_address', 'name']: # Avoid re-listing primary details
                 form_layout.addRow(f"Cấu hình ({key}):", QLabel(str(value)))
        layout.addLayout(form_layout)

        data_group = QGroupBox("Dữ liệu Raw Gần nhất")
        data_layout = QVBoxLayout(data_group)
        self.raw_data_display = QTextEdit()
        self.raw_data_display.setReadOnly(True)
        self.raw_data_display.setFontFamily("Courier New")
        
        if sensor_data_raw:
            try:
                pretty_json = json.dumps(sensor_data_raw, indent=4, ensure_ascii=False)
                self.raw_data_display.setText(pretty_json)
            except TypeError:
                self.raw_data_display.setText(str(sensor_data_raw))
        else:
            self.raw_data_display.setText("Không có dữ liệu gần nhất hoặc cảm biến chưa kết nối.")
            
        data_layout.addWidget(self.raw_data_display)
        layout.addWidget(data_group)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

# --- Dialog Thêm Cảm biến (AddSensorDialog) ---
class AddSensorDialog(QDialog):
    def __init__(self, sensor_manager, parent=None): # sensor_manager is passed
        super().__init__(parent)
        self.sensor_manager = sensor_manager
        self.setWindowTitle("Thêm Cảm biến Mới")
        self.setMinimumWidth(450)

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.sensor_name_input = QLineEdit()
        self.sensor_name_input.setPlaceholderText("Ví dụ: Cảm biến nhiệt phòng lab")
        self.form_layout.addRow("Tên Cảm biến (*):", self.sensor_name_input)

        self.sensor_id_input = QLineEdit()
        self.sensor_id_input.setPlaceholderText("Để trống để tự tạo ID duy nhất")
        self.form_layout.addRow("ID Cảm biến:", self.sensor_id_input)

        self.sensor_type_combo = QComboBox()
        if self.sensor_manager:
            self.sensor_type_combo.addItems(self.sensor_manager.get_available_sensor_types())
        else:
            # Fallback if sensor_manager is not available for some reason during init
            self.sensor_type_combo.addItems(["wit_motion_imu", "mock_sensor", "accelerometer", "temperature"])
        self.sensor_type_combo.currentTextChanged.connect(self._update_specific_config_fields)
        self.form_layout.addRow("Loại Cảm biến (*):", self.sensor_type_combo)

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["UART", "TCP/IP", "UDP", "Bluetooth", "Mock"])
        self.protocol_combo.currentTextChanged.connect(self._update_connection_fields)
        self.form_layout.addRow("Giao thức Kết nối (*):", self.protocol_combo)
        
        self.connection_details_group = QGroupBox("Chi tiết Kết nối Giao thức")
        self.connection_details_layout = QFormLayout()
        self.connection_details_group.setLayout(self.connection_details_layout)
        self.form_layout.addRow(self.connection_details_group)

        self.specific_config_group = QGroupBox("Cấu hình Đặc thù Loại Cảm biến")
        self.specific_config_layout = QFormLayout()
        self.specific_config_group.setLayout(self.specific_config_layout)
        self.form_layout.addRow(self.specific_config_group)
        
        self.sampling_rate_input = QLineEdit()
        self.sampling_rate_input.setPlaceholderText("Ví dụ: 100 (Hz), nếu cảm biến hỗ trợ")
        self.form_layout.addRow("Tốc độ lấy mẫu (Hz):", self.sampling_rate_input)

        self.layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept_and_validate) # Connect to custom validation
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.current_connection_widgets = {}
        self.current_specific_config_widgets = {}

        self._update_connection_fields() # Initial call
        self._update_specific_config_fields() # Initial call

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            sub_layout = item.layout()
            if sub_layout: # If item is a layout, recursively clear it
                self._clear_layout(sub_layout)


    def _update_connection_fields(self):
        self._clear_layout(self.connection_details_layout)
        self.current_connection_widgets.clear()
        protocol = self.protocol_combo.currentText()

        if protocol == "UART":
            port_entry_layout = QHBoxLayout()
            self.port_combo = QComboBox()
            self.port_combo.setMinimumWidth(200)
            self.refresh_ports_button = QPushButton("Làm mới")
            self.refresh_ports_button.clicked.connect(self.refresh_com_ports)
            port_entry_layout.addWidget(self.port_combo)
            port_entry_layout.addWidget(self.refresh_ports_button)
            port_entry_layout.addStretch(1)
            self.connection_details_layout.addRow("Cổng COM (*):", port_entry_layout)
            self.current_connection_widgets['port_address'] = self.port_combo # port_address is the combo itself
            self.refresh_com_ports() # Populate initially
            
            self.baudrate_input = QComboBox() # Changed to QComboBox for standard rates
            self.baudrate_input.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
            self.baudrate_input.setCurrentText("115200")
            self.connection_details_layout.addRow("Tốc độ Baud (*):", self.baudrate_input)
            self.current_connection_widgets['baudrate'] = self.baudrate_input

        elif protocol in ["TCP/IP", "UDP"]:
            self.ip_address_input = QLineEdit()
            self.ip_address_input.setPlaceholderText("Ví dụ: 192.168.1.100")
            self.connection_details_layout.addRow("Địa chỉ IP (*):", self.ip_address_input)
            self.current_connection_widgets['ip_address'] = self.ip_address_input
            
            self.port_number_input = QLineEdit() # Should be QLineEdit, not QSpinBox for port numbers
            self.port_number_input.setPlaceholderText("Ví dụ: 8080")
            self.connection_details_layout.addRow("Cổng (*):", self.port_number_input)
            self.current_connection_widgets['port_number'] = self.port_number_input
        elif protocol == "Bluetooth":
            self.mac_address_input = QLineEdit()
            self.mac_address_input.setPlaceholderText("Ví dụ: 00:1A:2B:3C:4D:5E")
            self.connection_details_layout.addRow("Địa chỉ MAC (*):", self.mac_address_input)
            self.current_connection_widgets['mac_address'] = self.mac_address_input
        elif protocol == "Mock":
             self.connection_details_layout.addRow(QLabel("Cảm biến Mock không yêu cầu chi tiết kết nối."))
        
        self.connection_details_group.setVisible(self.connection_details_layout.rowCount() > 0)


    def refresh_com_ports(self):
        if 'port_address' not in self.current_connection_widgets or not isinstance(self.current_connection_widgets['port_address'], QComboBox):
            return
        
        com_port_combo = self.current_connection_widgets['port_address']
        current_com_port = com_port_combo.currentData() # Save current selection
        com_port_combo.clear()
        ports = serial.tools.list_ports.comports()
        found_ports = False
        for port in ports:
            # Filter out ports with 'n/a' in description, often virtual or problematic
            if port.device and ('n/a' not in port.description.lower()):
                com_port_combo.addItem(f"{port.device} - {port.description}", userData=port.device)
                found_ports = True
        
        if not found_ports:
            com_port_combo.addItem("Không tìm thấy cổng COM", userData=None)
        
        # Try to restore previous selection
        idx = com_port_combo.findData(current_com_port)
        if idx != -1:
            com_port_combo.setCurrentIndex(idx)
        elif com_port_combo.count() > 0:
            com_port_combo.setCurrentIndex(0)


    def _update_specific_config_fields(self):
        self._clear_layout(self.specific_config_layout)
        self.current_specific_config_widgets.clear()
        sensor_type = self.sensor_type_combo.currentText()

        if sensor_type == "accelerometer" or sensor_type == "wit_motion_imu":
            self.accel_range_input = QComboBox()
            self.accel_range_input.addItems(["±2g", "±4g", "±8g", "±16g"])
            self.specific_config_layout.addRow("Dải đo Gia tốc:", self.accel_range_input)
            self.current_specific_config_widgets['accel_range'] = self.accel_range_input
            
            if sensor_type == "wit_motion_imu": # Specific to WIT
                self.wit_data_rate_combo = QComboBox()
                # Store actual hex byte string as userData
                self.wit_data_rate_combo.addItem("0.1 Hz (Rất chậm)", "00")
                self.wit_data_rate_combo.addItem("0.5 Hz", "0F") # Example, check WIT manual for actual value
                self.wit_data_rate_combo.addItem("1 Hz", "01")
                self.wit_data_rate_combo.addItem("10 Hz", "05") # Corresponds to old '0x05'
                self.wit_data_rate_combo.addItem("20 Hz", "0A") # Corresponds to old '0x0A'
                self.wit_data_rate_combo.addItem("50 Hz", "14") # Corresponds to old '0x14'
                self.wit_data_rate_combo.addItem("100 Hz", "19") # Corresponds to old '0x19'
                self.wit_data_rate_combo.addItem("200 Hz (Mặc định/Nhanh)", "0B") # Corresponds to old '0x0B'

                # Find index for "200 Hz" to set as default
                default_rate_idx = self.wit_data_rate_combo.findData("0B")
                self.wit_data_rate_combo.setCurrentIndex(default_rate_idx if default_rate_idx != -1 else 0)

                self.specific_config_layout.addRow("WIT Data Rate:", self.wit_data_rate_combo)
                self.current_specific_config_widgets['wit_data_rate_hex'] = self.wit_data_rate_combo
        
        elif sensor_type == "temperature":
            self.temp_unit_input = QComboBox()
            self.temp_unit_input.addItems(["Celsius", "Fahrenheit", "Kelvin"])
            self.specific_config_layout.addRow("Đơn vị (Unit):", self.temp_unit_input)
            self.current_specific_config_widgets['unit'] = self.temp_unit_input
        
        self.specific_config_group.setVisible(self.specific_config_layout.rowCount() > 0)

    def accept_and_validate(self):
        # Basic validation
        if not self.sensor_name_input.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Tên Cảm biến.")
            return

        protocol = self.protocol_combo.currentText()
        selected_port_device = None # For UART

        if protocol == "UART":
            if not self.current_connection_widgets['port_address'].currentData(): # Check if userData (device path) is set
                QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn Cổng COM hợp lệ cho UART.")
                return
            selected_port_device = self.current_connection_widgets['port_address'].currentData()
        elif protocol in ["TCP/IP", "UDP"]:
            if not self.current_connection_widgets['ip_address'].text().strip() or \
               not self.current_connection_widgets['port_number'].text().strip():
                QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập đầy đủ IP và Cổng.")
                return
            try:
                port_num = int(self.current_connection_widgets['port_number'].text().strip())
                if not (0 < port_num < 65536):
                    QMessageBox.warning(self, "Giá trị không hợp lệ", "Số cổng mạng phải từ 1 đến 65535.")
                    return
            except ValueError:
                QMessageBox.warning(self, "Giá trị không hợp lệ", "Số cổng mạng không hợp lệ.")
                return
        elif protocol == "Bluetooth":
            if not self.current_connection_widgets['mac_address'].text().strip(): # Basic check
                 QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập địa chỉ MAC cho Bluetooth.")
                 return

        # Proactive Resource Conflict Check (for UART COM ports)
        if protocol == "UART" and selected_port_device and self.sensor_manager:
            all_sensor_ids = self.sensor_manager.get_all_sensor_ids()
            for sid in all_sensor_ids:
                s_info = self.sensor_manager.get_sensor_info(sid)
                if s_info:
                    s_config = s_info.get('config', {})
                    if s_config.get('protocol') == "UART" and s_config.get('port') == selected_port_device:
                        # Allowing config if sensor is not connected, but warn if it's connected.
                        # For simplicity, let's check if it's *configured* for another sensor.
                        # A more advanced check would be if it's *actively connected*.
                        # For now, we prevent configuring the same port for two sensors regardless of connection state.
                        QMessageBox.warning(self, "Xung đột Tài nguyên",
                                            f"Cổng COM '{selected_port_device}' đã được cấu hình cho cảm biến: "
                                            f"'{s_config.get('name', sid)}' (ID: {sid}).\n"
                                            "Vui lòng chọn cổng khác hoặc xóa cảm biến kia trước.")
                        return
        
        # If all checks pass
        self.accept()


    def get_sensor_config(self):
        sensor_name = self.sensor_name_input.text().strip()
        sensor_id_text = self.sensor_id_input.text().strip()
        sensor_type = self.sensor_type_combo.currentText()

        if not sensor_id_text:
            # Generate a more descriptive unique ID
            type_prefix = sensor_type.replace('_', '-').split('-')[0].lower() # e.g. "wit" from "wit_motion_imu"
            sensor_id = f"{type_prefix}_{sensor_name.replace(' ', '_').lower()}_{uuid.uuid4().hex[:4]}"
            sensor_id = sensor_id[:32] # Keep it reasonably short
        else:
            sensor_id = sensor_id_text

        config = {
            "id": sensor_id,
            "name": sensor_name,
            "type": sensor_type,
            "protocol": self.protocol_combo.currentText()
        }

        protocol = config["protocol"]
        if protocol == "UART":
            config['port'] = self.current_connection_widgets['port_address'].currentData() # This is the device path
            config['baudrate'] = int(self.current_connection_widgets['baudrate'].currentText())
        elif protocol in ["TCP/IP", "UDP"]:
            ip = self.current_connection_widgets['ip_address'].text().strip()
            port_num_str = self.current_connection_widgets['port_number'].text().strip()
            try:
                port_num = int(port_num_str)
                config['address'] = (ip, port_num) # Store as tuple
            except ValueError: # Should be caught by validation, but defensive
                logger.error(f"Số cổng không hợp lệ khi lấy config: {port_num_str} cho {sensor_name}")
                # Potentially return None or raise error to signal MainWindow
                return None # Indicates an error in config gathering
        elif protocol == "Bluetooth":
            config['mac_address'] = self.current_connection_widgets['mac_address'].text().strip()
        
        # Specific sensor type configurations
        if sensor_type == "accelerometer" or sensor_type == "wit_motion_imu":
            if 'accel_range' in self.current_specific_config_widgets:
                config["accel_range"] = self.current_specific_config_widgets['accel_range'].currentText()
            if sensor_type == "wit_motion_imu" and 'wit_data_rate_hex' in self.current_specific_config_widgets:
                # Get the hex byte string from userData
                config["wit_data_rate_byte_hex"] = self.current_specific_config_widgets['wit_data_rate_hex'].currentData()
        elif sensor_type == "temperature":
            if 'unit' in self.current_specific_config_widgets:
                config["unit"] = self.current_specific_config_widgets['unit'].currentText()

        sr_text = self.sampling_rate_input.text().strip()
        if sr_text:
            try:
                config["sampling_rate_hz"] = float(sr_text)
            except ValueError:
                logger.warning(f"Giá trị tốc độ lấy mẫu không hợp lệ: {sr_text} cho {sensor_name}")
        
        # Return sensor_id, sensor_type, and config dictionary
        return sensor_id, sensor_type, config


# --- Màn hình Quản lý Cảm biến Chính (SensorManagementScreen) ---
class SensorManagementScreen(QWidget):
    sensor_selected = pyqtSignal(str) # Emitted when a sensor row is selected/double-clicked
    connect_sensor_requested = pyqtSignal(str)
    disconnect_sensor_requested = pyqtSignal(str)
    add_sensor_requested = pyqtSignal(str, str, dict) # sensor_id, sensor_type, config
    remove_sensor_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sensor_manager = None # Will be set by MainWindow via set_managers
        # self.sensor_processor is not directly used here, DataProcessor is handled by MainWindow
        
        self.cpu_data = []
        self.mem_data = []
        self.time_data = []
        self.max_data_points_resource_plot = 120 # 2 minutes of data at 1s interval

        self.setup_ui()

        self.resource_update_timer = QTimer(self)
        self.resource_update_timer.timeout.connect(self.update_resource_graphs_and_stats)
        self.resource_update_timer.start(1000) # Update every second

        self.table_update_timer = QTimer(self)
        self.table_update_timer.timeout.connect(self.update_sensors_table_if_needed) # More efficient update
        self.table_update_timer.start(1500) # Check for table updates periodically

    def set_managers(self, sensor_manager, data_processor_ref): # data_processor_ref is not directly used by this screen
        self.sensor_manager = sensor_manager
        # self.data_processor = data_processor_ref # If needed later
        self.update_sensors_table() # Initial population

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Top Bar for Actions ---
        top_bar_layout = QHBoxLayout()
        add_sensor_button = QPushButton(QIcon.fromTheme("list-add", QIcon("path/to/fallback/add_icon.png")), "Thêm Cảm biến Mới")
        add_sensor_button.setIconSize(QSize(16,16))
        add_sensor_button.setStyleSheet("padding: 8px 15px; font-size: 14px; background-color: #27ae60; color: white; border-radius: 3px;")
        add_sensor_button.clicked.connect(self.open_add_sensor_dialog)
        top_bar_layout.addWidget(add_sensor_button)
        
        # Add "Connect All" / "Disconnect All" buttons
        self.connect_all_button = QPushButton("Kết nối Tất cả")
        self.connect_all_button.clicked.connect(self.connect_all_inactive_sensors)
        top_bar_layout.addWidget(self.connect_all_button)

        self.disconnect_all_button = QPushButton("Ngắt Tất cả")
        self.disconnect_all_button.clicked.connect(self.disconnect_all_active_sensors)
        top_bar_layout.addWidget(self.disconnect_all_button)

        # Add "Remove All Inactive" button
        self.remove_inactive_button = QPushButton("Xóa Cảm biến Không Hoạt động")
        self.remove_inactive_button.setStyleSheet("padding: 8px 15px; font-size: 14px; background-color: #e74c3c; color: white; border-radius: 3px;")
        self.remove_inactive_button.clicked.connect(self.remove_all_inactive_sensors)
        top_bar_layout.addWidget(self.remove_inactive_button)

        top_bar_layout.addStretch()
        main_layout.addLayout(top_bar_layout)

        # --- Main Splitter ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Sensors List Group
        sensors_list_group = QGroupBox("Danh sách Cảm biến")
        sensors_list_layout = QVBoxLayout(sensors_list_group)
        self.sensors_table = QTableWidget()
        # Added "Tài nguyên" column
        self.sensors_table.setColumnCount(7) 
        self.sensors_table.setHorizontalHeaderLabels([
            "Tên Cảm biến", "ID", "Loại", "Giao thức", "Tài nguyên", "Trạng thái", "Hành động"
        ])
        self.sensors_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive) # Allow manual resize
        self.sensors_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sensors_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sensors_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sensors_table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.sensors_table.doubleClicked.connect(self.on_sensor_table_double_clicked) # For quick view details

        sensors_list_layout.addWidget(self.sensors_table)
        splitter.addWidget(sensors_list_group)

        # Resources and Stats Group
        resources_stats_group = QGroupBox("Tài nguyên Hệ thống và Thống kê")
        resources_stats_layout = QGridLayout(resources_stats_group)

        self.cpu_plot_widget = pg.PlotWidget(title="CPU Usage (%)")
        self.cpu_plot_widget.setLabel('left', '% CPU')
        self.cpu_plot_widget.setLabel('bottom', 'Thời gian (s)')
        self.cpu_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.cpu_curve = self.cpu_plot_widget.plot(pen='r')
        resources_stats_layout.addWidget(self.cpu_plot_widget, 0, 0)

        self.mem_plot_widget = pg.PlotWidget(title="Memory Usage (%)")
        self.mem_plot_widget.setLabel('left', '% RAM')
        self.mem_plot_widget.setLabel('bottom', 'Thời gian (s)')
        self.mem_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.mem_curve = self.mem_plot_widget.plot(pen='b')
        resources_stats_layout.addWidget(self.mem_plot_widget, 0, 1)

        stats_frame = QFrame()
        stats_layout = QFormLayout(stats_frame)
        self.total_sensors_label = QLabel("0") # Total configured
        self.connected_sensors_label = QLabel("0")
        # self.data_rate_label = QLabel("0 FPS") # This might be complex to aggregate meaningfully here
        stats_layout.addRow("Tổng số cảm biến cấu hình:", self.total_sensors_label)
        stats_layout.addRow("Số cảm biến đã kết nối:", self.connected_sensors_label)
        # stats_layout.addRow("Tốc độ dữ liệu tổng hợp:", self.data_rate_label)
        resources_stats_layout.addWidget(stats_frame, 1, 0, 1, 2) # Span across both plot columns

        splitter.addWidget(resources_stats_group)
        splitter.setStretchFactor(0, 2) # Give more space to sensor list
        splitter.setStretchFactor(1, 1) # Less space to resource graphs initially

        main_layout.addWidget(splitter)
        self.resize_table_columns_to_content()


    def resize_table_columns_to_content(self):
        self.sensors_table.resizeColumnsToContents()
        header = self.sensors_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # ID
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Protocol
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Resource
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Status
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Action


    def connect_all_inactive_sensors(self):
        if not self.sensor_manager: return
        all_ids = self.sensor_manager.get_all_sensor_ids()
        connected_any = False
        for sensor_id in all_ids:
            s_info = self.sensor_manager.get_sensor_info(sensor_id)
            if s_info and not s_info.get('connected'):
                self.connect_sensor_requested.emit(sensor_id)
                connected_any = True
        if not connected_any:
            QMessageBox.information(self, "Thông báo", "Không có cảm biến nào chưa kết nối để thực hiện.")


    def disconnect_all_active_sensors(self):
        if not self.sensor_manager: return
        all_ids = self.sensor_manager.get_all_sensor_ids()
        disconnected_any = False
        for sensor_id in all_ids:
            s_info = self.sensor_manager.get_sensor_info(sensor_id)
            if s_info and s_info.get('connected'):
                self.disconnect_sensor_requested.emit(sensor_id)
                disconnected_any = True
        if not disconnected_any:
            QMessageBox.information(self, "Thông báo", "Không có cảm biến nào đang kết nối để ngắt.")


    def open_add_sensor_dialog(self):
        # Pass sensor_manager to AddSensorDialog for conflict checking
        dialog = AddSensorDialog(self.sensor_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # get_sensor_config now returns a tuple: (sensor_id, sensor_type, config_dict)
            # or None if there was an issue like invalid port number.
            config_data = dialog.get_sensor_config() 
            if config_data is None: # Indicates an error during config gathering (e.g. invalid port)
                QMessageBox.critical(self, "Lỗi Cấu hình", 
                                     "Không thể lấy cấu hình cảm biến. Vui lòng kiểm tra lại các giá trị nhập.")
                return

            sensor_id, sensor_type, config_dict = config_data
            
            # Sensor ID existence check should be done by SensorManager.add_sensor
            # but a proactive check here is also fine.
            if self.sensor_manager and sensor_id in self.sensor_manager.get_all_sensor_ids():
                 QMessageBox.warning(self, "Lỗi", f"ID Cảm biến '{sensor_id}' đã tồn tại. Vui lòng chọn ID khác.")
                 return

            logger.debug(f"Dialog accepted. Requesting to add sensor ID: {sensor_id}, Type: {sensor_type}, Config: {config_dict}")
            self.add_sensor_requested.emit(sensor_id, sensor_type, config_dict)
        else:
            logger.debug("AddSensorDialog cancelled by user.")

    def show_table_context_menu(self, position: QPoint):
        selected_items = self.sensors_table.selectedItems()
        if not selected_items: return # No item selected

        row = self.sensors_table.rowAt(position.y()) # Get row from position
        if row < 0: return # Clicked outside rows

        sensor_id_item = self.sensors_table.item(row, 1) # ID is in column 1
        if not sensor_id_item: return
        
        sensor_id = sensor_id_item.text()
        sensor_info = self.sensor_manager.get_sensor_info(sensor_id) if self.sensor_manager else None

        menu = QMenu(self)
        
        detail_action = QAction("Xem Chi tiết", self)
        detail_action.triggered.connect(lambda: self.show_sensor_detail_for_id(sensor_id))
        menu.addAction(detail_action)
        
        if sensor_info:
            is_connected = sensor_info.get('connected', False)
            if is_connected:
                disconnect_action = QAction("Ngắt Kết nối", self)
                disconnect_action.triggered.connect(lambda: self.disconnect_sensor_requested.emit(sensor_id))
                menu.addAction(disconnect_action)
            else:
                connect_action = QAction("Kết nối", self)
                connect_action.triggered.connect(lambda: self.connect_sensor_requested.emit(sensor_id))
                menu.addAction(connect_action)
        
        menu.addSeparator()
        delete_action = QAction(QIcon.fromTheme("edit-delete"), "Xóa Cảm biến", self)
        delete_action.triggered.connect(lambda: self.request_remove_sensor(sensor_id))
        menu.addAction(delete_action)

        menu.exec(self.sensors_table.viewport().mapToGlobal(position))
        
    def on_sensor_table_double_clicked(self, model_index: QModelIndex):
        if not model_index.isValid(): return
        row = model_index.row()
        sensor_id_item = self.sensors_table.item(row, 1) # ID is in column 1
        if sensor_id_item:
            self.show_sensor_detail_for_id(sensor_id_item.text())


    def show_sensor_detail_for_id(self, sensor_id: str):
        if self.sensor_manager:
            sensor_info = self.sensor_manager.get_sensor_info(sensor_id)
            if sensor_info:
                sensor_instance = self.sensor_manager.get_sensor_instance(sensor_id)
                # Assuming SensorInstance has a `last_data` attribute like the old worker
                sensor_data_raw = sensor_instance.last_data if sensor_instance else None
                                        
                dialog = SensorDetailDialog(sensor_info, sensor_data_raw, self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Lỗi", f"Không tìm thấy thông tin cho cảm biến ID: {sensor_id}")
        else:
            QMessageBox.critical(self, "Lỗi nghiêm trọng", "SensorManager chưa được khởi tạo.")

    def request_remove_sensor(self, sensor_id: str):
        if not self.sensor_manager:
            QMessageBox.critical(self, "Lỗi nghiêm trọng", "SensorManager chưa được khởi tạo.")
            return

        sensor_info = self.sensor_manager.get_sensor_info(sensor_id)
        sensor_name = sensor_info.get('config', {}).get('name', sensor_id) if sensor_info else sensor_id
        
        if sensor_info and sensor_info.get('connected'):
            reply = QMessageBox.warning(self, 'Xác nhận Xóa', 
                                     f"Cảm biến '{sensor_name}' (ID: {sensor_id}) đang kết nối.\n"
                                     "Bạn có chắc chắn muốn ngắt kết nối và xóa cảm biến này không?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        else:
            reply = QMessageBox.question(self, 'Xác nhận Xóa', 
                                     f"Bạn có chắc chắn muốn xóa cảm biến '{sensor_name}' (ID: {sensor_id}) không?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        self.remove_sensor_requested.emit(sensor_id)

    def update_sensors_table_if_needed(self):
        if not self.sensor_manager or not self.isVisible(): return # Only update if visible
        
        current_row_count = self.sensors_table.rowCount()
        manager_sensor_count = len(self.sensor_manager.get_all_sensor_ids())

        # Force full update if count changes significantly
        if abs(current_row_count - manager_sensor_count) > 2 : # Threshold for full rebuild
            self.update_sensors_table()
            return

        needs_full_update = False
        if current_row_count != manager_sensor_count:
            needs_full_update = True
        else: # Check for status changes in existing rows
            for row in range(current_row_count):
                try:
                    sensor_id = self.sensors_table.item(row, 1).text() # ID column
                    sensor_info = self.sensor_manager.get_sensor_info(sensor_id)
                    if sensor_info:
                        current_status_in_table = self.sensors_table.item(row, 5).text() # Status column
                        actual_status = "Đã kết nối" if sensor_info.get('connected') else "Chưa kết nối"
                        if current_status_in_table != actual_status:
                            needs_full_update = True
                            break
                        # Check resource column as well
                        current_resource_in_table = self.sensors_table.item(row, 4).text()
                        actual_resource = self.get_resource_display_string(sensor_info.get('config', {}))
                        if current_resource_in_table != actual_resource:
                            needs_full_update = True
                            break
                    else: # Sensor in table no longer in manager - should not happen if remove is handled
                        needs_full_update = True
                        break
                except AttributeError: # Item might not exist yet if table is being built
                    needs_full_update = True
                    break
        
        if needs_full_update:
            self.update_sensors_table()


    def get_resource_display_string(self, config_dict):
        protocol = config_dict.get('protocol')
        if protocol == "UART":
            return f"{config_dict.get('port', 'N/A')} @ {config_dict.get('baudrate', 'N/A')}"
        elif protocol in ["TCP/IP", "UDP"]:
            addr = config_dict.get('address')
            return f"{addr[0]}:{addr[1]}" if isinstance(addr, (list, tuple)) and len(addr)==2 else str(addr or 'N/A')
        elif protocol == "Bluetooth":
            return f"MAC: {config_dict.get('mac_address', 'N/A')}"
        elif protocol == "Mock":
            return "Giả lập"
        return "Không rõ"

    def update_sensors_table(self):
        if not self.sensor_manager:
            self.sensors_table.setRowCount(0)
            return
            
        self.sensors_table.setSortingEnabled(False) # Disable sorting during update
        self.sensors_table.setRowCount(0) 
        all_sensor_ids = self.sensor_manager.get_all_sensor_ids()
        
        for sensor_id in all_sensor_ids:
            sensor_info = self.sensor_manager.get_sensor_info(sensor_id)
            if not sensor_info: continue

            config = sensor_info.get('config', {})
            row = self.sensors_table.rowCount()
            self.sensors_table.insertRow(row)
            
            # Col 0: Name
            self.sensors_table.setItem(row, 0, QTableWidgetItem(str(config.get('name', sensor_id))))
            # Col 1: ID
            id_item = QTableWidgetItem(str(sensor_id))
            self.sensors_table.setItem(row, 1, id_item)
            # Col 2: Type
            self.sensors_table.setItem(row, 2, QTableWidgetItem(str(sensor_info.get('type', 'N/A'))))
            # Col 3: Protocol
            self.sensors_table.setItem(row, 3, QTableWidgetItem(str(config.get('protocol', 'N/A'))))
            # Col 4: Resource (New)
            resource_str = self.get_resource_display_string(config)
            self.sensors_table.setItem(row, 4, QTableWidgetItem(resource_str))

            # Col 5: Status
            is_connected = sensor_info.get('connected', False)
            connection_error_msg = sensor_info.get('connection_error', '') # Get from SensorInstance
            status_text = "Đã kết nối" if is_connected else "Chưa kết nối"
            if not is_connected and connection_error_msg and "removed" not in connection_error_msg.lower() : # Show error if not simple disconnect
                status_text = f"Lỗi: {connection_error_msg[:30]}..." if len(connection_error_msg) > 30 else f"Lỗi: {connection_error_msg}"
            
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(Qt.GlobalColor.darkGreen if is_connected else Qt.GlobalColor.red)
            self.sensors_table.setItem(row, 5, status_item)
            
            # Col 6: Action Button
            action_button = QPushButton()
            action_button.setIconSize(QSize(16,16))
            if is_connected:
                action_button.setText("Ngắt")
                action_button.setIcon(QIcon.fromTheme("network-offline", QIcon("path/to/disconnect_icon.png")))
                action_button.clicked.connect(lambda checked=False, sid=sensor_id: self.disconnect_sensor_requested.emit(sid))
            else:
                action_button.setText("Nối")
                action_button.setIcon(QIcon.fromTheme("network-transmit-receive", QIcon("path/to/connect_icon.png")))
                action_button.clicked.connect(lambda checked=False, sid=sensor_id: self.connect_sensor_requested.emit(sid))
            self.sensors_table.setCellWidget(row, 6, action_button)

        self.sensors_table.setSortingEnabled(True)
        self.resize_table_columns_to_content()

    # on_sensor_selection_changed is not strictly needed if double-click handles selection for plotting
    # def on_sensor_selection_changed(self):
    #     selected_items = self.sensors_table.selectedItems()
    #     if selected_items:
    #         row = selected_items[0].row()
    #         sensor_id_item = self.sensors_table.item(row, 1) # ID Column
    #         if sensor_id_item:
    #             sensor_id = sensor_id_item.text()
    #             self.sensor_selected.emit(sensor_id) # MainWindow can use this

    def update_resource_graphs_and_stats(self):
        current_time_idx = len(self.time_data) # Use index as x-axis for simplicity
        
        try:
            cpu_val = psutil.cpu_percent(interval=None)
            mem_val = psutil.virtual_memory().percent
        except Exception as e: # psutil might fail in some environments
            logger.warning(f"Could not read system resources: {e}")
            cpu_val = 0
            mem_val = 0

        self.cpu_data.append(cpu_val)
        self.mem_data.append(mem_val)
        self.time_data.append(current_time_idx)

        if len(self.time_data) > self.max_data_points_resource_plot:
            self.time_data.pop(0)
            self.cpu_data.pop(0)
            self.mem_data.pop(0)
        
        # Adjust x-range for plots
        min_x_range = max(0, current_time_idx - self.max_data_points_resource_plot)
        max_x_range = current_time_idx if current_time_idx > 0 else 1 # Avoid empty range

        self.cpu_plot_widget.setXRange(min_x_range, max_x_range, padding=0)
        self.mem_plot_widget.setXRange(min_x_range, max_x_range, padding=0)

        self.cpu_curve.setData(self.time_data, self.cpu_data)
        self.mem_curve.setData(self.time_data, self.mem_data)

        if self.sensor_manager:
            self.total_sensors_label.setText(str(len(self.sensor_manager.get_all_sensor_ids())))
            connected_count = self.sensor_manager.get_connected_sensors_count()
            self.connected_sensors_label.setText(str(connected_count))
        
        # Data rate label removed as it's hard to aggregate meaningfully here

    def closeEvent(self, event):
        self.resource_update_timer.stop()
        self.table_update_timer.stop()
        # Any other cleanup specific to this screen
        super().closeEvent(event)

    def remove_all_inactive_sensors(self):
        """Remove all sensors that are not currently connected."""
        if not self.sensor_manager:
            return

        inactive_sensors = self.sensor_manager.get_inactive_sensors()
        if not inactive_sensors:
            QMessageBox.information(self, "Thông báo", "Không có cảm biến nào không hoạt động để xóa.")
            return

        # Get sensor names for confirmation message
        sensor_names = []
        for sensor_id in inactive_sensors:
            sensor_info = self.sensor_manager.get_sensor_info(sensor_id)
            if sensor_info:
                name = sensor_info.get('config', {}).get('name', sensor_id)
                sensor_names.append(f"'{name}' (ID: {sensor_id})")

        # Show confirmation dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Xác nhận Xóa")
        msg.setText(f"Bạn có chắc chắn muốn xóa {len(sensor_names)} cảm biến không hoạt động?")
        msg.setInformativeText("Danh sách cảm biến sẽ bị xóa:\n" + "\n".join(sensor_names))
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            removed_count = self.sensor_manager.remove_all_inactive_sensors()
            if removed_count > 0:
                QMessageBox.information(self, "Thành công", f"Đã xóa {removed_count} cảm biến không hoạt động.")
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể xóa bất kỳ cảm biến nào.")