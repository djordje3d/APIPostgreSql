<template>
  <div class="input-in-wrap">
    <label
      v-if="label"
      :for="id"
      class="mb-1 block text-sm font-medium text-slate-700"
    >
      {{ label }}
    </label>
    <input
      :id="id"
      :value="modelValue"
      :type="type"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :title="caption"
      :aria-invalid="variant === 'error'"
      :aria-describedby="error ? `${id}-error` : undefined"
      class="input-in w-full rounded border px-3 py-2 transition-colors focus:outline-none focus:ring-1"
      :class="variantClasses"
      v-bind="restAttrs"
      @input="onInput"
    />
    <p
      v-if="error"
      :id="`${id}-error`"
      class="mt-1 text-sm font-medium text-red-600"
      role="alert"
    >
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, useAttrs } from "vue";

defineOptions({
  inheritAttrs: false,
});

const props = withDefaults(
  defineProps<{
    id: string;
    label?: string;
    modelValue?: string | number;
    type?: "text" | "password" | "number" | "email";
    placeholder?: string;
    required?: boolean;
    disabled?: boolean;
    variant?: "default" | "error";
    caption?: string;
    error?: string;
  }>(),
  {
    type: "text",
    required: false,
    disabled: false,
    variant: "default",
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string | number];
}>();

const attrs = useAttrs();
const restAttrs = computed(() => {
  const { class: _c, ...rest } = attrs as Record<string, unknown>;
  return rest;
});

const variantClasses = computed(() => {
  if (props.variant === "error") {
    return "border-red-500 bg-red-50 focus:border-red-500 focus:ring-red-500";
  }
  return "border-slate-300 focus:border-emerald-500 focus:ring-emerald-500";
});

function onInput(e: Event) {
  const el = e.target as HTMLInputElement;
  const val =
    props.type === "number"
      ? (Number.isNaN(el.valueAsNumber) ? 0 : el.valueAsNumber)
      : el.value;
  emit("update:modelValue", val);
}
</script>

<style scoped>
.input-in-wrap {
  min-width: 0;
}
</style>
