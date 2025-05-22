import pytest
import numpy as np
from analysis.statistical_tools import (
    calculate_descriptive_stats,
    calculate_correlation_matrix,
    calculate_histogram
)

@pytest.fixture
def test_data():
    # Create test data with known properties
    np.random.seed(42)
    data = {
        'x': np.random.normal(0, 1, 1000),
        'y': np.random.normal(0, 1, 1000),
        'z': np.random.normal(0, 1, 1000)
    }
    return data

def test_calculate_descriptive_stats(test_data):
    """Test descriptive statistics calculation"""
    # Calculate statistics
    stats = calculate_descriptive_stats(test_data)
    
    # Check output structure
    assert isinstance(stats, list)
    assert len(stats) == 6  # Mean, Median, Std Dev, Min, Max, Variance
    
    # Check that all metrics are present
    metrics = [row['Metric'] for row in stats]
    assert 'Mean' in metrics
    assert 'Median' in metrics
    assert 'Std Dev' in metrics
    assert 'Min' in metrics
    assert 'Max' in metrics
    assert 'Variance' in metrics
    
    # Check values for each field
    for row in stats:
        for field in test_data.keys():
            assert field in row
            if row['Metric'] == 'Mean':
                assert abs(row[field] - np.mean(test_data[field])) < 1e-10
            elif row['Metric'] == 'Median':
                assert abs(row[field] - np.median(test_data[field])) < 1e-10
            elif row['Metric'] == 'Std Dev':
                assert abs(row[field] - np.std(test_data[field])) < 1e-10
            elif row['Metric'] == 'Min':
                assert abs(row[field] - np.min(test_data[field])) < 1e-10
            elif row['Metric'] == 'Max':
                assert abs(row[field] - np.max(test_data[field])) < 1e-10
            elif row['Metric'] == 'Variance':
                assert abs(row[field] - np.var(test_data[field])) < 1e-10

def test_calculate_correlation_matrix(test_data):
    """Test correlation matrix calculation"""
    # Calculate correlation matrix
    corr_matrix, field_names = calculate_correlation_matrix(test_data)
    
    # Check output structure
    assert isinstance(corr_matrix, np.ndarray)
    assert isinstance(field_names, list)
    assert corr_matrix.shape == (len(test_data), len(test_data))
    assert len(field_names) == len(test_data)
    
    # Check field names
    assert all(field in field_names for field in test_data.keys())
    
    # Check matrix properties
    assert np.all(np.diag(corr_matrix) == 1.0)  # Diagonal should be 1
    assert np.all(np.abs(corr_matrix) <= 1.0)  # All values should be between -1 and 1
    assert np.allclose(corr_matrix, corr_matrix.T)  # Matrix should be symmetric

def test_calculate_histogram(test_data):
    """Test histogram calculation"""
    # Calculate histogram for each field
    for field, data in test_data.items():
        hist, bin_edges = calculate_histogram(data)
        
        # Check output structure
        assert isinstance(hist, np.ndarray)
        assert isinstance(bin_edges, np.ndarray)
        assert len(hist) == 50  # Default number of bins
        assert len(bin_edges) == 51  # n+1 edges for n bins
        
        # Check histogram properties
        assert np.all(hist >= 0)  # All counts should be non-negative
        assert np.sum(hist) == len(data)  # Total count should match data length
        
        # Test with different number of bins
        hist_custom, bin_edges_custom = calculate_histogram(data, num_bins=20)
        assert len(hist_custom) == 20
        assert len(bin_edges_custom) == 21

def test_edge_cases():
    """Test edge cases and error handling"""
    # Test with empty dictionary
    empty_dict = {}
    stats = calculate_descriptive_stats(empty_dict)
    assert len(stats) == 6  # Should still return all metrics
    
    # Test with empty arrays
    empty_data = {'x': np.array([]), 'y': np.array([])}
    stats = calculate_descriptive_stats(empty_data)
    for row in stats:
        for field in empty_data.keys():
            assert row[field] == 'N/A'
    
    # Test with single value arrays
    single_data = {'x': np.array([1.0]), 'y': np.array([2.0])}
    stats = calculate_descriptive_stats(single_data)
    for row in stats:
        for field in single_data.keys():
            assert isinstance(row[field], (int, float))
    
    # Test with NaN values
    nan_data = {'x': np.array([1.0, np.nan, 2.0])}
    stats = calculate_descriptive_stats(nan_data)
    for row in stats:
        if isinstance(row['x'], float) and np.isnan(row['x']):
            continue
        assert row['x'] == 'N/A'
    
    # Test with infinite values
    inf_data = {'x': np.array([1.0, np.inf, 2.0])}
    stats = calculate_descriptive_stats(inf_data)
    for row in stats:
        if isinstance(row['x'], float) and np.isnan(row['x']):
            continue
        assert row['x'] == 'N/A' 