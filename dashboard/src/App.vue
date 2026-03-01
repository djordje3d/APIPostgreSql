<template>
  <div class="min-h-screen bg-gray-100">
    <div
      v-if="!isLoginPage && apiConnectionError"
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
        v-if="!isLoginPage && showIdleExpiryAlert"
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
    <header v-if="!isLoginPage" class="bg-slate-800 text-white shadow">
      <div
        class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-y-3 gap-x-4 px-4 py-3 sm:px-6"
      >
        <nav class="flex flex-wrap items-center gap-2 sm:gap-4">
          <router-link
            to="/"
            class="text-base font-semibold sm:text-xl"
          >
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
        <div class="flex flex-shrink-0 flex-wrap items-center gap-2 sm:gap-3">
          <button
            type="button"
            class="group/button relative inline-flex items-center justify-center overflow-hidden rounded-md border border-white/20 bg-gray-800/30 px-3 py-2 text-sm font-semibold text-white backdrop-blur-lg transition-all duration-300 ease-in-out hover:scale-110 hover:shadow-xl hover:shadow-gray-600/50 sm:px-6 sm:text-base"
            @click="logout"
          >
            <span class="text-base sm:text-lg">Logout</span>
            <div
              class="absolute inset-0 flex h-full w-full justify-center [transform:skew(-13deg)_translateX(-100%)] group-hover/button:duration-1000 group-hover/button:[transform:skew(-13deg)_translateX(100%)]"
            >
              <div class="relative h-full w-10 bg-white/20"></div>
            </div>
          </button>
          <button
            type="button"
            class="Download-button"
            title="New Vehicle Entry"
            @click="showNewEntry = true"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              height="32"
              width="32"
              viewBox="0 0 32 32"
              class="shrink-0"
              aria-hidden="true"
            >
              <path
                d="M23.371 29.529c0 0 0.335-2.012-1.731-4.469 2.011-5.641 2.29-10.778 2.29-10.778s4.133 0.95 4.133 5.026c-0.001 6.981-4.692 10.221-4.692 10.221zM11.979 27.078c0 0-2.768-8.883-2.768-12.568 0-1.658 0.187-3.133 0.478-4.472h12.61c0.293 1.34 0.481 2.816 0.481 4.473 0 3.629-2.76 12.567-2.76 12.567h-8.041zM15.99 12.069c-1.418 0-2.568 1.15-2.568 2.569 0 1.418 1.15 2.569 2.568 2.569s2.569-1.15 2.569-2.569c0.001-1.419-1.15-2.569-2.569-2.569zM15.438 0.596v-3.498h1v3.409c1.143 0.832 4.236 3.478 5.635 8.575h-12.16c1.352-4.957 4.296-7.574 5.525-8.486zM8.629 29.529c0 0-4.691-3.24-4.691-10.221 0-4.076 4.133-5.026 4.133-5.026s0.279 5.137 2.289 10.778c-2.067 2.458-1.731 4.469-1.731 4.469zM17.691 30.045l-0.838-0.838-0.893 2.793-1.062-2.793-0.726 1.451-1.062-2.625h5.752l-1.171 2.012z"
                fill="white"
              ></path>
            </svg>
            <span class="hidden sm:inline">New Vehicle Entry</span>
          </button>
        </div>
      </div>
    </header>
    <main v-if="!isLoginPage" class="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <router-view v-if="!isLoginPage" v-slot="{ Component }">
        <component :is="Component" @open-new-entry="showNewEntry = true" />
      </router-view>
    </main>
    <NewVehicleEntryModal
      v-if="!isLoginPage"
      v-model="showNewEntry"
      @done="onNewEntryDone"
    />
    <router-view v-if="isLoginPage" />
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
const pollingEnabled = computed(() => autoRefreshEnabled.value && !isLoginPage.value);

const {
  remainingMs,
  intervalMs,
  isRunning,
} = useDashboardPolling(refreshDashboardEverywhere, {
  intervalMs: POLL_MS,
  enabled: pollingEnabled,
});

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

  /* New vehicle entry button styles */
  /* https://uiverse.io/riyaz7us/hard-chipmunk-76 */
  .Download-button {
    display: flex;
    align-items: center;
    font-family: inherit;
    font-weight: 500;
    font-size: 17px;
    padding: 12px 20px;
    color: white;
    background: linear-gradient(144deg, #166534, #169934 50%, #168844);
    border: none;
    box-shadow: 0 0.7em 1.5em -0.5em rgba(59, 78, 48, 0.527);
    letter-spacing: 0.05em;
    border-radius: 8px;
    cursor: pointer;
    position: relative;
    transition: all 0.2s;
  }

  .Download-button svg {
    margin-right: 8px;
    width: 25px;
  }

  @media (max-width: 639px) {
    .Download-button {
      padding: 8px 12px;
      font-size: 14px;
    }
    .Download-button svg {
      margin-right: 0;
      width: 22px;
    }
  }

  .Download-button:hover {
    box-shadow: 0 0.5em 1.5em -0.5em #3b9982;
    border-top-left-radius: 40px;
    border-bottom-right-radius: 40px;
  }

  .Download-button:active {
    box-shadow: 0 0.3em 1em -0.5em #3bf682;
  }

  .Download-button::before {
    content: "";
    width: 4px;
    height: 40%;
    background-color: white;
    position: absolute;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    left: 0;
    transition: all 0.2s;
  }

  .Download-button::after {
    content: "";
    width: 4px;
    height: 40%;
    background-color: white;
    position: absolute;
    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    right: 0;
    transition: all 0.2s;
  }

  .Download-button:hover::before,
  .Download-button:hover::after {
    height: 60%;
  }

  .Download-button:hover::before {
    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    border-top-right-radius: 0px;
    border-bottom-right-radius: 0px;
    transform: translate(5px, -15px) rotate(45deg);
  }

  .Download-button:hover::after {
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    border-top-left-radius: 0px;
    border-bottom-left-radius: 0px;
    transform: translate(-5px, 15px) rotate(45deg);
  }
</style>
