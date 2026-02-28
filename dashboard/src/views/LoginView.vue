<template>
  <div class="login-screen">
    <div
      class="login-content flex min-h-screen items-center justify-center bg-gray-100"
    >
      <div class="w-full max-w-sm rounded-lg bg-white px-6 py-8 shadow-md">
        <h1 class="mb-6 text-center text-xl font-semibold text-slate-800">
          Dashboard Login
        </h1>

        <form @submit.prevent="onSubmit" class="space-y-4">
          <div>
            <label
              for="username"
              class="mb-1 block text-sm font-medium text-slate-700"
            >
              Username
            </label>
            <input
              id="username"
              v-model="username"
              type="text"
              required
              autocomplete="username"
              class="w-full rounded border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <div>
            <label
              for="password"
              class="mb-1 block text-sm font-medium text-slate-700"
            >
              Password
            </label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              class="w-full rounded border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

          <!-- ✅ Shimmer (idle) + Directional glow (hover) -->
          <GlowButton type="submit" :loading="loading" className="w-full">
            {{ loading ? "Signing in…" : "Sign in" }}
          </GlowButton>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { login } from "../api/auth";
import GlowButton from "../components/GlowButton.vue";

const router = useRouter();
const route = useRoute();

const username = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function onSubmit() {
  error.value = "";
  loading.value = true;

  try {
    await login(username.value, password.value);
    const redirect = (route.query.redirect as string) || "/";
    await router.push(redirect);
  } catch (e: unknown) {
    const msg =
      e && typeof e === "object" && "response" in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data
            ?.detail
        : null;

    error.value = msg || "Login failed. Check username and password.";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* Full-screen: whole background + login form zoom+fade as one */
.login-screen {
  min-height: 100vh;
  width: 100%;
  background: white;
  transform: scale(0.94);
  animation: loginFadeIn 2.3s ease-out forwards;
}

.login-content {
  min-height: 100vh;
}

@keyframes loginFadeIn {
  from {
    opacity: 0;
    transform: scale(0.94);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Button container */
.shimmer-btn {
  position: relative;
}

/* Slow, subtle shimmer that runs while idle */
.shimmer-layer {
  background: linear-gradient(
    120deg,
    transparent 0%,
    rgba(255, 255, 255, 0.35) 45%,
    rgba(255, 255, 255, 0.55) 50%,
    rgba(255, 255, 255, 0.35) 55%,
    transparent 100%
  );
  transform: translateX(-120%);
  animation: shimmer 3.5s ease-in-out infinite;
  opacity: 0.35;
}

@keyframes shimmer {
  0% {
    transform: translateX(-120%);
  }
  60% {
    transform: translateX(120%);
  }
  100% {
    transform: translateX(120%);
  }
}
</style>
