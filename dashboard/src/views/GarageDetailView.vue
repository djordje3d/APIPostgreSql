<template>
  <div class="dashboard-sections">
    <div class="flex items-center gap-4">
      <router-link to="/" class="text-gray-600 hover:text-gray-900"
        >&larr; {{ t('garageDetail.dashboard') }}</router-link
      >
      <h1 v-if="garage" class="text-2xl font-bold text-gray-900">
        {{ garage.name }}
      </h1>
      <h1 v-else class="text-2xl font-bold text-gray-900">
        {{ t('garageDetail.garage') }} #{{ $route.params.id }}
      </h1>
    </div>
    <div v-if="loading" class="text-gray-500">{{ t('garageDetail.loading') }}</div>
    <template v-else-if="garage">
      <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
        <p class="text-sm text-gray-600">
          {{ t('garageDetail.capacity') }}: {{ garage.capacity }} · {{ t('garageDetail.defaultRate') }}:
          {{ formatRate(garage.default_rate) }} RSD
        </p>
      </div>
      <RevenueSummary
        :today-revenue="revenueDash?.today_revenue ?? 0"
        :month-revenue="revenueDash?.month_revenue ?? 0"
        :unpaid-count="revenueDash?.unpaid_partially_paid_count ?? 0"
        :total-outstanding="revenueDash?.total_outstanding ?? 0"
        :loading="loading && revenueDash === null"
        :refreshing="false"
        :error="false"
        :has-loaded-once="revenueDash !== null"
      />
      <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
        <div class="border-b border-gray-200 px-4 py-3">
          <h2 class="text-lg font-semibold">{{ t('garageDetail.spots') }}</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th
                  class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
                >
                  {{ t('garageDetail.spot') }}
                </th>
                <th
                  class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
                >
                  {{ t('garageDetail.rentableSpots') }}
                </th>
                <th
                  class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
                >
                  {{ t('garageDetail.activeSpots') }}
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 bg-white">
              <tr v-for="s in spots" :key="s.id">
                <td class="px-4 py-3 font-medium">{{ s.code }}</td>
                <td class="px-4 py-3">{{ s.is_rentable ? t('garageDetail.yes') : t('garageDetail.no') }}</td>
                <td class="px-4 py-3">{{ s.is_active ? t('garageDetail.yes') : t('garageDetail.no') }}</td>
              </tr>
              <tr v-if="spots.length === 0">
                <td colspan="3" class="px-4 py-6 text-center text-gray-500">
                  {{ t('garageDetail.noSpots') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <PaginationBar
          :page="spotsPage"
          :page-size="spotsPageSize"
          :total="spotsTotal"
          @update:page="spotsPage = $event"
        />
      </div>

      <!-- Open tickets -->
      <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
        <div class="border-b border-gray-200 px-4 py-3">
          <h2 class="text-lg font-semibold">{{ t('garageDetail.openTickets') }}</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th
                  class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
                >
                {{ t('garageDetail.id') }}
                </th>
                <th
                  class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
                >
                  {{ t('garageDetail.entryTime') }}
                </th>
                <th
                  class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
                >
                  {{ t('garageDetail.spot') }}
                </th>
                <th
                  class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
                >
                  {{ t('garageDetail.plate') }}
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 bg-white">
              <tr v-for="t in openTickets" :key="t.id">
                <td class="px-4 py-3">{{ t.id }}</td>
                <td class="px-4 py-3 text-sm">
                  {{ formatTime(t.entry_time) }}
                </td>
                <td class="px-4 py-3">{{ t.spot_code ?? "–" }}</td>
                <td class="px-4 py-3">{{ t.licence_plate ?? "–" }}</td>
              </tr>
              <tr v-if="openTickets.length === 0">
                <td colspan="4" class="px-4 py-6 text-center text-gray-500">
                  {{ t('garageDetail.noOpenTickets') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
    <div v-else class="text-red-600">{{ t('garageDetail.garageNotFound') }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, inject, onMounted, onUnmounted, computed, provide } from "vue";
import type { Ref } from "vue";
import { useRoute } from "vue-router";
import { getGarage } from "../api/garages";
import { listSpots } from "../api/spots";
import { listTicketsDashboard } from "../api/tickets";
import { getDashboardAnalytics } from "../api/dashboard";
import type { DashboardAnalytics } from "../api/dashboard";
import { getTodayISO, getMonthStartEnd } from "../utils/dashboardDates";
import RevenueSummary from "../components/dashboard/RevenueSummary.vue";
import PaginationBar from "../components/ui/PaginationBar.vue";
import { formatTime, formatRate } from "../composables/useFormatters";
import { useDashboardPolling } from "../composables/useDashboardPolling";
import type { Garage } from "../api/garages";
import type { Spot } from "../api/spots"; 
import type { TicketDashboardRow } from "../api/tickets";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const autoRefreshEnabled = inject<Ref<boolean>>(
  "autoRefreshEnabled",
  ref(true),
);
const route = useRoute();
const garage = ref<Garage | null>(null);
const spots = ref<Spot[]>([]);
const openTickets = ref<TicketDashboardRow[]>([]);
const loading = ref(true);

/** AbortController for this view's refresh; aborted when fetch runs again or on unmount. */
const refreshAbortControllerRef = ref<AbortController | null>(null);
provide(
  "dashboardRefreshAbortSignal",
  computed(() => refreshAbortControllerRef.value?.signal ?? null),
);

const spotsPage = ref(1);
const spotsPageSize = ref(10);
const spotsTotal = ref(0);
const spotsOffset = computed(() => (spotsPage.value - 1) * spotsPageSize.value);
const revenueDash = ref<DashboardAnalytics | null>(null);

async function fetchSpots() {
  const id = Number(route.params.id);
  if (!id) return;
  const signal = refreshAbortControllerRef.value?.signal;
  const config = signal ? { signal } : undefined;
  try {
    const sRes = await listSpots(
      {
        garage_id: id,
        active_only: false,
        limit: spotsPageSize.value,
        offset: spotsOffset.value,
      },
      config
    );
    spots.value = sRes.data.items;
    spotsTotal.value = sRes.data.total;
  } catch {
    spots.value = [];
    spotsTotal.value = 0;
  }
}

async function fetch() {
  const id = Number(route.params.id);
  if (!id) return;
  if (refreshAbortControllerRef.value) {
    refreshAbortControllerRef.value.abort();
  }
  refreshAbortControllerRef.value = new AbortController();
  const signal = refreshAbortControllerRef.value.signal;
  const config = { signal };
  spotsPage.value = 1;
  loading.value = true;
  revenueDash.value = null;
  try {
    const today = getTodayISO();
    const { from: monthFrom, to: monthTo } = getMonthStartEnd();
    const [gRes, tRes, aRes] = await Promise.all([
      getGarage(id, config),
      listTicketsDashboard({ limit: 100 }, config),
      getDashboardAnalytics(
        {
          garage_id: id,
          today,
          month_from: monthFrom,
          month_to: monthTo,
        },
        config,
      ),
    ]);
    garage.value = gRes.data;
    openTickets.value = tRes.data.items.filter(
      (t) => t.garage_id === id && t.ticket_state === "OPEN",
    );
    revenueDash.value = aRes.data;
    await fetchSpots();
  } catch (err: unknown) {
    if ((err as { code?: string })?.code === "ERR_CANCELED") return;
    garage.value = null;
    spots.value = [];
    spotsTotal.value = 0;
    openTickets.value = [];
    revenueDash.value = null;
  } finally {
    loading.value = false;
  }
}

watch([spotsPage, spotsPageSize], () => {
  if (garage.value) fetchSpots();
});

useDashboardPolling(fetch, { intervalMs: 10_000, enabled: autoRefreshEnabled });
watch(() => route.params.id, fetch, { immediate: true });
onMounted(fetch);
onUnmounted(() => {
  if (refreshAbortControllerRef.value) {
    refreshAbortControllerRef.value.abort();
  }
});
</script>
