<template>
  <Teleport v-if="toast?.message" to="body">
    <div
      class="toast-snackbar"
      role="status"
      aria-live="polite"
    >
      {{ toast.message }}
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { inject } from "vue";
import type { ToastApi } from "../composables/useToast";

const toast = inject<ToastApi>("toast");
</script>

<style scoped>
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
</style>
