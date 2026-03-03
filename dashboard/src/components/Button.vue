<template>
    <button
      v-bind="restAttrs"
      :type="type"
      :disabled="isDisabled"
      @mousemove="onMove"
      @mouseleave="onLeave"
      class="glow-btn group relative overflow-hidden rounded-lg px-4 py-2 font-medium transition-all duration-200 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
      :class="[variantClasses, attrsClass]"
    >
      <!-- Idle shimmer -->
      <span
        v-if="!hoverGlow && !isDisabled"
        class="pointer-events-none absolute inset-0 shimmer-layer"
      />
  
      <!-- Directional hover glow -->
      <span
        class="pointer-events-none absolute inset-0 transition-opacity duration-150"
        :class="{
          'opacity-100': !!hoverGlow && !isDisabled,
          'opacity-0': !hoverGlow || isDisabled,
        }"
        :style="hoverGlow || {}"
      />
  
      <!-- Loading spinner -->
      <span v-if="loading" class="absolute inset-0 flex items-center justify-center">
        <span
          class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
        />
      </span>
  
      <!-- Content -->
      <span
        class="relative z-10 flex items-center justify-center gap-2"
        :class="{ 'opacity-0': loading }"
      >
        <slot />
      </span>
    </button>
  </template>
  
  <script setup lang="ts">
  import { computed, ref, useAttrs } from "vue"
  
  defineOptions({
    inheritAttrs: false,
  })
  
  const props = defineProps<{
    type?: "button" | "submit" | "reset"
    disabled?: boolean
    loading?: boolean
    variant?: "primary" | "danger" | "outline"
  }>()
  
  const attrs = useAttrs()
  
  // Split attrs into class and the rest (avoid duplicating class via v-bind)
  const attrsClass = computed(() => attrs.class)
  const restAttrs = computed(() => {
    const { class: _c, ...rest } = attrs as Record<string, unknown>
    return rest
  })
  
  const type = computed(() => props.type ?? "button")
  const loading = computed(() => props.loading ?? false)
  const disabled = computed(() => props.disabled ?? false)
  const variant = computed(() => props.variant ?? "primary")
  
  const isDisabled = computed(() => disabled.value || loading.value)
  
  const variantClasses = computed(() => {
    switch (variant.value) {
      case "danger":
        return "bg-red-600 text-white hover:bg-red-700"
      case "outline":
        return "border border-emerald-600 text-emerald-600 bg-transparent hover:bg-emerald-50"
      default:
        return "bg-emerald-600 text-white hover:bg-emerald-700"
    }
  })
  
  const hoverGlow = ref<Record<string, string> | null>(null)
  
  function onMove(e: MouseEvent) {
    if (isDisabled.value) return
  
    const el = e.currentTarget as HTMLElement
    const rect = el.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
  
    hoverGlow.value = {
      background: `radial-gradient(circle at ${x}px ${y}px,
        rgba(255,255,255,0.35),
        transparent 60%)`,
    }
  }
  
  function onLeave() {
    hoverGlow.value = null
  }
  </script>
  
  <style scoped>
  .glow-btn {
    position: relative;
  }
  
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