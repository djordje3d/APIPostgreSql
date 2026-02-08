<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="$emit('close')">
      <div class="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <div class="mb-4 flex justify-between">
          <h3 class="text-lg font-semibold">Payment – Ticket #{{ ticketId }}</h3>
          <button type="button" class="text-gray-500 hover:text-gray-700" @click="$emit('close')">&times;</button>
        </div>
        <p class="mb-2 text-sm text-gray-600">Fee: {{ fee ?? '–' }} RSD</p>
        <form @submit.prevent="submit">
          <div class="space-y-3">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Amount (RSD) *</label>
              <input
                v-model.number="amount"
                type="number"
                step="0.01"
                min="0.01"
                required
                class="w-full rounded border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Method *</label>
              <input v-model="method" type="text" required class="w-full rounded border border-gray-300 px-3 py-2" placeholder="e.g. CASH, CARD" />
            </div>
          </div>
          <p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
          <div class="mt-4 flex gap-2">
            <button
              type="submit"
              class="rounded bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-50"
              :disabled="loading"
            >
              {{ loading ? 'Sending…' : 'Submit payment' }}
            </button>
            <button type="button" class="rounded border border-gray-300 px-4 py-2 hover:bg-gray-50" @click="$emit('close')">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { createPayment } from '../api/payments'

const props = defineProps<{
  ticketId: number
  fee: string | null
}>()
const emit = defineEmits(['close', 'done'])

const amount = ref<number>(0)
const method = ref('CASH')
const loading = ref(false)
const error = ref('')

watch(
  () => props.fee,
  (f) => {
    const n = f ? parseFloat(f) : 0
    amount.value = Number.isNaN(n) ? 0 : n
  },
  { immediate: true }
)

async function submit() {
  error.value = ''
  if (amount.value <= 0) {
    error.value = 'Amount must be positive'
    return
  }
  loading.value = true
  try {
    await createPayment({
      ticket_id: props.ticketId,
      amount: amount.value,
      method: method.value,
      currency: 'RSD',
    })
    loading.value = false
    nextTick(() => {
      emit('done')
      emit('close')
    })
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    error.value = typeof msg === 'string' ? msg : 'Payment failed'
    loading.value = false
  }
}
</script>
