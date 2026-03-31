<template>
  <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
    <div class="border-b border-gray-200 px-4 py-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h2 class="text-lg font-semibold text-gray-900">Timeline</h2>
        <div class="flex items-center gap-3">
          <div class="w-[220px]">
            <StandardDropdown
              label="Y-axis metric"
              :options="yAxisOptions"
              :model-value="yAxisMode"
              :nullable="false"
              @update:model-value="
                emit('update:yAxisMode', (($event as string) ?? 'entries') as
                  | 'entries'
                  | 'exits')
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
        Failed to load timeline data.
      </div>
      <div
        v-else-if="loading"
        class="flex min-h-[320px] flex-col items-center justify-center gap-3 text-gray-500"
      >
        <span class="icon-spinner11 inline-block animate-spin text-2xl"></span>
        <span>Loading timeline...</span>
      </div>
      <div
        v-else-if="!hasLoadedOnce || points.length === 0"
        class="flex min-h-[320px] items-center justify-center text-gray-500"
      >
        No timeline data for selected period.
      </div>
      <div v-else class="relative min-h-[320px]">
        <div
          v-if="refreshing"
          class="absolute inset-0 z-10 flex items-center justify-center bg-white/60"
        >
          <span class="icon-spinner11 inline-block animate-spin text-3xl text-gray-500"></span>
        </div>

        <div class="mb-3 flex flex-wrap gap-3">
          <label
            v-for="s in series"
            :key="s.name"
            class="inline-flex items-center gap-2 text-sm text-gray-700"
          >
            <input
              type="checkbox"
              :checked="visibleSeries[s.name] !== false"
              @change="toggleSeries(s.name)"
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
          @mouseleave="hoverIndex = null"
          @mousemove="onMouseMove"
        >
          <svg class="h-full w-full" viewBox="0 0 1000 260" preserveAspectRatio="none">
            <line x1="40" y1="220" x2="980" y2="220" stroke="#d1d5db" />
            <line x1="40" y1="20" x2="40" y2="220" stroke="#d1d5db" />

            <g v-for="line in visibleLines" :key="line.name">
              <polyline
                :points="line.points"
                fill="none"
                :stroke="line.color"
                stroke-width="2.2"
                stroke-linejoin="round"
                stroke-linecap="round"
              />
            </g>

            <line
              v-if="hoverIndex != null && hoverX != null"
              :x1="hoverX"
              y1="20"
              :x2="hoverX"
              y2="220"
              stroke="#9ca3af"
              stroke-dasharray="4 4"
            />
          </svg>

          <div
            v-if="hoverIndex != null && tooltipRows.length"
            class="pointer-events-none absolute z-20 rounded border border-gray-200 bg-white px-3 py-2 text-xs shadow"
            :style="{ left: `${tooltipLeft}px`, top: '8px' }"
          >
            <div class="mb-1 font-semibold text-gray-800">{{ visiblePoints[hoverIndex] }}</div>
            <div v-for="row in tooltipRows" :key="row.name" class="flex items-center gap-2">
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
          <div class="mb-2 text-sm text-gray-700">Zoom range</div>
          <div
            ref="brushRef"
            class="relative h-[88px] w-full cursor-crosshair rounded border border-gray-200 bg-white"
            @pointerdown="onBrushPointerDown"
          >
            <svg class="absolute inset-0 h-full w-full" viewBox="0 0 1000 88" preserveAspectRatio="none">
              <line x1="0" y1="75" x2="1000" y2="75" stroke="#e5e7eb" />
              <g v-for="line in overviewLines" :key="line.name">
                <polyline
                  :points="line.points"
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
              :style="{ left: `${brushRightPercent}%`, width: `${100 - brushRightPercent}%` }"
            ></div>

            <div
              class="absolute inset-y-0 border-2 border-blue-500 bg-blue-200/20"
              :style="{ left: `${brushLeftPercent}%`, width: `${brushWidthPercent}%` }"
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
import StandardDropdown from "../ui/StandardDropdown.vue";

type Series = { name: string; values: number[]; color: string };
type DragMode = "move" | "start" | "end";

