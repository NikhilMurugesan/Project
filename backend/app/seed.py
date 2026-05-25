# Three hand-crafted demo scenarios. Each one is designed to stress a
# different part of the allocator so the greedy-vs-Hungarian comparison
# tells a clear story:
#
#   1) Balanced       -- trucks and orders evenly spread, mild constraints.
#                        Both algorithms should look very similar -- this
#                        is the "sanity check" scenario.
#
#   2) Priority crunch -- tight SLAs on a few high-priority orders plus
#                         capability requirements (refrigerated, hazmat).
#                         Bumping the priority weight should change the
#                         outcome here in obvious ways.
#
#   3) Workload stress -- one truck sits inside a big central cluster of
#                         orders; the other trucks are at the corners.
#                         Greedy tends to dump everything onto the central
#                         truck. Hungarian + the workload-balance weight
#                         spreads things out.
#
# Everything is fully deterministic: no randomness, no seeds. Re-running
# `seed_defaults` always produces the same three scenarios.
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from . import models


# ---------- scenario definitions ----------

_SCENARIOS = {
    "balanced": {
        "name": "1 · Balanced",
        "trucks": [
            # (name, lat, lon, capacity, capabilities, shift_start, shift_end, speed, cost/km)
            ("T1", 51.5150, -0.1400, 1500, [], 8 * 60, 18 * 60, 40, 1.00),
            ("T2", 51.5000, -0.1100, 1500, [], 8 * 60, 18 * 60, 40, 1.00),
            ("T3", 51.5250, -0.0800, 1500, [], 8 * 60, 18 * 60, 40, 1.00),
        ],
        "orders": [
            # (code, lat, lon, weight, required_caps, tw_start_h, tw_end_h, service_min, priority)
            ("O01", 51.5200, -0.1500, 120, [], 9, 12, 10, 3),
            ("O02", 51.5100, -0.1000, 80,  [], 9, 13, 10, 4),
            ("O03", 51.5300, -0.0900, 150, [], 10, 15, 10, 2),
            ("O04", 51.4950, -0.1200, 200, [], 9, 14, 10, 3),
            ("O05", 51.5050, -0.1350, 100, [], 11, 16, 10, 4),
            ("O06", 51.5220, -0.0700, 90,  [], 10, 17, 10, 2),
            ("O07", 51.4980, -0.1050, 130, [], 9, 15, 10, 3),
            ("O08", 51.5150, -0.1150, 75,  [], 8, 10, 10, 5),  # tight SLA
        ],
    },
    "priority": {
        "name": "2 · Priority crunch",
        "trucks": [
            ("T1", 51.5300, -0.1500, 1000, ["refrigerated"], 7 * 60, 18 * 60, 35, 1.20),
            ("T2", 51.4700, -0.1500, 1000, [], 7 * 60, 18 * 60, 35, 1.20),
            ("T3", 51.5300, -0.0800, 1000, ["refrigerated", "hazmat"], 7 * 60, 18 * 60, 35, 1.20),
            ("T4", 51.4700, -0.0800, 1000, ["hazmat"], 7 * 60, 18 * 60, 35, 1.20),
        ],
        "orders": [
            # tight, high-priority orders first
            ("O01", 51.5000, -0.1300, 200, [], 7, 10.5, 10, 5),
            ("O02", 51.5200, -0.1200, 180, [], 7, 10.5, 10, 5),
            ("O03", 51.4900, -0.1400, 220, ["refrigerated"], 7, 11, 10, 5),
            ("O04", 51.5100, -0.0900, 150, [], 8, 13, 10, 4),
            ("O05", 51.5000, -0.0750, 100, ["refrigerated"], 8, 14, 10, 4),
            ("O06", 51.4850, -0.1100, 130, [], 9, 15, 10, 3),
            ("O07", 51.5250, -0.1050, 110, [], 9, 16, 10, 3),
            ("O08", 51.4950, -0.1550, 90,  ["hazmat"], 10, 17, 10, 2),
            ("O09", 51.5150, -0.1350, 160, [], 10, 17, 10, 2),
            ("O10", 51.5350, -0.1000, 140, [], 10, 17, 10, 3),
            ("O11", 51.4750, -0.0950, 170, [], 11, 18, 10, 1),
            ("O12", 51.5150, -0.0820, 100, [], 8, 12, 10, 4),
        ],
    },
    "workload": {
        "name": "3 · Workload stress",
        "trucks": [
            # T1 sits inside the central order cluster -- greedy will pile
            # things onto it unless the workload weight kicks in.
            ("T1", 51.5100, -0.1250, 1800, [], 8 * 60, 18 * 60, 40, 1.00),
            ("T2", 51.5600, -0.1800, 1200, [], 8 * 60, 18 * 60, 40, 1.00),
            ("T3", 51.4600, -0.1800, 1200, [], 8 * 60, 18 * 60, 40, 1.00),
            ("T4", 51.5600, -0.0600, 1200, [], 8 * 60, 18 * 60, 40, 1.00),
            ("T5", 51.4600, -0.0600, 1200, [], 8 * 60, 18 * 60, 40, 1.00),
        ],
        "orders": [
            # central cluster -- 12 orders right next to T1
            ("O01", 51.5100, -0.1200, 120, [], 8, 16, 10, 3),
            ("O02", 51.5150, -0.1250, 100, [], 8, 16, 10, 3),
            ("O03", 51.5080, -0.1300, 140, [], 8, 16, 10, 2),
            ("O04", 51.5120, -0.1150, 130, [], 8, 16, 10, 3),
            ("O05", 51.5050, -0.1180, 150, [], 8, 16, 10, 2),
            ("O06", 51.5180, -0.1100, 110, [], 8, 14, 10, 4),
            ("O07", 51.5020, -0.1280, 160, [], 8, 16, 10, 3),
            ("O08", 51.5150, -0.1350, 170, [], 8, 16, 10, 2),
            ("O09", 51.5200, -0.1220, 180, [], 8, 16, 10, 3),
            ("O10", 51.4980, -0.1150, 90,  [], 8, 16, 10, 3),
            ("O11", 51.5120, -0.1080, 130, [], 8, 14, 10, 4),
            ("O12", 51.5050, -0.1350, 120, [], 8, 16, 10, 3),
            # corner orders -- one near each outer truck
            ("O13", 51.5550, -0.1750, 100, [], 8, 13, 10, 4),  # near T2
            ("O14", 51.4650, -0.1750, 120, [], 8, 13, 10, 4),  # near T3
            ("O15", 51.5550, -0.0650, 110, [], 8, 13, 10, 4),  # near T4
            ("O16", 51.4650, -0.0650, 140, [], 8, 13, 10, 4),  # near T5
            ("O17", 51.5450, -0.0900, 130, [], 9, 16, 10, 3),
            ("O18", 51.4750, -0.1400, 150, [], 9, 16, 10, 3),
        ],
    },
}

