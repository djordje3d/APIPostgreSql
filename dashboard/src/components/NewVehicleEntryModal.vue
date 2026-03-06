<template>
  <Modal :model-value="modelValue" @update:model-value="close" title="New Vehicle Entry">
    <form @submit.prevent="submit">
      <div class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium text-gray-700">Licence plate *</label>
          <input
            v-model="form.licence_plate"
            type="text"
            required
            class="w-full rounded border border-gray-300 px-3 py-2"
            placeholder="e.g. AB123CD"
          />
        </div>
        <div>
          <StandardDropdown
            label="Vehicle type *"
            :options="vehicleTypeOptions"
            :model-value="form.vehicle_type_id || null"
            placeholder="Select type"
            :nullable="false"
            @update:model-value="form.vehicle_type_id = $event ?? ''"
          />
        </div>
        <div>
          <StandardDropdown
            label="Garage *"
            :options="garageOptions"
            :model-value="form.garage_id || null"
            placeholder="Select garage"
            :nullable="false"
            @update:model-value="onGarageSelect($event)"
          />
        </div>
        <div>
          <StandardDropdown
            label="Spot (optional, auto if empty)"
            :options="spotOptions"
            v-model="form.spot_id"
            :nullable="true"
            null-option-label="Auto-assign first free"
          />
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
  </Modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Modal from './Modal.vue'
import StandardDropdown from './StandardDropdown.vue'
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

const vehicleTypeOptions = computed(() =>
  vehicleTypes.value.map((vt) => ({ id: vt.id, label: vt.type }))
)
const garageOptions = computed(() =>
  garages.value.map((g) => ({ id: g.id, label: g.name }))
)
const spotOptions = computed(() =>
  freeSpots.value.map((s) => ({ id: s.id, label: s.code }))
)
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

function onGarageSelect(value: number | null) {
  form.value.garage_id = value ?? ''
  form.value.spot_id = null
  onGarageChange()
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
