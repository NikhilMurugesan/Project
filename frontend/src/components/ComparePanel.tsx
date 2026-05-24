// Side-by-side metrics for Greedy vs Hungarian. The little "best" pills
// next to a metric just compare the two numbers -- they're not claiming
// any kind of statistical significance.
import type { CompareResult } from '../types';

interface Props { compare: CompareResult; }

export default function ComparePanel({ compare }: Props) {
  const g = compare.greedy.metrics;
  const h = compare.hungarian.metrics;
  return (
    <div>
      <h3>Algorithm Comparison</h3>
      <div className="compare-grid">
        <Col title="Greedy" m={compare.greedy.metrics} winnerDist={g.total_distance_km <= h.total_distance_km} winnerSla={g.sla_met_pct >= h.sla_met_pct} winnerLoad={g.workload_stddev_km <= h.workload_stddev_km} />
        <Col title="Hungarian" m={compare.hungarian.metrics} winnerDist={h.total_distance_km < g.total_distance_km} winnerSla={h.sla_met_pct > g.sla_met_pct} winnerLoad={h.workload_stddev_km < g.workload_stddev_km} />
      </div>
      <p style={{ marginTop: 12, color: 'var(--muted)', fontSize: 12 }}>
        Greedy processes orders sequentially. Hungarian picks an optimal one-to-one
        assignment per round, then re-plans.
      </p>
    </div>
  );
}

function Col({ title, m, winnerDist, winnerSla, winnerLoad }: any) {
  return (
    <div className="compare-col">
      <h3>{title}</h3>
      <div className="metric">
        <span className="metric-name">Distance</span>
        <span className="metric-value">
          {m.total_distance_km.toFixed(1)} km {winnerDist && <span className="pill good">best</span>}
        </span>
      </div>
      <div className="metric">
        <span className="metric-name">Cost</span>
        <span className="metric-value">{m.total_cost.toFixed(2)}</span>
      </div>
      <div className="metric">
        <span className="metric-name">Assigned</span>
        <span className="metric-value">{m.assigned_count}</span>
      </div>
      <div className="metric">
        <span className="metric-name">Unassigned</span>
        <span className={`metric-value ${m.unassigned_count === 0 ? 'good' : 'bad'}`}>{m.unassigned_count}</span>
      </div>
      <div className="metric">
        <span className="metric-name">SLA met</span>
        <span className="metric-value">
          {m.sla_met_pct.toFixed(1)}% {winnerSla && <span className="pill good">best</span>}
        </span>
      </div>
      <div className="metric">
        <span className="metric-name">Workload σ</span>
        <span className="metric-value">
          {m.workload_stddev_km.toFixed(2)} {winnerLoad && <span className="pill good">best</span>}
        </span>
      </div>
      <div className="metric">
        <span className="metric-name">Runtime</span>
        <span className="metric-value">{m.runtime_ms.toFixed(1)} ms</span>
      </div>
    </div>
  );
}
