<template>
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
      <div class="flex items-center gap-3">
        <span class="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 text-green-700" aria-hidden="true">🟢</span>
        <div>
          <p class="text-sm font-medium text-gray-500">Free spots</p>
          <p class="text-2xl font-semibold text-gray-900">{{ loading ? '…' : freeSpots }}</p>
        </div>
      </div>
    </div>
    <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
      <div class="flex items-center gap-3">
        <span class="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 text-red-700" aria-hidden="true">🔴</span>
        <div>
          <p class="text-sm font-medium text-gray-500">Occupied spots</p>
          <p class="text-2xl font-semibold text-gray-900">{{ loading ? '…' : occupiedSpots }}</p>
        </div>
      </div>
    </div>
    <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
      <div class="flex items-center gap-3">
        <span class="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-amber-700" aria-hidden="true">🟡</span>
        <div>
          <p class="text-sm font-medium text-gray-500">Inactive spots</p>
          <p class="text-2xl font-semibold text-gray-900">{{ loading ? '…' : inactiveSpots }}</p>
        </div>
      </div>
    </div>
    <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
      <div class="flex items-center gap-3">
        <span class="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-700" aria-hidden="true">🧾</span>
        <div>
          <p class="text-sm font-medium text-gray-500">Open tickets</p>
          <p class="text-2xl font-semibold text-gray-900">{{ loading ? '…' : openTickets }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listSpots } from '../api/spots'
import { listTickets } from '../api/tickets'

const loading = ref(true)
const freeSpots = ref(0)
const occupiedSpots = ref(0)
const inactiveSpots = ref(0)
const openTickets = ref(0)

async function fetch() {
  loading.value = true
  try {
    const [freeRes, allSpotsRes, activeOnlyRes, openRes] = await Promise.all([
      listSpots({ only_free: true, active_only: true, limit: 1000 }),
      listSpots({ active_only: false, limit: 1000 }),
      listSpots({ active_only: true, limit: 1000 }),
      listTickets({ state: 'OPEN', limit: 1 }),
    ])
    freeSpots.value = freeRes.data.total
    const totalActive = activeOnlyRes.data.total
    const totalAll = allSpotsRes.data.total
    inactiveSpots.value = Math.max(0, totalAll - totalActive)
    occupiedSpots.value = totalActive - freeRes.data.total
    openTickets.value = openRes.data.total
  } catch {
    freeSpots.value = occupiedSpots.value = inactiveSpots.value = openTickets.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(fetch)

defineExpose({ refresh: fetch })
</script>
