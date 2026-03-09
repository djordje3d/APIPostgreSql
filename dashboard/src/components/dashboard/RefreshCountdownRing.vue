<template>
    <div
      class="countdown"
      :class="{ 'countdown--paused': !autoRefreshEnabled }"
      role="button"
      tabindex="0"
      title="Click to toggle auto refresh"
      @click="emit('toggle-auto-refresh')"
      @keydown.enter.space.prevent="emit('toggle-auto-refresh')"
    >
      <span class="countdown__number">{{ secondsLeft }}</span>

      <svg class="countdown__icon" viewBox="0 0 130 130">
        <path
          ref="circlePath"
          class="countdown__icon__circle"
          d="M5,64.8a59.8,59.8 0 1,0 119.6,0a59.8,59.8 0 1,0 -119.6,0"
        />
      </svg>
    </div>
  </template>

  <script setup lang="ts">
  import { computed, onMounted, ref, watch } from "vue";

  const props = defineProps<{
    durationMs: number;
    remainingMs: number;
    enabled?: boolean;
    autoRefreshEnabled: boolean;
  }>();

  const emit = defineEmits<{
    "toggle-auto-refresh": [];
  }>();
  
  const circlePath = ref<SVGPathElement | null>(null);
  const secondsLeft = computed(() => Math.ceil(props.remainingMs / 1000));
  
  let length = 0;
  
  function updateRing() {
    if (!circlePath.value) return;
  
    const ratio = Math.max(0, Math.min(1, props.remainingMs / props.durationMs));
    circlePath.value.style.strokeDashoffset = String(length * (1 - ratio));
  }
  
  onMounted(() => {
    if (!circlePath.value) return;
    length = circlePath.value.getTotalLength();
    circlePath.value.style.strokeDasharray = String(length);
    updateRing();
  });
  
  watch(
    () => props.remainingMs,
    () => {
      updateRing();
    },
  );
  </script>
  
  <style scoped>
  
  /* https://codepen.io/kly/pen/eYyPNEY */
  /* Countdown Styles */
  .countdown {
    position: relative;
    width: 58px;
    height: 58px;
    border-radius: 50%;
    background: transparent;
    border: 3px solid grey;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: opacity 0.2s, border-color 0.2s;
  }
  .countdown:hover {
    opacity: 0.9;
  }
  .countdown--paused {
    opacity: 0.6;
    border-color: #555;
  }
  .countdown--paused .countdown__icon__circle {
    stroke: #666;
  }
  /* Countdown Icon Styles */
  .countdown__icon {
    position: absolute;
    top: -6px;
    left: -6px;
    width: 64px;
    fill: none;
    stroke-width: 10px;
    stroke-linecap: round;
    transform: rotate(90deg);
    transform-origin: center;
  }
  /* Countdown Icon Circle Styles */
  .countdown__icon__circle {
    stroke: #76e19e;
    transition: stroke-dashoffset 0.25s linear;
  }
  .countdown__number {
    color: black;
    font-weight: 600;
  }
  </style>