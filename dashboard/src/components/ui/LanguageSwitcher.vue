<template>
  <div class="flex items-center gap-1 text-sm">
    <button
      type="button"
      class="px-2 py-1 rounded-md border border-transparent"
      :class="{
        'bg-white text-slate-900 border-slate-300 shadow-sm': locale === 'en',
        'text-slate-200 hover:text-white hover:bg-slate-700': locale !== 'en',
      }"
      @click="changeLocale('en')"
    >
      EN
    </button>
    <button
      type="button"
      class="px-2 py-1 rounded-md border border-transparent"
      :class="{
        'bg-white text-slate-900 border-slate-300 shadow-sm': locale === 'sr',
        'text-slate-200 hover:text-white hover:bg-slate-700': locale !== 'sr',
      }"
      @click="changeLocale('sr')"
    >
      SR
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { setStoredLocale, type SupportedLocale } from "../../i18n";

const { locale } = useI18n();

const current = computed(() => String(locale.value) as SupportedLocale);

function changeLocale(next: SupportedLocale) {
  if (current.value === next) return;
  locale.value = next;
  setStoredLocale(next);
  // Backend sync of preferred_language will be handled where user/profile is known.
}
</script>

