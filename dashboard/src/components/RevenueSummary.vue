<template>
  <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
    <h2 class="mb-4 text-lg font-semibold text-gray-900">Payments & revenue</h2>

    <!-- Error: retry -->
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

    <!-- Loading (no data yet) -->
    <div
      v-else-if="loading"
      class="flex flex-col items-center justify-center gap-3 py-12 text-gray-500"
      aria-busy="true"
      aria-live="polite"
    >
      <span class="icon-spinner11 inline-block text-2xl animate-spin" aria-hidden="true"></span>
      <span>loading data...</span>
    </div>

    <!-- Idle -->
    <div
      v-else-if="!hasLoadedOnce && !refreshing"
      class="py-12 text-center text-gray-400"
    >
      —
    </div>

    <!-- Content with refreshing overlay -->
    <div v-else class="relative min-h-[100px]">
      <div
        v-if="refreshing"
        class="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70"
        aria-busy="true"
        aria-label="Refreshing"
      >
        <span class="icon-spinner11 inline-block text-3xl animate-spin text-gray-500" aria-hidden="true"></span>
      </div>
      <div class="space-y-4">
        <div class="flex justify-between text-sm">
          <span class="text-gray-600">Today's revenue</span>
          <span class="font-medium text-gray-900">{{ formatMoney(todayRevenue) }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-600">This month</span>
          <span class="font-medium text-gray-900">{{ formatMoney(monthRevenue) }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-600">Unpaid / partially paid tickets</span>
          <span class="font-medium text-amber-700">{{ unpaidCount }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-600">Rest to pay (to full paid)</span>
          <span class="font-medium text-amber-700">{{ formatMoney(totalOutstanding) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, inject, type Ref } from 'vue'
import { listPayments, getOutstanding } from '../api/payments'
import { listTickets } from '../api/tickets'

const props = withDefaults(
  defineProps<{ garageId?: number | null }>(),
  { garageId: undefined }
)

const dashboardRefreshAbortSignal = inject<Ref<AbortSignal | null>>(
  'dashboardRefreshAbortSignal',
  ref(null),
)

const loading = ref(false)
const refreshing = ref(false)
const error = ref(false)
const hasLoadedOnce = ref(false)
const todayRevenue = ref(0)
const monthRevenue = ref(0)
const unpaidCount = ref(0)
const totalOutstanding = ref(0)

function formatMoney(n: number) {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(n) + ' RSD'
}

function getTodayISO() {
  const d = new Date()
  return d.toISOString().slice(0, 10)
}

function getMonthStartEnd() {
  const d = new Date()
  const start = new Date(d.getFullYear(), d.getMonth(), 1)
  const end = new Date(d.getFullYear(), d.getMonth() + 1, 0)
  return {
    from: start.toISOString().slice(0, 10),
    to: end.toISOString().slice(0, 10),
  }
}

const paymentParams = (from: string, to: string) => ({
  from,
  to,
  limit: 1000,
  ...(props.garageId != null ? { garage_id: props.garageId } : {}),
})
const ticketParams = () => ({
  payment_status: 'UNPAID' as const,
  limit: 1,
  ...(props.garageId != null ? { garage_id: props.garageId } : {}),
})

async function fetch() {
  const hasData = hasLoadedOnce.value
  if (!hasData) {
    loading.value = true
    error.value = false
  } else {
    refreshing.value = true
  }
  const signal = dashboardRefreshAbortSignal?.value ?? undefined
  const config = signal ? { signal } : undefined
  try {
    const today = getTodayISO()
    const { from: monthFrom, to: monthTo } = getMonthStartEnd()
    const [todayRes, monthRes, unpaidRes, outstandingRes] = await Promise.all([
      listPayments(paymentParams(today, today), config),
      listPayments(paymentParams(monthFrom, monthTo), config),
      listTickets(ticketParams(), config),
      getOutstanding(props.garageId, config),
    ])
    const partialRes = await listTickets(
      {
        payment_status: 'PARTIALLY_PAID',
        limit: 1,
        ...(props.garageId != null ? { garage_id: props.garageId } : {}),
      },
      config
    )
    todayRevenue.value = todayRes.data.items.reduce((s, p) => s + parseFloat(p.amount), 0)
    monthRevenue.value = monthRes.data.items.reduce((s, p) => s + parseFloat(p.amount), 0)
    unpaidCount.value = unpaidRes.data.total + partialRes.data.total
    totalOutstanding.value = outstandingRes.data.total_outstanding ?? 0
    hasLoadedOnce.value = true
    error.value = false
  } catch (err: unknown) {
    if ((err as { code?: string })?.code === 'ERR_CANCELED') return
    error.value = true
    if (!hasData) {
      todayRevenue.value = monthRevenue.value = unpaidCount.value = totalOutstanding.value = 0
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

defineExpose({ refresh: () => fetch() })
</script>
