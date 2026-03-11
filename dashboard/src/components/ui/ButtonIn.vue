<template>
  <button
    v-bind="restAttrs"
    :type="type"
    :disabled="isDisabled"
    @click="onClick"
    @mousemove="onMove"
    @mouseleave="onLeave"
    class="btn-in group relative overflow-hidden rounded-lg px-4 py-2 font-medium transition-all duration-200 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
    :class="[variantClasses, attrsClass]"
    :title="title"
  >
    <!-- Directional hover glow (no idle wave/shimmer) -->
    <span
      class="pointer-events-none absolute inset-0 transition-opacity duration-150"
      :class="{
        'opacity-100': !!hoverGlow && !isDisabled,
        'opacity-0': !hoverGlow || isDisabled,
      }"
      :style="hoverGlow || {}"
    />

    <!-- Loading spinner -->
    <span
      v-if="loading"
      class="absolute inset-0 flex items-center justify-center"
    >
      <span
        class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
      />
    </span>

    <!-- Content -->
    <span
      class="relative z-10 flex items-center justify-center gap-2"
      :class="{ 'opacity-0': loading }"
    >
      <slot v-if="hasSlotContent" />
      <template v-else-if="label">{{ label }}</template>
    </span>
    <span v-if="typeof icon !== 'undefined'" :class="icon"></span>
  </button>
</template>

<script setup lang="ts">
import { computed, ref, useAttrs, useSlots } from "vue";

defineOptions({
  inheritAttrs: false,
});

const props = defineProps<{
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  loading?: boolean;
  variant?: "primary" | "danger" | "outline" | "logout";
  icon?: string;
  label?: string;
  title?: string;
}>();

const emit = defineEmits<{ click: [e?: MouseEvent] }>();

const attrs = useAttrs();
const slots = useSlots();
const hasSlotContent = computed(() => !!slots.default?.());

const attrsClass = computed(() => attrs.class);
const restAttrs = computed(() => {
  const { class: _c, ...rest } = attrs as Record<string, unknown>;
  return rest;
});

const type = computed(() => props.type ?? "button");
const loading = computed(() => props.loading ?? false);
const disabled = computed(() => props.disabled ?? false);
const variant = computed(() => props.variant ?? "primary");
const icon = computed(() => props.icon ?? undefined);
const label = computed(() => props.label ?? undefined);
const title = computed(() => props.title ?? undefined);

const isDisabled = computed(() => disabled.value || loading.value);

const variantClasses = computed(() => {
  switch (variant.value) {
    case "danger":
      return "bg-red-600 text-white hover:bg-red-700";
    case "outline":
      return "border border-emerald-600 text-emerald-600 bg-transparent hover:bg-emerald-50";
    case "logout":
      return "border-white/20 bg-gray-800/30 px-3 py-2 text-sm font-semibold text-white backdrop-blur-lg transition-all duration-300 ease-in-out hover:scale-110 hover:shadow-xl hover:border-emerald-400/40 hover:bg-gray-600/80 sm:px-6 sm:text-base";
    default:
      return "bg-emerald-600 text-white hover:bg-emerald-700";
  }
});

const hoverGlow = ref<Record<string, string> | null>(null);

function onClick(e: MouseEvent) {
  if (isDisabled.value) return;
  emit("click", e);
}

function onMove(e: MouseEvent) {
  if (isDisabled.value) return;

  const el = e.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  hoverGlow.value = {
    background: `radial-gradient(circle at ${x}px ${y}px,
      rgba(255,255,255,0.35),
      transparent 60%)`,
  };
}

function onLeave() {
  hoverGlow.value = null;
}
</script>

<style scoped>
.btn-in {
  position: relative;
}
</style>
