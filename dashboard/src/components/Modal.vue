<template>
  <Teleport to="body"> <!-- Teleport to the body to avoid z-index issues -->
    <div
      v-if="modelValue"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      style="pointer-events: auto"
      @click.self="close"
    >
      <div
        class="max-h-[90vh] w-full max-w-md overflow-auto rounded-lg bg-white p-6 shadow-xl"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="title ? 'modal-title' : undefined"
      >
        <div v-if="title" class="mb-4 flex items-center justify-between">
          <h2
            :id="title ? 'modal-title' : undefined"
            class="text-lg font-semibold text-gray-900"
          >
            {{ title }}
          </h2>
          <button
            type="button"
            class="text-gray-500 hover:text-gray-700"
            aria-label="Close"
            @click="close"
          >
            &times;
          </button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
        <div v-if="$slots.footer" class="mt-4 border-t border-gray-200 pt-4">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: boolean;
  title?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
}>();

function close() {
  emit("update:modelValue", false);
}
</script>
