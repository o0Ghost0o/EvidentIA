<script setup lang="ts">
import { cva } from "class-variance-authority";
import { cn } from "~/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 h-9 px-4 py-2",
  {
    variants: {
      variant: {
        default: "bg-primary text-on-primary hover:bg-primary-deep font-semibold shadow-ev-1",
        secondary: "bg-surface-sunken text-ink hover:bg-hairline",
        outline: "border border-hairline bg-transparent hover:bg-surface-sunken text-ink",
        ghost: "hover:bg-surface-sunken text-ink-muted hover:text-ink",
        destructive: "bg-error text-on-primary hover:bg-error/90 font-semibold shadow-ev-1",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

withDefaults(
  defineProps<{
    variant?: "default" | "secondary" | "outline" | "destructive" | "ghost";
    disabled?: boolean;
  }>(),
  { variant: "default" }
);
</script>

<template>
  <button :class="cn(buttonVariants({ variant }), $attrs.class)" :disabled="disabled">
    <slot />
  </button>
</template>
