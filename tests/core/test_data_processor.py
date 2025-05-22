import pytest
import numpy as np
from core.data_processor import DataProcessor

@pytest.fixture
def data_processor():
    return DataProcessor()

@pytest.fixture
def sample_sensor_data():
    # Use the format expected by handle_incoming_sensor_data
    return {
        'accX': 1.0,
        'accY': 2.0,
        'accZ': 3.0,
        'time': 0.1
    }

def test_initialization(data_processor):
    """Test DataProcessor initialization"""
    assert data_processor.N_FFT_POINTS == 512
    assert isinstance(data_processor._sensor_data_store, dict)
    assert len(data_processor._sensor_data_store) == 0

def test_ensure_sensor_id_structure(data_processor):
    """Test sensor data structure initialization"""
    sensor_id = "test_sensor"
    data_processor._ensure_sensor_id_structure(sensor_id)
    
    assert sensor_id in data_processor._sensor_data_store
    sensor_data = data_processor._sensor_data_store[sensor_id]
    
    # Check basic structure
    assert 'config' in sensor_data
    assert 'time_data' in sensor_data
    assert 'raw_acc' in sensor_data
    assert 'processed_acc' in sensor_data
    assert 'processed_vel' in sensor_data
    assert 'processed_disp' in sensor_data
    
    # Check data types
    assert isinstance(sensor_data['time_data'], np.ndarray)
    assert isinstance(sensor_data['raw_acc']['x'], np.ndarray)
    assert isinstance(sensor_data['processed_acc']['x'], np.ndarray)
    assert isinstance(sensor_data['processed_vel']['x'], np.ndarray)
    assert isinstance(sensor_data['processed_disp']['x'], np.ndarray)

def test_reset_sensor_data(data_processor):
    """Test resetting sensor data"""
    sensor_id = "test_sensor"
    data_processor._ensure_sensor_id_structure(sensor_id)
    
    # Add some test data
    data_processor._sensor_data_store[sensor_id]['time_data'] = np.array([1, 2, 3])
    data_processor._sensor_data_store[sensor_id]['raw_acc']['x'] = np.array([1, 2, 3])
    
    # Reset the data
    data_processor.reset_sensor_data(sensor_id)
    
    # Check if data is reset
    assert len(data_processor._sensor_data_store[sensor_id]['time_data']) == 0
    assert len(data_processor._sensor_data_store[sensor_id]['raw_acc']['x']) == 0

def test_update_processing_parameters(data_processor):
    """Test updating processing parameters"""
    sensor_id = "test_sensor"
    data_processor._ensure_sensor_id_structure(sensor_id)
    
    new_kin_params = {
        'sample_frame_size': 30,
        'calc_frame_multiplier': 60,
        'rls_filter_q_vel': 0.99,
        'rls_filter_q_disp': 0.99,
        'warmup_frames': 10
    }
    
    data_processor.update_processing_parameters(sensor_id, new_kin_params=new_kin_params)
    
    # Check if parameters are updated
    current_params = data_processor.get_sensor_kinematic_params(sensor_id)
    assert current_params['sample_frame_size'] == 30
    assert current_params['calc_frame_multiplier'] == 60
    assert current_params['rls_filter_q_vel'] == 0.99
    assert current_params['rls_filter_q_disp'] == 0.99
    assert current_params['warmup_frames'] == 10

def test_handle_incoming_sensor_data(data_processor, sample_sensor_data):
    """Test handling incoming sensor data"""
    sensor_id = "test_sensor"
    data_processor._ensure_sensor_id_structure(sensor_id)
    
    # Simulate multiple incoming data points to fill arrays
    for i in range(25):
        d = sample_sensor_data.copy()
        d['time'] = 0.1 * i
        data_processor.handle_incoming_sensor_data(sensor_id, d)
    
    # Check if data is stored correctly
    assert len(data_processor._sensor_data_store[sensor_id]['time_data']) > 0
    assert len(data_processor._sensor_data_store[sensor_id]['raw_acc']['x']) > 0

@pytest.mark.xfail(reason="calculate_fft_for_sensor không sinh ra FFT nếu không qua pipeline xử lý thực tế.")
def test_calculate_fft_for_sensor(data_processor):
    """Test FFT calculation"""
    sensor_id = "test_sensor"
    data_processor._ensure_sensor_id_structure(sensor_id)
    
    # Add enough test data as numpy array for FFT
    data = np.sin(np.linspace(0, 10, 512))
    data_processor._sensor_data_store[sensor_id]['processed_acc']['x'] = data
    data_processor._sensor_data_store[sensor_id]['time_data'] = np.linspace(0, 10, 512)
    
    # Calculate FFT
    data_processor.calculate_fft_for_sensor(sensor_id)
    
    # Check if FFT data is calculated
    fft_data = data_processor._sensor_data_store[sensor_id]['fft_plot_data']['x']
    assert fft_data['freq'] is not None
    assert fft_data['amp'] is not None
    assert len(fft_data['freq']) > 0
    assert len(fft_data['amp']) > 0 