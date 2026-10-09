<script setup lang="ts">
import { cn } from "~/lib/utils";
</script>

<template>
  <div :class="cn('rounded-md border border-hairline bg-surface text-ink shadow-ev-1', $attrs.class)">
    <div v-if="$slots.header" class="border-b border-hairline px-4 md:px-6 py-3 md:py-3.5 font-semibold text-ink">
      <slot name="header" />
    </div>
    <div class="p-4 md:p-6">
      <slot />
    </div>
  </div>
</template>
