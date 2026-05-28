import { ref, computed, reactive, type ComputedRef } from "vue";
import { listSpots } from "../api/spots";
import type { Spot } from "../api/spots";

function isCanceled(err: unknown): boolean {
  return (err as { code?: string })?.code === "ERR_CANCELED";
}

export function useGarageSpots(garageId: ComputedRef<number | null>) {
  const spots = ref<Spot[]>([]);
  const page = ref(1);
  const pageSize = ref(10);
  const total = ref(0);
  const loading = ref(true);
  const refreshing = ref(false);
  const error = ref(false);
  const hasLoadedOnce = ref(false);

  const offset = computed(() => (page.value - 1) * pageSize.value);

  async function fetchSpots(signal: AbortSignal): Promise<void> {
    const id = garageId.value;
    if (!id) {
      spots.value = [];
      total.value = 0;
      loading.value = false;
      refreshing.value = false;
      return;
    }

    const hadData = hasLoadedOnce.value;
    if (!hadData) {
      loading.value = true;
      error.value = false;
    } else {
      refreshing.value = true;
    }

    try {
      const res = await listSpots(
        {
          garage_id: id,
          active_only: false,
          limit: pageSize.value,
          offset: offset.value,
        },
        { signal },
      );
      spots.value = res.data.items;
      total.value = res.data.total;
      error.value = false;
      hasLoadedOnce.value = true;
    } catch (err: unknown) {
      if (isCanceled(err)) return;
      error.value = true;
      if (!hadData) {
        spots.value = [];
        total.value = 0;
      }
    } finally {
      loading.value = false;
      refreshing.value = false;
    }
  }

  return reactive({
    spots,
    page,
    pageSize,
    total,
    offset,
    loading,
    refreshing,
    error,
    hasLoadedOnce,
    fetchSpots,
  });
}
