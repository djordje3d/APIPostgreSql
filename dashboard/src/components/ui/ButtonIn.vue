<template>
  <button
    v-bind="restAttrs"
    :id="id"
    :type="type"
    :disabled="isDisabled"
    @click="onClick"
    @mousemove="onMove"
    @mouseleave="onLeave"
    class="btn-in group relative overflow-hidden rounded-lg px-4 py-2 font-medium transition-all duration-200 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
    :class="[variantClasses, attrsClass]"
    :title="caption"
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

    <!-- Content -->
    <span
      class="relative z-10 flex items-center justify-center gap-2"
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

const props = withDefaults(
  defineProps<{
    id: string;
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
    variant?: "primary" | "danger" | "outline" | "default";
    icon?: string;
    label?: string;
    caption?: string;
  }>(),
  {
    type: "button",
    disabled: false,
    variant: "primary",
  },
);

// emit userclick event
// parent component can listen to this event and handle the click event

const emit = defineEmits<{ userclick: [e?: MouseEvent] }>();

const attrs = useAttrs();  // get the attributes of the button
const slots = useSlots();  // get the slots of the button
const hasSlotContent = computed(() => !!slots.default?.());   // check if the button has a slot content

const attrsClass = computed(() => attrs.class);

// split the attributes into class and the rest (avoid duplicating class via v-bind) of the button attributes
const restAttrs = computed(() => {
  const { class: _c, ...rest } = attrs as Record<string, unknown>;
  return rest;
});

const isDisabled = computed(() => props.disabled);

const variantClasses = computed(() => {
  switch (props.variant) {
    case "danger":
      return "bg-red-600 text-white hover:bg-red-700";
    case "outline":
      return "border border-emerald-600 text-emerald-600 bg-transparent hover:bg-emerald-50";
    default:
      return "bg-emerald-600 text-white hover:bg-emerald-700";
  }
});

function onClick(e: MouseEvent) {
  if (isDisabled.value) return;
  emit("userclick", e);
}

// when the mouse is moved over the button, the hover glow style is applied
const hoverGlow = ref<Record<string, string> | null>(null);
 
// Computed where is mouse over the button and apply the hover glow style from that position
function onMove(e: MouseEvent) {
  if (isDisabled.value) return;

  const el = e.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect(); // get the bounding rectangle of the element
  const x = e.clientX - rect.left; // get the x coordinate of the mouse relative to the element
  const y = e.clientY - rect.top; // get the y coordinate of the mouse relative to the element

  // set the hover glow style
  hoverGlow.value = {
    background: `radial-gradient(circle at ${x}px ${y}px,
      rgba(255,255,255,0.35), // set the background color to white with 35% opacity
      transparent 60%)`, // set the background color to transparent with 60% opacity
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
