import math


def angular_distance(alt1: float, az1: float, alt2: float, az2: float) -> float:
    """Compute angular distance between two alt/az positions using Vincenty formula."""
    lat1 = math.radians(alt1)
    lat2 = math.radians(alt2)
    dlon = math.radians(az2 - az1)

    sin_lat1 = math.sin(lat1)
    cos_lat1 = math.cos(lat1)
    sin_lat2 = math.sin(lat2)
    cos_lat2 = math.cos(lat2)
    sin_dlon = math.sin(dlon)
    cos_dlon = math.cos(dlon)

    num = math.sqrt(
        (cos_lat2 * sin_dlon) ** 2
        + (cos_lat1 * sin_lat2 - sin_lat1 * cos_lat2 * cos_dlon) ** 2
    )
    den = sin_lat1 * sin_lat2 + cos_lat1 * cos_lat2 * cos_dlon

    return math.degrees(math.atan2(num, den))


def normalize_angle(angle: float, min_val: float, max_val: float) -> float:
    """Wrap angle to [min_val, max_val) range."""
    span = max_val - min_val
    if span <= 0:
        return angle
    result = angle
    while result >= max_val:
        result -= span
    while result < min_val:
        result += span
    return result


def clamp(value: float, low: float, high: float) -> float:
    """Clamp value to [low, high] range."""
    return max(low, min(high, value))


def alt_az_delta(
    current_alt: float, current_az: float,
    target_alt: float, target_az: float,
) -> tuple:
    """Compute (delta_alt, delta_az) with shortest-path azimuth wrapping."""
    d_alt = target_alt - current_alt
    d_az = target_az - current_az
    if d_az > 180.0:
        d_az -= 360.0
    elif d_az < -180.0:
        d_az += 360.0
    return (d_alt, d_az)


def degrees_to_arcsec(deg: float) -> float:
    """Convert degrees to arcseconds."""
    return deg * 3600.0


def arcsec_to_degrees(arcsec: float) -> float:
    """Convert arcseconds to degrees."""
    return arcsec / 3600.0
