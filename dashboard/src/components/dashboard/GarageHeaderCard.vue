<template>
  <section
    class="dashboard-card flex h-full flex-col p-4"
  >
    <div class="border-b border-gray-200 pb-4">
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

    <div class="flex-1 pt-4">
      <div
        class="grid h-full grid-cols-2 gap-3 rounded border border-gray-200 bg-gray-50 p-3 md:grid-cols-4 md:gap-0 md:divide-x md:divide-gray-200"
      >
        <div class="px-3 py-2">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {{ t("garageOverview.garageId") }}
          </p>
          <p class="mt-1 text-xl font-semibold text-slate-900">
            {{ garage?.id ?? fallbackId ?? "—" }}
          </p>
        </div>

        <div class="px-3 py-2">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {{ t("garageDetail.capacity") }}
          </p>
          <p class="mt-1 text-xl font-semibold text-slate-900">
            {{ garage?.capacity ?? "—" }}
          </p>
        </div>

        <div class="px-3 py-2">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {{ t("garageDetail.defaultRate") }}
          </p>
          <p class="mt-1 text-xl font-semibold text-slate-900">
            {{ garage?.default_rate ?? "—" }} RSD
          </p>
        </div>

        <div class="px-3 py-2">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {{ t("garageHeaderCard.status") }}
          </p>
          <div class="mt-1 inline-flex items-center gap-2">
            <span
              :class="
                refreshing
                  ? 'icon-spinner11 inline-block animate-spin text-emerald-600'
                  : 'icon-info text-emerald-600'
              "
              aria-hidden="true"
            ></span>
            <span class="text-sm font-semibold text-slate-900">{{
              t("garageHeaderCard.operational")
            }}</span>
          </div>
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