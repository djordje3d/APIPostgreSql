<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-wrap items-center gap-4">
      <router-link
        to="/"
        class="text-gray-600 hover:text-gray-900"
      >
        &larr; {{ t("garageDetail.dashboard") }}
      </router-link>
      <h1 v-if="garage" class="text-2xl font-bold text-gray-900">
        {{ garage.name }}
      </h1>
      <h1 v-else class="text-2xl font-bold text-gray-900">
        {{ t("garageDetail.garage") }} #{{ fallbackId }}
      </h1>
    </div>
    <div
      v-if="garage"
      class="relative rounded-lg bg-white p-4 shadow ring-1 ring-gray-200"
    >
      <div
        v-if="refreshing"
        class="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70"
        aria-busy="true"
      >
        <span
          class="icon-spinner3 inline-block text-2xl animate-spin text-gray-500"
          aria-hidden="true"
        ></span>
      </div>
      <p class="text-sm text-gray-600">
        {{ t("garageDetail.capacity") }}: {{ garage.capacity }} ·
        {{ t("garageDetail.defaultRate") }}:
        {{ formatRate(garage.default_rate) }} RSD
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { Garage } from "../../api/garages";
import { formatRate } from "../../composables/useFormatters";

const { t } = useI18n();

defineProps<{
  garage: Garage | null;
  fallbackId: string;
  refreshing?: boolean;
}>();
</script>
