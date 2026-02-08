import { ref, onMounted, onUnmounted } from 'vue'

const POLL_INTERVAL_MS = 12_000 // 12 seconds – balance between live feel and server load

/**
 * Polls while the tab is visible; runs refresh immediately when tab becomes visible again.
 * Use for dashboard and garage detail to keep data in sync with the database.
 */
export function useDashboardPolling(refresh: () => void, options?: { intervalMs?: number }) {
  const intervalMs = options?.intervalMs ?? POLL_INTERVAL_MS
  const intervalId = ref<ReturnType<typeof setInterval> | null>(null)

  function startPolling() {
    if (intervalId.value != null) return
    intervalId.value = setInterval(refresh, intervalMs)
  }

  function stopPolling() {
    if (intervalId.value != null) {
      clearInterval(intervalId.value)
      intervalId.value = null
    }
  }

  function onVisibilityChange() {
    if (document.visibilityState === 'visible') {
      refresh()
      startPolling()
    } else {
      stopPolling()
    }
  }

  onMounted(() => {
    if (document.visibilityState === 'visible') {
      startPolling()
    }
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onUnmounted(() => {
    stopPolling()
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return { startPolling, stopPolling }
}
