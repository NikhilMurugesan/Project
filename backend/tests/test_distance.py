from app.core.distance import haversine_km, travel_minutes


def test_haversine_zero():
    assert haversine_km(10, 20, 10, 20) == 0.0


def test_haversine_known_distance():
    # London (51.5074, -0.1278) -> Paris (48.8566, 2.3522) ≈ 343 km
    d = haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert 330 < d < 360


def test_travel_minutes():
    assert travel_minutes(40.0, 40.0) == 60.0
    assert travel_minutes(0.0, 40.0) == 0.0
