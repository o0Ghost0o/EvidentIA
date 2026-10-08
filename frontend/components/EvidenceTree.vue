<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Input from "~/components/ui/Input.vue";
import TreeBranch, { type Branch } from "~/components/TreeBranch.vue";
import EvidenceDetailModal from "~/components/EvidenceDetailModal.vue";
import ForceGraph, { type GraphNode, type GraphLink } from "~/components/ForceGraph.vue";

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

// Visual mode: 'tree' (hierarchical list) vs 'graph' (interactive force-directed GraphRAG)
const viewMode = ref<"tree" | "graph">("tree");

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

// Transform tree into GraphRAG nodes and links for ForceGraph
const graphNodes = computed<GraphNode[]>(() => {
  if (!props.tree) return [];
  return props.tree.nodes.map((n) => ({
    id: `${n.tipo}:${n.id}`,
    label: n.label,
    tipo: n.tipo,
    ref: n.id,
  }));
});

const graphLinks = computed<GraphLink[]>(() => {
  if (!props.tree) return [];
  return props.tree.edges.map((e) => ({
    source: `${e.origen_tipo}:${e.origen_id}`,
    target: `${e.destino_tipo}:${e.destino_id}`,
    tipo: e.tipo,
  }));
});

function handleGraphNodeClick(node: GraphNode) {
  const [tipo, ...rest] = node.id.split(":");
  const idVal = node.ref || rest.join(":");
  handleInspect({ tipo, id: idVal });
}

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
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <h3 class="font-serif text-heading-md font-semibold text-ink">Árbol de Evidencias y Trazabilidad</h3>
            <Badge variant="outline" class="text-caption font-medium">GraphRAG</Badge>
          </div>
          <p class="text-caption text-ink-muted mt-0.5 font-sans">
            Explora las cadenas de respaldo causal. Haz clic en cualquier nodo para inspeccionar su contenido original.
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <!-- View mode toggle: Tree vs Graph -->
          <div class="flex items-center rounded-md bg-surface-sunken p-0.5 border border-hairline text-caption font-sans">
            <button
              type="button"
              class="px-2.5 py-1 rounded-sm transition-colors flex items-center gap-1.5 cursor-pointer"
              :class="viewMode === 'tree' ? 'bg-surface text-ink font-semibold shadow-ev-1' : 'text-ink-muted hover:text-ink font-medium'"
              @click="viewMode = 'tree'"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h10M4 18h6" />
              </svg>
              <span>Árbol</span>
            </button>
            <button
              type="button"
              class="px-2.5 py-1 rounded-sm transition-colors flex items-center gap-1.5 cursor-pointer"
              :class="viewMode === 'graph' ? 'bg-surface text-ink font-semibold shadow-ev-1' : 'text-ink-muted hover:text-ink font-medium'"
              @click="viewMode = 'graph'"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Grafo Dinámico</span>
            </button>
          </div>

          <!-- Level Controls (visible in tree view) -->
          <div v-if="viewMode === 'tree'" class="flex flex-wrap items-center gap-1.5 border-l border-hairline pl-2">
            <span class="text-caption text-ink-muted mr-1">Niveles:</span>
            <Button
              size="sm"
              variant="outline"
              class="h-7 w-7 p-0 text-body-sm font-semibold"
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
                  'h-7 px-2 text-caption font-mono tabular-nums rounded border transition-colors cursor-pointer',
                  selectedDepth === d
                    ? 'bg-primary text-primary-foreground font-semibold border-primary shadow-ev-1'
                    : 'bg-surface hover:bg-surface-sunken text-ink-muted hover:text-ink border-hairline'
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
              class="h-7 w-7 p-0 text-body-sm font-semibold"
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
              class="h-7 px-2.5 text-caption ml-1"
              @click="toggleExpandAll"
            >
              {{ allExpanded ? 'Colapsar' : 'Expandir' }}
            </Button>
          </div>
        </div>
      </div>
    </template>

    <!-- Content / Tree presentation -->
    <div v-if="loading" class="py-6 text-center text-body-sm text-ink-muted">
      Cargando grafo de evidencias…
    </div>
    <div v-else-if="!tree || !branches.length" class="py-4 text-body-sm text-ink-muted">
      Sin árbol de evidencias para mostrar. Vincula fuentes o fichas de evidencia para comenzar el grafo.
    </div>
    <div v-else class="space-y-3">
      <!-- Quick Info Bar -->
      <div class="flex flex-wrap items-center justify-between text-caption text-ink-muted bg-surface-sunken/60 px-3 py-1.5 rounded-md border border-hairline font-sans">
        <div class="flex items-center gap-3">
          <span>Grafo: <strong class="font-mono tabular-nums text-ink font-semibold">{{ totalNodesCount }}</strong> nodo(s)</span>
          <span><strong class="font-mono tabular-nums text-ink font-semibold">{{ totalEdgesCount }}</strong> relación(es)</span>
          <span v-if="viewMode === 'tree'">Profundidad visual: <strong class="font-mono tabular-nums text-ink font-semibold">1 a {{ selectedDepth }} niveles</strong></span>
          <span v-else>Modo: <strong class="text-ink font-semibold">Fuerza dirigida SVG interactiva</strong></span>
        </div>
        <span class="text-[11px] italic">
          * Haz clic en cualquier nodo para inspeccionar titular, enlace o valor oficial.
        </span>
      </div>

      <!-- Mode 1: EvidentIA Native Force-Directed GraphRAG -->
      <div v-if="viewMode === 'graph'" class="w-full">
        <ForceGraph
          :nodes="graphNodes"
          :links="graphLinks"
          :initial-height="520"
          @node-click="handleGraphNodeClick"
        />
      </div>

      <!-- Mode 2: Hierarchical Tree List -->
      <div v-else class="rounded-md border border-hairline bg-surface p-3 overflow-x-auto">
        <ul :key="expandAllKey" class="text-body-sm space-y-1">
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
