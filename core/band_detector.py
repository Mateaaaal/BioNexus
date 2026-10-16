import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks


class BandDetector:
    """Handles the vertical detection of protein bands within a specific lane."""

    def __init__(
        self, prominence: float = 0.015, distance: int = 10, sigma: float = 1.0
    ):
        self.prominence = prominence
        self.distance = distance
        self.sigma = sigma

    def detect_bands(
        self,
        inverted_image: np.ndarray,
        lane_x: int,
        lane_width: int,
        y_start: int = 0,
        y_end: int = 0,
        crop_dye_front: bool = True,
    ) -> list[int]:
        """Scans a vertical section of the image to locate protein bands."""
        # Dynamically calculate bounds based on the true lane width
        half_width = max(3, lane_width // 2)
        x_min = max(0, int(lane_x - half_width))
        x_max = min(inverted_image.shape[1], int(lane_x + half_width))

        img_height = inverted_image.shape[0]

        if crop_dye_front:
            y_max = int(img_height * 0.93)
        else:
            y_max = img_height

        effective_y_end = y_max if (y_end == 0 or y_end > y_max) else y_end

        lane_crop = inverted_image[y_start:effective_y_end, x_min:x_max]

        profile = np.mean(lane_crop, axis=1)
        smoothed_profile = gaussian_filter1d(profile, sigma=self.sigma)

        peaks, _ = find_peaks(
            smoothed_profile, distance=self.distance, prominence=self.prominence
        )

        return [int(p + y_start) for p in peaks]