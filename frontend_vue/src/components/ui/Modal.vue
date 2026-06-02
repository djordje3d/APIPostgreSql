<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="modelValue"
        class="modal-backdrop fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        style="pointer-events: auto"
        @click.self="close"
      >
        <div
          class="modal-dialog dashboard-card max-h-[90vh] w-full max-w-md overflow-auto px-6 pt-6 pb-4"
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
            <ButtonIn
              id="cancelBtn"
            label="Cancel"
              variant="outline"
              @userclick="close"
              caption="Cancel"
            />
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="mt-4 border-t border-gray-200 pt-4">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
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

<style scoped>
/* Backdrop: fades in first (0.25s ease-out), fades out after dialog (0.2s ease-in, delayed) */
.modal-fade-enter-active.modal-backdrop {
  transition: opacity 0.3s ease-out;
}
.modal-fade-leave-active.modal-backdrop {
  transition: opacity 0.3s ease-in;
  transition-delay: 0.1s;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

/* Dialog: fades in slightly after backdrop (0.25s ease-out, delayed); fades out first (0.2s ease-in) */
.modal-fade-enter-active .modal-dialog {
  transition: opacity 0.25s ease-out 0.07s;
}
.modal-fade-leave-active .modal-dialog {
  transition: opacity 0.2s ease-in 0s;
}
.modal-fade-enter-from .modal-dialog,
.modal-fade-leave-to .modal-dialog {
  opacity: 0;
}
</style>
