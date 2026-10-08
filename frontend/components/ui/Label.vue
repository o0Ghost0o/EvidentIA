<script setup lang="ts">
import { Label } from "reka-ui";
import { cn } from "~/lib/utils";

// Field label — matches DESIGN "label" role (uppercase, 13px/600, ink-muted).
// `for` associates it with an input via reka-ui's Label primitive.
defineProps<{ for?: string }>();
</script>

<template>
  <Label
    :for="$props.for"
    :class="cn('text-label uppercase text-ink-muted', $attrs.class)"
  >
    <slot />
  </Label>
</template>
