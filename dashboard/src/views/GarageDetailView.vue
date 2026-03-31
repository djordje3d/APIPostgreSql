<template>
  <div class="dashboard-sections">
    <div v-if="!garageId" class="text-gray-500">
      {{ t("garageDetail.invalidGarageId") }}
    </div>

    <template v-else>
      <div class="dashboard-toolbar mb-4 flex items-center justify-end gap-3">
        <RefreshCountdownRing
          :duration-ms="intervalMs"
          :remaining-ms="remainingMs"
          :enabled="isRunning"
          :auto-refresh-enabled="autoRefreshEnabled"
          @toggle-auto-refresh="toggleAutoRefresh"
        />
        <div
          role="button"
          tabindex="0"
          :title="t('garageDetail.refreshNow')"
          class="flex cursor-pointer items-center justify-center rounded p-1.5 text-green-800 transition-opacity hover:opacity-80 focus:outline-none focus-visible:ring-2 focus:ring-emerald-500/50"
          @click="refreshNow"
          @keydown.enter.space.prevent="refreshNow"
        >
          <span class="icon-spinner11 text-4xl" aria-hidden="true"></span>
        </div>
      </div>

      <template v-if="garageSec.loading && !garageSec.hasLoadedOnce">
        <GarageHeaderCard
          :garage="garageSec.garage"
          :fallback-id="fallbackId"
          :refreshing="garageSec.refreshing"
        />
        <div class="mt-4 text-gray-500">
          {{ t("garageDetail.loading") }}
        </div>
      </template>

      <template v-else-if="garageSec.error && !garageSec.garage">
        <GarageHeaderCard
          :garage="garageSec.garage"
          :fallback-id="fallbackId"
          :refreshing="garageSec.refreshing"
        />
        <div
          class="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700"
          role="alert"
        >
          <p class="mb-2">{{ t("garageDetail.loadFailed") }}</p>
          <button
            type="button"
            class="underline hover:text-red-900 focus:outline-none focus:ring-2 focus:ring-red-500"
            @click="refreshNow"
          >
            {{ t("garageDetail.retryBtn") }}
          </button>
        </div>
      </template>

      <template v-else-if="!garageSec.garage">
        <GarageHeaderCard
          :garage="garageSec.garage"
          :fallback-id="fallbackId"
          :refreshing="garageSec.refreshing"
        />
        <div class="mt-4 text-red-600">
          {{ t("garageDetail.garageNotFound") }}
        </div>
      </template>

      <template v-else>
        <div
          class="dashboard-layout-lg lg:grid lg:grid-cols-12 lg:items-start lg:gap-6"
        >
          <div class="dashboard-fade dashboard-fade--1 lg:col-span-7">
            <GarageHeaderCard
              :garage="garageSec.garage"
              :fallback-id="fallbackId"
              :refreshing="garageSec.refreshing"
            />
          </div>
          <div class="dashboard-fade dashboard-fade--4 lg:col-span-5">
            <RevenueSummary
              class="max-lg:mt-4 lg:mt-0"
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

        <GarageSpotsTable
          class="dashboard-fade dashboard-fade--2 mt-4"
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

        <GarageOpenTicketsTable
          class="dashboard-fade dashboard-fade--3 mt-4"
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
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, inject, computed } from "vue";
import type { Ref } from "vue";
import { useRoute } from "vue-router";
import RevenueSummary from "../components/dashboard/RevenueSummary.vue";
import RefreshCountdownRing from "../components/dashboard/RefreshCountdownRing.vue";
import GarageHeaderCard from "../components/dashboard/GarageHeaderCard.vue";
import GarageSpotsTable from "../components/dashboard/GarageSpotsTable.vue";
import GarageOpenTicketsTable from "../components/dashboard/GarageOpenTicketsTable.vue";
import { useDashboardPolling } from "../composables/useDashboardPolling";
import { useGarageDetailContext } from "../composables/useGarageDetailContext";
import { useGarageDetailGarage } from "../composables/useGarageDetailGarage";
import { useGarageRevenue } from "../composables/useGarageRevenue";
import { useGarageSpots } from "../composables/useGarageSpots";
import { useGarageOpenTickets } from "../composables/useGarageOpenTickets";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const route = useRoute();

const autoRefreshEnabled = inject<Ref<boolean>>(
  "autoRefreshEnabled",
  ref(true),
);

const { garageId, prepareRefreshCycle } = useGarageDetailContext();
const fallbackId = computed(() => String(route.params.id ?? ""));

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

const { remainingMs, intervalMs, isRunning } = useDashboardPolling(
  pollRefresh,
  { intervalMs: 10_000, enabled: autoRefreshEnabled },
);

function refreshNow(): void {
  void runRefreshCycle();
}

function toggleAutoRefresh(): void {
  autoRefreshEnabled.value = !autoRefreshEnabled.value;
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
  animation: garageDetailFadeIn 0.4s ease-out forwards;
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
@keyframes garageDetailFadeIn {
  to {
    opacity: 1;
  }
}
</style>
