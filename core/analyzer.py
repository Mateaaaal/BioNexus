import numpy as np


class GelAnalyzer:
    """Utility class for advanced gel image processing and quantification."""

    @staticmethod
    def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
        """
        Converts an RGB/RGBA image to grayscale using precise luminance weights.

        Args:
            image: The input image array.

        Returns:
            2D grayscale image array.
        """
        if image.ndim == 3:
            # Standard human-perceived luminance weights
            return np.dot(image[..., :3], [0.2989, 0.5870, 0.1140])
        return image

    @staticmethod
    def invert_image(gray_image: np.ndarray) -> np.ndarray:
        """
        Inverts a normalized grayscale image so that dark bands become peaks.
        """
        return 1.0 - gray_image

    @staticmethod
    def detect_gel_bounds(
        inverted_image: np.ndarray, threshold_ratio: float = 0.2
    ) -> tuple[int, int]:
        """
        Detects the upper and lower boundaries of the actual gel.
        """
        row_means = np.mean(inverted_image, axis=1)
        threshold = np.max(row_means) * threshold_ratio
        valid_indices = np.where(row_means > threshold)[0]

        if len(valid_indices) > 0:
            return (int(valid_indices[0]), int(valid_indices[-1]))
        return (0, inverted_image.shape[0])