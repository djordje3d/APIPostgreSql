<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <router-link to="/" class="text-gray-600 hover:text-gray-900">&larr; Dashboard</router-link>
      <h1 v-if="garage" class="text-2xl font-bold text-gray-900">{{ garage.name }}</h1>
      <h1 v-else class="text-2xl font-bold text-gray-900">Garage #{{ $route.params.id }}</h1>
    </div>
    <div v-if="loading" class="text-gray-500">Loading…</div>
    <template v-else-if="garage">
      <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
        <p class="text-sm text-gray-600">Capacity: {{ garage.capacity }} · Default rate: {{ formatRate(garage.default_rate) }} RSD</p>
      </div>
      <RevenueSummary ref="revenueRef" :garage-id="garage.id" />
      <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
        <div class="border-b border-gray-200 px-4 py-3">
          <h2 class="text-lg font-semibold">Spots</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Code</th>
                <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Rentable</th>
                <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Active</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 bg-white">
              <tr v-for="s in spots" :key="s.id">
                <td class="px-4 py-3 font-medium">{{ s.code }}</td>
                <td class="px-4 py-3">{{ s.is_rentable ? 'Yes' : 'No' }}</td>
                <td class="px-4 py-3">{{ s.is_active ? 'Yes' : 'No' }}</td>
              </tr>
              <tr v-if="spots.length === 0">
                <td colspan="3" class="px-4 py-6 text-center text-gray-500">No spots</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="spotsTotal > 0" class="flex items-center justify-between border-t border-gray-200 px-4 py-3">
          <p class="text-sm text-gray-600">
            Showing {{ spotsOffset + 1 }}–{{ Math.min(spotsOffset + spotsPageSize, spotsTotal) }} of {{ spotsTotal }}
          </p>
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="spotsPage <= 1"
              @click="spotsPage = Math.max(1, spotsPage - 1)"
            >
              Previous
            </button>
            <span class="text-sm text-gray-600">
              Page {{ spotsPage }} of {{ spotsTotalPages }}
            </span>
            <button
              type="button"
              class="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="spotsPage >= spotsTotalPages"
              @click="spotsPage = Math.min(spotsTotalPages, spotsPage + 1)"
            >
              Next
            </button>
          </div>
        </div>
      </div>
      
      <!-- Open tickets -->
      <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
        <div class="border-b border-gray-200 px-4 py-3">
          <h2 class="text-lg font-semibold">Open tickets</h2>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">ID</th>
                <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Entry</th>
                <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Spot</th>
                <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Plate</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 bg-white">
              <tr v-for="t in openTickets" :key="t.id">
                <td class="px-4 py-3">{{ t.id }}</td>
                <td class="px-4 py-3 text-sm">{{ formatTime(t.entry_time) }}</td>
                <td class="px-4 py-3">{{ t.spot_code ?? '–' }}</td>
                <td class="px-4 py-3">{{ t.licence_plate ?? '–' }}</td>
              </tr>
              <tr v-if="openTickets.length === 0">
                <td colspan="4" class="px-4 py-6 text-center text-gray-500">No open tickets</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
    <div v-else class="text-red-600">Garage not found.</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, inject, onMounted, computed } from 'vue'
import type { Ref } from 'vue'
import { useRoute } from 'vue-router'
import { getGarage } from '../api/garages'
import { listSpots } from '../api/spots'
import { listTicketsDashboard } from '../api/tickets'
import RevenueSummary from '../components/RevenueSummary.vue'
import { useDashboardPolling } from '../composables/useDashboardPolling'
import type { Garage } from '../api/garages'
import type { Spot } from '../api/spots'
import type { TicketDashboardRow } from '../api/tickets'

const autoRefreshEnabled = inject<Ref<boolean>>('autoRefreshEnabled', ref(true))
const route = useRoute()
const garage = ref<Garage | null>(null)
const spots = ref<Spot[]>([])
const openTickets = ref<TicketDashboardRow[]>([])
const loading = ref(true)

const spotsPage = ref(1)
const spotsPageSize = ref(10)
const spotsTotal = ref(0)
const spotsOffset = computed(() => (spotsPage.value - 1) * spotsPageSize.value)
const spotsTotalPages = computed(() => Math.max(1, Math.ceil(spotsTotal.value / spotsPageSize.value)))
const revenueRef = ref<InstanceType<typeof RevenueSummary> | null>(null)

function formatTime(s: string | null) {
  if (!s) return '–'
  try {
    return new Date(s).toLocaleString()
  } catch {
    return s
  }
}

function formatRate(value: string | null | undefined): string {
  if (value == null || value === '') return '–'
  const n = parseFloat(String(value))
  if (Number.isNaN(n)) return '–'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(n)
}

async function fetchSpots() {
  const id = Number(route.params.id)
  if (!id) return
  try {
    const sRes = await listSpots({
      garage_id: id,
      active_only: false,
      limit: spotsPageSize.value,
      offset: spotsOffset.value,
    })
    spots.value = sRes.data.items
    spotsTotal.value = sRes.data.total
  } catch {
    spots.value = []
    spotsTotal.value = 0
  }
}

async function fetch() {
  const id = Number(route.params.id)
  if (!id) return
  spotsPage.value = 1
  loading.value = true
  try {
    const [gRes, tRes] = await Promise.all([
      getGarage(id),
      listTicketsDashboard({ limit: 100 }),
    ])
    garage.value = gRes.data
    openTickets.value = tRes.data.items.filter((t) => t.garage_id === id && t.ticket_state === 'OPEN')
    await fetchSpots()
    revenueRef.value?.refresh?.()
  } catch {
    garage.value = null
    spots.value = []
    spotsTotal.value = 0
    openTickets.value = []
  } finally {
    loading.value = false
  }
}

watch([spotsPage, spotsPageSize], () => {
  if (garage.value) fetchSpots()
})

useDashboardPolling(fetch, { intervalMs: 10_000, enabled: autoRefreshEnabled })
watch(() => route.params.id, fetch, { immediate: true })
onMounted(fetch)
</script>
