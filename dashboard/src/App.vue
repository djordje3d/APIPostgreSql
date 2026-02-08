<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-slate-800 text-white shadow">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <nav class="flex items-center gap-4">
          <router-link to="/" class="text-xl font-semibold">Garage Dashboard</router-link>
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
import { ref, nextTick } from 'vue'
import NewVehicleEntryModal from './components/NewVehicleEntryModal.vue'

const showNewEntry = ref(false)

function onNewEntryDone() {
  nextTick(() => {
    showNewEntry.value = false
    window.dispatchEvent(new CustomEvent('dashboard-refresh'))
  })
}
</script>
