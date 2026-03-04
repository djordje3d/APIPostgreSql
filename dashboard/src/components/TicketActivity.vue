<template>
  <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
    <div class="border-b border-gray-200 px-4 py-3">
      <h2 class="text-lg font-semibold text-gray-900">Ticket activity (last 10)</h2>
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
        <span class="icon-spinner11 inline-block text-2xl animate-spin" aria-hidden="true"></span>
        <span>loading data...</span>
      </div>

      <!-- Idle: nothing loaded, no loading in progress -->
      <div
        v-else-if="!hasLoadedOnce && !refreshing"
        class="px-4 py-12 text-center text-gray-400"
      >
        —
      </div>

      <!-- Content: table with optional refreshing overlay -->
      <div v-else class="relative min-h-[120px]">
        <!-- Refreshing overlay -->
        <div
          v-if="refreshing"
          class="absolute inset-0 z-10 flex items-center justify-center bg-white/70"
          aria-busy="true"
          aria-label="Refreshing"
        >
          <span class="icon-spinner11 inline-block text-3xl animate-spin text-gray-500" aria-hidden="true"></span>
        </div>

        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Garage</th>
              <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Plate</th>
              <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Spot</th>
              <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Entry time</th>
              <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Exit time</th>
              <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">Fee</th>
              <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">Rest to pay</th>
              <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Ticket ID</th>
              <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr v-for="t in (tickets || [])" :key="t.id" class="hover:bg-gray-50">
              <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">{{ t.garage_name ?? '–' }}</td>
              <td class="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">{{ t.licence_plate ?? '–' }}</td>
              <td class="px-4 py-3 text-sm text-gray-700">{{ t.spot_code ?? '–' }}</td>
              <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">{{ formatTime(t.entry_time) }}</td>
              <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">{{ formatTime(t.exit_time) }}</td>
              <td class="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-700">{{ formatMoney(t.fee) }}</td>
              <td class="whitespace-nowrap px-4 py-3 text-right text-sm font-medium" :class="restToPayClass(t)">{{ formatRestToPay(t) }}</td>
              <td class="px-4 py-3">
                <span class="font-mono text-sm tracking-[0.25em] text-gray-800" aria-label="Ticket ID">{{ t.id }}</span>
              </td>
              <td class="whitespace-nowrap px-4 py-3 text-right text-sm">
                <button
                  type="button"
                  class="icon-barcode text-2xl font-bold text-slate-800 hover:text-slate-900"
                  title="View ticket & payments"
                  @click="viewTicket(t)"
                  style="line-height: 1"
                >
                </button>
                <template v-if="t.ticket_state === 'OPEN'"> <!-- Close ticket -->
                  <button
                    type="button"
                    class="icon-exit text-2xl font-bold ml-2 text-amber-600 hover:text-amber-800"
                    title="Close ticket"
                    @click="closeTicket(t.id)"
                  >
                  </button>
                </template>
                <template v-else-if="t.ticket_state === 'CLOSED' && t.payment_status !== 'PAID'">
                  <button
                    type="button"
                    class="icon-credit-card text-2xl font-bold ml-2 text-emerald-600 hover:text-emerald-800"
                    title="Go to payment"
                    @click="openPayment(t)"
                  >
                  </button>
                </template>
              </td>
            </tr>
            <!-- Loaded empty -->
            <tr v-if="(tickets || []).length === 0">
              <td colspan="9" class="px-4 py-6 text-center text-gray-500">No tickets</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <PaymentModal
      v-if="paymentTicket"
      :ticket-id="paymentTicket.id"
      :fee="paymentTicket.fee"
      :garage-name="paymentTicket.garage_name ?? undefined"
      @close="closePaymentModal"
      @done="onPaymentDone"
    />
    <!-- View ticket detail modal: barcode + evidence of payments (Teleport so it stays above RevenueSummary when scrolling) -->
    <Teleport to="body">
      <div
        v-if="viewingTicket"
        class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50"
        style="pointer-events: auto"
      >
      <div class="max-h-[90vh] w-full max-w-md overflow-auto rounded-lg bg-white p-6 shadow-xl">
        <div class="mb-4 flex justify-between">
          <h3 class="text-lg font-semibold text-gray-900">{{ viewingTicket.garage_name ?? '–' }} — Ticket #{{ viewingTicket.id }}</h3>
          <button type="button" class="text-gray-500 hover:text-gray-700" @click="viewingTicket = null">&times;</button>
        </div>
        <dl class="space-y-2 text-sm">
          <div><dt class="text-gray-500">Garage</dt><dd>{{ viewingTicket.garage_name ?? '–' }}</dd></div>
          <div><dt class="text-gray-500">Plate</dt><dd>{{ viewingTicket.licence_plate ?? '–' }}</dd></div>
          <div><dt class="text-gray-500">Spot</dt><dd>{{ viewingTicket.spot_code ?? '–' }}</dd></div>
          <div><dt class="text-gray-500">Entry time</dt><dd>{{ formatTime(viewingTicket.entry_time) }}</dd></div>
          <div><dt class="text-gray-500">Exit time</dt><dd>{{ formatTime(viewingTicket.exit_time) || '–' }}</dd></div>
          <div><dt class="text-gray-500">Fee</dt><dd>{{ formatMoney(viewingTicket.fee) }}</dd></div>
        </dl>
        <!-- Ticket ID (barcode) -->
        <div class="mt-4 border-t border-gray-200 pt-4">
          <dt class="text-gray-500 text-xs font-medium uppercase">Ticket ID (barcode)</dt>
          <dd class="mt-2 flex flex-col items-center gap-2">
            <canvas
              ref="barcodeCanvasRef"
              class="max-w-full rounded border border-gray-200 bg-white"
              aria-label="Barcode for ticket"
            />
            <span class="font-mono text-sm tracking-[0.35em] text-gray-600">{{ viewingTicket.id }}</span>
          </dd>
        </div>
        <!-- Evidence of payments -->
        <div class="mt-4 border-t border-gray-200 pt-4">
          <h4 class="text-sm font-semibold text-gray-800">Evidence of payments</h4>
          <p class="mt-0.5 text-xs text-gray-500">All payments for this ticket (amount and when paid).</p>
          <div v-if="viewPaymentsLoading" class="mt-3 text-sm text-gray-500">Loading…</div>
          <div v-else-if="!viewPayments.length" class="mt-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-center text-sm text-gray-500">
            No payments recorded.
          </div>
          <div v-else class="mt-3 overflow-hidden rounded-lg border border-gray-200"> <!-- Payments table -->
            <table class="min-w-full divide-y divide-gray-200 text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">#</th>
                  <th scope="col" class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500">Amount</th>
                  <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">When</th>
                  <th scope="col" class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Method</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white"> <!-- Payments list -->
                <tr v-for="(p, idx) in viewPaymentsSorted" :key="p.id" class="hover:bg-gray-50">
                  <td class="whitespace-nowrap px-3 py-2 text-gray-600">{{ idx + 1 }}</td>
                  <td class="whitespace-nowrap px-3 py-2 text-right font-medium text-gray-900">{{ formatMoney(p.amount) }}</td>
                  <td class="whitespace-nowrap px-3 py-2 text-gray-700">{{ formatTime(p.paid_at) }}</td>
                  <td class="px-3 py-2 text-gray-600">{{ p.method ?? '–' }}</td>
                </tr>
              </tbody>
              <tfoot class="bg-gray-50"> <!-- Total paid -->
                <tr>
                  <td colspan="2" class="px-3 py-2 text-right text-xs font-semibold uppercase text-gray-600">Total paid</td>
                  <td colspan="2" class="whitespace-nowrap px-3 py-2 text-right font-semibold text-gray-900">{{ formatMoney(String(viewPaymentsTotal)) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
        <div class="mt-4 flex gap-2"> <!-- Buttons: go to payment, close -->
          <button
            v-if="viewingTicket.ticket_state === 'CLOSED' && viewingTicket.payment_status !== 'PAID'"
            type="button"
            class="rounded bg-emerald-600 px-3 py-1.5 text-sm text-white hover:bg-emerald-700"
            @click="openPayment(viewingTicket); viewingTicket = null"
          >
            Go to payment
          </button>
          <button
            type="button"
            class="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            @click="viewingTicket = null"
          >
            Close
          </button>
        </div>
      </div>
    </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import JsBarcode from 'jsbarcode'
import { listTicketsDashboard, ticketExit } from '../api/tickets'
import type { TicketDashboardRow } from '../api/tickets'
import { getPaymentsByTicket } from '../api/payments'
import type { Payment } from '../api/payments'
import PaymentModal from './PaymentModal.vue'

const props = withDefaults(
  defineProps<{ garageId?: number | null }>(),
  { garageId: undefined }
)

const loading = ref(false)
const refreshing = ref(false)
const error = ref(false)
const hasLoadedOnce = ref(false)
const tickets = ref<TicketDashboardRow[]>([])
const viewingTicket = ref<TicketDashboardRow | null>(null)
const viewPayments = ref<Payment[]>([])
const viewPaymentsLoading = ref(false)
const paymentTicket = ref<TicketDashboardRow | null>(null)
/** Rest to pay (fee - total paid) per ticket id, for table display. Fetched when tickets load. */
const restToPayMap = ref<Record<number, number>>({})

/** Cache payments by ticket id so reopening the same ticket doesn't refetch. */
const paymentsCache = new Map<number, Payment[]>()

const PAYMENTS_VIEW_LIMIT = 50

function invalidatePaymentsCache(ticketId?: number) {
  if (ticketId != null) paymentsCache.delete(ticketId)
  else paymentsCache.clear()
}

const viewPaymentsTotal = computed(() =>
  viewPayments.value.reduce((sum, p) => sum + parseFloat(p.amount), 0)
)

/** Payments sorted by paid_at descending (newest first) for the evidence table. */
const viewPaymentsSorted = computed(() => {
  const list = [...viewPayments.value]
  list.sort((a, b) => {
    const ta = a.paid_at ? new Date(a.paid_at).getTime() : 0
    const tb = b.paid_at ? new Date(b.paid_at).getTime() : 0
    return tb - ta
  })
  return list
})

const barcodeCanvasRef = ref<HTMLCanvasElement | null>(null)

function formatTime(s: string | null) {
  if (!s) return '–'
  try {
    const d = new Date(s)
    return d.toLocaleString()
  } catch {
    return s
  }
}

function formatMoney(value: string | null | undefined): string {
  if (value == null || value === '') return '–'
  const n = parseFloat(String(value))
  if (Number.isNaN(n)) return '–'
  return new Intl.NumberFormat('sr-RS', { style: 'decimal', maximumFractionDigits: 0 }).format(n) + ' RSD'
}

function formatRestToPay(t: TicketDashboardRow): string {
  if (t.ticket_state === 'OPEN') return '–'
  if (t.payment_status === 'PAID') return '0 RSD'
  const rest = restToPayMap.value[t.id]
  if (rest !== undefined) return formatMoney(String(rest))
  // Still loading rest-to-pay for this ticket
  if (t.ticket_state === 'CLOSED' && t.payment_status !== 'PAID') return '…'
  return '–'
}

function restToPayClass(t: TicketDashboardRow): string {
  if (t.payment_status === 'PAID' || t.ticket_state === 'OPEN') return 'text-gray-500'
  return 'text-amber-700'
}

async function fetchRestToPayForTickets(items: TicketDashboardRow[]) {
  const needRest = items.filter(
    (t) => t.ticket_state !== 'OPEN' && t.payment_status !== 'PAID'
  )
  if (needRest.length === 0) {
    restToPayMap.value = {}
    return
  }
  const map: Record<number, number> = {}
  await Promise.all(
    needRest.map(async (t) => {
      const feeNum =
        t.fee != null && t.fee !== ''
          ? parseFloat(String(t.fee))
          : 0
      const fee = Number.isNaN(feeNum) ? 0 : feeNum
      try {
        const res = await getPaymentsByTicket(t.id, { limit: 500 })
        const totalPaid = res.data.items.reduce(
          (s, p) => s + parseFloat(p.amount),
          0
        )
        map[t.id] = Math.max(0, fee - totalPaid)
      } catch {
        map[t.id] = fee
      }
    })
  )
  restToPayMap.value = { ...restToPayMap.value, ...map }
}

/** Fetch payments for the view ticket modal (cached per ticket, limit 50). */
async function fetchPaymentsForView(ticketId: number) {
  const cached = paymentsCache.get(ticketId)
  if (cached !== undefined) {
    viewPayments.value = cached
    return
  }
  viewPaymentsLoading.value = true
  viewPayments.value = []
  try {
    const res = await getPaymentsByTicket(ticketId, { limit: PAYMENTS_VIEW_LIMIT })
    const items = res.data.items
    viewPayments.value = items
    paymentsCache.set(ticketId, items)
  } catch {
    viewPayments.value = []
  } finally {
    viewPaymentsLoading.value = false
  }
}

function viewTicket(t: TicketDashboardRow) {
  viewingTicket.value = t
  fetchPaymentsForView(t.id)
}

function openPayment(t: TicketDashboardRow) {
  paymentTicket.value = t
}

async function closeTicket(id: number) {
  try {
    await ticketExit(id)
    // Let parent refreshAll() drive a single refresh for this and other widgets
    window.dispatchEvent(new CustomEvent('dashboard-refresh'))
  } catch {
    // could show toast
  }
}

function closePaymentModal() {
  nextTick(() => {
    paymentTicket.value = null
  })
}

function onPaymentDone() {
  invalidatePaymentsCache(paymentTicket.value?.id)
  nextTick(() => {
    paymentTicket.value = null
    // Let parent refreshAll() drive a single refresh for this and other widgets
    window.dispatchEvent(new CustomEvent('dashboard-refresh'))
  })
}

async function fetch() {
  const hasData = tickets.value.length > 0 || hasLoadedOnce.value
  if (!hasData) {
    loading.value = true
    error.value = false
    restToPayMap.value = {}
  } else {
    refreshing.value = true
  }
  try {
    const res = await listTicketsDashboard({
      ...(props.garageId != null ? { garage_id: props.garageId } : {}),
      limit: 10,
      offset: 0,
    })
    tickets.value = res.data.items
    await fetchRestToPayForTickets(tickets.value)
    hasLoadedOnce.value = true
    error.value = false
  } catch {
    error.value = true
    if (!hasData) {
      tickets.value = []
      restToPayMap.value = {}
    }
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function retry() {
  error.value = false
  fetch()
}

function renderBarcodeImage(ticketId: number) {
  const canvas = barcodeCanvasRef.value
  if (!canvas) return
  try {
    JsBarcode(canvas, String(ticketId), {
      format: 'CODE128',
      width: 2,
      height: 48,
      displayValue: false,
      margin: 4,
    })
  } catch {
    // e.g. invalid value; leave canvas blank
  }
}

watch(viewingTicket, (t) => {
  if (!t) {
    viewPayments.value = []
    viewPaymentsLoading.value = false
    return
  }
  nextTick(() => renderBarcodeImage(t.id))
})

defineExpose({ refresh: () => fetch() })
</script>
