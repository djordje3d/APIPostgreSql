<template>
  <div class="dashboard-sections">
    <div class="dashboard-toolbar flex items-center justify-end gap-3">
      <div
        class="dashboard-toolbar__refresh-info flex flex-col items-end gap-1"
      ></div>
      <HelpTooltip :text="t('help.autoRefresh')">
        <RefreshCountdownRing
          :duration-ms="intervalMs"
          :remaining-ms="remainingMs"
          :enabled="isRunning"
          :auto-refresh-enabled="autoRefreshEnabled"
          @toggle-auto-refresh="toggleAutoRefresh"
        />
      </HelpTooltip>

      <div
        role="button"
        tabindex="0"
        :title="t('garageDetail.refreshNow')"
        class="flex cursor-pointer items-center justify-center rounded p-1.5 text-green-500 transition-opacity hover:opacity-80 focus:outline-none focus-visible:ring-2 focus:ring-green-500/50"
        @click="refreshAll"
        @keydown.enter.space.prevent="refreshAll"
      >
        <span class="icon-spinner11 text-[42px] leading-none" aria-hidden="true"></span>
      </div>
    </div>

    <div class="dashboard-layout-lg lg:items-stretch lg:grid lg:grid-cols-12 lg:gap-6">
      <div class="dashboard-fade dashboard-fade--1 h-full lg:col-span-5">
        <StatusCards
          :free-spots="analytics?.free_spots ?? 0"
          :occupied-spots="analytics?.occupied_spots ?? 0"
          :inactive-spots="analytics?.inactive_spots ?? 0"
          :open-tickets="analytics?.open_tickets ?? 0"
          :loading="analyticsLoading && !analyticsHasLoadedOnce"
          :refreshing="analyticsRefreshing"
          :error="analyticsError"
          :has-loaded-once="analyticsHasLoadedOnce"
          @retry="fetchAnalyticsOnly"
        />
      </div>

      <div
        class="by-garage-card dashboard-card dashboard-fade dashboard-fade--0 h-full p-4 lg:col-span-3"
      >
        <GarageSelectDropdown
          :model-value="selectedGarageId"
          :garages="garages"
          @update:model-value="onGarageSelect($event as number | null)"
        />
      </div>

      <div class="dashboard-fade dashboard-fade--4 h-full lg:col-span-4">
        <RevenueSummary
          class="h-full"
          :today-revenue="analytics?.today_revenue ?? 0"
          :month-revenue="analytics?.month_revenue ?? 0"
          :unpaid-count="analytics?.unpaid_partially_paid_count ?? 0"
          :total-outstanding="analytics?.total_outstanding ?? 0"
          :loading="analyticsLoading && !analyticsHasLoadedOnce"
          :refreshing="analyticsRefreshing"
          :error="analyticsError"
          :has-loaded-once="analyticsHasLoadedOnce"
          @retry="fetchAnalyticsOnly"
        />
      </div>
    </div>

    <div class="dashboard-fade dashboard-fade--2">
      <div class="dashboard-card p-3">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="dashboard-tabs">
            <button
              type="button"
              class="dashboard-tab"
              :class="{ 'dashboard-tab--active': activeTab === 'overview' }"
              @click="activeTab = 'overview'"
            >
              {{ t("dashboard.tabOverview") }}
            </button>
            <button
              type="button"
              class="dashboard-tab"
              :class="{ 'dashboard-tab--active': activeTab === 'tickets' }"
              @click="activeTab = 'tickets'"
            >
              {{ t("dashboard.tabTickets") }}
            </button>
            <button
              type="button"
              class="dashboard-tab"
              :class="{ 'dashboard-tab--active': activeTab === 'timeline' }"
              @click="activeTab = 'timeline'"
            >
              {{ t("dashboard.tabTimeline") }}
            </button>
          </div>

          <div
            v-if="activeTab !== 'overview'"
            class="w-full max-w-[240px]"
          >
            <div class="mb-1 flex items-center gap-1 text-gray-600">
              <span class="block text-sm">{{ t("dashboard.timeFrame") }}</span>
              <HelpTooltip
                as-icon
                :text="t('help.dashboard.timeFrame')"
                :aria-label="t('help.aria.timeFrame')"
              />
            </div>
            <StandardDropdown
              label=""
              :options="timeFrameOptions"
              :model-value="selectedTimeFrame"
              :nullable="false"
              @update:model-value="selectedTimeFrame = ($event as string) ?? 'realtime'"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-fade dashboard-fade--3">
      <div v-show="activeTab === 'overview'">
        <GarageOverviewTable
          :garage-id="selectedGarageId ?? undefined"
          :refresh-key="selectedTimeFrame"
        />
      </div>

      <div v-show="activeTab === 'tickets'">
        <TicketActivity
          :garage-id="selectedGarageId ?? undefined"
          :from-date="range.fromDate"
          :to-date="range.toDate"
        />
      </div>

      <div v-show="activeTab === 'timeline'">
        <TimelineVehicleTypeChartBrush
          :from-date="range.fromDate"
          :to-date="range.toDate"
          :points="timelinePoints"
          :series="timelineSeries"
          :y-axis-mode="timelineYAxisMode"
          :loading="timelineLoading"
          :refreshing="timelineRefreshing"
          :error="timelineError"
          :has-loaded-once="timelineHasLoadedOnce"
          :zoom-start="timelineZoomStart"
          :zoom-end="timelineZoomEnd"
          @update:y-axis-mode="timelineYAxisMode = $event"
          @update:zoom-start="timelineZoomStart = $event"
          @update:zoom-end="timelineZoomEnd = $event"
        />
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import {
  ref,
  computed,
  inject,
  provide,
  onMounted,
  onUnmounted,
  watch,
  nextTick,
} from "vue";
import type { Ref } from "vue";

