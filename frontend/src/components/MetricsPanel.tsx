// Compact list of headline numbers for one allocation result. Used both
// in single-run mode and (twice over) inside the compare panel.
import type { Metrics } from '../types';

interface Props {
  metrics: Metrics | null;
  title?: string;
}

export default function MetricsPanel({ metrics, title }: Props) {
  if (!metrics) return <div className="muted">No allocation yet.</div>;
  return (
    <div>
      {title && <h3>{title}</h3>}
      <Metric name="Total distance" value={`${metrics.total_distance_km.toFixed(1)} km`} />
      <Metric name="Total cost" value={metrics.total_cost.toFixed(2)} />
      <Metric name="Assigned" value={`${metrics.assigned_count}`} />
      <Metric name="Unassigned" value={`${metrics.unassigned_count}`}
        cls={metrics.unassigned_count === 0 ? 'good' : 'bad'} />
      <Metric name="SLA met" value={`${metrics.sla_met_pct.toFixed(1)}%`}
        cls={metrics.sla_met_pct >= 95 ? 'good' : metrics.sla_met_pct >= 80 ? '' : 'bad'} />
      <Metric name="Capacity util." value={`${metrics.capacity_utilization_pct.toFixed(1)}%`} />
      <Metric name="Workload σ (km)" value={metrics.workload_stddev_km.toFixed(2)} />
      <Metric name="Runtime" value={`${metrics.runtime_ms.toFixed(1)} ms`} />
    </div>
  );
}

function Metric({ name, value, cls }: { name: string; value: string; cls?: string }) {
  return (
    <div className="metric">
      <span className="metric-name">{name}</span>
      <span className={`metric-value ${cls ?? ''}`}>{value}</span>
    </div>
  );
}
