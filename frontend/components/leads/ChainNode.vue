<script setup lang="ts">
import { ref } from "vue";

// One node of the evidence-chain tree. Recursive: a node renders its own row plus,
// when expanded, its children (the next sublevel) indented beneath it. Mirrors the
// design where each level toggles open to reveal the one below.
export interface ChainTreeNode {
  tipo: string;
  id: string;
  label: string;
  /** Relation code to the parent (edge tipo), empty for roots of the walk. */
  rel: string;
  relLabel: string;
  children: ChainTreeNode[];
}

const props = withDefaults(
  defineProps<{ node: ChainTreeNode; depth?: number }>(),
  { depth: 1 }
);
const emit = defineEmits<{ (e: "inspect", tipo: string, id: string): void }>();

// The first ring stays open so the tree reads at a glance; deeper rings start
// collapsed and the reporter toggles them.
const expanded = ref(props.depth <= 1);

const KIND_TONE: Record<string, string> = {
  news: "text-info bg-info/10",
  indicator: "text-teal-700 dark:text-teal-300 bg-teal-500/15",
  event: "text-warning bg-warning/10",
  entity: "text-purple-700 dark:text-purple-300 bg-purple-500/15",
  case: "text-primary bg-primary-soft",
};
const KIND_LABEL: Record<string, string> = {
  news: "Noticia",
  indicator: "Indicador",
  event: "Evento",
  entity: "Entidad",
  case: "Caso",
};
function kindTone(tipo: string) {
  return KIND_TONE[tipo] ?? "text-ink-muted bg-surface-sunken";
}
function relClass(rel: string) {
  if (rel === "contradicts") return "text-destructive border-destructive/40 bg-destructive/10";
  if (rel === "corroborates") return "text-success border-success/40 bg-success/10";
  return "text-ink-muted border-border bg-surface";
}
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <div class="flex items-start gap-1.5">
      <!-- Toggle (only when there are children) -->
      <button
        v-if="node.children.length"
        type="button"
        class="mt-2 flex h-5 w-5 shrink-0 items-center justify-center rounded-sm font-mono text-caption text-ink-muted transition-colors hover:bg-surface-sunken"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        {{ expanded ? "▾" : "▸" }}
      </button>
      <span v-else class="mt-2 h-5 w-5 shrink-0" aria-hidden="true" />

      <!-- Node row -->
      <button
        type="button"
        class="flex min-w-0 flex-1 flex-col gap-1 rounded-md border bg-surface px-3 py-2 text-left transition-shadow hover:shadow-ev-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/25"
        :class="node.rel === 'contradicts' ? 'border-destructive/50' : 'border-border'"
        @click="emit('inspect', node.tipo, node.id)"
      >
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="kindTone(node.tipo)">
            {{ KIND_LABEL[node.tipo] ?? node.tipo }}
          </span>
          <span class="font-mono text-caption text-ink-muted">{{ node.id }}</span>
          <span
            v-if="node.relLabel"
            class="rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase"
            :class="relClass(node.rel)"
          >
            {{ node.relLabel }}
          </span>
          <span v-if="node.children.length" class="font-mono text-[10px] text-ink-muted">
            · {{ node.children.length }}
          </span>
        </div>
        <span class="text-caption leading-snug">{{ node.label }}</span>
      </button>
    </div>

    <!-- Children (next sublevel), indented -->
    <div v-if="expanded && node.children.length" class="ml-[10px] flex flex-col gap-1.5 border-l border-border pl-2">
      <ChainNode
        v-for="child in node.children"
        :key="`${child.tipo}:${child.id}`"
        :node="child"
        :depth="depth + 1"
        @inspect="(t, i) => emit('inspect', t, i)"
      />
    </div>
  </div>
</template>
