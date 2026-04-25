<template>
  <div class="dashboard-sections">
    <div
      v-if="!garageId"
      class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800 shadow-sm"
    >
      {{ t("garageDetail.invalidGarageId") }}
    </div>

    <template v-else>
      <template v-if="garageSec.loading && !garageSec.hasLoadedOnce">
        <section class="dashboard-card overflow-hidden">
          <div
            class="flex flex-col gap-5 px-5 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between"
          >
            <div class="min-w-0 space-y-3">
              <div
                class="flex flex-wrap items-center gap-3 text-sm text-slate-500"
              >
                <span
                  class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700"
                >
                  {{ t("garageDetail.dashboard") }}
                </span>
                <span
                  class="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 font-medium text-emerald-700"
                >
                  {{ t("garageDetail.loading") }}
                </span>
              </div>

              <div>
                <h1
                  class="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl"
                >
                  {{ t("garageDetail.garage") }} #{{ fallbackId }}
                </h1>
                <p class="mt-1 text-sm text-slate-500">
                  {{ t("garageDetail.loading") }}
                </p>
              </div>
            </div>

          </div>
        </section>

        <div
          class="dashboard-layout-lg lg:items-stretch lg:grid lg:grid-cols-12 lg:gap-6"
        >
          <div class="h-full lg:col-span-7">
            <GarageHeaderCard
              :garage="garageSec.garage"
              :fallback-id="fallbackId"
              :refreshing="garageSec.refreshing"
            />
          </div>
          <div class="lg:col-span-5">
            <RevenueSummary
              :today-revenue="revenueSec.revenueDash?.today_revenue ?? 0"
              :month-revenue="revenueSec.revenueDash?.month_revenue ?? 0"
              :unpaid-count="
                revenueSec.revenueDash?.unpaid_partially_paid_count ?? 0
              "
              :total-outstanding="
                revenueSec.revenueDash?.total_outstanding ?? 0
              "
              :loading="revenueSec.loading && !revenueSec.hasLoadedOnce"
              :refreshing="revenueSec.refreshing"
              :error="revenueSec.error"
              :has-loaded-once="revenueSec.hasLoadedOnce"
              @retry="retryRevenue"
            />
          </div>
        </div>

        <div class="text-slate-500">
          {{ t("garageDetail.loading") }}
        </div>
      </template>

      <template v-else-if="garageSec.error && !garageSec.garage">
        <section
          class="overflow-hidden rounded-3xl border border-red-200 bg-white shadow-sm"
        >
          <div
            class="flex flex-col gap-5 px-5 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between"
          >
            <div class="min-w-0 space-y-3">
              <div
                class="flex flex-wrap items-center gap-3 text-sm text-slate-500"
              >
                <span
                  class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700"
                >
                  {{ t("garageDetail.dashboard") }}
                </span>
                <span
                  class="inline-flex items-center rounded-full bg-red-50 px-3 py-1 font-medium text-red-700"
                >
                  {{ t("garageDetail.loadFailed") }}
                </span>
              </div>

              <div>
                <h1
                  class="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl"
                >
                  {{ t("garageDetail.garage") }} #{{ fallbackId }}
                </h1>
                <p class="mt-1 text-sm text-slate-500">
                  {{ t("garageDetail.loadFailed") }}
                </p>
              </div>
            </div>

            <button
              type="button"
              class="inline-flex items-center justify-center rounded-2xl border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-medium text-red-700 shadow-sm transition hover:bg-red-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
              @click="refreshNow"
            >
              {{ t("garageDetail.retryBtn") }}
            </button>
          </div>
        </section>

        <GarageHeaderCard
          :garage="garageSec.garage"
          :fallback-id="fallbackId"
          :refreshing="garageSec.refreshing"
        />

        <div
          class="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-red-700 shadow-sm"
          role="alert"
        >
          <p class="mb-2 font-medium">{{ t("garageDetail.loadFailed") }}</p>
          <button
            type="button"
            class="underline decoration-red-400 underline-offset-4 hover:text-red-900 focus:outline-none focus:ring-2 focus:ring-red-500"
            @click="refreshNow"
          >
            {{ t("garageDetail.retryBtn") }}
          </button>
        </div>
      </template>

      <template v-else-if="!garageSec.garage">
        <section
          class="flex flex-col gap-4 rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-red-700 shadow-sm"
        >
          <GarageHeaderCard
            :garage="garageSec.garage"
            :fallback-id="fallbackId"
            :refreshing="garageSec.refreshing"
          />
          <div>
            {{ t("garageDetail.garageNotFound") }}
          </div>
        </section>
      </template>

      <template v-else>
        <!-- HERO / TOP PANEL -->
        <section
          class="dashboard-fade dashboard-fade--1 dashboard-card overflow-hidden"
        >
          <div
            class="flex flex-col gap-5 px-5 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between"
          >
            <div class="min-w-0 space-y-3">
              <div
                class="flex flex-wrap items-center gap-3 text-sm text-slate-500"
              >
                <router-link
                  :to="{ name: 'dashboard' }"
                  class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700 transition hover:bg-slate-200 hover:text-slate-900"
                >
                  &larr; {{ t("garageDetail.dashboard") }}
                </router-link>

                <span
                  v-if="
                    garageSec.refreshing ||
                    revenueSec.refreshing ||
                    spotsSec.refreshing ||
                    ticketsSec.refreshing
                  "
                  class="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 font-medium text-emerald-700"
                >
                  {{ t("common.refreshing") }}
                </span>
                <span
                  v-else
                  class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700"
                >
                  {{ t("garageDetail.liveOverview") }}
                </span>
              </div>

              <div>
                <h1
                  class="truncate text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl"
                >
                  {{ garageSec.garage.name }}
                </h1>
              </div>
            </div>

          </div>
        </section>

        <!-- TOP GRID -->
        <div
          class="dashboard-layout-lg lg:items-stretch lg:grid lg:grid-cols-12 lg:gap-6"
        >
          <div class="dashboard-fade dashboard-fade--2 h-full lg:col-span-7">
            <GarageHeaderCard
              :garage="garageSec.garage"
              :fallback-id="fallbackId"
              :refreshing="garageSec.refreshing"
            />
          </div>

          <div class="dashboard-fade dashboard-fade--3 lg:col-span-5">
            <RevenueSummary
              :today-revenue="revenueSec.revenueDash?.today_revenue ?? 0"
              :month-revenue="revenueSec.revenueDash?.month_revenue ?? 0"
              :unpaid-count="
                revenueSec.revenueDash?.unpaid_partially_paid_count ?? 0
              "
              :total-outstanding="
                revenueSec.revenueDash?.total_outstanding ?? 0
              "
              :loading="revenueSec.loading && !revenueSec.hasLoadedOnce"
              :refreshing="revenueSec.refreshing"
              :error="revenueSec.error"
              :has-loaded-once="revenueSec.hasLoadedOnce"
              @retry="retryRevenue"
            />
          </div>
        </div>

        <!-- CONTENT PANELS (tab strip + v-show, aligned with DashboardView) -->
        <div class="dashboard-fade dashboard-fade--4">
          <div class="dashboard-card px-5 py-3">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="dashboard-tabs gap-5">
                <button
                  type="button"
                  class="dashboard-tab"
                  :class="{ 'dashboard-tab--active': activeDetailTab === 'spots' }"
                  @click="activeDetailTab = 'spots'"
                >
                  {{ t("garageDetail.spots") }}
                </button>
                <button
                  type="button"
                  class="dashboard-tab"
                  :class="{
                    'dashboard-tab--active': activeDetailTab === 'tickets',
                  }"
                  @click="activeDetailTab = 'tickets'"
                >
                  {{ t("garageDetail.openTickets") }}
                </button>
              </div>

              <div
                v-if="activeDetailTab === 'tickets'"
                class="flex min-w-0 flex-wrap items-center gap-3"
              >
                <div class="flex shrink-0 items-baseline gap-1.5">
                  <span
                    class="text-xs font-medium uppercase tracking-wide text-gray-500"
                  >
                    {{ t("dashboard.timeFrame") }}
                  </span>
                  <HelpTooltip
                    as-icon
                    :text="t('help.dashboard.timeFrame')"
                    :aria-label="t('help.aria.timeFrame')"
                  />
                </div>

                <div class="w-[220px] min-w-[10rem] max-w-full shrink-0">
                  <StandardDropdown
                    label=""
                    :options="timeFrameOptions"
                    :model-value="selectedTimeFrame"
                    :nullable="false"
                    @update:model-value="
                      selectedTimeFrame = ($event as string) ?? 'realtime'
                    "
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="dashboard-fade dashboard-fade--5">
          <div v-show="activeDetailTab === 'spots'">
            <GarageSpotsTable
              :spots="spotsSec.spots"
              :page="spotsSec.page"
              :page-size="spotsSec.pageSize"
              :total="spotsSec.total"
              :loading="spotsSec.loading"
              :refreshing="spotsSec.refreshing"
              :error="spotsSec.error"
              :has-loaded-once="spotsSec.hasLoadedOnce"
              @retry="retrySpots"
              @update:page="onSpotsPageUpdate"
            />
          </div>

          <div v-show="activeDetailTab === 'tickets'">
            <GarageOpenTicketsTable
              :open-tickets="ticketsSec.openTickets"
              :page="ticketsSec.page"
              :page-size="ticketsSec.pageSize"
              :total="ticketsSec.total"
              :loading="ticketsSec.loading"
              :refreshing="ticketsSec.refreshing"
              :error="ticketsSec.error"
              :has-loaded-once="ticketsSec.hasLoadedOnce"
              @retry="retryOpenTickets"
              @update:page="onTicketsPageUpdate"
            />
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import RevenueSummary from "../components/dashboard/RevenueSummary.vue";
import HelpTooltip from "../components/ui/HelpTooltip.vue";
import StandardDropdown from "../components/ui/StandardDropdown.vue";
import GarageHeaderCard from "../components/dashboard/GarageHeaderCard.vue";
import GarageSpotsTable from "../components/dashboard/GarageSpotsTable.vue";
import GarageOpenTicketsTable from "../components/dashboard/GarageOpenTicketsTable.vue";
import { DASHBOARD_REQUEST_REFRESH_EVENT } from "../constants/dashboardRefresh";
import { useGarageDetailContext } from "../composables/useGarageDetailContext";
import { useGarageDetailGarage } from "../composables/useGarageDetailGarage";
import { useGarageRevenue } from "../composables/useGarageRevenue";
import { useGarageSpots } from "../composables/useGarageSpots";
import { useGarageOpenTickets } from "../composables/useGarageOpenTickets";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const route = useRoute();

