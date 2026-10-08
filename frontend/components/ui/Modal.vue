<script setup lang="ts">
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from "reka-ui";
import { cn } from "~/lib/utils";

// Centered modal dialog on Reka UI primitives (same convention as Sheet.vue).
const open = defineModel<boolean>("open", { default: false });
withDefaults(
  defineProps<{ title?: string; description?: string; widthClass?: string }>(),
  { widthClass: "w-full max-w-[640px]" }
);
</script>

<template>
  <DialogRoot v-model:open="open">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 z-50 bg-ink/40 backdrop-blur-[1px]" />
      <div class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto p-4 sm:p-6">
        <DialogContent
          :class="
            cn(
              'relative my-auto flex max-h-[calc(100vh-48px)] flex-col overflow-hidden rounded-lg border border-border bg-surface shadow-ev-3 focus:outline-none',
              widthClass
            )
          "
        >
          <div class="flex items-start justify-between gap-4 border-b border-border px-5 py-4">
            <div class="flex min-w-0 flex-col gap-1">
              <DialogTitle v-if="title" class="font-serif text-heading-md text-ink">{{ title }}</DialogTitle>
              <DialogDescription v-if="description" class="text-caption text-ink-muted">
                {{ description }}
              </DialogDescription>
            </div>
            <DialogClose
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-surface-sunken focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/25"
              aria-label="Cerrar"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </DialogClose>
          </div>
          <div class="min-h-0 flex-1 overflow-y-auto">
            <slot />
          </div>
          <div v-if="$slots.footer" class="border-t border-border px-5 py-4">
            <slot name="footer" />
          </div>
        </DialogContent>
      </div>
    </DialogPortal>
  </DialogRoot>
</template>
