import numpy as np
import logging

logger = logging.getLogger(__name__)

class Integrator:
    """Base class for all integrators."""
    def __init__(self, dt):
        """
        Initialize the integrator.
        
        Args:
            dt (float): Time step between data points
        """
        if dt <= 0:
            raise ValueError("Time step dt must be positive.")
        self.dt = dt

    def integrate(self, data_series):
        """
        Integrate the input data series.
        
        Args:
            data_series (np.ndarray): Input data series to integrate
            
        Returns:
            np.ndarray: Integrated data series
        """
        raise NotImplementedError("Subclasses must implement integrate()")

class TrapezoidalIntegrator(Integrator):
    """Trapezoidal rule integration implementation."""
    def integrate(self, data_series):
        if not isinstance(data_series, np.ndarray) or data_series.ndim != 1:
            raise ValueError("Input data_series must be a 1D numpy array.")
        if len(data_series) == 0:
            return np.array([])
            
        integrated_series = np.zeros_like(data_series, dtype=float)
        for i in range(1, len(data_series)):
            integrated_series[i] = integrated_series[i-1] + \
                                   (data_series[i-1] + data_series[i]) * self.dt / 2
        return integrated_series

class SimpsonIntegrator(Integrator):
    """Simpson's rule integration implementation."""
    def integrate(self, data_series):
        if not isinstance(data_series, np.ndarray) or data_series.ndim != 1:
            raise ValueError("Input data_series must be a 1D numpy array.")
        if len(data_series) == 0:
            return np.array([])
            
        integrated_series = np.zeros_like(data_series, dtype=float)
        
        # Use trapezoidal for the last point if odd number of points
        if len(data_series) % 2 != 0:
            logger.warning("Simpson's rule requires even number of points. Using trapezoidal rule for last point.")
            for i in range(1, len(data_series)-1, 2):
                integrated_series[i+1] = integrated_series[i-1] + \
                    (data_series[i-1] + 4*data_series[i] + data_series[i+1]) * self.dt / 3
            if len(data_series) % 2 != 0:
                integrated_series[-1] = integrated_series[-2] + \
                    (data_series[-2] + data_series[-1]) * self.dt / 2
        else:
            for i in range(1, len(data_series), 2):
                integrated_series[i+1] = integrated_series[i-1] + \
                    (data_series[i-1] + 4*data_series[i] + data_series[i+1]) * self.dt / 3
        return integrated_series

class RectangularIntegrator(Integrator):
    """Rectangular rule integration implementation."""
    def integrate(self, data_series):
        if not isinstance(data_series, np.ndarray) or data_series.ndim != 1:
            raise ValueError("Input data_series must be a 1D numpy array.")
        if len(data_series) == 0:
            return np.array([])
            
        integrated_series = np.zeros_like(data_series, dtype=float)
        for i in range(1, len(data_series)):
            integrated_series[i] = integrated_series[i-1] + data_series[i] * self.dt
        return integrated_series

def create_integrator(method, dt):
    """
    Factory function to create an integrator instance.
    
    Args:
        method (str): Integration method ("Trapezoidal", "Simpson", or "Rectangular")
        dt (float): Time step between data points
        
    Returns:
        Integrator: An instance of the specified integration method
    """
    if method == "Trapezoidal":
        return TrapezoidalIntegrator(dt)
    elif method == "Simpson":
        return SimpsonIntegrator(dt)
    elif method == "Rectangular":
        return RectangularIntegrator(dt)
    else:
        raise ValueError(f"Unknown integration method: {method}")

# For backward compatibility
class SignalIntegrator(Integrator):
    """Legacy class for backward compatibility."""
    def __init__(self, dt, method="Trapezoidal"):
        super().__init__(dt)
        self.method = method
        logger.info(f"SignalIntegrator initialized with dt={dt}, method={method}")

    def integrate(self, data_series):
        integrator = create_integrator(self.method, self.dt)
        return integrator.integrate(data_series) 