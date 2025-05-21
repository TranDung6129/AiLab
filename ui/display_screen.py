# ui/display_screen.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
                             QComboBox, QPushButton, QDialog, QDialogButtonBox,
                             QColorDialog, QSizePolicy, QFormLayout, QGroupBox, QMessageBox)
import pyqtgraph as pg
import numpy as np
from PyQt6.QtCore import pyqtSignal, Qt

class PlotConfigDialog(QDialog):
    # Signal: plot_styles_changed(dict_of_styles)
    # Example: {'acc': {'x': 'r', 'y': 'g', 'z': 'b'}, 'vel': {...}, 'disp': {...}}
    plot_styles_applied = pyqtSignal(dict)

    def __init__(self, current_styles, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tùy chỉnh Màu sắc Đồ thị")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)  # Set application modal
        self.current_styles = current_styles # Store a copy
        self.new_styles = {
            plot_type: {axis: pg.mkColor(color_val) for axis, color_val in axes.items()}
            for plot_type, axes in current_styles.items()
        } # Work with QColor objects initially

        self.color_buttons = {} # To store QPushButtons for color picking

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        for plot_type, axes_colors in self.current_styles.items():
            group_label = ""
            if plot_type == 'acc': group_label = "Gia tốc"
            elif plot_type == 'vel': group_label = "Vận tốc"
            elif plot_type == 'disp': group_label = "Chuyển vị"
            else: group_label = plot_type.capitalize()

            plot_group_box = QGroupBox(group_label)
            plot_group_layout = QFormLayout(plot_group_box)
            self.color_buttons[plot_type] = {}

            for axis, color_val in axes_colors.items():
                btn = QPushButton()
                btn.setStyleSheet(f"background-color: {pg.mkColor(color_val).name()}; color: white; padding: 5px;")
                btn.setText(f"Màu Trục {axis.upper()}")
                btn.clicked.connect(lambda checked, pt=plot_type, ax=axis, b=btn: self.pick_color(pt, ax, b))
                plot_group_layout.addRow(f"Trục {axis.upper()}:", btn)
                self.color_buttons[plot_type][axis] = btn
            
            layout.addWidget(plot_group_box)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.apply_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)
        self.setMinimumWidth(350)

    def pick_color(self, plot_type, axis, button_widget):
        initial_color = self.new_styles[plot_type][axis]
        color = QColorDialog.getColor(initial_color, self, f"Chọn màu cho {plot_type.capitalize()} - Trục {axis.upper()}")
        if color.isValid():
            self.new_styles[plot_type][axis] = color
            button_widget.setStyleSheet(f"background-color: {color.name()}; color: white; padding: 5px;")

    def apply_and_accept(self):
        # Convert QColor back to string for pyqtgraph when emitting
        final_styles_str = {
            plot_type: {axis: pg.mkColor(q_color).name() for axis, q_color in axes.items()}
            for plot_type, axes in self.new_styles.items()
        }
        self.plot_styles_applied.emit(final_styles_str)
        self.accept()


