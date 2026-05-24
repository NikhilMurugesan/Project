// Real-map view using Leaflet + OpenStreetMap tiles. No API key needed --
// OSM's tile server is fine for a local dev demo (we wouldn't hammer it
// in production though).
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip } from 'react-leaflet';
import type { AllocationResult, Scenario } from '../types';
import { colorForTruck } from '../utils';

interface Props {
  scenario: Scenario;
  result: AllocationResult | null;
}

export default function MapView({ scenario, result }: Props) {
  // Center the map on the mean of everything we're about to plot, so the
  // initial zoom always frames the scenario reasonably.
  const allLat = [
    ...scenario.trucks.map((t) => t.lat),
    ...scenario.orders.map((o) => o.lat),
  ];
  const allLon = [
    ...scenario.trucks.map((t) => t.lon),
    ...scenario.orders.map((o) => o.lon),
  ];
  const center: [number, number] = [
    allLat.reduce((a, b) => a + b, 0) / Math.max(allLat.length, 1),
    allLon.reduce((a, b) => a + b, 0) / Math.max(allLon.length, 1),
  ];

  const truckById = Object.fromEntries(scenario.trucks.map((t) => [t.id, t]));
  const orderById = Object.fromEntries(scenario.orders.map((o) => [o.id, o]));

  return (
    <MapContainer center={center} zoom={11} style={{ width: '100%', height: '100%' }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {result?.routes.map((r) => {
        const t = truckById[r.truck_id];
        if (!t || r.stops.length === 0) return null;
        const positions: [number, number][] = [
          [t.lat, t.lon],
          ...r.stops.map((s) => {
            const o = orderById[s.order_id];
            return [o.lat, o.lon] as [number, number];
          }),
        ];
        return (
          <Polyline
            key={`route-${r.truck_id}`}
            positions={positions}
            pathOptions={{ color: colorForTruck(r.truck_id), weight: 3, opacity: 0.85 }}
          />
        );
      })}

      {scenario.trucks.map((t) => (
        <CircleMarker
          key={`t-${t.id}`}
          center={[t.lat, t.lon]}
          radius={8}
          pathOptions={{ color: colorForTruck(t.id), fillColor: colorForTruck(t.id), fillOpacity: 1, weight: 2 }}
        >
          <Tooltip>
            <strong>{t.name}</strong> · cap {t.capacity_kg}kg
            <br />
            caps: {t.capabilities.join(', ') || '—'}
          </Tooltip>
        </CircleMarker>
      ))}

      {scenario.orders.map((o) => {
        const assignedTruckId = result?.routes.find((r) =>
          r.stops.some((s) => s.order_id === o.id)
        )?.truck_id;
        const fill = assignedTruckId != null ? colorForTruck(assignedTruckId) : '#94a3b8';
        const isUnassigned = result?.unassigned_order_ids.includes(o.id);
        return (
          <CircleMarker
            key={`o-${o.id}`}
            center={[o.lat, o.lon]}
            radius={4 + o.priority}
            pathOptions={{
              color: isUnassigned ? '#f87171' : fill,
              fillColor: isUnassigned ? '#f87171' : fill,
              fillOpacity: 0.85,
              weight: 1,
            }}
          >
            <Tooltip>
              <strong>{o.code}</strong> · priority {o.priority}
              <br />
              {o.weight_kg}kg · TW {formatMin(o.tw_start)}–{formatMin(o.tw_end)}
              <br />
              caps: {o.required_capabilities.join(', ') || '—'}
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}

function formatMin(m: number): string {
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return `${String(h).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
}
