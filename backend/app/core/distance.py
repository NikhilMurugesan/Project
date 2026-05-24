# Tiny geo helpers. Straight-line distance + a naive km->minutes conversion.
# If/when we hook this up to a real road network (OSRM, Valhalla, ...), only
# this file needs to change.
from __future__ import annotations

import math


# Mean Earth radius. Good enough for our purposes.
EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lon points."""
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def travel_minutes(distance_km: float, speed_kmh: float) -> float:
    # Guard against a zero-speed truck so we don't blow up with a div-by-zero.
    if speed_kmh <= 0:
        return float("inf")
    return (distance_km / speed_kmh) * 60.0
