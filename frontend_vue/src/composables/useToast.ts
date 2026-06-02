import { ref } from "vue";

const DEFAULT_DURATION_MS = 4000;

export function useToast() {
  const message = ref("");

  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  function showToast(msg: string, durationMs = DEFAULT_DURATION_MS) {
    const normalized = msg.trim();

    if (timeoutId != null) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }

    if (!normalized) {
      message.value = "";
      return;
    }

    message.value = normalized;

    timeoutId = setTimeout(() => {
      message.value = "";
      timeoutId = null;
    }, durationMs);
  }

  function clearToast() {
    if (timeoutId != null) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    message.value = "";
  }

  return { message, showToast, clearToast };
}

export type ToastApi = ReturnType<typeof useToast>;