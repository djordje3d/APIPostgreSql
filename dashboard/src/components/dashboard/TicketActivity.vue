<template>
  <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
    <div class="border-b border-gray-200 px-4 py-3">
      <h2 class="text-lg font-semibold text-gray-900">
        {{ t("ticket.Last 10") }}
      </h2>
    </div>

    <div class="overflow-x-auto">
      <!-- Error: retry -->
      <div
        v-if="error"
        class="flex flex-col items-center justify-center gap-2 px-4 py-8 text-center"
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

      <!-- Loading (no data yet): spinner + text -->
      <div
        v-else-if="loading"
        class="flex flex-col items-center justify-center gap-3 px-4 py-12 text-gray-500"
        aria-busy="true"
        aria-live="polite"
      >
        <span
          class="icon-spinner11 inline-block text-2xl animate-spin"
          aria-hidden="true"
        ></span>
        <span>loading data...</span>
      </div>

      <!-- Idle -->
      <div
        v-else-if="!hasLoadedOnce && !refreshing"
        class="px-4 py-12 text-center text-gray-400"
      >
        —
      </div>

      <!-- Content -->
      <div v-else class="relative min-h-[120px]">
        <div
          v-if="refreshing"
          class="absolute inset-0 z-10 flex items-center justify-center bg-white/70"
          aria-busy="true"
          aria-label="Refreshing"
        >
          <span
            class="icon-spinner11 inline-block text-3xl animate-spin text-gray-500"
            aria-hidden="true"
          ></span>
        </div>

        <TicketTable
          :tickets="tickets"
          :rest-to-pay-map="restToPayMap"
          @view-ticket="viewTicket"
          @close-ticket="closeTicket"
          @open-payment="openPayment"
        />
      </div>
    </div>

    <!-- Payment modal -->
    <PaymentModal
      v-model="showPaymentModal"
      :ticket-id="paymentTicket?.id ?? 0"
      :fee="paymentTicket?.fee ?? null"
      :garage-name="paymentTicket?.garage_name ?? undefined"
      @close="closePaymentModal"
      @done="onPaymentDone"
    />

    <!-- View ticket detail modal -->
    <TicketDetailModal
      :model-value="!!viewingTicket"
      :ticket="viewingTicket"
      :ticket-image-url="ticketImageUrl"
      :barcode-image-src="barcodeImageSrc"
      :payments-loading="viewPaymentsLoading"
      :payments="viewPaymentsSorted"
      :payments-total="viewPaymentsTotal"
      @update:model-value="viewingTicket = null"
      @go-to-payment="
        (t) => {
          openPayment(t);
          viewingTicket = null;
        }
      "
    />
  </div>
</template>

<script setup lang="ts">
import {
  ref,
  computed,
  watch,
  nextTick,
  inject,
  onMounted,
  onUnmounted,
  type Ref,
} from "vue";
import { listTicketsDashboard, ticketExit } from "../../api/tickets";
import type { TicketDashboardRow } from "../../api/tickets";
import { baseURL } from "../../api/client";
import { getPaymentsByTicket } from "../../api/payments";
import type { Payment } from "../../api/payments";
import PaymentModal from "./PaymentModal.vue";
import { useI18n } from "vue-i18n";
import { generateCode39BarcodeImage } from "../../utils/code39";
import TicketTable from "./TicketTable.vue";
import TicketDetailModal from "./TicketDetailModal.vue";

const DASHBOARD_REFRESH_EVENT = "dashboard-refresh";
const DASHBOARD_REQUEST_REFRESH_EVENT = "dashboard-request-refresh";

const props = withDefaults(defineProps<{ garageId?: number | null }>(), {
  garageId: undefined,
});

const { t } = useI18n();

const dashboardRefreshAbortSignal = inject<Ref<AbortSignal | null>>(
  "dashboardRefreshAbortSignal",
  ref(null),
);

const loading = ref(false);
const refreshing = ref(false);
const error = ref(false);
const hasLoadedOnce = ref(false);

const tickets = ref<TicketDashboardRow[]>([]);
const viewingTicket = ref<TicketDashboardRow | null>(null);
const BARCODE_WIDTH = 360;

const barcodeImageSrc = computed(() => {
  const ticket = viewingTicket.value;
  if (!ticket) return "";

  const token = ticket.ticket_token ?? String(ticket.id);
  if (!token) return "";

  try {
    // Code 39 with Canvas2D returns `data:image/png;base64,...`.
    return generateCode39BarcodeImage(String(token), BARCODE_WIDTH);
  } catch (err) {
    console.error("Failed to generate Code 39 barcode:", err);
    return "";
  }
});

const viewPayments = ref<Payment[]>([]);
const viewPaymentsLoading = ref(false);

const paymentTicket = ref<TicketDashboardRow | null>(null);
const showPaymentModal = ref(false);

const restToPayMap = ref<Record<number, number>>({});
const paymentsCache = new Map<number, Payment[]>();

const PAYMENTS_VIEW_LIMIT = 50;

function invalidatePaymentsCache(ticketId?: number) {
  if (ticketId != null) paymentsCache.delete(ticketId);
  else paymentsCache.clear();
}

