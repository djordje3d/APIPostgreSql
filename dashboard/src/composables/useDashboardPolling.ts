import { ref, watch, onMounted, onUnmounted } from "vue";
import type { Ref } from "vue";

const DEFAULT_POLL_MS = 12_000;
const TICK_MS = 250;

export function useDashboardPolling(
  refresh: () => void,
  options?: { intervalMs?: number; enabled?: Ref<boolean> }
) {
  const intervalMs = options?.intervalMs ?? DEFAULT_POLL_MS;
  const enabled = options?.enabled;

  const pollId = ref<ReturnType<typeof setInterval> | null>(null);
  const tickId = ref<ReturnType<typeof setInterval> | null>(null);

  const remainingMs = ref(intervalMs);
  const isRunning = ref(false);

  function isAllowed(): boolean {
    return enabled === undefined || enabled.value;
  }

  function stopCountdown() {
    if (tickId.value) {
      clearInterval(tickId.value);
      tickId.value = null;
    }
    isRunning.value = false;
  }

  function startCountdown() {
    stopCountdown();
    remainingMs.value = intervalMs;
    isRunning.value = true;

    tickId.value = setInterval(() => {
      remainingMs.value = Math.max(0, remainingMs.value - TICK_MS);
    }, TICK_MS);
  }

  function stopPolling() {
    if (pollId.value) {
      clearInterval(pollId.value);
      pollId.value = null;
    }
    stopCountdown();
  }

  function doRefreshAndRestartCountdown() {
    refresh();
    // countdown ima smisla samo ako poll sme da radi i tab je vidljiv
    if (document.visibilityState === "visible" && isAllowed()) {
      startCountdown();
    }
  }

  function startPolling() {
    if (pollId.value) return;
    if (!isAllowed()) return;
    if (document.visibilityState !== "visible") return;

    // start countdown odmah, pa zakazuj refresh
    startCountdown();
    pollId.value = setInterval(doRefreshAndRestartCountdown, intervalMs);
  }

  function onVisibilityChange() {
    if (document.visibilityState === "visible") {
      // kad se vrati tab: osveži jednom i pokreni polling
      stopPolling();
      if (isAllowed()) {
        doRefreshAndRestartCountdown();
        startPolling();
      }
    } else {
      stopPolling();
    }
  }

  onMounted(() => {
    if (document.visibilityState === "visible" && isAllowed()) {
      startPolling();
    }
    document.addEventListener("visibilitychange", onVisibilityChange);
  });

  if (enabled !== undefined) {
    watch(enabled, (on) => {
      if (document.visibilityState !== "visible") return;

      if (on) {
        // kad user uključi: osveži odmah + kreni
        doRefreshAndRestartCountdown();
        startPolling();
      } else {
        stopPolling();
      }
    });
  }

  onUnmounted(() => {
    stopPolling();
    document.removeEventListener("visibilitychange", onVisibilityChange);
  });

  return {
    startPolling,
    stopPolling,
    remainingMs,
    intervalMs,
    isRunning,
  };
}