<template>
  <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
    <h2 class="mb-4 text-lg font-semibold text-gray-900">Payments & revenue</h2>
    <div class="space-y-4">
      <div class="flex justify-between text-sm">
        <span class="text-gray-600">Today's revenue</span>
        <span class="font-medium text-gray-900">{{ loading ? '…' : formatMoney(todayRevenue) }}</span>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-gray-600">This month</span>
        <span class="font-medium text-gray-900">{{ loading ? '…' : formatMoney(monthRevenue) }}</span>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-gray-600">Unpaid / partially paid tickets</span>
        <span class="font-medium text-amber-700">{{ loading ? '…' : unpaidCount }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listPayments } from '../api/payments'
import { listTickets } from '../api/tickets'

const loading = ref(true)
const todayRevenue = ref(0)
const monthRevenue = ref(0)
const unpaidCount = ref(0)

function formatMoney(n: number) {
  return new Intl.NumberFormat('en-US', { minimumFractionDigits: 2 }).format(n) + ' RSD'
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

async function fetch() {
  loading.value = true
  try {
    const today = getTodayISO()
    const { from: monthFrom, to: monthTo } = getMonthStartEnd()
    const [todayRes, monthRes, unpaidRes] = await Promise.all([
      listPayments({ from: today, to: today, limit: 1000 }),
      listPayments({ from: monthFrom, to: monthTo, limit: 1000 }),
      listTickets({ payment_status: 'UNPAID', limit: 1 }),
    ])
    const partialRes = await listTickets({ payment_status: 'PARTIALLY_PAID', limit: 1 })
    todayRevenue.value = todayRes.data.items.reduce((s, p) => s + parseFloat(p.amount), 0)
    monthRevenue.value = monthRes.data.items.reduce((s, p) => s + parseFloat(p.amount), 0)
    unpaidCount.value = unpaidRes.data.total + partialRes.data.total
  } catch {
    todayRevenue.value = monthRevenue.value = unpaidCount.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(fetch)

defineExpose({ refresh: fetch })
</script>
