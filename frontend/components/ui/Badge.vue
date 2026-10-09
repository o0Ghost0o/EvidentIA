<script setup lang="ts">
import { cva } from "class-variance-authority";
import { cn } from "~/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      variant: {
        default: "bg-primary text-on-primary border-transparent",
        secondary: "bg-surface-sunken text-ink-muted border-hairline",
        outline: "text-ink border-hairline bg-transparent",
        destructive: "bg-error/15 text-error border-error/30",
        success: "bg-success/15 text-success border-success/30",
        warning: "bg-warning/15 text-warning border-warning/30",
        info: "bg-info/15 text-info border-info/30",
        purple: "bg-primary-soft text-primary border-primary/25",
        teal: "bg-success/15 text-success border-success/30",
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
