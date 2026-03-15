<template>
  <div
    v-if="total > 0"
    class="flex items-center justify-between border-t border-gray-200 px-4 py-3"
  >
    <p class="text-sm text-gray-600">
      Showing {{ start }}–{{ end }} of {{ total }}
    </p>
    <div class="flex items-center gap-2">
      <ButtonIn
        type="button"
        id="previousPage"
        variant="outline"
        :disabled="page <= 1"
        @userclick="goPrev"
        :label="t('garageDetail.previousPage')"
      />
      <span class="text-sm text-gray-600">
       {{ t('garageDetail.page')}} {{ page }} {{ t('garageDetail.of') }} {{ totalPages }}
      </span>
      <ButtonIn
        type="button"
        id="nextPage"
        variant="outline"
        :disabled="page >= totalPages"
        @userclick="goNext"
        :label="t('garageDetail.nextPage')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import ButtonIn from "./ButtonIn.vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const props = defineProps<{
  page: number;
  pageSize: number;
  total: number;
}>();

const emit = defineEmits<{
  "update:page": [value: number];
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
</script>
