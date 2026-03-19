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

    <td class="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-700">
      {{ formatMoney(ticket.fee) }}
    </td>

    <td
      class="whitespace-nowrap px-4 py-3 text-right text-sm font-medium"
      :class="restToPayClass"
    >
      {{ restToPayValue }}
    </td>

    <td class="px-4 py-3">
      <span
        class="font-mono text-sm tracking-[0.25em] text-gray-800"
        aria-label="Ticket ID"
      >
        {{ ticket.id }}
      </span>
    </td>

    <td class="whitespace-nowrap px-4 py-3 text-right text-sm">
      <button
        type="button"
        class="icon-barcode text-2xl font-bold text-slate-800 hover:text-slate-900"
        title="View ticket & payments"
        @click="$emit('view-ticket', ticket)"
        style="line-height: 1"
      ></button>

      <template v-if="ticket.ticket_state === 'OPEN'">
        <button
          type="button"
          class="icon-exit ml-2 text-2xl font-bold text-amber-600 hover:text-amber-800"
          title="Close ticket"
          @click="$emit('close-ticket', ticket.id)"
        ></button>
      </template>

      <template
        v-else-if="
          ticket.ticket_state === 'CLOSED' && ticket.payment_status !== 'PAID'
        "
      >
        <button
          type="button"
          class="icon-credit-card ml-2 text-2xl font-bold text-emerald-600 hover:text-emerald-800"
          title="Go to payment"
          @click="$emit('open-payment', ticket)"
        ></button>
      </template>
    </td>
  </tr>
</template>

<script setup lang="ts">
import { formatTime, formatMoney } from "../../composables/useFormatters";
import type { TicketDashboardRow } from "../../api/tickets";

defineProps<{
  ticket: TicketDashboardRow;
  restToPayValue: string;
  restToPayClass: string;
}>();

defineEmits<{
  "view-ticket": [ticket: TicketDashboardRow];
  "close-ticket": [ticketId: number];
  "open-payment": [ticket: TicketDashboardRow];
}>();
</script>