const { garageId, prepareRefreshCycle } = useGarageDetailContext();
const fallbackId = computed(() => String(route.params.id ?? ""));

const activeDetailTab = ref<"spots" | "tickets">("spots");
const selectedTimeFrame = ref("realtime");
const timeFrameOptions = computed(() => [
  { id: "realtime", label: t("dashboard.timeFrameRealtime") },
  { id: "last7", label: t("dashboard.timeFrameLast7") },
  { id: "last30", label: t("dashboard.timeFrameLast30") },
  { id: "last90", label: t("dashboard.timeFrameLast90") },
]);

const garageSec = useGarageDetailGarage(garageId);
const revenueSec = useGarageRevenue(garageId);
const spotsSec = useGarageSpots(garageId);
const ticketsSec = useGarageOpenTickets(garageId);

let refreshDepth = 0;
const refreshInProgress = ref(false);

let spotsPagAbort: AbortController | null = null;
let ticketsPagAbort: AbortController | null = null;

async function runRefreshCycle(): Promise<void> {
  const id = garageId.value;
  if (!id) return;

  refreshDepth++;
  refreshInProgress.value = true;

  spotsSec.page = 1;
  ticketsSec.page = 1;

  const signal = prepareRefreshCycle();

  try {
    await Promise.all([
      garageSec.fetchGarage(signal),
      revenueSec.fetchRevenue(signal),
      spotsSec.fetchSpots(signal),
      ticketsSec.fetchOpenTickets(signal),
    ]);
  } finally {
    refreshDepth--;
    if (refreshDepth === 0) refreshInProgress.value = false;
  }
}

