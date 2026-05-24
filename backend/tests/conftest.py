"""Shared pytest fixtures: in-memory DB, sample trucks/orders."""
from __future__ import annotations

import os
import sys
import tempfile

# Ensure repo root is on path so `from app...` works.
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Use a temp-file SQLite shared across the whole test run. We don't use
# ":memory:" because each new connection to it gets its own private DB,
# which breaks the multi-request API tests.
_DB_FD, _DB_PATH = tempfile.mkstemp(suffix=".db", prefix="alloc_test_")
os.close(_DB_FD)
os.environ.setdefault("ALLOCATION_DB_URL", f"sqlite:///{_DB_PATH}")

import pytest  # noqa: E402

from app.db import Base, engine, SessionLocal  # noqa: E402
from app import models  # noqa: E402


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def make_truck(scenario_id=1, **kwargs):
    base = dict(
        scenario_id=scenario_id,
        name="T",
        lat=51.5,
        lon=-0.1,
        capacity_kg=1000.0,
        capabilities=[],
        shift_start=8 * 60,
        shift_end=18 * 60,
        avg_speed_kmh=40.0,
        cost_per_km=1.0,
    )
    base.update(kwargs)
    return models.Truck(**base)


def make_order(scenario_id=1, **kwargs):
    base = dict(
        scenario_id=scenario_id,
        code="O",
        lat=51.51,
        lon=-0.11,
        weight_kg=100.0,
        required_capabilities=[],
        tw_start=9 * 60,
        tw_end=17 * 60,
        service_minutes=10,
        priority=3,
        sla_deadline=17 * 60,
    )
    base.update(kwargs)
    return models.Order(**base)
