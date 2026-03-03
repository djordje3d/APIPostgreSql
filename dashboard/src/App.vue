<template>
  <div class="min-h-screen bg-gray-100">
    <div
      v-if="routerReady && !isLoginPage && apiConnectionError"
      class="bg-amber-100 px-4 py-3 text-amber-900 ring-1 ring-amber-300"
      role="alert"
    >
      <p class="font-medium">
        Cannot connect to API at {{ apiConnectionError }}.
      </p>
      <p class="mt-1 text-sm">
        Start the backend from the project root:
        <code class="rounded bg-amber-200 px-1">python -m app.run</code>
      </p>
    </div>
    <!-- Session expiry modal: only when idle (no click/mouse move). Blocks entire dashboard until "Continue session". -->
    <Teleport to="body">
      <div
        v-if="routerReady && !isLoginPage && showIdleExpiryAlert"
        class="session-expiry-overlay"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="session-expiry-title"
      >
        <div class="session-expiry-modal">
          <p id="session-expiry-title" class="font-medium">
            Your session will expire in {{ sessionExpiryCountdown }}. You will
            be logged out automatically.
          </p>
          <p class="mt-1 text-sm opacity-90">
            Click the button below to continue your session.
          </p>
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
    <Transition name="fade" mode="out-in">
      <div v-if="!routerReady" key="waiting" class="min-h-screen bg-gray-100" />
      <div v-else-if="isLoginPage" key="login">
        <router-view />
      </div>
      <div v-else key="dashboard">
        <header class="bg-slate-800 text-white shadow">
          <div
            class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-y-3 gap-x-4 px-4 py-3 sm:px-6"
          >
            <nav class="flex flex-wrap items-center gap-2 sm:gap-4">
              <router-link to="/" class="text-base font-semibold sm:text-xl">
                Dashboard
              </router-link>
              <label class="checkbox-wrapper" title="Auto refresh">
                <input v-model="autoRefreshEnabled" type="checkbox" />
                <div class="checkmark">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path
                      d="M20 6L9 17L4 12"
                      stroke-width="3"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    ></path>
                  </svg>
                </div>
                <span class="label hidden sm:inline">Auto refresh</span>
              </label>
              <div class="toolbar">
                <RefreshCountdownRing
                  :duration-ms="intervalMs"
                  :remaining-ms="remainingMs"
                  :enabled="isRunning"
                />
              </div>
            </nav>
            <div
              class="flex flex-shrink-0 flex-wrap items-center gap-2 sm:gap-3"
            >
              <ButtonIn
                type="button"
                variant="outline"
                class="border-white/20 bg-gray-800/30 px-3 py-2 text-sm font-semibold text-white backdrop-blur-lg transition-all duration-300 ease-in-out hover:scale-110 hover:shadow-xl hover:border-emerald-400/40 hover:bg-gray-600/80 sm:px-6 sm:text-base"
                @click="logout"
                title="Logout"
              >
                Logout
              </ButtonIn>
              <ButtonIn 
                type="button"
                variant="outline"
                class="border-white/20 !bg-green-800 px-3 py-2 text-sm font-semibold text-white backdrop-blur-lg transition-all duration-300 ease-in-out hover:scale-110 hover:shadow-xl hover:border-emerald-400/40 hover:bg-emerald-600/80 sm:px-6 sm:text-base"
                @click="showNewEntry = true"
                title="New Vehicle Entry"
              >
                New Vehicle Entry
              </ButtonIn>
            </div>
          </div>
        </header>
        <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6">
          <router-view v-slot="{ Component }">
            <component :is="Component" @open-new-entry="showNewEntry = true" />
          </router-view>
        </main>
        <NewVehicleEntryModal v-model="showNewEntry" @done="onNewEntryDone" />
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import {
  ref,
  computed,
  nextTick,
  watch,
  provide,
  onMounted,
  onUnmounted,
} from "vue";
import { useRouter, useRoute } from "vue-router";
import NewVehicleEntryModal from "./components/NewVehicleEntryModal.vue";
import { baseURL } from "./api/client";
import { clearStoredToken, getMsUntilTokenExpiry } from "./api/auth-storage";
import { refresh as refreshToken } from "./api/auth";
import { useDashboardPolling } from "./composables/useDashboardPolling";
import RefreshCountdownRing from "./components/RefreshCountdownRing.vue";
import ButtonIn from "./components/ButtonIn.vue";

const AUTO_REFRESH_STORAGE_KEY = "dashboard-auto-refresh";
/** After this many ms without user activity (no click, no mouse move), show session-expiry alert with countdown. */
const IDLE_MS = 90 * 1000;
/** Throttle mousemove so we don't reset idle timer every frame. */
const IDLE_ACTIVITY_THROTTLE_MS = 1000;

function loadAutoRefreshEnabled(): boolean {
  try {
    const stored = localStorage.getItem(AUTO_REFRESH_STORAGE_KEY);
    return stored !== "false";
  } catch {
    return true;
  }
}

