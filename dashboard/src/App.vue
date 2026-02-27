<template>
  <div class="min-h-screen bg-gray-100">
    <div
      v-if="!isLoginPage && apiConnectionError"
      class="bg-amber-100 px-4 py-3 text-amber-900 ring-1 ring-amber-300"
      role="alert"
    >
      <p class="font-medium">Cannot connect to API at {{ apiConnectionError }}.</p>
      <p class="mt-1 text-sm">Start the backend from the project root: <code class="rounded bg-amber-200 px-1">python -m app.run</code></p>
    </div>
    <!-- Session expiry modal: only when idle (no click/mouse move). Blocks entire dashboard until "Continue session". -->
    <Teleport to="body">
      <div
        v-if="!isLoginPage && showIdleExpiryAlert"
        class="session-expiry-overlay"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="session-expiry-title"
      >
        <div class="session-expiry-modal">
          <p id="session-expiry-title" class="font-medium">
            Your session will expire in {{ sessionExpiryCountdown }}. You will be logged out automatically.
          </p>
          <p class="mt-1 text-sm opacity-90">Click the button below to continue your session.</p>
          <button
            type="button"
            class="mt-4 shrink-0 rounded bg-amber-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            @click="extendSession"
          >
            Continue session
          </button>
        </div>
      </div>
    </Teleport>
    <header v-if="!isLoginPage" class="bg-slate-800 text-white shadow">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <nav class="flex items-center gap-4">
          <router-link to="/" class="text-xl font-semibold">Dashboard</router-link>
          <router-link to="/by-garage" class="text-sm text-slate-300 hover:text-white">By garage</router-link>
          <label class="flex cursor-pointer select-none items-center gap-2 text-sm text-slate-200">
            <input
              v-model="autoRefreshEnabled"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-500 bg-slate-700 text-emerald-600 focus:ring-emerald-500"
            />
            Auto refresh
          </label>
        </nav>
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="rounded bg-slate-600 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
            @click="logout"
          >
            Logout
          </button>
          <button
            type="button"
            class="rounded bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700"
            @click="showNewEntry = true"
          >
            New Vehicle Entry
          </button>
        </div>
      </div>
    </header>
    <main v-if="!isLoginPage" class="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <router-view v-if="!isLoginPage" v-slot="{ Component }">
        <component :is="Component" @open-new-entry="showNewEntry = true" />
      </router-view>
    </main>
    <NewVehicleEntryModal v-if="!isLoginPage" v-model="showNewEntry" @done="onNewEntryDone" />
    <router-view v-if="isLoginPage" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, provide, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import NewVehicleEntryModal from './components/NewVehicleEntryModal.vue'
import { baseURL } from './api/client'
import { clearStoredToken, getMsUntilTokenExpiry } from './api/auth-storage'
import { refresh as refreshToken } from './api/auth'

const AUTO_REFRESH_STORAGE_KEY = 'dashboard-auto-refresh'
/** After this many ms without user activity (no click, no mouse move), show session-expiry alert with countdown. */
const IDLE_MS = 90 * 1000
/** Throttle mousemove so we don't reset idle timer every frame. */
const IDLE_ACTIVITY_THROTTLE_MS = 1000

function loadAutoRefreshEnabled(): boolean {
  try {
    const stored = localStorage.getItem(AUTO_REFRESH_STORAGE_KEY)
    return stored !== 'false'
  } catch {
    return true
  }
}

function formatCountdown(ms: number): string {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000))
  const m = Math.floor(totalSeconds / 60)
  const s = totalSeconds % 60
  return s > 0 ? `${m}:${s.toString().padStart(2, '0')}` : `${m} min`
}

const router = useRouter()
const route = useRoute()
const isLoginPage = computed(() => route.name === 'login')
const sessionExpiryCountdown = computed(() => idleExpiryCountdown.value)
const showNewEntry = ref(false)
const apiConnectionError = ref<string | null>(null)
const autoRefreshEnabled = ref(loadAutoRefreshEnabled())
const showIdleExpiryAlert = ref(false)
const idleExpiryCountdown = ref('')
let tokenExpiryTimeoutId: ReturnType<typeof setTimeout> | null = null
let idleTimeoutId: ReturnType<typeof setTimeout> | null = null
let idleCountdownIntervalId: ReturnType<typeof setInterval> | null = null
let lastActivityAt = 0

function logout() {
  showIdleExpiryAlert.value = false
  if (idleCountdownIntervalId != null) {
    clearInterval(idleCountdownIntervalId)
    idleCountdownIntervalId = null
  }
  if (idleTimeoutId != null) {
    clearTimeout(idleTimeoutId)
    idleTimeoutId = null
  }
  clearStoredToken()
  router.push('/login')
}

