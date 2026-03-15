<template>
  <div class="rounded-lg bg-white shadow ring-1 ring-gray-200">
    <div class="border-b border-gray-200 px-4 py-3">
      <h2 class="text-lg font-semibold text-gray-900">{{ t('garageOverview.title') }}</h2>
    </div>

    <div class="overflow-x-auto">
      <div
        v-if="error"
        class="flex flex-col items-center justify-center gap-2 px-4 py-8 text-center"
        role="alert"
      >
        <ButtonIn
          id="retryBtn"
          :label="t('garageOverview.failedToFetchData')"
          variant="outline"
          @userclick="retry"
          :caption="t('garageOverview.retry')"
        />
      </div>

      <div
        v-else-if="loading"
        class="flex flex-col items-center justify-center gap-3 px-4 py-12 text-gray-500"
        aria-busy="true"
        aria-live="polite"
      >
        <span
          class="icon-spinner11 inline-block text-2xl animate-spin"
          aria-hidden="true"
        ></span>
        <span>{{ t('garageOverview.loading') }}</span>
      </div>

      <div
        v-else-if="!hasLoadedOnce && !refreshing"
        class="px-4 py-12 text-center text-gray-400"
      >
        —
      </div>

      <div v-else class="relative min-h-[120px]">
        <div
          v-if="refreshing"
          class="absolute inset-0 z-10 flex items-center justify-center bg-white/70"
          aria-busy="true"
          aria-label="Refreshing"
        >
          <span
            class="icon-spinner2 inline-block text-3xl animate-spin text-gray-500"
            aria-hidden="true"
          ></span>
        </div>

        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th
                class="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500"
              >
                {{ t('garageOverview.garage') }}
              </th>
              <th
                class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500"
              >
                {{ t('garageOverview.garageTotalSpots') }}
              </th>
              <th
                class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500"
              >
                {{ t('garageOverview.free') }}
              </th>
              <th
                class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500"
              >
                {{ t('garageOverview.occupied') }}
              </th>
              <th
                class="px-4 py-2 text-right text-xs font-medium uppercase text-gray-500"
              >
                {{ t('garageOverview.rentable') }}
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-200 bg-white">
            <tr
              v-for="row in rows"
              :key="row.garage_id"
              :class="garageId ? '' : 'cursor-pointer hover:bg-gray-50'"
              @click="
                !garageId &&
                $router.push({
                  name: 'garage-detail',
                  params: { id: row.garage_id },
                })
              "
            >
              <td class="px-4 py-3 font-medium text-gray-900">
                {{ row.name }}
              </td>
              <td class="px-4 py-3 text-right text-gray-700">
                {{ row.total_spots }}
              </td>
              <td class="px-4 py-3 text-right text-green-700">
                {{ row.free }}
              </td>
              <td class="px-4 py-3 text-right text-red-700">
                {{ row.occupied }}
              </td>
              <td class="px-4 py-3 text-right text-gray-700">
                {{ row.rentable }}
              </td>
            </tr>

            <tr v-if="rows.length === 0">
              <td colspan="5" class="px-4 py-6 text-center text-gray-500">
                {{ t('garageOverview.noGarages') }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, inject, onMounted, onUnmounted, watch, type Ref } from "vue";
import { getGarageOverview } from "../../api/garages";
import ButtonIn from "../ui/ButtonIn.vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const DASHBOARD_REFRESH_EVENT = "dashboard-refresh";

const props = withDefaults(defineProps<{ garageId?: number | null }>(), {
  garageId: undefined,
});

const dashboardRefreshAbortSignal = inject<Ref<AbortSignal | null>>(
  "dashboardRefreshAbortSignal",
  ref(null),
);

interface Row {
  garage_id: number;
  name: string;
  total_spots: number;
  free: number;
  occupied: number;
  rentable: number;
}

const loading = ref(false);
const refreshing = ref(false);
const error = ref(false);
const hasLoadedOnce = ref(false);
const rows = ref<Row[]>([]);

async function fetch() {
  const hasData = rows.value.length > 0 || hasLoadedOnce.value;

  if (!hasData) {
    loading.value = true;
    error.value = false;
  } else {
    refreshing.value = true;
  }

  const signal = dashboardRefreshAbortSignal?.value ?? undefined;
  const config = signal ? { signal } : undefined;

  try {
    const res = await getGarageOverview(props.garageId ?? undefined, config);
    rows.value = res.data.map((r) => ({
      garage_id: r.garage_id,
      name: r.name,
      total_spots: r.total_spots,
      free: r.free_spots,
      occupied: r.occupied_spots,
      rentable: r.rentable_spots,
    }));
    hasLoadedOnce.value = true;
    error.value = false;
  } catch (err: unknown) {
    if ((err as { code?: string })?.code === "ERR_CANCELED") return;
    error.value = true;
    if (!hasData) rows.value = [];
  } finally {
    loading.value = false;
    refreshing.value = false;
  }
}

function retry() {
  error.value = false;
  fetch();
}

function onDashboardRefresh() {
  fetch();
}

watch(
  () => props.garageId,
  () => {
    fetch();
  },
);

onMounted(() => {
  window.addEventListener(DASHBOARD_REFRESH_EVENT, onDashboardRefresh);
  fetch();
});

onUnmounted(() => {
  window.removeEventListener(DASHBOARD_REFRESH_EVENT, onDashboardRefresh);
});
</script>