<script setup lang="ts">
import { ref } from "vue";
import Badge from "~/components/ui/Badge.vue";

export interface Branch {
  node: { tipo: string; id: string; label: string };
  via: string | null;
  level: number;
  children: Branch[];
}

const props = withDefaults(
  defineProps<{
    branch: Branch;
    maxLevel?: number;
    defaultExpanded?: boolean;
  }>(),
  {
    maxLevel: 5,
    defaultExpanded: true,
  }
);

const emit = defineEmits<{
  (e: "inspect", node: { tipo: string; id: string; label: string }): void;
}>();

const isExpanded = ref(props.defaultExpanded);

function toggleExpand() {
  isExpanded.value = !isExpanded.value;
}

function onInspectNode() {
  emit("inspect", props.branch.node);
}

function nodeTypeBadge(tipo: string): { label: string; variant: "default" | "secondary" | "outline" | "destructive" | "success" | "warning" | "info" } {
  switch (tipo) {
    case "case":
      return { label: "Lead Principal", variant: "default" };
    case "news":
      return { label: "Ficha Noticia", variant: "info" };
    case "entity":
      return { label: "Entidad", variant: "secondary" };
    case "indicator":
      return { label: "Indicador WB", variant: "info" };
    case "event":
      return { label: "Evento Sísmico", variant: "warning" };
    default:
      return { label: tipo, variant: "secondary" };
  }
}

function relationLabel(via: string | null): string {
  if (!via) return "";
  const map: Record<string, string> = {
    has_evidence: "Evidencia vinculada",
    mentions: "Menciona entidad",
    same_event: "Mismo evento",
    source_of: "Fuente / Agencia",
    contradicts: "Contradice datos",
    corroborates: "Corrobora",
  };
  return map[via] || via;
}

function levelBadgeVariant(level: number): "outline" | "secondary" | "info" | "warning" | "default" {
  if (level === 1) return "outline";
  if (level === 2) return "secondary";
  if (level === 3) return "info";
  if (level === 4) return "warning";
  if (level >= 5) return "default";
  return "outline";
}
</script>

<template>
  <li class="relative ml-2 border-l-2 border-hairline pl-3 py-1.5 transition-colors">
    <div class="flex flex-wrap items-center gap-2 group">
      <!-- Expand/collapse button if has visible children -->
      <button
        v-if="branch.children.length && branch.level < maxLevel"
        type="button"
        class="flex h-5 w-5 items-center justify-center rounded border border-hairline bg-surface text-[11px] font-bold text-ink-muted hover:bg-surface-sunken hover:text-ink shadow-ev-1 cursor-pointer transition-colors"
        :title="isExpanded ? 'Colapsar rama' : 'Expandir rama'"
        @click="toggleExpand"
      >
        {{ isExpanded ? "−" : "+" }}
      </button>
      <span v-else-if="branch.level > 0" class="inline-block w-2 h-0.5 bg-hairline"></span>

      <!-- Level badge -->
      <Badge
        v-if="branch.level > 0"
        :variant="levelBadgeVariant(branch.level)"
        class="text-[10px] px-1.5 py-0 font-mono tracking-tight"
      >
        L{{ branch.level }}
      </Badge>

      <!-- Node type badge -->
      <Badge :variant="nodeTypeBadge(branch.node.tipo).variant" class="text-caption">
        {{ nodeTypeBadge(branch.node.tipo).label }}
      </Badge>

      <!-- Clickable Label & Inspection Button -->
      <button
        type="button"
        class="inline-flex items-center gap-1.5 text-left rounded-md px-1.5 py-0.5 hover:bg-surface-sunken transition-colors cursor-pointer group/node"
        title="Clic para inspeccionar el contenido de esta evidencia"
        @click="onInspectNode"
      >
        <span class="font-medium text-ink group-hover/node:text-primary text-body-sm tracking-tight break-all">
          {{ branch.node.label }}
        </span>
        <svg
          class="w-3.5 h-3.5 text-ink-muted opacity-60 group-hover/node:opacity-100 group-hover/node:text-primary shrink-0 transition-opacity"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      </button>

      <!-- Identifier pill -->
      <span class="font-mono text-mono tabular-nums text-[11px] text-ink-muted bg-surface-sunken border border-hairline px-1 rounded-sm">
        {{ branch.node.id }}
      </span>

      <!-- Relation edge note -->
      <span v-if="branch.via" class="text-caption text-ink-muted flex items-center gap-1">
        <span>←</span>
        <span class="italic text-[11px]">{{ relationLabel(branch.via) }}</span>
      </span>

      <!-- Child count badge if collapsed -->
      <span
        v-if="branch.children.length && (!isExpanded || branch.level >= maxLevel)"
        class="text-caption text-ink-muted bg-surface-sunken border border-hairline px-1.5 py-0.5 rounded-pill font-mono tabular-nums"
      >
        ({{ branch.children.length }} sub-conexiones{{ branch.level >= maxLevel ? " [límite nivel]" : "" }})
      </span>
    </div>

    <!-- Children rendered hierarchically up to maxLevel -->
    <ul
      v-if="branch.children.length && isExpanded && branch.level < maxLevel"
      class="mt-1 space-y-1"
    >
      <TreeBranch
        v-for="(child, idx) in branch.children"
        :key="`${child.node.tipo}-${child.node.id}-${idx}`"
        :branch="child"
        :max-level="maxLevel"
        :default-expanded="defaultExpanded"
        @inspect="(n) => emit('inspect', n)"
      />
    </ul>
  </li>
</template>
