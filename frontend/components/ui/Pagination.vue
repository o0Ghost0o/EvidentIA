<script setup lang="ts">
import { computed } from "vue";
import { ChevronLeft, ChevronRight } from "lucide-vue-next";
import { cn } from "~/lib/utils";

const props = defineProps<{
  page: number;
  pageCount: number;
  total: number;
  rangeStart: number;
  rangeEnd: number;
}>();

const emit = defineEmits<{ "update:page": [value: number] }>();

// Build a compact page list with ellipses: always first and last, plus a window
// around the current page. `-1` marks an ellipsis gap.
const pages = computed<number[]>(() => {
  const count = props.pageCount;
  if (count <= 7) return Array.from({ length: count }, (_, i) => i + 1);
  const current = props.page;
  const out = new Set<number>([1, count, current, current - 1, current + 1]);
  const sorted = [...out].filter((p) => p >= 1 && p <= count).sort((a, b) => a - b);
  const result: number[] = [];
  let prev = 0;
  for (const p of sorted) {
    if (prev && p - prev > 1) result.push(-1);
    result.push(p);
    prev = p;
  }
  return result;
});

const atStart = computed(() => props.page <= 1);
const atEnd = computed(() => props.page >= props.pageCount);

function go(p: number) {
  if (p < 1 || p > props.pageCount || p === props.page) return;
  emit("update:page", p);
}

const navBtn =
  "inline-flex items-center justify-center h-8 min-w-8 px-2 rounded-md text-body-sm transition-colors disabled:opacity-40 disabled:pointer-events-none";
</script>

<template>
  <nav
    v-if="pageCount > 1"
    aria-label="Paginación"
    class="flex flex-wrap items-center justify-between gap-3 border-t border-hairline pt-3"
  >
    <p class="text-caption text-ink-muted tabular-nums">
      {{ rangeStart }}–{{ rangeEnd }} de {{ total }}
    </p>

    <div class="flex items-center gap-1">
      <button
        type="button"
        :class="cn(navBtn, 'border border-hairline bg-transparent text-ink-muted hover:bg-surface-sunken hover:text-ink')"
        :disabled="atStart"
        :aria-disabled="atStart"
        aria-label="Página anterior"
        @click="go(page - 1)"
      >
        <ChevronLeft class="h-4 w-4" />
      </button>

      <template v-for="(p, i) in pages" :key="`${p}-${i}`">
        <span v-if="p === -1" class="px-1 text-caption text-ink-muted select-none">…</span>
        <button
          v-else
          type="button"
          :class="cn(
            navBtn,
            'font-medium tabular-nums',
            p === page
              ? 'bg-primary text-on-primary'
              : 'text-ink-muted hover:bg-surface-sunken hover:text-ink'
          )"
          :aria-current="p === page ? 'page' : undefined"
          :aria-label="`Página ${p}`"
          @click="go(p)"
        >
          {{ p }}
        </button>
      </template>

      <button
        type="button"
        :class="cn(navBtn, 'border border-hairline bg-transparent text-ink-muted hover:bg-surface-sunken hover:text-ink')"
        :disabled="atEnd"
        :aria-disabled="atEnd"
        aria-label="Página siguiente"
        @click="go(page + 1)"
      >
        <ChevronRight class="h-4 w-4" />
      </button>
    </div>
  </nav>
</template>
