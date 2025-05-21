from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
                             QPushButton, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import pyqtSignal, Qt

class SettingsScreenWidget(QWidget):
    display_rate_changed = pyqtSignal(int) # rate_hz
    kinematic_settings_applied = pyqtSignal(str, dict) # sensor_id, settings_dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_sensor_id_for_settings = None
        self.default_kinematic_params = {
            'sample_frame_size': 20,
            'calc_frame_multiplier': 50, # Default from DataProcessor
            'rls_filter_q_vel': 0.9875,  # Default from DataProcessor
            'rls_filter_q_disp': 0.9875, # Default from DataProcessor
            'warmup_frames': 5
        }
        self.init_ui()
        self.update_kinematic_inputs_enabled(False) # Initially disabled

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # === Display Rate Settings ===
        display_settings_group = QGroupBox("Cài đặt Hiển thị")
        display_settings_layout = QVBoxLayout(display_settings_group)

        frame_rate_layout = QHBoxLayout()
        self.frame_rate_label = QLabel("Tốc độ làm mới đồ thị (Hz):")
        self.frame_rate_combo = QComboBox()
        frame_rates = [10, 20, 30, 50, 60, 100] # Common refresh rates
        for rate in frame_rates:
            self.frame_rate_combo.addItem(f"{rate} Hz", rate)
        self.frame_rate_combo.setCurrentIndex(frame_rates.index(30) if 30 in frame_rates else 0) # Default to 30Hz
        self.frame_rate_combo.currentIndexChanged.connect(self.on_display_rate_changed)
        frame_rate_layout.addWidget(self.frame_rate_label)
        frame_rate_layout.addWidget(self.frame_rate_combo)
        frame_rate_layout.addStretch(1)
        display_settings_layout.addLayout(frame_rate_layout)
        main_layout.addWidget(display_settings_group)

        # === Kinematic Processor Settings ===
        self.kinematic_group = QGroupBox("Bộ xử lý Động học (Áp dụng cho cảm biến đang hiển thị)")
        kinematic_layout = QFormLayout(self.kinematic_group)

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
        kinematic_layout.addRow("Hệ số Quên RLS Vận tốc (q_vel):", self.rls_filter_q_vel_input)
        kinematic_layout.addRow("Hệ số Quên RLS Chuyển vị (q_disp):", self.rls_filter_q_disp_input)
        kinematic_layout.addRow("Số Frame Khởi động:", self.warmup_frames_input)

        self.apply_kinematic_button = QPushButton("Áp dụng cho Cảm biến Hiện tại")
        self.apply_kinematic_button.clicked.connect(self.on_apply_kinematic_settings)
        kinematic_layout.addRow(self.apply_kinematic_button)
        
        main_layout.addWidget(self.kinematic_group)
        main_layout.addStretch(1)

    def on_display_rate_changed(self):
        rate_hz = self.frame_rate_combo.currentData()
        if rate_hz is not None:
            self.display_rate_changed.emit(rate_hz)

    def get_current_display_rate(self):
        return self.frame_rate_combo.currentData()

    def on_apply_kinematic_settings(self):
        if self._current_sensor_id_for_settings:
            settings = {
                'sample_frame_size': self.sample_frame_size_input.value(),
                'calc_frame_multiplier': self.calc_frame_multiplier_input.value(),
                'rls_filter_q_vel': self.rls_filter_q_vel_input.value(),
                'rls_filter_q_disp': self.rls_filter_q_disp_input.value(),
                'warmup_frames': self.warmup_frames_input.value()
            }
            self.kinematic_settings_applied.emit(self._current_sensor_id_for_settings, settings)
        else:
            # This case should ideally be prevented by disabling the button
            # if no sensor is active for settings.
            pass 

    def set_current_sensor_for_settings(self, sensor_id, current_params=None):
        """
        Called by MainWindow when the active plotting sensor changes.
        `current_params` is a dict with the current kinematic parameters for that sensor.
        """
        self._current_sensor_id_for_settings = sensor_id
        if sensor_id:
            self.update_kinematic_inputs_enabled(True)
            self.kinematic_group.setTitle(f"Bộ xử lý Động học (Cho cảm biến: {sensor_id})")
            if current_params:
                self.sample_frame_size_input.setValue(current_params.get('sample_frame_size', self.default_kinematic_params['sample_frame_size']))
                self.calc_frame_multiplier_input.setValue(current_params.get('calc_frame_multiplier', self.default_kinematic_params['calc_frame_multiplier']))
                self.rls_filter_q_vel_input.setValue(current_params.get('rls_filter_q_vel', self.default_kinematic_params['rls_filter_q_vel']))
                self.rls_filter_q_disp_input.setValue(current_params.get('rls_filter_q_disp', self.default_kinematic_params['rls_filter_q_disp']))
                self.warmup_frames_input.setValue(current_params.get('warmup_frames', self.default_kinematic_params['warmup_frames']))
            else: # Reset to defaults if no specific params are provided
                self.load_default_kinematic_params()
        else:
            self.update_kinematic_inputs_enabled(False)
            self.kinematic_group.setTitle("Bộ xử lý Động học (Chưa chọn cảm biến hiển thị)")
            self.load_default_kinematic_params()

    def load_default_kinematic_params(self):
        self.sample_frame_size_input.setValue(self.default_kinematic_params['sample_frame_size'])
        self.calc_frame_multiplier_input.setValue(self.default_kinematic_params['calc_frame_multiplier'])
        self.rls_filter_q_vel_input.setValue(self.default_kinematic_params['rls_filter_q_vel'])
        self.rls_filter_q_disp_input.setValue(self.default_kinematic_params['rls_filter_q_disp'])
        self.warmup_frames_input.setValue(self.default_kinematic_params['warmup_frames'])

    def update_kinematic_inputs_enabled(self, enabled):
        self.sample_frame_size_input.setEnabled(enabled)
        self.calc_frame_multiplier_input.setEnabled(enabled)
        self.rls_filter_q_vel_input.setEnabled(enabled)
        self.rls_filter_q_disp_input.setEnabled(enabled)
        self.warmup_frames_input.setEnabled(enabled)
        self.apply_kinematic_button.setEnabled(enabled)