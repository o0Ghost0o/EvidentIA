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

const isExpanded = ref(props.defaultExpanded);

function toggleExpand() {
  isExpanded.value = !isExpanded.value;
}

function nodeTypeBadge(tipo: string): { label: string; variant: "default" | "secondary" | "outline" | "destructive" | "success" | "warning" | "info" | "purple" | "teal" } {
  switch (tipo) {
    case "case":
      return { label: "Lead Principal", variant: "default" };
    case "news":
      return { label: "Ficha Noticia", variant: "info" };
    case "entity":
      return { label: "Entidad", variant: "purple" };
    case "indicator":
      return { label: "Indicador WB", variant: "teal" };
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

function levelBadgeVariant(level: number) {
  if (level === 1) return "outline";
  if (level === 2) return "secondary";
  if (level === 3) return "info";
  if (level === 4) return "purple";
  if (level >= 5) return "teal";
  return "outline";
}
</script>

<template>
  <li class="relative ml-2 border-l-2 border-border/70 pl-3 py-1.5 transition-colors">
    <div class="flex flex-wrap items-center gap-2 group">
      <!-- Expand/collapse button if has visible children -->
      <button
        v-if="branch.children.length && branch.level < maxLevel"
        type="button"
        class="flex h-5 w-5 items-center justify-center rounded border bg-background text-[11px] font-bold text-muted-foreground hover:bg-muted hover:text-foreground shadow-xs"
        :title="isExpanded ? 'Colapsar rama' : 'Expandir rama'"
        @click="toggleExpand"
      >
        {{ isExpanded ? "−" : "+" }}
      </button>
      <span v-else-if="branch.level > 0" class="inline-block w-2 h-0.5 bg-border/80"></span>

      <!-- Level badge -->
      <Badge
        v-if="branch.level > 0"
        :variant="levelBadgeVariant(branch.level)"
        class="text-[10px] px-1.5 py-0 font-mono tracking-tight"
      >
        L{{ branch.level }}
      </Badge>

      <!-- Node type badge -->
      <Badge :variant="nodeTypeBadge(branch.node.tipo).variant" class="text-xs">
        {{ nodeTypeBadge(branch.node.tipo).label }}
      </Badge>

      <!-- Label -->
      <span class="font-medium text-foreground text-sm tracking-tight break-all">
        {{ branch.node.label }}
      </span>

      <!-- Identifier pill -->
      <span class="font-mono text-[11px] text-muted-foreground bg-muted/60 px-1 rounded">
        {{ branch.node.id }}
      </span>

      <!-- Relation edge note -->
      <span v-if="branch.via" class="text-xs text-muted-foreground flex items-center gap-1">
        <span>←</span>
        <span class="italic text-[11px]">{{ relationLabel(branch.via) }}</span>
      </span>

      <!-- Child count badge if collapsed -->
      <span
        v-if="branch.children.length && (!isExpanded || branch.level >= maxLevel)"
        class="text-[11px] text-muted-foreground/80 bg-muted/40 px-1.5 py-0.5 rounded-full"
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
      />
    </ul>
  </li>
</template>