import StatusCards from "../components/dashboard/StatusCards.vue";
import GarageOverviewTable from "../components/dashboard/GarageOverviewTable.vue";
import TicketActivity from "../components/dashboard/TicketActivity.vue";
import RevenueSummary from "../components/dashboard/RevenueSummary.vue";
import RefreshCountdownRing from "../components/dashboard/RefreshCountdownRing.vue";
import GarageSelectDropdown from "../components/dashboard/GarageSelectDropdown.vue";
import StandardDropdown from "../components/ui/StandardDropdown.vue";
import HelpTooltip from "../components/ui/HelpTooltip.vue";
import TimelineVehicleTypeChartBrush from "../components/dashboard/TimelineVehicleTypeChartBrush.vue";

import { useDashboardPolling } from "../composables/useDashboardPolling";
import { listGarages } from "../api/garages";
import type { Garage } from "../api/garages";
import type { ToastApi } from "../composables/useToast";
import { getDashboardAnalytics } from "../api/dashboard";
import type { DashboardAnalytics } from "../api/dashboard";
import { listTicketsDashboard } from "../api/tickets";
import type { TicketDashboardRow } from "../api/tickets";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import {
  readGaragesCache,
  writeGaragesCache,
} from "../utils/garageCache";
import { getTodayISO, getMonthStartEnd } from "../utils/dashboardDates";
import { DASHBOARD_WIDGET_FETCH_DONE } from "../constants/dashboardRefresh";

const DASHBOARD_REFRESH_EVENT = "dashboard-refresh";
const DASHBOARD_REQUEST_REFRESH_EVENT = "dashboard-request-refresh";

const WIDGET_FETCH_TIMEOUT_MS = 45_000;

const { t } = useI18n();
const route = useRoute(); /** Rute za dashboard . Čita se iz URL-a*/
const router = useRouter(); /** Router za dashboard . Koristi se za preusmeravanje na druge stranice */

const toast = inject<ToastApi | null>("toast", null);
const autoRefreshEnabled = inject<Ref<boolean>>(
  "autoRefreshEnabled",
  ref(true),
);

const garages = ref<Garage[]>([]);
const selectedGarageId = ref<number | null>(null);
const garageWatchReady = ref(false);

/** this function gets the garage id from the route params */
function garageIdParamAsString(): string | undefined {
  const raw = route.params.garageId;
  if (raw == null || raw === "") return undefined;
  if (Array.isArray(raw)) return raw[0];
  return String(raw);
}

/** this function applies the garage from the route params */
async function applyGarageFromRoute() {
  const s = garageIdParamAsString();
  if (s !== undefined && s !== "") {
    const n = Number.parseInt(s, 10);
    if (!Number.isFinite(n) || n <= 0) { /** Proverava da li je broj validan */
      await router.replace({ name: "dashboard" }); /** Ako je broj nevalidan, preusmerava na početnu stranicu */
      return;
    }
    selectedGarageId.value = n; /** Ako je broj validan, postavlja izabranu garazu */
    return;
  }
  selectedGarageId.value = null;
}

