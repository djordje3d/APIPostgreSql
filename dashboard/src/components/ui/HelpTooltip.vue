<template>
  <template v-if="asIcon">
    <button
      ref="btnRef"
      type="button"
      class="help-tooltip__icon-btn inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-gray-300 bg-white text-[10px] font-bold leading-none text-gray-500 hover:border-gray-400 hover:text-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-1"
      :aria-label="ariaLabel"
      :aria-describedby="open ? tipId : undefined"
      @mouseenter="openTip"
      @mouseleave="scheduleClose"
      @focus="openTip"
      @blur="scheduleClose"
    >
      <span aria-hidden="true">?</span>
    </button>
  </template>
  <div
    v-else
    ref="rootRef"
    class="help-tooltip__wrap inline-flex"
    @mouseenter="openTip"
    @mouseleave="scheduleClose"
    @focusin="onWrapFocusIn"
    @focusout="onWrapFocusOut"
  >
    <slot />
  </div>

  <Teleport to="body">
    <div
      v-show="open"
      :id="tipId"
      ref="tipRef"
      role="tooltip"
      class="help-tooltip__panel pointer-events-none fixed z-[10050] max-w-xs rounded-md border border-gray-700 bg-gray-900 px-2.5 py-1.5 text-left text-xs font-normal leading-snug text-white shadow-lg"
      :style="panelStyle"
    >
      {{ text }}
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from "vue";

const props = withDefaults(
  defineProps<{
    text: string;
    /** When true, renders only a small “?” control; no default slot. */
    asIcon?: boolean;
    /** Accessible name for the icon button. */
    ariaLabel?: string;
  }>(),
  {
    asIcon: false,
    ariaLabel: "Help",
  },
);

const open = ref(false);
const rootRef = ref<HTMLElement | null>(null);
const btnRef = ref<HTMLButtonElement | null>(null);
const tipRef = ref<HTMLElement | null>(null);
const tipId = `help-tip-${Math.random().toString(36).slice(2, 11)}`;

const panelStyle = ref<Record<string, string>>({
  top: "0px",
  left: "0px",
  transform: "translateX(-50%)",
});

let closeTimer: ReturnType<typeof setTimeout> | null = null;

function clearCloseTimer() {
  if (closeTimer != null) {
    clearTimeout(closeTimer);
    closeTimer = null;
  }
}

function openTip() {
  clearCloseTimer();
  open.value = true;
}

function scheduleClose() {
  clearCloseTimer();
  closeTimer = setTimeout(() => {
    open.value = false;
    closeTimer = null;
  }, 100);
}

function onWrapFocusIn() {
  clearCloseTimer();
  open.value = true;
}

function onWrapFocusOut(ev: FocusEvent) {
  const next = ev.relatedTarget as Node | null;
  if (next && rootRef.value?.contains(next)) return;
  open.value = false;
}

function anchorEl(): HTMLElement | null {
  return props.asIcon ? btnRef.value : rootRef.value;
}

function updatePosition() {
  const el = anchorEl();
  if (!el) return;

  const r = el.getBoundingClientRect();
  const margin = 8;
  let top = r.bottom + margin;
  let left = r.left + r.width / 2;

  const tip = tipRef.value;
  if (tip) {
    const tr = tip.getBoundingClientRect();
    const half = tr.width / 2;
    left = Math.max(
      margin + half,
      Math.min(left, window.innerWidth - margin - half),
    );
    if (top + tr.height > window.innerHeight - margin) {
      top = Math.max(margin, r.top - tr.height - margin);
    }
  }

  panelStyle.value = {
    top: `${top}px`,
    left: `${left}px`,
    transform: "translateX(-50%)",
  };
}

const scrollOrResizeHandler = () => {
  if (open.value) updatePosition();
};

watch(open, async (isOpen) => {
  if (isOpen) {
    await nextTick();
    updatePosition();
    window.addEventListener("scroll", scrollOrResizeHandler, true);
    window.addEventListener("resize", scrollOrResizeHandler);
  } else {
    window.removeEventListener("scroll", scrollOrResizeHandler, true);
    window.removeEventListener("resize", scrollOrResizeHandler);
  }
});

onBeforeUnmount(() => {
  clearCloseTimer();
  window.removeEventListener("scroll", scrollOrResizeHandler, true);
  window.removeEventListener("resize", scrollOrResizeHandler);
});
</script>
