<script setup lang="ts">
import {
  SelectContent,
  SelectIcon,
  SelectItem,
  SelectItemIndicator,
  SelectItemText,
  SelectPortal,
  SelectRoot,
  SelectTrigger,
  SelectValue,
  SelectViewport,
} from "reka-ui";
import { cn } from "~/lib/utils";

// Custom Select built on Reka UI primitives (shadcn-vue has no CLI component wired
// into this project's hand-rolled design system). Styling tracks the DESIGN input
// spec: 36px control, hairline border, 2px primary focus ring, surface popover.
interface Option {
  value: string;
  label: string;
}

const model = defineModel<string>({ default: "" });
withDefaults(
  defineProps<{
    options: Option[];
    placeholder?: string;
    invalid?: boolean;
  }>(),
  { placeholder: "Selecciona…", invalid: false }
);
</script>

<template>
  <SelectRoot v-model="model">
    <SelectTrigger
      :class="
        cn(
          'flex h-9 w-full items-center justify-between gap-2 rounded-md border bg-background px-3 text-sm text-ink shadow-sm transition-colors',
          'data-[placeholder]:text-muted-foreground',
          'focus-visible:outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/25',
          invalid ? 'border-destructive' : 'border-border',
          $attrs.class
        )
      "
    >
      <SelectValue :placeholder="placeholder" />
      <SelectIcon class="shrink-0 text-ink-muted">
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </SelectIcon>
    </SelectTrigger>

    <SelectPortal>
      <SelectContent
        position="popper"
        :side-offset="4"
        class="z-50 max-h-64 min-w-[var(--reka-select-trigger-width)] overflow-hidden rounded-md border border-border bg-surface text-ink shadow-ev-2"
      >
        <SelectViewport class="p-1">
          <SelectItem
            v-for="opt in options"
            :key="opt.value"
            :value="opt.value"
            class="relative flex cursor-pointer select-none items-center rounded-sm py-2 pl-8 pr-3 text-sm outline-none transition-colors data-[highlighted]:bg-surface-sunken data-[state=checked]:font-semibold"
          >
            <span class="absolute left-2 flex h-4 w-4 items-center justify-center">
              <SelectItemIndicator>
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  class="text-primary"
                  aria-hidden="true"
                >
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              </SelectItemIndicator>
            </span>
            <SelectItemText>{{ opt.label }}</SelectItemText>
          </SelectItem>
        </SelectViewport>
      </SelectContent>
    </SelectPortal>
  </SelectRoot>
</template>
