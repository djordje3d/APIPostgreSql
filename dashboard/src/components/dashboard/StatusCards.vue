<template>
  <!-- Error: retry -->
  <div
    v-if="error"
    class="flex flex-col items-center justify-center gap-2 rounded-lg bg-white px-4 py-8 shadow ring-1 ring-gray-200"
    role="alert"
  >
    <button
      type="button"
      class="text-red-600 underline hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1"
      @click="$emit('retry')"
    >
      Failed to fetch data, click here to retry
    </button>
  </div>

  <!-- Loading (no data yet) -->
  <div
    v-else-if="loading"
    class="flex flex-col items-center justify-center gap-3 rounded-lg bg-white px-4 py-12 text-gray-500 shadow ring-1 ring-gray-200"
    aria-busy="true"
    aria-live="polite"
  >
    <span
      class="icon-spinner inline-block text-2xl animate-spin"
      aria-hidden="true"
    ></span>
    <span>loading data...</span>
  </div>

  <!-- Idle -->
  <div
    v-else-if="!hasLoadedOnce && !refreshing"
    class="rounded-lg bg-white px-4 py-12 text-center text-gray-400 shadow ring-1 ring-gray-200"
  >
    —
  </div>

  <!-- Content with refreshing overlay -->
  <div v-else class="relative">
    <div
      v-if="refreshing"
      class="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70"
      aria-busy="true"
      aria-label="Refreshing"
    >
      <span
        class="icon-spinner inline-block text-3xl animate-spin text-gray-500"
        aria-hidden="true"
      ></span>
    </div>

    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-2">
      <StatCard :label="t('statusCards.freeSpots')" :value="freeSpots" variant="green" />
      <StatCard :label="t('statusCards.occupiedSpots')" :value="occupiedSpots" variant="red" />
      <StatCard :label="t('statusCards.inactiveSpots')" :value="inactiveSpots" variant="amber" />
      <StatCard :label="t('statusCards.openTickets')" :value="openTickets" variant="slate" />
    </div>
  </div>
</template>

<script setup lang="ts">
import StatCard from "./StatCard.vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

withDefaults(
  defineProps<{
    freeSpots?: number;
    occupiedSpots?: number;
    inactiveSpots?: number;
    openTickets?: number;
    loading?: boolean;
    refreshing?: boolean;
    error?: boolean;
    hasLoadedOnce?: boolean;
  }>(),
  {
    freeSpots: 0,
    occupiedSpots: 0,
    inactiveSpots: 0,
    openTickets: 0,
    loading: false,
    refreshing: false,
    error: false,
    hasLoadedOnce: false,
  },
);

defineEmits<{ retry: [] }>();
</script>
