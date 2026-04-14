<template>
  <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
    <div class="border-b border-gray-200 px-4 py-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h2 class="text-lg font-semibold text-gray-900">
          {{ t("timeline.title") }}
        </h2>

        <div class="flex items-center gap-3">
          <div class="w-[220px]">
            <StandardDropdown
              :label="t('timeline.yAxisMetric')"
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

          <div class="text-sm text-gray-500">
            {{ fromDate }} - {{ toDate }}
          </div>
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
          @mouseleave="onMouseLeave"
          @mousemove="onMouseMove"
        >
          <svg
            class="h-full w-full"
            viewBox="0 0 1000 260"
            preserveAspectRatio="none"
          >
            <!-- grid -->
            <line x1="40" y1="220" x2="980" y2="220" stroke="#d1d5db" />
            <line x1="40" y1="170" x2="980" y2="170" stroke="#f1f5f9" />
            <line x1="40" y1="120" x2="980" y2="120" stroke="#f1f5f9" />
            <line x1="40" y1="70" x2="980" y2="70" stroke="#f1f5f9" />
            <line x1="40" y1="20" x2="980" y2="20" stroke="#f8fafc" />

            <!-- y axis -->
            <line x1="40" y1="20" x2="40" y2="220" stroke="#d1d5db" />

            <g v-for="line in visibleLines" :key="line.name">
              <path
                :d="line.path"
                fill="none"
                :stroke="line.color"
                stroke-width="3"
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

            <!-- hover dots only -->
            <g v-if="hoverIndex != null">
              <circle
                v-for="line in visibleLines"
                :key="`hover-${line.name}`"
                :cx="line.plotPoints[hoverIndex]?.x"
                :cy="line.plotPoints[hoverIndex]?.y"
                r="4.5"
                :fill="line.color"
                stroke="white"
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
              {{ visiblePoints[hoverIndex] }}
            </div>

            <div
              v-for="row in tooltipRows"
              :key="row.name"
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

        <div class="mt-4 grid grid-cols-1 gap-2 md:grid-cols-2">
          <label class="text-sm text-gray-700">
            {{ t("timeline.zoomStartDay") }}
            <input
              type="range"
              min="0"
              :max="Math.max(points.length - 1, 0)"
              :value="safeZoomStart"
              class="w-full"
              @input="onStartInput"
            />
          </label>

          <label class="text-sm text-gray-700">
            {{ t("timeline.zoomEndDay") }}
            <input
              type="range"
              min="0"
              :max="Math.max(points.length - 1, 0)"
              :value="safeZoomEnd"
              class="w-full"
              @input="onEndInput"
            />
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import StandardDropdown from "../ui/StandardDropdown.vue";

const { t } = useI18n();

type Series = { name: string; values: number[]; color: string };
type PlotPoint = { x: number; y: number };

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
const hoverIndex = ref<number | null>(null);
const hoverX = ref<number | null>(null);
const visibleSeries = ref<Record<string, boolean>>({});

const yAxisOptions = computed(() => [
  { id: "entries", label: t("timeline.entriesPerDay") },
  { id: "exits", label: t("timeline.exitsPerDay") },
]);

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

const visibleLines = computed(() =>
  activeSeries.value.map((s) => {
    const values = s.values.slice(safeZoomStart.value, safeZoomEnd.value + 1);

    const plotPoints: PlotPoint[] = values.map((value, i) => {
      const x =
        visiblePoints.value.length <= 1
          ? 40
          : 40 + (940 * i) / (visiblePoints.value.length - 1);

      const y = 220 - (200 * value) / maxY.value;

      return { x, y };
    });

    return {
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
    name: s.name,
    color: s.color,
    value: s.values[safeZoomStart.value + idx] ?? 0,
  }));
});

const tooltipLeft = computed(() => {
  if (hoverX.value == null || !chartRef.value) return 12;

  const chartWidth = chartRef.value.clientWidth;
  const leftPx = (hoverX.value / 1000) * chartWidth + 12;

  return Math.min(Math.max(leftPx, 12), Math.max(chartWidth - 180, 12));
});

function toggleSeries(name: string) {
  const current = visibleSeries.value[name] !== false;
  visibleSeries.value = { ...visibleSeries.value, [name]: !current };
}

function onStartInput(e: Event) {
  const value = Number((e.target as HTMLInputElement).value);
  emit("update:zoomStart", Math.min(value, safeZoomEnd.value));
}

function onEndInput(e: Event) {
  const value = Number((e.target as HTMLInputElement).value);
  emit("update:zoomEnd", Math.max(value, safeZoomStart.value));
}

function onMouseLeave() {
  hoverIndex.value = null;
  hoverX.value = null;
}

function onMouseMove(e: MouseEvent) {
  if (!chartRef.value || visiblePoints.value.length === 0) return;

  const rect = chartRef.value.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const clamped = Math.min(Math.max(x, 0), rect.width);
  const ratio = rect.width > 0 ? clamped / rect.width : 0;
  const idx = Math.round(ratio * (visiblePoints.value.length - 1));
  const normalizedIndex = Math.min(
    Math.max(idx, 0),
    visiblePoints.value.length - 1,
  );

  hoverIndex.value = normalizedIndex;
  hoverX.value =
    visiblePoints.value.length <= 1
      ? 40
      : 40 + (940 * normalizedIndex) / (visiblePoints.value.length - 1);
}

function buildQuadraticSmoothPath(points: PlotPoint[]): string {
  if (points.length === 0) return "";
  if (points.length === 1) {
    return `M ${points[0].x} ${points[0].y}`;
  }
  if (points.length === 2) {
    return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
  }

  let d = `M ${points[0].x} ${points[0].y}`;

  for (let i = 0; i < points.length - 1; i++) {
    const current = points[i];
    const next = points[i + 1];
    const midX = (current.x + next.x) / 2;
    const midY = (current.y + next.y) / 2;

    d += ` Q ${current.x} ${current.y}, ${midX} ${midY}`;
  }

  const last = points[points.length - 1];
  d += ` T ${last.x} ${last.y}`;

  return d;
}
</script>