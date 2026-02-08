<template>
  <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
    <div class="border-b border-gray-200 px-4 py-3">
      <h2 class="text-lg font-semibold text-gray-900">Ticket activity (last 10)</h2>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Entry time</th>
            <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Spot</th>
            <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Plate</th>
            <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Status</th>
            <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white">
          <tr v-if="loading" class="text-center text-gray-500">
            <td colspan="5" class="px-4 py-6">Loading…</td>
          </tr>
          <tr v-for="t in (tickets || [])" :key="t.id" class="hover:bg-gray-50">
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">{{ formatTime(t.entry_time) }}</td>
            <td class="px-4 py-3 text-sm text-gray-700">{{ t.spot_code ?? '–' }}</td>
            <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ t.licence_plate ?? '–' }}</td>
            <td class="px-4 py-3">
              <span
                :class="[
                  'rounded px-2 py-0.5 text-xs font-medium',
                  t.ticket_state === 'OPEN' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800',
                ]"
              >
                {{ t.ticket_state }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-right text-sm">
              <button
                type="button"
                class="text-slate-600 hover:text-slate-900"
                title="View ticket"
                @click="viewTicket(t)"
              >
                View
              </button>
              <template v-if="t.ticket_state === 'OPEN'">
                <button
                  type="button"
                  class="ml-2 text-amber-600 hover:text-amber-800"
                  title="Close ticket"
                  @click="closeTicket(t.id)"
                >
                  Close
                </button>
              </template>
              <template v-else-if="t.ticket_state === 'CLOSED' && t.payment_status !== 'PAID'">
                <button
                  type="button"
                  class="ml-2 text-emerald-600 hover:text-emerald-800"
                  title="Go to payment"
                  @click="openPayment(t)"
                >
                  Payment
                </button>
              </template>
            </td>
          </tr>
          <tr v-if="!loading && (!tickets || tickets.length === 0)">
            <td colspan="5" class="px-4 py-6 text-center text-gray-500">No tickets</td>
          </tr>
        </tbody>
      </table>
    </div>
    <PaymentModal
      v-if="paymentTicket"
      :ticket-id="paymentTicket.id"
      :fee="paymentTicket.fee"
      @close="closePaymentModal"
      @done="onPaymentDone"
    />
    <div v-if="viewingTicket" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="viewingTicket = null">
      <div class="max-h-[90vh] w-full max-w-md overflow-auto rounded-lg bg-white p-6 shadow-xl">
        <div class="mb-4 flex justify-between">
          <h3 class="text-lg font-semibold">Ticket #{{ viewingTicket.id }}</h3>
          <button type="button" class="text-gray-500 hover:text-gray-700" @click="viewingTicket = null">&times;</button>
        </div>
        <dl class="space-y-2 text-sm">
          <div><dt class="text-gray-500">Entry</dt><dd>{{ formatTime(viewingTicket.entry_time) }}</dd></div>
          <div><dt class="text-gray-500">Exit</dt><dd>{{ formatTime(viewingTicket.exit_time) || '–' }}</dd></div>
          <div><dt class="text-gray-500">Spot</dt><dd>{{ viewingTicket.spot_code ?? '–' }}</dd></div>
          <div><dt class="text-gray-500">Plate</dt><dd>{{ viewingTicket.licence_plate ?? '–' }}</dd></div>
          <div><dt class="text-gray-500">State</dt><dd>{{ viewingTicket.ticket_state }}</dd></div>
          <div><dt class="text-gray-500">Payment</dt><dd>{{ viewingTicket.payment_status }}</dd></div>
          <div><dt class="text-gray-500">Fee</dt><dd>{{ viewingTicket.fee ?? '–' }}</dd></div>
        </dl>
        <button
          v-if="viewingTicket.ticket_state === 'CLOSED' && viewingTicket.payment_status !== 'PAID'"
          type="button"
          class="mt-4 rounded bg-emerald-600 px-3 py-1.5 text-white hover:bg-emerald-700"
          @click="openPayment(viewingTicket); viewingTicket = null"
        >
          Go to payment
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { listTicketsDashboard, ticketExit } from '../api/tickets'
import type { TicketDashboardRow } from '../api/tickets'
import PaymentModal from './PaymentModal.vue'

const props = withDefaults(
  defineProps<{ garageId?: number | null }>(),
  { garageId: undefined }
)

const loading = ref(true)
const tickets = ref<TicketDashboardRow[]>([])
const viewingTicket = ref<TicketDashboardRow | null>(null)
const paymentTicket = ref<TicketDashboardRow | null>(null)

function formatTime(s: string | null) {
  if (!s) return '–'
  try {
    const d = new Date(s)
    return d.toLocaleString()
  } catch {
    return s
  }
}

async function fetch() {
  loading.value = true
  try {
    const res = await listTicketsDashboard({
      ...(props.garageId != null ? { garage_id: props.garageId } : {}),
      limit: 10,
      offset: 0,
    })
    tickets.value = res.data.items
  } catch {
    tickets.value = []
  } finally {
    loading.value = false
  }
}

function viewTicket(t: TicketDashboardRow) {
  viewingTicket.value = t
}

function openPayment(t: TicketDashboardRow) {
  paymentTicket.value = t
}

async function closeTicket(id: number) {
  try {
    await ticketExit(id)
    await fetch()
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
  nextTick(() => {
    paymentTicket.value = null
    fetch()
    window.dispatchEvent(new CustomEvent('dashboard-refresh'))
  })
}

onMounted(fetch)
watch(() => props.garageId, fetch)

defineExpose({ refresh: fetch })
</script>