const props = withDefaults(
  defineProps<{
    fromDate: string;
    toDate: string;
    points: string[];
    series: Series[];
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
const yAxisOptions = [
  { id: "entries", label: "Entries per day" },
  { id: "exits", label: "Exits per day" },
];

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
  props.series.filter((s) => visibleSeries.value[s.name] !== false),
);

const maxY = computed(() => {
  const values = activeSeries.value.flatMap((s) =>
    s.values.slice(safeZoomStart.value, safeZoomEnd.value + 1),
  );
  const max = Math.max(...values, 0);
  return max === 0 ? 1 : max;
});

const overviewMaxY = computed(() => {
  const values = activeSeries.value.flatMap((s) => s.values);
  const max = Math.max(...values, 0);
  return max === 0 ? 1 : max;
});

const visibleLines = computed(() =>
  activeSeries.value.map((s) => {
    const values = s.values.slice(safeZoomStart.value, safeZoomEnd.value + 1);
    const points = values
      .map((value, i) => {
        const x =
          visiblePoints.value.length <= 1
            ? 40
            : 40 + (940 * i) / (visiblePoints.value.length - 1);
        const y = 220 - (200 * value) / maxY.value;
        return `${x},${y}`;
      })
      .join(" ");
    return { name: s.name, color: s.color, points };
  }),
);

const overviewLines = computed(() =>
  activeSeries.value.map((s) => {
    const values = s.values.length ? s.values : [0];
    const points = values
      .map((value, i) => {
        const x = values.length <= 1 ? 0 : (1000 * i) / (values.length - 1);
        const y = 75 - (63 * value) / overviewMaxY.value;
        return `${x},${y}`;
      })
      .join(" ");
    return { name: s.name, color: s.color, points };
  }),
);

const tooltipRows = computed(() => {
  const idx = hoverIndex.value;
  if (idx == null) return [];
  return activeSeries.value.map((s) => ({
    name: s.name,
    color: s.color,
    value: s.values[safeZoomStart.value + idx] ?? 0,
  }));
});

const tooltipLeft = computed(() => {
  if (hoverX.value == null) return 10;
  return Math.min(Math.max(hoverX.value / 10 + 10, 10), 80);
});

const brushLeftPercent = computed(() =>
  percentForIndex(safeZoomStart.value, Math.max(props.points.length - 1, 0)),
);
const brushRightPercent = computed(() =>
  percentForIndex(safeZoomEnd.value, Math.max(props.points.length - 1, 0)),
);
const brushWidthPercent = computed(() =>
  Math.max(brushRightPercent.value - brushLeftPercent.value, 0),
);

function percentForIndex(index: number, maxIndex: number) {
  if (maxIndex <= 0) return 0;
  return (index / maxIndex) * 100;
}

function indexFromClientX(clientX: number) {
  const el = brushRef.value;
  if (!el || props.points.length === 0) return 0;
  const rect = el.getBoundingClientRect();
  const x = Math.min(Math.max(clientX - rect.left, 0), rect.width);
  const ratio = rect.width > 0 ? x / rect.width : 0;
  return Math.round(ratio * Math.max(props.points.length - 1, 0));
}

function setZoom(start: number, end: number) {
  const maxIndex = Math.max(props.points.length - 1, 0);
  const nextStart = Math.min(Math.max(start, 0), maxIndex);
  const nextEnd = Math.min(Math.max(end, nextStart), maxIndex);
  emit("update:zoomStart", nextStart);
  emit("update:zoomEnd", nextEnd);
}

function startDrag(mode: DragMode, pointerId: number, clientX: number) {
  dragState.value = {
    mode,
    pointerId,
    originIndex: indexFromClientX(clientX),
    startAtDown: safeZoomStart.value,
    endAtDown: safeZoomEnd.value,
  };
}

function onBrushPointerDown(e: PointerEvent) {
  if (props.points.length === 0) return;
  (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  const clickedIndex = indexFromClientX(e.clientX);
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
  if (clickedIndex >= safeZoomStart.value && clickedIndex <= safeZoomEnd.value) {
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
  const currentIndex = indexFromClientX(e.clientX);
  const delta = currentIndex - state.originIndex;
  const maxIndex = Math.max(props.points.length - 1, 0);

  if (state.mode === "move") {
    const width = state.endAtDown - state.startAtDown;
    let nextStart = state.startAtDown + delta;
    nextStart = Math.min(Math.max(nextStart, 0), Math.max(maxIndex - width, 0));
    setZoom(nextStart, nextStart + width);
    return;
  }

  if (state.mode === "start") {
    const nextStart = Math.min(
      Math.max(state.startAtDown + delta, 0),
      safeZoomEnd.value,
    );
    setZoom(nextStart, safeZoomEnd.value);
    return;
  }

  const nextEnd = Math.max(
    Math.min(state.endAtDown + delta, maxIndex),
    safeZoomStart.value,
  );
  setZoom(safeZoomStart.value, nextEnd);
}

function endDrag(pointerId: number) {
  if (dragState.value?.pointerId === pointerId) {
    dragState.value = null;
  }
}

function toggleSeries(name: string) {
  const current = visibleSeries.value[name] !== false;
  visibleSeries.value = { ...visibleSeries.value, [name]: !current };
}

function onMouseMove(e: MouseEvent) {
  if (!chartRef.value || visiblePoints.value.length === 0) return;
  const rect = chartRef.value.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const clamped = Math.min(Math.max(x, 0), rect.width);
  const ratio = rect.width > 0 ? clamped / rect.width : 0;
  const idx = Math.round(ratio * (visiblePoints.value.length - 1));
  const normalizedIndex = Math.min(Math.max(idx, 0), visiblePoints.value.length - 1);
  hoverIndex.value = normalizedIndex;
  hoverX.value =
    visiblePoints.value.length <= 1
      ? 40
      : 40 + (940 * normalizedIndex) / (visiblePoints.value.length - 1);
}

function onWindowPointerUp(e: PointerEvent) {
  endDrag(e.pointerId);
}

onMounted(() => {
  window.addEventListener("pointermove", onBrushPointerMove);
  window.addEventListener("pointerup", onWindowPointerUp);
  window.addEventListener("pointercancel", onWindowPointerUp);
});

onBeforeUnmount(() => {
  window.removeEventListener("pointermove", onBrushPointerMove);
  window.removeEventListener("pointerup", onWindowPointerUp);
  window.removeEventListener("pointercancel", onWindowPointerUp);
});
</script>
