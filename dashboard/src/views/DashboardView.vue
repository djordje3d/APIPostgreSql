<template>
  <div class="space-y-6">
    <div class="flex items-center justify-end">
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
    <TicketActivityTable ref="ticketRef" />
    <RevenueSummary ref="revenueRef" />
  </div>
</template>

<script setup lang="ts">
import { ref, inject, onMounted, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import StatusCards from '../components/StatusCards.vue'
import GarageOverviewTable from '../components/GarageOverviewTable.vue'
import TicketActivityTable from '../components/TicketActivityTable.vue'
import RevenueSummary from '../components/RevenueSummary.vue'
import { useDashboardPolling } from '../composables/useDashboardPolling'

const autoRefreshEnabled = inject<Ref<boolean>>('autoRefreshEnabled', ref(true))
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

useDashboardPolling(refreshAll, { enabled: autoRefreshEnabled })

onMounted(() => {
  refreshAll() // load data immediately so it appears without clicking Refresh
  window.addEventListener('dashboard-refresh', refreshAll)
})
onUnmounted(() => {
  window.removeEventListener('dashboard-refresh', refreshAll)
})

defineExpose({ refreshAll })
</script>
