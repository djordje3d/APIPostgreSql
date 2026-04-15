export type TimelineSeries = {
  id?: string;
  name: string;
  values: number[];
  color: string;
};

// NormalizedTimelineSeries is a type that represents a timeline series with normalized values.
// The values are normalized to the range 0-100.
export type NormalizedTimelineSeries = {
  id: string;
  name: string;
  values: number[];
  color: string;
};

export type PlotPoint = { x: number; y: number };
// TIMELINE_LAYOUT is a constant that represents the layout of the timeline chart.
// It contains the width and height of the main chart, the width and height of the brush chart,
// the width and height of the plot, the width and height of the tooltip, and the width and height of the tooltip estimated width.
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

// clamp is a function that clamps the given value between the given minimum and maximum.
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

// percentForIndex is a function that converts the index of the point to the percentage of the point.
// It is used to calculate the percentage of the point on the main chart.
export function percentForIndex(index: number, maxIndex: number): number {
  if (maxIndex <= 0) return 0;
  return (index / maxIndex) * 100;
}
// indexFromClientX is a function that converts the client x coordinate to the index of the point.
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

// mapIndexToMainChartX is a function that maps the index of the point to the x coordinate of the point on the main chart.
export function mapIndexToMainChartX(index: number, pointCount: number): number {
  if (pointCount <= 1) return TIMELINE_LAYOUT.main.axisLeft;
  return (
    TIMELINE_LAYOUT.main.axisLeft +
    (TIMELINE_LAYOUT.main.plotWidth * index) / (pointCount - 1)
  );
}

export function mapIndexToOverviewX(index: number, pointCount: number): number {
  if (pointCount <= 1) return 0;
  return (TIMELINE_LAYOUT.brush.viewBoxWidth * index) / (pointCount - 1);
}

// normalizeSeries is a function that normalizes the values of the series to the range 0-100.
export function normalizeSeries(
  series: TimelineSeries[],
  pointCount: number,
): NormalizedTimelineSeries[] {
  return series.map((item, index) => {
    const stableId = item.id ?? `${item.name}__${item.color}__${index}`;
    const normalizedValues =
      item.values.length >= pointCount
        ? item.values.slice(0, pointCount)
        : [...item.values, ...Array.from({ length: pointCount - item.values.length }, () => 0)];
    return {
      id: stableId,
      name: item.name,
      color: item.color,
      values: normalizedValues,
    };
  });
}

// maxFromRange is a function that finds the maximum value in the given range of the series.
export function maxFromRange(
  series: NormalizedTimelineSeries[],
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

// maxFromAll is a function that finds the maximum value in all the series.
export function maxFromAll(series: NormalizedTimelineSeries[]): number {
  let max = 0;
  for (const item of series) {
    for (const value of item.values) {
      if (value > max) max = value;
    }
  }
  return max === 0 ? 1 : max;
}

// buildQuadraticSmoothPath is a function that builds a quadratic smooth path from the given points.
// It uses the quadratic bezier curve to smooth the path.
export function buildQuadraticSmoothPath(points: PlotPoint[]): string {
  if (points.length === 0) return "";
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
  if (points.length === 2) {
    return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
  }

  let d = `M ${points[0].x} ${points[0].y}`;
  for (let index = 0; index < points.length - 1; index++) {
    const current = points[index];
    const next = points[index + 1];
    const midX = (current.x + next.x) / 2;
    const midY = (current.y + next.y) / 2;
    d += ` Q ${current.x} ${current.y}, ${midX} ${midY}`;
  }
  const last = points[points.length - 1];
  d += ` T ${last.x} ${last.y}`;
  return d;
}

// createRafThrottled is a function that creates a throttled function that calls the given function at a maximum of 60 times per second.
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
