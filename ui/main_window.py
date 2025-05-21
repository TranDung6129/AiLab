import logging
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal

from core.data_processor import DataProcessor
from core.plot_manager import PlotManager
from ui.display_screen import DisplayScreenWidget
from ui.sensor_management_screen import SensorManagementScreen
from ui.settings_screen import SettingsScreenWidget
from ui.advanced_analysis_screen import AdvancedAnalysisScreenWidget
from ui.data_hub_screen import DataHubScreenWidget
from core.sensor_core import SensorManager
from ui.multi_sensor_analysis_screen import MultiSensorAnalysisScreenWidget

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AiLab - Real-time Displacement Monitoring")
        self.setGeometry(100, 100, 1800, 1000)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.sensor_manager = SensorManager(self)
        self.data_processor = DataProcessor(self)

        self.tabs = QTabWidget()
        self.display_screen = DisplayScreenWidget()
        self.sensor_screen_new = SensorManagementScreen(self)
        self.sensor_screen_new.set_managers(self.sensor_manager, self.data_processor)
        self.settings_screen = SettingsScreenWidget()
        self.advanced_analysis_screen = AdvancedAnalysisScreenWidget(self.data_processor, self)
        
        # Initialize the new multi-sensor analysis screen
        self.multi_sensor_analysis_screen = MultiSensorAnalysisScreenWidget(self.data_processor, self.sensor_manager, self)
        
        self.data_hub_screen = DataHubScreenWidget(self)
        self.data_hub_screen.set_managers(self.sensor_manager, self.data_processor)
        
        self.plot_manager = PlotManager(self.display_screen, self.data_processor)
        
        self.tabs.addTab(self.display_screen, "Hiển thị đồ thị")
        self.tabs.addTab(self.sensor_screen_new, "Quản lý cảm biến")
        self.tabs.addTab(self.advanced_analysis_screen, "Phân tích chuyên sâu")
        self.tabs.addTab(self.multi_sensor_analysis_screen, "Phân tích đa cảm biến")
        self.tabs.addTab(self.data_hub_screen, "Truyền/Nhận dữ liệu")
        self.tabs.addTab(self.settings_screen, "Thiết lập")

        self.layout.addWidget(self.tabs)
        self.current_plotting_sensor_id = None
        self._connect_signals()
        self.update_display_sensor_selector()

    def _connect_signals(self):
        # SensorManager -> DataProcessor, UI
        self.sensor_manager.sensorDataReceived.connect(self.handle_sensor_data_from_manager)
        self.sensor_manager.sensorConnectionStatusChanged.connect(self.handle_sensor_connection_status_from_manager)
        self.sensor_manager.sensorListChanged.connect(self.sensor_screen_new.update_sensors_table)
        self.sensor_manager.sensorListChanged.connect(self.update_display_sensor_selector) # Update combo on display screen
        self.sensor_manager.sensorListChanged.connect(self.data_hub_screen.update_sensor_selection_combo)

        # SensorManagementScreen (UI) -> SensorManager, MainWindow
        self.sensor_screen_new.add_sensor_requested.connect(self.handle_add_sensor_request)
        self.sensor_screen_new.remove_sensor_requested.connect(self.handle_remove_sensor_request)
        self.sensor_screen_new.connect_sensor_requested.connect(self.sensor_manager.connect_sensor_by_id)
        self.sensor_screen_new.disconnect_sensor_requested.connect(self.sensor_manager.disconnect_sensor_by_id)
        self.sensor_screen_new.sensor_selected.connect(self.handle_sensor_selected_for_plotting_from_table)

        # SettingsScreen -> MainWindow, PlotManager
        self.settings_screen.display_rate_changed.connect(self.handle_display_rate_change)
        self.settings_screen.kinematic_settings_applied.connect(self.handle_kinematic_settings_applied)
        self.settings_screen.advanced_processing_settings_applied.connect(self.handle_advanced_processing_settings_applied)

        # DisplayScreen -> MainWindow
        self.display_screen.sensor_selection_changed.connect(self.handle_display_sensor_changed_from_combo)
        # self.display_screen.plot_styles_updated.connect(self.handle_plot_styles_updated) # If we need to save them

        # For MultiSensorAnalysisScreenWidget
        self.sensor_manager.sensorListChanged.connect(self.multi_sensor_analysis_screen.handle_sensor_list_or_status_changed)
        self.sensor_manager.sensorConnectionStatusChanged.connect(
            lambda sid, conn, msg: self.multi_sensor_analysis_screen.handle_sensor_list_or_status_changed()
        ) # Rebuild list on connection change too

    def update_display_sensor_selector(self):
        """Updates the sensor selector combo box on the DisplayScreenWidget."""
        self.display_screen.update_sensor_selector(self.sensor_manager)
        if not self.current_plotting_sensor_id and self.display_screen.sensor_selector_combo.count() > 0:
             new_sensor_id_to_plot = self.display_screen.sensor_selector_combo.currentData()
             if new_sensor_id_to_plot: # if an actual sensor ID, not None
                 self.switch_plotting_sensor(new_sensor_id_to_plot) # This will also set current_plotting_sensor_id
             elif self.display_screen.sensor_selector_combo.itemData(0) is None: # "No sensor" selected
                  self.handle_display_sensor_changed_from_combo("") # Explicitly handle no sensor selection

    def handle_add_sensor_request(self, sensor_id, sensor_type, config):
        logger.info(f"MainWindow: Received request to add sensor: {sensor_id}, type: {sensor_type}")
        
        if config is None: # Check if config dict itself is None (error from AddSensorDialog)
            # QMessageBox is already shown by AddSensorDialog if config is None from its get_sensor_config
            logger.error(f"MainWindow: Received None config for sensor {sensor_id}. Aborting add.")
            return

        # Prepare initial kinematic parameters (defaults or from a global setting if available)
        initial_kin_params = self.data_processor.default_kinematic_params.copy()
        dt_for_dp = 0.005 # Default dt
        
        if sensor_type == "wit_motion_imu":
            hex_val = config.get('wit_data_rate_byte_hex', "0b") # Use new hex string "0B"
            if isinstance(hex_val, str): # Ensure it's a string
                hex_val = hex_val.lower().replace("0x","")
            rate_map_to_dt = {"0b": 0.005, "19": 0.01, "14": 0.02, "0a": 0.05, "05": 0.1}
            # Add other WIT data rates if present in AddSensorDialog
            dt_for_dp = rate_map_to_dt.get(hex_val, 0.005) # Default to 200Hz if not found
        # Add other sensor type dt calculations if necessary

        # Ensure DataProcessor has a structure for this sensor with initial kinematic params
        self.data_processor._ensure_sensor_id_structure(sensor_id, sensor_type, dt_for_dp, initial_kin_params)

        success = self.sensor_manager.add_sensor(sensor_id, sensor_type, config)
        if success:
            QMessageBox.information(self, "Thành công", f"Đã yêu cầu thêm cảm biến '{config.get('name', sensor_id)}'.")
        else:
            # SensorManager.add_sensor will log if ID already exists,
            # but a warning here is fine too if add_sensor returns False for other reasons.
            existing_sensor = self.sensor_manager.get_sensor_info(sensor_id)
            if existing_sensor: # If it failed because it exists
                 QMessageBox.warning(self, "Lỗi", f"Cảm biến ID '{sensor_id}' đã tồn tại.")
            else: # Other failure reason
                 QMessageBox.warning(self, "Lỗi", f"Không thể thêm cảm biến ID '{sensor_id}'.")
        # self.sensor_screen_new.update_sensors_table() # Covered by sensorListChanged

    def handle_remove_sensor_request(self, sensor_id_to_remove):
        logger.info(f"MainWindow: Received request to remove sensor: {sensor_id_to_remove}")
        
        sensor_info_before_remove = self.sensor_manager.get_sensor_info(sensor_id_to_remove)
        sensor_name_for_msg = sensor_info_before_remove.get('config', {}).get('name', sensor_id_to_remove) if sensor_info_before_remove else sensor_id_to_remove

        if self.sensor_manager.remove_sensor(sensor_id_to_remove):
            QMessageBox.information(self, "Thành công", f"Đã xóa cảm biến '{sensor_name_for_msg}'.")
            self.data_processor.remove_sensor_data(sensor_id_to_remove)
            if self.current_plotting_sensor_id == sensor_id_to_remove:
                self.current_plotting_sensor_id = None
                self.plot_manager.stop_plotting()
                self.plot_manager.reset_plots()
                self.display_screen.dominant_freq_label.setText("Tần số đặc trưng X: -- Hz, Y: -- Hz, Z: -- Hz")
                self.tabs.setTabText(0, "Hiển thị Đồ thị")
                self.settings_screen.set_current_sensor_for_settings(None)
                # After removal, sensorListChanged will update the combo.
                # If the combo becomes empty or changes selection, handle_display_sensor_changed_from_combo
                # should handle selecting a new sensor if available.
        else:
            QMessageBox.warning(self, "Lỗi", f"Không thể xóa cảm biến '{sensor_name_for_msg}'.")

    def handle_sensor_data_from_manager(self, sensor_id, data_dict):
        sensor_info = self.sensor_manager.get_sensor_info(sensor_id)
        sensor_config = sensor_info.get('config') if sensor_info else {}
        self.data_processor.handle_incoming_sensor_data(sensor_id, data_dict, sensor_config)
        if sensor_id == self.current_plotting_sensor_id:
            self.data_processor.calculate_fft_for_sensor(sensor_id)

    def handle_sensor_connection_status_from_manager(self, sensor_id, connected, message):
        logger.info(f"MainWindow: Connection status for {sensor_id}: {connected}, Msg: {message}")
        # self.sensor_screen_new.update_sensors_table() will be called by sensorListChanged if status implies list change
        # or explicitly if needed by tracking. For now, rely on direct updates or periodic checks.

        if sensor_id == self.current_plotting_sensor_id:
            if connected:
                if not self.plot_manager.is_collecting_data:
                    self.plot_manager.start_plotting(self.settings_screen.get_current_display_rate(), sensor_id)
                    logger.info(f"Plotting started for currently selected sensor {sensor_id}.")
            else:
                if self.plot_manager.is_collecting_data:
                    self.plot_manager.stop_plotting()
                    logger.info(f"Plotting stopped for {sensor_id} due to disconnection.")
                if "removed" not in message.lower(): # Don't show warning if it was a manual removal
                    QMessageBox.warning(self, "Mất kết nối", f"Mất kết nối với cảm biến đang hiển thị: {sensor_id}. {message}")
            
            # Update kinematic settings tab title/state
            current_kin_params = self.data_processor.get_sensor_kinematic_params(sensor_id)
            current_adv_params = self.data_processor.get_sensor_advanced_processing_params(sensor_id)
            self.settings_screen.set_current_sensor_for_settings(
                sensor_id if connected else None, 
                current_kin_params if connected else None,
                current_adv_params if connected else None
            )
        
        # Ensure table reflects the latest status (SensorManager should emit list changed if needed)
        # Or SensorManagementScreen can listen to connectionStatusChanged directly too.
        # For simplicity, we can call it here as well if SensorManagementScreen doesn't subscribe directly.
        self.sensor_screen_new.update_sensors_table()

        # Nếu cảm biến vừa kết nối thành công và chưa từng được chọn để hiển thị, tự động chuyển sang hiển thị
        if connected and self.current_plotting_sensor_id is None:
            self.switch_plotting_sensor(sensor_id, suppress_not_connected_msg=True)

    def handle_sensor_selected_for_plotting_from_table(self, sensor_id):
        """Called when a sensor is double-clicked or selected in the SensorManagementScreen table."""
        logger.info(f"MainWindow: Sensor {sensor_id} selected for plotting from table.")
        self.switch_plotting_sensor(sensor_id, suppress_not_connected_msg=False)
        self.display_screen.set_selected_sensor_in_combo(sensor_id) # Sync combobox

    def handle_display_sensor_changed_from_combo(self, sensor_id):
        """Called when sensor selection changes in DisplayScreenWidget's ComboBox."""
        logger.info(f"MainWindow: Sensor {sensor_id} selected for plotting from DisplayScreen ComboBox.")
        if sensor_id == "": # Handles "No sensor" case
            if self.current_plotting_sensor_id: # If there was a sensor plotted
                self.plot_manager.stop_plotting()
                self.plot_manager.reset_plots()
            self.current_plotting_sensor_id = None
            self.tabs.setTabText(0, "Hiển thị Đồ thị")
            self.settings_screen.set_current_sensor_for_settings(None)
            self.advanced_analysis_screen.set_current_sensor(None) # Update analysis screen
            self.display_screen.reset_plots() # Ensure plots are clear
            self.display_screen.dominant_freq_label.setText("Tần số đặc trưng X: -- Hz, Y: -- Hz, Z: -- Hz")

        elif sensor_id and sensor_id != self.current_plotting_sensor_id:
            self.switch_plotting_sensor(sensor_id, suppress_not_connected_msg=False)
        elif sensor_id and sensor_id == self.current_plotting_sensor_id and not self.plot_manager.is_collecting_data:
            # If same sensor selected but not plotting (e.g., was disconnected and now reconnected)
            sensor_info = self.sensor_manager.get_sensor_info(sensor_id)
            if sensor_info and sensor_info.get('connected'):
                self.plot_manager.start_plotting(self.settings_screen.get_current_display_rate(), sensor_id)

    def switch_plotting_sensor(self, new_sensor_id, suppress_not_connected_msg=False):
        """Central logic to switch the sensor being plotted."""
        if self.current_plotting_sensor_id == new_sensor_id and self.plot_manager.is_collecting_data:
            return # Already plotting this sensor

        if self.plot_manager.is_collecting_data:
            self.plot_manager.stop_plotting()

        self.current_plotting_sensor_id = new_sensor_id
        self.data_processor.reset_sensor_data(new_sensor_id) # Reset data for the new sensor
        self.plot_manager.reset_plots() # Clear old plot lines

        sensor_info = self.sensor_manager.get_sensor_info(new_sensor_id)
        display_name = new_sensor_id
        is_connected = False
        if sensor_info:
            display_name = sensor_info.get('config', {}).get('name', new_sensor_id)
            is_connected = sensor_info.get('connected', False)

        self.tabs.setTabText(0, f"Hiển thị Đồ thị ({display_name})")
        
        current_kin_params = self.data_processor.get_sensor_kinematic_params(new_sensor_id)
        current_adv_params = self.data_processor.get_sensor_advanced_processing_params(new_sensor_id)
        self.settings_screen.set_current_sensor_for_settings(
            new_sensor_id if is_connected else None, 
            current_kin_params if is_connected else None,
            current_adv_params if is_connected else None
        )
        self.advanced_analysis_screen.set_current_sensor(new_sensor_id)

        if is_connected:
            self.plot_manager.start_plotting(self.settings_screen.get_current_display_rate(), new_sensor_id)
        else:
            # logger.warning(f"Sensor {new_sensor_id} selected but not connected. Plotting will not start.")
            # if not suppress_not_connected_msg:
            #     QMessageBox.information(self, "Thông báo", f"Cảm biến '{display_name}' hiện chưa kết nối.")
            self.display_screen.reset_plots() # Ensure plots are clear
            self.display_screen.dominant_freq_label.setText("Tần số đặc trưng X: -- Hz, Y: -- Hz, Z: -- Hz")

    def handle_kinematic_settings_applied(self, sensor_id, settings_dict):
        if sensor_id == self.current_plotting_sensor_id:
            logger.info(f"Applying kinematic settings for sensor {sensor_id}: {settings_dict}")
            self.data_processor.update_kinematic_parameters(sensor_id, settings_dict)
            # Data is reset within update_kinematic_parameters, plotting will use new params.
            QMessageBox.information(self, "Thành công", f"Đã áp dụng cài đặt động học cho cảm biến {sensor_id}.")
            # If sensor was plotting, it will continue with new params after data reset.
            # If it was not plotting but connected, it will use new params when plotting starts.
        else:
            QMessageBox.warning(self, "Lưu ý", "Cài đặt động học chỉ áp dụng cho cảm biến đang được hiển thị đồ thị.")

    def handle_advanced_processing_settings_applied(self, sensor_id, settings_dict):
        if sensor_id == self.current_plotting_sensor_id:
            logger.info(f"Applying advanced processing settings for sensor {sensor_id}: {settings_dict}")
            self.data_processor.update_advanced_processing_parameters(sensor_id, settings_dict)
            # Data is reset within update_advanced_processing_parameters, plotting will use new params.
            QMessageBox.information(self, "Thành công", f"Đã áp dụng cài đặt xử lý nâng cao cho cảm biến {sensor_id}.")
            # If sensor was plotting, it will continue with new params after data reset.
            # If it was not plotting but connected, it will use new params when plotting starts.
        else:
            QMessageBox.warning(self, "Lưu ý", "Cài đặt xử lý nâng cao chỉ áp dụng cho cảm biến đang được hiển thị đồ thị.")

    def handle_display_rate_change(self, rate_hz):
        logger.info(f"Display rate changed to {rate_hz} Hz")
        self.plot_manager.set_plot_rate(rate_hz) # Update rate in plot manager
        if self.current_plotting_sensor_id and self.plot_manager.is_collecting_data:
            # Restart with new rate if already plotting
            self.plot_manager.start_plotting(rate_hz, self.current_plotting_sensor_id)

    def closeEvent(self, event):
        logger.info("Closing application...")
        if self.plot_manager: self.plot_manager.stop_plotting()
        if self.sensor_manager:
            self.sensor_manager.stop_all_sensors()
        # Give threads a moment to close, though SensorManager should handle waits.
        QThread.msleep(200) 
        super().closeEvent(event)