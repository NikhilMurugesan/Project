"""Algorithm tests, including the canonical example where Hungarian beats Greedy."""
from __future__ import annotations

from app.algorithms import greedy, hungarian
from app.schemas import Weights
from tests.conftest import make_order, make_truck


def _hungarian_beats_greedy_setup():
    """Build a scenario where greedy locks A onto T1 and forces B onto a costly T2,
    while Hungarian (global optimum) swaps to give both stops cheap distances.

    Geometry (longitudes at lat ≈ 51.5°N → 1° ≈ 69 km):
      T1 at (51.5, -0.1)
      T2 at (51.5, +0.045)         (~10 km east of T1)
      A  at (51.5, -0.035)         (closer to T1, ~4.5 km from T1, ~5.5 km from T2)
      B  at (51.5, -0.093)         (right next to T1, ~9.5 km from T2)

    Capacity = 100 kg per truck and weight 80 kg per order ⇒ each truck can take
    only one of {A, B}. A's priority (5) is higher than B's (1), so greedy
    handles A first and naively claims T1; B is then forced onto T2.
    """
    trucks = [
        make_truck(id=1, name="T1", lat=51.5, lon=-0.1, capacity_kg=100.0),
        make_truck(id=2, name="T2", lat=51.5, lon=0.045, capacity_kg=100.0),
    ]
    orders = [
        make_order(id=1, code="A", lat=51.5, lon=-0.035, weight_kg=80, priority=5),
        make_order(id=2, code="B", lat=51.5, lon=-0.093, weight_kg=80, priority=1),
    ]
    return trucks, orders


def test_hungarian_total_distance_better_than_greedy():
    trucks, orders = _hungarian_beats_greedy_setup()
    w = Weights()
    g = greedy.allocate(trucks, orders, w)
    h = hungarian.allocate(trucks, orders, w)
    assert g.metrics.assigned_count == 2
    assert h.metrics.assigned_count == 2
    assert h.metrics.total_distance_km < g.metrics.total_distance_km - 1.0


def test_capability_hard_constraint_blocks():
    """Order requiring 'refrigerated' is unassigned when no truck has it."""
    trucks = [make_truck(id=1, name="T1", capabilities=[])]
    orders = [make_order(id=1, code="O1", required_capabilities=["refrigerated"])]
    g = greedy.allocate(trucks, orders, Weights())
    h = hungarian.allocate(trucks, orders, Weights())
    assert g.metrics.unassigned_count == 1
    assert h.metrics.unassigned_count == 1
    assert 1 in g.unassigned_order_ids
    assert 1 in h.unassigned_order_ids


def test_capability_match_assigns():
    trucks = [
        make_truck(id=1, name="T1", capabilities=[]),
        make_truck(id=2, name="T2", capabilities=["refrigerated"]),
    ]
    orders = [make_order(id=1, code="O1", required_capabilities=["refrigerated"])]
    g = greedy.allocate(trucks, orders, Weights())
    h = hungarian.allocate(trucks, orders, Weights())
    assert g.metrics.assigned_count == 1
    assert h.metrics.assigned_count == 1
    # Both should pick T2.
    assert g.explanations[0].chosen_truck_id == 2
    assert h.explanations[0].chosen_truck_id == 2


def test_explanations_include_runner_up_when_multiple_feasible():
    trucks = [
        make_truck(id=1, name="T1", lat=51.50, lon=-0.10),
        make_truck(id=2, name="T2", lat=51.51, lon=-0.09),
    ]
    orders = [make_order(id=1, code="O1", lat=51.505, lon=-0.095)]
    g = greedy.allocate(trucks, orders, Weights())
    assert g.explanations[0].runner_up_truck_id is not None


def test_multiple_orders_share_truck_when_capacity_allows():
    trucks = [make_truck(id=1, name="T1", capacity_kg=1000.0)]
    orders = [
        make_order(id=1, code="O1", lat=51.51, lon=-0.10, weight_kg=100),
        make_order(id=2, code="O2", lat=51.52, lon=-0.10, weight_kg=100),
    ]
    g = greedy.allocate(trucks, orders, Weights())
    assert g.metrics.assigned_count == 2
    assert len(g.routes[0].stops) == 2
