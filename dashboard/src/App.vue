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

const AUTO_REFRESH_STORAGE_KEY = 'dashboard-auto-refresh'

function loadAutoRefreshEnabled(): boolean {
  try {
    const stored = localStorage.getItem(AUTO_REFRESH_STORAGE_KEY)
    return stored !== 'false'
  } catch {
    return true
  }
}

const router = useRouter()
const route = useRoute()
const isLoginPage = computed(() => route.name === 'login')
const showNewEntry = ref(false)
const apiConnectionError = ref<string | null>(null)
const autoRefreshEnabled = ref(loadAutoRefreshEnabled())
let tokenExpiryTimeoutId: ReturnType<typeof setTimeout> | null = null

function logout() {
  clearStoredToken()
  router.push('/login')
}

function scheduleTokenExpiryLogout() {
  const ms = getMsUntilTokenExpiry()
  if (ms === null) return
  if (ms <= 0) {
    clearStoredToken()
    router.push('/login')
    return
  }
  tokenExpiryTimeoutId = setTimeout(() => {
    tokenExpiryTimeoutId = null
    clearStoredToken()
    router.push('/login')
  }, ms)
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
  if (!isLoginPage.value) scheduleTokenExpiryLogout()
})
onUnmounted(() => {
  window.removeEventListener('api-connection-error', onApiError)
  window.removeEventListener('api-connection-ok', onApiOk)
  if (tokenExpiryTimeoutId != null) clearTimeout(tokenExpiryTimeoutId)
})

function onNewEntryDone() {
  nextTick(() => {
    showNewEntry.value = false
    window.dispatchEvent(new CustomEvent('dashboard-refresh'))
  })
}
</script>
