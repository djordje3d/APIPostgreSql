<template>
  <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
    <div class="border-b border-gray-200 px-4 py-3">
      <h2 class="text-lg font-semibold text-gray-900">
        Ticket activity (last 10)
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

        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                Garage
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                Plate
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                Spot
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                Entry time
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                Exit time
              </th>
              <th
                class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500"
              >
                Fee
              </th>
              <th
                class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500"
              >
                Rest to pay
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                Ticket ID
              </th>
              <th
                class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500"
              >
                Actions
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-200 bg-white">
            <tr v-for="t in tickets || []" :key="t.id" class="hover:bg-gray-50">
              <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {{ t.garage_name ?? "–" }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900"
              >
                {{ t.licence_plate ?? "–" }}
              </td>

              <td class="px-4 py-3 text-sm text-gray-700">
                {{ t.spot_code ?? "–" }}
              </td>

              <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {{ formatTime(t.entry_time) }}
              </td>

              <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {{ formatTime(t.exit_time) }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-700"
              >
                {{ formatMoney(t.fee) }}
              </td>

              <td
                class="whitespace-nowrap px-4 py-3 text-right text-sm font-medium"
                :class="restToPayClass(t)"
              >
                {{ formatRestToPay(t) }}
              </td>

              <td class="px-4 py-3">
                <span
                  class="font-mono text-sm tracking-[0.25em] text-gray-800"
                  aria-label="Ticket ID"
                >
                  {{ t.id }}
                </span>
              </td>

              <td class="whitespace-nowrap px-4 py-3 text-right text-sm">
                <button
                  type="button"
                  class="icon-barcode text-2xl font-bold text-slate-800 hover:text-slate-900"
                  title="View ticket & payments"
                  @click="viewTicket(t)"
                  style="line-height: 1"
                ></button>

                <template v-if="t.ticket_state === 'OPEN'">
                  <button
                    type="button"
                    class="icon-exit ml-2 text-2xl font-bold text-amber-600 hover:text-amber-800"
                    title="Close ticket"
                    @click="closeTicket(t.id)"
                  ></button>
                </template>

                <template
                  v-else-if="
                    t.ticket_state === 'CLOSED' && t.payment_status !== 'PAID'
                  "
                >
                  <button
                    type="button"
                    class="icon-credit-card ml-2 text-2xl font-bold text-emerald-600 hover:text-emerald-800"
                    title="Go to payment"
                    @click="openPayment(t)"
                  ></button>
                </template>
              </td>
            </tr>

            <tr v-if="(tickets || []).length === 0">
              <td colspan="9" class="px-4 py-6 text-center text-gray-500">
                No tickets
              </td>
            </tr>
          </tbody>
        </table>
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
    <Modal
      :model-value="!!viewingTicket"
      @update:model-value="viewingTicket = null"
      :title="
        viewingTicket
          ? `${viewingTicket.garage_name ?? '–'} — Ticket #${viewingTicket.id}`
          : ''
      "
    >
      <template v-if="viewingTicket">
        <div v-if="ticketImageUrl" class="mb-4">
          <ImageIn
            :key="`ticket-img-${viewingTicket.id}-${ticketImageUrl}`"
            :src="ticketImageUrl"
            :alt="`Ticket #${viewingTicket.id}`"
          />
        </div>
        <dl class="space-y-2 text-sm">
          <div>
            <dt class="text-gray-500">Garage</dt>
            <dd>{{ viewingTicket.garage_name ?? "–" }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">Plate</dt>
            <dd>{{ viewingTicket.licence_plate ?? "–" }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">Spot</dt>
            <dd>{{ viewingTicket.spot_code ?? "–" }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">Entry time</dt>
            <dd>{{ formatTime(viewingTicket.entry_time) }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">Exit time</dt>
            <dd>{{ formatTime(viewingTicket.exit_time) || "–" }}</dd>
          </div>
          <div>
            <dt class="text-gray-500">Fee</dt>
            <dd>{{ formatMoney(viewingTicket.fee) }}</dd>
          </div>
        </dl>

        <div class="mt-4 border-t border-gray-200 pt-4">
          <dt class="text-xs font-medium uppercase text-gray-500">
            Ticket ID (barcode)
          </dt>
          <dd class="mt-2 flex flex-col items-center gap-2">
            <canvas
              ref="barcodeCanvasRef"
              class="max-w-full rounded border border-gray-200 bg-white"
              aria-label="Barcode for ticket"
            />
            <span class="font-mono text-sm tracking-[0.35em] text-gray-600">
              {{ viewingTicket.id }}
            </span>
          </dd>
        </div>

        <div class="mt-4 border-t border-gray-200 pt-4">
          <h4 class="text-sm font-semibold text-gray-800">
            Evidence of payments
          </h4>
          <p class="mt-0.5 text-xs text-gray-500">
            All payments for this ticket (amount and when paid).
          </p>

          <div v-if="viewPaymentsLoading" class="mt-3 text-sm text-gray-500">
            Loading…
          </div>

          <div
            v-else-if="!viewPayments.length"
            class="mt-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-center text-sm text-gray-500"
          >
            No payments recorded.
          </div>

          <div
            v-else
            class="mt-3 overflow-hidden rounded-lg border border-gray-200"
          >
            <table class="min-w-full divide-y divide-gray-200 text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th
                    scope="col"
                    class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500"
                  >
                    #
                  </th>
                  <th
                    scope="col"
                    class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500"
                  >
                    Amount
                  </th>
                  <th
                    scope="col"
                    class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500"
                  >
                    When
                  </th>
                  <th
                    scope="col"
                    class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500"
                  >
                    Method
                  </th>
                </tr>
              </thead>

              <tbody class="divide-y divide-gray-200 bg-white">
                <tr
                  v-for="(p, idx) in viewPaymentsSorted"
                  :key="p.id"
                  class="hover:bg-gray-50"
                >
                  <td class="whitespace-nowrap px-3 py-2 text-gray-600">
                    {{ idx + 1 }}
                  </td>
                  <td
                    class="whitespace-nowrap px-3 py-2 text-right font-medium text-gray-900"
                  >
                    {{ formatMoney(p.amount) }}
                  </td>
                  <td class="whitespace-nowrap px-3 py-2 text-gray-700">
                    {{ formatTime(p.paid_at) }}
                  </td>
                  <td class="px-3 py-2 text-right text-gray-600">
                    {{ p.method ?? "–" }}
                  </td>
                </tr>
              </tbody>

              <tfoot class="bg-gray-50">
                <tr>
                  <td
                    colspan="2"
                    class="px-3 py-2 text-right text-xs font-semibold uppercase text-gray-600"
                  >
                    Total paid
                  </td>
                  <td
                    colspan="2"
                    class="whitespace-nowrap px-3 py-2 text-right font-semibold text-gray-900"
                  >
                    {{ formatMoney(String(viewPaymentsTotal)) }}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <div class="mt-4 flex justify-between gap-2">
          <ButtonIn
            type="button"
            variant="outline"
            @click="viewingTicket = null"
          >
            Close
          </ButtonIn>

          <ButtonIn
            v-if="
              viewingTicket.ticket_state === 'CLOSED' &&
              viewingTicket.payment_status !== 'PAID'
            "
            type="button"
            variant="primary"
            @click="
              openPayment(viewingTicket);
              viewingTicket = null;
            "
          >
            Go to payment
          </ButtonIn>
        </div>
      </template>
    </Modal>
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
import JsBarcode from "jsbarcode";
import { formatTime, formatMoney } from "../../composables/useFormatters";
import { listTicketsDashboard, ticketExit } from "../../api/tickets";
import type { TicketDashboardRow } from "../../api/tickets";
import { baseURL } from "../../api/client";
import { getPaymentsByTicket } from "../../api/payments";
import type { Payment } from "../../api/payments";
import Modal from "../ui/Modal.vue";
import PaymentModal from "./PaymentModal.vue";
import ButtonIn from "../ui/ButtonIn.vue";
import ImageIn from "../ui/ImageIn.vue";

const DASHBOARD_REFRESH_EVENT = "dashboard-refresh";
const DASHBOARD_REQUEST_REFRESH_EVENT = "dashboard-request-refresh";

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

const tickets = ref<TicketDashboardRow[]>([]);
const viewingTicket = ref<TicketDashboardRow | null>(null);

const viewPayments = ref<Payment[]>([]);
const viewPaymentsLoading = ref(false);

const paymentTicket = ref<TicketDashboardRow | null>(null);
const showPaymentModal = ref(false);

const restToPayMap = ref<Record<number, number>>({});
const paymentsCache = new Map<number, Payment[]>();

const barcodeCanvasRef = ref<HTMLCanvasElement | null>(null);

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
    const api = new URL(baseURL, typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");
    return `${api.origin}${path}`;
  } catch {
    const base = baseURL.replace(/\/+$/, "");
    return base ? `${base}${path}` : path;
  }
});

function formatRestToPay(t: TicketDashboardRow): string {
  if (t.ticket_state === "OPEN") return "–";
  if (t.payment_status === "PAID") return "0 RSD";

  const rest = restToPayMap.value[t.id];
  if (rest !== undefined) return formatMoney(String(rest));

  if (t.ticket_state === "CLOSED" && t.payment_status !== "PAID") return "…";
  return "–";
}

function restToPayClass(t: TicketDashboardRow): string {
  if (t.payment_status === "PAID" || t.ticket_state === "OPEN") {
    return "text-gray-500";
  }
  return "text-amber-700";
}

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

function renderBarcodeImage(ticketId: number) {
  const canvas = barcodeCanvasRef.value;
  if (!canvas) return;

  try {
    JsBarcode(canvas, String(ticketId), {
      format: "CODE128",
      width: 2,
      height: 48,
      displayValue: false,
      margin: 4,
    });
  } catch {
    // leave blank
  }
}

function onDashboardRefresh() {
  fetch();
}

watch(viewingTicket, (t) => {
  if (!t) {
    viewPayments.value = [];
    viewPaymentsLoading.value = false;
    return;
  }

  nextTick(() => renderBarcodeImage(t.id));
});

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