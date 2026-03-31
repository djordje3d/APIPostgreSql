<template>
  <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
    <div class="border-b border-gray-200 px-4 py-3">
      <h2 class="text-lg font-semibold">{{ t("garageDetail.spots") }}</h2>
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
                {{ t("garageDetail.spot") }}
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                {{ t("garageDetail.rentableSpots") }}
              </th>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                {{ t("garageDetail.activeSpots") }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr v-for="s in spots" :key="s.id">
              <td class="px-4 py-3 font-medium">{{ s.code }}</td>
              <td class="px-4 py-3">
                {{ s.is_rentable ? t("garageDetail.yes") : t("garageDetail.no") }}
              </td>
              <td class="px-4 py-3">
                {{ s.is_active ? t("garageDetail.yes") : t("garageDetail.no") }}
              </td>
            </tr>
            <tr v-if="spots.length === 0">
              <td colspan="3" class="px-4 py-6 text-center text-gray-500">
                {{ t("garageDetail.noSpots") }}
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
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { Spot } from "../../api/spots";
import PaginationBar from "../ui/PaginationBar.vue";

const { t } = useI18n();

defineProps<{
  spots: Spot[];
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
</script>
