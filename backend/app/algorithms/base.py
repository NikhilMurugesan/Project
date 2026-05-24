# Bits and pieces shared by both algorithms: a tiny stopwatch, the
# Truck -> Route conversion, the Order -> Stop conversion, and the final
# packaging of routes + metrics into an AllocationResult.
#
# Keeping all of this in one place is what lets the two algorithms be a
# clean apples-to-apples comparison.
from __future__ import annotations

import statistics
import time
from dataclasses import dataclass
from typing import Iterable

from ..core.router import Route, StopState
from ..models import Order, Truck
from ..schemas import (
    AllocationResult,
    AssignmentExplanation,
    Metrics,
    RouteStop,
    TruckRoute,
    Weights,
)


@dataclass
class AlgoContext:
    trucks: list[Truck]
    orders: list[Order]
    weights: Weights


def make_routes(trucks: Iterable[Truck]) -> dict[int, Route]:
    return {
        t.id: Route(
            truck_id=t.id,
            truck_name=t.name,
            depot_lat=t.lat,
            depot_lon=t.lon,
            capacity_kg=t.capacity_kg,
            speed_kmh=t.avg_speed_kmh,
            shift_start=t.shift_start,
            shift_end=t.shift_end,
            capabilities=list(t.capabilities or []),
            cost_per_km=t.cost_per_km,
        )
        for t in trucks
    }


def order_to_stop(o: Order) -> StopState:
    return StopState(
        order_id=o.id,
        order_code=o.code,
        lat=o.lat,
        lon=o.lon,
        weight_kg=o.weight_kg,
        service_minutes=o.service_minutes,
        tw_start=o.tw_start,
        tw_end=o.tw_end,
        sla_deadline=o.sla_deadline,
    )


def build_result(
    algorithm: str,
    routes: dict[int, Route],
    trucks: list[Truck],
    orders: list[Order],
    explanations: list[AssignmentExplanation],
    unassigned_ids: list[int],
    elapsed_ms: float,
) -> AllocationResult:
    truck_routes: list[TruckRoute] = []
    total_distance = 0.0
    total_cost = 0.0
    per_truck_distance: list[float] = []
    total_capacity = sum(t.capacity_kg for t in trucks) or 1.0
    used_capacity = 0.0
    sla_met = 0
    assigned = 0
    truck_by_id = {t.id: t for t in trucks}

    for tid, route in routes.items():
        stops_out: list[RouteStop] = []
        for idx, s in enumerate(route.stops):
            stops_out.append(
                RouteStop(
                    order_id=s.order_id,
                    order_code=s.order_code,
                    sequence=idx,
                    arrival_minute=int(round(s.arrival_minute)),
                    departure_minute=int(round(s.departure_minute)),
                    distance_km_from_prev=round(s.distance_km_from_prev, 3),
                )
            )
        truck_routes.append(
            TruckRoute(
                truck_id=tid,
                truck_name=route.truck_name,
                stops=stops_out,
                total_distance_km=round(route.total_distance_km, 3),
                total_load_kg=round(route.total_load_kg, 3),
            )
        )
        total_distance += route.total_distance_km
        total_cost += route.total_distance_km * truck_by_id[tid].cost_per_km
        per_truck_distance.append(route.total_distance_km)
        used_capacity += route.total_load_kg
        assigned += len(route.stops)
        for s in route.stops:
            if s.arrival_minute <= s.sla_deadline:
                sla_met += 1

    workload_std = statistics.pstdev(per_truck_distance) if per_truck_distance else 0.0
    metrics = Metrics(
        algorithm=algorithm,
        total_distance_km=round(total_distance, 3),
        total_cost=round(total_cost, 3),
        assigned_count=assigned,
        unassigned_count=len(unassigned_ids),
        sla_met_pct=round(100.0 * sla_met / assigned, 2) if assigned else 0.0,
        capacity_utilization_pct=round(100.0 * used_capacity / total_capacity, 2),
        workload_stddev_km=round(workload_std, 3),
        runtime_ms=round(elapsed_ms, 3),
    )
    return AllocationResult(
        algorithm=algorithm,
        metrics=metrics,
        routes=truck_routes,
        unassigned_order_ids=unassigned_ids,
        explanations=explanations,
    )


class Timer:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.elapsed_ms = (time.perf_counter() - self.t0) * 1000.0
