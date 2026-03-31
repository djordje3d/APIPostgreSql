import { computed, provide, ref, onUnmounted, type ComputedRef, type Ref } from "vue";
import { useRoute } from "vue-router";

/**
 * Route id, abort lifecycle, and provide dashboardRefreshAbortSignal for child widgets.
 */
export function useGarageDetailContext(): {
  garageId: ComputedRef<number | null>;
  refreshAbortControllerRef: Ref<AbortController | null>;
  abortSignal: ComputedRef<AbortSignal | null>;
  prepareRefreshCycle: () => AbortSignal;
} {
  const route = useRoute();
  const garageId = computed(() => {
    const id = Number(route.params.id);
    return Number.isFinite(id) && id > 0 ? id : null;
  });

  const refreshAbortControllerRef = ref<AbortController | null>(null);
  const abortSignal = computed(
    () => refreshAbortControllerRef.value?.signal ?? null,
  );

  provide(
    "dashboardRefreshAbortSignal",
    abortSignal,
  );

  function prepareRefreshCycle(): AbortSignal {
    refreshAbortControllerRef.value?.abort();
    refreshAbortControllerRef.value = new AbortController();
    return refreshAbortControllerRef.value.signal;
  }

  onUnmounted(() => {
    refreshAbortControllerRef.value?.abort();
  });

  return {
    garageId,
    refreshAbortControllerRef,
    abortSignal,
    prepareRefreshCycle,
  };
}
