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
        outline: "text-foreground",
        destructive: "bg-destructive text-destructive-foreground border-transparent",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

withDefaults(
  defineProps<{ variant?: "default" | "secondary" | "outline" | "destructive" }>(),
  { variant: "default" }
);
</script>

<template>
  <span :class="cn(badgeVariants({ variant }), $attrs.class)"><slot /></span>
</template>
