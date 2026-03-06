<template>
  <div class="dashboard-sections">
    <div class="dashboard-toolbar flex items-center justify-end gap-3">
      <div class="dashboard-toolbar__refresh-info flex flex-col items-end gap-1">
        <span class="text-sm text-gray-500">Auto-refresh</span>
      </div>
      <RefreshCountdownRing
        :duration-ms="intervalMs"
        :remaining-ms="remainingMs"
        :enabled="isRunning"
        :auto-refresh-enabled="autoRefreshEnabled"
        @toggle-auto-refresh="toggleAutoRefresh"
      />
      <ButtonIn
        type="button"
        variant="outline"
        class="min-w-[50px] min-h-[50px] border-white/20 !bg-green-800 px-3 py-2 text-sm font-semibold text-white backdrop-blur-lg transition-all duration-300 ease-in-out hover:scale-110 hover:shadow-xl hover:border-emerald-400/40 hover:bg-emerald-600/80 sm:px-6 sm:text-base"
        @click="refreshAll"
        title="Refresh now"
        icon="icon-spinner11"
      />
    </div>
    <div class="by-garage-card dashboard-fade dashboard-fade--0">
      <GarageSelectDropdown v-model="selectedGarageId" :garages="garages" />
      <div
        v-if="selectedGarageId != null"
        class="by-garage-card__viewing by-garage-card__cell"
      >
        <span class="icon-eye text-lg text-gray-600"></span>
        <router-link
          :to="{ name: 'garage-detail', params: { id: selectedGarageId } }"
          class="font-semibold text-emerald-600 hover:text-emerald-700 hover:underline"
        >
          {{ selectedGarage?.name ?? "Garage" }}
        </router-link>
        <span class="text-base text-gray-500"
          >— click to open garage detail (spots & vehicles)</span
        >
      </div>
    </div>
    <div class="dashboard-fade dashboard-fade--1">
      <StatusCards ref="statusRef" :garage-id="selectedGarageId ?? undefined" />
    </div>
    <div class="dashboard-fade dashboard-fade--2">
      <GarageOverviewTable
        ref="garageRef"
        :garage-id="selectedGarageId ?? undefined"
      />
    </div>
    <div class="dashboard-fade dashboard-fade--3">
      <TicketActivity
        ref="ticketActivityRef"
        :garage-id="selectedGarageId ?? undefined"
        :key="selectedGarageId ?? 'all'"
      />
    </div>
    <div class="dashboard-fade dashboard-fade--4">
      <RevenueSummary
        ref="revenueRef"
        :garage-id="selectedGarageId ?? undefined"
      />
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
import StatusCards from "../components/StatusCards.vue";
import GarageOverviewTable from "../components/GarageOverviewTable.vue";
import TicketActivityTable from "../components/TicketActivityTable.vue";
import TicketActivity from "../components/TicketActivity.vue";
import RevenueSummary from "../components/RevenueSummary.vue";
import ButtonIn from "../components/ButtonIn.vue";
import RefreshCountdownRing from "../components/RefreshCountdownRing.vue";
import { useDashboardPolling } from "../composables/useDashboardPolling";
import { listGarages } from "../api/garages";
import type { Garage } from "../api/garages";
import GarageSelectDropdown from "../components/GarageSelectDropdown.vue";

const autoRefreshEnabled = inject<Ref<boolean>>(
  "autoRefreshEnabled",
  ref(true),
);
const garages = ref<Garage[]>([]);
const selectedGarageId = ref<number | null>(null);
const statusRef = ref<InstanceType<typeof StatusCards> | null>(null);
const garageRef = ref<InstanceType<typeof GarageOverviewTable> | null>(null);
const ticketRef = ref<InstanceType<typeof TicketActivityTable> | null>(null);
const revenueRef = ref<InstanceType<typeof RevenueSummary> | null>(null);
const ticketActivityRef = ref<InstanceType<typeof TicketActivity> | null>(null);

/** AbortController for the current refresh cycle; aborted when a new refresh starts or on unmount. */
const refreshAbortControllerRef = ref<AbortController | null>(null);
provide(
  "dashboardRefreshAbortSignal",
  computed(() => refreshAbortControllerRef.value?.signal ?? null),
);

const selectedGarage = computed(
  () => garages.value.find((g) => g.id === selectedGarageId.value) ?? null,
);

function refreshAll() {
  if (refreshAbortControllerRef.value) {
    refreshAbortControllerRef.value.abort();
  }
  refreshAbortControllerRef.value = new AbortController();
  statusRef.value?.refresh?.();
  garageRef.value?.refresh?.();
  ticketRef.value?.refresh?.();
  revenueRef.value?.refresh?.();
  ticketActivityRef.value?.refresh?.();
}

async function loadGarages() {
  try {
    const res = await listGarages({ limit: 200 });
    garages.value = res.data.items;
    if (garages.value.length === 1 && selectedGarageId.value == null) {
      selectedGarageId.value = garages.value[0].id;
    }
  } catch {
    garages.value = [];
  }
}

watch(selectedGarageId, () => {
  nextTick(refreshAll);
});

const { remainingMs, intervalMs, isRunning } = useDashboardPolling(
  refreshAll,
  { enabled: autoRefreshEnabled },
);

function toggleAutoRefresh() {
  autoRefreshEnabled.value = !autoRefreshEnabled.value;
}

onMounted(() => {
  loadGarages();
  refreshAll(); // load data immediately so it appears without clicking Refresh
  window.addEventListener("dashboard-refresh", refreshAll);
});
onUnmounted(() => {
  window.removeEventListener("dashboard-refresh", refreshAll);
  if (refreshAbortControllerRef.value) {
    refreshAbortControllerRef.value.abort();
  }
});

defineExpose({ refreshAll }); // expose refreshAll to parent components
</script>

<style scoped>
/* By garage selector card */
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
.by-garage-card__viewing {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 16rem;
  margin-left: auto;
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

/* Staggered fade-in (top to bottom) when dashboard is shown */
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
