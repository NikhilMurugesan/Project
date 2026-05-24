# Resource Allocation Engine — Delivery Fleet

This is my take on the resource allocation problem. I picked the **delivery fleet** angle:
a bunch of trucks sitting at depots, a bunch of orders coming in, and the system has to
figure out which truck should do which order. Nothing fancier than that.

It runs entirely on your laptop. No API keys, no paid services. The backend is FastAPI +
SQLite, the frontend is React + Vite, and the map uses Leaflet with OpenStreetMap tiles.

Two algorithms are implemented so you can compare them: a **greedy** one that handles
orders one at a time, and a **Hungarian** one that looks at everything at once. There's a
button in the UI to run both and put the results side by side.

```
React (Vite) ──HTTP──▶ FastAPI ──▶ SQLite
                         │
                         ├── algorithms/greedy
                         ├── algorithms/hungarian
                         └── core/router (cheapest-insertion)
```

## What's in the repo

```
backend/
  app/
    main.py              FastAPI endpoints
    models.py            SQLAlchemy tables (Truck, Order, Scenario)
    schemas.py           Pydantic request/response shapes
    db.py                DB engine + session
    seed.py              Generates demo scenarios
    core/
      distance.py        Haversine + travel time
      router.py          Per-truck route + cheapest-insertion logic
      scoring.py         Soft-constraint scoring
    algorithms/
      base.py            Helpers shared by both algorithms
      greedy.py          The greedy strategy
      hungarian.py       The Hungarian (batch) strategy
  tests/                 pytest suite
  requirements.txt
frontend/
  src/
    App.tsx
    api/client.ts
    components/
      Sidebar.tsx
      MapView.tsx
      SvgView.tsx
      MetricsPanel.tsx
      ComparePanel.tsx
      AssignmentTable.tsx
  package.json
README.md
ANALYSIS.md
```

## What you need

- Python 3.11 or newer
- Node 18 or newer (with npm)

That's it. Everything else gets installed by the steps below.

## Running it

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The first time it boots, it creates an `allocation.db` SQLite file in the working
directory and seeds three demo scenarios: `small-demo`, `medium-demo`, `large-demo`.
You can browse the auto-generated API docs at <http://localhost:8000/docs>.

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Then go to <http://localhost:5173>. Vite proxies `/api/*` to port 8000, so the two
sides talk to each other without any CORS setup on your end.

## Using the UI

1. Pick one of the seeded scenarios from the sidebar, or click **+ New scenario** and
   pick a size and a seed.
2. Optionally drag the three sliders to change how much the algorithms care about
   distance, priority, and workload balance.
3. Hit **Greedy**, **Hungarian**, or **Compare both**.
4. Switch between the **Map (OSM)** view and the **Schematic SVG** view — they show
   the same plan in two different ways.
5. Hover any row in the assignments table to see *why* a particular truck got picked
   (chosen truck, its score, what the runner-up was, and the extra km it cost).
6. When comparing, the right-hand panel shows both algorithms next to each other with
   little "best" badges on whichever metric won. You can swap the map between the two
   plans with **Show Greedy / Show Hungarian**.

## Tests

### Backend
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

The interesting ones:
- `test_algorithms.py::test_hungarian_total_distance_better_than_greedy` — a small
  hand-built case where greedy grabs the cheap truck for a high-priority order and
  ends up forcing the second order onto a long leg. Greedy ≈ 14.5 km total,
  Hungarian ≈ 5.5 km. Same constraints, same scoring, different selection logic.
- `test_router.py` — covers cheapest-insertion under capability, capacity, and
  time-window limits, including multi-stop ordering.
- `test_api.py` — full round-trip through `TestClient`: create scenario → allocate →
  compare.

### Frontend
```powershell
cd frontend
npm test
```

## Data model

| Thing       | Fields                                                                                  |
|-------------|------------------------------------------------------------------------------------------|
| **Truck**   | name, depot lat/lon, capacity_kg, capabilities, shift_start/end, avg_speed_kmh, cost_per_km |
| **Order**   | code, lat/lon, weight_kg, required_capabilities, time window, priority (1–5), SLA deadline |
| **Scenario**| a named bundle of trucks + orders                                                        |

Times are stored as minutes since midnight, so an 08:00–18:00 shift is just `480–1080`.
Makes the arithmetic easy and skips any timezone headaches.

## The two algorithms in a sentence each

**Greedy.** Sort the orders by priority (then by SLA deadline), and for each one in
turn, ask every truck "how much extra would this cost you?" Pick the truck with the
best score. Move on. Cheap, fast, and pretty much how a human dispatcher would do it.

**Hungarian.** Build a full `orders × trucks` cost matrix using the same cheapest-insertion
numbers, hand it to `scipy.optimize.linear_sum_assignment`, and commit the resulting
1-to-1 assignment. If there are more orders than trucks, repeat with what's left until
nothing changes. The win here is that it looks at everything at once instead of one
order at a time.

Both algorithms share the same router, the same feasibility checks, and the same
scoring function. The only thing that differs is *how they pick*.

## Constraints

| Kind | Constraint            | Where it's enforced                                    |
|------|-----------------------|--------------------------------------------------------|
| Hard | Capability match      | the order's required tags must be a subset of the truck's |
| Hard | Capacity              | total load on the route can't exceed `capacity_kg`     |
| Hard | Time window           | arrival must fall inside the order's `[tw_start, tw_end]` |
| Hard | SLA                   | arrival has to be at or before the deadline            |
| Hard | Shift end             | every departure has to be before the driver's shift ends |
| Soft | Distance              | extra km from cheapest-insertion, weighted             |
| Soft | Priority              | high-priority orders get a score bonus                 |
| Soft | Workload balance      | trucks doing more than the fleet average get a penalty |

## Metrics the API returns

For each run: `total_distance_km`, `total_cost`, `assigned_count`, `unassigned_count`,
`sla_met_pct`, `capacity_utilization_pct`, `workload_stddev_km`, `runtime_ms`.

## A few things to know about scope

- **Distance** is straight-line (Haversine) times an `avg_speed_kmh` per truck. A real
  product would use a road network — OSRM, Valhalla, or a paid matrix API. The
  algorithm code wouldn't change; only `core/distance.py` would.
- **Routing** uses cheapest-insertion, not a proper VRP solver. That's enough to make
  the greedy-vs-Hungarian comparison meaningful without dragging in OR-Tools.
- The **Hungarian** wrapper runs in rounds because typically there are way more orders
  than trucks. Each round is optimal on its own; across rounds it's a heuristic. There's
  more on this in [`ANALYSIS.md`](ANALYSIS.md).
