import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

class BandDetector:
    """Handles the vertical detection of protein bands within a specific lane."""

    def __init__(self, prominence: float = 0.015, distance: int = 10, sigma: float = 1.0):
        self.prominence = prominence
        self.distance = distance
        self.sigma = sigma

    def detect_bands(self, 
                     inverted_image: np.ndarray,
                     lane_x: int,
                     lane_width: int,
                     y_start: int = 0,
                     y_end: int = 0,
                     crop_dye_front: bool = True) -> list[int]:
        """
        Scans a vertical section of the image to locate protein bands.
        
        Args:
            inverted_image (np.ndarray): The processed gel image.
            lane_x (int): The center X-coordinate of the lane.
            lane_width (int): The width of the lane in pixels.
            y_start (int): Top boundary.
            y_end (int): Bottom boundary.
            crop_dye_front (bool): If True, ignores the bottom 7% of the image.
            
        Returns:
            list[int]: The Y-coordinates (pixels) of the detected bands.
        """
        x_min = max(0, int(lane_x - 5))
        x_max = min(inverted_image.shape[1], int(lane_x + 5))

        img_height = inverted_image.shape[0]

        # Exclude the dye front artifact if requested
        if crop_dye_front:
            y_max = int(img_height * 0.93)
        else:
            y_max = img_height

        if y_end == 0 or y_end > y_max:
            effective_y_end = y_max
        else:
            effective_y_end = y_end
        
        lane_crop = inverted_image[y_start:effective_y_end, x_min:x_max]
        
        # Generate vertical density profile
        profile = np.mean(lane_crop, axis=1)
        smoothed_profile = gaussian_filter1d(profile, sigma=self.sigma)
        
        peaks, _ = find_peaks(smoothed_profile, distance=self.distance, prominence=self.prominence)

        return [int(p + y_start) for p in peaks]