class DisplayScreenWidget(QWidget):
    MAX_DATA_POINTS = 1000
    # Signal: selected_sensor_changed(sensor_id_str)
    sensor_selection_changed = pyqtSignal(str)
    # Signal: plot_config_requested() -> MainWindow opens dialog
    # No, dialog is opened by this class, emits styles then.
    plot_styles_updated = pyqtSignal(dict)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_plot_styles = {
            'acc': {'x': 'r', 'y': 'g', 'z': 'b'},
            'vel': {'x': 'r', 'y': 'g', 'z': 'b'},
            'disp': {'x': 'r', 'y': 'g', 'z': 'b'}
        }
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Top bar for sensor selection and config button
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(QLabel("Hiển thị cảm biến:"))
        self.sensor_selector_combo = QComboBox()
        self.sensor_selector_combo.setMinimumWidth(200)
        self.sensor_selector_combo.currentIndexChanged.connect(self._on_sensor_selection_changed)
        top_bar_layout.addWidget(self.sensor_selector_combo)
        
        self.configure_plot_button = QPushButton("Tùy chỉnh Đồ thị")
        self.configure_plot_button.clicked.connect(self.open_plot_config_dialog)
        top_bar_layout.addWidget(self.configure_plot_button)
        top_bar_layout.addStretch(1)
        main_layout.addLayout(top_bar_layout)

        # Label hiển thị tần số đặc trưng
        self.dominant_freq_label = QLabel("Tần số đặc trưng X: -- Hz, Y: -- Hz, Z: -- Hz")
        main_layout.addWidget(self.dominant_freq_label)

        plot_grid_layout = QGridLayout()
        self.plot_widget_main = pg.GraphicsLayoutWidget()
        self.plot_widget_fft = pg.GraphicsLayoutWidget()

        plot_grid_layout.addWidget(self.plot_widget_main, 0, 0)
        plot_grid_layout.addWidget(self.plot_widget_fft, 0, 1)
        main_layout.addLayout(plot_grid_layout)

        # Plots chính
        self.plot_acc = self.plot_widget_main.addPlot(row=0, col=0, title="Gia tốc (m/s^2)")
        self.plot_vel = self.plot_widget_main.addPlot(row=1, col=0, title="Vận tốc (m/s)")
        self.plot_disp = self.plot_widget_main.addPlot(row=2, col=0, title="Li độ (m)")

        # Plots FFT
        self.plot_fft_x = self.plot_widget_fft.addPlot(row=0, col=0, title="FFT Gia tốc X")
        self.plot_fft_y = self.plot_widget_fft.addPlot(row=1, col=0, title="FFT Gia tốc Y")
        self.plot_fft_z = self.plot_widget_fft.addPlot(row=2, col=0, title="FFT Gia tốc Z")

        for plot_item_pg in [self.plot_acc, self.plot_vel, self.plot_disp,
                               self.plot_fft_x, self.plot_fft_y, self.plot_fft_z]:
            plot_item_pg.showGrid(x=True, y=True)
            if plot_item_pg not in [self.plot_fft_x, self.plot_fft_y, self.plot_fft_z]:
                plot_item_pg.addLegend()
            plot_item_pg.setDownsampling(auto=True, mode='peak', ds=5)

        # Curves cho plots chính
        self.curves_acc = {
            'x': self.plot_acc.plot(pen=self.current_plot_styles['acc']['x'], name='AccX'),
            'y': self.plot_acc.plot(pen=self.current_plot_styles['acc']['y'], name='AccY'),
            'z': self.plot_acc.plot(pen=self.current_plot_styles['acc']['z'], name='AccZ')
        }
        self.curves_vel = {
            'x': self.plot_vel.plot(pen=self.current_plot_styles['vel']['x'], name='VelX'),
            'y': self.plot_vel.plot(pen=self.current_plot_styles['vel']['y'], name='VelY'),
            'z': self.plot_vel.plot(pen=self.current_plot_styles['vel']['z'], name='VelZ')
        }
        self.curves_disp = {
            'x': self.plot_disp.plot(pen=self.current_plot_styles['disp']['x'], name='DispX'),
            'y': self.plot_disp.plot(pen=self.current_plot_styles['disp']['y'], name='DispY'),
            'z': self.plot_disp.plot(pen=self.current_plot_styles['disp']['z'], name='DispZ')
        }

        # Curves cho FFT
        self.curve_fft_x = self.plot_fft_x.plot(pen='r')
        self.curve_fft_y = self.plot_fft_y.plot(pen='g')
        self.curve_fft_z = self.plot_fft_z.plot(pen='b')

    def _on_sensor_selection_changed(self):
        sensor_id = self.sensor_selector_combo.currentData()
        if sensor_id:
            self.sensor_selection_changed.emit(sensor_id)

    def update_sensor_selector(self, sensor_manager):
        """Called by MainWindow to populate the sensor selector."""
        current_selection_id = self.sensor_selector_combo.currentData()
        self.sensor_selector_combo.blockSignals(True)
        self.sensor_selector_combo.clear()
        all_sensor_ids = sensor_manager.get_all_sensor_ids()
        if not all_sensor_ids:
            self.sensor_selector_combo.addItem("Không có cảm biến nào", None)
            self.sensor_selector_combo.setEnabled(False)
            self.sensor_selector_combo.blockSignals(False)
            # Do NOT emit sensor_selection_changed here to avoid warning popup on startup
            return

        self.sensor_selector_combo.setEnabled(True)
        for sensor_id_val in all_sensor_ids:
            s_info = sensor_manager.get_sensor_info(sensor_id_val)
            display_name = s_info.get('config', {}).get('name', sensor_id_val) if s_info else sensor_id_val
            self.sensor_selector_combo.addItem(f"{display_name} ({sensor_id_val})", sensor_id_val)

        # Try to restore previous selection or select the first one
        index_to_restore = self.sensor_selector_combo.findData(current_selection_id)
        if index_to_restore != -1:
            self.sensor_selector_combo.setCurrentIndex(index_to_restore)
        elif self.sensor_selector_combo.count() > 0:
             self.sensor_selector_combo.setCurrentIndex(0)
             # Explicitly emit for the first item if current_selection_id was None or not found
             if current_selection_id != self.sensor_selector_combo.currentData():
                  self.sensor_selection_changed.emit(self.sensor_selector_combo.currentData())

        self.sensor_selector_combo.blockSignals(False)
        # If only one sensor is available and no selection was made prior, emit its ID
        if self.sensor_selector_combo.count() == 1 and current_selection_id is None:
             self.sensor_selection_changed.emit(self.sensor_selector_combo.currentData())


    def set_selected_sensor_in_combo(self, sensor_id):
        """Allows MainWindow to externally set the combo's selection."""
        index = self.sensor_selector_combo.findData(sensor_id)
        if index != -1:
            self.sensor_selector_combo.blockSignals(True) # Avoid re-emitting selection changed
            self.sensor_selector_combo.setCurrentIndex(index)
            self.sensor_selector_combo.blockSignals(False)
        elif not sensor_id and self.sensor_selector_combo.count() > 0 and self.sensor_selector_combo.itemData(0) is None:
             # Case for "No sensors available" or placeholder
             self.sensor_selector_combo.blockSignals(True)
             self.sensor_selector_combo.setCurrentIndex(0)
             self.sensor_selector_combo.blockSignals(False)


    def open_plot_config_dialog(self):
        # Placeholder: show a simple message box instead of opening the color config dialog
        QMessageBox.information(self, "Thông báo", "Chức năng tùy chỉnh màu sắc sẽ sớm được cập nhật.")

    def apply_plot_styles(self, new_styles):
        self.current_plot_styles = new_styles
        for plot_type, axes_colors in new_styles.items():
            curves_dict = None
            if plot_type == 'acc': curves_dict = self.curves_acc
            elif plot_type == 'vel': curves_dict = self.curves_vel
            elif plot_type == 'disp': curves_dict = self.curves_disp
            
            if curves_dict:
                for axis, color_val in axes_colors.items():
                    if axis in curves_dict:
                        curves_dict[axis].setPen(pg.mkPen(color_val))
        self.plot_styles_updated.emit(self.current_plot_styles) # Inform MainWindow if needed (e.g. to save settings)


    def update_plots(self, time_data, acc_data, vel_data, disp_data, fft_data, dominant_freqs):
        min_main_len = len(time_data)
        if not (acc_data and vel_data and disp_data and
                all(axis in acc_data for axis in ['x', 'y', 'z']) and
                all(axis in vel_data for axis in ['x', 'y', 'z']) and
                all(axis in disp_data for axis in ['x', 'y', 'z'])):
            # self.reset_plots() # Consider if reset is desired or just wait for data
            return

        for axis in ['x', 'y', 'z']:
            min_main_len = min(min_main_len, len(acc_data[axis]), len(vel_data[axis]), len(disp_data[axis]))

        if min_main_len == 0:
            # It's possible time_data has points but others don't yet, or vice versa.
            # Clearing might be too aggressive if it's just a momentary lag.
            # For now, if no consistent data, don't plot.
            return

        n_points_main = min(min_main_len, self.MAX_DATA_POINTS)
        plot_time_main = time_data[-n_points_main:]

        if len(plot_time_main) > 0:
            self.curves_acc['x'].setData(plot_time_main, acc_data['x'][-n_points_main:])
            self.curves_acc['y'].setData(plot_time_main, acc_data['y'][-n_points_main:])
            self.curves_acc['z'].setData(plot_time_main, acc_data['z'][-n_points_main:])

            self.curves_vel['x'].setData(plot_time_main, vel_data['x'][-n_points_main:])
            self.curves_vel['y'].setData(plot_time_main, vel_data['y'][-n_points_main:])
            self.curves_vel['z'].setData(plot_time_main, vel_data['z'][-n_points_main:])

            self.curves_disp['x'].setData(plot_time_main, disp_data['x'][-n_points_main:])
            self.curves_disp['y'].setData(plot_time_main, disp_data['y'][-n_points_main:])
            self.curves_disp['z'].setData(plot_time_main, disp_data['z'][-n_points_main:])

        # Update FFT plots
        if fft_data and 'x' in fft_data and fft_data['x']['freq'] is not None and fft_data['x']['amp'] is not None:
            self.curve_fft_x.setData(fft_data['x']['freq'], fft_data['x']['amp'])
        else:
            self.curve_fft_x.clear()

        if fft_data and 'y' in fft_data and fft_data['y']['freq'] is not None and fft_data['y']['amp'] is not None:
            self.curve_fft_y.setData(fft_data['y']['freq'], fft_data['y']['amp'])
        else:
            self.curve_fft_y.clear()

        if fft_data and 'z' in fft_data and fft_data['z']['freq'] is not None and fft_data['z']['amp'] is not None:
            self.curve_fft_z.setData(fft_data['z']['freq'], fft_data['z']['amp'])
        else:
            self.curve_fft_z.clear()

        self.update_dominant_freq_label(dominant_freqs if dominant_freqs else {'x':0,'y':0,'z':0})


    def update_dominant_freq_label(self, dominant_freqs):
        fx = dominant_freqs.get('x', 0)
        fy = dominant_freqs.get('y', 0)
        fz = dominant_freqs.get('z', 0)
        self.dominant_freq_label.setText(f"Tần số X: {fx:.2f} Hz, Y: {fy:.2f} Hz, Z: {fz:.2f} Hz")

    def reset_plots(self):
        empty_arr = np.array([])
        for axis in ['x', 'y', 'z']:
            if axis in self.curves_acc: self.curves_acc[axis].setData(empty_arr, empty_arr)
            if axis in self.curves_vel: self.curves_vel[axis].setData(empty_arr, empty_arr)
            if axis in self.curves_disp: self.curves_disp[axis].setData(empty_arr, empty_arr)
        if hasattr(self, 'curve_fft_x'): self.curve_fft_x.clear()
        if hasattr(self, 'curve_fft_y'): self.curve_fft_y.clear()
        if hasattr(self, 'curve_fft_z'): self.curve_fft_z.clear()
        self.update_dominant_freq_label({'x': 0, 'y': 0, 'z': 0})