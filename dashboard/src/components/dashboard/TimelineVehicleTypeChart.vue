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
            v-for="s in alignedSeries"
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
          @mousemove="onMouseMoveThrottled"
        >
          <svg
            class="h-full w-full"
            :viewBox="`0 0 ${TIMELINE_LAYOUT.main.viewBoxWidth} ${TIMELINE_LAYOUT.main.viewBoxHeight}`"
            preserveAspectRatio="none"
          >
            <!-- grid -->
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

            <g v-for="line in visibleLines" :key="line.id">
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
                :key="`hover-${line.id}`"
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
import { ref, toRef } from "vue";
import { useI18n } from "vue-i18n";
import StandardDropdown from "../ui/StandardDropdown.vue";
import {
  TIMELINE_LAYOUT,
  createRafThrottled,
  type TimelineSeries,
} from "../../composables/timelineChart.utils";
import { useTimelineMainChartState } from "../../composables/useTimelineMainChartState";

const { t } = useI18n();

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
const {
  yAxisOptions,
  visibleSeries,
  alignedSeries,
  safeZoomStart,
  safeZoomEnd,
  visiblePoints,
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
} = useTimelineMainChartState({
  points: toRef(props, "points"),
  series: toRef(props, "series"),
  zoomStart: toRef(props, "zoomStart"),
  zoomEnd: toRef(props, "zoomEnd"),
  chartRef,
  t: t as (key: string) => string,
});

function onStartInput(e: Event) {
  const value = Number((e.target as HTMLInputElement).value);
  emit("update:zoomStart", Math.min(value, safeZoomEnd.value));
}

function onEndInput(e: Event) {
  const value = Number((e.target as HTMLInputElement).value);
  emit("update:zoomEnd", Math.max(value, safeZoomStart.value));
}

function onMouseLeave() {
  clearHover();
}
const onMouseMoveThrottled = createRafThrottled((e: MouseEvent) => {
  setHoverFromMouse(e);
});
</script>