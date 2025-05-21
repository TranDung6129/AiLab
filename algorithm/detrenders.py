import numpy as np
import logging

logger = logging.getLogger(__name__)

class Detrender:
    """Base class for all detrenders."""
    def __init__(self, params=None):
        """
        Initialize the detrender.
        
        Args:
            params (dict): Parameters specific to the detrending method
        """
        self.params = params or {}

    def detrend(self, data, time_vector):
        """
        Remove trend from the data.
        
        Args:
            data (np.ndarray): Input data series
            time_vector (np.ndarray): Corresponding time vector
            
        Returns:
            tuple: (detrended_data, trend)
        """
        raise NotImplementedError("Subclasses must implement detrend()")

class RLSDetrender(Detrender):
    """Recursive Least Squares detrending implementation."""
    def __init__(self, params=None):
        super().__init__(params)
        self.filter_q = params.get('filter_q', 0.9825)
        self.P = np.eye(2) * 1000  # Initial covariance matrix
        self.theta = np.zeros(2)   # Initial parameter vector

    def reset(self):
        """Reset the filter state."""
        self.P = np.eye(2) * 1000
        self.theta = np.zeros(2)
        logger.info("RLSDetrender reset.")

    def detrend(self, data, time_vector):
        if len(data) != len(time_vector):
            raise ValueError("Data and time_vector must have the same length.")
            
        n = len(data)
        trend_values = np.zeros_like(data)
        
        for i in range(n):
            phi = np.array([time_vector[i], 1.0])  # Regressor vector for y = a*t + b
            
            y_pred = np.dot(self.theta, phi)  # Predict using current parameters
            e = data[i] - y_pred  # Prediction error
            
            # Update gain vector k
            P_phi = np.dot(self.P, phi)
            denom = self.filter_q + np.dot(phi, P_phi)
            k = P_phi / denom if denom != 0 else np.zeros_like(phi)
            
            # Update parameters theta
            self.theta = self.theta + k * e
            
            # Update covariance matrix P
            self.P = (self.P - np.outer(k, np.dot(phi, self.P))) / self.filter_q
        
        # Calculate the trend based on the final (updated) theta for this batch
        for i in range(n):
            trend_values[i] = np.dot(self.theta, np.array([time_vector[i], 1.0]))
            
        detrended_data = data - trend_values
        return detrended_data, trend_values

class PolynomialDetrender(Detrender):
    """Polynomial fitting detrending implementation."""
    def detrend(self, data, time_vector):
        if len(data) != len(time_vector):
            raise ValueError("Data and time_vector must have the same length.")
            
        poly_order = self.params.get('poly_order', 2)
        coeffs = np.polyfit(time_vector, data, poly_order)
        trend_values = np.polyval(coeffs, time_vector)
        detrended_data = data - trend_values
        return detrended_data, trend_values

def create_detrender(method, params=None):
    """
    Factory function to create a detrender instance.
    
    Args:
        method (str): Detrending method ("RLS", "Polynomial", or "None")
        params (dict): Parameters specific to the detrending method
        
    Returns:
        Detrender: An instance of the specified detrending method
    """
    if method == "RLS":
        return RLSDetrender(params)
    elif method == "Polynomial":
        return PolynomialDetrender(params)
    elif method == "None":
        return None
    else:
        raise ValueError(f"Unknown detrending method: {method}") 