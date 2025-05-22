import pytest
import numpy as np
from PyQt6.QtCore import QTimer
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
def plot_manager(mock_display_screen, mock_data_processor):
    return PlotManager(mock_display_screen, mock_data_processor)

def test_plot_manager_initialization(plot_manager):
    """Test PlotManager initialization"""
    assert plot_manager.display_screen is not None
    assert plot_manager.data_processor is not None
    assert isinstance(plot_manager.plot_update_timer, QTimer)
    assert not plot_manager.is_collecting_data
    assert plot_manager.current_sensor_id_plotting is None
    assert plot_manager._target_plot_rate_hz == 10

def test_set_plot_rate(plot_manager):
    """Test setting plot rate"""
    new_rate = 20
    plot_manager.set_plot_rate(new_rate)
    assert plot_manager._target_plot_rate_hz == new_rate

def test_start_plotting(plot_manager):
    """Test starting plotting"""
    sensor_id = "test_sensor"
    rate_hz = 20
    
    plot_manager.start_plotting(rate_hz, sensor_id)
    
    assert plot_manager.current_sensor_id_plotting == sensor_id
    assert plot_manager._target_plot_rate_hz == rate_hz
    assert plot_manager.is_collecting_data
    # Do not check QTimer.isActive() in headless test

def test_stop_plotting(plot_manager):
    """Test stopping plotting"""
    sensor_id = "test_sensor"
    plot_manager.start_plotting(10, sensor_id)
    plot_manager.stop_plotting()
    
    assert not plot_manager.is_collecting_data
    assert plot_manager.current_sensor_id_plotting == sensor_id  # Should not reset sensor_id

def test_update_plots(plot_manager, mock_display_screen, mock_data_processor):
    """Test updating plots"""
    sensor_id = "test_sensor"
    plot_manager.start_plotting(10, sensor_id)
    
    # Simulate timer timeout
    plot_manager.update_plots()
    
    assert mock_data_processor.get_plot_data_called
    assert mock_display_screen.update_plots_called
    assert (mock_display_screen.last_plot_data['time_data'] == mock_data_processor.test_data['time_data']).all()

def test_reset_plots(plot_manager, mock_display_screen, mock_data_processor):
    """Test resetting plots"""
    sensor_id = "test_sensor"
    plot_manager.current_sensor_id_plotting = sensor_id
    
    plot_manager.reset_plots()
    
    assert mock_data_processor.reset_called
    assert mock_display_screen.reset_plots_called

def test_invalid_plot_rate(plot_manager):
    """Test handling invalid plot rate"""
    sensor_id = "test_sensor"
    plot_manager.start_plotting(0, sensor_id)  # Invalid rate
    # is_collecting_data may be True, but timer should not be active
    assert not plot_manager.plot_update_timer.isActive()

def test_start_plotting_without_sensor_id(plot_manager):
    """Test starting plotting without sensor ID"""
    plot_manager.start_plotting(10, None)
    
    assert not plot_manager.is_collecting_data
    # Do not check QTimer.isActive() in headless test

def test_update_plots_without_data(plot_manager, mock_display_screen, mock_data_processor):
    """Test updating plots when no data is available"""
    sensor_id = "test_sensor"
    plot_manager.start_plotting(10, sensor_id)
    
    # Set empty data
    mock_data_processor.test_data['time_data'] = np.array([])
    
    # Simulate timer timeout
    plot_manager.update_plots()
    
    assert mock_data_processor.get_plot_data_called
    assert not mock_display_screen.update_plots_called  # Should not update with empty data 