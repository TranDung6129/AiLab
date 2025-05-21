import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.signal import windows
import logging
from PyQt6.QtCore import QObject
from algorithm.kinematic_processor import KinematicProcessor #

logger = logging.getLogger(__name__)

class DataProcessor(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.N_FFT_POINTS = 512
        self._sensor_data_store = {}
        self.default_kinematic_params = {
            'sample_frame_size': 20,
            'calc_frame_multiplier': 50,
            'rls_filter_q_vel': 0.9875,
            'rls_filter_q_disp': 0.9875,
            'warmup_frames': 5
        }
        self.reset_all_data()

    def _ensure_sensor_id_structure(self, sensor_id, sensor_type="wit_motion_imu", dt=0.005,
                                   kin_params=None):
        if sensor_id not in self._sensor_data_store:
            logger.info(f"DataProcessor: Initializing data structure for sensor_id: {sensor_id}")
            
            current_kin_params = kin_params if kin_params else self.default_kinematic_params.copy()
            # Ensure all required keys are present in current_kin_params, falling back to default if not
            for key, default_val in self.default_kinematic_params.items():
                if key not in current_kin_params:
                    current_kin_params[key] = default_val
            
            self._sensor_data_store[sensor_id] = {
                'config': {
                    'type': sensor_type, 
                    'dt': dt,
                    # Store the actual kinematic params used for this sensor
                    'kinematic_params': current_kin_params.copy() 
                },
                'time_data': np.array([]),
                'raw_acc': {'x': np.array([]), 'y': np.array([]), 'z': np.array([])},
                'processed_acc': {'x': np.array([]), 'y': np.array([]), 'z': np.array([])},
                'processed_vel': {'x': np.array([]), 'y': np.array([]), 'z': np.array([])},
                'processed_disp': {'x': np.array([]), 'y': np.array([]), 'z': np.array([])},
                'current_time_plot': 0.0,
                'acc_input_buffers': {'x': [], 'y': [], 'z': []},
                'kinematic_processors': {
                    axis: KinematicProcessor(
                        dt=dt,
                        sample_frame_size=current_kin_params['sample_frame_size'],
                        calc_frame_multiplier=current_kin_params['calc_frame_multiplier'],
                        rls_filter_q_vel=current_kin_params['rls_filter_q_vel'],
                        rls_filter_q_disp=current_kin_params['rls_filter_q_disp'],
                        warmup_frames=current_kin_params['warmup_frames']
                    ) for axis in ['x', 'y', 'z']
                },
                'fft_plot_data': {ax: {'freq': None, 'amp': None} for ax in ['x', 'y', 'z']},
                'dominant_freqs': {'x': 0, 'y': 0, 'z': 0}
            }
        else: # Sensor structure already exists, check if dt or kin_params need update
            sds_config = self._sensor_data_store[sensor_id]['config']
            config_changed = False
            if sds_config['dt'] != dt:
                sds_config['dt'] = dt
                config_changed = True
            
            if kin_params and sds_config.get('kinematic_params') != kin_params:
                sds_config['kinematic_params'] = kin_params.copy()
                config_changed = True

            if config_changed:
                logger.info(f"DataProcessor: Re-initializing KinematicProcessors for {sensor_id} due to config change.")
                current_kin_params_for_reinit = sds_config['kinematic_params']
                for axis in ['x', 'y', 'z']:
                    self._sensor_data_store[sensor_id]['kinematic_processors'][axis] = KinematicProcessor(
                        dt=sds_config['dt'],
                        sample_frame_size=current_kin_params_for_reinit['sample_frame_size'],
                        calc_frame_multiplier=current_kin_params_for_reinit['calc_frame_multiplier'],
                        rls_filter_q_vel=current_kin_params_for_reinit['rls_filter_q_vel'],
                        rls_filter_q_disp=current_kin_params_for_reinit['rls_filter_q_disp'],
                        warmup_frames=current_kin_params_for_reinit['warmup_frames']
                    )

    def update_kinematic_parameters(self, sensor_id, new_kin_params):
        if sensor_id in self._sensor_data_store:
            sds = self._sensor_data_store[sensor_id]
            sds['config']['kinematic_params'] = new_kin_params.copy() # Update stored params
            
            # Re-initialize KinematicProcessors with new parameters
            logger.info(f"DataProcessor: Updating kinematic parameters for sensor {sensor_id}.")
            for axis in ['x', 'y', 'z']:
                sds['kinematic_processors'][axis] = KinematicProcessor(
                    dt=sds['config']['dt'], # Use existing dt
                    sample_frame_size=new_kin_params['sample_frame_size'],
                    calc_frame_multiplier=new_kin_params['calc_frame_multiplier'],
                    rls_filter_q_vel=new_kin_params['rls_filter_q_vel'],
                    rls_filter_q_disp=new_kin_params['rls_filter_q_disp'],
                    warmup_frames=new_kin_params['warmup_frames']
                )
            # Reset data arrays as processing will restart with new parameters
            self.reset_sensor_data_arrays_only(sensor_id)
            logger.info(f"Kinematic parameters updated and data reset for {sensor_id}.")
        else:
            logger.warning(f"Cannot update kinematic parameters. Sensor ID {sensor_id} not found.")

    def get_sensor_kinematic_params(self, sensor_id):
        if sensor_id in self._sensor_data_store:
            return self._sensor_data_store[sensor_id]['config'].get('kinematic_params')
        return None

    def reset_sensor_data_arrays_only(self, sensor_id):
        """Resets only the data arrays, not the entire structure or processors, for a sensor."""
        if sensor_id in self._sensor_data_store:
            sds = self._sensor_data_store[sensor_id]
            sds['time_data'] = np.array([])
            for dtype in ['raw_acc', 'processed_acc', 'processed_vel', 'processed_disp']:
                for axis in ['x', 'y', 'z']:
                    if dtype in sds and axis in sds[dtype]:
                         sds[dtype][axis] = np.array([])
            sds['current_time_plot'] = 0.0
            sds['acc_input_buffers'] = {'x': [], 'y': [], 'z': []}
            sds['fft_plot_data'] = {ax: {'freq': None, 'amp': None} for ax in ['x', 'y', 'z']}
            sds['dominant_freqs'] = {'x': 0, 'y': 0, 'z': 0}
            # Also reset state of kinematic processors
            for kp_axis in sds['kinematic_processors'].values():
                kp_axis.reset() #
            logger.info(f"Data arrays and processor states reset for sensor {sensor_id}.")


    def reset_sensor_data(self, sensor_id):
        if sensor_id in self._sensor_data_store:
            # Retrieve original config before full reset by _ensure_sensor_id_structure
            original_config = self._sensor_data_store[sensor_id]['config'].copy()
            dt = original_config['dt']
            sensor_type = original_config['type']
            kin_params = original_config.get('kinematic_params', self.default_kinematic_params.copy())

            # This will effectively reset by re-initializing if it exists
            self._ensure_sensor_id_structure(sensor_id, sensor_type, dt, kin_params)
            
            # Explicitly reset data arrays after re-initialization of structure and processors
            self.reset_sensor_data_arrays_only(sensor_id)
            logger.info(f"Full data and structure for sensor {sensor_id} has been reset.")
        else:
            logger.warning(f"Cannot reset data for unknown sensor_id: {sensor_id}")

    def reset_all_data(self):
        for sensor_id in list(self._sensor_data_store.keys()):
            self.reset_sensor_data(sensor_id)
        logger.info("All sensor data structures have been reset in DataProcessor.")


    def remove_sensor_data(self, sensor_id):
        if sensor_id in self._sensor_data_store:
            del self._sensor_data_store[sensor_id]
            logger.info(f"Data structure for sensor {sensor_id} removed from DataProcessor.")
        else:
            logger.warning(f"Cannot remove data for unknown sensor_id: {sensor_id}")


    def handle_incoming_sensor_data(self, sensor_id, sensor_data_dict, sensor_config_from_manager=None):
        _dt = 0.005 
        _sensor_type = "unknown"
        # Default kinematic params; will be overridden if sensor already exists with custom params
        _kin_params = self.default_kinematic_params.copy()


        if sensor_config_from_manager:
            _sensor_type = sensor_config_from_manager.get('type', 'unknown')
            # Determine dt based on sensor type and its config
            if _sensor_type == "wit_motion_imu":
                hex_val = sensor_config_from_manager.get('wit_data_rate_byte_hex', "0b").lower().replace("0x","")
                rate_map_to_dt = {"0b": 0.005, "19": 0.01, "14": 0.02, "0a": 0.05, "05": 0.1}
                _dt = rate_map_to_dt.get(hex_val, 0.01)
            elif _sensor_type == "mock_sensor":
                 _dt = sensor_config_from_manager.get('mock_update_interval', 0.1)
            
            # If sensor already exists, use its stored kinematic params, otherwise use defaults
            if sensor_id in self._sensor_data_store:
                _kin_params = self._sensor_data_store[sensor_id]['config'].get('kinematic_params', _kin_params)

        self._ensure_sensor_id_structure(sensor_id, _sensor_type, _dt, _kin_params)
        sds = self._sensor_data_store[sensor_id]

        if not sensor_data_dict: return

        try:
            accX = sensor_data_dict.get("accX")
            accY = sensor_data_dict.get("accY")
            accZ = sensor_data_dict.get("accZ")

            if accX is None or accY is None or accZ is None: return

            g_conversion = 9.80665
            accX_ms2 = accX * g_conversion
            accY_ms2 = accY * g_conversion
            accZ_ms2 = (accZ - 1.0) * g_conversion if sds['config']['type'] == "wit_motion_imu" else accZ * g_conversion

            fft_buffer_size = self.N_FFT_POINTS * 2 
            sds['raw_acc']['x'] = np.append(sds['raw_acc']['x'], accX_ms2)[-fft_buffer_size:]
            sds['raw_acc']['y'] = np.append(sds['raw_acc']['y'], accY_ms2)[-fft_buffer_size:]
            sds['raw_acc']['z'] = np.append(sds['raw_acc']['z'], accZ_ms2)[-fft_buffer_size:]

            sds['acc_input_buffers']['x'].append(accX_ms2)
            sds['acc_input_buffers']['y'].append(accY_ms2)
            sds['acc_input_buffers']['z'].append(accZ_ms2)
            
            # Use sample_frame_size from the sensor's specific kinematic_params
            current_frame_size = sds['config']['kinematic_params']['sample_frame_size']

            if len(sds['acc_input_buffers']['x']) >= current_frame_size:
                frames = {}
                for axis in ['x', 'y', 'z']:
                    frames[axis] = np.array(sds['acc_input_buffers'][axis][:current_frame_size])
                    sds['acc_input_buffers'][axis] = sds['acc_input_buffers'][axis][current_frame_size:]

                disp_f, vel_f, acc_f_filtered = {}, {}, {}
                for axis in ['x', 'y', 'z']:
                    disp_f[axis], vel_f[axis], acc_f_filtered[axis] = \
                        sds['kinematic_processors'][axis].process_frame(frames[axis])

                num_samples_in_frame = len(acc_f_filtered['x'])
                dt_this_sensor = sds['config']['dt']
                new_times_segment = np.arange(
                    sds['current_time_plot'],
                    sds['current_time_plot'] + num_samples_in_frame * dt_this_sensor,
                    dt_this_sensor
                )[:num_samples_in_frame]

                if not new_times_segment.size: return

                sds['current_time_plot'] += num_samples_in_frame * dt_this_sensor
                sds['time_data'] = np.append(sds['time_data'], new_times_segment)

                for axis in ['x', 'y', 'z']:
                    sds['processed_acc'][axis] = np.append(sds['processed_acc'][axis], acc_f_filtered[axis])
                    sds['processed_vel'][axis] = np.append(sds['processed_vel'][axis], vel_f[axis])
                    sds['processed_disp'][axis] = np.append(sds['processed_disp'][axis], disp_f[axis])
                
                self._trim_data_arrays_for_sensor(sensor_id)

        except Exception as e:
            logger.error(f"Error processing data for sensor {sensor_id}: {e}", exc_info=True)

    def _trim_data_arrays_for_sensor(self, sensor_id, max_points=2000): # Max points for internal storage
        sds = self._sensor_data_store.get(sensor_id)
        if not sds: return

        data_arrays_to_trim_keys = [
            ('time_data', None),
            ('processed_acc', 'x'), ('processed_acc', 'y'), ('processed_acc', 'z'),
            ('processed_vel', 'x'), ('processed_vel', 'y'), ('processed_vel', 'z'),
            ('processed_disp', 'x'), ('processed_disp', 'y'), ('processed_disp', 'z'),
        ]
        
        current_min_len = -1

        for key1, key2 in data_arrays_to_trim_keys:
            target_array_container = sds.get(key1)
            if target_array_container is None: continue # Skip if top-level key doesn't exist

            arr = target_array_container if key2 is None else target_array_container.get(key2)
            
            if isinstance(arr, np.ndarray) and hasattr(arr, '__len__'):
                if current_min_len == -1 or len(arr) < current_min_len:
                    current_min_len = len(arr)
        
        if current_min_len == -1 or current_min_len <= max_points: return

        slice_start = current_min_len - max_points
        
        sds['time_data'] = sds['time_data'][slice_start:]
        for axis in ['x', 'y', 'z']:
            if axis in sds['processed_acc']: sds['processed_acc'][axis] = sds['processed_acc'][axis][slice_start:]
            if axis in sds['processed_vel']: sds['processed_vel'][axis] = sds['processed_vel'][axis][slice_start:]
            if axis in sds['processed_disp']: sds['processed_disp'][axis] = sds['processed_disp'][axis][slice_start:]


    def calculate_fft_for_sensor(self, sensor_id):
        sds = self._sensor_data_store.get(sensor_id)
        if not sds: return
        
        dt_sensor = sds['config']['dt']
        if dt_sensor <= 0: return

        new_dominant_freqs = {}
        for axis in ['x', 'y', 'z']:
            acc_data_axis = sds['raw_acc'][axis]
            if len(acc_data_axis) >= self.N_FFT_POINTS:
                segment_for_fft = acc_data_axis[-self.N_FFT_POINTS:]
                hanning_window = windows.hann(self.N_FFT_POINTS)
                segment_windowed = segment_for_fft * hanning_window

                yf = rfft(segment_windowed)
                xf = rfftfreq(self.N_FFT_POINTS, dt_sensor)
                
                if len(xf) > 1 and len(yf) > 1: 
                    amplitude_spectrum = np.abs(yf[1:])
                    freq_axis_fft = xf[1:]

                    if amplitude_spectrum.size > 0:
                        sds['fft_plot_data'][axis]['freq'] = freq_axis_fft
                        sds['fft_plot_data'][axis]['amp'] = amplitude_spectrum
                        min_freq_idx = np.where(freq_axis_fft >= 0.1)[0]
                        if min_freq_idx.size > 0:
                            start_idx = min_freq_idx[0]
                            if start_idx < len(amplitude_spectrum):
                                peak_idx = np.argmax(amplitude_spectrum[start_idx:]) + start_idx
                                dominant_freq = freq_axis_fft[peak_idx]
                                new_dominant_freqs[axis] = dominant_freq
                            else: 
                                new_dominant_freqs[axis] = 0
                                sds['fft_plot_data'][axis]['freq'] = None
                                sds['fft_plot_data'][axis]['amp'] = None
                        else: 
                            new_dominant_freqs[axis] = 0
                            sds['fft_plot_data'][axis]['freq'] = None
                            sds['fft_plot_data'][axis]['amp'] = None
                    else: 
                        new_dominant_freqs[axis] = 0
                        sds['fft_plot_data'][axis]['freq'] = None
                        sds['fft_plot_data'][axis]['amp'] = None
                else: 
                    new_dominant_freqs[axis] = 0
                    sds['fft_plot_data'][axis]['freq'] = None
                    sds['fft_plot_data'][axis]['amp'] = None
            else: 
                new_dominant_freqs[axis] = sds['dominant_freqs'].get(axis, 0)
        
        if new_dominant_freqs:
            sds['dominant_freqs'].update(new_dominant_freqs)

    def get_plot_data_for_sensor(self, sensor_id):
        sds = self._sensor_data_store.get(sensor_id)
        if not sds:
            empty_axis_data = {'x': np.array([]), 'y': np.array([]), 'z': np.array([])}
            empty_fft_axis_data = {'freq': None, 'amp': None}
            return { 
                'time_data': np.array([]),
                'acc_data': empty_axis_data.copy(),
                'vel_data': empty_axis_data.copy(),
                'disp_data': empty_axis_data.copy(),
                'fft_data': {'x': empty_fft_axis_data.copy(), 'y': empty_fft_axis_data.copy(), 'z': empty_fft_axis_data.copy()},
                'dominant_freqs': {'x': 0, 'y': 0, 'z': 0}
            }
        
        # Ensure all data components exist, even if empty, to prevent KeyErrors higher up
        acc_data = sds.get('processed_acc', {'x': np.array([]), 'y': np.array([]), 'z': np.array([])})
        vel_data = sds.get('processed_vel', {'x': np.array([]), 'y': np.array([]), 'z': np.array([])})
        disp_data = sds.get('processed_disp', {'x': np.array([]), 'y': np.array([]), 'z': np.array([])})
        fft_data = sds.get('fft_plot_data', {'x': {'freq': None, 'amp': None}, 
                                             'y': {'freq': None, 'amp': None}, 
                                             'z': {'freq': None, 'amp': None}})
        
        return {
            'time_data': sds.get('time_data', np.array([])),
            'acc_data': acc_data,
            'vel_data': vel_data,
            'disp_data': disp_data,
            'fft_data': fft_data,
            'dominant_freqs': sds.get('dominant_freqs', {'x': 0, 'y': 0, 'z': 0})
        }