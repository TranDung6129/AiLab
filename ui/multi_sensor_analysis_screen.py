# ui/multi_sensor_analysis_screen.py
import logging
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QGroupBox, QListWidget,
    QTreeWidget, QTreeWidgetItem, QComboBox, QPushButton, QSpinBox, QLabel,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal

logger = logging.getLogger(__name__)

# Available data fields for selection (can be expanded)
AVAILABLE_DATA_FIELDS = {
    "Processed": ["AccX", "AccY", "AccZ", "VelX", "VelY", "VelZ", "DispX", "DispY", "DispZ"],
    "Raw (for FFT)": ["RawAccX", "RawAccY", "RawAccZ"], # Assuming raw acc is stored with these keys
    "FFT": ["FFTFreqX", "FFTAmpX", "FFTFreqY", "FFTAmpY", "FFTFreqZ", "FFTAmpZ"]
}


class MultiSensorAnalysisScreenWidget(QWidget):
    def __init__(self, data_processor, sensor_manager, parent=None):
        super().__init__(parent)
        self.data_processor = data_processor
        self.sensor_manager = sensor_manager
        self.current_analysis_data = {} # To store fetched data for analysis

        self.init_ui()
        self.update_sensor_list() # Initial population

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Left Control Panel ---
        left_panel_widget = QWidget()
        left_panel_layout = QVBoxLayout(left_panel_widget)

        # Sensor and Field Selection
        selection_group = QGroupBox("Chọn Cảm biến và Trường Dữ liệu")
        selection_layout = QVBoxLayout(selection_group)
        self.sensor_field_tree = QTreeWidget()
        self.sensor_field_tree.setHeaderLabels(["Cảm biến / Trường dữ liệu"])
        self.sensor_field_tree.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection) # Not directly used for checks
        selection_layout.addWidget(self.sensor_field_tree)
        left_panel_layout.addWidget(selection_group)

        # Analysis Configuration
        config_group = QGroupBox("Cấu hình Phân tích")
        config_layout = QVBoxLayout(config_group)

        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems(["Overlay Đồ thị", "Phân tích Tương quan", "Đồ thị Chênh lệch"])
        self.analysis_type_combo.currentTextChanged.connect(self.on_analysis_type_changed)
        config_layout.addWidget(QLabel("Loại Phân tích:"))
        config_layout.addWidget(self.analysis_type_combo)

        self.num_data_points_spinbox = QSpinBox()
        self.num_data_points_spinbox.setRange(100, 5000)
        self.num_data_points_spinbox.setValue(1000)
        self.num_data_points_spinbox.setToolTip("Số điểm dữ liệu gần nhất từ mỗi stream để phân tích.")
        config_layout.addWidget(QLabel("Số điểm dữ liệu/stream:"))
        config_layout.addWidget(self.num_data_points_spinbox)
        
        # Placeholder for specific analysis options
        self.analysis_options_widget = QWidget()
        self.analysis_options_layout = QVBoxLayout(self.analysis_options_widget)
        self.analysis_options_widget.setLayout(self.analysis_options_layout)
        config_layout.addWidget(self.analysis_options_widget)


        self.run_analysis_button = QPushButton("Chạy Phân tích")
        self.run_analysis_button.clicked.connect(self.run_analysis)
        config_layout.addWidget(self.run_analysis_button)
        left_panel_layout.addWidget(config_group)

        left_panel_layout.addStretch(1)
        left_panel_widget.setLayout(left_panel_layout)

        # --- Right Display Area ---
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        self.analysis_results_tabs = QTabWidget()

        # Tab 1: Overlay Plot
        self.overlay_plot_tab = QWidget()
        overlay_layout = QVBoxLayout(self.overlay_plot_tab)
        self.overlay_plot_widget = pg.PlotWidget()
        self.overlay_plot_widget.addLegend()
        self.overlay_plot_widget.showGrid(x=True, y=True)
        overlay_layout.addWidget(self.overlay_plot_widget)
        self.analysis_results_tabs.addTab(self.overlay_plot_tab, "Overlay Đồ thị")

        # Tab 2: Correlation Analysis
        self.correlation_tab = QWidget()
        correlation_layout = QVBoxLayout(self.correlation_tab)
        self.correlation_table = QTableWidget()
        self.correlation_heatmap = pg.ImageView() # For heatmap
        correlation_splitter = QSplitter(Qt.Orientation.Vertical)
        correlation_splitter.addWidget(self.correlation_table)
        correlation_splitter.addWidget(self.correlation_heatmap)
        correlation_layout.addWidget(correlation_splitter)
        self.analysis_results_tabs.addTab(self.correlation_tab, "Phân tích Tương quan")

        # Tab 3: Difference Plot
        self.difference_plot_tab = QWidget()
        difference_layout = QVBoxLayout(self.difference_plot_tab)
        self.difference_plot_widget = pg.PlotWidget()
        self.difference_plot_widget.addLegend()
        self.difference_plot_widget.showGrid(x=True, y=True)
        difference_layout.addWidget(self.difference_plot_widget)
        self.analysis_results_tabs.addTab(self.difference_plot_tab, "Đồ thị Chênh lệch")

        right_panel_layout.addWidget(self.analysis_results_tabs)
        right_panel_widget.setLayout(right_panel_layout)

        splitter.addWidget(left_panel_widget)
        splitter.addWidget(right_panel_widget)
        splitter.setStretchFactor(0, 1) # Control panel
        splitter.setStretchFactor(1, 3) # Display area
        main_layout.addWidget(splitter)

        self.on_analysis_type_changed(self.analysis_type_combo.currentText()) # Setup initial options

    def on_analysis_type_changed(self, analysis_type):
        # Clear previous options
        while self.analysis_options_layout.count():
            child = self.analysis_options_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if analysis_type == "Đồ thị Chênh lệch":
            self.stream_a_label = QLabel("Stream A:")
            self.stream_a_combo = QComboBox()
            self.stream_b_label = QLabel("Stream B:")
            self.stream_b_combo = QComboBox()
            self.analysis_options_layout.addWidget(self.stream_a_label)
            self.analysis_options_layout.addWidget(self.stream_a_combo)
            self.analysis_options_layout.addWidget(self.stream_b_label)
            self.analysis_options_layout.addWidget(self.stream_b_combo)
            self.update_difference_plot_combos() # Populate if streams already selected
        # Add more specific options for other types if needed later

    def update_sensor_list(self):
        self.sensor_field_tree.clear()
        if not self.sensor_manager:
            return

        all_sensor_ids = self.sensor_manager.get_all_sensor_ids()
        for sensor_id in all_sensor_ids:
            sensor_info = self.sensor_manager.get_sensor_info(sensor_id)
            if sensor_info and sensor_info.get('connected'):
                sensor_name = sensor_info.get('config', {}).get('name', sensor_id)
                sensor_item = QTreeWidgetItem(self.sensor_field_tree, [f"{sensor_name} ({sensor_id})"])
                sensor_item.setData(0, Qt.ItemDataRole.UserRole, sensor_id) # Store sensor_id
                sensor_item.setFlags(sensor_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
                sensor_item.setCheckState(0, Qt.CheckState.Unchecked)

                # Add data fields as children
                for group_name, fields in AVAILABLE_DATA_FIELDS.items():
                    # For simplicity, we'll assume these fields are generally available.
                    # A more robust way would be to check DataProcessor for actual available keys.
                    for field_key in fields:
                        field_item = QTreeWidgetItem(sensor_item, [field_key])
                        field_item.setData(0, Qt.ItemDataRole.UserRole, field_key) # Store field_key
                        field_item.setFlags(field_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        field_item.setCheckState(0, Qt.CheckState.Unchecked)
        self.sensor_field_tree.expandAll()


    def get_selected_streams(self):
        """
        Returns a list of tuples: (sensor_id, field_key, display_name)
        Example: [('SensorAlpha_123', 'AccX', 'SensorAlpha-AccX'), ...]
        """
        selected_streams = []
        root = self.sensor_field_tree.invisibleRootItem()
        for i in range(root.childCount()):
            sensor_item = root.child(i)
            sensor_id = sensor_item.data(0, Qt.ItemDataRole.UserRole)
            sensor_display_name_parts = sensor_item.text(0).split('(')
            sensor_short_name = sensor_display_name_parts[0].strip()

            for j in range(sensor_item.childCount()):
                field_item = sensor_item.child(j)
                if field_item.checkState(0) == Qt.CheckState.Checked:
                    field_key = field_item.data(0, Qt.ItemDataRole.UserRole)
                    display_name = f"{sensor_short_name}-{field_key}"
                    selected_streams.append({'id': sensor_id, 'key': field_key, 'name': display_name})
        return selected_streams

    def update_difference_plot_combos(self):
        if not hasattr(self, 'stream_a_combo'): return # UI not ready

        selected_streams = self.get_selected_streams()
        current_a = self.stream_a_combo.currentData()
        current_b = self.stream_b_combo.currentData()

        self.stream_a_combo.clear()
        self.stream_b_combo.clear()

        for stream in selected_streams:
            # Use a unique identifier for combo data if needed, e.g., sensor_id + field_key
            unique_stream_id = f"{stream['id']}_{stream['key']}"
            self.stream_a_combo.addItem(stream['name'], unique_stream_id)
            self.stream_b_combo.addItem(stream['name'], unique_stream_id)
        
        idx_a = self.stream_a_combo.findData(current_a)
        if idx_a != -1: self.stream_a_combo.setCurrentIndex(idx_a)
        idx_b = self.stream_b_combo.findData(current_b)
        if idx_b != -1: self.stream_b_combo.setCurrentIndex(idx_b)


    def run_analysis(self):
        selected_streams_details = self.get_selected_streams()
        if not selected_streams_details:
            QMessageBox.warning(self, "Chọn Dữ liệu", "Vui lòng chọn ít nhất một stream dữ liệu để phân tích.")
            return

        analysis_type = self.analysis_type_combo.currentText()
        num_points = self.num_data_points_spinbox.value()
        
        self.current_analysis_data.clear()
        self.current_analysis_data['streams'] = {}
        self.current_analysis_data['time_vectors'] = {}
        min_len_all_streams = float('inf')

        # Fetch data for all selected streams
        for stream_info in selected_streams_details:
            sensor_id = stream_info['id']
            field_key = stream_info['key'] # e.g., "AccX", "VelY", "RawAccZ"
            
            # DataProcessor stores data in a nested structure, e.g.
            # sds['processed_acc']['x'], sds['raw_acc']['x']
            # We need to map field_key to the actual data path in DataProcessor
            
            full_plot_data = self.data_processor.get_plot_data_for_sensor(sensor_id)
            if not full_plot_data:
                logger.warning(f"Không có dữ liệu từ DataProcessor cho cảm biến: {sensor_id}")
                continue

            target_data_array = None
            time_data_array = full_plot_data['time_data'] # Common time vector for processed data

            # Map field_key to actual data arrays
            if field_key.startswith("Acc") or field_key.startswith("Vel") or field_key.startswith("Disp"):
                dtype_map = {"Acc": "acc_data", "Vel": "vel_data", "Disp": "disp_data"}
                axis_map = field_key[-1].lower() # X, Y, Z -> x, y, z
                data_category = dtype_map.get(field_key[:-1]) # Acc, Vel, Disp
                if data_category and axis_map in full_plot_data.get(data_category, {}):
                    target_data_array = full_plot_data[data_category][axis_map]
            elif field_key.startswith("RawAcc"): # Assuming sds['raw_acc']['x'] from DataProcessor
                axis_map = field_key[-1].lower()
                if axis_map in full_plot_data.get('raw_acc_data_for_multi_analysis', {}): # DP needs to provide this
                     # DP's get_plot_data_for_sensor does not return raw_acc directly for plotting in display_screen
                     # We might need to fetch it separately or enhance get_plot_data_for_sensor.
                     # For now, let's assume DataProcessor's main data store has sds['raw_acc']
                    if sensor_id in self.data_processor._sensor_data_store: # Accessing internal for now
                        target_data_array = self.data_processor._sensor_data_store[sensor_id]['raw_acc'][axis_map]
                        # Raw data might not share the same time_data as processed.
                        # This needs careful handling if raw_acc has different length/dt.
                        # For simplicity, let's assume it uses the same time_data length for now.
                else: # Fallback for demonstration if DP doesn't explicitly provide raw_acc for multi-analysis
                    sds = self.data_processor._sensor_data_store.get(sensor_id)
                    if sds and axis_map in sds['raw_acc']:
                        target_data_array = sds['raw_acc'][axis_map]


            # TODO: Add mapping for FFT data if needed (FFTFreqX, FFTAmpX etc.)

            if target_data_array is not None and len(target_data_array) > 0 and len(time_data_array) > 0:
                # Ensure data and time are of same length before slicing
                current_len = min(len(target_data_array), len(time_data_array))
                if current_len == 0 : continue

                slice_len = min(num_points, current_len)
                
                self.current_analysis_data['streams'][stream_info['name']] = target_data_array[-slice_len:]
                self.current_analysis_data['time_vectors'][stream_info['name']] = time_data_array[-slice_len:]
                min_len_all_streams = min(min_len_all_streams, slice_len)
            else:
                logger.warning(f"Không tìm thấy hoặc dữ liệu rỗng cho {field_key} của cảm biến {sensor_id}")

        if not self.current_analysis_data['streams']:
            QMessageBox.warning(self, "Lỗi Dữ liệu", "Không thể lấy dữ liệu cho các stream đã chọn.")
            return

        # Optional: Interpolate all streams to a common time vector of min_len_all_streams
        # This is important for correlation and difference plots.
        # For simplicity in this step, we will truncate all to min_len_all_streams
        # and assume their dt is similar enough for initial overlay.
        if min_len_all_streams == float('inf') : min_len_all_streams = 0
        
        common_time_vector = None
        for stream_name in list(self.current_analysis_data['streams'].keys()): # Use list for safe iteration
            if len(self.current_analysis_data['streams'][stream_name]) > min_len_all_streams:
                self.current_analysis_data['streams'][stream_name] = self.current_analysis_data['streams'][stream_name][-min_len_all_streams:]
            if len(self.current_analysis_data['time_vectors'][stream_name]) > min_len_all_streams:
                self.current_analysis_data['time_vectors'][stream_name] = self.current_analysis_data['time_vectors'][stream_name][-min_len_all_streams:]
            if common_time_vector is None and len(self.current_analysis_data['time_vectors'][stream_name]) == min_len_all_streams:
                common_time_vector = self.current_analysis_data['time_vectors'][stream_name]

        if common_time_vector is None and min_len_all_streams > 0: # Create a generic time vector if needed
             # Find a dt from one of the sensors, assume others are similar for this simple case.
            first_stream_info = selected_streams_details[0]
            s_id = first_stream_info['id']
            dt_sensor = self.data_processor._sensor_data_store.get(s_id, {}).get('config',{}).get('dt', 0.01)
            common_time_vector = np.arange(0, min_len_all_streams * dt_sensor, dt_sensor)[:min_len_all_streams]


        self.current_analysis_data['common_time_vector'] = common_time_vector


        # --- Perform Analysis and Display ---
        if analysis_type == "Overlay Đồ thị":
            self.display_overlay_plot()
            self.analysis_results_tabs.setCurrentWidget(self.overlay_plot_tab)
        elif analysis_type == "Phân tích Tương quan":
            self.display_correlation_analysis()
            self.analysis_results_tabs.setCurrentWidget(self.correlation_tab)
        elif analysis_type == "Đồ thị Chênh lệch":
            self.display_difference_plot()
            self.analysis_results_tabs.setCurrentWidget(self.difference_plot_tab)
            
        self.update_difference_plot_combos() # Refresh combos for difference plot

    def display_overlay_plot(self):
        self.overlay_plot_widget.clear()
        self.overlay_plot_widget.addLegend(offset=(-10,10)) # Re-add legend

        if not self.current_analysis_data.get('streams'):
            return

        time_vector = self.current_analysis_data.get('common_time_vector')
        if time_vector is None or time_vector.size == 0:
            logger.warning("Không có vector thời gian chung cho overlay plot.")
            # Fallback: plot against sample index if time vector is problematic
            use_index_as_time = True
        else:
            use_index_as_time = False


        pens = [pg.mkPen(color, width=1) for color in ['r', 'g', 'b', 'c', 'm', 'y', 'k', 
                                                        (255,165,0), (128,0,128), (0,128,0)]] # Some default pens

        for i, (stream_name, data_array) in enumerate(self.current_analysis_data['streams'].items()):
            if use_index_as_time:
                time_data_for_plot = np.arange(len(data_array))
                self.overlay_plot_widget.setLabel('bottom', 'Chỉ số Mẫu')
            else:
                time_data_for_plot = time_vector
                self.overlay_plot_widget.setLabel('bottom', 'Thời gian (s)')

            if len(time_data_for_plot) == len(data_array) and len(data_array) > 0 :
                 self.overlay_plot_widget.plot(time_data_for_plot, data_array, pen=pens[i % len(pens)], name=stream_name)
            else:
                 logger.warning(f"Bỏ qua stream {stream_name} cho overlay: độ dài không khớp hoặc rỗng.")

    def display_correlation_analysis(self):
        self.correlation_table.clearContents()
        self.correlation_table.setRowCount(0)
        self.correlation_table.setColumnCount(0)
        self.correlation_heatmap.clear()

        stream_names = list(self.current_analysis_data.get('streams', {}).keys())
        if len(stream_names) < 2:
            QMessageBox.information(self, "Tương quan", "Cần ít nhất 2 stream dữ liệu để tính tương quan.")
            return

        # Create a data matrix (streams as columns)
        # Ensure all data arrays are of the same length (already done by min_len_all_streams truncation)
        num_points = len(self.current_analysis_data['streams'][stream_names[0]])
        data_matrix = np.zeros((num_points, len(stream_names)))

        for i, name in enumerate(stream_names):
            data_matrix[:, i] = self.current_analysis_data['streams'][name]
        
        if data_matrix.shape[0] < 2 : # Need at least 2 data points
             QMessageBox.warning(self, "Lỗi dữ liệu", "Không đủ điểm dữ liệu để tính toán tương quan.")
             return

        try:
            corr_matrix = np.corrcoef(data_matrix, rowvar=False) # Columns are variables
        except Exception as e:
            QMessageBox.critical(self, "Lỗi tính toán", f"Lỗi khi tính ma trận tương quan: {e}")
            logger.error(f"Lỗi np.corrcoef: {e}", exc_info=True)
            return


        self.correlation_table.setRowCount(len(stream_names))
        self.correlation_table.setColumnCount(len(stream_names))
        self.correlation_table.setHorizontalHeaderLabels(stream_names)
        self.correlation_table.setVerticalHeaderLabels(stream_names)

        for r in range(len(stream_names)):
            for c in range(len(stream_names)):
                self.correlation_table.setItem(r, c, QTableWidgetItem(f"{corr_matrix[r, c]:.4f}"))
        self.correlation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.correlation_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        if not np.isnan(corr_matrix).all() and not np.isinf(corr_matrix).all():
            self.correlation_heatmap.setImage(corr_matrix.T, autoLevels=True, autoRange=True)
            # TODO: Add axis labels to heatmap if possible (ImageView is limited)
        else:
            logger.warning("Ma trận tương quan chứa NaN hoặc Inf, không hiển thị heatmap.")


    def display_difference_plot(self):
        self.difference_plot_widget.clear()
        self.difference_plot_widget.addLegend(offset=(-10,10))

        stream_a_id = self.stream_a_combo.currentData()
        stream_b_id = self.stream_b_combo.currentData()

        if not stream_a_id or not stream_b_id:
            QMessageBox.warning(self, "Chọn Stream", "Vui lòng chọn Stream A và Stream B cho đồ thị chênh lệch.")
            return

        # Extract sensor_id and field_key from the unique_stream_id (e.g., "SensorAlpha_123_AccX")
        def parse_stream_id(unique_id):
            parts = unique_id.split('_')
            sensor_id = "_".join(parts[:-1])
            field_key = parts[-1]
            # Find the display name from self.get_selected_streams() for better matching
            # This is a bit complex here, simpler to just use unique_id as name for now.
            all_selected = self.get_selected_streams()
            for s_info in all_selected:
                if f"{s_info['id']}_{s_info['key']}" == unique_id:
                    return s_info['name']
            return unique_id # Fallback

        stream_a_name = parse_stream_id(stream_a_id)
        stream_b_name = parse_stream_id(stream_b_id)

        data_a = self.current_analysis_data.get('streams', {}).get(stream_a_name)
        data_b = self.current_analysis_data.get('streams', {}).get(stream_b_name)
        time_vector = self.current_analysis_data.get('common_time_vector')

        if data_a is None or data_b is None:
            QMessageBox.warning(self, "Lỗi Dữ liệu", f"Không tìm thấy dữ liệu cho một hoặc cả hai stream: {stream_a_name}, {stream_b_name}")
            return
        
        if len(data_a) != len(data_b):
            QMessageBox.warning(self, "Lỗi Dữ liệu", "Độ dài dữ liệu của Stream A và Stream B không khớp.")
            return
            
        if time_vector is None or len(time_vector) != len(data_a):
            logger.warning("Vector thời gian không khớp hoặc không tồn tại cho difference plot. Sử dụng chỉ số mẫu.")
            time_data_for_plot = np.arange(len(data_a))
            self.difference_plot_widget.setLabel('bottom', 'Chỉ số Mẫu')
        else:
            time_data_for_plot = time_vector
            self.difference_plot_widget.setLabel('bottom', 'Thời gian (s)')

        difference = data_a - data_b
        self.difference_plot_widget.plot(time_data_for_plot, difference, pen='r', name=f"{stream_a_name} - {stream_b_name}")
        self.difference_plot_widget.setTitle(f"Chênh lệch: {stream_a_name} và {stream_b_name}")


    def handle_sensor_list_or_status_changed(self):
        """Called by MainWindow when sensor list or their statuses change."""
        self.update_sensor_list()
        self.update_difference_plot_combos() # Selections might become invalid