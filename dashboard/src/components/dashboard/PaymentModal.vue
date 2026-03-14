<template>
  <Modal
    :model-value="modelValue"
    @update:model-value="close"
    :title="modalTitle"
  >
    <p class="mt-1 text-sm text-gray-600">Ticket #{{ ticketId }}</p>
    <p class="mb-1 text-sm text-gray-600"> {{ t('payment.totalFee') }}: {{ formatMoney(fee) }}</p>
    <p v-if="restToPay != null" class="mb-2 text-sm font-medium text-amber-700">
      {{ t('payment.restToPay') }}: {{ formatMoney(restToPay) }}
    </p>
    <form @submit.prevent="submit">
      <div class="space-y-3">
        <div class="flex gap-3">
          <div class="min-w-0 flex-1">
            <InputIn
              id="amount"
              v-model="amount"
              :label="t('payment.amount')"
              type="number"
              step="1"
              min="1"
              required
              :variant="amountExceedsRest ? 'error' : 'default'"
              :error="
                amountExceedsRest && restToPay != null
                  ? `${t('payment.amountExceedsRemainingBalance')} ${formatMoney(restToPay)}.`
                  : undefined
              "
            />
          </div>
          <div class="min-w-0 flex-1">
            <StandardDropdown
              :label="t('payment.method')"
              :options="methodOptions"
              v-model="method"
              :placeholder="t('payment.selectMethod')"
              :nullable="false"
            />
          </div>
        </div>
      </div>
      <p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
      <div class="mt-4 flex justify-between gap-2">
        <ButtonIn
          id="cancelBtn"
          label="Cancel"
          variant="outline"
          @userclick="close"
          caption="Cancel"
        />

        <ButtonIn
          id="submitPaymentBtn"
          label="Submit payment"
          variant="primary"
          :disabled="amountExceedsRest || loading"
          @userclick="submit"
          caption="Submit payment"
        />
      </div>
    </form>
  </Modal>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed, onMounted } from "vue";
import Modal from "../ui/Modal.vue";
import StandardDropdown from "../ui/StandardDropdown.vue";
import ButtonIn from "../ui/ButtonIn.vue";
import InputIn from "../ui/InputIn.vue";
import { formatMoney } from "../../composables/useFormatters";
import { createPayment, getPaymentsByTicket } from "../../api/payments";
import { useI18n } from "vue-i18n";

const props = defineProps<{
  modelValue: boolean;
  ticketId: number;
  fee: string | null;
  garageName?: string | null;
}>();
const emit = defineEmits<{
  close: [];
  done: [];
  "update:modelValue": [value: boolean];
}>();
const { t } = useI18n();

function close() {
  emit("update:modelValue", false);
  emit("close");
}

const modalTitle = computed(() =>
  props.garageName ? `${t('payment.payment')} – ${props.garageName}` : t('payment.payment'),
);

const amount = ref<number>(0);
const method = ref<string | null>("CASH");

const methodOptions = [
  { id: "CASH" as const, label: t('payment.cash') },
  { id: "CARD" as const, label: t('payment.card') },
];
const loading = ref(false);
const error = ref("");
const totalPaid = ref<number>(0);

const feeNum = computed(() => {
  const f = props.fee ? parseFloat(props.fee) : 0;
  return Number.isNaN(f) ? 0 : f;
});

const restToPay = computed(() => {
  const rest = feeNum.value - totalPaid.value;
  return rest < 0 ? 0 : rest;
});

const amountExceedsRest = computed(() => {
  if (restToPay.value == null || restToPay.value <= 0) return false;
  return amount.value > restToPay.value;
});

async function loadPayments() {
  try {
    const res = await getPaymentsByTicket(props.ticketId, { limit: 500 });
    const sum = res.data.items.reduce((s, p) => s + parseFloat(p.amount), 0);
    totalPaid.value = sum;
    const fee = props.fee ? parseFloat(props.fee) : 0;
    amount.value = Math.max(0, (Number.isNaN(fee) ? 0 : fee) - sum);
  } catch {
    totalPaid.value = 0;
  }
}

watch(
  () => [props.fee, props.ticketId],
  () => {
    loadPayments();
  },
  { immediate: true },
);

onMounted(loadPayments);

async function submit() {
  error.value = "";
  if (amount.value <= 0) {
    error.value = t('payment.amountMustBePositive');
    return;
  }
  if (amountExceedsRest.value) {
    error.value = t('payment.amountExceedsRemainingBalance', { amount: formatMoney(restToPay.value!) });
    return;
  }
  loading.value = true;
  try {
    await createPayment({
      ticket_id: props.ticketId,
      amount: amount.value,
      method: method.value ?? "CASH",
      currency: "RSD",
    });
    loading.value = false;
    nextTick(() => {
      emit("done");
      close();
    });
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response
      ?.data?.detail;
    error.value = typeof msg === "string" ? msg : t('payment.paymentFailed');
    loading.value = false;
  }
}
</script>
