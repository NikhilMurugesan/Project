// Left-hand control panel: scenario picker, new-scenario form, the three
// weight sliders, and the buttons that fire off algorithm runs.
import { useEffect, useState } from 'react';
import type { Weights } from '../types';

interface Props {
  scenarios: { id: number; name: string }[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onCreate: (size: 'small' | 'medium' | 'large', seed: number) => void;
  onDelete: (id: number) => void;
  weights: Weights;
  onWeightsChange: (w: Weights) => void;
  onRun: (algorithm: 'greedy' | 'hungarian') => void;
  onCompare: () => void;
  running: boolean;
}

export default function Sidebar({
  scenarios, selectedId, onSelect, onCreate, onDelete,
  weights, onWeightsChange, onRun, onCompare, running,
}: Props) {
  const [size, setSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [seed, setSeed] = useState(42);

  return (
    <div className="sidebar">
      <h2>Allocation Engine</h2>

      <h3>Scenario</h3>
      <select
        value={selectedId ?? ''}
        onChange={(e) => onSelect(Number(e.target.value))}
      >
        <option value="" disabled>— pick —</option>
        {scenarios.map((s) => (
          <option key={s.id} value={s.id}>{s.id}. {s.name}</option>
        ))}
      </select>

      <div className="row" style={{ marginTop: 8 }}>
        <select value={size} onChange={(e) => setSize(e.target.value as any)}>
          <option value="small">small</option>
          <option value="medium">medium</option>
          <option value="large">large</option>
        </select>
        <input
          type="number"
          value={seed}
          onChange={(e) => setSeed(Number(e.target.value))}
          title="seed"
        />
      </div>
      <div className="row">
        <button onClick={() => onCreate(size, seed)}>+ New scenario</button>
        <button
          onClick={() => selectedId && onDelete(selectedId)}
          disabled={!selectedId}
          title="Delete selected scenario"
        >
          Delete
        </button>
      </div>

      <h3 style={{ marginTop: 16 }}>Weights</h3>
      <WeightSlider label="Distance" value={weights.distance}
        onChange={(v) => onWeightsChange({ ...weights, distance: v })} />
      <WeightSlider label="Priority" value={weights.priority}
        onChange={(v) => onWeightsChange({ ...weights, priority: v })} />
      <WeightSlider label="Workload balance" value={weights.workload}
        onChange={(v) => onWeightsChange({ ...weights, workload: v })} />

      <h3 style={{ marginTop: 16 }}>Run</h3>
      <div className="row">
        <button onClick={() => onRun('greedy')} disabled={!selectedId || running}>Greedy</button>
        <button onClick={() => onRun('hungarian')} disabled={!selectedId || running}>Hungarian</button>
      </div>
      <button
        className="primary"
        onClick={onCompare}
        disabled={!selectedId || running}
        style={{ width: '100%' }}
      >
        Compare both
      </button>
    </div>
  );
}

function WeightSlider({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void; }) {
  return (
    <div>
      <label>{label}: <strong>{value.toFixed(2)}</strong></label>
      <input
        type="range" min={0} max={2} step={0.05}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}
