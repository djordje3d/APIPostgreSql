<template>
  <div class="login-screen">
    <!-- Background layer (animated) -->
    <div class="bg-layer" aria-hidden="true"></div>

    <!-- Content -->
    <div
      class="login-content flex min-h-screen items-center justify-center px-4"
    >
      <div class="card dashboard-card w-full max-w-sm px-6 py-8">
        <h1 class="mb-6 text-center text-xl font-semibold text-slate-800">
          {{ t("login.title") }}
        </h1>

        <p
          v-if="sessionExpiredMessage"
          class="mb-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800"
          role="status"
        >
          {{ sessionExpiredMessage }}
        </p>

        <form @submit.prevent="onSubmit" class="space-y-4">
          <InputIn
            id="username"
            v-model="username"
            :label="t('login.username')"
            type="text"
            required
            autocomplete="username"
          />
          <InputIn
            id="password"
            v-model="password"
            :label="t('login.password')"
            type="password"
            required
            autocomplete="current-password"
          />
          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
          <ButtonIn
            id="signInBtn"
            :label="t('login.signIn')"
            variant="primary"
            type="submit"
            :disabled="!canSubmit || isSubmitting"
            :caption="t('login.signIn')"
            class="w-full"
          />
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { login } from "../api/auth";
import { parseApiError } from "../api/error";
import ButtonIn from "../components/ui/ButtonIn.vue";
import InputIn from "../components/ui/InputIn.vue";
import { useI18n } from "vue-i18n";

const router = useRouter();
const route = useRoute();
const { t } = useI18n();

const username = ref("");
const password = ref("");
const error = ref("");
const isSubmitting = ref(false);

const sessionExpiredMessage = computed(() =>
  route.query.reason === "expired" ? t("login.sessionExpired") : "",
);

const canSubmit = computed(() => {
  return username.value.trim().length > 0 && password.value.trim().length > 0;
});

async function onSubmit() {
  if (!canSubmit.value || isSubmitting.value) return;

  error.value = "";
  isSubmitting.value = true;

  try {
    await login(username.value, password.value);
    const redirect = (route.query.redirect as string) || "/dashboard";
    await router.push(redirect);
  } catch (e: unknown) {
    error.value = parseApiError(
      e,
      "Login failed. Check username and password.",
    ).message;
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
/* Whole page container */
.login-screen {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

/* Animated background (this is what makes it feel "intro") */
.bg-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;

  /* final look */
  background:
    radial-gradient(
      900px 500px at 20% 15%,
      rgba(16, 185, 129, 0.16),
      transparent 60%
    ),
    radial-gradient(
      900px 500px at 80% 85%,
      rgba(59, 130, 246, 0.12),
      transparent 60%
    ),
    linear-gradient(to bottom, #f8fafc, #f1f5f9);

  opacity: 0;
  transform: scale(1.03);
  filter: blur(6px);
  animation: bgIn 650ms ease-out forwards;
}

/* Content appears above background */
.login-content {
  position: relative;
  z-index: 1;
}

/* Card intro (separate animation: pop in) */
.card {
  opacity: 0;
  transform: translateY(10px) scale(0.985);
  filter: blur(4px);
  animation: cardIn 620ms ease-out forwards;
  animation-delay: 120ms;
}

/* Background intro */
@keyframes bgIn {
  from {
    opacity: 0;
    transform: scale(1.03);
    filter: blur(10px);
  }
  to {
    opacity: 1;
    transform: scale(1);
    filter: blur(0px);
  }
}

/* Card intro */
@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.985);
    filter: blur(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0px);
  }
}

/* Accessibility: respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  .bg-layer,
  .card {
    animation: none;
    opacity: 1;
    transform: none;
    filter: none;
  }
}
</style>
