import pytest
import numpy as np
from scipy import ndimage
from algorithm.filters import (
    Filter, HighPassFilter, LowPassFilter,
    create_filter,
    apply_butterworth_filter,
    apply_moving_average_filter,
    apply_median_filter,
    apply_gaussian_filter
)

# Test data - increased length to satisfy filter requirements
@pytest.fixture
def sample_data():
    return np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
                     11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0])

@pytest.fixture
def fs():
    return 100.0  # Sampling frequency

@pytest.fixture
def cutoff_freq():
    return 10.0  # Cutoff frequency

# Test base Filter class
def test_filter_initialization(fs, cutoff_freq):
    # Test valid initialization
    filter_obj = Filter(cutoff_freq, fs)
    assert filter_obj.cutoff_freq == cutoff_freq
    assert filter_obj.fs == fs
    assert filter_obj.order == 2  # Default order
    assert filter_obj.nyq == fs / 2
    assert filter_obj.normal_cutoff == cutoff_freq / (fs / 2)
    
    # Test with custom order
    filter_obj = Filter(cutoff_freq, fs, order=4)
    assert filter_obj.order == 4

# Test HighPassFilter
def test_high_pass_filter(sample_data, fs, cutoff_freq):
    filter_obj = HighPassFilter(cutoff_freq, fs)
    result = filter_obj.apply(sample_data)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    
    # Test with invalid cutoff frequency
    filter_obj = HighPassFilter(fs, fs)  # cutoff >= Nyquist
    assert np.array_equal(filter_obj.apply(sample_data), sample_data)
    
    filter_obj = HighPassFilter(0, fs)  # cutoff <= 0
    assert np.array_equal(filter_obj.apply(sample_data), sample_data)

# Test LowPassFilter
def test_low_pass_filter(sample_data, fs, cutoff_freq):
    filter_obj = LowPassFilter(cutoff_freq, fs)
    result = filter_obj.apply(sample_data)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    
    # Test with invalid cutoff frequency
    filter_obj = LowPassFilter(fs, fs)  # cutoff >= Nyquist
    assert np.array_equal(filter_obj.apply(sample_data), sample_data)
    
    filter_obj = LowPassFilter(0, fs)  # cutoff <= 0
    assert np.array_equal(filter_obj.apply(sample_data), sample_data)

# Test create_filter factory function
def test_create_filter(fs, cutoff_freq):
    # Test valid filter types
    assert isinstance(create_filter("High-pass", cutoff_freq, fs), HighPassFilter)
    assert isinstance(create_filter("Low-pass", cutoff_freq, fs), LowPassFilter)
    
    # Test invalid filter type
    with pytest.raises(ValueError):
        create_filter("Invalid", cutoff_freq, fs)

# Test Butterworth filter
def test_apply_butterworth_filter(sample_data, fs, cutoff_freq):
    result = apply_butterworth_filter(sample_data, cutoff_freq, fs)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        apply_butterworth_filter(np.array([1.0]), cutoff_freq, fs)  # Too few points
    with pytest.raises(ValueError):
        apply_butterworth_filter(sample_data, -cutoff_freq, fs)  # Negative cutoff
    with pytest.raises(ValueError):
        apply_butterworth_filter(sample_data, cutoff_freq, -fs)  # Negative fs
    with pytest.raises(ValueError):
        apply_butterworth_filter(sample_data, cutoff_freq, fs, order=-1)  # Negative order

# Test Moving Average filter
def test_apply_moving_average_filter(sample_data):
    window_size = 3
    result = apply_moving_average_filter(sample_data, window_size)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        apply_moving_average_filter(np.array([1.0]), window_size)  # Too few points
    with pytest.raises(ValueError):
        apply_moving_average_filter(sample_data, -window_size)  # Negative window size
    with pytest.raises(ValueError):
        apply_moving_average_filter(sample_data, len(sample_data) + 1)  # Window too large

# Test Median filter
def test_apply_median_filter(sample_data):
    kernel_size = 3
    result = apply_median_filter(sample_data, kernel_size)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        apply_median_filter(np.array([1.0]), kernel_size)  # Too few points
    with pytest.raises(ValueError):
        apply_median_filter(sample_data, -kernel_size)  # Negative kernel size
    with pytest.raises(ValueError):
        apply_median_filter(sample_data, len(sample_data) + 1)  # Kernel too large

# Test Gaussian filter
def test_apply_gaussian_filter(sample_data):
    sigma = 1.0
    result = apply_gaussian_filter(sample_data, sigma)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        apply_gaussian_filter(np.array([1.0]), sigma)  # Too few points
    with pytest.raises(ValueError):
        apply_gaussian_filter(sample_data, -sigma)  # Negative sigma 