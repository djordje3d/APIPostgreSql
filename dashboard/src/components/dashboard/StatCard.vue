<template>
  <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
    <div class="flex items-center gap-3">
      <!-- ICON BADGE -->
      <span
        class="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-600"
        aria-hidden="true"
      >
        <span :class="`icon-${icon}`" class="text-lg"></span>
      </span>

      <!-- TEXT -->
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-1">
          <p class="text-sm font-medium text-gray-500">{{ label }}</p>
          <HelpTooltip
            v-if="helpText"
            as-icon
            :text="helpText"
            :aria-label="helpAriaLabel"
          />
        </div>

        <p class="text-2xl font-semibold text-gray-900">{{ value }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import HelpTooltip from "../ui/HelpTooltip.vue";


/**
 * DEFAULT ICONS (fallback ako ne proslediš icon)
 */
 const DEFAULT_ICONS: Record<string, string> = {
  free: "checkmark2",
  occupied: "truck",
  inactive: "blocked",
  tickets: "ticket",
  default: "grid",
};

const props = defineProps<{
  label: string;
  value: number;
  /** Direktno prosleđena ikona iz parenta */
  icon?: string;
  /** Opcioni semantic key ako ne proslediš icon */
  type?: "free" | "occupied" | "inactive" | "tickets";
  helpText?: string;
  helpAriaLabel?: string;
}>();

const icon = computed(() => {
  if (props.icon) return props.icon;
  if (props.type) return DEFAULT_ICONS[props.type];
  return DEFAULT_ICONS.default;
});

</script>
