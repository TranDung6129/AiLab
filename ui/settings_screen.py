# ui/settings_screen.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
                             QPushButton, QSpacerItem, QSizePolicy, QFrame) # Added QFrame
from PyQt6.QtCore import pyqtSignal, Qt

class SettingsScreenWidget(QWidget):
    display_rate_changed = pyqtSignal(int) # rate_hz
    kinematic_settings_applied = pyqtSignal(str, dict) # sensor_id, settings_dict
    # New signal for advanced processing settings
    # dict will contain: 'pre_filter_type', 'pre_filter_params', 
    #                    'integration_method', 
    #                    'detrend_method', 'detrend_params'
    advanced_processing_settings_applied = pyqtSignal(str, dict) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_sensor_id_for_settings = None
        self.default_kinematic_params = {
            'sample_frame_size': 20,
            'calc_frame_multiplier': 50,
            'rls_filter_q_vel': 0.9875,
            'rls_filter_q_disp': 0.9875,
            'warmup_frames': 5
        }
        self.default_advanced_processing_params = {
            'pre_filter_type': "None",
            'pre_filter_params': {'cutoff_hz': 0.5, 'order': 2}, # Example for high-pass
            'integration_method': "Trapezoidal",
            'detrend_method': "RLS Filter", # Default to RLS
            'detrend_params': {'poly_order': 2} # Example for polynomial
        }
        self.init_ui()
        self.update_kinematic_inputs_enabled(False) 
        self.update_advanced_processing_inputs_enabled(False) # Initially disabled

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # === Display Rate Settings ===
        display_settings_group = QGroupBox("Cài đặt Hiển thị")
        display_settings_layout = QVBoxLayout(display_settings_group)
        # ... (Display rate settings as before) ...
        frame_rate_layout = QHBoxLayout()
        self.frame_rate_label = QLabel("Tốc độ làm mới đồ thị (Hz):")
        self.frame_rate_combo = QComboBox()
        frame_rates = [10, 20, 30, 50, 60, 100] 
        for rate in frame_rates:
            self.frame_rate_combo.addItem(f"{rate} Hz", rate)
        self.frame_rate_combo.setCurrentIndex(frame_rates.index(30) if 30 in frame_rates else 0)
        self.frame_rate_combo.currentIndexChanged.connect(self.on_display_rate_changed)
        frame_rate_layout.addWidget(self.frame_rate_label)
        frame_rate_layout.addWidget(self.frame_rate_combo)
        frame_rate_layout.addStretch(1)
        display_settings_layout.addLayout(frame_rate_layout)
        main_layout.addWidget(display_settings_group)


        # === Kinematic Processor Settings (RLS specific params are here) ===
        self.kinematic_group = QGroupBox("Cấu hình Bộ xử lý Động học (Mặc định/RLS)")
        kinematic_layout = QFormLayout(self.kinematic_group)
        # ... (Kinematic params: sample_frame_size, calc_frame_multiplier, RLS q_vel, q_disp, warmup_frames as before) ...
        self.sample_frame_size_input = QSpinBox()
        self.sample_frame_size_input.setRange(5, 200)
        self.sample_frame_size_input.setValue(self.default_kinematic_params['sample_frame_size'])

        self.calc_frame_multiplier_input = QSpinBox()
        self.calc_frame_multiplier_input.setRange(10, 500)
        self.calc_frame_multiplier_input.setValue(self.default_kinematic_params['calc_frame_multiplier'])

        self.rls_filter_q_vel_input = QDoubleSpinBox()
        self.rls_filter_q_vel_input.setRange(0.9000, 0.9999)
        self.rls_filter_q_vel_input.setDecimals(4)
        self.rls_filter_q_vel_input.setSingleStep(0.0001)
        self.rls_filter_q_vel_input.setValue(self.default_kinematic_params['rls_filter_q_vel'])

        self.rls_filter_q_disp_input = QDoubleSpinBox()
        self.rls_filter_q_disp_input.setRange(0.9000, 0.9999)
        self.rls_filter_q_disp_input.setDecimals(4)
        self.rls_filter_q_disp_input.setSingleStep(0.0001)
        self.rls_filter_q_disp_input.setValue(self.default_kinematic_params['rls_filter_q_disp'])
        
        self.warmup_frames_input = QSpinBox()
        self.warmup_frames_input.setRange(1, 100)
        self.warmup_frames_input.setValue(self.default_kinematic_params['warmup_frames'])

        kinematic_layout.addRow("Kích thước Frame Mẫu:", self.sample_frame_size_input)
        kinematic_layout.addRow("Bội số Frame Tính toán:", self.calc_frame_multiplier_input)
        self.label_rls_q_vel = QLabel("Hệ số Quên RLS Vận tốc (q_vel):") # Store label to show/hide
        kinematic_layout.addRow(self.label_rls_q_vel, self.rls_filter_q_vel_input)
        self.label_rls_q_disp = QLabel("Hệ số Quên RLS Chuyển vị (q_disp):") # Store label to show/hide
        kinematic_layout.addRow(self.label_rls_q_disp, self.rls_filter_q_disp_input)
        kinematic_layout.addRow("Số Frame Khởi động:", self.warmup_frames_input)
        
        # This button now applies BOTH kinematic and advanced settings together
        # self.apply_kinematic_button = QPushButton("Áp dụng Cài đặt Động học")
        # self.apply_kinematic_button.clicked.connect(self.on_apply_kinematic_settings)
        # kinematic_layout.addRow(self.apply_kinematic_button)
        main_layout.addWidget(self.kinematic_group)

        # === Advanced Signal Processing Options ===
        self.adv_processing_group = QGroupBox("Tùy chọn Xử lý Tín hiệu Nâng cao")
        adv_proc_layout = QFormLayout(self.adv_processing_group)

        # --- Input Pre-Filter ---
        self.pre_filter_type_combo = QComboBox()
        self.pre_filter_type_combo.addItems(["None", "High-pass", "Low-pass"]) # "Band-pass" later
        self.pre_filter_type_combo.currentTextChanged.connect(self.on_pre_filter_type_changed)
        adv_proc_layout.addRow("Bộ lọc Gia tốc Đầu vào:", self.pre_filter_type_combo)

        self.pre_filter_params_widget = QWidget() # Container for conditional params
        self.pre_filter_params_layout = QFormLayout(self.pre_filter_params_widget)
        self.pre_filter_params_layout.setContentsMargins(0,0,0,0)
        
        self.pre_filter_cutoff_input = QDoubleSpinBox()
        self.pre_filter_cutoff_input.setRange(0.01, 50.0) # Example range
        self.pre_filter_cutoff_input.setDecimals(2)
        self.pre_filter_cutoff_input.setValue(self.default_advanced_processing_params['pre_filter_params']['cutoff_hz'])
        self.pre_filter_cutoff_label = QLabel("Tần số cắt (Hz):")
        
        self.pre_filter_order_input = QSpinBox()
        self.pre_filter_order_input.setRange(1, 8) # Example range
        self.pre_filter_order_input.setValue(self.default_advanced_processing_params['pre_filter_params']['order'])
        self.pre_filter_order_label = QLabel("Bậc lọc:")

        # Add to layout (will be shown/hidden)
        self.pre_filter_params_layout.addRow(self.pre_filter_cutoff_label, self.pre_filter_cutoff_input)
        self.pre_filter_params_layout.addRow(self.pre_filter_order_label, self.pre_filter_order_input)
        adv_proc_layout.addRow(self.pre_filter_params_widget)
        self.pre_filter_params_widget.setVisible(False) # Initially hidden

        # --- Integration Method ---
        self.integration_method_combo = QComboBox()
        self.integration_method_combo.addItems(["Trapezoidal"]) # "Simpson" later
        self.integration_method_combo.setCurrentText(self.default_advanced_processing_params['integration_method'])
        adv_proc_layout.addRow("Phương pháp Tích phân:", self.integration_method_combo)

        # --- Detrending Method ---
        self.detrend_method_combo = QComboBox()
        self.detrend_method_combo.addItems(["RLS Filter", "None"]) # "Polynomial" later
        self.detrend_method_combo.setCurrentText(self.default_advanced_processing_params['detrend_method'])
        self.detrend_method_combo.currentTextChanged.connect(self.on_detrend_method_changed)
        adv_proc_layout.addRow("Phương pháp Loại bỏ Xu hướng:", self.detrend_method_combo)
        
        # Detrend parameters (e.g., for Polynomial, if added)
        self.detrend_params_widget = QWidget()
        self.detrend_params_layout = QFormLayout(self.detrend_params_widget)
        self.detrend_params_layout.setContentsMargins(0,0,0,0)
        # Example for Polynomial
        self.detrend_poly_order_input = QSpinBox()
        self.detrend_poly_order_input.setRange(1, 5)
        self.detrend_poly_order_input.setValue(self.default_advanced_processing_params['detrend_params']['poly_order'])
        self.detrend_poly_order_label = QLabel("Bậc đa thức (Polynomial):")
        self.detrend_params_layout.addRow(self.detrend_poly_order_label, self.detrend_poly_order_input)
        adv_proc_layout.addRow(self.detrend_params_widget)
        self.detrend_params_widget.setVisible(False) # Initially hidden

        main_layout.addWidget(self.adv_processing_group)
        
        # === Apply Button for ALL settings ===
        self.apply_all_settings_button = QPushButton("Áp dụng Tất cả Cài đặt cho Cảm biến Hiện tại")
        self.apply_all_settings_button.setStyleSheet("font-weight: bold; padding: 10px;")
        self.apply_all_settings_button.clicked.connect(self.on_apply_all_settings)
        main_layout.addWidget(self.apply_all_settings_button)

        main_layout.addStretch(1)
        self.on_pre_filter_type_changed(self.pre_filter_type_combo.currentText()) # Initial setup for visibility
        self.on_detrend_method_changed(self.detrend_method_combo.currentText()) # Initial setup for RLS param visibility

    def on_display_rate_changed(self):
        rate_hz = self.frame_rate_combo.currentData()
        if rate_hz is not None:
            self.display_rate_changed.emit(rate_hz)

    def get_current_display_rate(self):
        return self.frame_rate_combo.currentData()

    def on_pre_filter_type_changed(self, filter_type):
        is_active = filter_type != "None"
        self.pre_filter_params_widget.setVisible(is_active)
        if filter_type == "High-pass":
            self.pre_filter_cutoff_label.setText("Tần số cắt HP (Hz):")
            self.pre_filter_order_label.setVisible(True)
            self.pre_filter_order_input.setVisible(True)
        elif filter_type == "Low-pass":
            self.pre_filter_cutoff_label.setText("Tần số cắt LP (Hz):")
            self.pre_filter_order_label.setVisible(True)
            self.pre_filter_order_input.setVisible(True)
        # Add "Band-pass" logic here if implemented (two cutoff inputs)

    def on_detrend_method_changed(self, detrend_method):
        # Show/hide RLS specific params in the Kinematic group
        rls_active = detrend_method == "RLS Filter"
        self.label_rls_q_vel.setVisible(rls_active)
        self.rls_filter_q_vel_input.setVisible(rls_active)
        self.label_rls_q_disp.setVisible(rls_active)
        self.rls_filter_q_disp_input.setVisible(rls_active)
        
        # Show/hide other detrend method params
        poly_active = detrend_method == "Polynomial" # Example
        self.detrend_params_widget.setVisible(poly_active)
        if poly_active:
            self.detrend_poly_order_label.setVisible(True)
            self.detrend_poly_order_input.setVisible(True)
        else:
            self.detrend_poly_order_label.setVisible(False)
            self.detrend_poly_order_input.setVisible(False)


    def on_apply_all_settings(self):
        if self._current_sensor_id_for_settings:
            # Kinematic settings
            kin_settings = {
                'sample_frame_size': self.sample_frame_size_input.value(),
                'calc_frame_multiplier': self.calc_frame_multiplier_input.value(),
                'rls_filter_q_vel': self.rls_filter_q_vel_input.value(),
                'rls_filter_q_disp': self.rls_filter_q_disp_input.value(),
                'warmup_frames': self.warmup_frames_input.value()
            }
            self.kinematic_settings_applied.emit(self._current_sensor_id_for_settings, kin_settings)

            # Advanced processing settings
            adv_settings = {
                'pre_filter_type': self.pre_filter_type_combo.currentText(),
                'pre_filter_params': {
                    'cutoff_hz': self.pre_filter_cutoff_input.value(),
                    'order': self.pre_filter_order_input.value()
                    # Add more params like high_cutoff_hz for band-pass later
                },
                'integration_method': self.integration_method_combo.currentText(),
                'detrend_method': self.detrend_method_combo.currentText(),
                'detrend_params': {
                    'poly_order': self.detrend_poly_order_input.value()
                    # RLS q values are part of kin_settings if detrend_method is RLS
                }
            }
            self.advanced_processing_settings_applied.emit(self._current_sensor_id_for_settings, adv_settings)
        else:
            QMessageBox.information(self, "Thông báo", "Chưa có cảm biến nào được chọn để áp dụng cài đặt.")


    def set_current_sensor_for_settings(self, sensor_id, current_kin_params=None, current_adv_proc_params=None):
        self._current_sensor_id_for_settings = sensor_id
        is_sensor_active = bool(sensor_id)

        self.update_kinematic_inputs_enabled(is_sensor_active)
        self.update_advanced_processing_inputs_enabled(is_sensor_active)

        title_suffix = f"(Cho cảm biến: {sensor_id})" if is_sensor_active else "(Chưa chọn cảm biến)"
        self.kinematic_group.setTitle(f"Cấu hình Bộ xử lý Động học {title_suffix}")
        self.adv_processing_group.setTitle(f"Tùy chọn Xử lý Tín hiệu Nâng cao {title_suffix}")

        if is_sensor_active:
            # Load Kinematic Params
            loaded_kin_params = current_kin_params if current_kin_params else self.default_kinematic_params
            self.sample_frame_size_input.setValue(loaded_kin_params.get('sample_frame_size', self.default_kinematic_params['sample_frame_size']))
            self.calc_frame_multiplier_input.setValue(loaded_kin_params.get('calc_frame_multiplier', self.default_kinematic_params['calc_frame_multiplier']))
            self.rls_filter_q_vel_input.setValue(loaded_kin_params.get('rls_filter_q_vel', self.default_kinematic_params['rls_filter_q_vel']))
            self.rls_filter_q_disp_input.setValue(loaded_kin_params.get('rls_filter_q_disp', self.default_kinematic_params['rls_filter_q_disp']))
            self.warmup_frames_input.setValue(loaded_kin_params.get('warmup_frames', self.default_kinematic_params['warmup_frames']))

            # Load Advanced Processing Params
            loaded_adv_params = current_adv_proc_params if current_adv_proc_params else self.default_advanced_processing_params
            
            self.pre_filter_type_combo.setCurrentText(loaded_adv_params.get('pre_filter_type', self.default_advanced_processing_params['pre_filter_type']))
            pre_filter_p = loaded_adv_params.get('pre_filter_params', self.default_advanced_processing_params['pre_filter_params'])
            self.pre_filter_cutoff_input.setValue(pre_filter_p.get('cutoff_hz', self.default_advanced_processing_params['pre_filter_params']['cutoff_hz']))
            self.pre_filter_order_input.setValue(pre_filter_p.get('order', self.default_advanced_processing_params['pre_filter_params']['order']))
            
            self.integration_method_combo.setCurrentText(loaded_adv_params.get('integration_method', self.default_advanced_processing_params['integration_method']))
            self.detrend_method_combo.setCurrentText(loaded_adv_params.get('detrend_method', self.default_advanced_processing_params['detrend_method']))
            
            detrend_p = loaded_adv_params.get('detrend_params', self.default_advanced_processing_params['detrend_params'])
            self.detrend_poly_order_input.setValue(detrend_p.get('poly_order', self.default_advanced_processing_params['detrend_params']['poly_order']))

        else: # No sensor active, load defaults
            self.load_default_kinematic_params()
            self.load_default_advanced_processing_params()
        
        # Update visibility based on loaded/default combo values
        self.on_pre_filter_type_changed(self.pre_filter_type_combo.currentText())
        self.on_detrend_method_changed(self.detrend_method_combo.currentText())


    def load_default_kinematic_params(self):
        # ... (same as before) ...
        self.sample_frame_size_input.setValue(self.default_kinematic_params['sample_frame_size'])
        self.calc_frame_multiplier_input.setValue(self.default_kinematic_params['calc_frame_multiplier'])
        self.rls_filter_q_vel_input.setValue(self.default_kinematic_params['rls_filter_q_vel'])
        self.rls_filter_q_disp_input.setValue(self.default_kinematic_params['rls_filter_q_disp'])
        self.warmup_frames_input.setValue(self.default_kinematic_params['warmup_frames'])


    def load_default_advanced_processing_params(self):
        self.pre_filter_type_combo.setCurrentText(self.default_advanced_processing_params['pre_filter_type'])
        self.pre_filter_cutoff_input.setValue(self.default_advanced_processing_params['pre_filter_params']['cutoff_hz'])
        self.pre_filter_order_input.setValue(self.default_advanced_processing_params['pre_filter_params']['order'])
        self.integration_method_combo.setCurrentText(self.default_advanced_processing_params['integration_method'])
        self.detrend_method_combo.setCurrentText(self.default_advanced_processing_params['detrend_method'])
        self.detrend_poly_order_input.setValue(self.default_advanced_processing_params['detrend_params']['poly_order'])
        # Ensure conditional UI updates
        self.on_pre_filter_type_changed(self.pre_filter_type_combo.currentText())
        self.on_detrend_method_changed(self.detrend_method_combo.currentText())


    def update_kinematic_inputs_enabled(self, enabled):
        # ... (same as before, affects RLS params visibility too via on_detrend_method_changed) ...
        self.sample_frame_size_input.setEnabled(enabled)
        self.calc_frame_multiplier_input.setEnabled(enabled)
        self.rls_filter_q_vel_input.setEnabled(enabled and self.detrend_method_combo.currentText() == "RLS Filter")
        self.rls_filter_q_disp_input.setEnabled(enabled and self.detrend_method_combo.currentText() == "RLS Filter")
        self.warmup_frames_input.setEnabled(enabled)
        # Apply button is now global
        # self.apply_kinematic_button.setEnabled(enabled)


    def update_advanced_processing_inputs_enabled(self, enabled):
        self.pre_filter_type_combo.setEnabled(enabled)
        self.pre_filter_cutoff_input.setEnabled(enabled and self.pre_filter_type_combo.currentText() != "None")
        self.pre_filter_order_input.setEnabled(enabled and self.pre_filter_type_combo.currentText() != "None")
        self.integration_method_combo.setEnabled(enabled)
        self.detrend_method_combo.setEnabled(enabled)
        self.detrend_poly_order_input.setEnabled(enabled and self.detrend_method_combo.currentText() == "Polynomial")
        self.apply_all_settings_button.setEnabled(enabled)