// Schematic SVG view. Useful when you don't want the noise of the actual
// map -- it normalises lat/lon to a clean grid so the geometry of the
// routes is easier to eyeball.
import type { AllocationResult, Scenario } from '../types';
import { colorForTruck } from '../utils';

interface Props {
  scenario: Scenario;
  result: AllocationResult | null;
}

export default function SvgView({ scenario, result }: Props) {
  const W = 1000, H = 700, PAD = 40;

  const allLat = [
    ...scenario.trucks.map((t) => t.lat),
    ...scenario.orders.map((o) => o.lat),
  ];
  const allLon = [
    ...scenario.trucks.map((t) => t.lon),
    ...scenario.orders.map((o) => o.lon),
  ];
  const minLat = Math.min(...allLat), maxLat = Math.max(...allLat);
  const minLon = Math.min(...allLon), maxLon = Math.max(...allLon);
  const dLat = maxLat - minLat || 0.01;
  const dLon = maxLon - minLon || 0.01;

  const project = (lat: number, lon: number): [number, number] => [
    PAD + ((lon - minLon) / dLon) * (W - 2 * PAD),
    PAD + (1 - (lat - minLat) / dLat) * (H - 2 * PAD), // invert Y
  ];

  const truckById = Object.fromEntries(scenario.trucks.map((t) => [t.id, t]));
  const orderById = Object.fromEntries(scenario.orders.map((o) => [o.id, o]));

  return (
    <div className="svg-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet">
        {/* grid */}
        <rect x={0} y={0} width={W} height={H} fill="#0b1224" />
        {Array.from({ length: 10 }).map((_, i) => (
          <line
            key={`gx${i}`}
            x1={PAD + (i * (W - 2 * PAD)) / 9}
            x2={PAD + (i * (W - 2 * PAD)) / 9}
            y1={PAD}
            y2={H - PAD}
            stroke="#1e293b"
          />
        ))}
        {Array.from({ length: 8 }).map((_, i) => (
          <line
            key={`gy${i}`}
            y1={PAD + (i * (H - 2 * PAD)) / 7}
            y2={PAD + (i * (H - 2 * PAD)) / 7}
            x1={PAD}
            x2={W - PAD}
            stroke="#1e293b"
          />
        ))}

        {/* routes */}
        {result?.routes.map((r) => {
          const t = truckById[r.truck_id];
          if (!t || r.stops.length === 0) return null;
          const pts = [
            project(t.lat, t.lon),
            ...r.stops.map((s) => {
              const o = orderById[s.order_id];
              return project(o.lat, o.lon);
            }),
          ];
          const d = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
          return (
            <path
              key={`r${r.truck_id}`}
              d={d}
              stroke={colorForTruck(r.truck_id)}
              strokeWidth={2}
              fill="none"
              opacity={0.85}
            />
          );
        })}

        {/* trucks: square markers */}
        {scenario.trucks.map((t) => {
          const [x, y] = project(t.lat, t.lon);
          const c = colorForTruck(t.id);
          return (
            <g key={`t${t.id}`}>
              <rect x={x - 8} y={y - 8} width={16} height={16} fill={c} stroke="#0b1224" strokeWidth={2} />
              <text x={x + 12} y={y + 4} fill={c} fontSize={11}>{t.name}</text>
            </g>
          );
        })}

        {/* orders: circles colored by assigned truck */}
        {scenario.orders.map((o) => {
          const [x, y] = project(o.lat, o.lon);
          const assignedTruckId = result?.routes.find((r) =>
            r.stops.some((s) => s.order_id === o.id)
          )?.truck_id;
          const isUnassigned = result?.unassigned_order_ids.includes(o.id);
          const fill = isUnassigned
            ? '#f87171'
            : assignedTruckId != null
            ? colorForTruck(assignedTruckId)
            : '#94a3b8';
          return (
            <g key={`o${o.id}`}>
              <circle cx={x} cy={y} r={3 + o.priority} fill={fill} stroke="#0b1224" />
              <title>{o.code} · prio {o.priority} · {o.weight_kg}kg</title>
            </g>
          );
        })}

        {/* legend */}
        <g transform={`translate(${W - 200}, ${H - 80})`}>
          <rect x={0} y={0} width={180} height={68} fill="#1e293b" stroke="#475569" rx={4} />
          <text x={10} y={18} fill="#94a3b8" fontSize={11}>■ Trucks (square)</text>
          <text x={10} y={36} fill="#94a3b8" fontSize={11}>● Orders (size=priority)</text>
          <text x={10} y={54} fill="#f87171" fontSize={11}>● Unassigned (red)</text>
        </g>
      </svg>
    </div>
  );
}
