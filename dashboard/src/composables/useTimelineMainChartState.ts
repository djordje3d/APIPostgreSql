import { computed, ref, type Ref } from "vue";
import {
  TIMELINE_LAYOUT,
  buildSmoothInterpolatedPath,
  clamp,
  mapIndexToMainChartX,
  maxFromRange,
  alignSeriesToPointCount,
  type PlotPoint,
  type TimelineSeries,
} from "./timelineChart.utils";

type YAxisMode = "entries" | "exits";

type UseTimelineMainChartStateParams = {
  points: Ref<string[]>;
  series: Ref<TimelineSeries[]>;
  zoomStart: Ref<number>;
  zoomEnd: Ref<number>;
  chartRef: Ref<HTMLElement | null>;
  t: (key: string) => string;
  gridSecondaryStroke?: string;
};

export function useTimelineMainChartState({
  points,
  series,
  zoomStart,
  zoomEnd,
  chartRef,
  t,
  gridSecondaryStroke = "#f1f5f9",
}: UseTimelineMainChartStateParams) {
  const hoverIndex = ref<number | null>(null);
  const hoverX = ref<number | null>(null);
  const visibleSeries = ref<Record<string, boolean>>({});

  const alignedSeries = computed(() =>
    alignSeriesToPointCount(series.value, points.value.length),
  );

  const yAxisOptions = computed(() => [
    { id: "entries", label: t("timeline.entriesPerDay") },
    { id: "exits", label: t("timeline.exitsPerDay") },
  ]);

  const safeZoomStart = computed(() =>
    Math.min(Math.max(zoomStart.value, 0), Math.max(points.value.length - 1, 0)),
  );

  const safeZoomEnd = computed(() =>
    Math.min(
      Math.max(zoomEnd.value, safeZoomStart.value),
      Math.max(points.value.length - 1, 0),
    ),
  );

  const visiblePoints = computed(() =>
    points.value.slice(safeZoomStart.value, safeZoomEnd.value + 1),
  );

  const activeSeries = computed(() =>
    alignedSeries.value.filter((s) => visibleSeries.value[s.id] !== false),
  );

  const rawMaxY = computed(() =>
    maxFromRange(activeSeries.value, safeZoomStart.value, safeZoomEnd.value),
  );

  // Add headroom above the tallest visible point so Bézier peaks
  // do not visually flatten against the chart ceiling.
  const maxY = computed(() => {
    const raw = rawMaxY.value;
    if (raw <= 0) return 1;
    return Math.max(1, raw * 1.15);
  });

  const mainGridLines = computed(() => {
    const count = 5;
    const span = TIMELINE_LAYOUT.main.axisBottom - TIMELINE_LAYOUT.main.axisTop;
    return Array.from({ length: count }, (_, index) => {
      const ratio = index / (count - 1);
      const y = TIMELINE_LAYOUT.main.axisBottom - ratio * span;
      const value = Math.round(ratio * maxY.value);
      const isBase = index === 0;
      return { y, value, stroke: isBase ? "#d1d5db" : gridSecondaryStroke };
    });
  });

  function formatXAxisLabel(value: string): string {
    return value || "–";
  }

  const xAxisTicks = computed(() => {
    const count = visiblePoints.value.length;
    if (count === 0) return [];

    const targetTicks = 8;
    const step = Math.max(
      1,
      Math.floor((count - 1) / Math.max(targetTicks - 1, 1)),
    );
    const ticks: Array<{ index: number; x: number; label: string }> = [];

    for (let index = 0; index < count; index += step) {
      ticks.push({
        index,
        x: mapIndexToMainChartX(index, count),
        label: formatXAxisLabel(visiblePoints.value[index]),
      });
    }

    if (ticks[ticks.length - 1]?.index !== count - 1) {
      ticks.push({
        index: count - 1,
        x: mapIndexToMainChartX(count - 1, count),
        label: formatXAxisLabel(visiblePoints.value[count - 1]),
      });
    }

    return ticks;
  });

  const visibleLines = computed(() =>
    activeSeries.value.map((s) => {
      const values = s.values.slice(safeZoomStart.value, safeZoomEnd.value + 1);

      const plotPoints: PlotPoint[] = values.map((value, i) => {
        const x = mapIndexToMainChartX(i, visiblePoints.value.length);
        const y =
          TIMELINE_LAYOUT.main.axisBottom -
          (TIMELINE_LAYOUT.main.plotHeight * value) / maxY.value;
        return { x, y };
      });

      return {
        id: s.id,
        name: s.name,
        color: s.color,
        plotPoints,
        path: buildSmoothInterpolatedPath(plotPoints, {
          tension: 0.75,
          minY: TIMELINE_LAYOUT.main.axisTop,
          maxY: TIMELINE_LAYOUT.main.axisBottom,
        }),
      };
    }),
  );

  const tooltipRows = computed(() => {
    const idx = hoverIndex.value;
    if (idx == null) return [];

    return activeSeries.value.map((s) => ({
      id: s.id,
      name: s.name,
      color: s.color,
      value: s.values[safeZoomStart.value + idx] ?? 0,
    }));
  });

  const tooltipLeft = computed(() => {
    if (hoverX.value == null || !chartRef.value) {
      return TIMELINE_LAYOUT.main.tooltipOffset;
    }

    const chartWidth = chartRef.value.clientWidth;
    const leftPx =
      (hoverX.value / TIMELINE_LAYOUT.main.viewBoxWidth) * chartWidth +
      TIMELINE_LAYOUT.main.tooltipOffset;

    return Math.min(
      Math.max(leftPx, TIMELINE_LAYOUT.main.tooltipOffset),
      Math.max(
        chartWidth -
        TIMELINE_LAYOUT.main.tooltipEstimatedWidth -
        TIMELINE_LAYOUT.main.tooltipOffset,
        TIMELINE_LAYOUT.main.tooltipOffset,
      ),
    );
  });

  function toggleSeries(id: string) {
    const current = visibleSeries.value[id] !== false;
    visibleSeries.value = { ...visibleSeries.value, [id]: !current };
  }

  function clearHover() {
    hoverIndex.value = null;
    hoverX.value = null;
  }

  function setHoverFromMouse(e: MouseEvent) {
    if (!chartRef.value || visiblePoints.value.length === 0) return;

    const rect = chartRef.value.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const clampedX = clamp(x, 0, rect.width);
    const ratio = rect.width > 0 ? clampedX / rect.width : 0;
    const idx = Math.round(ratio * (visiblePoints.value.length - 1));
    const normalizedIndex = clamp(idx, 0, visiblePoints.value.length - 1);

    hoverIndex.value = normalizedIndex;
    hoverX.value = mapIndexToMainChartX(normalizedIndex, visiblePoints.value.length);
  }

  return {
    yAxisOptions,
    visibleSeries,
    alignedSeries,
    safeZoomStart,
    safeZoomEnd,
    visiblePoints,
    activeSeries,
    maxY,
    mainGridLines,
    xAxisTicks,
    visibleLines,
    hoverIndex,
    hoverX,
    tooltipRows,
    tooltipLeft,
    formatXAxisLabel,
    toggleSeries,
    clearHover,
    setHoverFromMouse,
  };
}