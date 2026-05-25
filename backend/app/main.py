# FastAPI entrypoint. Endpoints are kept thin -- they just look stuff up
# in the DB, hand it to the algorithm, and return the result. The real
# logic lives in app/algorithms and app/core.
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, seed
from .algorithms import greedy, hungarian
from .db import SessionLocal, init_db
from .schemas import (
    AllocateRequest,
    AllocationResult,
    CompareResult,
    CreateScenarioRequest,
    ScenarioOut,
)


app = FastAPI(title="Resource Allocation Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _on_startup() -> None:
    init_db()
    # First-run friendliness: if the DB is empty, drop in the three
    # hand-crafted demo scenarios so the UI has something to show
    # immediately. See seed.py for what each one is designed to stress.
    db = SessionLocal()
    try:
        if db.query(models.Scenario).count() == 0:
            seed.seed_defaults(db)
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/scenarios")
def list_scenarios(db: Session = Depends(get_db)):
    rows = db.query(models.Scenario).order_by(models.Scenario.id.asc()).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@app.post("/api/scenarios", response_model=ScenarioOut)
def create_scenario(req: CreateScenarioRequest, db: Session = Depends(get_db)):
    scenario = seed.create_scenario(db, size=req.size, seed=req.seed, name=req.name)
    return scenario


@app.get("/api/scenarios/{scenario_id}", response_model=ScenarioOut)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scenario = db.get(models.Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario not found")
    return scenario


@app.delete("/api/scenarios/{scenario_id}")
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scenario = db.get(models.Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario not found")
    db.delete(scenario)
    db.commit()
    return {"deleted": scenario_id}


@app.post("/api/scenarios/{scenario_id}/allocate", response_model=AllocationResult)
def allocate(scenario_id: int, req: AllocateRequest, db: Session = Depends(get_db)):
    scenario = db.get(models.Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario not found")
    trucks = list(scenario.trucks)
    orders = list(scenario.orders)
    if req.algorithm == "greedy":
        return greedy.allocate(trucks, orders, req.weights)
    return hungarian.allocate(trucks, orders, req.weights)


@app.post("/api/scenarios/{scenario_id}/compare", response_model=CompareResult)
def compare(scenario_id: int, req: AllocateRequest, db: Session = Depends(get_db)):
    scenario = db.get(models.Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario not found")
    trucks = list(scenario.trucks)
    orders = list(scenario.orders)
    g = greedy.allocate(trucks, orders, req.weights)
    h = hungarian.allocate(trucks, orders, req.weights)
    return CompareResult(greedy=g, hungarian=h)
