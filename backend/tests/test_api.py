"""End-to-end API tests via FastAPI TestClient."""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient  # noqa: E402

import pytest  # noqa: E402
from app.main import app  # noqa: E402
from app.db import Base, engine, init_db  # noqa: E402


client = TestClient(app)


@pytest.fixture(autouse=True)
def _fresh_db():
    # Other test modules' fixtures drop_all on teardown, so we recreate the
    # schema before each test in here to keep this module self-contained.
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_create_and_allocate_and_compare():
    r = client.post("/api/scenarios", json={"size": "small", "seed": 1, "name": "t"})
    assert r.status_code == 200, r.text
    sid = r.json()["id"]

    r = client.get(f"/api/scenarios/{sid}")
    assert r.status_code == 200
    payload = r.json()
    assert len(payload["trucks"]) > 0
    assert len(payload["orders"]) > 0

    r = client.post(
        f"/api/scenarios/{sid}/allocate",
        json={"algorithm": "greedy", "weights": {"distance": 1.0, "priority": 0.5, "workload": 0.3}},
    )
    assert r.status_code == 200, r.text
    g = r.json()
    assert g["algorithm"] == "greedy"
    assert "metrics" in g
    assert "routes" in g

    r = client.post(f"/api/scenarios/{sid}/compare", json={"algorithm": "greedy"})
    assert r.status_code == 200, r.text
    c = r.json()
    assert "greedy" in c and "hungarian" in c
    assert c["greedy"]["algorithm"] == "greedy"
    assert c["hungarian"]["algorithm"] == "hungarian"
