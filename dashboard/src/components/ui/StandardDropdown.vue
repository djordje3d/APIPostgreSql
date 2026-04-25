<template>
  <div ref="root" class="standard-dropdown relative inline-block w-full">
    <label
      v-if="label"
      class="mb-1 block text-gray-600"
      :class="labelClass"
    >
      {{ label }}
    </label>

    <!-- Trigger -->
    <button
      ref="trigger"
      type="button"
      class="h-12 w-full rounded border px-3 text-left text-sm font-medium shadow-sm transition"
      :class="[
        { 'mt-1': label },
        dark
          ? 'border-slate-600 bg-slate-800 text-white hover:bg-slate-700 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500'
          : 'border-gray-300 bg-white text-gray-900 hover:border-gray-400 focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400',
      ]"
      :aria-expanded="open"
      @click="toggle"
      @keydown.down.prevent="openAndFocusFirst()"
      @keydown.up.prevent="openAndFocusLast()"
      @keydown.esc.prevent="close()"
    >
      <span class="flex items-center justify-between gap-2">
        <span class="truncate">
          {{ selectedLabel }}
        </span>
        <span :class="dark ? 'text-slate-300' : 'text-gray-500'">
          <svg
            class="h-4 w-4 transition-transform"
            :class="{ 'rotate-180': open }"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 10.94l3.71-3.71a.75.75 0 1 1 1.06 1.06l-4.24 4.24a.75.75 0 0 1-1.06 0L5.21 8.29a.75.75 0 0 1 .02-1.08z"
              clip-rule="evenodd"
            />
          </svg>
        </span>
      </span>
    </button>

    <!-- Dropdown (teleport so it won't be clipped by parent/overflow) -->
    <Teleport to="body">
      <Transition name="pop">
        <div v-if="open" ref="menu" class="fixed zPopup" :style="menuStyle">
          <div
            class="rounded-lg border shadow-xl overflow-hidden"
            :class="
              dark
                ? 'border-slate-600 bg-slate-800 ring-1 ring-black/20'
                : 'border-gray-200 bg-white ring-1 ring-black/5'
            "
          >
            <div class="pointer-events-none absolute left-6" :style="nubStyle">
              <div
                class="h-3 w-3 rotate-45 shadow-sm"
                :class="[
                  nubBorderAdjustClass,
                  dark
                    ? 'bg-slate-800 border-slate-600'
                    : 'bg-white border border-gray-200',
                ]"
              ></div>
            </div>

            <ul
              class="max-h-64 overflow-auto py-1 text-sm"
              :class="dark ? 'text-white' : ''"
              role="listbox"
              tabindex="-1"
              @keydown.esc.prevent="close()"
              @keydown.down.prevent="focusNext()"
              @keydown.up.prevent="focusPrev()"
              @keydown.enter.prevent="selectFocused()"
            >
              <li v-if="nullable">
                <button
                  ref="items"
                  type="button"
                  class="w-full px-3 py-2 text-left focus:outline-none"
                  :class="[
                    dark
                      ? 'hover:bg-slate-700 focus:bg-slate-700'
                      : 'hover:bg-emerald-50 focus:bg-emerald-50',
                    {
                      'font-semibold text-emerald-700':
                        !dark && modelValue === null,
                      'font-semibold text-emerald-300':
                        dark && modelValue === null,
                    },
                  ]"
                  @click="choose(null)"
                >
                  {{ nullOptionLabel }}
                </button>
              </li>

              <li v-for="opt in options" :key="opt.id">
                <button
                  ref="items"
                  type="button"
                  class="w-full px-3 py-2 text-left focus:outline-none"
                  :class="[
                    dark
                      ? 'hover:bg-slate-700 focus:bg-slate-700'
                      : 'hover:bg-emerald-50 focus:bg-emerald-50',
                    {
                      'font-semibold text-emerald-700':
                        !dark && modelValue === opt.id,
                      'font-semibold text-emerald-300':
                        dark && modelValue === opt.id,
                    },
                  ]"
                  @click="choose(opt.id)"
                >
                  {{ opt.label }}
                </button>
              </li>
            </ul>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";

export type DropdownOption = { id: number | string; label: string };

const props = withDefaults(
  defineProps<{
    label?: string;
    labelClass?: string;
    options: DropdownOption[];
    modelValue: number | string | null;
    placeholder?: string;
    nullable?: boolean;
    nullOptionLabel?: string;
    /** When true, use dark background (e.g. for header) matching slate-800 */
    dark?: boolean;
  }>(),
  {
    placeholder: "Select…",
    nullable: false,
    nullOptionLabel: "",
    dark: false,
    labelClass: "text-sm font-medium",
  },
);

const emit = defineEmits<{
  (e: "update:modelValue", value: number | string | null): void;
  (e: "change", value: number | string | null): void;
}>();

const trigger = ref<HTMLElement | null>(null);
const menu = ref<HTMLElement | null>(null);
const items = ref<HTMLButtonElement[] | null>(null);

const open = ref(false);
const openUp = ref(false);

const menuStyle = ref<Record<string, string>>({});
const nubStyle = ref<Record<string, string>>({});
const focusedIndex = ref(0);

