<template>
  <div class="rounded-lg bg-white p-4 shadow ring-1 ring-gray-200">
    <div class="flex items-center gap-3">
      <span
        class="flex h-10 w-10 items-center justify-center rounded-full"
        :class="badgeClass"
        aria-hidden="true"
      >
        {{ icon }}
      </span>
      <div>
        <p class="text-sm font-medium text-gray-500">{{ label }}</p>
        <p class="text-2xl font-semibold text-gray-900">{{ value }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const VARIANT_CONFIG: Record<
  string,
  { icon: string; badgeClass: string }
> = {
  green: { icon: '🟢', badgeClass: 'bg-green-100 text-green-700' },
  red: { icon: '🔴', badgeClass: 'bg-red-100 text-red-700' },
  amber: { icon: '🟡', badgeClass: 'bg-amber-100 text-amber-700' },
  slate: { icon: '🧾', badgeClass: 'bg-slate-100 text-slate-700' },
}

// TODO: add a tooltip to the icon
const props = withDefaults(
  defineProps<{
    label: string
    value: number
    variant?: 'green' | 'red' | 'amber' | 'slate'
    icon?: string
  }>(),
  { variant: 'slate' }
)

// TODO: add a tooltip to the value
const config = computed(() => VARIANT_CONFIG[props.variant] ?? VARIANT_CONFIG.slate)
const icon = computed(() => props.icon ?? config.value.icon)
const badgeClass = computed(() => config.value.badgeClass)
</script>
