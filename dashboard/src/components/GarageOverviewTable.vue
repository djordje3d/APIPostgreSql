<template>
  <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
    <div class="border-b border-gray-200 px-4 py-3">
      <h2 class="text-lg font-semibold text-gray-900">Garage overview</h2>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th v-if="!garageId" class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Garage</th>
            <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">Total spots</th>
            <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">Free</th>
            <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">Occupied</th>
            <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">Rentable</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white">
          <tr v-if="loading" class="text-center text-gray-500">
            <td :colspan="garageId ? 4 : 5" class="px-4 py-6">Loading…</td>
          </tr>
          <tr
            v-for="row in rows"
            :key="row.garage_id"
            :class="garageId ? '' : 'cursor-pointer hover:bg-gray-50'"
            @click="!garageId && $router.push({ name: 'garage-detail', params: { id: row.garage_id } })"
          >
            <td v-if="!garageId" class="px-4 py-3 font-medium text-gray-900">{{ row.name }}</td>
            <td class="px-4 py-3 text-right text-gray-700">{{ row.total_spots }}</td>
            <td class="px-4 py-3 text-right text-green-700">{{ row.free }}</td>
            <td class="px-4 py-3 text-right text-red-700">{{ row.occupied }}</td>
            <td class="px-4 py-3 text-right text-gray-700">{{ row.rentable }}</td>
          </tr>
          <tr v-if="!loading && rows.length === 0">
            <td :colspan="garageId ? 4 : 5" class="px-4 py-6 text-center text-gray-500">No garages</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { listGarages, getGarage } from '../api/garages'
import { listSpots } from '../api/spots'
import type { Garage } from '../api/garages'

const props = withDefaults(
  defineProps<{ garageId?: number | null }>(),
  { garageId: undefined }
)

interface Row {
  garage_id: number
  name: string
  total_spots: number
  free: number
  occupied: number
  rentable: number
}

const loading = ref(true)
const rows = ref<Row[]>([])

async function fetch() {
  loading.value = true
  try {
    const garages: Garage[] = props.garageId != null
      ? [(await getGarage(props.garageId)).data]
      : (await listGarages({ limit: 100 })).data.items
    const result: Row[] = []
    for (const g of garages) {
      const [allRes, freeRes] = await Promise.all([
        listSpots({ garage_id: g.id, active_only: false, limit: 1000 }),
        listSpots({ garage_id: g.id, only_free: true, active_only: true, limit: 1000 }),
      ])
      const total = allRes.data.total
      const free = freeRes.data.total
      const activeSpots = allRes.data.items.filter((s) => s.is_active)
      const rentable = activeSpots.filter((s) => s.is_rentable).length
      result.push({
        garage_id: g.id,
        name: g.name,
        total_spots: total,
        free,
        occupied: total - free,
        rentable,
      })
    }
    rows.value = result
  } catch {
    rows.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
watch(() => props.garageId, fetch)

defineExpose({ refresh: fetch })
</script>
