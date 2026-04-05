<template>
  <div
    class="countdown"
    :class="{ 'countdown--paused': !autoRefreshEnabled }"
    role="button"
    tabindex="0"
    :aria-label="
      autoRefreshEnabled
        ? t('help.autoRefreshAriaOn')
        : t('help.autoRefreshAriaOff')
    "
    @click="emit('toggle-auto-refresh')"
    @keydown.enter.space.prevent="emit('toggle-auto-refresh')"
  >
    <svg class="countdown__icon" viewBox="0 0 100 100" aria-hidden="true">
      <circle class="countdown__icon__track" cx="50" cy="50" r="42" />
      <circle
        ref="circlePath"
        class="countdown__icon__circle"
        cx="50"
        cy="50"
        r="42"
      />
    </svg>
    <span class="countdown__number">{{ secondsLeft }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const props = defineProps<{
  durationMs: number;
  remainingMs: number;
  enabled?: boolean;
  autoRefreshEnabled: boolean;
}>();

const emit = defineEmits<{ "toggle-auto-refresh": [] }>();

const circlePath = ref<SVGCircleElement | null>(null);
const secondsLeft = computed(() =>
  Math.max(0, Math.ceil(props.remainingMs / 1000)),
);

let length = 0;

function updateRing() {
  if (!circlePath.value || !props.durationMs) return;
  const ratio = Math.max(0, Math.min(1, props.remainingMs / props.durationMs));
  const offset = length * (1 - ratio);
  circlePath.value.style.strokeDashoffset = String(offset);
}

onMounted(() => {
  if (!circlePath.value) return;
  length = circlePath.value.getTotalLength();
  circlePath.value.style.strokeDasharray = String(length);
  circlePath.value.style.strokeDashoffset = "0";
  updateRing();
});

watch(() => props.remainingMs, updateRing);
watch(() => props.autoRefreshEnabled, updateRing);
</script>

<style scoped>
/* Countdown Ring Styles */
.countdown {
  position: relative;
  width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

/* Countdown Icon Styles */
.countdown__icon {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  fill: none;
}

.countdown__icon__track,
.countdown__icon__circle {
  fill: none;
  stroke-width: 9; /* širina tj. debljina prstena koji se smanjuje od punog do praznog prstena */
  /* width of the ring that shrinks from full to empty ring */
}

/* Countdown Track Styles */
.countdown__icon__track {
  stroke: #d1d5db;
}

.countdown__icon__circle {
  stroke: #22c55e;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.5s linear;
  transform: rotate(-90deg) scale(-1,1) rotate(-180deg); /* početak na 12h + smer kazaljke */
  /* rotate(-90deg) → pomera početak sa 3h na 12h , scale(-1,1) → menja smer u kazaljke, rotate(-180deg) → dodatno koriguje da početak ostane na 12h, a ne da se pomeri na 6h. */
  transform-origin: center;
}

/* Countdown Number Styles */
.countdown__number {
  position: relative;
  z-index: 1;
  color: #111827;
  font-weight: 600;
}
</style>