const selectedLabel = computed(() => {
  if (props.modelValue == null) {
    return props.nullable ? props.nullOptionLabel : props.placeholder;
  }
  return (
    props.options.find((o) => o.id === props.modelValue)?.label ??
    props.placeholder
  );
});

const nubBorderAdjustClass = computed(() => {
  return openUp.value
    ? "border-b-0 border-r-0 -mb-[1px]"
    : "border-t-0 border-l-0 -mt-[1px]";
});

function toggle() {
  open.value ? close() : openMenu();
}

function close() {
  open.value = false;
}

function choose(id: number | string | null) {
  emit("update:modelValue", id);
  emit("change", id);
  close();
  nextTick(() => trigger.value?.focus());
}

function getAllItemButtons(): HTMLButtonElement[] {
  return (items.value as unknown as HTMLButtonElement[]) ?? [];
}

function focusItem(index: number) {
  const els = getAllItemButtons();
  if (!els.length) return;
  const clamped = Math.max(0, Math.min(index, els.length - 1));
  focusedIndex.value = clamped;
  els[clamped]?.focus();
}

function focusNext() {
  focusItem(focusedIndex.value + 1);
}

function focusPrev() {
  focusItem(focusedIndex.value - 1);
}

function selectFocused() {
  const els = getAllItemButtons();
  const el = els[focusedIndex.value];
  el?.click();
}

function openAndFocusFirst() {
  if (!open.value) openMenu(() => focusItem(0));
  else focusItem(0);
}

function openAndFocusLast() {
  const count = getAllItemButtons().length;
  if (!open.value) openMenu(() => focusItem(count - 1));
  else focusItem(count - 1);
}

function getSelectedIndex(): number {
  if (props.modelValue == null) return props.nullable ? 0 : -1;
  const idx = props.options.findIndex((o) => o.id === props.modelValue);
  return idx >= 0 ? (props.nullable ? 1 + idx : idx) : -1;
}

const MENU_GAP = 8;
const VIEW_MARGIN = 10;
/** max-h-64 on the list (256px) + chrome (border, nub) */
const LIST_MAX_H = 256;
const ROW_EST = 40;

function estimateMenuHeight(): number {
  const rows = (props.nullable ? 1 : 0) + props.options.length;
  return Math.min(LIST_MAX_H + 36, Math.max(48, rows * ROW_EST + 32));
}

function readMenuHeight(): number {
  const m = menu.value;
  if (!m) return estimateMenuHeight();
  const h = m.getBoundingClientRect().height;
  if (h > 1) return h;
  return estimateMenuHeight();
}

function openMenu(after?: () => void) {
  open.value = true;
  nextTick(() => {
    positionMenu();
    const selectedIdx = getSelectedIndex();
    focusItem(selectedIdx >= 0 ? selectedIdx : 0);
    after?.();
    // Second pass after teleported menu paints (avoids using a fixed 320px “ghost” height).
    requestAnimationFrame(() => {
      positionMenu();
    });
  });
}

function positionMenu() {
  const t = trigger.value;
  if (!t) return;

  const rect = t.getBoundingClientRect();
  const viewportW = window.innerWidth;
  const viewportH = window.innerHeight;

  const menuH = readMenuHeight();
  const needH = menuH + MENU_GAP;

  const spaceBelow = viewportH - rect.bottom - VIEW_MARGIN;
  const spaceAbove = rect.top - VIEW_MARGIN;

  openUp.value = spaceBelow < needH && spaceAbove > spaceBelow;

  const width = rect.width;
  const left = Math.min(
    Math.max(rect.left, VIEW_MARGIN),
    viewportW - width - VIEW_MARGIN,
  );

  let top: number;
  if (openUp.value) {
    top = rect.top - MENU_GAP - menuH;
    top = Math.max(VIEW_MARGIN, top);
  } else {
    top = rect.bottom + MENU_GAP;
    if (top + menuH > viewportH - VIEW_MARGIN) {
      top = Math.max(
        VIEW_MARGIN,
        Math.min(top, viewportH - VIEW_MARGIN - menuH),
      );
    }
  }

  menuStyle.value = {
    left: `${left}px`,
    top: `${top}px`,
    width: `${width}px`,
  };

  nubStyle.value = openUp.value ? { bottom: "-6px" } : { top: "-6px" };
}

function onClickOutside(e: MouseEvent) {
  if (!open.value) return;
  const trg = trigger.value;
  const mn = menu.value;
  const target = e.target as Node;

  if (trg && trg.contains(target)) return;
  if (mn && mn.contains(target)) return;
  close();
}

function onResizeOrScroll() {
  if (!open.value) return;
  positionMenu();
}

onMounted(() => {
  document.addEventListener("mousedown", onClickOutside);
  window.addEventListener("resize", onResizeOrScroll);
  window.addEventListener("scroll", onResizeOrScroll, true);
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onClickOutside);
  window.removeEventListener("resize", onResizeOrScroll);
  window.removeEventListener("scroll", onResizeOrScroll, true);
});

watch(
  () => props.options,
  () => {
    if (open.value) nextTick(positionMenu);
  },
);
</script>

<style scoped>
.pop-enter-active,
.pop-leave-active {
  transition:
    opacity 140ms ease,
    transform 140ms ease;
}

.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

.pop-enter-to,
.pop-leave-from {
  opacity: 1;
  transform: scale(1);
}
</style>
