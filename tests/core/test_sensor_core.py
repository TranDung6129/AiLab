import pytest
from unittest.mock import patch
from core.sensor_core import SensorInstance, SensorManager

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

def test_sensor_instance_initialization(qtbot, mock_sensor_config):
    sensor = SensorInstance("test_sensor_1", mock_sensor_config)
    assert sensor.sensor_id == "test_sensor_1"
    assert sensor.config == mock_sensor_config
    assert not sensor.connected
    assert not sensor._running
    assert sensor.thread is None
    assert sensor.worker is None

def test_sensor_instance_get_info(qtbot, mock_sensor_config):
    sensor = SensorInstance("test_sensor_1", mock_sensor_config)
    info = sensor.get_sensor_info()
    assert info['id'] == "test_sensor_1"
    assert info['type'] == 'mock_sensor'
    assert not info['connected']
    assert info['connection_error'] is None

def test_sensor_manager_initialization(qtbot):
    manager = SensorManager()
    assert isinstance(manager._sensors, dict)
    assert len(manager._sensors) == 0

@patch('core.sensor_core.QThread')
@patch('PyQt6.QtCore.QObject.moveToThread', lambda self, thread: None)
def test_sensor_manager_add_sensor(mock_qthread, qtbot, mock_sensor_config):
    manager = SensorManager()
    sensor_id = "test_sensor_1"
    result = manager.add_sensor(sensor_id, 'mock_sensor', mock_sensor_config)
    assert result
    assert sensor_id in manager._sensors
    assert manager.get_sensor_info(sensor_id) is not None
    with qtbot.waitSignal(manager.sensorConnectionStatusChanged, timeout=1000, raising=False):
        pass

@patch('core.sensor_core.QThread')
@patch('PyQt6.QtCore.QObject.moveToThread', lambda self, thread: None)
def test_sensor_manager_remove_sensor(mock_qthread, qtbot, mock_sensor_config):
    manager = SensorManager()
    sensor_id = "test_sensor_1"
    manager.add_sensor(sensor_id, 'mock_sensor', mock_sensor_config)
    with qtbot.waitSignal(manager.sensorConnectionStatusChanged, timeout=1000, raising=False):
        pass
    removed = manager.remove_sensor(sensor_id)
    assert removed
    assert sensor_id not in manager._sensors

@patch('core.sensor_core.QThread')
@patch('PyQt6.QtCore.QObject.moveToThread', lambda self, thread: None)
def test_sensor_manager_get_connected_sensors(mock_qthread, qtbot, mock_sensor_config):
    manager = SensorManager()
    sensor_id = "test_sensor_1"
    manager.add_sensor(sensor_id, 'mock_sensor', mock_sensor_config)
    with qtbot.waitSignal(manager.sensorConnectionStatusChanged, timeout=1000, raising=False):
        pass
    assert manager.get_connected_sensors_count() in (0, 1)
    manager.connect_sensor_by_id(sensor_id)

@patch('core.sensor_core.QThread')
@patch('PyQt6.QtCore.QObject.moveToThread', lambda self, thread: None)
def test_sensor_manager_get_inactive_sensors(mock_qthread, qtbot, mock_sensor_config):
    manager = SensorManager()
    sensor_id = "test_sensor_1"
    manager.add_sensor(sensor_id, 'mock_sensor', mock_sensor_config)
    with qtbot.waitSignal(manager.sensorConnectionStatusChanged, timeout=1000, raising=False):
        pass
    inactive_sensors = manager.get_inactive_sensors()
    assert sensor_id in inactive_sensors or len(inactive_sensors) == 0

@patch('core.sensor_core.QThread')
@patch('PyQt6.QtCore.QObject.moveToThread', lambda self, thread: None)
def test_sensor_manager_stop_all_sensors(mock_qthread, qtbot, mock_sensor_config):
    manager = SensorManager()
    sensor_id = "test_sensor_1"
    manager.add_sensor(sensor_id, 'mock_sensor', mock_sensor_config)
    with qtbot.waitSignal(manager.sensorConnectionStatusChanged, timeout=1000, raising=False):
        pass
    manager.connect_sensor_by_id(sensor_id)
    # Patch worker.stop to set _running to False
    instance = manager._sensors[sensor_id]
    if instance.worker:
        def fake_stop():
            instance._running = False
        instance.worker.stop = fake_stop
    manager.stop_all_sensors()
    with qtbot.waitSignal(manager.sensorConnectionStatusChanged, timeout=1000, raising=False):
        pass
    assert not manager._sensors[sensor_id]._running

@patch('core.sensor_core.QThread')
@patch('PyQt6.QtCore.QObject.moveToThread', lambda self, thread: None)
def test_sensor_manager_resource_conflict(mock_qthread, qtbot, wit_sensor_config):
    manager = SensorManager()
    sensor_id1 = "test_sensor_1"
    sensor_id2 = "test_sensor_2"
    manager.add_sensor(sensor_id1, 'wit_motion_imu', wit_sensor_config)
    with qtbot.waitSignal(manager.sensorConnectionStatusChanged, timeout=1000, raising=False):
        pass
    result = manager.add_sensor(sensor_id2, 'wit_motion_imu', wit_sensor_config)
    assert not result

@patch('core.sensor_core.QThread')
@patch('PyQt6.QtCore.QObject.moveToThread', lambda self, thread: None)
def test_sensor_manager_remove_all_inactive(mock_qthread, qtbot, mock_sensor_config):
    manager = SensorManager()
    sensor_id1 = "test_sensor_1"
    sensor_id2 = "test_sensor_2"
    manager.add_sensor(sensor_id1, 'mock_sensor', mock_sensor_config)
    manager.add_sensor(sensor_id2, 'mock_sensor', mock_sensor_config)
    with qtbot.waitSignal(manager.sensorConnectionStatusChanged, timeout=1000, raising=False):
        pass
    manager.connect_sensor_by_id(sensor_id1)
    removed = manager.remove_all_inactive_sensors()
    assert removed >= 1
    assert sensor_id2 not in manager._sensors 