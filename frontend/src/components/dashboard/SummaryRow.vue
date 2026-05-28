<template>
  <div class="flex justify-between text-sm">
    <span class="text-gray-600">{{ label }}</span>
    <span class="font-medium" :class="valueClass">{{ value }}</span>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    value: string | number
    valueClass?: string
  }>(),
  { valueClass: 'text-gray-900' }
)
</script>
