import { useState } from 'react';
import type { AllocationResult } from '../types';
import { colorForTruck, minutesToClock } from '../utils';

interface Props { result: AllocationResult; }

// One row per (truck, stop). Hovering shows the explanation text the
// backend produced -- this is where the "why this truck?" answer lives.
export default function AssignmentTable({ result }: Props) {
  const [hover, setHover] = useState<number | null>(null);

  // Flatten each truck's stop list so we can render it as a single table.
  const rows = result.routes.flatMap((r) =>
    r.stops.map((s) => ({
      truck_id: r.truck_id,
      truck_name: r.truck_name,
      ...s,
    }))
  );

  const expById = Object.fromEntries(result.explanations.map((e) => [e.order_id, e]));

  return (
    <div style={{ position: 'relative' }}>
      <h3>Assignments ({rows.length})</h3>
      <table className="table">
        <thead>
          <tr>
            <th>Order</th><th>Truck</th><th>Seq</th><th>ETA</th><th>Δkm</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={r.order_id}
              onMouseEnter={() => setHover(r.order_id)}
              onMouseLeave={() => setHover(null)}
            >
              <td>{r.order_code}</td>
              <td>
                <span style={{ color: colorForTruck(r.truck_id), fontWeight: 600 }}>{r.truck_name}</span>
              </td>
              <td>{r.sequence + 1}</td>
              <td>{minutesToClock(r.arrival_minute)}</td>
              <td>{r.distance_km_from_prev.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {result.unassigned_order_ids.length > 0 && (
        <div style={{ marginTop: 8, color: 'var(--bad)', fontSize: 12 }}>
          Unassigned: {result.unassigned_order_ids.join(', ')}
        </div>
      )}

      {hover != null && expById[hover] && (
        <div className="tooltip" style={{ top: 40, right: 0 }}>
          <strong>Order {expById[hover].order_code}</strong>
          <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
            {expById[hover].reasons.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
