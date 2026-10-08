<script setup lang="ts">
import { cva } from "class-variance-authority";
import { cn } from "~/lib/utils";

// state-chip — the shared status vocabulary from DESIGN.md (state-system).
// Same tone always means the same thing: evidence sufficiency, priority band,
// review state. Pill radius, caption 600, optional 8px leading dot for dense rows.
// Tones map to the semantic tokens; `soft` tints the token, `outline` leaves the
// fill transparent (used for `insuficiente`, which must read as a warning outline).
const chipVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap",
  {
    variants: {
      tone: {
        success: "",
        warning: "",
        error: "",
        info: "",
        primary: "",
        neutral: "",
      },
      variant: { soft: "border", outline: "border" },
    },
    compoundVariants: [
      { tone: "success", variant: "soft", class: "bg-success/10 border-success/30 text-success" },
      { tone: "warning", variant: "soft", class: "bg-warning/10 border-warning/30 text-warning" },
      { tone: "error", variant: "soft", class: "bg-error/10 border-error/30 text-error" },
      { tone: "info", variant: "soft", class: "bg-info/10 border-info/30 text-info" },
      { tone: "primary", variant: "soft", class: "bg-primary-soft border-primary/25 text-primary" },
      { tone: "neutral", variant: "soft", class: "bg-surface-sunken border-hairline text-ink-muted" },
      { tone: "success", variant: "outline", class: "bg-transparent border-success text-success" },
      { tone: "warning", variant: "outline", class: "bg-transparent border-warning text-warning" },
      { tone: "error", variant: "outline", class: "bg-transparent border-error text-error" },
      { tone: "info", variant: "outline", class: "bg-transparent border-info text-info" },
      { tone: "primary", variant: "outline", class: "bg-transparent border-primary text-primary" },
      { tone: "neutral", variant: "outline", class: "bg-transparent border-hairline text-ink-muted" },
    ],
    defaultVariants: { tone: "neutral", variant: "soft" },
  }
);

withDefaults(
  defineProps<{
    tone?: "success" | "warning" | "error" | "info" | "primary" | "neutral";
    variant?: "soft" | "outline";
    dot?: boolean;
  }>(),
  { tone: "neutral", variant: "soft", dot: false }
);
</script>

<template>
  <span :class="cn(chipVariants({ tone, variant }), $attrs.class)">
    <span v-if="dot" class="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
    <slot />
  </span>
</template>
