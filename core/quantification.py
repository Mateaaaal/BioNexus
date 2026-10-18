def calculate_stoichiometric_ratio(area_band_1: float, area_band_2: float) -> float:
    """
    Calculates the relative ratio between two protein bands (e.g., Heavy vs Light chain).
    
    Args:
        area_band_1: Integrated area of the primary band.
        area_band_2: Integrated area of the secondary reference band.
        
    Returns:
        The calculated ratio rounded to 2 decimal places, or 0.0 if invalid.
    """
    if area_band_2 <= 0.0:
        return 0.0
    return round(area_band_1 / area_band_2, 2)

def calculate_fraction_purity(target_area: float, total_lane_area: float) -> float:
    """
    Calculates the purity percentage of a specific protein fraction within a lane.
    
    Args:
        target_area: Integrated area of the target purified protein.
        total_lane_area: Total integrated area of all detected bands in the lane.
        
    Returns:
        The purity percentage (0.0 to 100.0) rounded to 1 decimal place.
    """
    if total_lane_area <= 0.0:
        return 0.0
    return round((target_area / total_lane_area) * 100.0, 1)