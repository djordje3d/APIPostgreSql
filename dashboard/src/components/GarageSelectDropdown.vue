<template>
  <span class="by-garage-card__icon by-garage-card__cell" aria-hidden="true">
    <img :src="garageIcon" alt="" class="by-garage-card__icon-img" />
  </span>
  <div ref="root" class="by-garage-card__dropdown-wrap by-garage-card__cell relative inline-block w-full">
    <span class="by-garage-card__desc">See status and activity per garage</span>
  
      <!-- Trigger -->
      <button
        ref="trigger"
        type="button"
        class="mt-2 w-full rounded border border-gray-300 bg-white px-3 py-2 text-left text-sm shadow-sm
               focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500
               hover:border-gray-400 transition"
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
          <span class="shrink-0 text-gray-500">
            <!-- chevron -->
            <svg class="h-4 w-4 transition-transform" :class="{ 'rotate-180': open }" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 10.94l3.71-3.71a.75.75 0 1 1 1.06 1.06l-4.24 4.24a.75.75 0 0 1-1.06 0L5.21 8.29a.75.75 0 0 1 .02-1.08z" clip-rule="evenodd"/>
            </svg>
          </span>
        </span>
      </button>
  
      <!-- Dropdown (teleport so it won't be clipped by parent/overflow) -->
      <Teleport to="body">
        <Transition name="pop">
          <div
            v-if="open"
            ref="menu"
            class="fixed zPopup"
            :style="menuStyle"
          >
            <!-- popup box -->
            <div
              class="rounded-lg border border-gray-200 bg-white shadow-xl ring-1 ring-black/5 overflow-hidden"
            >
              <!-- nub/arrow -->
              <div
                class="pointer-events-none absolute left-6"
                :style="nubStyle"
              >
                <div
                  class="h-3 w-3 rotate-45 bg-white border border-gray-200 shadow-sm"
                  :class="nubBorderAdjustClass"
                ></div>
              </div>
  
              <!-- scroll area -->
              <ul
                class="max-h-64 overflow-auto py-1 text-sm"
                role="listbox"
                tabindex="-1"
                @keydown.esc.prevent="close()"
                @keydown.down.prevent="focusNext()"
                @keydown.up.prevent="focusPrev()"
                @keydown.enter.prevent="selectFocused()"
              >
                <li>
                  <button
                    ref="items"
                    type="button"
                    class="w-full px-3 py-2 text-left hover:bg-emerald-50 focus:bg-emerald-50 focus:outline-none"
                    :class="{ 'font-semibold text-emerald-700': modelValue === null }"
                    @click="choose(null)"
                  >
                    All garages
                  </button>
                </li>
  
                <li v-for="g in garages" :key="g.id">
                  <button
                    ref="items"
                    type="button"
                    class="w-full px-3 py-2 text-left hover:bg-emerald-50 focus:bg-emerald-50 focus:outline-none"
                    :class="{ 'font-semibold text-emerald-700': modelValue === g.id }"
                    @click="choose(g.id)"
                  >
                    {{ g.name }}
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
  import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
  import garageIcon from "../img/urban-parking-garage.svg"
  
  type Garage = { id: number; name: string }
  
  const props = defineProps<{
    garages: Garage[]
    modelValue: number | null
  }>()
  
  const emit = defineEmits<{
    (e: "update:modelValue", value: number | null): void
  }>()
  
  const root = ref<HTMLElement | null>(null)
  const trigger = ref<HTMLElement | null>(null)
  const menu = ref<HTMLElement | null>(null)
  const items = ref<HTMLButtonElement[] | null>(null)
  
  const open = ref(false)
  const openUp = ref(false)
  
  const menuStyle = ref<Record<string, string>>({})
  const nubStyle = ref<Record<string, string>>({})
  const focusedIndex = ref(0)
  
  const selectedLabel = computed(() => {
    if (props.modelValue == null) return "All garages"
    return props.garages.find(g => g.id === props.modelValue)?.name ?? "Select a garage…"
  })
  
  const nubBorderAdjustClass = computed(() => {
    // hide the border edge touching the box, so it looks like a single shape
    return openUp.value ? "border-b-0 border-r-0 -mb-[1px]" : "border-t-0 border-l-0 -mt-[1px]"
  })
  
  function toggle() {
    open.value ? close() : openMenu()
  }
  
  function close() {
    open.value = false
  }
  
  function choose(id: number | null) {
    emit("update:modelValue", id)
    close()
    nextTick(() => trigger.value?.focus())
  }
  
  function getAllItemButtons(): HTMLButtonElement[] {
    // Vue collects multiple refs with same name into array
    // @ts-ignore
    return (items.value as any) ?? []
  }
  
  function focusItem(index: number) {
    const els = getAllItemButtons()
    if (!els.length) return
    const clamped = Math.max(0, Math.min(index, els.length - 1))
    focusedIndex.value = clamped
    els[clamped]?.focus()
  }
  
  function focusNext() {
    focusItem(focusedIndex.value + 1)
  }
  
  function focusPrev() {
    focusItem(focusedIndex.value - 1)
  }
  
  function selectFocused() {
    const els = getAllItemButtons()
    const el = els[focusedIndex.value]
    el?.click()
  }
  
  function openAndFocusFirst() {
    if (!open.value) openMenu(() => focusItem(0))
    else focusItem(0)
  }
  
  function openAndFocusLast() {
    const count = getAllItemButtons().length
    if (!open.value) openMenu(() => focusItem(count - 1))
    else focusItem(count - 1)
  }
  
  function openMenu(after?: () => void) {
    open.value = true
    nextTick(() => {
      positionMenu()
      // focus selected item if possible
      const els = getAllItemButtons()
      const selectedIdx =
        props.modelValue == null
          ? 0
          : 1 + props.garages.findIndex(g => g.id === props.modelValue)
      focusItem(selectedIdx >= 0 ? selectedIdx : 0)
      after?.()
    })
  }
  
  function positionMenu() {
    const t = trigger.value
    if (!t) return
  
    const rect = t.getBoundingClientRect()
    const viewportW = window.innerWidth
    const viewportH = window.innerHeight
  
    const margin = 10
    const menuMaxH = 256 // matches max-h-64 (64*4px)
    const estimatedH = Math.min(menuMaxH + 20, 320) // rough including padding/border
  
    const spaceBelow = viewportH - rect.bottom - margin
    const spaceAbove = rect.top - margin
  
    openUp.value = spaceBelow < estimatedH && spaceAbove > spaceBelow
  
    const width = rect.width
    const left = Math.min(Math.max(rect.left, margin), viewportW - width - margin)
  
    // We’ll place the menu either under or above trigger
    const top = openUp.value
      ? Math.max(margin, rect.top - estimatedH)
      : Math.min(viewportH - estimatedH - margin, rect.bottom + 8)
  
    menuStyle.value = {
      left: `${left}px`,
      top: `${top}px`,
      width: `${width}px`,
    }
  
    // nub position: if opening down, nub is on top edge; if opening up, nub is on bottom edge
    nubStyle.value = openUp.value
      ? { bottom: "-6px" } // sits at bottom of box, pointing down to trigger
      : { top: "-6px" } // sits at top of box, pointing up to trigger
  }
  
  function onClickOutside(e: MouseEvent) {
    if (!open.value) return
    const trg = trigger.value
    const mn = menu.value
    const target = e.target as Node
  
    if (trg && trg.contains(target)) return
    if (mn && mn.contains(target)) return
    close()
  }
  
  function onResizeOrScroll() {
    if (!open.value) return
    positionMenu()
  }
  
  onMounted(() => {
    document.addEventListener("mousedown", onClickOutside)
    window.addEventListener("resize", onResizeOrScroll)
    window.addEventListener("scroll", onResizeOrScroll, true) // true = capture, catches inner scroll containers too
  })
  
  onBeforeUnmount(() => {
    document.removeEventListener("mousedown", onClickOutside)
    window.removeEventListener("resize", onResizeOrScroll)
    window.removeEventListener("scroll", onResizeOrScroll, true)
  })
  
  watch(
    () => props.garages,
    () => {
      if (open.value) nextTick(positionMenu)
    }
  )
  </script>
  
  <style scoped>
  .pop-enter-active,
  .pop-leave-active {
    transition: opacity 140ms ease, transform 140ms ease;
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
  .by-garage-card__dropdown-wrap {
    width: 24rem;
    min-width: 13rem;
  }
  </style>