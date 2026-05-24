# Demo scenario generator. Deterministic for a given (size, seed) pair so
# that the UI's compare-mode always gives reproducible numbers and the
# adversarial unit tests stay reliable.
from __future__ import annotations

import random
from typing import Optional

from sqlalchemy.orm import Session

from . import models


CAPABILITIES_POOL = ["refrigerated", "hazmat", "oversized", "fragile"]

# Greater-London-ish bounding box. Picked because Leaflet's default OSM
# tiles look good there and the centre coords are easy to remember. Has no
# meaning beyond "makes the demo map look like a real city".
CENTER_LAT = 51.5074
CENTER_LON = -0.1278
SPREAD_LAT = 0.18
SPREAD_LON = 0.30


def _sizes(size: str) -> tuple[int, int]:
    return {
        "small": (4, 10),
        "medium": (8, 25),
        "large": (15, 60),
    }[size]


def create_scenario(
    db: Session, size: str = "medium", seed: int = 42, name: Optional[str] = None
) -> models.Scenario:
    n_trucks, n_orders = _sizes(size)
    rng = random.Random(seed)

    scenario = models.Scenario(name=name or f"{size}-seed{seed}")
    db.add(scenario)
    db.flush()

    for i in range(n_trucks):
        caps_pool_size = rng.choice([0, 1, 1, 2])
        caps = rng.sample(CAPABILITIES_POOL, k=caps_pool_size)
        truck = models.Truck(
            scenario_id=scenario.id,
            name=f"T{i + 1}",
            lat=CENTER_LAT + (rng.random() - 0.5) * SPREAD_LAT * 0.6,
            lon=CENTER_LON + (rng.random() - 0.5) * SPREAD_LON * 0.6,
            capacity_kg=rng.choice([800, 1200, 1500, 2000]),
            capabilities=caps,
            shift_start=8 * 60,
            shift_end=18 * 60,
            avg_speed_kmh=rng.choice([30, 35, 40, 45]),
            cost_per_km=round(rng.uniform(0.8, 1.4), 2),
        )
        db.add(truck)

    for i in range(n_orders):
        require_caps = []
        if rng.random() < 0.35:
            require_caps.append(rng.choice(CAPABILITIES_POOL))
        tw_start = rng.choice([8, 9, 10, 11, 12, 13, 14]) * 60
        tw_end = tw_start + rng.choice([90, 120, 180, 240])
        order = models.Order(
            scenario_id=scenario.id,
            code=f"O{i + 1:03d}",
            lat=CENTER_LAT + (rng.random() - 0.5) * SPREAD_LAT,
            lon=CENTER_LON + (rng.random() - 0.5) * SPREAD_LON,
            weight_kg=round(rng.uniform(20, 350), 1),
            required_capabilities=require_caps,
            tw_start=tw_start,
            tw_end=tw_end,
            service_minutes=rng.choice([5, 10, 15, 20]),
            priority=rng.choices([1, 2, 3, 4, 5], weights=[1, 2, 4, 2, 1])[0],
            sla_deadline=tw_end,
        )
        db.add(order)

    db.commit()
    db.refresh(scenario)
    return scenario