watch(
  () => route.params.garageId,
  () => {
    void applyGarageFromRoute();
  },
  { immediate: true },
);

function onGarageSelect(v: number | null) {
  const s = garageIdParamAsString();
  if (v == null && s === undefined) return;
  if (v != null && s === String(v)) return; /** Ako je izabrana garaza (u ovom slučaju v) ista kao i ona koja je već izabrana (u ovom slučaju s), funkcija se ne izvršava */
  if (v == null) {
    router.push({ name: "dashboard" });
  } else {
    router.push({ name: "dashboard", params: { garageId: String(v) } });
  }
}
const activeTab = ref<"overview" | "tickets" | "timeline">("overview");

const selectedTimeFrame = ref("realtime");
const timeFrameOptions = computed(() => [
  { id: "realtime", label: t("dashboard.timeFrameRealtime") },
  { id: "last7", label: t("dashboard.timeFrameLast7") },
  { id: "last30", label: t("dashboard.timeFrameLast30") },
  { id: "last90", label: t("dashboard.timeFrameLast90") },
]);

const analytics = ref<DashboardAnalytics | null>(null);
const analyticsLoading = ref(true);
const analyticsRefreshing = ref(false);
const analyticsError = ref(false);
const analyticsHasLoadedOnce = ref(false);

const timelineLoading = ref(true);
const timelineRefreshing = ref(false);
const timelineError = ref(false);
const timelineHasLoadedOnce = ref(false);
const timelineRows = ref<TicketDashboardRow[]>([]);
const timelineYAxisMode = ref<"entries" | "exits">("entries");
const timelineZoomStart = ref(0);
const timelineZoomEnd = ref(0);

const refreshAbortControllerRef = ref<AbortController | null>(null);
/** Monotonic id for each full dashboard refresh (widgets match in fetch finally). */
const refreshEpoch = ref(0);
/** Nested refresh runs (manual during poll) — only clear inProgress when depth hits 0. */
let refreshDepth = 0;
const refreshInProgress = ref(false);

provide(
  "dashboardRefreshAbortSignal",
  computed(() => refreshAbortControllerRef.value?.signal ?? null),
);

