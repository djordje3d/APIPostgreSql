<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-100">
    <div class="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
      <div v-if="!garageId" class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800 shadow-sm">
        {{ t("garageDetail.invalidGarageId") }}
      </div>

      <template v-else>
        <template v-if="garageSec.loading && !garageSec.hasLoadedOnce">
          <section
            class="overflow-hidden rounded-3xl border border-slate-200 bg-white/90 shadow-sm ring-1 ring-white/60 backdrop-blur"
          >
            <div
              class="flex flex-col gap-5 px-5 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between"
            >
              <div class="min-w-0 space-y-3">
                <div class="flex flex-wrap items-center gap-3 text-sm text-slate-500">
                  <span class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700">
                    {{ t("garageDetail.dashboard") }}
                  </span>
                  <span class="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 font-medium text-emerald-700">
                    {{ t("garageDetail.loading") }}
                  </span>
                </div>

                <div>
                  <h1 class="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                    {{ t("garageDetail.garage") }} #{{ fallbackId }}
                  </h1>
                  <p class="mt-1 text-sm text-slate-500">
                    {{ t("garageDetail.loading") }}
                  </p>
                </div>
              </div>

              <div class="flex items-center justify-end gap-3">
                <RefreshCountdownRing
                  :duration-ms="intervalMs"
                  :remaining-ms="remainingMs"
                  :enabled="isRunning"
                  :auto-refresh-enabled="autoRefreshEnabled"
                  @toggle-auto-refresh="toggleAutoRefresh"
                />
                <button
                  type="button"
                  :title="t('garageDetail.refreshNow')"
                  class="inline-flex h-12 w-12 items-center justify-center rounded-2xl border border-emerald-200 bg-emerald-50 text-emerald-700 shadow-sm transition hover:-translate-y-0.5 hover:bg-emerald-100 hover:shadow focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                  @click="refreshNow"
                >
                  <span class="icon-spinner11 text-2xl" aria-hidden="true"></span>
                </button>
              </div>
            </div>
          </section>

          <div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
            <div class="lg:col-span-7">
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
                :unpaid-count="revenueSec.revenueDash?.unpaid_partially_paid_count ?? 0"
                :total-outstanding="revenueSec.revenueDash?.total_outstanding ?? 0"
                :loading="revenueSec.loading && !revenueSec.hasLoadedOnce"
                :refreshing="revenueSec.refreshing"
                :error="revenueSec.error"
                :has-loaded-once="revenueSec.hasLoadedOnce"
                @retry="retryRevenue"
              />
            </div>
          </div>

          <div class="mt-6 text-slate-500">
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
                <div class="flex flex-wrap items-center gap-3 text-sm text-slate-500">
                  <span class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700">
                    {{ t("garageDetail.dashboard") }}
                  </span>
                  <span class="inline-flex items-center rounded-full bg-red-50 px-3 py-1 font-medium text-red-700">
                    {{ t("garageDetail.loadFailed") }}
                  </span>
                </div>

                <div>
                  <h1 class="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
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
            class="mt-6"
            :garage="garageSec.garage"
            :fallback-id="fallbackId"
            :refreshing="garageSec.refreshing"
          />

          <div
            class="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-red-700 shadow-sm"
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
          <section class="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-red-700 shadow-sm">
            <GarageHeaderCard
              :garage="garageSec.garage"
              :fallback-id="fallbackId"
              :refreshing="garageSec.refreshing"
            />
            <div class="mt-4">
              {{ t("garageDetail.garageNotFound") }}
            </div>
          </section>
        </template>

        <template v-else>
          <!-- HERO / TOP PANEL -->
          <section
            class="dashboard-fade dashboard-fade--1 overflow-hidden rounded-3xl border border-slate-200 bg-white/90 shadow-sm ring-1 ring-white/60 backdrop-blur"
          >
            <div
              class="flex flex-col gap-5 px-5 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between"
            >
              <div class="min-w-0 space-y-3">
                <div class="flex flex-wrap items-center gap-3 text-sm text-slate-500">
                  <router-link
                    to="/"
                    class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700 transition hover:bg-slate-200 hover:text-slate-900"
                  >
                    &larr; {{ t("garageDetail.dashboard") }}
                  </router-link>

                  <span class="inline-flex items-center rounded-full bg-sky-50 px-3 py-1 font-medium text-sky-700">
                    ID: {{ garageSec.garage.id }}
                  </span>

                  <span
                    v-if="garageSec.refreshing || revenueSec.refreshing || spotsSec.refreshing || ticketsSec.refreshing"
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
                  <h1 class="truncate text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                    {{ garageSec.garage.name }}
                  </h1>
                  <p class="mt-1 text-sm text-slate-500">
                    {{ t("garageDetail.capacity") }}: {{ garageSec.garage.capacity }}
                    ·
                    {{ t("garageDetail.defaultRate") }}:
                    {{ garageSec.garage.default_rate }} RSD
                  </p>
                </div>
              </div>

              <div class="flex items-center justify-end gap-3">
                <RefreshCountdownRing
                  :duration-ms="intervalMs"
                  :remaining-ms="remainingMs"
                  :enabled="isRunning"
                  :auto-refresh-enabled="autoRefreshEnabled"
                  @toggle-auto-refresh="toggleAutoRefresh"
                />
                <button
                  type="button"
                  :title="t('garageDetail.refreshNow')"
                  class="inline-flex h-12 w-12 items-center justify-center rounded-2xl border border-emerald-200 bg-emerald-50 text-emerald-700 shadow-sm transition hover:-translate-y-0.5 hover:bg-emerald-100 hover:shadow focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                  @click="refreshNow"
                >
                  <span class="icon-spinner11 text-2xl" aria-hidden="true"></span>
                </button>
              </div>
            </div>
          </section>

          <!-- TOP GRID -->
          <div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12 lg:items-start">
            <div class="dashboard-fade dashboard-fade--2 lg:col-span-7">
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
                :unpaid-count="revenueSec.revenueDash?.unpaid_partially_paid_count ?? 0"
                :total-outstanding="revenueSec.revenueDash?.total_outstanding ?? 0"
                :loading="revenueSec.loading && !revenueSec.hasLoadedOnce"
                :refreshing="revenueSec.refreshing"
                :error="revenueSec.error"
                :has-loaded-once="revenueSec.hasLoadedOnce"
                @retry="retryRevenue"
              />
            </div>
          </div>

          <!-- CONTENT PANELS -->
          <div class="mt-6 grid grid-cols-1 gap-6">
            <section class="dashboard-fade dashboard-fade--4">
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
            </section>

            <section class="dashboard-fade dashboard-fade--5">
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
            </section>
          </div>
        </template>
      </template>
    </div>
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
    if (!garageId.value || !garageSec.hasLoadedOnce || refreshInProgress.value) {
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
    if (!garageId.value || !garageSec.hasLoadedOnce || refreshInProgress.value) {
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
</style>