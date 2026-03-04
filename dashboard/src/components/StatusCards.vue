<template>
  <!-- Error: retry -->
  <div
    v-if="error"
    class="flex flex-col items-center justify-center gap-2 rounded-lg bg-white px-4 py-8 shadow ring-1 ring-gray-200"
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
    class="flex flex-col items-center justify-center gap-3 rounded-lg bg-white px-4 py-12 shadow ring-1 ring-gray-200 text-gray-500"
    aria-busy="true"
    aria-live="polite"
  >
    <span class="icon-spinner11 inline-block text-2xl animate-spin" aria-hidden="true"></span>
    <span>loading data...</span>
  </div>

  <!-- Idle -->
  <div
    v-else-if="!hasLoadedOnce && !refreshing"
    class="rounded-lg bg-white px-4 py-12 text-center shadow ring-1 ring-gray-200 text-gray-400"
  >
    —
  </div>

  <!-- Content with refreshing overlay -->
  <div v-else class="relative min-h-[120px]">
    <div
      v-if="refreshing"
      class="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70"
      aria-busy="true"
      aria-label="Refreshing"
    >
      <span class="icon-spinner11 inline-block text-3xl animate-spin text-gray-500" aria-hidden="true"></span>
    </div>
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
        <div class="flex items-center gap-3">
          <span class="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 text-green-700" aria-hidden="true">🟢</span>
          <div>
            <p class="text-sm font-medium text-gray-500">Free spots</p>
            <p class="text-2xl font-semibold text-gray-900">{{ freeSpots }}</p>
          </div>
        </div>
      </div>
      <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
        <div class="flex items-center gap-3">
          <span class="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 text-red-700" aria-hidden="true">🔴</span>
          <div>
            <p class="text-sm font-medium text-gray-500">Occupied spots</p>
            <p class="text-2xl font-semibold text-gray-900">{{ occupiedSpots }}</p>
          </div>
        </div>
      </div>
      <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
        <div class="flex items-center gap-3">
          <span class="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-amber-700" aria-hidden="true">🟡</span>
          <div>
            <p class="text-sm font-medium text-gray-500">Inactive spots</p>
            <p class="text-2xl font-semibold text-gray-900">{{ inactiveSpots }}</p>
          </div>
        </div>
      </div>
      <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
        <div class="flex items-center gap-3">
          <span class="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-700" aria-hidden="true">🧾</span>
          <div>
            <p class="text-sm font-medium text-gray-500">Open tickets</p>
            <p class="text-2xl font-semibold text-gray-900">{{ openTickets }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { listSpots } from '../api/spots'
import { listTickets } from '../api/tickets'

const props = withDefaults(
  defineProps<{ garageId?: number | null }>(),
  { garageId: undefined }
)

const loading = ref(false)
const refreshing = ref(false)
const error = ref(false)
const hasLoadedOnce = ref(false)
const freeSpots = ref(0)
const occupiedSpots = ref(0)
const inactiveSpots = ref(0)
const openTickets = ref(0)

const spotParams = () => ({
  ...(props.garageId != null ? { garage_id: props.garageId } : {}),
  limit: 1,
})
const ticketParams = () => ({
  ...(props.garageId != null ? { garage_id: props.garageId } : {}),
  state: 'OPEN' as const,
  limit: 1,
})

async function fetch() {
  const hasData = hasLoadedOnce.value
  if (!hasData) {
    loading.value = true
    error.value = false
  } else {
    refreshing.value = true
  }
  try {
    const [freeRes, allSpotsRes, activeOnlyRes, openRes] = await Promise.all([
      listSpots({ ...spotParams(), only_free: true, active_only: true }),
      listSpots({ ...spotParams(), active_only: false }),
      listSpots({ ...spotParams(), active_only: true }),
      listTickets(ticketParams()),
    ])
    freeSpots.value = freeRes.data.total
    const totalActive = activeOnlyRes.data.total
    const totalAll = allSpotsRes.data.total
    inactiveSpots.value = Math.max(0, totalAll - totalActive)
    occupiedSpots.value = totalActive - freeRes.data.total
    openTickets.value = openRes.data.total
    hasLoadedOnce.value = true
    error.value = false
  } catch {
    error.value = true
    if (!hasData) {
      freeSpots.value = occupiedSpots.value = inactiveSpots.value = openTickets.value = 0
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
