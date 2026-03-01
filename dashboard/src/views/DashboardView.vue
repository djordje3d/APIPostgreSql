<template>
  <div class="space-y-6">
    <div class="flex items-center justify-end">
      <button class="btn" @click="refreshAll">
    <span class="btn-text-one">Osvezi me</span>
    <span class="btn-text-two">Click </span>
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
onUnmounted(() => {  // cleanup event listener
  window.removeEventListener('dashboard-refresh', refreshAll)
})

defineExpose({ refreshAll }) // expose refreshAll to parent components
</script>

<style scoped>
/* button styles */
/* https://uiverse.io/mobinkakei/ancient-goose-30 */
.btn {
  width: 140px;
  height: 50px;
  background: linear-gradient(to top, #00154c, #12376e, #23487f);
  color: #fff;
  border-radius: 50px;
  border: none;
  outline: none;
  cursor: pointer;
  position: relative;
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.btn span {
  font-size: 16px;
  /* text-transform: uppercase; */  
  letter-spacing: 1px;
  transition: top 0.5s;
}

.btn-text-one {
  position: absolute;
  width: 100%;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
}

.btn-text-two {
  position: absolute;
  width: 100%;
  top: 150%;
  left: 0;
  transform: translateY(-50%);
}

.btn:hover .btn-text-one {
  top: -100%;
}

.btn:hover .btn-text-two {
  top: 50%;
}

</style>