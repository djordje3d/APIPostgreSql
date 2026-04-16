<template>
  <div class="dashboard-card p-4">
    <h2 class="mb-4 text-lg font-semibold text-gray-900">{{ t('paymentsRevenue.title') }}</h2>

    <div
      v-if="error"
      class="flex flex-col items-center justify-center gap-2 py-8 text-center"
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

    <div
      v-else-if="loading"
      class="flex flex-col items-center justify-center gap-3 py-12 text-gray-500"
      aria-busy="true"
      aria-live="polite"
    >
      <span
        class="icon-spinner5 inline-block text-2xl animate-spin"
        aria-hidden="true"
      ></span>
      <span>loading data...</span>
    </div>

    <div
      v-else-if="!hasLoadedOnce && !refreshing"
      class="py-12 text-center text-gray-400"
    >
      —
    </div>

    <div v-else class="relative min-h-[100px]">
      <div
        v-if="refreshing"
        class="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70"
        aria-busy="true"
        aria-label="Refreshing"
      >
        <span
          class="icon-spinner3 inline-block text-3xl animate-spin text-gray-500"
          aria-hidden="true"
        ></span>
      </div>

      <div class="space-y-4">
        <SummaryRow :label="t('paymentsRevenue.todayRevenue')" :value="formatMoney(todayRevenue)" />
        <SummaryRow :label="t('paymentsRevenue.thisMonthRevenue')" :value="formatMoney(monthRevenue)" />
        <SummaryRow
          :label="t('paymentsRevenue.unpaidPartiallyPaidTickets')"
          :value="unpaidCount"
          value-class="text-amber-700"
        />
        <SummaryRow
          :label="t('paymentsRevenue.restToPayDescription')"
          :value="formatMoney(totalOutstanding)"
          value-class="text-amber-700"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SummaryRow from "./SummaryRow.vue";
import { formatMoney } from "../../composables/useFormatters";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

withDefaults(
  defineProps<{
    todayRevenue?: number;
    monthRevenue?: number;
    unpaidCount?: number;
    totalOutstanding?: number;
    loading?: boolean;
    refreshing?: boolean;
    error?: boolean;
    hasLoadedOnce?: boolean;
  }>(),
  {
    todayRevenue: 0,
    monthRevenue: 0,
    unpaidCount: 0,
    totalOutstanding: 0,
    loading: false,
    refreshing: false,
    error: false,
    hasLoadedOnce: false,
  },
);

defineEmits<{ retry: [] }>();
</script>
