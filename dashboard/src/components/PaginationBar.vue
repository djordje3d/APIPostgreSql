<template>
  <div
    v-if="total > 0"
    class="flex items-center justify-between border-t border-gray-200 px-4 py-3"
  >
    <p class="text-sm text-gray-600">
      Showing {{ start }}–{{ end }} of {{ total }}
    </p>
    <div class="flex items-center gap-2">
      <button
        type="button"
        class="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="page <= 1"
        @click="goPrev"
      >
        Previous
      </button>
      <span class="text-sm text-gray-600">
        Page {{ page }} of {{ totalPages }}
      </span>
      <button
        type="button"
        class="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="page >= totalPages"
        @click="goNext"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  pageSize: number
  total: number
}>()

const emit = defineEmits<{
  'update:page': [value: number]
}>()

const totalPages = computed(() =>
  Math.max(1, Math.ceil(props.total / props.pageSize))
)

const start = computed(() => (props.page - 1) * props.pageSize + 1)

const end = computed(() =>
  Math.min(props.page * props.pageSize, props.total)
)

function goPrev() {
  if (props.page > 1) {
    emit('update:page', props.page - 1)
  }
}

function goNext() {
  if (props.page < totalPages.value) {
    emit('update:page', props.page + 1)
  }
}
</script>
