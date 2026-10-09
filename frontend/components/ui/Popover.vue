<script setup lang="ts">
import {
  PopoverArrow,
  PopoverContent,
  PopoverPortal,
  PopoverRoot,
  PopoverTrigger,
} from "reka-ui";
import { cn } from "~/lib/utils";

// Popover built on Reka UI primitives — shadcn-vue has no CLI wired into this
// project's hand-rolled design system, so new primitives track the existing
// pattern (see Select.vue). Drives the score-breakdown panel in the Bandeja.
// `open` is two-way bound so the parent can also pin/close on hover + Escape.
const open = defineModel<boolean>("open", { default: false });

withDefaults(
  defineProps<{
    align?: "start" | "center" | "end";
    side?: "top" | "right" | "bottom" | "left";
    sideOffset?: number;
    contentClass?: string;
  }>(),
  { align: "end", side: "bottom", sideOffset: 8 }
);
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child>
      <slot name="trigger" />
    </PopoverTrigger>
    <PopoverPortal>
      <PopoverContent
        :align="align"
        :side="side"
        :side-offset="sideOffset"
        :class="
          cn(
            'z-30 w-[380px] max-w-[calc(100vw-2rem)] rounded-md border border-hairline bg-surface p-4 text-ink shadow-ev-2',
            'focus:outline-none',
            contentClass
          )
        "
      >
        <slot />
        <PopoverArrow class="fill-surface" />
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>