function formatCountdown(ms: number): string {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return s > 0 ? `${m}:${s.toString().padStart(2, "0")}` : `${m} min`;
}

const router = useRouter();
const route = useRoute();
const routerReady = ref(false);
const isLoginPage = computed(() => route.name === "login");
const sessionExpiryCountdown = computed(() => idleExpiryCountdown.value);
const showNewEntry = ref(false);
const apiConnectionError = ref<string | null>(null);
const autoRefreshEnabled = ref(loadAutoRefreshEnabled());
const showIdleExpiryAlert = ref(false);
const idleExpiryCountdown = ref("");
let tokenExpiryTimeoutId: ReturnType<typeof setTimeout> | null = null;
let idleTimeoutId: ReturnType<typeof setTimeout> | null = null;
let idleCountdownIntervalId: ReturnType<typeof setInterval> | null = null;
let lastActivityAt = 0;

function logout() {
  showIdleExpiryAlert.value = false;
  if (idleCountdownIntervalId != null) {
    clearInterval(idleCountdownIntervalId);
    idleCountdownIntervalId = null;
  }
  if (idleTimeoutId != null) {
    clearTimeout(idleTimeoutId);
    idleTimeoutId = null;
  }
  clearStoredToken();
  router.push("/login");
}

/** Clear only token-expiry timers (used when rescheduling). Leaves idle timer intact. */
function clearSessionTimers() {
  if (tokenExpiryTimeoutId != null) {
    clearTimeout(tokenExpiryTimeoutId);
    tokenExpiryTimeoutId = null;
  }
}

/** Clear idle timers (and optionally token-expiry). Use before startSessionTimers after refresh. */
function clearAllTimers() {
  clearSessionTimers();
  if (idleTimeoutId != null) {
    clearTimeout(idleTimeoutId);
    idleTimeoutId = null;
  }
  if (idleCountdownIntervalId != null) {
    clearInterval(idleCountdownIntervalId);
    idleCountdownIntervalId = null;
  }
}

function updateIdleExpiryCountdown() {
  const ms = getMsUntilTokenExpiry();
  if (ms !== null && ms > 0) {
    idleExpiryCountdown.value = formatCountdown(ms);
  }
}

function onIdleTimeout() {
  idleTimeoutId = null;
  showIdleExpiryAlert.value = true;
  updateIdleExpiryCountdown();
  idleCountdownIntervalId = setInterval(updateIdleExpiryCountdown, 1000);
}

function resetIdleTimer() {
  if (showIdleExpiryAlert.value) return;
  if (idleTimeoutId != null) {
    clearTimeout(idleTimeoutId);
    idleTimeoutId = null;
  }
  idleTimeoutId = setTimeout(onIdleTimeout, IDLE_MS);
}

function onActivity() {
  const now = Date.now();
  if (now - lastActivityAt < IDLE_ACTIVITY_THROTTLE_MS) return;
  lastActivityAt = now;
  if (isLoginPage.value || getMsUntilTokenExpiry() === null) return;
  resetIdleTimer();
}

async function extendSession() {
  showIdleExpiryAlert.value = false;
  if (idleCountdownIntervalId != null) {
    clearInterval(idleCountdownIntervalId);
    idleCountdownIntervalId = null;
  }
  try {
    await refreshToken();
    clearAllTimers();
    startSessionTimers();
  } catch {
    // Token may have expired; 401 will clear token and redirect via client interceptor
  }
}

function scheduleTokenExpiryLogout() {
  clearSessionTimers();
  const ms = getMsUntilTokenExpiry();
  if (ms === null) return;
  if (ms <= 0) {
    clearStoredToken();
    router.push("/login");
    return;
  }
  tokenExpiryTimeoutId = setTimeout(() => {
    tokenExpiryTimeoutId = null;
    if (idleCountdownIntervalId != null) {
      clearInterval(idleCountdownIntervalId);
      idleCountdownIntervalId = null;
    }
    clearStoredToken();
    router.push("/login");
  }, ms);
}

function startSessionTimers() {
  if (getMsUntilTokenExpiry() === null) return;
  resetIdleTimer();
  scheduleTokenExpiryLogout();
}

watch(
  autoRefreshEnabled,
  (value) => {
    try {
      localStorage.setItem(AUTO_REFRESH_STORAGE_KEY, String(value));
    } catch {
      // ignore
    }
  },
  { immediate: true },
);

provide("autoRefreshEnabled", autoRefreshEnabled);

function onApiError(e: Event) {
  apiConnectionError.value = (e as CustomEvent).detail?.baseURL ?? baseURL;
}
function onApiOk() {
  apiConnectionError.value = null;
}

onMounted(() => {
  router.isReady().then(() => {
    routerReady.value = true;
  });
  window.addEventListener("api-connection-error", onApiError);
  window.addEventListener("api-connection-ok", onApiOk);
  window.addEventListener("mousemove", onActivity);
  window.addEventListener("click", onActivity);
  window.addEventListener("keydown", onActivity);
  if (!isLoginPage.value) startSessionTimers();
});

