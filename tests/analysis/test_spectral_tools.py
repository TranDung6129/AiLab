import pytest
import numpy as np
from analysis.spectral_tools import (
    calculate_fft,
    find_dominant_frequency
)

@pytest.fixture
def test_signal():
    # Create a test signal with known frequency components
    t = np.linspace(0, 1, 1000)
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)
    return signal, t[1] - t[0]  # Return signal and dt

def test_calculate_fft(test_signal):
    """Test FFT calculation"""
    signal, dt = test_signal
    n_fft = 256
    
    # Calculate FFT
    freq_array, amplitude_spectrum = calculate_fft(signal, dt, n_fft)
    
    # Check output structure
    assert isinstance(freq_array, np.ndarray)
    assert isinstance(amplitude_spectrum, np.ndarray)
    assert len(freq_array) == len(amplitude_spectrum)
    assert len(freq_array) == n_fft // 2 + 1
    
    # Test with different window types
    freq_hann, amp_hann = calculate_fft(signal, dt, n_fft, window_type='Hann')
    freq_hamming, amp_hamming = calculate_fft(signal, dt, n_fft, window_type='Hamming')
    freq_blackman, amp_blackman = calculate_fft(signal, dt, n_fft, window_type='Blackman')
    freq_rect, amp_rect = calculate_fft(signal, dt, n_fft, window_type='Rectangular')
    
    # Check that all window types produce valid results
    assert len(freq_hann) == len(freq_hamming) == len(freq_blackman) == len(freq_rect)
    assert len(amp_hann) == len(amp_hamming) == len(amp_blackman) == len(amp_rect)
    
    # Test with invalid window type
    with pytest.raises(ValueError):
        calculate_fft(signal, dt, n_fft, window_type='Invalid')

def test_find_dominant_frequency(test_signal):
    """Test dominant frequency detection"""
    signal, dt = test_signal
    n_fft = 256
    
    # Calculate FFT
    freq_array, amplitude_spectrum = calculate_fft(signal, dt, n_fft)
    
    # Find dominant frequency
    dominant_freq = find_dominant_frequency(freq_array, amplitude_spectrum)
    
    # Check that dominant frequency is found
    assert dominant_freq is not None
    assert 9.5 <= dominant_freq <= 20.5  # Should be close to either 10 Hz or 20 Hz
    
    # Test with different minimum frequencies
    freq_high = find_dominant_frequency(freq_array, amplitude_spectrum, min_freq=15.0)
    assert freq_high is not None
    assert 19.5 <= freq_high <= 20.5  # Should be close to 20 Hz
    
    # Test with empty arrays
    assert find_dominant_frequency(np.array([]), np.array([])) is None
    
    # Test with minimum frequency higher than all frequencies
    assert find_dominant_frequency(freq_array, amplitude_spectrum, min_freq=1000.0) is None

def test_edge_cases():
    """Test edge cases and error handling"""
    # Test with empty array
    empty_array = np.array([])
    freq_array, amp_spectrum = calculate_fft(empty_array, 0.001, 256)
    assert len(freq_array) == 0
    assert len(amp_spectrum) == 0
    
    # Test with array smaller than n_fft
    small_array = np.random.randn(100)
    freq_array, amp_spectrum = calculate_fft(small_array, 0.001, 256)
    assert len(freq_array) == 0
    assert len(amp_spectrum) == 0
    
    # Test with invalid parameters
    signal = np.random.randn(1000)
    with pytest.raises(ValueError):
        calculate_fft(signal, -0.001, 256)  # Negative dt
    with pytest.raises(ValueError):
        calculate_fft(signal, 0.001, 0)  # Zero n_fft
    
    # Test with NaN values
    nan_array = np.array([1.0, np.nan, 2.0])
    calculate_fft(nan_array, 0.001, 256)
    
    # Test with infinite values
    inf_array = np.array([1.0, np.inf, 2.0])
    calculate_fft(inf_array, 0.001, 256) 