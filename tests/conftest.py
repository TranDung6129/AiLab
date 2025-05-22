import pytest
import numpy as np
from PyQt6.QtCore import QObject
from core.data_processor import DataProcessor
from core.sensor_core import SensorInstance, SensorManager
from core.plot_manager import PlotManager

class MockDisplayScreen:
    def __init__(self):
        self.update_plots_called = False
        self.reset_plots_called = False
        self.last_plot_data = None

    def update_plots(self, time_data, acc_data, vel_data, disp_data, fft_data, dominant_freqs):
        self.update_plots_called = True
        self.last_plot_data = {
            'time_data': time_data,
            'acc_data': acc_data,
            'vel_data': vel_data,
            'disp_data': disp_data,
            'fft_data': fft_data,
            'dominant_freqs': dominant_freqs
        }

    def reset_plots(self):
        self.reset_plots_called = True

class MockDataProcessor:
    def __init__(self):
        self.reset_called = False
        self.get_plot_data_called = False
        self.test_data = {
            'time_data': np.array([1, 2, 3]),
            'acc_data': {'x': np.array([1, 2, 3]), 'y': np.array([2, 3, 4]), 'z': np.array([3, 4, 5])},
            'vel_data': {'x': np.array([0.1, 0.2, 0.3]), 'y': np.array([0.2, 0.3, 0.4]), 'z': np.array([0.3, 0.4, 0.5])},
            'disp_data': {'x': np.array([0.01, 0.02, 0.03]), 'y': np.array([0.02, 0.03, 0.04]), 'z': np.array([0.03, 0.04, 0.05])},
            'fft_data': {'x': {'freq': np.array([1, 2, 3]), 'amp': np.array([0.1, 0.2, 0.3])}},
            'dominant_freqs': {'x': 1.0, 'y': 2.0, 'z': 3.0}
        }

    def get_plot_data_for_sensor(self, sensor_id):
        self.get_plot_data_called = True
        return self.test_data

    def reset_sensor_data(self, sensor_id):
        self.reset_called = True

@pytest.fixture
def mock_display_screen():
    return MockDisplayScreen()

@pytest.fixture
def mock_data_processor():
    return MockDataProcessor()

@pytest.fixture
def data_processor():
    return DataProcessor()

@pytest.fixture
def mock_sensor_config():
    return {
        'name': 'Test Sensor',
        'type': 'mock_sensor',
        'protocol': 'Mock',
        'port': 'COM1',
        'baudrate': 115200
    }

@pytest.fixture
def wit_sensor_config():
    return {
        'name': 'WIT Sensor',
        'type': 'wit_motion_imu',
        'protocol': 'UART',
        'port': 'COM2',
        'baudrate': 115200
    }

@pytest.fixture
def sensor_instance(mock_sensor_config):
    return SensorInstance("test_sensor_1", mock_sensor_config)

@pytest.fixture
def sensor_manager():
    return SensorManager()

@pytest.fixture
def plot_manager(mock_display_screen, mock_data_processor):
    return PlotManager(mock_display_screen, mock_data_processor)

@pytest.fixture
def sample_sensor_data():
    return {
        'accX': 1.0,
        'accY': 2.0,
        'accZ': 3.0,
        'time': 0.1
    } 