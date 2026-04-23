<template>
  <div class="flex items-center gap-1 text-sm">
    <StandardDropdown
      :options="localeOptions"
      :model-value="current"
      :nullable="false"
      @update:model-value="changeLocale($event as SupportedLocale)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { setStoredLocale, type SupportedLocale } from "../../i18n";
import StandardDropdown from "./StandardDropdown.vue";

const { locale } = useI18n();

const current = computed((): SupportedLocale => {
  const v = String(locale.value ?? "").toLowerCase();
  return v.startsWith("sr") ? "sr" : "en";
});

const localeOptions = [
  { id: "en" as const, label: "EN" },
  { id: "sr" as const, label: "SR" },
];

function changeLocale(next: SupportedLocale | null) {
  if (next == null || current.value === next) return;
  locale.value = next;
  setStoredLocale(next);
}
</script>
