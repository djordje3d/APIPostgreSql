<template>
  <div class="login-screen">
    <!-- Background layer (animated) -->
    <div class="bg-layer" aria-hidden="true"></div>

    <!-- Content -->
    <div class="login-content flex min-h-screen items-center justify-center px-4">
      <div class="card w-full max-w-sm rounded-lg bg-white px-6 py-8 shadow-md">
        <h1 class="mb-6 text-center text-xl font-semibold text-slate-800">
          Dashboard Login
        </h1>

        <form @submit.prevent="onSubmit" class="space-y-4">
          <div>
            <label for="username" class="mb-1 block text-sm font-medium text-slate-700">
              Username
            </label>
            <input
              id="username"
              v-model="username"
              type="text"
              required
              autocomplete="username"
              class="w-full rounded border border-slate-300 px-3 py-2
                     focus:border-emerald-500 focus:outline-none focus:ring-1
                     focus:ring-emerald-500"
            />
          </div>

          <div>
            <label for="password" class="mb-1 block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              class="w-full rounded border border-slate-300 px-3 py-2
                     focus:border-emerald-500 focus:outline-none focus:ring-1
                     focus:ring-emerald-500"
            />
          </div>

          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

          <GlowButton type="submit" :loading="loading" className="w-full">
            {{ loading ? "Signing in…" : "Sign in" }}
          </GlowButton>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { useRouter, useRoute } from "vue-router"
import { login } from "../api/auth"
import GlowButton from "../components/GlowButton.vue"

const router = useRouter()
const route = useRoute()

const username = ref("")
const password = ref("")
const error = ref("")
const loading = ref(false)

async function onSubmit() {
  error.value = ""
  loading.value = true

  try {
    await login(username.value, password.value)
    const redirect = (route.query.redirect as string) || "/"
    await router.push(redirect)
  } catch (e: unknown) {
    const msg =
      e && typeof e === "object" && "response" in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : null

    error.value = msg || "Login failed. Check username and password."
  } finally {
    loading.value = false
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

  /* final look */
  background:
    radial-gradient(900px 500px at 20% 15%, rgba(16, 185, 129, 0.16), transparent 60%),
    radial-gradient(900px 500px at 80% 85%, rgba(59, 130, 246, 0.12), transparent 60%),
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