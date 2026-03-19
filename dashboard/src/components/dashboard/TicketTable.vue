<template>
  <table class="min-w-full divide-y divide-gray-200">
    <thead class="bg-gray-50">
      <tr>
        <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
          {{ t("ticket.garage") }}
        </th>
        <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
          {{ t("ticket.plate") }}
        </th>
        <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
          {{ t("ticket.spot") }}
        </th>
        <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
          {{ t("ticket.entryTime") }}
        </th>
        <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
          {{ t("ticket.exitTime") }}
        </th>
        <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">
          {{ t("ticket.fee") }}
        </th>
        <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">
          {{ t("ticket.restToPay") }}
        </th>
        <th class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
          {{ t("ticket.ticketId") }}
        </th>
        <th class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500">
          {{ t("ticket.actions") }}
        </th>
      </tr>
    </thead>

    <tbody class="divide-y divide-gray-200 bg-white">
      <TicketRow
        v-for="t in tickets"
        :key="t.id"
        :ticket="t"
        :rest-to-pay-value="formatRestToPay(t)"
        :rest-to-pay-class="restToPayClass(t)"
        @view-ticket="$emit('view-ticket', $event)"
        @close-ticket="$emit('close-ticket', $event)"
        @open-payment="$emit('open-payment', $event)"
      />

      <tr v-if="tickets.length === 0">
        <td colspan="9" class="px-4 py-6 text-center text-gray-500">
          {{ t("ticket.noTickets") }}
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { TicketDashboardRow } from "../../api/tickets";
import { formatMoney } from "../../composables/useFormatters";
import TicketRow from "./TicketRow.vue";

const props = defineProps<{
  tickets: TicketDashboardRow[];
  restToPayMap: Record<number, number>;
}>();

defineEmits<{
  "view-ticket": [ticket: TicketDashboardRow];
  "close-ticket": [ticketId: number];
  "open-payment": [ticket: TicketDashboardRow];
}>();

const { t } = useI18n();

function formatRestToPay(ticket: TicketDashboardRow): string {
  if (ticket.ticket_state === "OPEN") return "–";
  if (ticket.payment_status === "PAID") return "0 RSD";

  const rest = props.restToPayMap[ticket.id];
  if (rest !== undefined) return formatMoney(String(rest));

  if (
    ticket.ticket_state === "CLOSED" &&
    ticket.payment_status !== "PAID"
  ) {
    return "…";
  }

  return "–";
}

function restToPayClass(ticket: TicketDashboardRow): string {
  if (ticket.payment_status === "PAID" || ticket.ticket_state === "OPEN") {
    return "text-gray-500";
  }
  return "text-amber-700";
}
</script>

