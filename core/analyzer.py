import numpy as np

class GelAnalyzer:
    """Utility class for basic gel image processing operations."""

    @staticmethod
    def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
        """
        Converts an RGB/RGBA image to grayscale using the mean of color channels.
        
        Args:
            image (np.ndarray): The input image array.
            
        Returns:
            np.ndarray: 2D grayscale image array.
        """
        if image.ndim == 3:
            return np.mean(image[:, :, :3], axis=2)
        else: 
            return image

    @staticmethod
    def invert_image(gray_image: np.ndarray) -> np.ndarray:
        """
        Inverts a normalized grayscale image (0.0 to 1.0) so that dark bands become peaks.
        
        Args:
            gray_image (np.ndarray): The input grayscale image.
            
        Returns:
            np.ndarray: The inverted image.
        """
        return 1.0 - gray_image

    @staticmethod
    def detect_gel_bounds(inverted_image: np.ndarray, threshold_ratio: float = 0.2) -> tuple[int, int]:
        """
        Detects the upper and lower boundaries of the actual gel by analyzing row means.
        
        Args:
            inverted_image (np.ndarray): The inverted grayscale gel image.
            threshold_ratio (float): The ratio of the max intensity used as cutoff.
            
        Returns:
            tuple[int, int]: (y_start, y_end) vertical boundaries of the gel.
        """
        row_means = np.mean(inverted_image, axis=1)
        threshold = np.max(row_means) * threshold_ratio
        valid_indices = np.where(row_means > threshold)[0]

        if len(valid_indices) > 0:
            return (int(valid_indices[0]), int(valid_indices[-1]))
        else:
            return (0, inverted_image.shape[0])