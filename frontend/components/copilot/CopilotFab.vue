<script setup lang="ts">
import { computed } from "vue";
import { Sparkles, Loader2 } from "lucide-vue-next";
import { useCopilot } from "~/composables/useCopilot";

const { isOpen, toggle, status } = useCopilot();

const isBusy = computed(() => status.value === "streaming" || status.value === "submitted");
</script>

<template>
  <div
    class="fixed bottom-6 right-6 z-40 transition-all duration-300 ease-out"
    :class="isOpen ? 'pointer-events-none scale-90 opacity-0 translate-y-2' : 'scale-100 opacity-100 translate-y-0'"
  >
    <button
      type="button"
      class="group relative flex items-center gap-2.5 rounded-full bg-primary px-4 py-2.5 text-on-primary shadow-ev-3 border border-white/15 transition-all duration-200 hover:-translate-y-0.5 hover:bg-primary-deep hover:shadow-xl active:translate-y-0 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
      aria-label="Abrir Copiloto Editorial (Atajo: ⌘K)"
      title="Copiloto Editorial (⌘K)"
      @click="toggle"
    >
      <!-- Activity pulse dot -->
      <span
        v-if="isBusy"
        class="absolute -top-1 -right-1 flex h-3 w-3"
      >
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
        <span class="relative inline-flex rounded-full h-3 w-3 bg-accent" />
      </span>

      <!-- Icon with animation when busy -->
      <div class="flex h-5 w-5 items-center justify-center">
        <Loader2 v-if="isBusy" class="h-4 w-4 animate-spin text-on-primary" />
        <Sparkles
          v-else
          class="h-4 w-4 text-on-primary transition-transform duration-300 group-hover:rotate-12 group-hover:scale-110"
        />
      </div>

      <!-- Editorial label -->
      <span class="font-sans text-body-sm font-semibold tracking-tight text-on-primary select-none">
        Copiloto
      </span>

      <!-- Monospace keyboard shortcut badge -->
      <span
        class="hidden sm:inline-flex items-center rounded-sm bg-white/20 px-1.5 py-0.5 font-mono text-[10px] font-medium text-on-primary/95 select-none"
      >
        ⌘K
      </span>
    </button>
  </div>
</template>
