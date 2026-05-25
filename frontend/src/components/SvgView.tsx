// Schematic SVG view. Useful when you don't want the noise of the actual
// map -- it normalises lat/lon to a clean grid so the geometry of the
// routes is easier to eyeball.
import { useState } from 'react';
import type { AllocationResult, Scenario } from '../types';
import { colorForTruck } from '../utils';

interface Props {
  scenario: Scenario;
  result: AllocationResult | null;
}

export default function SvgView({ scenario, result }: Props) {
  const W = 1000, H = 700, PAD = 40;
  const [hoverTruckId, setHoverTruckId] = useState<number | null>(null);
  const [hoverOrderId, setHoverOrderId] = useState<number | null>(null);

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
  const routeByTruck = Object.fromEntries((result?.routes ?? []).map((r) => [r.truck_id, r]));
  const explByOrder = Object.fromEntries((result?.explanations ?? []).map((e) => [e.order_id, e]));

  const formatMin = (m: number) => {
    const h = Math.floor(m / 60), mm = Math.floor(m % 60);
    return `${String(h).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
  };

  const hoverTruck = hoverTruckId != null ? truckById[hoverTruckId] : null;
  const hoverRoute = hoverTruckId != null ? routeByTruck[hoverTruckId] : null;

  // Build the lines that appear inside the hover panel
  type Line = { text: string; color?: string; bold?: boolean; indent?: number };
  const buildPanelLines = (): Line[] => {
    if (!hoverTruck) return [];
    const lines: Line[] = [];
    lines.push({ text: hoverTruck.name, color: colorForTruck(hoverTruck.id), bold: true });
    lines.push({ text: `Capacity: ${hoverTruck.capacity_kg} kg` });
    lines.push({ text: `Rate: $${hoverTruck.cost_per_km.toFixed(2)}/km` });
    lines.push({ text: `Avg speed: ${hoverTruck.avg_speed_kmh} km/h` });
    lines.push({
      text: `Shift: ${formatMin(hoverTruck.shift_start)}–${formatMin(hoverTruck.shift_end)}`,
    });
    lines.push({
      text: `Capabilities: ${hoverTruck.capabilities.join(', ') || '—'}`,
    });

    if (hoverRoute) {
      lines.push({ text: '────────────', color: '#475569' });
      lines.push({ text: `Stops: ${hoverRoute.stops.length}` });
      lines.push({ text: `Distance: ${hoverRoute.total_distance_km.toFixed(2)} km` });
      const pct = (hoverRoute.total_load_kg / hoverTruck.capacity_kg) * 100;
      lines.push({
        text: `Load: ${hoverRoute.total_load_kg.toFixed(1)} kg (${pct.toFixed(0)}%)`,
      });
      lines.push({
        text: `Total cost: $${(hoverRoute.total_distance_km * hoverTruck.cost_per_km).toFixed(2)}`,
      });
      lines.push({ text: `Parcels (${hoverRoute.stops.length}):`, bold: true });

      if (hoverRoute.stops.length === 0) {
        lines.push({ text: 'No parcels assigned.', color: '#94a3b8', indent: 1 });
      } else {
        hoverRoute.stops.forEach((s, idx) => {
          const o = orderById[s.order_id];
          const expl = explByOrder[s.order_id];
          const header = o
            ? `${idx + 1}. ${s.order_code}  ${o.weight_kg}kg · prio ${o.priority}`
            : `${idx + 1}. ${s.order_code}`;
          lines.push({ text: header, bold: true, indent: 1 });
          lines.push({
            text: `arrive ${formatMin(s.arrival_minute)} · ${s.distance_km_from_prev.toFixed(2)} km from prev`,
            color: '#94a3b8',
            indent: 2,
          });
          if (expl && expl.runner_up_truck_name) {
            const score = expl.runner_up_score != null ? ` (score ${expl.runner_up_score.toFixed(2)})` : '';
            lines.push({
              text: `runner-up: ${expl.runner_up_truck_name}${score}`,
              color: '#64748b',
              indent: 2,
            });
          }
        });
      }
    } else {
      lines.push({ text: 'No route assigned to this truck.', color: '#94a3b8' });
    }
    return lines;
  };

  const panelLines = buildPanelLines();
  const panelWidth = 360;
  const lineHeight = 14;
  const panelPadX = 10;
  const panelPadY = 10;
  const panelHeight = panelLines.length * lineHeight + panelPadY * 2;  // Position the panel near the hovered truck, but clamp inside the viewbox
  let panelX = 0;
  let panelY = 0;
  if (hoverTruck) {
    const [tx, ty] = project(hoverTruck.lat, hoverTruck.lon);
    panelX = tx + 18;
    panelY = ty - 10;
    if (panelX + panelWidth > W - 4) panelX = tx - panelWidth - 18;
    if (panelX < 4) panelX = 4;
    if (panelY + panelHeight > H - 4) panelY = H - 4 - panelHeight;
    if (panelY < 4) panelY = 4;
  }

  // Build the lines that appear inside the order hover panel
  const hoverOrder = hoverOrderId != null ? orderById[hoverOrderId] : null;
  const buildOrderPanelLines = (): Line[] => {
    if (!hoverOrder) return [];
    const o = hoverOrder;
    const lines: Line[] = [];
    const assignedRoute = result?.routes.find((r) =>
      r.stops.some((s) => s.order_id === o.id)
    );
    const stop = assignedRoute?.stops.find((s) => s.order_id === o.id);
    const isUnassigned = !!result?.unassigned_order_ids.includes(o.id);
    const headerColor = isUnassigned
      ? '#f87171'
      : assignedRoute
      ? colorForTruck(assignedRoute.truck_id)
      : '#e2e8f0';
    lines.push({ text: `Order ${o.code}`, color: headerColor, bold: true });
    lines.push({ text: `Weight: ${o.weight_kg} kg` });
    lines.push({ text: `Priority: ${o.priority}` });
    lines.push({
      text: `Time window: ${formatMin(o.tw_start)}–${formatMin(o.tw_end)}`,
    });
    lines.push({ text: `Service: ${o.service_minutes} min` });
    lines.push({ text: `SLA deadline: ${formatMin(o.sla_deadline)}` });
    lines.push({
      text: `Requires: ${o.required_capabilities.join(', ') || '—'}`,
    });
    lines.push({ text: `Location: ${o.lat.toFixed(4)}, ${o.lon.toFixed(4)}`, color: '#94a3b8' });
    lines.push({ text: '────────────', color: '#475569' });
    if (isUnassigned) {
      lines.push({ text: 'Status: UNASSIGNED', color: '#f87171', bold: true });
    } else if (assignedRoute && stop) {
      lines.push({
        text: `Assigned: ${assignedRoute.truck_name}`,
        color: colorForTruck(assignedRoute.truck_id),
        bold: true,
      });
      lines.push({ text: `Stop #${stop.sequence}`, indent: 1 });
      lines.push({
        text: `Arrival: ${formatMin(stop.arrival_minute)}`,
        indent: 1,
      });
      lines.push({
        text: `Departure: ${formatMin(stop.departure_minute)}`,
        indent: 1,
      });
      lines.push({
        text: `Distance from prev: ${stop.distance_km_from_prev.toFixed(2)} km`,
        indent: 1,
      });
    } else {
      lines.push({ text: 'Status: not in any route', color: '#94a3b8' });
    }
    const expl = explByOrder[o.id];
    if (expl) {
      if (expl.score != null) {
        lines.push({ text: `Score: ${expl.score.toFixed(2)}`, color: '#94a3b8' });
      }
      if (expl.runner_up_truck_name) {
        const rs = expl.runner_up_score != null ? ` (${expl.runner_up_score.toFixed(2)})` : '';
        lines.push({
          text: `Runner-up: ${expl.runner_up_truck_name}${rs}`,
          color: '#64748b',
        });
      }
      if (expl.reasons && expl.reasons.length > 0) {
        lines.push({ text: 'Reasons:', bold: true });
        expl.reasons.forEach((r) => {
          lines.push({ text: `• ${r}`, color: '#cbd5e1', indent: 1 });
        });
      }
    }
    return lines;
  };

  const orderPanelLines = buildOrderPanelLines();
  const orderPanelWidth = 340;
  const orderPanelHeight = orderPanelLines.length * lineHeight + panelPadY * 2;
  let orderPanelX = 0;
  let orderPanelY = 0;
  if (hoverOrder) {
    const [ox, oy] = project(hoverOrder.lat, hoverOrder.lon);
    orderPanelX = ox + 14;
    orderPanelY = oy - 10;
    if (orderPanelX + orderPanelWidth > W - 4) orderPanelX = ox - orderPanelWidth - 14;
    if (orderPanelX < 4) orderPanelX = 4;
    if (orderPanelY + orderPanelHeight > H - 4) orderPanelY = H - 4 - orderPanelHeight;
    if (orderPanelY < 4) orderPanelY = 4;
  }

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
          const dimmed = hoverTruckId != null && hoverTruckId !== r.truck_id;
          return (
            <path
              key={`r${r.truck_id}`}
              d={d}
              stroke={colorForTruck(r.truck_id)}
              strokeWidth={hoverTruckId === r.truck_id ? 3.5 : 2}
              fill="none"
              opacity={dimmed ? 0.2 : 0.85}
            />
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
          const dimmed = hoverTruckId != null && assignedTruckId !== hoverTruckId;
          const isHovered = hoverOrderId === o.id;
          return (
            <g
              key={`o${o.id}`}
              opacity={dimmed ? 0.25 : 1}
              cursor="pointer"
              onMouseEnter={() => setHoverOrderId(o.id)}
              onMouseLeave={() => setHoverOrderId(null)}
            >
              {/* larger transparent hit area for easier hovering */}
              <circle cx={x} cy={y} r={Math.max(10, 6 + o.priority)} fill="transparent" />
              <circle
                cx={x}
                cy={y}
                r={3 + o.priority}
                fill={fill}
                stroke={isHovered ? '#fef08a' : '#0b1224'}
                strokeWidth={isHovered ? 2 : 1}
              />
            </g>
          );
        })}

        {/* trucks: square markers (drawn last so hover targets are on top) */}
        {scenario.trucks.map((t) => {
          const [x, y] = project(t.lat, t.lon);
          const c = colorForTruck(t.id);
          const isHovered = hoverTruckId === t.id;
          return (
            <g
              key={`t${t.id}`}
              cursor="pointer"
              onMouseEnter={() => setHoverTruckId(t.id)}
              onMouseLeave={() => setHoverTruckId(null)}
            >
              {/* larger transparent hit area for easier hovering */}
              <rect x={x - 14} y={y - 14} width={28} height={28} fill="transparent" />
              <rect
                x={x - 8}
                y={y - 8}
                width={16}
                height={16}
                fill={c}
                stroke={isHovered ? '#fef08a' : '#0b1224'}
                strokeWidth={isHovered ? 3 : 2}
              />
              <text x={x + 12} y={y + 4} fill={c} fontSize={11}>{t.name}</text>
            </g>
          );
        })}

        {/* hover detail panel */}
        {hoverTruck && (
          <g transform={`translate(${panelX}, ${panelY})`} pointerEvents="none">
            <rect
              x={0}
              y={0}
              width={panelWidth}
              height={panelHeight}
              fill="#0f172a"
              fillOpacity={0.97}
              stroke={colorForTruck(hoverTruck.id)}
              strokeWidth={1.5}
              rx={6}
            />
            {panelLines.map((line, i) => (
              <text
                key={`pl${i}`}
                x={panelPadX + (line.indent ?? 0) * 10}
                y={panelPadY + (i + 1) * lineHeight - 3}
                fill={line.color ?? '#e2e8f0'}
                fontSize={11}
                fontWeight={line.bold ? 600 : 400}
                fontFamily="'Segoe UI', system-ui, sans-serif"
              >
                {line.text}
              </text>
            ))}
          </g>
        )}

        {/* hover detail panel for orders */}
        {hoverOrder && (
          <g transform={`translate(${orderPanelX}, ${orderPanelY})`} pointerEvents="none">
            <rect
              x={0}
              y={0}
              width={orderPanelWidth}
              height={orderPanelHeight}
              fill="#0f172a"
              fillOpacity={0.97}
              stroke={
                result?.unassigned_order_ids.includes(hoverOrder.id)
                  ? '#f87171'
                  : (() => {
                      const r = result?.routes.find((rt) =>
                        rt.stops.some((s) => s.order_id === hoverOrder.id)
                      );
                      return r ? colorForTruck(r.truck_id) : '#94a3b8';
                    })()
              }
              strokeWidth={1.5}
              rx={6}
            />
            {orderPanelLines.map((line, i) => (
              <text
                key={`opl${i}`}
                x={panelPadX + (line.indent ?? 0) * 10}
                y={panelPadY + (i + 1) * lineHeight - 3}
                fill={line.color ?? '#e2e8f0'}
                fontSize={11}
                fontWeight={line.bold ? 600 : 400}
                fontFamily="'Segoe UI', system-ui, sans-serif"
              >
                {line.text}
              </text>
            ))}
          </g>
        )}
      </svg>
    </div>
  );
}