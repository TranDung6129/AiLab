import pytest
import numpy as np
from algorithm.kinematic_processor import KinematicProcessor

@pytest.fixture
def kinematic_processor():
    return KinematicProcessor(dt=0.001)

@pytest.fixture
def sample_data():
    # Create sample acceleration data
    t = np.linspace(0, 1, 1000)
    acc_x = np.sin(2 * np.pi * 10 * t)
    acc_y = np.cos(2 * np.pi * 10 * t)
    acc_z = np.zeros_like(t)
    return {
        'time': t,
        'acc_x': acc_x,
        'acc_y': acc_y,
        'acc_z': acc_z
    }

def test_initialization(kinematic_processor):
    """Test KinematicProcessor initialization"""
    assert kinematic_processor.dt == 0.001
    assert kinematic_processor.sample_frame_size == 20
    assert kinematic_processor.calc_frame_size == 2000
    assert kinematic_processor.integrator is not None
    assert kinematic_processor.vel_detrender is not None
    assert kinematic_processor.disp_detrender is not None

def test_process_frame(kinematic_processor, sample_data):
    """Test frame processing"""
    # Process a frame of acceleration data
    frame_size = kinematic_processor.sample_frame_size
    acc_frame = sample_data['acc_x'][:frame_size]
    
    disp_output, vel_output, acc_output = kinematic_processor.process_frame(acc_frame)
    
    # Check output lengths
    assert len(disp_output) == frame_size
    assert len(vel_output) == frame_size
    assert len(acc_output) == frame_size
    
    # Check that data has been processed (not equal to input)
    assert not np.array_equal(vel_output, acc_frame)
    assert not np.array_equal(disp_output, acc_frame)

def test_warmup(kinematic_processor, sample_data):
    """Test warmup behavior"""
    frame_size = kinematic_processor.sample_frame_size
    acc_frame = sample_data['acc_x'][:frame_size]
    
    # Process frames up to warmup_frames
    for _ in range(kinematic_processor.warmup_frames):
        disp_output, vel_output, acc_output = kinematic_processor.process_frame(acc_frame)
    
    # Check that processor is warmed up
    assert kinematic_processor.is_warmed_up()

def test_reset(kinematic_processor, sample_data):
    """Test reset functionality"""
    frame_size = kinematic_processor.sample_frame_size
    acc_frame = sample_data['acc_x'][:frame_size]
    
    # Process some frames
    for _ in range(3):
        kinematic_processor.process_frame(acc_frame)
    
    # Reset the processor
    kinematic_processor.reset()
    
    # Check that frame count is reset
    assert kinematic_processor.frame_count == 0
    
    # Check that buffers are reset
    assert np.all(kinematic_processor.acc_buffer == 0)
    assert np.all(kinematic_processor.vel_buffer_detrended == 0)
    assert np.all(kinematic_processor.disp_buffer_detrended == 0)

def test_get_cumulative_results(kinematic_processor, sample_data):
    """Test getting cumulative results"""
    frame_size = kinematic_processor.sample_frame_size
    acc_frame = sample_data['acc_x'][:frame_size]
    
    # Process some frames
    for _ in range(3):
        kinematic_processor.process_frame(acc_frame)
    
    # Get cumulative results
    time_vector, disp_buffer, vel_buffer, acc_buffer = kinematic_processor.get_cumulative_results()
    
    # Check buffer lengths
    assert len(time_vector) == kinematic_processor.calc_frame_size
    assert len(disp_buffer) == kinematic_processor.calc_frame_size
    assert len(vel_buffer) == kinematic_processor.calc_frame_size
    assert len(acc_buffer) == kinematic_processor.calc_frame_size

def test_edge_cases(kinematic_processor):
    """Test edge cases and error handling"""
    # Test with empty array
    empty_array = np.array([])
    disp_output, vel_output, acc_output = kinematic_processor.process_frame(empty_array)
    
    # Check that outputs are NaN arrays of correct length
    assert len(disp_output) == kinematic_processor.sample_frame_size
    assert len(vel_output) == kinematic_processor.sample_frame_size
    assert len(acc_output) == kinematic_processor.sample_frame_size
    assert np.all(np.isnan(disp_output))
    assert np.all(np.isnan(vel_output))
    assert np.all(np.isnan(acc_output))
    
    # Test with frame larger than sample_frame_size
    large_frame = np.ones(kinematic_processor.sample_frame_size + 10)
    disp_output, vel_output, acc_output = kinematic_processor.process_frame(large_frame)
    
    # Check that outputs are truncated to sample_frame_size
    assert len(disp_output) == kinematic_processor.sample_frame_size
    assert len(vel_output) == kinematic_processor.sample_frame_size
    assert len(acc_output) == kinematic_processor.sample_frame_size
    
    # Test with frame smaller than sample_frame_size
    small_frame = np.ones(kinematic_processor.sample_frame_size - 5)
    disp_output, vel_output, acc_output = kinematic_processor.process_frame(small_frame)
    
    # Check that outputs are padded to sample_frame_size
    assert len(disp_output) == kinematic_processor.sample_frame_size
    assert len(vel_output) == kinematic_processor.sample_frame_size
    assert len(acc_output) == kinematic_processor.sample_frame_size 