<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="close">
      <div class="max-h-[90vh] w-full max-w-md overflow-auto rounded-lg bg-white p-6 shadow-xl">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-lg font-semibold">New Vehicle Entry</h2>
          <button type="button" class="text-gray-500 hover:text-gray-700" @click="close">&times;</button>
        </div>
        <form @submit.prevent="submit">
          <div class="space-y-4">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Licence plate *</label>
              <input
                v-model="form.licence_plate"
                type="text"
                required
                class="w-full rounded border border-gray-300 px-3 py-2"
                placeholder="e.g. AB-123-CD"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Vehicle type *</label>
              <select v-model="form.vehicle_type_id" required class="w-full rounded border border-gray-300 px-3 py-2">
                <option value="">Select type</option>
                <option v-for="vt in vehicleTypes" :key="vt.id" :value="vt.id">{{ vt.type }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Garage *</label>
              <select v-model="form.garage_id" required class="w-full rounded border border-gray-300 px-3 py-2" @change="onGarageChange">
                <option value="">Select garage</option>
                <option v-for="g in garages" :key="g.id" :value="g.id">{{ g.name }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Spot (optional, auto if empty)</label>
              <select v-model="form.spot_id" class="w-full rounded border border-gray-300 px-3 py-2">
                <option :value="null">Auto-assign first free</option>
                <option v-for="s in freeSpots" :key="s.id" :value="s.id">{{ s.code }}</option>
              </select>
            </div>
          </div>
          <p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
          <p v-if="success" class="mt-2 text-sm text-green-600">{{ success }}</p>
          <div class="mt-6 flex gap-2">
            <button
              type="submit"
              class="rounded bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-50"
              :disabled="loading"
            >
              {{ loading ? 'Creating…' : 'Create entry' }}
            </button>
            <button type="button" class="rounded border border-gray-300 px-4 py-2 hover:bg-gray-50" @click="close">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { listVehicleTypes } from '../api/vehicleTypes'
import { listGarages } from '../api/garages'
import { listSpots } from '../api/spots'
import { getVehicleByPlate, createVehicle } from '../api/vehicles'
import { ticketEntry } from '../api/tickets'
import type { VehicleType } from '../api/vehicleTypes'
import type { Garage } from '../api/garages'
import type { Spot } from '../api/spots'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits(['update:modelValue', 'done'])

const form = ref({
  licence_plate: '',
  vehicle_type_id: '' as number | '',
  garage_id: '' as number | '',
  spot_id: null as number | null,
})
const vehicleTypes = ref<VehicleType[]>([])
const garages = ref<Garage[]>([])
const freeSpots = ref<Spot[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')

function close() {
  emit('update:modelValue', false)
  error.value = ''
  success.value = ''
}

async function loadOptions() {
  try {
    const [vtRes, gRes] = await Promise.all([
      listVehicleTypes({ limit: 100 }),
      listGarages({ limit: 100 }),
    ])
    vehicleTypes.value = vtRes.data.items
    garages.value = gRes.data.items
  } catch {
    error.value = 'Failed to load options'
  }
}

async function onGarageChange() {
  const gid = form.value.garage_id
  if (!gid) {
    freeSpots.value = []
    return
  }
  try {
    const res = await listSpots({ garage_id: gid, only_free: true, active_only: true, limit: 500 })
    freeSpots.value = res.data.items
  } catch {
    freeSpots.value = []
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      loadOptions()
      form.value = { licence_plate: '', vehicle_type_id: '', garage_id: '', spot_id: null }
      freeSpots.value = []
    }
  }
)

async function submit() {
  error.value = ''
  success.value = ''
  const plate = form.value.licence_plate.trim()
  const vehicleTypeId = form.value.vehicle_type_id
  const garageId = form.value.garage_id
  if (!plate || !vehicleTypeId || !garageId) return

  loading.value = true
  try {
    let vehicleId: number
    try {
      const byPlate = await getVehicleByPlate(plate)
      vehicleId = byPlate.data.id
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } })?.response?.status
      if (status === 404) {
        const create = await createVehicle({
          licence_plate: plate,
          vehicle_type_id: vehicleTypeId,
        })
        vehicleId = create.data.id
      } else throw e
    }
    await ticketEntry({
      vehicle_id: vehicleId,
      garage_id: garageId,
      spot_id: form.value.spot_id ?? undefined,
      rentable_only: false,
    })
    success.value = 'Entry created.'
    setTimeout(() => {
      emit('done')
    }, 800)
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string }; status?: number } })?.response?.data?.detail
    error.value = typeof msg === 'string' ? msg : 'Entry failed.'
  } finally {
    loading.value = false
  }
}
</script>
