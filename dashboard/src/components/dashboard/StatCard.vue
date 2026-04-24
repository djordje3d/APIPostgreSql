<template>
  <div class="dashboard-card group relative p-5">
    <div
      v-if="helpText"
      class="absolute top-[10px] right-[10px] z-10 h-4 w-4"
    >
      <HelpTooltip
        as-icon
        :text="helpText"
        :aria-label="helpAriaLabel"
      />
    </div>

    <div class="flex items-center gap-4">
      <span
        class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-slate-600 transition "
        aria-hidden="true"
      >
        <span :class="`icon-${icon}`" class="text-lg"></span>
      </span>

      <div class="min-w-0 flex-1">
        <p class="truncate text-sm font-medium text-gray-500">{{ label }}</p>

        <p class="mt-1 text-3xl font-semibold tracking-tight text-gray-900">
          {{ value }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import HelpTooltip from "../ui/HelpTooltip.vue";

const DEFAULT_ICONS: Record<string, string> = {
  free: "checkmark",
  occupied: "truck",
  inactive: "blocked",
  tickets: "ticket",
  default: "grid",
};

const props = defineProps<{
  label: string;
  value: number;
  icon?: string;
  type?: "free" | "occupied" | "inactive" | "tickets";
  subtitle?: string;
  helpText?: string;
  helpAriaLabel?: string;
}>();

const icon = computed(() => {
  if (props.icon) return props.icon;
  if (props.type) return DEFAULT_ICONS[props.type];
  return DEFAULT_ICONS.default;
});
</script>
