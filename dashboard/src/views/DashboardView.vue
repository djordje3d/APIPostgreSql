<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
        <span class="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800" title="Data refreshes automatically every 12s and when you return to this tab">Live</span>
      </div>
      <button
        type="button"
        class="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm hover:bg-gray-50"
        @click="refreshAll"
      >
        Refresh
      </button>
    </div>
    <StatusCards ref="statusRef" />
    <GarageOverviewTable ref="garageRef" />
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div class="lg:col-span-2">
        <TicketActivityTable ref="ticketRef" />
      </div>
      <div>
        <RevenueSummary ref="revenueRef" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import StatusCards from '../components/StatusCards.vue'
import GarageOverviewTable from '../components/GarageOverviewTable.vue'
import TicketActivityTable from '../components/TicketActivityTable.vue'
import RevenueSummary from '../components/RevenueSummary.vue'
import { useDashboardPolling } from '../composables/useDashboardPolling'

const statusRef = ref<InstanceType<typeof StatusCards> | null>(null)
const garageRef = ref<InstanceType<typeof GarageOverviewTable> | null>(null)
const ticketRef = ref<InstanceType<typeof TicketActivityTable> | null>(null)
const revenueRef = ref<InstanceType<typeof RevenueSummary> | null>(null)

function refreshAll() {
  statusRef.value?.refresh?.()
  garageRef.value?.refresh?.()
  ticketRef.value?.refresh?.()
  revenueRef.value?.refresh?.()
}

useDashboardPolling(refreshAll)

onMounted(() => {
  window.addEventListener('dashboard-refresh', refreshAll)
})
onUnmounted(() => {
  window.removeEventListener('dashboard-refresh', refreshAll)
})

defineExpose({ refreshAll })
</script>
