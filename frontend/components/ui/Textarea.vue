<script setup lang="ts">
import { cn } from "~/lib/utils";

const model = defineModel<string>({ default: "" });
defineProps<{ placeholder?: string; rows?: number }>();
</script>

<template>
  <textarea
    v-model="model"
    :rows="rows || 3"
    :placeholder="placeholder"
    :class="cn('flex w-full rounded-md border bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary', $attrs.class)"
  />
</template>
