<template>
  <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
    <div class="border-b border-gray-200 px-4 py-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h2 class="text-lg font-semibold text-gray-900">
          {{ t("timeline.title") }}
        </h2>

        <div class="flex flex-wrap items-center gap-3">
          <div class="w-[220px]">
            <div class="mb-1 flex items-center gap-1 text-gray-600">
              <span class="block text-sm">{{ t("timeline.yAxisMetric") }}</span>
              <HelpTooltip
                as-icon
                :text="t('help.timeline.yAxis')"
                :aria-label="t('help.aria.timelineYAxis')"
              />
            </div>

            <StandardDropdown
              label=""
              :options="yAxisOptions"
              :model-value="yAxisMode"
              :nullable="false"
              @update:model-value="
                emit(
                  'update:yAxisMode',
                  (($event as string) ?? 'entries') as 'entries' | 'exits',
                )
              "
            />
          </div>

          <div class="text-sm text-gray-500">{{ fromDate }} - {{ toDate }}</div>
        </div>
      </div>
    </div>

    <div class="min-h-[360px] px-4 py-4">
      <div
        v-if="error"
        class="flex min-h-[320px] items-center justify-center text-red-600"
        role="alert"
      >
        {{ t("timeline.loadFailed") }}
      </div>

      <div
        v-else-if="loading"
        class="flex min-h-[320px] flex-col items-center justify-center gap-3 text-gray-500"
      >
        <span class="icon-spinner11 inline-block animate-spin text-2xl"></span>
        <span>{{ t("timeline.loading") }}</span>
      </div>

      <div
        v-else-if="!hasLoadedOnce || points.length === 0"
        class="flex min-h-[320px] items-center justify-center text-gray-500"
      >
        {{ t("timeline.noDataForPeriod") }}
      </div>

      <div v-else class="relative min-h-[320px]">
        <div
          v-if="refreshing"
          class="absolute inset-0 z-10 flex items-center justify-center bg-white/60"
        >
          <span
            class="icon-spinner11 inline-block animate-spin text-3xl text-gray-500"
          ></span>
        </div>

        <div class="mb-2 flex items-center gap-1 text-sm text-gray-600">
          <span>{{ t("timeline.vehicleSeriesFilter") }}</span>
          <HelpTooltip
            as-icon
            :text="t('help.timeline.series')"
            :aria-label="t('help.aria.timelineSeries')"
          />
        </div>

        <div class="mb-3 flex flex-wrap gap-3">
          <label
            v-for="s in normalizedSeries"
            :key="s.id"
            class="inline-flex items-center gap-2 text-sm text-gray-700"
          >
            <input
              type="checkbox"
              :checked="visibleSeries[s.id] !== false"
              @change="toggleSeries(s.id)"
            />
            <span
              class="inline-block h-2.5 w-2.5 rounded-full"
              :style="{ backgroundColor: s.color }"
            ></span>
            <span>{{ s.name }}</span>
          </label>
        </div>

        <div
          ref="chartRef"
          class="relative h-[260px] w-full rounded border border-gray-200 bg-white"
          @mouseleave="onMouseLeave"
          @mousemove="onMouseMove"
        >
          <svg
            class="h-full w-full"
            :viewBox="`0 0 ${TIMELINE_LAYOUT.main.viewBoxWidth} ${TIMELINE_LAYOUT.main.viewBoxHeight}`"
            preserveAspectRatio="none"
          >
            <!-- horizontal grid -->
            <line
              v-for="grid in mainGridLines"
              :key="`grid-${grid.y}`"
              :x1="TIMELINE_LAYOUT.main.axisLeft"
              :y1="grid.y"
              :x2="TIMELINE_LAYOUT.main.axisLeft + TIMELINE_LAYOUT.main.plotWidth"
              :y2="grid.y"
              :stroke="grid.stroke"
            />

            <!-- y axis -->
            <line
              :x1="TIMELINE_LAYOUT.main.axisLeft"
              :y1="TIMELINE_LAYOUT.main.axisTop"
              :x2="TIMELINE_LAYOUT.main.axisLeft"
              :y2="TIMELINE_LAYOUT.main.axisBottom"
              stroke="#d1d5db"
            />

            <text
              v-for="grid in mainGridLines"
              :key="`grid-label-${grid.y}`"
              :x="TIMELINE_LAYOUT.main.axisLeft - 6"
              :y="grid.y + 3"
              text-anchor="end"
              font-size="10"
              fill="#6b7280"
            >
              {{ grid.value }}
            </text>

            <text
              v-for="tick in xAxisTicks"
              :key="`x-tick-${tick.index}`"
              :x="tick.x"
              :y="TIMELINE_LAYOUT.main.axisBottom + 16"
              text-anchor="middle"
              font-size="9"
              fill="#6b7280"
            >
              {{ tick.label }}
            </text>

            <!-- main lines -->
            <g v-for="line in visibleLines" :key="line.id">
              <path
                :d="line.path"
                fill="none"
                :stroke="line.color"
                stroke-width="2.6"
                stroke-linejoin="round"
                stroke-linecap="round"
              />
            </g>

            <!-- hover vertical line -->
            <line
              v-if="hoverIndex != null && hoverX != null"
              :x1="hoverX"
              y1="20"
              :x2="hoverX"
              y2="220"
              stroke="#9ca3af"
              stroke-dasharray="4 4"
            />

            <!-- hover markers -->
            <g v-if="hoverIndex != null">
              <circle
                v-for="line in visibleLines"
                :key="`hover-${line.id}`"
                :cx="line.plotPoints[hoverIndex]?.x"
                :cy="line.plotPoints[hoverIndex]?.y"
                r="4.5"
                :fill="line.color"
                stroke="#ffffff"
                stroke-width="2"
              />
            </g>
          </svg>

          <div
            v-if="hoverIndex != null && tooltipRows.length"
            class="pointer-events-none absolute z-20 rounded border border-gray-200 bg-white px-3 py-2 text-xs shadow"
            :style="{ left: `${tooltipLeft}px`, top: '8px' }"
          >
            <div class="mb-1 font-semibold text-gray-800">
              {{ formatXAxisLabel(visiblePoints[hoverIndex]) }}
            </div>

            <div
              v-for="row in tooltipRows"
              :key="row.id"
              class="flex items-center gap-2"
            >
              <span
                class="inline-block h-2 w-2 rounded-full"
                :style="{ backgroundColor: row.color }"
              ></span>
              <span class="text-gray-600">{{ row.name }}:</span>
              <span class="font-semibold text-gray-900">{{ row.value }}</span>
            </div>
          </div>
        </div>

        <div class="mt-4 rounded border border-gray-200 bg-gray-50 p-3">
          <div class="mb-2 flex items-center gap-1 text-sm text-gray-700">
            <span>{{ t("timeline.zoomRange") }}</span>
            <HelpTooltip
              as-icon
              :text="t('help.timeline.zoomRange')"
              :aria-label="t('help.aria.timelineZoom')"
            />
          </div>

          <div
            ref="brushRef"
            class="relative h-[88px] w-full cursor-crosshair rounded border border-gray-200 bg-white"
            @pointerdown="onBrushPointerDown"
          >
            <svg
              class="absolute inset-0 h-full w-full"
              :viewBox="`0 0 ${TIMELINE_LAYOUT.brush.viewBoxWidth} ${TIMELINE_LAYOUT.brush.viewBoxHeight}`"
              preserveAspectRatio="none"
            >
              <line x1="0" y1="75" x2="1000" y2="75" stroke="#e5e7eb" />

              <g v-for="line in overviewLines" :key="line.id">
                <path
                  :d="line.path"
                  fill="none"
                  :stroke="line.color"
                  stroke-width="1.8"
                  stroke-linejoin="round"
                  stroke-linecap="round"
                  opacity="0.8"
                />
              </g>
            </svg>

            <div
              class="absolute inset-y-0 bg-gray-400/25"
              :style="{ left: '0%', width: `${brushLeftPercent}%` }"
            ></div>

            <div
              class="absolute inset-y-0 bg-gray-400/25"
              :style="{
                left: `${brushRightPercent}%`,
                width: `${100 - brushRightPercent}%`,
              }"
            ></div>

            <div
              class="absolute inset-y-0 border-2 border-blue-500 bg-blue-200/20"
              :style="{
                left: `${brushLeftPercent}%`,
                width: `${brushWidthPercent}%`,
              }"
            >
              <button
                type="button"
                aria-label="Resize start"
                class="absolute inset-y-0 left-0 w-3 -translate-x-1/2 cursor-ew-resize bg-blue-500/80"
                @pointerdown.stop.prevent="onHandlePointerDown('start', $event)"
              ></button>

              <button
                type="button"
                aria-label="Resize end"
                class="absolute inset-y-0 right-0 w-3 translate-x-1/2 cursor-ew-resize bg-blue-500/80"
                @pointerdown.stop.prevent="onHandlePointerDown('end', $event)"
              ></button>
            </div>
          </div>

          <div class="mt-2 text-xs text-gray-500">
            {{ points[safeZoomStart] }} - {{ points[safeZoomEnd] }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import StandardDropdown from "../ui/StandardDropdown.vue";
import HelpTooltip from "../ui/HelpTooltip.vue";
import {
  TIMELINE_LAYOUT,
  buildQuadraticSmoothPath,
  clamp,
  createRafThrottled,
  indexFromClientX,
  mapIndexToMainChartX,
  mapIndexToOverviewX,
  maxFromAll,
  maxFromRange,
  normalizeSeries,
  percentForIndex,
  type PlotPoint,
  type TimelineSeries,
} from "../../composables/useTimelineChartUtils";

const { t } = useI18n();

type DragMode = "move" | "start" | "end";

const props = withDefaults(
  defineProps<{
    fromDate: string;
    toDate: string;
    points: string[];
    series: TimelineSeries[];
    loading: boolean;
    refreshing: boolean;
    error: boolean;
    hasLoadedOnce: boolean;
    yAxisMode: "entries" | "exits";
    zoomStart?: number;
    zoomEnd?: number;
  }>(),
  {
    zoomStart: 0,
    zoomEnd: 0,
  },
);

const emit = defineEmits<{
  "update:zoomStart": [value: number];
  "update:zoomEnd": [value: number];
  "update:yAxisMode": [value: "entries" | "exits"];
}>();

const chartRef = ref<HTMLElement | null>(null);
const brushRef = ref<HTMLElement | null>(null);
const hoverIndex = ref<number | null>(null);
const hoverX = ref<number | null>(null);
const visibleSeries = ref<Record<string, boolean>>({});
const normalizedSeries = computed(() =>
  normalizeSeries(props.series, props.points.length),
);

const yAxisOptions = computed(() => [
  { id: "entries", label: t("timeline.entriesPerDay") },
  { id: "exits", label: t("timeline.exitsPerDay") },
]);

const dragState = ref<{
  mode: DragMode;
  pointerId: number;
  originIndex: number;
  startAtDown: number;
  endAtDown: number;
} | null>(null);

const safeZoomStart = computed(() =>
  Math.min(Math.max(props.zoomStart, 0), Math.max(props.points.length - 1, 0)),
);

const safeZoomEnd = computed(() =>
  Math.min(
    Math.max(props.zoomEnd, safeZoomStart.value),
    Math.max(props.points.length - 1, 0),
  ),
);

const visiblePoints = computed(() =>
  props.points.slice(safeZoomStart.value, safeZoomEnd.value + 1),
);

const activeSeries = computed(() =>
  normalizedSeries.value.filter((s) => visibleSeries.value[s.id] !== false),
);

const maxY = computed(() => {
  return maxFromRange(activeSeries.value, safeZoomStart.value, safeZoomEnd.value);
});

const mainGridLines = computed(() => {
  const count = 5;
  const span = TIMELINE_LAYOUT.main.axisBottom - TIMELINE_LAYOUT.main.axisTop;
  return Array.from({ length: count }, (_, index) => {
    const ratio = index / (count - 1);
    const y = TIMELINE_LAYOUT.main.axisBottom - ratio * span;
    const value = Math.round(ratio * maxY.value);
    const isBase = index === 0;
    const stroke = isBase ? "#d1d5db" : "#eef2f7";
    return { y, value, stroke };
  });
});

function formatXAxisLabel(value: string): string {
  return value || "–";
}

const xAxisTicks = computed(() => {
  const count = visiblePoints.value.length;
  if (count === 0) return [];

  const targetTicks = 8;
  const step = Math.max(1, Math.floor((count - 1) / Math.max(targetTicks - 1, 1)));
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

const overviewMaxY = computed(() => {
  return maxFromAll(activeSeries.value);
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
      path: buildQuadraticSmoothPath(plotPoints),
    };
  }),
);

const overviewLines = computed(() =>
  activeSeries.value.map((s) => {
    const values = s.values.length ? s.values : [0];

    const plotPoints: PlotPoint[] = values.map((value, i) => {
      const x = mapIndexToOverviewX(i, values.length);
      const y =
        TIMELINE_LAYOUT.brush.baselineY -
        (TIMELINE_LAYOUT.brush.plotHeight * value) / overviewMaxY.value;

      return { x, y };
    });

    return {
      id: s.id,
      name: s.name,
      color: s.color,
      plotPoints,
      path: buildQuadraticSmoothPath(plotPoints),
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

const brushLeftPercent = computed(() =>
  percentForIndex(safeZoomStart.value, Math.max(props.points.length - 1, 0)),
);

const brushRightPercent = computed(() =>
  percentForIndex(safeZoomEnd.value, Math.max(props.points.length - 1, 0)),
);

const brushWidthPercent = computed(() => {
  return Math.max(brushRightPercent.value - brushLeftPercent.value, 0);
});

function indexFromClientXWithinBrush(clientX: number) {
  return indexFromClientX(
    clientX,
    brushRef.value,
    Math.max(props.points.length - 1, 0),
  );
}

function setZoom(start: number, end: number) {
  const maxIndex = Math.max(props.points.length - 1, 0);
  const nextStart = clamp(start, 0, maxIndex);
  const nextEnd = clamp(end, nextStart, maxIndex);

  emit("update:zoomStart", nextStart);
  emit("update:zoomEnd", nextEnd);
}

function startDrag(mode: DragMode, pointerId: number, clientX: number) {
  dragState.value = {
    mode,
    pointerId,
    originIndex: indexFromClientXWithinBrush(clientX),
    startAtDown: safeZoomStart.value,
    endAtDown: safeZoomEnd.value,
  };
}

function onBrushPointerDown(e: PointerEvent) {
  if (props.points.length === 0) return;

  (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);

  const clickedIndex = indexFromClientXWithinBrush(e.clientX);
  const distToStart = Math.abs(clickedIndex - safeZoomStart.value);
  const distToEnd = Math.abs(clickedIndex - safeZoomEnd.value);

  if (distToStart <= 1 && distToStart <= distToEnd) {
    startDrag("start", e.pointerId, e.clientX);
    return;
  }

  if (distToEnd <= 1) {
    startDrag("end", e.pointerId, e.clientX);
    return;
  }

  if (
    clickedIndex >= safeZoomStart.value &&
    clickedIndex <= safeZoomEnd.value
  ) {
    startDrag("move", e.pointerId, e.clientX);
  } else {
    const windowSize = Math.max(safeZoomEnd.value - safeZoomStart.value, 0);
    const start = Math.min(
      Math.max(clickedIndex - Math.floor(windowSize / 2), 0),
      Math.max(props.points.length - 1 - windowSize, 0),
    );
    setZoom(start, start + windowSize);
    startDrag("move", e.pointerId, e.clientX);
  }
}

function onHandlePointerDown(mode: "start" | "end", e: PointerEvent) {
  if (!brushRef.value || props.points.length === 0) return;
  brushRef.value.setPointerCapture(e.pointerId);
  startDrag(mode, e.pointerId, e.clientX);
}

function onBrushPointerMove(e: PointerEvent) {
  if (!dragState.value || e.pointerId !== dragState.value.pointerId) return;

  const state = dragState.value;
  const currentIndex = indexFromClientXWithinBrush(e.clientX);
  const delta = currentIndex - state.originIndex;
  const maxIndex = Math.max(props.points.length - 1, 0);

  if (state.mode === "move") {
    const width = state.endAtDown - state.startAtDown;
    let nextStart = state.startAtDown + delta;
    nextStart = clamp(nextStart, 0, Math.max(maxIndex - width, 0));
    setZoom(nextStart, nextStart + width);
    return;
  }

  if (state.mode === "start") {
    const nextStart = clamp(state.startAtDown + delta, 0, safeZoomEnd.value);
    setZoom(nextStart, safeZoomEnd.value);
    return;
  }

  const nextEnd = clamp(state.endAtDown + delta, safeZoomStart.value, maxIndex);
  setZoom(safeZoomStart.value, nextEnd);
}

function endDrag(pointerId: number) {
  if (dragState.value?.pointerId === pointerId) {
    dragState.value = null;
  }
}

function toggleSeries(id: string) {
  const current = visibleSeries.value[id] !== false;
  visibleSeries.value = { ...visibleSeries.value, [id]: !current };
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

function onMouseLeave() {
  hoverIndex.value = null;
  hoverX.value = null;
}

function onWindowPointerUp(e: PointerEvent) {
  endDrag(e.pointerId);
}
const onMouseMove = createRafThrottled((e: MouseEvent) => {
  setHoverFromMouse(e);
});

const onBrushPointerMoveThrottled = createRafThrottled((e: PointerEvent) => {
  onBrushPointerMove(e);
});

function onWindowPointerMove(e: PointerEvent) {
  onBrushPointerMoveThrottled(e);
}

onMounted(() => {
  window.addEventListener("pointermove", onWindowPointerMove);
  window.addEventListener("pointerup", onWindowPointerUp);
  window.addEventListener("pointercancel", onWindowPointerUp);
});

onBeforeUnmount(() => {
  window.removeEventListener("pointermove", onWindowPointerMove);
  window.removeEventListener("pointerup", onWindowPointerUp);
  window.removeEventListener("pointercancel", onWindowPointerUp);
});
</script>