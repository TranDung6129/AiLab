import pytest
import numpy as np
from analysis.anomaly_detection_tools import (
    detect_outliers_zscore,
    detect_anomalies_moving_average,
    detect_sudden_changes
)

@pytest.fixture
def normal_data():
    # Create normal data with some anomalies
    t = np.linspace(0, 1, 1000)
    signal = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(1000)
    # Add some anomalies
    signal[100] = 5.0  # Point anomaly
    signal[200:210] = 3.0  # Collective anomaly
    return signal

def test_detect_outliers_zscore(normal_data):
    """Test Z-score based outlier detection"""
    # Detect outliers
    outlier_indices, outlier_values = detect_outliers_zscore(normal_data, threshold=3.0)
    
    # Check output structure
    assert isinstance(outlier_indices, np.ndarray)
    assert isinstance(outlier_values, np.ndarray)
    assert len(outlier_indices) == len(outlier_values)
    
    # Check that known anomalies are detected
    assert 100 in outlier_indices  # Point anomaly
    assert np.any(np.isin(np.arange(200, 211), outlier_indices))  # Collective anomaly
    
    # Test with different thresholds
    indices_loose, values_loose = detect_outliers_zscore(normal_data, threshold=2.0)
    indices_strict, values_strict = detect_outliers_zscore(normal_data, threshold=4.0)
    assert len(indices_loose) >= len(outlier_indices) >= len(indices_strict)
    
    # Test with constant signal
    constant_signal = np.ones(100)
    indices, values = detect_outliers_zscore(constant_signal, threshold=3.0)
    assert len(indices) == 0
    assert len(values) == 0

def test_detect_anomalies_moving_average(normal_data):
    """Test moving average based anomaly detection"""
    # Detect anomalies
    anomaly_indices, anomaly_values = detect_anomalies_moving_average(normal_data, window_size=20, threshold=2.0)
    
    # Check output structure
    assert isinstance(anomaly_indices, np.ndarray)
    assert isinstance(anomaly_values, np.ndarray)
    assert len(anomaly_indices) == len(anomaly_values)
    
    # Check that known anomalies are detected
    assert 100 in anomaly_indices  # Point anomaly
    assert np.any(np.isin(np.arange(200, 211), anomaly_indices))  # Collective anomaly
    
    # Test with different window sizes
    indices_small, values_small = detect_anomalies_moving_average(normal_data, window_size=10, threshold=2.0)
    indices_large, values_large = detect_anomalies_moving_average(normal_data, window_size=50, threshold=2.0)
    
    # Test with different thresholds
    indices_loose, values_loose = detect_anomalies_moving_average(normal_data, window_size=20, threshold=1.0)
    indices_strict, values_strict = detect_anomalies_moving_average(normal_data, window_size=20, threshold=3.0)
    assert len(indices_loose) >= len(anomaly_indices) >= len(indices_strict)

def test_detect_sudden_changes(normal_data):
    """Test sudden change detection"""
    # Detect changes
    change_indices, change_magnitudes = detect_sudden_changes(normal_data, threshold=2.0)
    
    # Check output structure
    assert isinstance(change_indices, np.ndarray)
    assert isinstance(change_magnitudes, np.ndarray)
    assert len(change_indices) == len(change_magnitudes)
    
    # Test with different thresholds
    indices_loose, magnitudes_loose = detect_sudden_changes(normal_data, threshold=1.0)
    indices_strict, magnitudes_strict = detect_sudden_changes(normal_data, threshold=3.0)
    assert len(indices_loose) >= len(change_indices) >= len(indices_strict)

def test_edge_cases():
    """Test edge cases and error handling"""
    # Test with empty array
    empty_array = np.array([])
    indices, values = detect_outliers_zscore(empty_array)
    assert len(indices) == 0
    assert len(values) == 0
    
    # Test with single value
    single_value = np.array([1.0])
    indices, values = detect_outliers_zscore(single_value)
    assert len(indices) == 0
    assert len(values) == 0
    
    # Test với tham số không hợp lệ
    signal = np.random.randn(100)
    with pytest.raises(ValueError):
        detect_anomalies_moving_average(signal, window_size=0, threshold=2.0)
    
    # Test với NaN values
    nan_array = np.array([1.0, np.nan, 2.0])
    detect_outliers_zscore(nan_array)
    
    # Test với infinite values
    inf_array = np.array([1.0, np.inf, 2.0])
    detect_outliers_zscore(inf_array) 