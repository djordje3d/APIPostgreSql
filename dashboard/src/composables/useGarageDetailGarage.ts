import { ref, reactive, type ComputedRef } from "vue";
import { getGarage } from "../api/garages";
import type { Garage } from "../api/garages";

function isCanceled(err: unknown): boolean {
  return (err as { code?: string })?.code === "ERR_CANCELED";
}

export function useGarageDetailGarage(garageId: ComputedRef<number | null>) {
  const garage = ref<Garage | null>(null);
  const loading = ref(true);
  const refreshing = ref(false);
  const error = ref(false);
  const hasLoadedOnce = ref(false);

  async function fetchGarage(signal: AbortSignal): Promise<void> {
    const id = garageId.value;
    if (!id) {
      garage.value = null;
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
      const res = await getGarage(id, { signal });
      garage.value = res.data;
      error.value = false;
      hasLoadedOnce.value = true;
    } catch (err: unknown) {
      if (isCanceled(err)) return;
      error.value = true;
      if (!hadData) garage.value = null;
    } finally {
      loading.value = false;
      refreshing.value = false;
    }
  }

  return reactive({
    garage,
    loading,
    refreshing,
    error,
    hasLoadedOnce,
    fetchGarage,
  });
}
