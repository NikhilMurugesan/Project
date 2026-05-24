# Per-truck route state and the cheapest-insertion logic both algorithms
# share. The shape is intentionally small:
#
#   Route = depot + ordered list of stops, all timed off shift_start using
#           the truck's avg_speed_kmh.
#
# `best_insertion` tries every position in the current route, keeps only
# feasible ones (capability, capacity, time windows, SLA, shift end), and
# returns the one that adds the fewest extra km.
#
# Not a real VRP solver -- just enough to make the greedy-vs-Hungarian
# comparison meaningful. If we ever needed real multi-stop optimisation
# we'd reach for OR-Tools here.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .distance import haversine_km, travel_minutes


@dataclass
class StopState:
    order_id: int
    order_code: str
    lat: float
    lon: float
    weight_kg: float
    service_minutes: int
    tw_start: int
    tw_end: int
    sla_deadline: int
    arrival_minute: float = 0.0
    departure_minute: float = 0.0
    distance_km_from_prev: float = 0.0


@dataclass
class Route:
    truck_id: int
    truck_name: str
    depot_lat: float
    depot_lon: float
    capacity_kg: float
    speed_kmh: float
    shift_start: int
    shift_end: int
    capabilities: list[str]
    cost_per_km: float = 1.0
    stops: list[StopState] = field(default_factory=list)

    # ---- derived ----
    @property
    def total_distance_km(self) -> float:
        return sum(s.distance_km_from_prev for s in self.stops)

    @property
    def total_load_kg(self) -> float:
        return sum(s.weight_kg for s in self.stops)

    def clone(self) -> "Route":
        r = Route(
            truck_id=self.truck_id,
            truck_name=self.truck_name,
            depot_lat=self.depot_lat,
            depot_lon=self.depot_lon,
            capacity_kg=self.capacity_kg,
            speed_kmh=self.speed_kmh,
            shift_start=self.shift_start,
            shift_end=self.shift_end,
            capabilities=list(self.capabilities),
            cost_per_km=self.cost_per_km,
            stops=[StopState(**s.__dict__) for s in self.stops],
        )
        return r


def _recompute(route: Route, stops: list[StopState]) -> Optional[list[StopState]]:
    """Walk through `stops` in order, working out when the truck arrives at
    each one and whether that arrival is actually legal.

    Returns the timed list of stops, or None if anything is violated
    (time window closed, SLA missed, or shift would run over).
    """
    out: list[StopState] = []
    prev_lat, prev_lon = route.depot_lat, route.depot_lon
    t = float(route.shift_start)
    for s in stops:
        d = haversine_km(prev_lat, prev_lon, s.lat, s.lon)
        t += travel_minutes(d, route.speed_kmh)
        # If we'd get there before the window opens, wait at the door.
        arrival = max(t, float(s.tw_start))
        if arrival > s.tw_end:
            return None
        if arrival > s.sla_deadline:
            return None
        departure = arrival + s.service_minutes
        if departure > route.shift_end:
            return None
        new_stop = StopState(
            order_id=s.order_id,
            order_code=s.order_code,
            lat=s.lat,
            lon=s.lon,
            weight_kg=s.weight_kg,
            service_minutes=s.service_minutes,
            tw_start=s.tw_start,
            tw_end=s.tw_end,
            sla_deadline=s.sla_deadline,
            arrival_minute=arrival,
            departure_minute=departure,
            distance_km_from_prev=d,
        )
        out.append(new_stop)
        prev_lat, prev_lon = s.lat, s.lon
        t = departure
    return out


def capabilities_ok(route: Route, required: list[str]) -> bool:
    caps = set(route.capabilities)
    return all(r in caps for r in required)


def capacity_ok(route: Route, weight_kg: float) -> bool:
    return route.total_load_kg + weight_kg <= route.capacity_kg + 1e-9


@dataclass
class InsertionResult:
    position: int
    delta_km: float
    new_stops: list[StopState]


def best_insertion(route: Route, candidate: StopState, required_caps: list[str]) -> Optional[InsertionResult]:
    """Try every position in the route and pick the one that adds the fewest km.

    Returns None if no position works -- the truck doesn't have the right
    capabilities, is over capacity, or every slot blows a time window or
    runs past the shift.
    """
    if not capabilities_ok(route, required_caps):
        return None
    if not capacity_ok(route, candidate.weight_kg):
        return None

    base_distance = route.total_distance_km
    best: Optional[InsertionResult] = None
    for pos in range(len(route.stops) + 1):
        trial = route.stops[:pos] + [candidate] + route.stops[pos:]
        recomputed = _recompute(route, trial)
        if recomputed is None:
            continue
        new_dist = sum(s.distance_km_from_prev for s in recomputed)
        delta = new_dist - base_distance
        if best is None or delta < best.delta_km:
            best = InsertionResult(position=pos, delta_km=delta, new_stops=recomputed)
    return best


def insert(route: Route, candidate: StopState, required_caps: list[str]) -> Optional[InsertionResult]:
    """Same as `best_insertion`, but actually commits the change to the route."""
    res = best_insertion(route, candidate, required_caps)
    if res is None:
        return None
    route.stops = res.new_stops
    return res
