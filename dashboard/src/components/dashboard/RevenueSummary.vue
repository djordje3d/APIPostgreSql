<template>
  <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
    <h2 class="mb-4 text-lg font-semibold text-gray-900">{{ t('paymenetsRevenue.title') }}</h2>

    <div
      v-if="error"
      class="flex flex-col items-center justify-center gap-2 py-8 text-center"
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

    <div
      v-else-if="loading"
      class="flex flex-col items-center justify-center gap-3 py-12 text-gray-500"
      aria-busy="true"
      aria-live="polite"
    >
      <span
        class="icon-spinner5 inline-block text-2xl animate-spin"
        aria-hidden="true"
      ></span>
      <span>loading data...</span>
    </div>

    <div
      v-else-if="!hasLoadedOnce && !refreshing"
      class="py-12 text-center text-gray-400"
    >
      —
    </div>

    <div v-else class="relative min-h-[100px]">
      <div
        v-if="refreshing"
        class="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70"
        aria-busy="true"
        aria-label="Refreshing"
      >
        <span
          class="icon-spinner3 inline-block text-3xl animate-spin text-gray-500"
          aria-hidden="true"
        ></span>
      </div>

      <div class="space-y-4">
        <SummaryRow :label="t('paymenetsRevenue.todayRevenue')" :value="formatMoney(todayRevenue)" />
        <SummaryRow :label="t('paymenetsRevenue.thisMonthRevenue')" :value="formatMoney(monthRevenue)" />
        <SummaryRow
          :label="t('paymenetsRevenue.unpaidPartiallyPaidTickets')"
          :value="unpaidCount"
          value-class="text-amber-700"
        />
        <SummaryRow
          :label="t('paymenetsRevenue.restToPayDescription')"
          :value="formatMoney(totalOutstanding)"
          value-class="text-amber-700"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, inject, onMounted, onUnmounted, watch, type Ref } from "vue";
import SummaryRow from "./SummaryRow.vue";
import { formatMoney } from "../../composables/useFormatters";
import { listPayments, getOutstanding } from "../../api/payments";
import { listTickets } from "../../api/tickets";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

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
const todayRevenue = ref(0);
const monthRevenue = ref(0);
const unpaidCount = ref(0);
const totalOutstanding = ref(0);

function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getTodayISO() {
  return formatLocalDate(new Date());
}

function getMonthStartEnd() {
  const d = new Date();
  const start = new Date(d.getFullYear(), d.getMonth(), 1);
  const end = new Date(d.getFullYear(), d.getMonth() + 1, 0);

  return {
    from: formatLocalDate(start),
    to: formatLocalDate(end),
  };
}

const paymentParams = (from: string, to: string) => ({
  from,
  to,
  limit: 1000,
  ...(props.garageId != null ? { garage_id: props.garageId } : {}),
});

const ticketParams = (paymentStatus: "UNPAID" | "PARTIALLY_PAID") => ({
  payment_status: paymentStatus,
  limit: 1,
  ...(props.garageId != null ? { garage_id: props.garageId } : {}),
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
    const today = getTodayISO();
    const { from: monthFrom, to: monthTo } = getMonthStartEnd();

    const [todayRes, monthRes, unpaidRes, partialRes, outstandingRes] =
      await Promise.all([
        listPayments(paymentParams(today, today), config),
        listPayments(paymentParams(monthFrom, monthTo), config),
        listTickets(ticketParams("UNPAID"), config),
        listTickets(ticketParams("PARTIALLY_PAID"), config),
        getOutstanding(props.garageId, config),
      ]);

    todayRevenue.value = todayRes.data.items.reduce(
      (sum, p) => sum + parseFloat(p.amount),
      0,
    );
    monthRevenue.value = monthRes.data.items.reduce(
      (sum, p) => sum + parseFloat(p.amount),
      0,
    );
    unpaidCount.value = unpaidRes.data.total + partialRes.data.total;
    totalOutstanding.value = outstandingRes.data.total_outstanding ?? 0;

    hasLoadedOnce.value = true;
    error.value = false;
  } catch (err: unknown) {
    if ((err as { code?: string })?.code === "ERR_CANCELED") return;

    error.value = true;

    if (!hasData) {
      todayRevenue.value = 0;
      monthRevenue.value = 0;
      unpaidCount.value = 0;
      totalOutstanding.value = 0;
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