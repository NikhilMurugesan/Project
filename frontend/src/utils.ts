// Same colour for the same truck across both views. The palette is just
// a hand-picked set that reads OK on dark backgrounds; nothing magical
// about the order.
export function colorForTruck(id: number): string {
  const palette = [
    '#38bdf8', '#4ade80', '#fbbf24', '#f472b6', '#a78bfa',
    '#fb923c', '#34d399', '#60a5fa', '#f87171', '#c084fc',
    '#facc15', '#22d3ee', '#fda4af', '#84cc16', '#e879f9',
  ];
  return palette[id % palette.length];
}

export function minutesToClock(m: number): string {
  // The backend stores everything as "minutes since midnight" so 510 -> 08:30.
  const h = Math.floor(m / 60);
  const mm = Math.floor(m % 60);
  return `${String(h).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
}
