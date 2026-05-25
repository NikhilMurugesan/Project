// Left-hand control panel: scenario picker, the three weight sliders, and
// the buttons that fire off algorithm runs. The three demo scenarios are
// seeded on the backend -- nothing to create or delete from the UI.
import type { Weights } from '../types';

interface Props {
  scenarios: { id: number; name: string }[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  weights: Weights;
  onWeightsChange: (w: Weights) => void;
  onRun: (algorithm: 'greedy' | 'hungarian') => void;
  onCompare: () => void;
  running: boolean;
}

export default function Sidebar({
  scenarios, selectedId, onSelect,
  weights, onWeightsChange, onRun, onCompare, running,
}: Props) {
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
          <option key={s.id} value={s.id}>{s.name}</option>
        ))}
      </select>

      <h3 style={{ marginTop: 16 }}>Weights</h3>
      <p className="weight-hint">
        Each slider sets how much that factor counts when scoring a (truck, order) match.
        <strong> 0 = ignore</strong> · <strong>1 = normal</strong> · <strong>2 = double weight</strong>.
      </p>

      <WeightSlider
        label="Distance"
        value={weights.distance}
        onChange={(v) => onWeightsChange({ ...weights, distance: v })}
        hint="How much extra driving (km) hurts a match."
        lowEnd="Ignore distance · trucks may take long detours"
        highEnd="Punish detours · pick the closest truck"
      />
      <WeightSlider
        label="Priority"
        value={weights.priority}
        onChange={(v) => onWeightsChange({ ...weights, priority: v })}
        hint="How much a high-priority parcel is favoured over a low one."
        lowEnd="Treat all parcels equally"
        highEnd="Strongly prefer priority-5 parcels first"
      />
      <WeightSlider
        label="Workload balance"
        value={weights.workload}
        onChange={(v) => onWeightsChange({ ...weights, workload: v })}
        hint="How much a truck already busier than the fleet average is penalised."
        lowEnd="One truck may do most of the work"
        highEnd="Spread parcels evenly across trucks"
      />

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

function WeightSlider({
  label, value, onChange, hint, lowEnd, highEnd,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  hint: string;
  lowEnd: string;
  highEnd: string;
}) {
  return (
    <div className="weight-slider">
      <div className="weight-head">
        <span className="weight-name">{label}</span>
        <span className="weight-value">{value.toFixed(2)}</span>
      </div>
      <div className="weight-hint">{hint}</div>
      <input
        type="range" min={0} max={2} step={0.05}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={label}
      />
      <div className="weight-ends">
        <span>0 · {lowEnd}</span>
        <span>2 · {highEnd}</span>
      </div>
    </div>
  );
}
