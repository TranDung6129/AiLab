import numpy as np
import logging
from scipy import signal

logger = logging.getLogger(__name__)

class RLSFilter:
    """
    A filter that can remove trends from data using various methods.
    """
    def __init__(self, filter_q=0.9825, method="RLS", detrend_params=None):
        """
        Initializes the RLSFilter.

        Args:
            filter_q (float): Forgetting factor for RLS filter (0 < q <= 1).
            method (str): Detrending method to use. Options:
                - "RLS": Recursive Least Squares (default)
                - "Polynomial": Polynomial fitting
                - "None": No detrending
            detrend_params (dict): Parameters for the detrending method:
                - For "Polynomial": {'poly_order': int}
                - For "RLS": {'filter_q': float}
        """
        self.method = method
        self.detrend_params = detrend_params or {}
        
        # Initialize RLS-specific parameters
        self.filter_q = filter_q
        self.P = np.eye(2) * 1000  # Initial covariance matrix
        self.theta = np.zeros(2)   # Initial parameter vector
        
        logger.info(f"RLSFilter initialized with method={method}, filter_q={filter_q}")

    def reset(self):
        """Resets the filter to its initial state."""
        self.P = np.eye(2) * 1000
        self.theta = np.zeros(2)
        logger.info("RLSFilter reset.")

    def detrend(self, data, time_vector):
        """
        Removes trend from the data using the specified method.

        Args:
            data (np.ndarray): The input data series.
            time_vector (np.ndarray): The corresponding time vector for the data.

        Returns:
            tuple: (detrended_data, trend)
                   - detrended_data (np.ndarray): Data with the trend removed.
                   - trend (np.ndarray): The calculated trend.
        """
        if len(data) != len(time_vector):
            raise ValueError("Data and time_vector must have the same length.")
        
        if self.method == "None":
            return data, np.zeros_like(data)
        elif self.method == "RLS":
            return self._rls_detrend(data, time_vector)
        elif self.method == "Polynomial":
            return self._polynomial_detrend(data, time_vector)
        else:
            raise ValueError(f"Unknown detrending method: {self.method}")

    def _rls_detrend(self, data, time_vector):
        """Removes trend using RLS algorithm."""
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

    def _polynomial_detrend(self, data, time_vector):
        """Removes trend using polynomial fitting."""
        poly_order = self.detrend_params.get('poly_order', 2)
        coeffs = np.polyfit(time_vector, data, poly_order)
        trend_values = np.polyval(coeffs, time_vector)
        detrended_data = data - trend_values
        return detrended_data, trend_values 