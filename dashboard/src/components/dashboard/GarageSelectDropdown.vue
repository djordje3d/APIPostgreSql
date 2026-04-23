<template>
  <div class="by-garage-card__right-row h-full">
    <div
      class="by-garage-card__dropdown-wrap by-garage-card__cell relative flex h-full min-h-0 w-full flex-col"
    >
      <div
        class="by-garage-card__icon-region flex min-h-0 flex-1 items-center justify-center"
      >
        <span class="by-garage-card__icon" aria-hidden="true">
          <img :src="garageIcon" alt="" class="by-garage-card__icon-img" />
        </span>
      </div>
      <div class="w-full min-w-0 shrink-0">
        <StandardDropdown
          :label="t('garageSelectDropdown.title')"
          label-class="text-base"
          :options="garageOptions"
          :model-value="modelValue"
          :nullable="true"
          :null-option-label="t('garageSelectDropdown.allGarages')"
          :placeholder="t('garageSelectDropdown.selectGarage')"
          @update:model-value="
            (v) => emit('update:modelValue', v as number | null)
          "
        />
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import StandardDropdown from "../ui/StandardDropdown.vue";
import { useI18n } from "vue-i18n";
import garageIcon from "../../assets/images/urban-parking-garage.svg";

const { t } = useI18n();

type Garage = { id: number; name: string };

const props = defineProps<{
  garages: Garage[];
  modelValue: number | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: number | null): void;
}>();

const garageOptions = computed(() =>
  props.garages.map((g) => ({ id: g.id, label: g.name })),
);
</script>

<style scoped>
.by-garage-card__cell {
  flex-shrink: 0;
}
.by-garage-card__icon {
  width: 6.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 6rem;
  border-radius: 0.375rem;
  background: transparent;
  color: rgb(71 85 105);
}
.by-garage-card__icon-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.by-garage-card__right-row {
  display: flex;
  align-items: stretch;
  gap: 1rem;
  flex: 1;
  height: 100%;
  min-width: 0;
}
.by-garage-card__dropdown-wrap {
  gap: 0.5rem;
  min-width: 11rem;
  max-width: 16rem;
}
.by-garage-card__viewing {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 16rem;
  margin-left: auto;
}
</style>
