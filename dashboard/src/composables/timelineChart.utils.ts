export type TimelineSeries = {
  id?: string;
  name: string;
  values: number[];
  color: string;
};

export type AlignedTimelineSeries = {
  id: string;
  name: string;
  values: number[];
  color: string;
};

export type PlotPoint = { x: number; y: number };

// Shared layout constants for the main timeline chart and the brush overview.
export const TIMELINE_LAYOUT = {
  main: {
    viewBoxWidth: 1000,
    viewBoxHeight: 260,
    axisLeft: 40,
    axisTop: 20,
    axisBottom: 220,
    plotWidth: 940,
    plotHeight: 200,
    tooltipOffset: 12,
    tooltipEstimatedWidth: 180,
  },
  brush: {
    viewBoxWidth: 1000,
    viewBoxHeight: 88,
    baselineY: 75,
    plotHeight: 63,
  },
} as const;

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

// Converts a point index into a 0-100 percentage within the current range.
export function percentForIndex(index: number, maxIndex: number): number {
  if (maxIndex <= 0) return 0;
  return (index / maxIndex) * 100;
}

// Maps a pointer X position within an element to the nearest data-point index.
export function indexFromClientX(
  clientX: number,
  element: HTMLElement | null,
  maxIndex: number,
): number {
  if (!element || maxIndex <= 0) return 0;
  const rect = element.getBoundingClientRect();
  const x = clamp(clientX - rect.left, 0, rect.width);
  const ratio = rect.width > 0 ? x / rect.width : 0;
  return Math.round(ratio * maxIndex);
}

// Converts a point index into its X coordinate in the main chart viewBox.
export function mapIndexToMainChartX(index: number, pointCount: number): number {
  if (pointCount <= 1) return TIMELINE_LAYOUT.main.axisLeft;
  return (
    TIMELINE_LAYOUT.main.axisLeft +
    (TIMELINE_LAYOUT.main.plotWidth * index) / (pointCount - 1)
  );
}
// Converts a point index into its X coordinate in the brush overview viewBox.
export function mapIndexToOverviewX(index: number, pointCount: number): number {
  if (pointCount <= 1) return 0;
  return (TIMELINE_LAYOUT.brush.viewBoxWidth * index) / (pointCount - 1);
}

// Ensures each series has a stable `id`, truncates `values` to `pointCount`, or pads with zeros
// so every series has the same length for shared indices (main chart, brush, tooltips).
export function alignSeriesToPointCount(
  series: TimelineSeries[],
  pointCount: number,
): AlignedTimelineSeries[] {
  return series.map((item, index) => {
    const stableId = item.id ?? `${item.name}__${item.color}__${index}`;
    const alignedValues =
      item.values.length >= pointCount
        ? item.values.slice(0, pointCount)
        : [...item.values, ...Array.from({ length: pointCount - item.values.length }, () => 0)];
    return {
      id: stableId,
      name: item.name,
      color: item.color,
      values: alignedValues,
    };
  });
}

// Returns the maximum value across all series within the inclusive [start, end] range.
export function maxFromRange(
  series: AlignedTimelineSeries[],
  start: number,
  end: number,
): number {
  let max = 0;
  for (const item of series) {
    const slice = item.values.slice(start, end + 1);
    for (const value of slice) {
      if (value > max) max = value;
    }
  }
  return max === 0 ? 1 : max;
}

// Returns the maximum value across all points in all series.
export function maxFromAll(series: AlignedTimelineSeries[]): number {
  let max = 0;
  for (const item of series) {
    for (const value of item.values) {
      if (value > max) max = value;
    }
  }
  return max === 0 ? 1 : max;
}

// Catmull-Rom-style cubics: curve passes through every point. Endpoints use duplicated
// neighbors via `??` (not array negative indices — those are undefined in JS for dense arrays).
export function buildSmoothInterpolatedPath(points: PlotPoint[]): string {
  if (points.length === 0) return "";
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
  if (points.length === 2) {
    return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
  }

  let d = `M ${points[0].x} ${points[0].y}`;
  const tension = 1;

  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i - 1] ?? points[i];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2] ?? p2;

    const cp1x = p1.x + ((p2.x - p0.x) / 6) * tension;
    const cp1y = p1.y + ((p2.y - p0.y) / 6) * tension;
    const cp2x = p2.x - ((p3.x - p1.x) / 6) * tension;
    const cp2y = p2.y - ((p3.y - p1.y) / 6) * tension;

    d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
  }

  return d;
}

// Throttles calls so the wrapped function runs at most once per animation frame.
export function createRafThrottled<T extends (...args: any[]) => void>(fn: T): T {
  let rafId: number | null = null;
  let lastArgs: Parameters<T> | null = null;

  const throttled = ((...args: Parameters<T>) => {
    lastArgs = args;
    if (rafId != null) return;

    rafId = window.requestAnimationFrame(() => {
      rafId = null;
      if (!lastArgs) return;
      fn(...lastArgs);
      lastArgs = null;
    });
  }) as T;

  return throttled;
}
