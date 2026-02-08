<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex flex-wrap items-center gap-3">
        <label class="flex items-center gap-2">
          <span class="text-sm font-medium text-gray-700">Garage</span>
          <select
            v-model="selectedGarageId"
            class="rounded border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option :value="null">Select a garage…</option>
            <option v-for="g in garages" :key="g.id" :value="g.id">{{ g.name }}</option>
          </select>
        </label>
      </div>
      <button
        type="button"
        class="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm hover:bg-gray-50"
        @click="refreshAll"
      >
        Refresh
      </button>
    </div>
    <template v-if="selectedGarageId != null">
      <StatusCards ref="statusRef" :garage-id="selectedGarageId" />
      <GarageOverviewTable ref="garageRef" :garage-id="selectedGarageId" />
      <TicketActivityTable ref="ticketRef" :garage-id="selectedGarageId" />
      <section class="rounded-lg bg-slate-50 p-4 text-sm ring-1 ring-slate-200">
        <h3 class="mb-3 font-semibold text-slate-800">Status &amp; actions</h3>
        <dl class="grid gap-x-4 gap-y-2 sm:grid-cols-2 lg:grid-cols-3">
          <div><dt class="font-medium text-slate-700">OPEN</dt><dd class="text-slate-600">Ticket is active; vehicle is parked. You can <strong>Close</strong> the ticket when the vehicle leaves.</dd></div>
          <div><dt class="font-medium text-slate-700">CLOSED</dt><dd class="text-slate-600">Vehicle has left. Use <strong>Payment</strong> to record payment until the ticket is fully paid.</dd></div>
          <div><dt class="font-medium text-slate-700">UNPAID / PARTIALLY_PAID</dt><dd class="text-slate-600">Fee is not fully paid. “Rest to pay” shows how much is still due; do not enter more than that amount.</dd></div>
          <div><dt class="font-medium text-slate-700">PAID</dt><dd class="text-slate-600">Full fee has been collected. No further payment needed.</dd></div>
          <div><dt class="font-medium text-slate-700">Refresh</dt><dd class="text-slate-600">Updates all dashboard data (balance, revenue, tickets, spots). Use after making changes elsewhere.</dd></div>
        </dl>
      </section>
      <RevenueSummary ref="revenueRef" :garage-id="selectedGarageId" />
    </template>
    <div v-else class="rounded-lg bg-white p-8 text-center shadow ring-1 ring-gray-200">
      <p class="text-gray-500">Select a garage from the dropdown to view its dashboard.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import StatusCards from '../components/StatusCards.vue'
import GarageOverviewTable from '../components/GarageOverviewTable.vue'
import TicketActivityTable from '../components/TicketActivityTable.vue'
import RevenueSummary from '../components/RevenueSummary.vue'
import { listGarages } from '../api/garages'
import type { Garage } from '../api/garages'

const garages = ref<Garage[]>([])
const selectedGarageId = ref<number | null>(null)

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

async function loadGarages() {
  try {
    const res = await listGarages({ limit: 200 })
    garages.value = res.data.items
    if (garages.value.length === 1 && selectedGarageId.value == null) {
      selectedGarageId.value = garages.value[0].id
    }
  } catch {
    garages.value = []
  }
}

watch(selectedGarageId, () => {
  if (selectedGarageId.value != null) refreshAll()
})

onMounted(loadGarages)

defineExpose({ refreshAll })
</script>
