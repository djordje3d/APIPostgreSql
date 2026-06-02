import { ref, reactive, type ComputedRef } from "vue";
import { getDashboardAnalytics } from "../api/dashboard";
import type { DashboardAnalytics } from "../api/dashboard";
import { getTodayISO, getMonthStartEnd } from "../utils/dashboardDates";

function isCanceled(err: unknown): boolean {
  return (err as { code?: string })?.code === "ERR_CANCELED";
}

export function useGarageRevenue(garageId: ComputedRef<number | null>) {
  const revenueDash = ref<DashboardAnalytics | null>(null);
  const loading = ref(true);
  const refreshing = ref(false);
  const error = ref(false);
  const hasLoadedOnce = ref(false);

  async function fetchRevenue(signal: AbortSignal): Promise<void> {
    const id = garageId.value;
    if (!id) {
      revenueDash.value = null;
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

    const today = getTodayISO();
    const { from: monthFrom, to: monthTo } = getMonthStartEnd();

    try {
      const res = await getDashboardAnalytics(
        {
          garage_id: id,
          today,
          month_from: monthFrom,
          month_to: monthTo,
        },
        { signal },
      );
      revenueDash.value = res.data;
      error.value = false;
      hasLoadedOnce.value = true;
    } catch (err: unknown) {
      if (isCanceled(err)) return;
      error.value = true;
      if (!hadData) revenueDash.value = null;
    } finally {
      loading.value = false;
      refreshing.value = false;
    }
  }

  return reactive({
    revenueDash,
    loading,
    refreshing,
    error,
    hasLoadedOnce,
    fetchRevenue,
  });
}
