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

// Monotone cubic Hermite (PCHIP / Fritsch–Carlson style): passes through every point and
// avoids Catmull–Rom overshoot between samples, so y stays within each segment’s endpoints
// when the discrete series is monotone there (e.g. nonnegative counts per day).
export function buildSmoothInterpolatedPath(points: PlotPoint[]): string {
  if (points.length === 0) return "";
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
  if (points.length === 2) {
    return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
  }

  const n = points.length;
  const dx: number[] = [];
  const slopes: number[] = [];

  for (let i = 0; i < n - 1; i++) {
    const h = points[i + 1].x - points[i].x;
    dx.push(h);

    if (h === 0) {
      slopes.push(0);
    } else {
      slopes.push((points[i + 1].y - points[i].y) / h);
    }
  }

  const tangents = new Array<number>(n).fill(0);

  // Endpoints
  tangents[0] = slopes[0];
  tangents[n - 1] = slopes[n - 2];

  // Interior tangents: Fritsch-Carlson style monotone tangents
  for (let i = 1; i < n - 1; i++) {
    const mPrev = slopes[i - 1];
    const mNext = slopes[i];

    // If slope changes sign or one side is flat, force tangent to zero.
    // This prevents overshoot around local extrema / flat sections.
    if (mPrev === 0 || mNext === 0 || mPrev * mNext <= 0) {
      tangents[i] = 0;
      continue;
    }

    const hPrev = dx[i - 1];
    const hNext = dx[i];

    const w1 = 2 * hNext + hPrev;
    const w2 = hNext + 2 * hPrev;

    tangents[i] = (w1 + w2) / (w1 / mPrev + w2 / mNext);
  }

  // Extra monotonicity clamp per segment
  for (let i = 0; i < n - 1; i++) {
    const m = slopes[i];

    if (m === 0) {
      tangents[i] = 0;
      tangents[i + 1] = 0;
      continue;
    }

    const a = tangents[i] / m;
    const b = tangents[i + 1] / m;
    const s = a * a + b * b;

    if (s > 9) {
      const t = 3 / Math.sqrt(s);
      tangents[i] = t * a * m;
      tangents[i + 1] = t * b * m;
    }
  }

  let d = `M ${points[0].x} ${points[0].y}`;

  for (let i = 0; i < n - 1; i++) {
    const p0 = points[i];
    const p1 = points[i + 1];
    const h = p1.x - p0.x;

    const cp1x = p0.x + h / 3;
    const cp1y = p0.y + (tangents[i] * h) / 3;

    const cp2x = p1.x - h / 3;
    const cp2y = p1.y - (tangents[i + 1] * h) / 3;

    d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p1.x} ${p1.y}`;
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
