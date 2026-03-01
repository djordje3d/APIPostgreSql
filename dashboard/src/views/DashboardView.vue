<template>
  <div class="space-y-6">
    <div class="flex items-center justify-end">
      <button class="btn" @click="refreshAll">
    <span class="btn-text-one">Refresh</span>
    <span class="btn-text-two">Click </span>
</button>

    </div>
    <router-link
      to="/by-garage"
      class="by-garage-card"
    >
      <span class="by-garage-card__icon" aria-hidden="true">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
      </span>
      <div class="by-garage-card__content">
        <span class="by-garage-card__title">View by garage</span>
        <span class="by-garage-card__desc">See status and activity per garage</span>
      </div>
      <span class="by-garage-card__arrow" aria-hidden="true">→</span>
    </router-link>
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

/* By garage entry card */
.by-garage-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid rgb(226 232 240);
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.by-garage-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: rgb(148 163 184);
}
.by-garage-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.375rem;
  background: rgb(241 245 249);
  color: rgb(71 85 105);
}
.by-garage-card__icon svg {
  width: 1.25rem;
  height: 1.25rem;
}
.by-garage-card__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}
.by-garage-card__title {
  font-weight: 600;
  color: rgb(30 41 59);
}
.by-garage-card__desc {
  font-size: 0.875rem;
  color: rgb(100 116 139);
}
.by-garage-card__arrow {
  font-size: 1.25rem;
  color: rgb(148 163 184);
}

</style>