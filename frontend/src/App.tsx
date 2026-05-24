// Top-level component. Holds all the state (selected scenario, weights,
// last result, compare result, which algorithm to show on the map) and
// hands chunks of it down to the smaller components. Kept deliberately
// flat -- no Redux, no context -- because the app is small enough that
// useState is just easier to follow.
import { useEffect, useMemo, useState } from 'react';
import * as api from './api/client';
import type {
  AllocationResult,
  CompareResult,
  Scenario,
  Weights,
} from './types';
import Sidebar from './components/Sidebar';
import MapView from './components/MapView';
import SvgView from './components/SvgView';
import MetricsPanel from './components/MetricsPanel';
import ComparePanel from './components/ComparePanel';
import AssignmentTable from './components/AssignmentTable';

export default function App() {
  const [scenarios, setScenarios] = useState<{ id: number; name: string }[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [view, setView] = useState<'map' | 'svg'>('map');
  const [weights, setWeights] = useState<Weights>({ distance: 1, priority: 0.5, workload: 0.3 });
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<AllocationResult | null>(null);
  const [compare, setCompare] = useState<CompareResult | null>(null);
  const [shownAlgo, setShownAlgo] = useState<'greedy' | 'hungarian'>('greedy');
  const [error, setError] = useState<string | null>(null);

  // Load scenarios on mount.
  useEffect(() => {
    api.listScenarios().then((rows) => {
      setScenarios(rows);
      if (rows.length > 0 && selectedId == null) {
        setSelectedId(rows[0].id);
      }
    }).catch((e) => setError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load scenario detail when selectedId changes.
  useEffect(() => {
    if (selectedId == null) return;
    setResult(null);
    setCompare(null);
    api.getScenario(selectedId).then(setScenario).catch((e) => setError(String(e)));
  }, [selectedId]);

  const handleCreate = async (size: 'small' | 'medium' | 'large', seed: number) => {
    try {
      const s = await api.createScenario(size, seed);
      const rows = await api.listScenarios();
      setScenarios(rows);
      setSelectedId(s.id);
    } catch (e) { setError(String(e)); }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteScenario(id);
      const rows = await api.listScenarios();
      setScenarios(rows);
      setSelectedId(rows.length ? rows[0].id : null);
    } catch (e) { setError(String(e)); }
  };

  const handleRun = async (algorithm: 'greedy' | 'hungarian') => {
    if (selectedId == null) return;
    setRunning(true);
    setCompare(null);
    try {
      const r = await api.allocate(selectedId, algorithm, weights);
      setResult(r);
      setShownAlgo(algorithm);
    } catch (e) { setError(String(e)); }
    setRunning(false);
  };

  const handleCompare = async () => {
    if (selectedId == null) return;
    setRunning(true);
    try {
      const c = await api.compare(selectedId, weights);
      setCompare(c);
      setResult(c[shownAlgo]);
    } catch (e) { setError(String(e)); }
    setRunning(false);
  };

  const shownResult: AllocationResult | null = useMemo(() => {
    if (compare) return compare[shownAlgo];
    return result;
  }, [compare, result, shownAlgo]);

  return (
    <div className="app">
      <Sidebar
        scenarios={scenarios}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onCreate={handleCreate}
        onDelete={handleDelete}
        weights={weights}
        onWeightsChange={setWeights}
        onRun={handleRun}
        onCompare={handleCompare}
        running={running}
      />

      <div className="center">
        <div className="viewToggle">
          <button
            className={view === 'map' ? 'primary' : ''}
            onClick={() => setView('map')}
          >Map (OSM)</button>
          <button
            className={view === 'svg' ? 'primary' : ''}
            onClick={() => setView('svg')}
          >Schematic SVG</button>
          {compare && (
            <span style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
              <button
                className={shownAlgo === 'greedy' ? 'primary' : ''}
                onClick={() => setShownAlgo('greedy')}
              >Show Greedy</button>
              <button
                className={shownAlgo === 'hungarian' ? 'primary' : ''}
                onClick={() => setShownAlgo('hungarian')}
              >Show Hungarian</button>
            </span>
          )}
          {error && <span style={{ color: 'var(--bad)', marginLeft: 12 }}>{error}</span>}
        </div>
        <div className="viewContent">
          {scenario && view === 'map' && (
            <MapView scenario={scenario} result={shownResult} />
          )}
          {scenario && view === 'svg' && (
            <SvgView scenario={scenario} result={shownResult} />
          )}
          {!scenario && <div style={{ padding: 20 }}>Select or create a scenario.</div>}
        </div>
      </div>

      <div className="right">
        {compare ? (
          <ComparePanel compare={compare} />
        ) : (
          <MetricsPanel metrics={result?.metrics ?? null} title={result?.algorithm} />
        )}
        {shownResult && <AssignmentTable result={shownResult} />}
      </div>
    </div>
  );
}
