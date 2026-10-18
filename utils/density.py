import numpy as np
from scipy.signal import find_peaks

def calculate_lane_density(
    lane_crop: np.ndarray,
    distance_threshold: int = 15,
    prominence: float = 10.0,
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """
    Extracts a 1D intensity profile and calculates relative peak area percentages.

    Args:
        lane_crop: 2D grayscale image array of the lane.
        distance_threshold: Minimum pixel distance between detected peaks.
        prominence: Minimum peak prominence for detection.

    Returns:
        profile: 1D intensity array (inverted and baseline-corrected).
        peaks: Indices of detected peak centers.
        percentages: Relative area percentages for each detected band.
    """
    profile_raw = np.mean(lane_crop, axis=1)

    profile = 255.0 - profile_raw
    profile = profile - np.min(profile)

    peaks, _ = find_peaks(
        profile, distance=distance_threshold, prominence=prominence
    )

    if len(peaks) == 0:
        return profile, peaks, []

    half_width = distance_threshold // 2
    band_areas = []

    for peak in peaks:
        start = max(0, peak - half_width)
        end = min(len(profile), peak + half_width)
        area = np.trapz(profile[start:end])
        band_areas.append(area)

    total_area = sum(band_areas) if sum(band_areas) > 0 else 1.0
    percentages = [(area / total_area) * 100.0 for area in band_areas]

    return profile, peaks, percentages