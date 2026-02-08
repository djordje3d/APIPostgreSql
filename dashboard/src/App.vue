<template>
  <div class="min-h-screen bg-gray-100">
    <div
      v-if="apiConnectionError"
      class="bg-amber-100 px-4 py-3 text-amber-900 ring-1 ring-amber-300"
      role="alert"
    >
      <p class="font-medium">Cannot connect to API at {{ apiConnectionError }}.</p>
      <p class="mt-1 text-sm">Start the backend from the project root: <code class="rounded bg-amber-200 px-1">python -m app.run</code></p>
    </div>
    <header class="bg-slate-800 text-white shadow">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <nav class="flex items-center gap-4">
          <router-link to="/" class="text-xl font-semibold">Dashboard</router-link>
          <router-link to="/by-garage" class="text-sm text-slate-300 hover:text-white">By garage</router-link>
        </nav>
        <button
          type="button"
          class="rounded bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700"
          @click="showNewEntry = true"
        >
          New Vehicle Entry
        </button>
      </div>
    </header>
    <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <router-view v-slot="{ Component }">
        <component :is="Component" @open-new-entry="showNewEntry = true" />
      </router-view>
    </main>
    <NewVehicleEntryModal v-model="showNewEntry" @done="onNewEntryDone" />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import NewVehicleEntryModal from './components/NewVehicleEntryModal.vue'
import { baseURL } from './api/client'

const showNewEntry = ref(false)
const apiConnectionError = ref<string | null>(null)

function onApiError(e: Event) {
  apiConnectionError.value = (e as CustomEvent).detail?.baseURL ?? baseURL
}
function onApiOk() {
  apiConnectionError.value = null
}

onMounted(() => {
  window.addEventListener('api-connection-error', onApiError)
  window.addEventListener('api-connection-ok', onApiOk)
})
onUnmounted(() => {
  window.removeEventListener('api-connection-error', onApiError)
  window.removeEventListener('api-connection-ok', onApiOk)
})

function onNewEntryDone() {
  nextTick(() => {
    showNewEntry.value = false
    window.dispatchEvent(new CustomEvent('dashboard-refresh'))
  })
}
</script>
