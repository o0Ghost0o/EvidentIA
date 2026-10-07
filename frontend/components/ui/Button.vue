<script setup lang="ts">
import { cva } from "class-variance-authority";
import { cn } from "~/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 h-9 px-4 py-2",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        outline: "border border-border bg-background hover:bg-accent",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

withDefaults(
  defineProps<{
    variant?: "default" | "secondary" | "outline" | "destructive";
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
