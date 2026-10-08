<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Input from "~/components/ui/Input.vue";
import TreeBranch, { type Branch } from "~/components/TreeBranch.vue";
import EvidenceDetailModal from "~/components/EvidenceDetailModal.vue";

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
  (e: "inspectNode", node: TreeNode): void;
}>();

// Depth level state (default 5 levels per specification)
const selectedDepth = ref(props.depth || 5);
const searchQuery = ref("");
const expandAllKey = ref(0);
const allExpanded = ref(true);

// Modal state for viewing evidence node content on click
const modalOpen = ref(false);
const inspectedNode = ref<{ tipo: string; id: string } | null>(null);

function handleInspect(node: { tipo: string; id: string }) {
  inspectedNode.value = { tipo: node.tipo, id: node.id };
  modalOpen.value = true;
  emit("inspectNode", node as TreeNode);
}

function handleModalNavigate(tipo: string, id: string) {
  inspectedNode.value = { tipo, id };
  modalOpen.value = true;
}

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
  const rootNode = byKey.get(rootKey) || {
    tipo: props.tree.root.tipo,
    id: props.tree.root.id,
    label: `Lead ${props.tree.root.id}`,
  };

  // Build tree using DFS with cycle prevention
  function buildSubtree(
    currNode: TreeNode,
    currentLevel: number,
    via: string | null,
    visited: Set<string>
  ): Branch {
    const currKey = `${currNode.tipo}:${currNode.id}`;
    const nextVisited = new Set(visited);
    nextVisited.add(currKey);

    const children: Branch[] = [];
    if (currentLevel < selectedDepth.value) {
      const neighbors = adjacency.get(currKey) || [];
      for (const n of neighbors) {
        const neighborKey = `${n.other.tipo}:${n.other.id}`;
        if (!visited.has(neighborKey)) {
          // If search filter is active, optionally highlight or prune
          children.push(
            buildSubtree(n.other, currentLevel + 1, n.via, nextVisited)
          );
        }
      }
    }

    return {
      node: currNode,
      via,
      level: currentLevel,
      children,
    };
  }

  const rootBranch = buildSubtree(rootNode, 0, null, new Set());
  return [rootBranch];
});

const totalNodesCount = computed(() => props.tree?.nodes.length || 0);
const totalEdgesCount = computed(() => props.tree?.edges.length || 0);
</script>

<template>
  <Card>
    <template #header>
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <span class="font-bold text-base">Árbol de Evidencias y Trazabilidad</span>
            <Badge variant="outline" class="text-xs">Multi-nivel</Badge>
          </div>
          <p class="text-xs text-muted-foreground mt-0.5">
            Explora las cadenas de respaldo causal. Haz clic en cualquier nodo para inspeccionar su contenido o noticia original.
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
          * Haz clic en cualquier nodo para inspeccionar titular, enlace o valor oficial.
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
            @inspect="handleInspect"
          />
        </ul>
      </div>
    </div>

    <!-- Interactive Evidence Content Modal -->
    <EvidenceDetailModal
      v-model:open="modalOpen"
      :tipo="inspectedNode?.tipo"
      :id="inspectedNode?.id"
      @navigate="handleModalNavigate"
    />
  </Card>
</template>
