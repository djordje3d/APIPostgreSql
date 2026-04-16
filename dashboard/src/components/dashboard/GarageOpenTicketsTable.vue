<template>
  <div class="dashboard-card overflow-hidden">
    <div class="border-b border-gray-200 px-4 py-3">
      <h2 class="text-lg font-semibold">{{ t("garageDetail.openTickets") }}</h2>
    </div>

    <div
      v-if="error"
      class="flex flex-col items-center justify-center gap-2 px-4 py-8 text-center"
      role="alert"
    >
      <button
        type="button"
        class="text-red-600 underline hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1"
        @click="$emit('retry')"
      >
        {{ t("garageDetail.retryBtn") }}
      </button>
    </div>

    <div
      v-else-if="loading && !hasLoadedOnce"
      class="flex flex-col items-center justify-center gap-3 px-4 py-12 text-gray-500"
      aria-busy="true"
    >
      <span
        class="icon-spinner5 inline-block text-2xl animate-spin"
        aria-hidden="true"
      ></span>
      <span>{{ t("garageDetail.loading") }}</span>
    </div>

    <template v-else>
      <div class="relative overflow-x-auto">
        <div
          v-if="refreshing"
          class="absolute inset-0 z-10 flex items-center justify-center bg-white/70"
          aria-busy="true"
        >
          <span
            class="icon-spinner3 inline-block text-3xl animate-spin text-gray-500"
            aria-hidden="true"
          ></span>
        </div>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                {{ t("garageDetail.id") }}
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                {{ t("garageDetail.entryTime") }}
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                {{ t("garageDetail.spot") }}
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                {{ t("garageDetail.plate") }}
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                {{ t("ticket.image") }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr
              v-for="row in openTickets"
              :key="row.id"
              class="hover:bg-gray-50"
            >
              <td class="px-4 py-3">{{ row.id }}</td>
              <td class="px-4 py-3 text-sm">
                {{ formatTime(row.entry_time) }}
              </td>
              <td class="px-4 py-3">{{ row.spot_code ?? "–" }}</td>
              <td class="px-4 py-3">{{ row.licence_plate ?? "–" }}</td>
              <td class="whitespace-nowrap px-4 py-3">
                <button
                  v-if="rowImageUrl(row)"
                  type="button"
                  class="inline-flex h-10 w-10 items-center justify-center overflow-hidden rounded-lg bg-white p-0 hover:shadow-sm"
                  :title="t('garageDetail.viewTicketImage')"
                  @click="openTicketImage(row)"
                >
                  <img
                    :src="rowImageUrl(row)"
                    :alt="`Ticket image for #${row.id}`"
                    class="h-full w-full object-cover"
                    loading="lazy"
                  />
                </button>
                <div
                  v-else
                  class="flex h-10 w-10 items-center justify-center rounded-lg border border-dashed border-gray-200 bg-gray-50 text-xs text-gray-400 select-none"
                  :title="t('garageDetail.noTicketImage')"
                >
                  –
                </div>
              </td>
            </tr>
            <tr v-if="openTickets.length === 0">
              <td colspan="5" class="px-4 py-6 text-center text-gray-500">
                {{ t("garageDetail.noOpenTickets") }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <PaginationBar
        :page="page"
        :page-size="pageSize"
        :total="total"
        @update:page="$emit('update:page', $event)"
      />
    </template>

    <Modal
      :model-value="showTicketImageModal"
      :title="
        viewingTicketImage
          ? `${viewingTicketImage.garage_name ?? '–'} — Ticket #${viewingTicketImage.id}`
          : ''
      "
      @update:model-value="onTicketImageModalUpdate"
    >
      <div class="flex items-center justify-center p-1">
        <img
          v-if="ticketImagePreviewUrl"
          :src="ticketImagePreviewUrl"
          :alt="
            viewingTicketImage
              ? `Ticket image for #${viewingTicketImage.id}`
              : 'Ticket image'
          "
          class="max-h-[70vh] w-full rounded-lg border border-gray-200 bg-white object-contain"
        />
        <div
          v-else
          class="flex h-[200px] w-full items-center justify-center rounded-lg border border-dashed border-gray-200 bg-gray-50 text-gray-400"
        >
          –
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from "vue";
import { useI18n } from "vue-i18n";
import type { TicketDashboardRow } from "../../api/tickets";
import { formatTime } from "../../composables/useFormatters";
import { normalizeTicketImageUrl } from "../../utils/ticketImageUrl";
import PaginationBar from "../ui/PaginationBar.vue";
import Modal from "../ui/Modal.vue";

const { t } = useI18n();

defineProps<{
  openTickets: TicketDashboardRow[];
  page: number;
  pageSize: number;
  total: number;
  loading: boolean;
  refreshing: boolean;
  error: boolean;
  hasLoadedOnce: boolean;
}>();

defineEmits<{
  retry: [];
  "update:page": [page: number];
}>();

const viewingTicketImage = ref<TicketDashboardRow | null>(null);
const showTicketImageModal = ref(false);

const ticketImagePreviewUrl = computed(() =>
  normalizeTicketImageUrl(viewingTicketImage.value?.image_url),
);

function rowImageUrl(row: TicketDashboardRow): string | undefined {
  return normalizeTicketImageUrl(row.image_url);
}

function openTicketImage(t: TicketDashboardRow): void {
  viewingTicketImage.value = t;
  showTicketImageModal.value = true;
}

function onTicketImageModalUpdate(value: boolean): void {
  showTicketImageModal.value = value;
  if (!value) {
    nextTick(() => {
      viewingTicketImage.value = null;
    });
  }
}
</script>
