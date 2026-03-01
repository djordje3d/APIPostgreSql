<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="$emit('close')">
      <div class="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <div class="mb-4 flex justify-between">
          <h3 class="text-lg font-semibold">Payment – {{ garageName ? garageName + ' – ' : '' }}Ticket #{{ ticketId }}</h3>
          <button type="button" class="text-gray-500 hover:text-gray-700" @click="$emit('close')">&times;</button>
        </div>
        <p class="mb-1 text-sm text-gray-600">Total fee: {{ formatFeeDisplay(fee) }} RSD</p>
        <p v-if="restToPay != null" class="mb-2 text-sm font-medium text-amber-700">Rest to pay: {{ formatMoney(restToPay) }} RSD</p>
        <form @submit.prevent="submit">
          <div class="space-y-3">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Amount (RSD) *</label>
              <input
                v-model.number="amount"
                type="number"
                step="1"
                min="1"
                required
                class="w-full rounded border px-3 py-2"
                :class="amountExceedsRest ? 'border-red-500 bg-red-50' : 'border-gray-300'"
              />
              <p v-if="amountExceedsRest" class="mt-1 text-sm font-medium text-red-600">Amount exceeds remaining balance. Rest to pay: {{ formatMoney(restToPay!) }} RSD.</p>
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
              :disabled="loading || amountExceedsRest"
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
import { ref, watch, nextTick, computed, onMounted } from 'vue'
import { createPayment, getPaymentsByTicket } from '../api/payments'

const props = defineProps<{
  ticketId: number
  fee: string | null
  garageName?: string | null
}>()
const emit = defineEmits(['close', 'done'])

const amount = ref<number>(0)
const method = ref('CASH')
const loading = ref(false)
const error = ref('')
const totalPaid = ref<number>(0)

const feeNum = computed(() => {
  const f = props.fee ? parseFloat(props.fee) : 0
  return Number.isNaN(f) ? 0 : f
})

const restToPay = computed(() => {
  const rest = feeNum.value - totalPaid.value
  return rest < 0 ? 0 : rest
})

const amountExceedsRest = computed(() => {
  if (restToPay.value == null || restToPay.value <= 0) return false
  return amount.value > restToPay.value
})

function formatMoney(n: number) {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(n)
}

function formatFeeDisplay(fee: string | null): string {
  if (fee == null || fee === '') return '–'
  const n = parseFloat(fee)
  if (Number.isNaN(n)) return '–'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(n)
}

async function loadPayments() {
  try {
    const res = await getPaymentsByTicket(props.ticketId, { limit: 500 })
    const sum = res.data.items.reduce((s, p) => s + parseFloat(p.amount), 0)
    totalPaid.value = sum
    const fee = props.fee ? parseFloat(props.fee) : 0
    amount.value = Math.max(0, (Number.isNaN(fee) ? 0 : fee) - sum)
  } catch {
    totalPaid.value = 0
  }
}

watch(
  () => [props.fee, props.ticketId],
  () => { loadPayments() },
  { immediate: true }
)

onMounted(loadPayments)

async function submit() {
  error.value = ''
  if (amount.value <= 0) {
    error.value = 'Amount must be positive'
    return
  }
  if (amountExceedsRest.value) {
    error.value = `Amount exceeds remaining balance. Rest to pay: ${formatMoney(restToPay.value!)} RSD.`
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
