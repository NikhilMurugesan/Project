# Hungarian allocator.
#
# Same scoring + feasibility checks as the greedy version -- the only thing
# that changes is the selection step. Instead of picking one order at a time
# we build an N x M cost matrix and hand it to scipy.
#
# Wrinkle: linear_sum_assignment is strictly 1-to-1, but we usually have way
# more orders than trucks. So we run it in rounds: assign at most one order
# per truck per round, update the routes, repeat with whatever's left.
# Per-round optimality, not global optimality across rounds -- documented in
# ANALYSIS.md.
from __future__ import annotations

from typing import Optional

import numpy as np
from scipy.optimize import linear_sum_assignment

from ..core.router import best_insertion
from ..core.scoring import soft_score
from ..models import Order, Truck
from ..schemas import AllocationResult, AssignmentExplanation, Weights
from .base import Timer, build_result, make_routes, order_to_stop


# Sentinel cost for infeasible (order, truck) pairs. Big enough that the
# solver will only pick one if literally nothing else is feasible.
INFEASIBLE = 1e9


def _build_cost_matrix(routes, orders_to_assign, weights):
    truck_ids = list(routes.keys())
    n_orders = len(orders_to_assign)
    n_trucks = len(truck_ids)
    cost = np.full((n_orders, n_trucks), INFEASIBLE, dtype=float)
    delta_km = np.full((n_orders, n_trucks), INFEASIBLE, dtype=float)
    fleet_avg = (
        sum(r.total_distance_km for r in routes.values()) / max(1, len(routes))
    )
    for i, order in enumerate(orders_to_assign):
        stop = order_to_stop(order)
        required = list(order.required_capabilities or [])
        for j, tid in enumerate(truck_ids):
            route = routes[tid]
            ins = best_insertion(route, stop, required)
            if ins is None:
                continue
            cost[i, j] = soft_score(
                delta_km=ins.delta_km,
                priority=order.priority,
                truck_current_distance_km=route.total_distance_km,
                fleet_avg_distance_km=fleet_avg,
                weights=weights,
            )
            delta_km[i, j] = ins.delta_km
    return truck_ids, cost, delta_km


def allocate(trucks: list[Truck], orders: list[Order], weights: Weights) -> AllocationResult:
    with Timer() as timer:
        routes = make_routes(trucks)

        explanations: list[AssignmentExplanation] = []
        unassigned: list[int] = []

        # The Hungarian solver doesn't care about order, but pre-sorting by
        # priority makes tie-breaks lean the right way and keeps results
        # comparable to the greedy run on the same input.
        remaining = sorted(orders, key=lambda o: (-o.priority, o.sla_deadline))

        while remaining:
            truck_ids, cost, delta_km = _build_cost_matrix(routes, remaining, weights)
            if not truck_ids:
                unassigned.extend(o.id for o in remaining)
                for o in remaining:
                    explanations.append(
                        AssignmentExplanation(
                            order_id=o.id,
                            order_code=o.code,
                            chosen_truck_id=None,
                            chosen_truck_name=None,
                            score=None,
                            reasons=["No trucks available."],
                        )
                    )
                break

            row_ind, col_ind = linear_sum_assignment(cost)

            assigned_in_round: list[int] = []
            for r, c in zip(row_ind, col_ind):
                if cost[r, c] >= INFEASIBLE / 2:
                    continue
                order = remaining[r]
                tid = truck_ids[c]
                route = routes[tid]
                stop = order_to_stop(order)
                required = list(order.required_capabilities or [])
                ins = best_insertion(route, stop, required)
                if ins is None:
                    continue
                route.stops = ins.new_stops

                # Explanation: what would have been the next-best truck for
                # this order? Blank out the chosen column, then take the min
                # of the rest.
                row = cost[r].copy()
                row[c] = INFEASIBLE
                runner_col = int(np.argmin(row))
                runner_id = truck_ids[runner_col] if row[runner_col] < INFEASIBLE / 2 else None
                runner_score = float(row[runner_col]) if runner_id is not None else None
                runner_name = routes[runner_id].truck_name if runner_id is not None else None

                reasons = [
                    f"Hungarian optimum for this round (score {cost[r, c]:.2f})",
                    f"Insertion delta = {ins.delta_km:.2f} km",
                    f"Priority {order.priority}/5, SLA at minute {order.sla_deadline}",
                ]
                if runner_id is not None:
                    reasons.append(
                        f"Next-best truck '{runner_name}' scored {runner_score:.2f}"
                    )
                explanations.append(
                    AssignmentExplanation(
                        order_id=order.id,
                        order_code=order.code,
                        chosen_truck_id=tid,
                        chosen_truck_name=route.truck_name,
                        score=round(float(cost[r, c]), 3),
                        reasons=reasons,
                        runner_up_truck_id=runner_id,
                        runner_up_truck_name=runner_name,
                        runner_up_score=round(runner_score, 3) if runner_score is not None else None,
                    )
                )
                assigned_in_round.append(order.id)

            if not assigned_in_round:
                # Bail-out: nothing in this round was feasible for any truck.
                # Without this we'd loop forever on impossible orders.
                for o in remaining:
                    unassigned.append(o.id)
                    # Generate a short blockers note if none yet.
                    if not any(e.order_id == o.id for e in explanations):
                        explanations.append(
                            AssignmentExplanation(
                                order_id=o.id,
                                order_code=o.code,
                                chosen_truck_id=None,
                                chosen_truck_name=None,
                                score=None,
                                reasons=["No feasible truck (capability/capacity/time)."],
                            )
                        )
                break

            assigned_set = set(assigned_in_round)
            remaining = [o for o in remaining if o.id not in assigned_set]

    return build_result(
        "hungarian", routes, trucks, orders, explanations, unassigned, timer.elapsed_ms
    )