function pollRefresh(): void {
  if (refreshInProgress.value) return;
  void runRefreshCycle();
}

function onGlobalRequestRefresh(): void {
  pollRefresh();
}

onMounted(() => {
  window.addEventListener(
    DASHBOARD_REQUEST_REFRESH_EVENT,
    onGlobalRequestRefresh,
  );
});

onUnmounted(() => {
  window.removeEventListener(
    DASHBOARD_REQUEST_REFRESH_EVENT,
    onGlobalRequestRefresh,
  );
});

function refreshNow(): void {
  void runRefreshCycle();
}

async function retryRevenue(): Promise<void> {
  if (!garageId.value || refreshInProgress.value) return;
  const c = new AbortController();
  await revenueSec.fetchRevenue(c.signal);
}

function onSpotsPageUpdate(page: number): void {
  spotsSec.page = page;
}

function onTicketsPageUpdate(page: number): void {
  ticketsSec.page = page;
}

function retrySpots(): void {
  if (!garageId.value || refreshInProgress.value) return;
  spotsPagAbort?.abort();
  spotsPagAbort = new AbortController();
  void spotsSec.fetchSpots(spotsPagAbort.signal);
}

function retryOpenTickets(): void {
  if (!garageId.value || refreshInProgress.value) return;
  ticketsPagAbort?.abort();
  ticketsPagAbort = new AbortController();
  void ticketsSec.fetchOpenTickets(ticketsPagAbort.signal);
}

