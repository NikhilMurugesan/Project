# Greedy allocator.
#
# The mental model: a human dispatcher with a clipboard. Sort the orders by
# how badly they need to be served (priority first, then SLA deadline), then
# for each one in turn ask every truck "how much extra would this cost you?"
# Pick the cheapest, commit, move on. We also remember the runner-up so the
# UI can show *why* this truck got picked.
from __future__ import annotations

from typing import Optional

from ..core.router import best_insertion
from ..core.scoring import soft_score
from ..models import Order, Truck
from ..schemas import AllocationResult, AssignmentExplanation, Weights
from .base import Timer, build_result, make_routes, order_to_stop


def allocate(trucks: list[Truck], orders: list[Order], weights: Weights) -> AllocationResult:
    with Timer() as timer:
        routes = make_routes(trucks)

        explanations: list[AssignmentExplanation] = []
        unassigned: list[int] = []

        ordered = sorted(orders, key=lambda o: (-o.priority, o.sla_deadline))

        for order in ordered:
            stop = order_to_stop(order)
            required = list(order.required_capabilities or [])

            # Workload term needs the current fleet average. Re-computing this
            # each iteration is cheap and keeps the penalty up to date as we
            # commit new stops.
            fleet_avg = (
                sum(r.total_distance_km for r in routes.values()) / max(1, len(routes))
            )

            best: Optional[tuple[int, float, float]] = None  # (truck_id, score, delta_km)
            runner: Optional[tuple[int, float]] = None
            reasons_blockers: list[str] = []

            for tid, route in routes.items():
                ins = best_insertion(route, stop, required)
                if ins is None:
                    # Record a short reason why this truck failed -- handy
                    # for the UI when an order ends up unassigned.
                    if required and not all(c in route.capabilities for c in required):
                        reasons_blockers.append(f"{route.truck_name}: missing capabilities")
                    elif route.total_load_kg + order.weight_kg > route.capacity_kg + 1e-9:
                        reasons_blockers.append(f"{route.truck_name}: over capacity")
                    else:
                        reasons_blockers.append(f"{route.truck_name}: time window infeasible")
                    continue
                s = soft_score(
                    delta_km=ins.delta_km,
                    priority=order.priority,
                    truck_current_distance_km=route.total_distance_km,
                    fleet_avg_distance_km=fleet_avg,
                    weights=weights,
                )
                if best is None or s < best[1]:
                    if best is not None:
                        runner = (best[0], best[1])
                    best = (tid, s, ins.delta_km)
                elif runner is None or s < runner[1]:
                    runner = (tid, s)

            if best is None:
                unassigned.append(order.id)
                explanations.append(
                    AssignmentExplanation(
                        order_id=order.id,
                        order_code=order.code,
                        chosen_truck_id=None,
                        chosen_truck_name=None,
                        score=None,
                        reasons=["No feasible truck."] + reasons_blockers[:5],
                    )
                )
                continue

            tid, score, delta_km = best
            chosen_route = routes[tid]
            # Re-run insertion to get the actual stop list. (We could have
            # cached it from the loop above; the recompute is cheap enough
            # that it isn't worth the extra bookkeeping.)
            best_ins = best_insertion(chosen_route, stop, required)
            assert best_ins is not None
            chosen_route.stops = best_ins.new_stops

            reasons = [
                f"Cheapest insertion delta = {delta_km:.2f} km",
                f"Priority {order.priority}/5, SLA at minute {order.sla_deadline}",
                f"Truck '{chosen_route.truck_name}' had pre-route distance "
                f"{(chosen_route.total_distance_km - delta_km):.2f} km",
            ]
            runner_id, runner_score = (None, None)
            runner_name = None
            if runner is not None:
                runner_id, runner_score = runner
                runner_name = routes[runner_id].truck_name
                reasons.append(
                    f"Runner-up '{runner_name}' scored {runner_score:.2f} (chosen {score:.2f})"
                )
            explanations.append(
                AssignmentExplanation(
                    order_id=order.id,
                    order_code=order.code,
                    chosen_truck_id=tid,
                    chosen_truck_name=chosen_route.truck_name,
                    score=round(score, 3),
                    reasons=reasons,
                    runner_up_truck_id=runner_id,
                    runner_up_truck_name=runner_name,
                    runner_up_score=round(runner_score, 3) if runner_score is not None else None,
                )
            )

    return build_result(
        "greedy", routes, trucks, orders, explanations, unassigned, timer.elapsed_ms
    )