# Mirror the old "small/medium/large" knob onto the three presets so the
# existing POST /api/scenarios endpoint and the sidebar's "+ New scenario"
# button keep working without any frontend change.
_SIZE_ALIASES = {
    "small": "balanced",
    "medium": "priority",
    "large": "workload",
}


# ---------- builders ----------


def _build(db: Session, key: str, name_override: Optional[str] = None) -> models.Scenario:
    spec = _SCENARIOS[key]
    scenario = models.Scenario(name=name_override or spec["name"])
    db.add(scenario)
    db.flush()

    for (t_name, lat, lon, cap, caps, sh_start, sh_end, speed, cpk) in spec["trucks"]:
        db.add(
            models.Truck(
                scenario_id=scenario.id,
                name=t_name,
                lat=lat,
                lon=lon,
                capacity_kg=cap,
                capabilities=list(caps),
                shift_start=sh_start,
                shift_end=sh_end,
                avg_speed_kmh=speed,
                cost_per_km=cpk,
            )
        )

    for (code, lat, lon, weight, req_caps, tw_start_h, tw_end_h, svc, prio) in spec["orders"]:
        tw_start = int(tw_start_h * 60)
        tw_end = int(tw_end_h * 60)
        db.add(
            models.Order(
                scenario_id=scenario.id,
                code=code,
                lat=lat,
                lon=lon,
                weight_kg=weight,
                required_capabilities=list(req_caps),
                tw_start=tw_start,
                tw_end=tw_end,
                service_minutes=svc,
                priority=prio,
                sla_deadline=tw_end,
            )
        )

    db.commit()
    db.refresh(scenario)
    return scenario


def seed_defaults(db: Session) -> list[models.Scenario]:
    """Create the three preset scenarios. Called once on app startup if the
    DB is empty."""
    return [_build(db, key) for key in ("balanced", "priority", "workload")]


def create_scenario(
    db: Session,
    size: str = "medium",
    seed: int = 0,  # kept for API compatibility; ignored
    name: Optional[str] = None,
) -> models.Scenario:
    """Compatibility shim for the POST /api/scenarios endpoint and the
    sidebar's "+ New scenario" button.

    `size` maps onto one of the three static presets:
      small  -> Balanced
      medium -> Priority crunch
      large  -> Workload stress

    The `seed` argument is accepted but ignored -- the scenarios are
    deterministic by design.
    """
    key = _SIZE_ALIASES.get(size, "balanced")
    return _build(db, key, name_override=name)
