import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

class LaneDetector:
    """Handles the horizontal detection of migration lanes in a gel image."""

    def __init__(self, lane_width: int = 50, y_start: int = 0, y_end: int = 0):
        self.lane_width = lane_width
        self.y_start = y_start
        self.y_end = y_end

    def find_lanes(self, 
                   inverted_image: np.ndarray, 
                   min_distance: int = 70, 
                   prominence: float = 0.015) -> list[int]:
        """
        Detects the X-coordinates of migration lanes using a 1D density profile.
        """
        # 1. Sampling region: Top 40% of the gel to avoid blurred low-MW regions
        y_top = self.y_start + int((self.y_end - self.y_start) * 0.40)
        cropped_image = inverted_image[self.y_start:y_top, :]

        # 2. 1D Profile extraction and smoothing
        profile = np.mean(cropped_image, axis=0)
        smoothed_profile = gaussian_filter1d(profile, sigma=8.0)

        # 3. Min-Max Normalization (Scales profile between 0.0 and 1.0)
        p_min = np.min(smoothed_profile)
        p_max = np.max(smoothed_profile)
        if p_max > p_min:
            normalized_profile = (smoothed_profile - p_min) / (p_max - p_min)
        else:
            normalized_profile = smoothed_profile

        # 4. Search margin (Ignore outer 4% of edges to prevent artifact detection)
        margin = int(inverted_image.shape[1] * 0.04)
        search_region = normalized_profile[margin:-margin]

        # 5. Peak detection on the normalized profile
        peaks_sub, _ = find_peaks(search_region, distance=min_distance, prominence=prominence)
        
        return [int(p + margin) for p in peaks_sub]