const viewPaymentsTotal = computed(() =>
  viewPayments.value.reduce((sum, p) => sum + parseFloat(p.amount), 0),
);

const viewPaymentsSorted = computed(() => {
  const list = [...viewPayments.value];
  list.sort((a, b) => {
    const ta = a.paid_at ? new Date(a.paid_at).getTime() : 0;
    const tb = b.paid_at ? new Date(b.paid_at).getTime() : 0;
    return tb - ta;
  });
  return list;
});

/** Image URL for the ticket modal. Use API origin for static paths so /uploads works (no /api prefix). */
const ticketImageUrl = computed(() => {
  const url = viewingTicket.value?.image_url;
  if (!url?.trim()) return undefined;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  const path = url.startsWith("/") ? url : `/${url}`;
  try {
    const api = new URL(
      baseURL,
      typeof window !== "undefined"
        ? window.location.origin
        : "http://localhost:8000",
    );
    return `${api.origin}${path}`;
  } catch {
    const base = baseURL.replace(/\/+$/, "");
    return base ? `${base}${path}` : path;
  }
});

async function fetchRestToPayForTickets(
  items: TicketDashboardRow[],
  config?: { signal?: AbortSignal },
) {
  const needRest = items.filter(
    (t) => t.ticket_state !== "OPEN" && t.payment_status !== "PAID",
  );

  if (needRest.length === 0) {
    restToPayMap.value = {};
    return;
  }

  const map: Record<number, number> = {};

  await Promise.all(
    needRest.map(async (t) => {
      const feeNum =
        t.fee != null && t.fee !== "" ? parseFloat(String(t.fee)) : 0;
      const fee = Number.isNaN(feeNum) ? 0 : feeNum;

      try {
        const res = await getPaymentsByTicket(t.id, { limit: 500 }, config);
        const totalPaid = res.data.items.reduce(
          (sum, p) => sum + parseFloat(p.amount),
          0,
        );
        map[t.id] = Math.max(0, fee - totalPaid);
      } catch {
        map[t.id] = fee;
      }
    }),
  );

  restToPayMap.value = { ...map };
}

async function fetchPaymentsForView(
  ticketId: number,
  config?: { signal?: AbortSignal },
) {
  const cached = paymentsCache.get(ticketId);
  if (cached !== undefined) {
    viewPayments.value = cached;
    return;
  }

  viewPaymentsLoading.value = true;
  viewPayments.value = [];

  try {
    const res = await getPaymentsByTicket(
      ticketId,
      { limit: PAYMENTS_VIEW_LIMIT },
      config,
    );
    const items = res.data.items;
    viewPayments.value = items;
    paymentsCache.set(ticketId, items);
  } catch {
    viewPayments.value = [];
  } finally {
    viewPaymentsLoading.value = false;
  }
}

function viewTicket(t: TicketDashboardRow) {
  viewingTicket.value = t;
  const signal = dashboardRefreshAbortSignal?.value ?? undefined;
  fetchPaymentsForView(t.id, signal ? { signal } : undefined);
}

function openPayment(t: TicketDashboardRow) {
  paymentTicket.value = t;
  showPaymentModal.value = true;
}

async function closeTicket(id: number) {
  try {
    await ticketExit(id);
    window.dispatchEvent(new CustomEvent(DASHBOARD_REQUEST_REFRESH_EVENT));
  } catch {
    // optionally show toast
  }
}

// Razlika window.dispatchEvent i Pinia je da window.dispatchEvent moze da se koristi u bilo kom delu koda, 
// dok Pinia moze da se koristi samo u komponentama. Pinia je bolji za state management, a window.dispatchEvent je bolji za event handling.

function closePaymentModal() {
  showPaymentModal.value = false;
  nextTick(() => {
    paymentTicket.value = null;
  });
}

function onPaymentDone() {
  invalidatePaymentsCache(paymentTicket.value?.id);
  showPaymentModal.value = false;

  nextTick(() => {
    paymentTicket.value = null;
    window.dispatchEvent(new CustomEvent(DASHBOARD_REQUEST_REFRESH_EVENT));
  });
}

async function fetch() {
  const hasData = tickets.value.length > 0 || hasLoadedOnce.value;

  if (!hasData) {
    loading.value = true;
    error.value = false;
    restToPayMap.value = {};
  } else {
    refreshing.value = true;
  }

  const signal = dashboardRefreshAbortSignal?.value ?? undefined;
  const config = signal ? { signal } : undefined;

  try {
    const res = await listTicketsDashboard(
      {
        ...(props.garageId != null ? { garage_id: props.garageId } : {}),
        limit: 10,
        offset: 0,
      },
      config,
    );

    tickets.value = res.data.items;
    await fetchRestToPayForTickets(tickets.value, config);

    hasLoadedOnce.value = true;
    error.value = false;
  } catch (err: unknown) {
    if ((err as { code?: string })?.code === "ERR_CANCELED") return;

    error.value = true;

    if (!hasData) {
      tickets.value = [];
      restToPayMap.value = {};
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
