import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

def calculate_lane_density(
    lane_crop: np.ndarray,
    known_peaks: list[int] = None,
    distance_threshold: int = 15,
    prominence: float = 0.05,
    sigma: float = 2.0
) -> tuple[np.ndarray, list[int], list[float]]:
    """
    Extracts a smoothed 1D intensity profile and calculates relative peak area percentages.
    Uses predefined peaks if provided, otherwise detects them automatically.
    """
    profile = np.mean(lane_crop, axis=1)
    profile = gaussian_filter1d(profile, sigma=sigma)
    profile = profile - np.min(profile)

    # Use the already validated bands from the GUI if they exist
    if known_peaks is not None and len(known_peaks) > 0:
        peaks = sorted(known_peaks)
    else:
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
        area = np.trapezoid(profile[start:end])
        band_areas.append(area)

    total_area = sum(band_areas) if sum(band_areas) > 0 else 1.0
    percentages = [(area / total_area) * 100.0 for area in band_areas]

    return profile, peaks, percentages