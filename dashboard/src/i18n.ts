import { createI18n } from "vue-i18n";
import en from "./locales/en.json";
import sr from "./locales/sr.json";

export type SupportedLocale = "en" | "sr";

const STORAGE_KEY = "parking-dashboard-locale";

function getStoredLocale(): SupportedLocale | null {
  if (typeof window === "undefined") return null;
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "sr") return stored;
  } catch {
    // ignore
  }
  return null;
}

export function setStoredLocale(locale: SupportedLocale) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // ignore
  }
}

function detectBrowserLocale(): SupportedLocale {
  if (typeof navigator === "undefined") return "en";
  const lang = navigator.language || navigator.languages?.[0] || "en";
  const lower = lang.toLowerCase();
  if (lower.startsWith("sr")) return "sr";
  return "en";
}

const stored = getStoredLocale();

export const i18n = createI18n({
  legacy: false,
  locale: stored ?? "en",
  fallbackLocale: "en",
  messages: {
    en,
    sr,
  },
});

export const LOCALE_STORAGE_KEY = STORAGE_KEY;

