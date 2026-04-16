<template>
  <div
    v-if="total > 0"
    class="flex items-center justify-between border-t border-gray-200 px-4 py-3"
  >
    <div class="flex items-center gap-3">
      <p class="text-sm text-gray-600">
        Showing {{ start }}–{{ end }} of {{ total }}
      </p>

      <label
        v-if="showPageSize"
        class="flex items-center gap-2 text-sm text-gray-600"
      >
        <span>Page size</span>
        <select
          :value="pageSize"
          class="rounded border border-gray-300 bg-white px-2 py-1 text-sm text-gray-700"
          @change="onPageSizeChange"
        >
          <option v-for="size in pageSizeOptions" :key="size" :value="size">
            {{ size }}
          </option>
        </select>
      </label>
    </div>

    <div class="flex items-center gap-2">
      <button
        v-if="page > 1"
        type="button"
        class="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-600 focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-1"
        aria-label="Previous page"
        :title="t('garageDetail.previousPage')"
        @click="goPrev"
      >
        <span class="icon-arrow-left text-sm" aria-hidden="true"></span>
      </button>

      <span class="text-sm text-gray-600">
        {{ t("garageDetail.page") }} {{ page }} {{ t("garageDetail.of") }}
        {{ totalPages }}
      </span>

      <button
        v-if="page < totalPages"
        type="button"
        class="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-600 focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-1"
        aria-label="Next page"
        :title="t('garageDetail.nextPage')"
        @click="goNext"
      >
        <span class="icon-arrow-right text-sm" aria-hidden="true"></span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const props = withDefaults(
  defineProps<{
    page: number;
    pageSize: number;
    total: number;
    showPageSize?: boolean;
    pageSizeOptions?: number[];
  }>(),
  {
    showPageSize: false,
    pageSizeOptions: () => [5, 10, 20],
  },
);

const emit = defineEmits<{
  "update:page": [value: number];
  "update:pageSize": [value: number];
}>();

const totalPages = computed(() =>
  Math.max(1, Math.ceil(props.total / props.pageSize)),
);

const start = computed(() => (props.page - 1) * props.pageSize + 1);

const end = computed(() => Math.min(props.page * props.pageSize, props.total));

function goPrev() {
  if (props.page > 1) {
    emit("update:page", props.page - 1);
  }
}

function goNext() {
  if (props.page < totalPages.value) {
    emit("update:page", props.page + 1);
  }
}

function onPageSizeChange(event: Event) {
  const value = Number((event.target as HTMLSelectElement).value);
  if (Number.isFinite(value) && value > 0) {
    emit("update:pageSize", value);
  }
}
</script>