/** Clear only token-expiry timers (used when rescheduling). Leaves idle timer intact. */
function clearSessionTimers() {
  if (tokenExpiryTimeoutId != null) {
    clearTimeout(tokenExpiryTimeoutId)
    tokenExpiryTimeoutId = null
  }
}

/** Clear idle timers (and optionally token-expiry). Use before startSessionTimers after refresh. */
function clearAllTimers() {
  clearSessionTimers()
  if (idleTimeoutId != null) {
    clearTimeout(idleTimeoutId)
    idleTimeoutId = null
  }
  if (idleCountdownIntervalId != null) {
    clearInterval(idleCountdownIntervalId)
    idleCountdownIntervalId = null
  }
}

function updateIdleExpiryCountdown() {
  const ms = getMsUntilTokenExpiry()
  if (ms !== null && ms > 0) {
    idleExpiryCountdown.value = formatCountdown(ms)
  }
}

function onIdleTimeout() {
  idleTimeoutId = null
  showIdleExpiryAlert.value = true
  updateIdleExpiryCountdown()
  idleCountdownIntervalId = setInterval(updateIdleExpiryCountdown, 1000)
}

function resetIdleTimer() {
  if (showIdleExpiryAlert.value) return
  if (idleTimeoutId != null) {
    clearTimeout(idleTimeoutId)
    idleTimeoutId = null
  }
  idleTimeoutId = setTimeout(onIdleTimeout, IDLE_MS)
}

function onActivity() {
  const now = Date.now()
  if (now - lastActivityAt < IDLE_ACTIVITY_THROTTLE_MS) return
  lastActivityAt = now
  if (isLoginPage.value || getMsUntilTokenExpiry() === null) return
  resetIdleTimer()
}

async function extendSession() {
  showIdleExpiryAlert.value = false
  if (idleCountdownIntervalId != null) {
    clearInterval(idleCountdownIntervalId)
    idleCountdownIntervalId = null
  }
  try {
    await refreshToken()
    clearAllTimers()
    startSessionTimers()
  } catch {
    // Token may have expired; 401 will clear token and redirect via client interceptor
  }
}

function scheduleTokenExpiryLogout() {
  clearSessionTimers()
  const ms = getMsUntilTokenExpiry()
  if (ms === null) return
  if (ms <= 0) {
    clearStoredToken()
    router.push('/login')
    return
  }
  tokenExpiryTimeoutId = setTimeout(() => {
    tokenExpiryTimeoutId = null
    if (idleCountdownIntervalId != null) {
      clearInterval(idleCountdownIntervalId)
      idleCountdownIntervalId = null
    }
    clearStoredToken()
    router.push('/login')
  }, ms)
}

function startSessionTimers() {
  if (getMsUntilTokenExpiry() === null) return
  resetIdleTimer()
  scheduleTokenExpiryLogout()
}

watch(autoRefreshEnabled, (value) => {
  try {
    localStorage.setItem(AUTO_REFRESH_STORAGE_KEY, String(value))
  } catch {
    // ignore
  }
}, { immediate: true })

provide('autoRefreshEnabled', autoRefreshEnabled)

function onApiError(e: Event) {
  apiConnectionError.value = (e as CustomEvent).detail?.baseURL ?? baseURL
}
function onApiOk() {
  apiConnectionError.value = null
}

onMounted(() => {
  window.addEventListener('api-connection-error', onApiError)
  window.addEventListener('api-connection-ok', onApiOk)
  window.addEventListener('mousemove', onActivity)
  window.addEventListener('click', onActivity)
  window.addEventListener('keydown', onActivity)
  if (!isLoginPage.value) startSessionTimers()
})

watch(
  () => route.name,
  (name) => {
    if (name === 'login') {
      clearAllTimers()
      showIdleExpiryAlert.value = false
    } else if (getMsUntilTokenExpiry() !== null) {
      startSessionTimers()
    }
  }
)

onUnmounted(() => {
  window.removeEventListener('api-connection-error', onApiError)
  window.removeEventListener('api-connection-ok', onApiOk)
  window.removeEventListener('mousemove', onActivity)
  window.removeEventListener('click', onActivity)
  window.removeEventListener('keydown', onActivity)
  clearAllTimers()
})

function onNewEntryDone() {
  nextTick(() => {
    showNewEntry.value = false
    window.dispatchEvent(new CustomEvent('dashboard-refresh'))
  })
}
</script>

<style scoped>
.session-expiry-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.6);
  pointer-events: auto;
}
.session-expiry-modal {
  pointer-events: auto;
  max-width: 24rem;
  padding: 1.5rem;
  background: rgb(245 158 11); /* amber-500 */
  color: rgb(30 27 75); /* amber-950 */
  border-radius: 0.5rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}
</style>
