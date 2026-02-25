import { ref, watch, onMounted, onUnmounted } from 'vue'
import type { Ref } from 'vue'

const POLL_INTERVAL_MS = 12_000 // 12 seconds – balance between live feel and server load

/**
 * Polls while the tab is visible; runs refresh immediately when tab becomes visible again.
 * Use for dashboard and garage detail to keep data in sync with the database.
 * When options.enabled is a ref and false, polling does not run; only manual refresh applies.
 */
export function useDashboardPolling(
  refresh: () => void,
  options?: { intervalMs?: number; enabled?: Ref<boolean> }
) {
  const intervalMs = options?.intervalMs ?? POLL_INTERVAL_MS
  const enabled = options?.enabled
  const intervalId = ref<ReturnType<typeof setInterval> | null>(null)

  function isPollingAllowed(): boolean {
    return enabled === undefined || enabled.value
  }

  function startPolling() {
    if (intervalId.value != null) return
    if (!isPollingAllowed()) return
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
      if (isPollingAllowed()) startPolling()
    } else {
      stopPolling()
    }
  }

  onMounted(() => {
    if (document.visibilityState === 'visible' && isPollingAllowed()) {
      startPolling()
    }
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  if (enabled !== undefined) {
    watch(enabled, (on) => {
      if (document.visibilityState !== 'visible') return
      if (on) {
        refresh()
        startPolling()
      } else {
        stopPolling()
      }
    })
  }

  onUnmounted(() => {
    stopPolling()
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return { startPolling, stopPolling }
}
