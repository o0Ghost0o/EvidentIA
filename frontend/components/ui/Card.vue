<script setup lang="ts">
import { cn } from "~/lib/utils";
</script>

<template>
  <div :class="cn('rounded-lg border bg-card text-card-foreground shadow-sm', $attrs.class)">
    <div v-if="$slots.header" class="border-b px-4 py-3 font-semibold">
      <slot name="header" />
    </div>
    <div class="p-4">
      <slot />
    </div>
  </div>
</template>