function formatIsoDate(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function buildDateRange(timeFrame: string): { fromDate: string; toDate: string } {
  const now = new Date();
  const end = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const start = new Date(end);
  const days =
    timeFrame === "last7"
      ? 7
      : timeFrame === "last30"
        ? 30
        : timeFrame === "last90"
          ? 90
          : 5;
  start.setDate(end.getDate() - (days - 1));
  return { fromDate: formatIsoDate(start), toDate: formatIsoDate(end) };
}

const range = computed(() => buildDateRange(selectedTimeFrame.value));
const timelinePoints = computed(() => {
  const points: string[] = [];
  const start = new Date(`${range.value.fromDate}T00:00:00`);
  const end = new Date(`${range.value.toDate}T00:00:00`);
  const cur = new Date(start);
  while (cur <= end) {
    points.push(formatIsoDate(cur));
    cur.setDate(cur.getDate() + 1);
  }
  return points;
});

const timelineSeries = computed(() => {
  const colorPalette = ["#ef4444", "#3b82f6", "#eab308", "#22c55e", "#a855f7", "#f97316"];
  const perType = new Map<string, Record<string, number>>();
  for (const row of timelineRows.value) {
    const daySource = timelineYAxisMode.value === "entries" ? row.entry_time : row.exit_time;
    const day = daySource ? daySource.slice(0, 10) : "";
    if (!day) continue;
    const typeName = row.vehicle_type?.trim() || "Other";
    if (!perType.has(typeName)) perType.set(typeName, {});
    const bucket = perType.get(typeName)!;
    bucket[day] = (bucket[day] ?? 0) + 1;
  }
  return Array.from(perType.entries()).map(([name, days], idx) => ({
    name,
    color: colorPalette[idx % colorPalette.length],
    values: timelinePoints.value.map((p) => days[p] ?? 0),
  }));
});

watch(timelinePoints, (points) => {
  const maxIdx = Math.max(points.length - 1, 0);
  timelineZoomStart.value = Math.min(timelineZoomStart.value, maxIdx);
  timelineZoomEnd.value = Math.min(Math.max(timelineZoomEnd.value, timelineZoomStart.value), maxIdx);
  if (timelineHasLoadedOnce.value && timelineZoomEnd.value === 0 && maxIdx > 0) {
    timelineZoomEnd.value = maxIdx;
  }
});

function prepareRefreshCycle() {
  refreshAbortControllerRef.value?.abort();
  refreshAbortControllerRef.value = new AbortController();
}

function waitForTwoWidgetFetches(epoch: number): Promise<void> {
  return new Promise((resolve) => {
    let received = 0;
    const onDone = (e: Event) => {
      const d = (e as CustomEvent<{ epoch?: number }>).detail;
      if (d?.epoch !== epoch) return;
      received++;
      if (received >= 2) {
        cleanup();
        resolve();
      }
    };
    const cleanup = () => {
      window.removeEventListener(DASHBOARD_WIDGET_FETCH_DONE, onDone);
      clearTimeout(tid);
    };
    const tid = setTimeout(() => {
      cleanup();
      resolve();
    }, WIDGET_FETCH_TIMEOUT_MS);
    window.addEventListener(DASHBOARD_WIDGET_FETCH_DONE, onDone);
  });
}

/** Funkcija koja se koristi za rekoncilijaciju izbora garaze */
async function reconcileGarageSelection() {
  const hasGarageParam = garageIdParamAsString() !== undefined;

  if (
    selectedGarageId.value != null &&
    garages.value.length > 0 &&
    !garages.value.some((g) => g.id === selectedGarageId.value)
  ) {
    await router.replace({ name: "dashboard" });
    return;
  }

  if (garages.value.length === 1 && !hasGarageParam) {
    await router.replace({
      name: "dashboard",
      params: { garageId: String(garages.value[0].id) },
    });
  }
}

async function loadGarages() {
  const cached = readGaragesCache();
  if (cached?.fresh) {
    garages.value = cached.items;
    await reconcileGarageSelection();
    return;
  }
  try {
    const res = await listGarages({ limit: 200 });
    garages.value = res.data.items;
    writeGaragesCache(res.data.items);
    await reconcileGarageSelection();
  } catch {
    garages.value = [];
  }
}

async function fetchAnalyticsOnly() {
  const hasData = analyticsHasLoadedOnce.value;
  if (!hasData) {
    analyticsLoading.value = true;
    analyticsError.value = false;
  } else {
    analyticsRefreshing.value = true;
  }

  const signal = refreshAbortControllerRef.value?.signal;
  const config = signal ? { signal } : undefined;
  const today = getTodayISO();
  const { from: monthFrom, to: monthTo } = getMonthStartEnd();

  try {
    const res = await getDashboardAnalytics(
      {
        garage_id: selectedGarageId.value ?? undefined,
        today,
        month_from: monthFrom,
        month_to: monthTo,
      },
      config,
    );
    analytics.value = res.data;
    analyticsError.value = false;
    analyticsHasLoadedOnce.value = true;
  } catch (err: unknown) {
    if ((err as { code?: string })?.code === "ERR_CANCELED") return;
    analyticsError.value = true;
    if (!hasData) {
      analytics.value = null;
    }
  } finally {
    analyticsLoading.value = false;
    analyticsRefreshing.value = false;
  }
}

async function fetchTimelineOnly() {
  const hasData = timelineRows.value.length > 0 || timelineHasLoadedOnce.value;
  if (!hasData) {
    timelineLoading.value = true;
    timelineError.value = false;
  } else {
    timelineRefreshing.value = true;
  }
  const signal = refreshAbortControllerRef.value?.signal;
  const config = signal ? { signal } : undefined;
  try {
    const res = await listTicketsDashboard(
      {
        ...(selectedGarageId.value != null ? { garage_id: selectedGarageId.value } : {}),
        from_date: range.value.fromDate,
        to_date: range.value.toDate,
        limit: 5000,
        offset: 0,
      },
      config,
    );
    timelineRows.value = res.data.items;
    timelineError.value = false;
    const maxIdx = Math.max(timelinePoints.value.length - 1, 0);
    if (!timelineHasLoadedOnce.value || timelineZoomEnd.value === 0) {
      timelineZoomStart.value = 0;
      timelineZoomEnd.value = maxIdx;
    }
    timelineHasLoadedOnce.value = true;
  } catch (err: unknown) {
    if ((err as { code?: string })?.code === "ERR_CANCELED") return;
    timelineError.value = true;
    if (!hasData) timelineRows.value = [];
  } finally {
    timelineLoading.value = false;
    timelineRefreshing.value = false;
  }
}

async function runRefreshCycle() {
  refreshDepth++;
  refreshInProgress.value = true;
  try {
    refreshEpoch.value++;
    const epoch = refreshEpoch.value;
    prepareRefreshCycle();
    const analyticsP = fetchAnalyticsOnly();
    const widgetsP = waitForTwoWidgetFetches(epoch);
    const timelineP = fetchTimelineOnly();
    window.dispatchEvent(
      new CustomEvent(DASHBOARD_REFRESH_EVENT, { detail: { epoch } }),
    );
    await Promise.all([analyticsP, widgetsP, timelineP]);
  } finally {
    refreshDepth--;
    if (refreshDepth === 0) refreshInProgress.value = false;
  }
}

/** Manual / user-driven: always runs (aborts in-flight via prepareRefreshCycle). */
function refreshAll() {
  void runRefreshCycle();
}

/** Polling: skip if a full cycle is still in flight to avoid aborting overview/tickets. */
function pollRefresh() {
  if (refreshInProgress.value) return;
  void runRefreshCycle();
}

function onDashboardRequestRefresh() {
  refreshAll();
}

watch(selectedGarageId, () => {
  if (!garageWatchReady.value) return;
  nextTick(refreshAll);
});

watch(selectedTimeFrame, () => {
  if (!garageWatchReady.value) return;
  nextTick(refreshAll);
});

watch(timelineYAxisMode, () => {
  const maxIdx = Math.max(timelinePoints.value.length - 1, 0);
  timelineZoomStart.value = Math.min(timelineZoomStart.value, maxIdx);
  timelineZoomEnd.value = Math.min(Math.max(timelineZoomEnd.value, timelineZoomStart.value), maxIdx);
});

const { remainingMs, intervalMs, isRunning } = useDashboardPolling(pollRefresh, {
  enabled: autoRefreshEnabled,
});

function toggleAutoRefresh() {
  autoRefreshEnabled.value = !autoRefreshEnabled.value;
}

onMounted(async () => {
  toast?.clearToast();
  await loadGarages();
  refreshAll();
  await nextTick();
  garageWatchReady.value = true;
  window.addEventListener(
    DASHBOARD_REQUEST_REFRESH_EVENT,
    onDashboardRequestRefresh,
  );
});

onUnmounted(() => {
  window.removeEventListener(
    DASHBOARD_REQUEST_REFRESH_EVENT,
    onDashboardRequestRefresh,
  );
  refreshAbortControllerRef.value?.abort();
});

defineExpose({ refreshAll });
</script>

<style scoped>
.by-garage-card {
  display: flex;
  flex-wrap: nowrap;
  align-items: stretch;
  gap: 1rem;
  height: 100%;
  color: inherit;
}
.by-garage-card__cell {
  flex-shrink: 0;
}
.garage-select {
  min-width: 12rem;
}
.by-garage-card__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}
.by-garage-card__title {
  font-weight: 600;
  color: rgb(30 41 59);
}
.by-garage-card__desc {
  font-size: 0.875rem;
  color: rgb(100 116 139);
}

.dashboard-fade {
  opacity: 0;
  animation: dashboardFadeIn 0.4s ease-out forwards;
}
.dashboard-fade--0 {
  animation-delay: 0s;
}
.dashboard-fade--1 {
  animation-delay: 0.15s;
}
.dashboard-fade--2 {
  animation-delay: 0.3s;
}
.dashboard-fade--3 {
  animation-delay: 0.45s;
}
.dashboard-fade--4 {
  animation-delay: 0.6s;
}
.dashboard-fade--5 {
  animation-delay: 0.75s;
}
.dashboard-tabs {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.dashboard-tab {
  border: 1px solid rgb(203 213 225);
  border-radius: 0.5rem;
  padding: 0.45rem 0.9rem;
  font-weight: 600;
  color: rgb(51 65 85);
  background: white;
}
.dashboard-tab--active {
  border-color: rgb(16 185 129);
  color: rgb(5 150 105);
  background: rgb(236 253 245);
}
@keyframes dashboardFadeIn {
  to {
    opacity: 1;
  }
}
</style>
