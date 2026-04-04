<template>
  <section
    class="overflow-hidden rounded-3xl border border-slate-200 bg-white/90 shadow-sm ring-1 ring-white/60 backdrop-blur"
  >
    <div class="border-b border-slate-100 px-5 py-4 sm:px-6">
      <div
        class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <p
            class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400"
          >
            Garage
          </p>
          <h2 class="mt-1 text-xl font-semibold text-slate-900">
            {{ t("garageDetail.spots") }}
          </h2>
          <p class="mt-1 text-sm text-slate-500">
            Overview of active and rentable parking spots.
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <span
            class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700 ring-1 ring-slate-200"
          >
            {{ total }} total
          </span>

          <span
            v-if="refreshing"
            class="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700 ring-1 ring-emerald-200"
          >
            Refreshing...
          </span>
        </div>
      </div>
    </div>

    <div
      v-if="error"
      class="px-5 py-6 sm:px-6"
      role="alert"
    >
      <div
        class="rounded-2xl border border-red-200 bg-red-50 px-6 py-8 text-center"
      >
        <p class="text-base font-medium text-red-700">
          Failed to load spots.
        </p>
        <button
          type="button"
          class="mt-3 inline-flex items-center justify-center rounded-xl border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-700 transition hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1"
          @click="$emit('retry')"
        >
          {{ t("garageDetail.retryBtn") }}
        </button>
      </div>
    </div>

    <div
      v-else-if="loading && !hasLoadedOnce"
      class="px-5 py-6 sm:px-6"
      aria-busy="true"
    >
      <div
        class="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 py-12 text-slate-500"
      >
        <span
          class="icon-spinner5 inline-block animate-spin text-3xl"
          aria-hidden="true"
        ></span>
        <span class="text-sm font-medium">{{ t("garageDetail.loading") }}</span>
      </div>
    </div>

    <template v-else>
      <div class="p-5 sm:p-6">
        <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <div class="relative overflow-x-auto">
            <div
              v-if="refreshing"
              class="absolute inset-0 z-10 flex items-center justify-center bg-white/70 backdrop-blur-[1px]"
              aria-busy="true"
            >
              <div
                class="flex items-center gap-3 rounded-full border border-slate-200 bg-white px-4 py-2 shadow-sm"
              >
                <span
                  class="icon-spinner3 inline-block animate-spin text-lg text-slate-500"
                  aria-hidden="true"
                ></span>
                <span class="text-sm font-medium text-slate-600">
                  Refreshing...
                </span>
              </div>
            </div>

            <table class="min-w-full">
              <thead class="bg-slate-50/80">
                <tr>
                  <th
                    class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                  >
                    {{ t("garageDetail.spot") }}
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                  >
                    {{ t("garageDetail.spotOccupancy") }}
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                  >
                    {{ t("garageDetail.rentableSpots") }}
                  </th>
                  <th
                    class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                  >
                    {{ t("garageDetail.activeSpots") }}
                  </th>
                </tr>
              </thead>

              <tbody class="bg-white">
                <tr
                  v-for="s in spots"
                  :key="s.id"
                  class="transition hover:bg-slate-50"
                >
                  <td
                    class="border-t border-slate-100 px-4 py-3 text-sm font-semibold text-slate-900"
                  >
                    {{ s.code }}
                  </td>

                  <td class="border-t border-slate-100 px-4 py-3 text-sm">
                    <span
                      class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold"
                      :class="
                        s.is_occupied
                          ? 'bg-amber-50 text-amber-800 ring-1 ring-amber-200'
                          : 'bg-slate-50 text-slate-700 ring-1 ring-slate-200'
                      "
                    >
                      {{
                        s.is_occupied
                          ? t('garageDetail.spotOccupied')
                          : t('garageDetail.spotFree')
                      }}
                    </span>
                  </td>

                  <td class="border-t border-slate-100 px-4 py-3 text-sm">
                    <span
                      class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold"
                      :class="
                        s.is_rentable
                          ? 'bg-sky-50 text-sky-700 ring-1 ring-sky-200'
                          : 'bg-slate-100 text-slate-600 ring-1 ring-slate-200'
                      "
                    >
                      {{
                        s.is_rentable
                          ? t('garageDetail.yes')
                          : t('garageDetail.no')
                      }}
                    </span>
                  </td>

                  <td class="border-t border-slate-100 px-4 py-3 text-sm">
                    <span
                      class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold"
                      :class="
                        s.is_active
                          ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
                          : 'bg-rose-50 text-rose-700 ring-1 ring-rose-200'
                      "
                    >
                      {{
                        s.is_active
                          ? t('garageDetail.yes')
                          : t('garageDetail.no')
                      }}
                    </span>
                  </td>
                </tr>

                <tr v-if="spots.length === 0">
                  <td colspan="4" class="px-4 py-0">
                    <div
                      class="mx-2 my-4 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center"
                    >
                      <p class="text-base font-medium text-slate-700">
                        {{ t("garageDetail.noSpots") }}
                      </p>
                      <p class="mt-1 text-sm text-slate-500">
                        There are no parking spots to display right now.
                      </p>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="mt-4">
          <PaginationBar
            :page="page"
            :page-size="pageSize"
            :total="total"
            @update:page="$emit('update:page', $event)"
          />
        </div>
      </div>
    </template>
  </section>
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