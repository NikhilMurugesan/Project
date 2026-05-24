# Pydantic models that describe what the API sends and receives. These also
# double as the in-memory types that the algorithms work with on the way
# back out, so changing one of these usually means touching a frontend
# component too.
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class TruckOut(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    capacity_kg: float
    capabilities: list[str]
    shift_start: int
    shift_end: int
    avg_speed_kmh: float
    cost_per_km: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    code: str
    lat: float
    lon: float
    weight_kg: float
    required_capabilities: list[str]
    tw_start: int
    tw_end: int
    service_minutes: int
    priority: int
    sla_deadline: int

    class Config:
        from_attributes = True


class ScenarioOut(BaseModel):
    id: int
    name: str
    trucks: list[TruckOut]
    orders: list[OrderOut]

    class Config:
        from_attributes = True


class Weights(BaseModel):
    distance: float = 1.0
    priority: float = 0.5
    workload: float = 0.3


class RouteStop(BaseModel):
    order_id: int
    order_code: str
    sequence: int
    arrival_minute: int
    departure_minute: int
    distance_km_from_prev: float


class TruckRoute(BaseModel):
    truck_id: int
    truck_name: str
    stops: list[RouteStop]
    total_distance_km: float
    total_load_kg: float


class AssignmentExplanation(BaseModel):
    order_id: int
    order_code: str
    chosen_truck_id: Optional[int]
    chosen_truck_name: Optional[str]
    score: Optional[float]
    reasons: list[str]
    runner_up_truck_id: Optional[int] = None
    runner_up_truck_name: Optional[str] = None
    runner_up_score: Optional[float] = None


class Metrics(BaseModel):
    algorithm: str
    total_distance_km: float
    total_cost: float
    assigned_count: int
    unassigned_count: int
    sla_met_pct: float
    capacity_utilization_pct: float
    workload_stddev_km: float
    runtime_ms: float


class AllocationResult(BaseModel):
    algorithm: str
    metrics: Metrics
    routes: list[TruckRoute]
    unassigned_order_ids: list[int]
    explanations: list[AssignmentExplanation]


class AllocateRequest(BaseModel):
    algorithm: str = Field(pattern="^(greedy|hungarian)$")
    weights: Weights = Weights()


class CompareResult(BaseModel):
    greedy: AllocationResult
    hungarian: AllocationResult


class CreateScenarioRequest(BaseModel):
    size: str = Field(default="medium", pattern="^(small|medium|large)$")
    seed: int = 42
    name: Optional[str] = None
