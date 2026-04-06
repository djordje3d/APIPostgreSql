<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Global connection banner: offline or API down -->
    <Transition name="banner-slide">
      <div
        v-if="routerReady && !isLoginPage && connectionBannerMessage"
        class="connection-banner"
        :class="connectionBannerVariant"
        role="alert"
        aria-live="assertive"
      >
        <span class="connection-banner__icon" aria-hidden="true">{{
          connectionBannerIcon
        }}</span>
        <div class="connection-banner__content">
          <p class="connection-banner__title">{{ connectionBannerMessage }}</p>
          <p v-if="connectionBannerDetail" class="connection-banner__detail">
            {{ connectionBannerDetail }}
          </p>
        </div>
      </div>
    </Transition>
    
    <!-- Brief "Connection restored" toast -->
    <Teleport to="body">
      <Transition name="toast-fade">
        <div
          v-if="connectionRestoredToast"
          class="connection-restored-toast"
          role="status"
          aria-live="polite"
        >
          <span class="connection-restored-toast__icon" aria-hidden="true"
            >✓</span
          >
          {{ t("connection.restored") }}
        </div>
      </Transition>
    </Teleport>

    <!-- Snackbar toast: only on dashboard and only when entry is created -->
    <Teleport to="body">
      <Transition name="toast-snackbar-fade">
        <div
          v-if="!isLoginPage && toastMessage.trim()"
          class="toast-snackbar"
          role="status"
          aria-live="polite"
        >
          {{ toastMessage }}
        </div>
      </Transition>
    </Teleport>

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
            {{
              t("session.idle.title", { countdown: sessionExpiryCountdown })
            }}
          </p>
          <p class="mt-1 text-sm opacity-90">
            {{ t("session.idle.detail") }}
          </p>
          <ButtonIn
            id="extendSessionBtn"
            type="button"
            variant="primary"
            class="mt-4 shrink-0 !bg-amber-600 hover:!bg-amber-700 focus:ring-amber-500"
            @userclick="extendSession"
          >
            {{ t("session.idle.continue") }}
          </ButtonIn>
        </div>
      </div>
    </Teleport>

    <!-- Session expired (401): shown when API returns unauthorized, then redirect to login. -->
    <Teleport to="body">
      <div
        v-if="!isLoginPage && showSessionExpiredModal"
        class="session-expiry-overlay"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="session-expired-title"
      >
        <div class="session-expired-modal">
          <p id="session-expired-title" class="font-medium">
            {{ t("session.expired.title") }}
          </p>
          <p class="mt-1 text-sm opacity-90">
            {{
              t("session.expired.detail", {
                countdown: sessionExpiredRedirectCountdown,
              })
            }}
          </p>
          <ButtonIn
            id="sessionExpiredLoginBtn"
            type="button"
            variant="primary"
            class="mt-4 shrink-0 !bg-slate-700 hover:!bg-slate-800 focus:ring-slate-500"
            @userclick="goToLoginAfterExpired"
          >
            {{ t("session.expired.goToLogin") }}
          </ButtonIn>
        </div>
      </div>
    </Teleport>

    <!-- Dashboard content -->
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
              <router-link
                :to="{ name: 'dashboard' }"
                class="text-base font-semibold sm:text-xl"
              >
                {{ t("header.dashboard") }}
              </router-link>
              <LanguageSwitcher />
            </nav>
            <div
              class="flex flex-shrink-0 flex-wrap items-center gap-2 sm:gap-3"
            >

              <ButtonIn
                id="logoutBtn"
                variant="outline"
                :label="t('header.logout')"
                @userclick="logout"
                :caption="t('header.logout')"
              />
              <ButtonIn
                id="newVehicleEntryBtn"
                variant="primary"
                :label="t('header.newVehicleEntry')"
                @userclick="showNewEntry = true"
                :caption="t('header.newVehicleEntry')"
              />
            </div>
          </div>
        </header>
        <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6">
          <router-view v-slot="{ Component }">
            <Transition name="fade" mode="out-in">
              <component
                :is="Component"
                :key="$route.fullPath"
                @open-new-entry="showNewEntry = true"
              />
            </Transition>
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
import NewVehicleEntryModal from "./components/dashboard/NewVehicleEntryModal.vue";
import { useToast } from "./composables/useToast";
import { baseURL } from "./api/client";
import { clearStoredToken, getMsUntilTokenExpiry } from "./api/auth-storage";
import { clearGaragesCache } from "./utils/garageCache";
import { refresh as refreshToken } from "./api/auth";
import { useDashboardPolling } from "./composables/useDashboardPolling";
import ButtonIn from "./components/ui/ButtonIn.vue";
import LanguageSwitcher from "./components/ui/LanguageSwitcher.vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

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
const isDashboard = computed(() => route.name === "dashboard");
const sessionExpiryCountdown = computed(() => idleExpiryCountdown.value);
const showNewEntry = ref(false);
const toast = useToast();
const { message: toastMessage, showToast, clearToast } = useToast();

