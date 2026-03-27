<template>
  <div class="by-garage-card__right-row">
    <div
      class="by-garage-card__dropdown-wrap by-garage-card__cell relative inline-block w-full"
    >
      <span class="by-garage-card__icon" aria-hidden="true">
        <img :src="garageIcon" alt="" class="by-garage-card__icon-img" />
      </span>
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

    <div
      v-if="modelValue != null"
      class="by-garage-card__viewing by-garage-card__cell"
    >
      <span class="icon-eye text-lg text-gray-600"></span>
      <router-link
        :to="{ name: 'garage-detail', params: { id: modelValue } }"
        class="font-semibold text-emerald-600 hover:text-emerald-700 hover:underline"
      >
        {{ selectedGarageName }}
      </router-link>
      <span class="text-base text-gray-600">
        {{ t("garageSelectDropdown.clickToOpenGarageDetail") }}
      </span>
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

const selectedGarageName = computed(
  () => props.garages.find((g) => g.id === props.modelValue)?.name ?? "Garage",
);
</script>

<style scoped>
.by-garage-card__cell {
  flex-shrink: 0;
}
.by-garage-card__icon {
  width: 5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 4rem;
  border-radius: 0.375rem;
  background: rgb(241 245 249);
  color: rgb(71 85 105);
}
.by-garage-card__icon-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.by-garage-card__right-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex: 1;
  min-width: 0;
}
.by-garage-card__dropdown-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
  width: 100%;
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
