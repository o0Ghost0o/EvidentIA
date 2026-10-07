<script setup lang="ts">
import { cva } from "class-variance-authority";
import { cn } from "~/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground border-transparent",
        secondary: "bg-secondary text-secondary-foreground border-transparent",
        outline: "text-foreground border-border",
        destructive: "bg-destructive text-destructive-foreground border-transparent",
        success: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
        warning: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30",
        info: "bg-sky-500/15 text-sky-700 dark:text-sky-300 border-sky-500/30",
        purple: "bg-purple-500/15 text-purple-700 dark:text-purple-300 border-purple-500/30",
        teal: "bg-teal-500/15 text-teal-700 dark:text-teal-300 border-teal-500/30",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

withDefaults(
  defineProps<{
    variant?:
      | "default"
      | "secondary"
      | "outline"
      | "destructive"
      | "success"
      | "warning"
      | "info"
      | "purple"
      | "teal";
  }>(),
  { variant: "default" }
);
</script>

<template>
  <span :class="cn(badgeVariants({ variant }), $attrs.class)"><slot /></span>
</template>