provide("toast", {
  message: toastMessage,
  showToast,
  clearToast,
});

watch(showNewEntry, (open) => {
  if (open) clearToast();
});
const apiConnectionError = ref<string | null>(null);
const apiConnectionTimeout = ref<string | null>(null);
const isOffline = ref(typeof navigator !== "undefined" && !navigator.onLine);
const connectionRestoredToast = ref(false);
let connectionRestoredToastId: ReturnType<typeof setTimeout> | null = null;
const autoRefreshEnabled = ref(loadAutoRefreshEnabled());
const showIdleExpiryAlert = ref(false);
const idleExpiryCountdown = ref("");
const showSessionExpiredModal = ref(false);
const sessionExpiredRedirectCountdown = ref("3");
let sessionExpiredRedirectTimeoutId: ReturnType<typeof setTimeout> | null =
  null;
let sessionExpiredCountdownIntervalId: ReturnType<typeof setInterval> | null =
  null;
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
  clearGaragesCache();
  clearStoredToken();
  router.push("/login");
}

const SESSION_EXPIRED_REDIRECT_MS = 3000;

function goToLoginAfterExpired() {
  if (sessionExpiredRedirectTimeoutId != null) {
    clearTimeout(sessionExpiredRedirectTimeoutId);
    sessionExpiredRedirectTimeoutId = null;
  }
  if (sessionExpiredCountdownIntervalId != null) {
    clearInterval(sessionExpiredCountdownIntervalId);
    sessionExpiredCountdownIntervalId = null;
  }
  showSessionExpiredModal.value = false;
  clearGaragesCache();
  clearStoredToken();
  router.push({ path: "/login", query: { reason: "expired" } });
}

