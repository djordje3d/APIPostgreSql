<template>
  <div class="dashboard-sections">
    <div class="dashboard-toolbar flex items-center justify-end gap-3">
      <div
        class="dashboard-toolbar__refresh-info flex flex-col items-end gap-1"
      >
      </div>

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
        title="Refresh now"
        class="flex min-h-[50px] min-w-[50px] cursor-pointer items-center justify-center rounded-lg bg-green-800 text-white transition-opacity hover:opacity-80 focus:outline focus:ring-2 focus:ring-emerald-500/50"
        @click="refreshAll"
        @keydown.enter.space.prevent="refreshAll"
      >
        <span class="icon-spinner11 text-2xl" aria-hidden="true"></span>
      </div>
    </div>

    <div class="by-garage-card dashboard-fade dashboard-fade--0">
      <GarageSelectDropdown v-model="selectedGarageId" :garages="garages" />
    </div>

    <div class="dashboard-fade dashboard-fade--1">
      <StatusCards :garage-id="selectedGarageId ?? undefined" />
    </div>

    <div class="dashboard-fade dashboard-fade--2">
      <GarageOverviewTable :garage-id="selectedGarageId ?? undefined" />
    </div>

    <div class="dashboard-fade dashboard-fade--3">
      <TicketActivity
        :garage-id="selectedGarageId ?? undefined"
        :key="selectedGarageId ?? 'all'"
      />
    </div>

    <div class="dashboard-fade dashboard-fade--4">
      <RevenueSummary :garage-id="selectedGarageId ?? undefined" />
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

import { useDashboardPolling } from "../composables/useDashboardPolling";
import { listGarages } from "../api/garages";
import type { Garage } from "../api/garages";
import type { ToastApi } from "../composables/useToast";

const DASHBOARD_REFRESH_EVENT = "dashboard-refresh";
const DASHBOARD_REQUEST_REFRESH_EVENT = "dashboard-request-refresh";

const toast = inject<ToastApi | null>("toast", null);
const autoRefreshEnabled = inject<Ref<boolean>>(
  "autoRefreshEnabled",
  ref(true),
);

const garages = ref<Garage[]>([]);
const selectedGarageId = ref<number | null>(null);

const refreshAbortControllerRef = ref<AbortController | null>(null);

provide(
  "dashboardRefreshAbortSignal",
  computed(() => refreshAbortControllerRef.value?.signal ?? null),
);

function prepareRefreshCycle() {
  refreshAbortControllerRef.value?.abort();
  refreshAbortControllerRef.value = new AbortController();
}

function refreshAll() {
  prepareRefreshCycle();
  window.dispatchEvent(new CustomEvent(DASHBOARD_REFRESH_EVENT));
}

function onDashboardRequestRefresh() {
  refreshAll();
}

async function loadGarages() {
  try {
    const res = await listGarages({ limit: 200 });
    garages.value = res.data.items;

    if (garages.value.length === 1 && selectedGarageId.value == null) {
      selectedGarageId.value = garages.value[0].id;
    }

    if (
      selectedGarageId.value != null &&
      !garages.value.some((g) => g.id === selectedGarageId.value)
    ) {
      selectedGarageId.value = null;
    }
  } catch {
    garages.value = [];
  }
}

watch(selectedGarageId, () => {
  nextTick(refreshAll);
});

const { remainingMs, intervalMs, isRunning } = useDashboardPolling(refreshAll, {
  enabled: autoRefreshEnabled,
});

function toggleAutoRefresh() {
  autoRefreshEnabled.value = !autoRefreshEnabled.value;
}

onMounted(() => {
  toast?.clearToast();
  loadGarages();
  refreshAll();
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
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid rgb(226 232 240);
  color: inherit;
  transition:
    box-shadow 0.2s,
    border-color 0.2s;
}
.by-garage-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: rgb(148 163 184);
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
@keyframes dashboardFadeIn {
  to {
    opacity: 1;
  }
}
</style>