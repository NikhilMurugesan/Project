import { render, screen } from '@testing-library/react';
import MetricsPanel from '../components/MetricsPanel';

const m = {
  algorithm: 'greedy',
  total_distance_km: 42.5,
  total_cost: 50.25,
  assigned_count: 10,
  unassigned_count: 0,
  sla_met_pct: 100,
  capacity_utilization_pct: 55.5,
  workload_stddev_km: 3.2,
  runtime_ms: 12.3,
};

describe('MetricsPanel', () => {
  it('renders metric values', () => {
    render(<MetricsPanel metrics={m} title="greedy" />);
    expect(screen.getByText(/42.5 km/)).toBeInTheDocument();
    expect(screen.getByText(/100.0%/)).toBeInTheDocument();
    expect(screen.getByText(/12.3 ms/)).toBeInTheDocument();
  });

  it('renders empty state when no metrics', () => {
    render(<MetricsPanel metrics={null} />);
    expect(screen.getByText(/No allocation/)).toBeInTheDocument();
  });
});