/** Show "session expired" modal and redirect after countdown. Token is cleared only on redirect so the guard does not send user to login before the modal is seen. */
function onSessionExpired() {
  if (showSessionExpiredModal.value) return;
  showSessionExpiredModal.value = true;
  let remainingMs = SESSION_EXPIRED_REDIRECT_MS;
  sessionExpiredRedirectCountdown.value = String(Math.ceil(remainingMs / 1000));
  sessionExpiredCountdownIntervalId = setInterval(() => {
    remainingMs -= 1000;
    sessionExpiredRedirectCountdown.value = String(
      Math.max(0, Math.ceil(remainingMs / 1000)),
    );
    if (remainingMs <= 0 && sessionExpiredCountdownIntervalId != null) {
      clearInterval(sessionExpiredCountdownIntervalId);
      sessionExpiredCountdownIntervalId = null;
    }
  }, 1000);
  sessionExpiredRedirectTimeoutId = setTimeout(() => {
    sessionExpiredRedirectTimeoutId = null;
    if (sessionExpiredCountdownIntervalId != null) {
      clearInterval(sessionExpiredCountdownIntervalId);
      sessionExpiredCountdownIntervalId = null;
    }
    showSessionExpiredModal.value = false;
    clearGaragesCache();
    clearStoredToken();
    router.push({ path: "/login", query: { reason: "expired" } });
  }, SESSION_EXPIRED_REDIRECT_MS);
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

// Don't update on login page
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

// Don't update on login page
function onActivity() {
  const now = Date.now();
  if (now - lastActivityAt < IDLE_ACTIVITY_THROTTLE_MS) return;
  lastActivityAt = now;
  if (isLoginPage.value || getMsUntilTokenExpiry() === null) return;
  resetIdleTimer();
}

// Don't update on login page
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

// Don't update on login page — when token expires, show session-expired modal then redirect (same as 401 path).
function scheduleTokenExpiryLogout() {
  clearSessionTimers();
  const ms = getMsUntilTokenExpiry();
  if (ms === null) return;
  if (ms <= 0) {
    onSessionExpired();
    return;
  }
  tokenExpiryTimeoutId = setTimeout(() => {
    tokenExpiryTimeoutId = null;
    if (idleCountdownIntervalId != null) {
      clearInterval(idleCountdownIntervalId);
      idleCountdownIntervalId = null;
    }
    onSessionExpired();
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

function showConnectionRestoredToast() {
  if (connectionRestoredToastId != null) {
    clearTimeout(connectionRestoredToastId);
    connectionRestoredToastId = null;
  }
  connectionRestoredToast.value = true;
  connectionRestoredToastId = setTimeout(() => {
    connectionRestoredToast.value = false;
    connectionRestoredToastId = null;
  }, 3000);
}

function onApiError(e: Event) {
  apiConnectionError.value = (e as CustomEvent).detail?.baseURL ?? baseURL;
}
function onApiTimeout(e: Event) {
  apiConnectionTimeout.value = (e as CustomEvent).detail?.baseURL ?? baseURL;
}
function onApiOk() {
  const hadError =
    apiConnectionError.value != null || apiConnectionTimeout.value != null;
  apiConnectionError.value = null;
  apiConnectionTimeout.value = null;
  if (hadError && !isLoginPage.value) showConnectionRestoredToast();
}

function onBrowserOffline() {
  isOffline.value = true;
}
function onBrowserOnline() {
  const hadOfflineBanner = !isLoginPage.value && isOffline.value;
  isOffline.value = false;
  if (hadOfflineBanner) showConnectionRestoredToast();
}

onMounted(() => {
  router.isReady().then(() => {
    routerReady.value = true;
  });
  window.addEventListener("api-connection-error", onApiError);
  window.addEventListener("api-connection-timeout", onApiTimeout);
  window.addEventListener("api-connection-ok", onApiOk);
  window.addEventListener("offline", onBrowserOffline);
  window.addEventListener("online", onBrowserOnline);
  window.addEventListener("mousemove", onActivity);
  window.addEventListener("click", onActivity);
  window.addEventListener("keydown", onActivity);
  window.addEventListener("session-expired", onSessionExpired);
  if (!isLoginPage.value) startSessionTimers();
});

watch(
  () => route.name,
  (name) => {
    if (name === "login") {
      clearAllTimers();
      showIdleExpiryAlert.value = false;
      showSessionExpiredModal.value = false;
    } else if (getMsUntilTokenExpiry() !== null) {
      startSessionTimers();
    }
  },
);

onUnmounted(() => {
  window.removeEventListener("api-connection-error", onApiError);
  window.removeEventListener("api-connection-timeout", onApiTimeout);
  window.removeEventListener("api-connection-ok", onApiOk);
  window.removeEventListener("offline", onBrowserOffline);
  window.removeEventListener("online", onBrowserOnline);
  window.removeEventListener("mousemove", onActivity);
  window.removeEventListener("click", onActivity);
  window.removeEventListener("keydown", onActivity);
  window.removeEventListener("session-expired", onSessionExpired);
  if (connectionRestoredToastId != null) {
    clearTimeout(connectionRestoredToastId);
  }
  if (sessionExpiredRedirectTimeoutId != null) {
    clearTimeout(sessionExpiredRedirectTimeoutId);
  }
  if (sessionExpiredCountdownIntervalId != null) {
    clearInterval(sessionExpiredCountdownIntervalId);
  }
  clearAllTimers();
});

function onNewEntryDone() {
  nextTick(() => { // wait for the DOM to be updated
    showNewEntry.value = false;
    showToast("Vehicle entry created.");
    window.dispatchEvent(new CustomEvent("dashboard-refresh"));
  });
}

const POLL_MS = 10_000;

function refreshDashboardEverywhere() {
  window.dispatchEvent(new CustomEvent("dashboard-refresh"));
}

// Don't update on login page
const pollingEnabled = computed(
  () => autoRefreshEnabled.value && !isLoginPage.value,
);

/** Message for the global connection banner (offline, timeout, or API down). */
const connectionBannerMessage = computed(() => {
  if (isOffline.value) return t("connection.offline.title");
  if (apiConnectionTimeout.value) return t("connection.timeout.title");
  if (apiConnectionError.value) return t("connection.apiDown.title");
  return null;
});
const connectionBannerDetail = computed(() => {
  if (isOffline.value) return t("connection.offline.detail");
  if (apiConnectionTimeout.value) {
    return t("connection.timeout.detail");
  }
  if (apiConnectionError.value && apiConnectionError.value.length) {
    return t("connection.apiDown.detail", {
      baseURL: apiConnectionError.value,
    });
  }
  return null;
});
const connectionBannerVariant = computed(() => {
  if (isOffline.value) return "connection-banner--offline";
  if (apiConnectionTimeout.value) return "connection-banner--timeout";
  return "connection-banner--api-down";
});
const connectionBannerIcon = computed(() => {
  if (isOffline.value) return "📡";
  if (apiConnectionTimeout.value) return "⏱";
  return "⚠";
});

// Don't update on login page
// This is the polling that refreshes the dashboard every ?? seconds
useDashboardPolling(refreshDashboardEverywhere, {
  intervalMs: POLL_MS,
  enabled: pollingEnabled,
});
</script>

<style scoped>
/* Connection banner (offline / API down) */
.connection-banner {
  position: sticky;
  top: 0;
  z-index: 1000;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem 1rem 0.75rem 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
.connection-banner__icon {
  font-size: 1.25rem;
  line-height: 1;
  flex-shrink: 0;
}
.connection-banner__content {
  flex: 1;
  min-width: 0;
}
.connection-banner__title {
  font-weight: 600;
  font-size: 0.9375rem;
}
.connection-banner__detail {
  margin-top: 0.25rem;
  font-size: 0.8125rem;
  opacity: 0.95;
}
.connection-banner--offline {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  color: #e2e8f0;
}
.connection-banner--offline .connection-banner__detail {
  color: #94a3b8;
}
.connection-banner--timeout {
  background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
  color: #eff6ff;
}
.connection-banner--timeout .connection-banner__detail {
  color: #bfdbfe;
}
.connection-banner--api-down {
  background: linear-gradient(135deg, #b45309 0%, #d97706 100%);
  color: #1c1917;
}
.connection-banner--api-down .connection-banner__detail {
  color: rgba(28, 25, 23, 0.9);
}


.banner-slide-enter-active,
.banner-slide-leave-active {
  transition:
    transform 0.25s ease-out,
    opacity 0.25s ease-out;
}
.banner-slide-enter-from,
.banner-slide-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

/* This is the toast that appears when the connection is restored*/
.connection-restored-toast {
  position: fixed;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10001;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: #065f46;
  color: #ecfdf5;
  font-weight: 500;
  font-size: 0.875rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
}
.connection-restored-toast__icon {
  font-size: 1rem;
  color: #6ee7b7;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-0.5rem);
}

/* Entry-created snackbar (bottom-right), only in DOM when message is set */
.toast-snackbar {
  position: fixed;
  bottom: 1.25rem;
  right: 1.25rem;
  z-index: 10001;
  padding: 0.75rem 1.25rem;
  background: #065f46;
  color: #ecfdf5;
  font-weight: 500;
  font-size: 0.875rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
  max-width: min(22rem, calc(100vw - 2.5rem));
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* This is the overlay that appears when the session is expired */
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
.session-expired-modal {
  pointer-events: auto;
  max-width: 24rem;
  padding: 1.5rem;
  background: rgb(51 65 85); /* slate-700 */
  color: rgb(248 250 252); /* slate-50 */
  border-radius: 0.5rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.toast-snackbar-fade-enter-active,
.toast-snackbar-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.toast-snackbar-fade-enter-from,
.toast-snackbar-fade-leave-to {
  opacity: 0;
  transform: translateY(0.5rem);
}
</style>
