<template>
    <button
      :type="type"
      :disabled="disabled || loading"
      @mousemove="onMove"
      @mouseleave="onLeave"
      class="glow-btn relative overflow-hidden rounded
             bg-emerald-600 py-2 font-medium text-white
             transition-colors duration-200
             hover:bg-emerald-700
             disabled:opacity-50"
      :class="className"
    >
      <!-- Idle shimmer layer (visible only when not hovering and not loading) -->
      <span
        v-if="!hoverGlow && !(disabled || loading)"
        class="pointer-events-none absolute inset-0 shimmer-layer"
      ></span>
  
      <!-- Hover glow layer (your existing directional glow behavior) -->
      <span
        class="pointer-events-none absolute inset-0 transition-opacity duration-150"
        :class="{ 'opacity-100': !!hoverGlow && !(disabled || loading), 'opacity-0': !hoverGlow || (disabled || loading) }"
        :style="hoverGlow || {}"
      ></span>
  
      <!-- Content -->
      <span class="relative z-10">
        <slot />
      </span>
    </button>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue'
  
  const props = defineProps<{
    type?: 'button' | 'submit' | 'reset'
    disabled?: boolean
    loading?: boolean
    className?: string
  }>()
  
  const type = props.type ?? 'button'
  const disabled = props.disabled ?? false
  const loading = props.loading ?? false
  const className = props.className ?? ''
  
  const hoverGlow = ref<Record<string, string> | null>(null)
  
  function onMove(e: MouseEvent) {
    if (disabled || loading) return
  
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
    0% { transform: translateX(-120%); }
    60% { transform: translateX(120%); }
    100% { transform: translateX(120%); }
  }
  </style>