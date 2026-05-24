# Soft scoring. The hard constraints decide what's *allowed*; this decides
# which of the allowed options is best. Both algorithms use this exact
# function, so any tweak here changes both at once.
from __future__ import annotations

from ..schemas import Weights


def soft_score(
    delta_km: float,
    priority: int,
    truck_current_distance_km: float,
    fleet_avg_distance_km: float,
    weights: Weights,
) -> float:
    """Score a (truck, order) candidate. Lower is better.

    The three terms:
      * distance  -- extra km this insertion would cost
      * priority  -- we *prefer* to serve high-priority orders, so we knock
                     points off the score for them
      * workload  -- a truck already doing more than the fleet average gets
                     penalised, so the load tends to spread out
    """
    # Map priority 1..5 -> 0..1 so the weight has a predictable range.
    priority_bonus = (priority - 1) / 4.0
    workload_penalty = max(0.0, truck_current_distance_km - fleet_avg_distance_km)
    # The 10.0 factor below is a rough "priority is worth up to ~10 km of
    # detour" rule of thumb. Tunable in the UI via the sliders.
    return (
        weights.distance * delta_km
        - weights.priority * priority_bonus * 10.0
        + weights.workload * workload_penalty
    )
