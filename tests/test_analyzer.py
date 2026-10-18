import numpy as np
from core.analyzer import GelAnalyzer

def test_invert_image():
    # 1. Create a dummy 2x2 gel image (pixel values between 0.0 and 1.0)
    fake_gel = np.array([
        [0.0, 1.0], 
        [0.2, 0.8]
    ])
    
    # 2. Process the dummy gel through the analyzer
    result = GelAnalyzer.invert_image(fake_gel)
    
    # 3. Define the perfect mathematical expectation (1.0 - value)
    expected = np.array([
        [1.0, 0.0], 
        [0.8, 0.2]
    ])
    
    # 4. Assert that the result matches the expectation exactly
    np.testing.assert_array_almost_equal(result, expected)

def test_detect_gel_bounds():
    # 1. Create a virtual 4-row gel with a clear band in the middle
    fake_gel = np.array([
        [0.0, 0.0],  # Row 0: Empty background
        [1.0, 1.0],  # Row 1: Bright protein band
        [0.8, 0.9],  # Row 2: Fading band
        [0.1, 0.0]   # Row 3: Empty background
    ])
    
    # 2. Extract boundaries with a 50% threshold
    y_start, y_end = GelAnalyzer.detect_gel_bounds(fake_gel, threshold_ratio=0.5)
    
    # 3. Assert the bounds correctly identified rows 1 and 2
    assert y_start == 1
    assert y_end == 2