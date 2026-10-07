<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Input from "~/components/ui/Input.vue";
import TreeBranch, { type Branch } from "~/components/TreeBranch.vue";

export interface TreeNode {
  tipo: string;
  id: string;
  label: string;
}
export interface TreeEdge {
  origen_tipo: string;
  origen_id: string;
  destino_tipo: string;
  destino_id: string;
  tipo: string;
}
export interface EvidenceTreeData {
  root: { tipo: string; id: string };
  nodes: TreeNode[];
  edges: TreeEdge[];
}

const props = withDefaults(
  defineProps<{
    tree: EvidenceTreeData | null;
    depth?: number;
    loading?: boolean;
  }>(),
  {
    depth: 5,
    loading: false,
  }
);

const emit = defineEmits<{
  (e: "changeDepth", newDepth: number): void;
}>();

// Depth level state (default 5 levels per specification)
const selectedDepth = ref(props.depth || 5);
const searchQuery = ref("");
const expandAllKey = ref(0);
const allExpanded = ref(true);

watch(
  () => props.depth,
  (newVal) => {
    if (newVal && newVal !== selectedDepth.value) {
      selectedDepth.value = newVal;
    }
  }
);

function setDepth(level: number) {
  if (level < 1 || level > 10) return;
  selectedDepth.value = level;
  emit("changeDepth", level);
}

function increaseDepth() {
  if (selectedDepth.value < 10) {
    setDepth(selectedDepth.value + 1);
  }
}

function decreaseDepth() {
  if (selectedDepth.value > 1) {
    setDepth(selectedDepth.value - 1);
  }
}

function toggleExpandAll() {
  allExpanded.value = !allExpanded.value;
  expandAllKey.value += 1;
}

const PRESET_DEPTHS = [1, 2, 3, 4, 5, 6, 7, 8, 10];

const branches = computed<Branch[]>(() => {
  if (!props.tree) return [];
  const byKey = new Map(props.tree.nodes.map((n) => [`${n.tipo}:${n.id}`, n]));

  // Build graph adjacency list
  const adjacency = new Map<string, { other: TreeNode; via: string }[]>();
  for (const e of props.tree.edges) {
    const from = `${e.origen_tipo}:${e.origen_id}`;
    const to = `${e.destino_tipo}:${e.destino_id}`;
    const toNode = byKey.get(to);
    const fromNode = byKey.get(from);

    if (toNode) {
      if (!adjacency.has(from)) adjacency.set(from, []);
      adjacency.get(from)!.push({ other: toNode, via: e.tipo });
    }
    // Also bidirectional so relations stored in either direction are reachable
    if (fromNode && e.origen_tipo !== "case") {
      if (!adjacency.has(to)) adjacency.set(to, []);
      adjacency.get(to)!.push({ other: fromNode, via: e.tipo });
    }
  }

  const rootKey = `${props.tree.root.tipo}:${props.tree.root.id}`;
  const root = byKey.get(rootKey);
  if (!root) return [];

  const visited = new Set<string>([rootKey]);

  const build = (node: TreeNode, via: string | null, level: number): Branch => {
    const key = `${node.tipo}:${node.id}`;
    const kids: Branch[] = [];

    // Traverse down up to selectedDepth
    if (level < selectedDepth.value) {
      const neighbors = adjacency.get(key) || [];
      for (const { other, via: edgeVia } of neighbors) {
        const ck = `${other.tipo}:${other.id}`;
        if (visited.has(ck)) continue;
        visited.add(ck);
        kids.push(build(other, edgeVia, level + 1));
      }
    }
    return { node, via, level, children: kids };
  };

  return [build(root, null, 0)];
});

// Count total nodes in graph
const totalNodesCount = computed(() => props.tree?.nodes?.length || 0);
const totalEdgesCount = computed(() => props.tree?.edges?.length || 0);
</script>

<template>
  <Card>
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="space-y-0.5">
          <div class="flex items-center gap-2">
            <h2 class="text-base font-semibold">Árbol Jerárquico de Evidencia</h2>
            <Badge variant="outline" class="font-mono text-xs">
              {{ selectedDepth }} niveles {{ selectedDepth === 5 ? '(por defecto)' : '' }}
            </Badge>
          </div>
          <p class="text-xs text-muted-foreground">
            Despliegue multi-nivel de fuentes, entidades y correlaciones (hasta 5 niveles por defecto).
          </p>
        </div>

        <!-- Level Controls -->
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="text-xs text-muted-foreground mr-1">Niveles:</span>
          <Button
            size="sm"
            variant="outline"
            class="h-7 w-7 p-0 text-sm font-bold"
            :disabled="selectedDepth <= 1"
            title="Reducir nivel de profundidad"
            @click="decreaseDepth"
          >
            −
          </Button>

          <!-- Level Presets -->
          <div class="flex items-center gap-1">
            <button
              v-for="d in PRESET_DEPTHS"
              :key="d"
              type="button"
              :class="[
                'h-7 px-2 text-xs rounded border transition-colors',
                selectedDepth === d
                  ? 'bg-primary text-primary-foreground font-semibold border-primary shadow-xs'
                  : 'bg-background hover:bg-muted text-muted-foreground border-border'
              ]"
              :title="`Ver hasta ${d} nivel(es)`"
              @click="setDepth(d)"
            >
              {{ d }}{{ d === 5 ? '*' : '' }}
            </button>
          </div>

          <Button
            size="sm"
            variant="outline"
            class="h-7 w-7 p-0 text-sm font-bold"
            :disabled="selectedDepth >= 10"
            title="Aumentar nivel de profundidad"
            @click="increaseDepth"
          >
            +
          </Button>

          <!-- Expand / Collapse All Toggle -->
          <Button
            size="sm"
            variant="outline"
            class="h-7 px-2.5 text-xs ml-2"
            @click="toggleExpandAll"
          >
            {{ allExpanded ? 'Colapsar todo' : 'Expandir todo' }}
          </Button>
        </div>
      </div>
    </template>

    <!-- Content / Tree presentation -->
    <div v-if="loading" class="py-6 text-center text-sm text-muted-foreground">
      Cargando árbol de evidencias…
    </div>
    <div v-else-if="!tree || !branches.length" class="py-4 text-sm text-muted-foreground">
      Sin árbol de evidencias para mostrar. Vincula fuentes o fichas de evidencia para comenzar el grafo.
    </div>
    <div v-else class="space-y-3">
      <!-- Quick Info Bar -->
      <div class="flex flex-wrap items-center justify-between text-xs text-muted-foreground bg-muted/30 px-3 py-1.5 rounded-md border border-border/50">
        <div class="flex items-center gap-3">
          <span>Grafo: <strong>{{ totalNodesCount }}</strong> nodo(s)</span>
          <span><strong>{{ totalEdgesCount }}</strong> relación(es)</span>
          <span>Profundidad visual: <strong>1 a {{ selectedDepth }} niveles</strong></span>
        </div>
        <span class="text-[11px] italic">
          * Nivel 5 es el estándar por defecto. Usa los botones superiores para ajustar.
        </span>
      </div>

      <!-- Tree list -->
      <div class="rounded-md border bg-card/50 p-3 overflow-x-auto">
        <ul :key="expandAllKey" class="text-sm space-y-1">
          <TreeBranch
            v-for="(b, i) in branches"
            :key="`${b.node.tipo}-${b.node.id}-${i}`"
            :branch="b"
            :max-level="selectedDepth"
            :default-expanded="allExpanded"
          />
        </ul>
      </div>
    </div>
  </Card>
</template>
