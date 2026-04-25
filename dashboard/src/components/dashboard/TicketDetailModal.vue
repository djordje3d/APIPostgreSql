<template>
  <Modal
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :title="modalTitle"
  >
    <template v-if="ticket">
      <div class="mx-auto w-full max-w-sm">
      <div v-if="ticketImageUrl" class="mb-4">
        <ImageIn
          :key="`ticket-img-${ticket.id}-${ticketImageUrl}`"
          :src="ticketImageUrl"
          :alt="`Ticket #${ticket.id}`"
        />
      </div>

      <dl class="space-y-2 text-sm">
        <div>
          <dt class="text-gray-500">{{ t("ticket.garage") }}</dt>
          <dd>{{ ticket.garage_name ?? "–" }}</dd>
        </div>

        <div>
          <dt class="text-gray-500">{{ t("ticket.plate") }}</dt>
          <dd>{{ ticket.licence_plate ?? "–" }}</dd>
        </div>

        <div>
          <dt class="text-gray-500">{{ t("ticket.spot") }}</dt>
          <dd>{{ ticket.spot_code ?? "–" }}</dd>
        </div>

        <div>
          <dt class="text-gray-500">{{ t("ticket.entryTime") }}</dt>
          <dd>{{ formatTime(ticket.entry_time) }}</dd>
        </div>

        <div>
          <dt class="text-gray-500">{{ t("ticket.exitTime") }}</dt>
          <dd>{{ formatTime(ticket.exit_time) || "–" }}</dd>
        </div>

        <div>
          <dt class="text-gray-500">{{ t("ticket.fee") }}</dt>
          <dd>{{ formatMoney(ticket.fee) }}</dd>
        </div>
      </dl>
      </div>

        <dd class="mt-2 -mx-6">
          <img
            v-if="barcodeImageSrc"
            :src="barcodeImageSrc"
            class="block h-auto w-full bg-white"
            :alt="`Barcode for ticket ${ticket.ticket_token ?? ticket.id}`"
          />

          <span v-if="!barcodeImageSrc" class="px-6 text-xs text-gray-400">
            Barcode unavailable
          </span>
        </dd>
      

      <div class="mt-4 border-t border-gray-200 pt-4">
        <h4 class="text-sm font-semibold text-gray-800">
          {{ t("ticket.evidenceOfPayments") }}
        </h4>
        <p class="mt-0.5 text-xs text-gray-500">
          {{ t("ticket.allPaymentsForThisTicket") }}
        </p>

        <PaymentList
          :payments-loading="paymentsLoading"
          :payments="payments"
          :total-paid="paymentsTotal"
        />
      </div>

      <div class="mt-4 flex justify-between gap-2">
        <ButtonIn
          id="ticket-detail-close"
          type="button"
          variant="outline"
          @click="emit('update:modelValue', false)"
          :label="t('ticket.close')"
          :caption="t('ticket.close')"
        >
          {{ t("ticket.close") }}
        </ButtonIn>

        <ButtonIn
          id="ticket-detail-go-to-payment"
          v-if="
            ticket.ticket_state === 'CLOSED' && ticket.payment_status !== 'PAID'
          "
          type="button"
          variant="primary"
          @click="
            emit('go-to-payment', ticket);
            emit('update:modelValue', false)
          "
        >
          {{ t("ticket.goToPayment") }}
        </ButtonIn>
      </div>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { Payment } from "../../api/payments";
import type { TicketDashboardRow } from "../../api/tickets";
import Modal from "../ui/Modal.vue";
import ButtonIn from "../ui/ButtonIn.vue";
import ImageIn from "../ui/ImageIn.vue";
import PaymentList from "./PaymentList.vue";
import { formatTime, formatMoney } from "../../composables/useFormatters";

const props = defineProps<{
  modelValue: boolean;
  ticket: TicketDashboardRow | null;
  ticketImageUrl?: string;
  barcodeImageSrc: string;
  paymentsLoading: boolean;
  payments: Payment[];
  paymentsTotal: number;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  "go-to-payment": [ticket: TicketDashboardRow];
}>();

const { t } = useI18n();

const modalTitle = computed(() =>
  props.ticket
    ? `${props.ticket.garage_name ?? "–"} — Ticket #${props.ticket.id}`
    : ""
);
</script>

