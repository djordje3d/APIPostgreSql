<template>
  <section
    class="h-full overflow-hidden rounded-lg bg-white shadow ring-1 ring-gray-200"
  >
    <div class="border-b border-gray-200 px-5 py-4 sm:px-6">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            {{ t("garageOverview.garage") }}
          </p>
          <h2 class="mt-1 text-xl font-semibold text-slate-900">
            {{ t("garageHeaderCard.title") }}
          </h2>
        </div>

        <span
          class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold"
          :class="
            refreshing
              ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
              : 'bg-slate-100 text-slate-700 ring-1 ring-slate-200'
          "
        >
          {{ refreshing ? t("common.refreshing") : t("common.ready") }}
        </span>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2 sm:p-6">
      <div class="rounded-xl border border-gray-200 bg-gray-50 px-4 py-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {{ t("garageOverview.garageId") }}
        </p>
        <p class="mt-2 text-2xl font-bold text-slate-900">
          {{ garage?.id ?? fallbackId ?? "—" }}
        </p>
      </div>

      <div class="rounded-xl border border-gray-200 bg-gray-50 px-4 py-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {{ t("garageDetail.capacity") }}
        </p>
        <p class="mt-2 text-2xl font-bold text-slate-900">
          {{ garage?.capacity ?? "—" }}
        </p>
      </div>

      <div class="rounded-xl border border-gray-200 bg-gray-50 px-4 py-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {{ t("garageDetail.defaultRate") }}
        </p>
        <p class="mt-2 text-2xl font-bold text-slate-900">
          {{ garage?.default_rate ?? "—" }} RSD
        </p>
      </div>

      <div class="rounded-xl border border-gray-200 bg-gray-50 px-4 py-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {{ t("garageHeaderCard.status") }}
        </p>
        <div class="mt-2 flex items-center gap-2">
          <span class="h-3 w-3 rounded-full bg-emerald-500"></span>
          <span class="text-lg font-semibold text-slate-900">{{
            t("garageHeaderCard.operational")
          }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";

const { t } = useI18n();

defineProps<{
  garage: {
    id?: number | string
    capacity?: number | string
    default_rate?: number | string
  } | null
  fallbackId?: string | number
  refreshing?: boolean
}>()
</script>