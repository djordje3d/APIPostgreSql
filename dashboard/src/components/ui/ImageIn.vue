<template>
  <div v-if="src" class="image-in-wrap relative min-h-[120px] max-h-[200px]">
    <img
      :src="src"
      :alt="alt"
      class="image-in max-h-[200px] w-full rounded-lg border border-gray-200 object-cover"
      :class="{ 'invisible': loading || error }"
      :style="imageStyle"
      @load="onLoad"
      @error="onError"
    />
    <div
      v-show="loading"
      class="image-in-skeleton absolute inset-0 flex items-center justify-center rounded-lg bg-gray-100"
      aria-busy="true"
      aria-label="Loading image"
    >
      <span
        class="icon-spinner11 inline-block text-2xl animate-spin text-gray-400"
        aria-hidden="true"
      />
    </div>
    <div
      v-show="error"
      class="image-in-fallback absolute inset-0 flex items-center justify-center rounded-lg border border-gray-200 bg-gray-50 px-4 py-6 text-center text-sm text-gray-500"
      role="img"
      :aria-label="alt || 'Image unavailable'"
    >
      Image unavailable
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";

const props = withDefaults(
  defineProps<{
    src?: string | null;
    alt?: string;
    aspectRatio?: string;
    objectFit?: "contain" | "cover" | "fill" | "none";
  }>(),
  {
    alt: "",
    objectFit: "cover",
  },
);

const loading = ref(true);
const error = ref(false);

const imageStyle = computed(() => {
  const style: Record<string, string> = {};
  if (props.aspectRatio) {
    style.aspectRatio = props.aspectRatio;
  }
  if (props.objectFit) {
    style.objectFit = props.objectFit;
  }
  return style;
});

function onLoad() {
  loading.value = false;
  error.value = false;
}

function onError() {
  loading.value = false;
  error.value = true;
}

watch(
  () => props.src,
  (newSrc) => {
    if (newSrc) {
      loading.value = true;
      error.value = false;
    }
  },
  { immediate: true },
);
</script>

<style scoped>
.image-in-wrap {
  min-width: 0;
}
</style>