watch(
  () => [spotsSec.page, spotsSec.pageSize] as const,
  () => {
    if (
      !garageId.value ||
      !garageSec.hasLoadedOnce ||
      refreshInProgress.value
    ) {
      return;
    }
    spotsPagAbort?.abort();
    spotsPagAbort = new AbortController();
    void spotsSec.fetchSpots(spotsPagAbort.signal);
  },
);

watch(
  () => [ticketsSec.page, ticketsSec.pageSize] as const,
  () => {
    if (
      !garageId.value ||
      !garageSec.hasLoadedOnce ||
      refreshInProgress.value
    ) {
      return;
    }
    ticketsPagAbort?.abort();
    ticketsPagAbort = new AbortController();
    void ticketsSec.fetchOpenTickets(ticketsPagAbort.signal);
  },
);

watch(
  () => selectedTimeFrame.value,
  () => {
    if (!garageId.value || !garageSec.hasLoadedOnce || refreshInProgress.value) {
      return;
    }
    if (activeDetailTab.value !== "tickets") return;
    ticketsSec.page = 1;
    ticketsPagAbort?.abort();
    ticketsPagAbort = new AbortController();
    void ticketsSec.fetchOpenTickets(ticketsPagAbort.signal);
  },
);

watch(
  garageId,
  (id) => {
    if (!id) {
      garageSec.garage = null;
      revenueSec.revenueDash = null;
      spotsSec.spots = [];
      spotsSec.total = 0;
      ticketsSec.openTickets = [];
      ticketsSec.total = 0;
      return;
    }
    void runRefreshCycle();
  },
  { immediate: true },
);
</script>

<style scoped>
.dashboard-fade {
  opacity: 0;
  transform: translateY(10px);
  animation: garageDetailFadeIn 0.45s ease-out forwards;
}

.dashboard-fade--1 {
  animation-delay: 0.05s;
}
.dashboard-fade--2 {
  animation-delay: 0.12s;
}
.dashboard-fade--3 {
  animation-delay: 0.2s;
}
.dashboard-fade--4 {
  animation-delay: 0.28s;
}
.dashboard-fade--5 {
  animation-delay: 0.36s;
}

@keyframes garageDetailFadeIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dashboard-tabs {
  display: flex;
  align-items: center;
}
.dashboard-tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 3rem;
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
</style>
