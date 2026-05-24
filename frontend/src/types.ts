export interface Truck {
  id: number;
  name: string;
  lat: number;
  lon: number;
  capacity_kg: number;
  capabilities: string[];
  shift_start: number;
  shift_end: number;
  avg_speed_kmh: number;
  cost_per_km: number;
}

export interface Order {
  id: number;
  code: string;
  lat: number;
  lon: number;
  weight_kg: number;
  required_capabilities: string[];
  tw_start: number;
  tw_end: number;
  service_minutes: number;
  priority: number;
  sla_deadline: number;
}

export interface Scenario {
  id: number;
  name: string;
  trucks: Truck[];
  orders: Order[];
}

export interface Weights {
  distance: number;
  priority: number;
  workload: number;
}

export interface RouteStop {
  order_id: number;
  order_code: string;
  sequence: number;
  arrival_minute: number;
  departure_minute: number;
  distance_km_from_prev: number;
}

export interface TruckRoute {
  truck_id: number;
  truck_name: string;
  stops: RouteStop[];
  total_distance_km: number;
  total_load_kg: number;
}

export interface AssignmentExplanation {
  order_id: number;
  order_code: string;
  chosen_truck_id: number | null;
  chosen_truck_name: string | null;
  score: number | null;
  reasons: string[];
  runner_up_truck_id: number | null;
  runner_up_truck_name: string | null;
  runner_up_score: number | null;
}

export interface Metrics {
  algorithm: string;
  total_distance_km: number;
  total_cost: number;
  assigned_count: number;
  unassigned_count: number;
  sla_met_pct: number;
  capacity_utilization_pct: number;
  workload_stddev_km: number;
  runtime_ms: number;
}

export interface AllocationResult {
  algorithm: string;
  metrics: Metrics;
  routes: TruckRoute[];
  unassigned_order_ids: number[];
  explanations: AssignmentExplanation[];
}

export interface CompareResult {
  greedy: AllocationResult;
  hungarian: AllocationResult;
}
