import numpy as np
from scipy.signal import butter, sosfilt, sosfreqz
import logging

logger = logging.getLogger(__name__)

class Filter:
    """Base class for all filters."""
    def __init__(self, cutoff_freq, fs, order=2):
        """
        Initialize the filter.
        
        Args:
            cutoff_freq (float): Cutoff frequency in Hz
            fs (float): Sampling frequency in Hz
            order (int): Filter order
        """
        self.cutoff_freq = cutoff_freq
        self.fs = fs
        self.order = order
        self.nyq = 0.5 * fs
        self.normal_cutoff = cutoff_freq / self.nyq
        
        if self.normal_cutoff >= 1.0:
            logger.warning(f"Cutoff frequency {cutoff_freq}Hz is >= Nyquist frequency {self.nyq}Hz. Filter will be bypassed.")
        if self.normal_cutoff <= 0.0:
            logger.warning(f"Cutoff frequency {cutoff_freq}Hz is <= 0Hz. Filter will be bypassed.")

    def apply(self, data):
        """Apply the filter to the input data."""
        raise NotImplementedError("Subclasses must implement apply()")

class HighPassFilter(Filter):
    """High-pass filter implementation using Butterworth filter."""
    def apply(self, data):
        if self.normal_cutoff >= 1.0 or self.normal_cutoff <= 0.0:
            return data
            
        sos = butter(self.order, self.normal_cutoff, btype='high', analog=False, output='sos')
        return sosfilt(sos, data)

class LowPassFilter(Filter):
    """Low-pass filter implementation using Butterworth filter."""
    def apply(self, data):
        if self.normal_cutoff >= 1.0 or self.normal_cutoff <= 0.0:
            return data
            
        sos = butter(self.order, self.normal_cutoff, btype='low', analog=False, output='sos')
        return sosfilt(sos, data)

def create_filter(filter_type, cutoff_freq, fs, order=2):
    """
    Factory function to create a filter instance.
    
    Args:
        filter_type (str): Type of filter ("High-pass" or "Low-pass")
        cutoff_freq (float): Cutoff frequency in Hz
        fs (float): Sampling frequency in Hz
        order (int): Filter order
        
    Returns:
        Filter: An instance of the specified filter type
    """
    if filter_type == "High-pass":
        return HighPassFilter(cutoff_freq, fs, order)
    elif filter_type == "Low-pass":
        return LowPassFilter(cutoff_freq, fs, order)
    else:
        raise ValueError(f"Unknown filter type: {filter_type}") 