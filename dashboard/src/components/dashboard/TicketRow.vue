<template>
  <tr class="hover:bg-gray-50">
    <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
      {{ ticket.garage_name ?? "–" }}
    </td>

    <td class="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
      {{ ticket.licence_plate ?? "–" }}
    </td>

    <td class="px-4 py-3 text-sm text-gray-700">
      {{ ticket.spot_code ?? "–" }}
    </td>

    <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
      {{ formatTime(ticket.entry_time) }}
    </td>

    <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
      {{ formatTime(ticket.exit_time) }}
    </td>

    <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
      {{ ticketStateLabel }}
    </td>

    <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
      {{ paymentStatusLabel }}
    </td>

    <td class="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-700">
      {{ formatMoney(ticket.fee) }}
    </td>

    <td
      class="whitespace-nowrap px-4 py-3 text-right text-sm font-medium"
      :class="restToPayClass"
    >
      {{ restToPayValue }}
    </td>

    <td class="px-4 py-3 whitespace-nowrap">
      <button
        v-if="ticketImageUrl"
        type="button"
        class="inline-flex h-10 w-10 items-center justify-center overflow-hidden rounded-lg bg-white p-0 hover:shadow-sm"
        title="View image"
        @click="$emit('view-ticket-image', ticket)"
      >
        <img
          :src="ticketImageUrl"
          :alt="`Ticket image for #${ticket.id}`"
          class="h-full w-full object-cover"
          loading="lazy"
        />
      </button>

      <div
        v-else
        class="flex h-10 w-10 items-center justify-center rounded-lg text-xs text-gray-400 select-none"
        title="No image"
      >
        –
      </div>
    </td>

    <td class="whitespace-nowrap px-4 py-3 text-right text-sm">
      <div class="flex items-center justify-end gap-2">
        <button
          type="button"
          class="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-1"
          title="View ticket & payments"
          aria-label="View ticket & payments"
          @click="$emit('view-ticket', ticket)"
        >
          <span class="icon-barcode text-lg" aria-hidden="true"></span>
        </button>

        <template v-if="ticket.ticket_state === 'OPEN'">
          <button
            type="button"
            class="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-1"
            title="Close ticket"
            aria-label="Close ticket"
            @click="$emit('close-ticket', ticket.id)"
          >
            <span class="icon-exit text-lg" aria-hidden="true"></span>
          </button>
        </template>

        <template
          v-else-if="
            ticket.ticket_state === 'CLOSED' && ticket.payment_status !== 'PAID'
          "
        >
          <button
            type="button"
            class="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-1"
            title="Go to payment"
            aria-label="Go to payment"
            @click="$emit('open-payment', ticket)"
          >
            <span class="icon-credit-card text-lg" aria-hidden="true"></span>
          </button>
        </template>
      </div>
    </td>
  </tr>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { formatTime, formatMoney } from "../../composables/useFormatters";
import type { TicketDashboardRow } from "../../api/tickets";

const props = defineProps<{
  ticket: TicketDashboardRow;
  ticketImageUrl?: string;
  restToPayValue: string;
  restToPayClass: string;
}>();

const { t, te } = useI18n();

const ticketStateLabel = computed(() => {
  const s = props.ticket.ticket_state;
  if (!s) return "–";
  const key = `ticket.ticketState.${s}`;
  return te(key) ? t(key) : s;
});

const paymentStatusLabel = computed(() => {
  const s = props.ticket.payment_status;
  if (!s) return "–";
  const key = `ticket.paymentStatus.${s}`;
  return te(key) ? t(key) : s;
});

defineEmits<{
  "view-ticket": [ticket: TicketDashboardRow];
  "view-ticket-image": [ticket: TicketDashboardRow];
  "close-ticket": [ticketId: number];
  "open-payment": [ticket: TicketDashboardRow];
}>();
</script>
