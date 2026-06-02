import { ref, computed, reactive, type ComputedRef } from "vue";
import { listTicketsDashboard } from "../api/tickets";
import type { TicketDashboardRow } from "../api/tickets";

function isCanceled(err: unknown): boolean {
  return (err as { code?: string })?.code === "ERR_CANCELED";
}

export function useGarageOpenTickets(garageId: ComputedRef<number | null>) {
  const openTickets = ref<TicketDashboardRow[]>([]);
  const page = ref(1);
  const pageSize = ref(10);
  const total = ref(0);
  const loading = ref(true);
  const refreshing = ref(false);
  const error = ref(false);
  const hasLoadedOnce = ref(false);

  const offset = computed(() => (page.value - 1) * pageSize.value);

  async function fetchOpenTickets(signal: AbortSignal): Promise<void> {
    const id = garageId.value;
    if (!id) {
      openTickets.value = [];
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
      const res = await listTicketsDashboard(
        {
          garage_id: id,
          ticket_state: "OPEN",
          limit: pageSize.value,
          offset: offset.value,
        },
        { signal },
      );
      openTickets.value = res.data.items;
      total.value = res.data.total;
      error.value = false;
      hasLoadedOnce.value = true;
    } catch (err: unknown) {
      if (isCanceled(err)) return;
      error.value = true;
      if (!hadData) {
        openTickets.value = [];
        total.value = 0;
      }
    } finally {
      loading.value = false;
      refreshing.value = false;
    }
  }

  return reactive({
    openTickets,
    page,
    pageSize,
    total,
    offset,
    loading,
    refreshing,
    error,
    hasLoadedOnce,
    fetchOpenTickets,
  });
}
