<template>
  <!-- Error: retry -->
  <div
    v-if="error"
    class="flex flex-col items-center justify-center gap-2 rounded-lg bg-white px-4 py-8 shadow ring-1 ring-gray-200"
    role="alert"
  >
    <button
      type="button"
      class="text-red-600 underline hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1"
      @click="retry"
    >
      Failed to fetch data, click here to retry
    </button>
  </div>

  <!-- Loading (no data yet) -->
  <div
    v-else-if="loading"
    class="flex flex-col items-center justify-center gap-3 rounded-lg bg-white px-4 py-12 text-gray-500 shadow ring-1 ring-gray-200"
    aria-busy="true"
    aria-live="polite"
  >
    <span
      class="icon-spinner inline-block text-2xl animate-spin"
      aria-hidden="true"
    ></span>
    <span>loading data...</span>
  </div>

  <!-- Idle -->
  <div
    v-else-if="!hasLoadedOnce && !refreshing"
    class="rounded-lg bg-white px-4 py-12 text-center text-gray-400 shadow ring-1 ring-gray-200"
  >
    —
  </div>

  <!-- Content with refreshing overlay -->
  <div v-else class="relative">
    <div
      v-if="refreshing"
      class="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70"
      aria-busy="true"
      aria-label="Refreshing"
    >
      <span
        class="icon-spinner inline-block text-3xl animate-spin text-gray-500"
        aria-hidden="true"
      ></span>
    </div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard label="Free spots" :value="freeSpots" variant="green" />
      <StatCard label="Occupied spots" :value="occupiedSpots" variant="red" />
      <StatCard label="Inactive spots" :value="inactiveSpots" variant="amber" />
      <StatCard label="Open tickets" :value="openTickets" variant="slate" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, inject, onMounted, onUnmounted, watch, type Ref } from "vue";
import StatCard from "./StatCard.vue";
import { listSpots } from "../../api/spots";
import { listTickets } from "../../api/tickets";

const DASHBOARD_REFRESH_EVENT = "dashboard-refresh";

const props = withDefaults(defineProps<{ garageId?: number | null }>(), {
  garageId: undefined,
});

const dashboardRefreshAbortSignal = inject<Ref<AbortSignal | null>>(
  "dashboardRefreshAbortSignal",
  ref(null),
);

const loading = ref(false);
const refreshing = ref(false);
const error = ref(false);
const hasLoadedOnce = ref(false);

const freeSpots = ref(0);
const occupiedSpots = ref(0);
const inactiveSpots = ref(0);
const openTickets = ref(0);

const spotParams = () => ({
  ...(props.garageId != null ? { garage_id: props.garageId } : {}),
  limit: 1,
});

const ticketParams = () => ({
  ...(props.garageId != null ? { garage_id: props.garageId } : {}),
  state: "OPEN" as const,
  limit: 1,
});

async function fetch() {
  const hasData = hasLoadedOnce.value;

  if (!hasData) {
    loading.value = true;
    error.value = false;
  } else {
    refreshing.value = true;
  }

  const signal = dashboardRefreshAbortSignal?.value ?? undefined;
  const config = signal ? { signal } : undefined;

  try {
    const [freeRes, allSpotsRes, activeOnlyRes, openRes] = await Promise.all([
      listSpots({ ...spotParams(), only_free: true, active_only: true }, config),
      listSpots({ ...spotParams(), active_only: false }, config),
      listSpots({ ...spotParams(), active_only: true }, config),
      listTickets(ticketParams(), config),
    ]);

    freeSpots.value = freeRes.data.total;

    const totalActive = activeOnlyRes.data.total;
    const totalAll = allSpotsRes.data.total;

    inactiveSpots.value = Math.max(0, totalAll - totalActive);
    occupiedSpots.value = Math.max(0, totalActive - freeRes.data.total);
    openTickets.value = openRes.data.total;

    hasLoadedOnce.value = true;
    error.value = false;
  } catch (err: unknown) {
    if ((err as { code?: string })?.code === "ERR_CANCELED") return;

    error.value = true;

    if (!hasData) {
      freeSpots.value = 0;
      occupiedSpots.value = 0;
      inactiveSpots.value = 0;
      openTickets.value = 0;
    }
  } finally {
    loading.value = false;
    refreshing.value = false;
  }
}

function retry() {
  error.value = false;
  fetch();
}

function onDashboardRefresh() {
  fetch();
}

watch(
  () => props.garageId,
  () => {
    fetch();
  },
);

onMounted(() => {
  window.addEventListener(DASHBOARD_REFRESH_EVENT, onDashboardRefresh);
  fetch();
});

onUnmounted(() => {
  window.removeEventListener(DASHBOARD_REFRESH_EVENT, onDashboardRefresh);
});
</script>