from app.core.router import Route, StopState, best_insertion


def _route():
    return Route(
        truck_id=1,
        truck_name="T1",
        depot_lat=51.5,
        depot_lon=-0.1,
        capacity_kg=500.0,
        speed_kmh=40.0,
        shift_start=8 * 60,
        shift_end=18 * 60,
        capabilities=["refrigerated"],
    )


def _stop(order_id=1, lat=51.51, lon=-0.11, weight=100, tw=(9 * 60, 17 * 60), sla=17 * 60):
    return StopState(
        order_id=order_id,
        order_code=f"O{order_id}",
        lat=lat,
        lon=lon,
        weight_kg=weight,
        service_minutes=10,
        tw_start=tw[0],
        tw_end=tw[1],
        sla_deadline=sla,
    )


def test_insertion_feasible():
    r = _route()
    res = best_insertion(r, _stop(), required_caps=[])
    assert res is not None
    assert res.delta_km > 0


def test_capability_blocks_insertion():
    r = _route()
    res = best_insertion(r, _stop(), required_caps=["hazmat"])
    assert res is None


def test_capacity_blocks_insertion():
    r = _route()
    res = best_insertion(r, _stop(weight=600), required_caps=[])
    assert res is None


def test_time_window_blocks_insertion():
    r = _route()
    res = best_insertion(r, _stop(tw=(7 * 60, 7 * 60 + 5), sla=7 * 60 + 5), required_caps=[])
    assert res is None


def test_multi_stop_arrival_times_monotonic():
    r = _route()
    # Two stops along a line.
    s1 = _stop(order_id=1, lat=51.52, lon=-0.10)
    s2 = _stop(order_id=2, lat=51.54, lon=-0.08)
    r1 = best_insertion(r, s1, [])
    r.stops = r1.new_stops
    r2 = best_insertion(r, s2, [])
    r.stops = r2.new_stops
    arrivals = [s.arrival_minute for s in r.stops]
    assert arrivals == sorted(arrivals)
    assert r.total_distance_km > 0