watch(
  () => route.name,
  (name) => {
    if (name === "login") {
      clearAllTimers();
      showIdleExpiryAlert.value = false;
    } else if (getMsUntilTokenExpiry() !== null) {
      startSessionTimers();
    }
  },
);

onUnmounted(() => {
  window.removeEventListener("api-connection-error", onApiError);
  window.removeEventListener("api-connection-ok", onApiOk);
  window.removeEventListener("mousemove", onActivity);
  window.removeEventListener("click", onActivity);
  window.removeEventListener("keydown", onActivity);
  clearAllTimers();
});

function onNewEntryDone() {
  nextTick(() => {
    showNewEntry.value = false;
    window.dispatchEvent(new CustomEvent("dashboard-refresh"));
  });
}

const POLL_MS = 10_000;

function refreshDashboardEverywhere() {
  window.dispatchEvent(new CustomEvent("dashboard-refresh"));
}

// Bitno: ne radi polling na login strani
const pollingEnabled = computed(
  () => autoRefreshEnabled.value && !isLoginPage.value,
);

const { remainingMs, intervalMs, isRunning } = useDashboardPolling(
  refreshDashboardEverywhere,
  {
    intervalMs: POLL_MS,
    enabled: pollingEnabled,
  },
);
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

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

/* Neon checkbox */
.checkbox-wrapper {
  --checkbox-size: 25px;
  --checkbox-color: #00ff88;
  --checkbox-shadow: rgba(0, 255, 136, 0.3);
  --checkbox-border: rgba(0, 255, 136, 0.7);
  display: flex;
  align-items: center;
  position: relative;
  cursor: pointer;
  padding: 10px;
  margin-inline: 1.5rem;
}

@media (max-width: 639px) {
  .checkbox-wrapper {
    --checkbox-size: 20px;
    padding: 6px;
  }
  .checkbox-wrapper input:checked ~ .checkmark svg {
    width: 14px;
    height: 14px;
  }
  .checkbox-wrapper .label {
    margin-left: 0;
  }
}

.checkbox-wrapper input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkbox-wrapper .checkmark {
  position: relative;
  width: var(--checkbox-size);
  height: var(--checkbox-size);
  border: 2px solid var(--checkbox-border);
  border-radius: 8px;
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.2);
  box-shadow: 0 0 15px var(--checkbox-shadow);
  overflow: hidden;
}

.checkbox-wrapper .checkmark::before {
  content: "";
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(45deg, var(--checkbox-color), #00ffcc);
  opacity: 0;
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  transform: scale(0) rotate(-45deg);
}

.checkbox-wrapper input:checked ~ .checkmark::before {
  opacity: 1;
  transform: scale(1) rotate(0);
}

.checkbox-wrapper .checkmark svg {
  width: 0;
  height: 0;
  color: #1a1a1a;
  z-index: 1;
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  filter: drop-shadow(0 0 2px rgba(0, 0, 0, 0.5));
}

.checkbox-wrapper input:checked ~ .checkmark svg {
  width: 18px;
  height: 18px;
  transform: rotate(360deg);
}

.checkbox-wrapper:hover .checkmark {
  border-color: var(--checkbox-color);
  transform: scale(1.1);
  box-shadow:
    0 0 20px var(--checkbox-shadow),
    0 0 40px var(--checkbox-shadow),
    inset 0 0 10px var(--checkbox-shadow);
}

.checkbox-wrapper input:checked ~ .checkmark {
  animation: pulse 1s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 20px var(--checkbox-shadow);
  }
  50% {
    transform: scale(0.9);
    box-shadow:
      0 0 30px var(--checkbox-shadow),
      0 0 50px var(--checkbox-shadow);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 20px var(--checkbox-shadow);
  }
}

.checkbox-wrapper .label {
  margin-left: 15px;
  font-family: "Segoe UI", sans-serif;
  color: var(--checkbox-color);
  font-size: 18px;
  text-shadow: 0 0 10px var(--checkbox-shadow);
  opacity: 0.9;
  transition: all 0.3s;
}

.checkbox-wrapper:hover .label {
  opacity: 1;
  transform: translateX(5px);
}

/* Glowing dots animation */
.checkbox-wrapper::after,
.checkbox-wrapper::before {
  content: "";
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--checkbox-color);
  opacity: 0;
  transition: all 0.5s;
}

.checkbox-wrapper::before {
  left: -10px;
  top: 50%;
}

.checkbox-wrapper::after {
  right: -10px;
  top: 50%;
}

.checkbox-wrapper:hover::before {
  opacity: 1;
  transform: translateX(-10px);
  box-shadow: 0 0 10px var(--checkbox-color);
}

.checkbox-wrapper:hover::after {
  opacity: 1;
  transform: translateX(10px);
  box-shadow: 0 0 10px var(--checkbox-color);
}

</style>
