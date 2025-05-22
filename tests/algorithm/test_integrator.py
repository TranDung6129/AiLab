import pytest
import numpy as np
from algorithm.integrator import (
    Integrator, TrapezoidalIntegrator, SimpsonIntegrator, RectangularIntegrator,
    create_integrator, SignalIntegrator,
    integrate_acceleration, integrate_velocity,
    apply_dc_correction, apply_high_pass_filter
)

# Test data - increased length to satisfy filter requirements
@pytest.fixture
def sample_data():
    return np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
                     11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0])

@pytest.fixture
def dt():
    return 0.1

# Test base Integrator class
def test_integrator_initialization():
    with pytest.raises(ValueError):
        Integrator(dt=-1.0)
    
    integrator = Integrator(dt=0.1)
    assert integrator.dt == 0.1

# Test TrapezoidalIntegrator
def test_trapezoidal_integrator(sample_data, dt):
    integrator = TrapezoidalIntegrator(dt)
    result = integrator.integrate(sample_data)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    assert result[0] == 0.0  # Initial value should be 0
    
    # Test with empty array
    assert len(integrator.integrate(np.array([]))) == 0
    
    # Test with invalid input
    with pytest.raises(ValueError):
        integrator.integrate([1, 2, 3])  # Not a numpy array

# Test SimpsonIntegrator
def test_simpson_integrator(sample_data, dt):
    integrator = SimpsonIntegrator(dt)
    result = integrator.integrate(sample_data)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    assert result[0] == 0.0  # Initial value should be 0

# Test RectangularIntegrator
def test_rectangular_integrator(sample_data, dt):
    integrator = RectangularIntegrator(dt)
    result = integrator.integrate(sample_data)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    assert result[0] == 0.0  # Initial value should be 0

# Test create_integrator factory function
def test_create_integrator(dt):
    # Test valid methods
    assert isinstance(create_integrator("Trapezoidal", dt), TrapezoidalIntegrator)
    assert isinstance(create_integrator("Simpson", dt), SimpsonIntegrator)
    assert isinstance(create_integrator("Rectangular", dt), RectangularIntegrator)
    
    # Test invalid method
    with pytest.raises(ValueError):
        create_integrator("Invalid", dt)

# Test SignalIntegrator
def test_signal_integrator(sample_data, dt):
    integrator = SignalIntegrator(dt, method="Trapezoidal")
    result = integrator.integrate(sample_data)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)

# Test direct integration functions
def test_integrate_acceleration(sample_data, dt):
    result = integrate_acceleration(sample_data, dt)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    assert result[0] == 0.0
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        integrate_acceleration(np.array([1.0]), dt)  # Too few points
    with pytest.raises(ValueError):
        integrate_acceleration(sample_data, -dt)  # Negative dt

def test_integrate_velocity(sample_data, dt):
    result = integrate_velocity(sample_data, dt)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    assert result[0] == 0.0
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        integrate_velocity(np.array([1.0]), dt)  # Too few points
    with pytest.raises(ValueError):
        integrate_velocity(sample_data, -dt)  # Negative dt

# Test signal processing functions
def test_apply_dc_correction(sample_data):
    result = apply_dc_correction(sample_data)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    assert np.abs(np.mean(result)) < 1e-10  # Mean should be close to 0
    
    # Test invalid input
    with pytest.raises(ValueError):
        apply_dc_correction(np.array([1.0]))  # Too few points

def test_apply_high_pass_filter(sample_data):
    fs = 100.0  # Sampling frequency
    cutoff_freq = 10.0  # Cutoff frequency
    order = 4
    
    result = apply_high_pass_filter(sample_data, cutoff_freq, fs, order)
    
    assert len(result) == len(sample_data)
    assert isinstance(result, np.ndarray)
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        apply_high_pass_filter(np.array([1.0]), cutoff_freq, fs, order)  # Too few points
    with pytest.raises(ValueError):
        apply_high_pass_filter(sample_data, -cutoff_freq, fs, order)  # Negative cutoff
    with pytest.raises(ValueError):
        apply_high_pass_filter(sample_data, cutoff_freq, -fs, order)  # Negative fs
    with pytest.raises(ValueError):
        apply_high_pass_filter(sample_data, cutoff_freq, fs, -order)  # Negative order 