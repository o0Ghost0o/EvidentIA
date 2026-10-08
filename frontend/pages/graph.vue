<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Input from "~/components/ui/Input.vue";
import ForceGraph, { type GraphNode, type GraphLink } from "~/components/ForceGraph.vue";
import EvidenceDetailModal from "~/components/EvidenceDetailModal.vue";
import { api } from "~/composables/useApi";
import { GRAPH_TYPE_COLORS, GRAPH_TYPE_LABELS } from "~/utils/graph";

interface GraphResponse {
  nodes: GraphNode[];
  links: GraphLink[];
  total_nodes: number;
  total_links: number;
}

const loading = ref(true);
const error = ref<string | null>(null);
const allNodes = ref<GraphNode[]>([]);
const allLinks = ref<GraphLink[]>([]);

// Filter state
const filterType = ref<string>("all");
const searchQuery = ref<string>("");

// Modal inspection state
const modalOpen = ref(false);
const activeNode = ref<{ tipo: string; id: string } | null>(null);

async function loadGlobalGraph() {
  loading.value = true;
  error.value = null;
  try {
    const res = await api<GraphResponse>("evidence/graph", {
      query: { limit_relations: "400" },
    });
    allNodes.value = res.nodes;
    allLinks.value = res.links;
  } catch (err: any) {
    error.value = err?.message || "No se pudo cargar el grafo de conocimiento.";
  } finally {
    loading.value = false;
  }
}

const typeOptions = [
  { value: "all", label: "Todos los nodos" },
  { value: "news", label: "Noticias" },
  { value: "indicator", label: "Indicadores WB" },
  { value: "event", label: "Eventos Sísmicos" },
  { value: "entity", label: "Entidades" },
  { value: "case", label: "Leads Editoriales" },
];

const filteredNodes = computed(() => {
  let list = allNodes.value;
  if (filterType.value !== "all") {
    list = list.filter((n) => (n.tipo || "").toLowerCase() === filterType.value);
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim();
    list = list.filter(
      (n) =>
        (n.label || "").toLowerCase().includes(q) ||
        (n.id || "").toLowerCase().includes(q)
    );
  }
  return list;
});

const filteredLinks = computed(() => {
  const visibleIds = new Set(filteredNodes.value.map((n) => n.id));
  return allLinks.value.filter(
    (l) => visibleIds.has(l.source) && visibleIds.has(l.target)
  );
});

function onNodeClick(node: GraphNode) {
  const [tipo, ...idParts] = node.id.split(":");
  const idVal = node.ref || idParts.join(":");
  activeNode.value = { tipo, id: idVal };
  modalOpen.value = true;
}

// Counts by type
const countNews = computed(
  () => allNodes.value.filter((n) => n.tipo === "news").length
);
const countIndicators = computed(
  () => allNodes.value.filter((n) => n.tipo === "indicator").length
);
const countEvents = computed(
  () => allNodes.value.filter((n) => n.tipo === "event").length
);
const countEntities = computed(
  () => allNodes.value.filter((n) => n.tipo === "entity").length
);

onMounted(loadGlobalGraph);
</script>

<template>
  <div class="mx-auto max-w-container px-4 py-6 space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="space-y-1">
        <div class="flex items-center gap-1.5 text-caption text-ink-muted mb-1">
          <NuxtLink to="/" class="hover:text-ink transition-colors">Bandeja</NuxtLink>
          <span>/</span>
          <span class="text-ink">Red Global GraphRAG</span>
        </div>
        <h1 class="font-serif text-display-xl font-semibold tracking-tight text-ink">
          Grafo de Conocimiento y Evidencias
        </h1>
        <p class="text-body-sm text-ink-muted max-w-[72ch] leading-relaxed">
          Red interconectada de noticias verificadas, series del Banco Mundial, eventos USGS y entidades extraídas con física en tiempo real.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" :disabled="loading" class="h-9 text-body-sm" @click="loadGlobalGraph">
          <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Recargar red</span>
        </Button>
      </div>
    </div>

    <!-- Quick Stats Metric Tiles -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-body-sm">
      <div class="p-4 rounded-md border border-hairline bg-surface shadow-ev-1">
        <div class="text-label uppercase tracking-wider text-ink-muted font-semibold">Noticias de Prensa</div>
        <div class="text-display-lg font-semibold text-info mt-1 font-mono tabular-nums">
          {{ countNews }}
        </div>
        <div class="text-caption text-ink-muted mt-0.5">TVN Noticias + Feeds</div>
      </div>

      <div class="p-4 rounded-md border border-hairline bg-surface shadow-ev-1">
        <div class="text-label uppercase tracking-wider text-ink-muted font-semibold">Indicadores Oficiales</div>
        <div class="text-display-lg font-semibold text-success mt-1 font-mono tabular-nums">
          {{ countIndicators }}
        </div>
        <div class="text-caption text-ink-muted mt-0.5">World Bank Open Data</div>
      </div>

      <div class="p-4 rounded-md border border-hairline bg-surface shadow-ev-1">
        <div class="text-label uppercase tracking-wider text-ink-muted font-semibold">Eventos Geofísicos</div>
        <div class="text-display-lg font-semibold text-warning mt-1 font-mono tabular-nums">
          {{ countEvents }}
        </div>
        <div class="text-caption text-ink-muted mt-0.5">Sismos USGS</div>
      </div>

      <div class="p-4 rounded-md border border-hairline bg-surface shadow-ev-1">
        <div class="text-label uppercase tracking-wider text-ink-muted font-semibold">Entidades y Enlaces</div>
        <div class="text-display-lg font-semibold text-primary mt-1 font-mono tabular-nums">
          {{ countEntities }} / {{ allLinks.length }}
        </div>
        <div class="text-caption text-ink-muted mt-0.5">Grafo semántico</div>
      </div>
    </div>

    <!-- Filter & Search Bar -->
    <Card class="p-3.5">
      <div class="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        <!-- Type Filter Chips -->
        <div class="flex flex-wrap items-center gap-1.5">
          <button
            v-for="opt in typeOptions"
            :key="opt.value"
            type="button"
            class="px-2.5 py-1 rounded-md text-caption font-semibold border transition-colors cursor-pointer"
            :class="
              filterType === opt.value
                ? 'bg-primary text-on-primary border-primary shadow-ev-1'
                : 'bg-surface-sunken hover:bg-surface text-ink-muted hover:text-ink border-hairline'
            "
            @click="filterType = opt.value"
          >
            {{ opt.label }}
          </button>
        </div>

        <!-- Search Input -->
        <div class="w-full md:w-72">
          <Input
            v-model="searchQuery"
            placeholder="Buscar entidad, noticia o indicador…"
            class="text-mono font-mono h-9"
          />
        </div>
      </div>
    </Card>

    <!-- Graph Container -->
    <div v-if="loading" class="p-12 text-center rounded-md border border-hairline bg-surface text-ink-muted text-body-sm shadow-ev-1">
      <div class="flex items-center justify-center gap-2">
        <svg class="animate-spin h-5 w-5 text-primary" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
        </svg>
        <span>Inicializando simulación de fuerza dirigida para el grafo global…</span>
      </div>
    </div>

    <div v-else-if="error" class="p-6 rounded-md border border-error/30 bg-error/10 text-error text-body-sm">
      {{ error }}
    </div>

    <div v-else class="rounded-lg border border-hairline bg-surface-sunken p-1 shadow-ev-1 overflow-hidden">
      <ForceGraph
        :nodes="filteredNodes"
        :links="filteredLinks"
        :initial-height="620"
        @node-click="onNodeClick"
      />
    </div>

    <!-- 1-Click Evidence Inspection Modal -->
    <EvidenceDetailModal
      v-model:open="modalOpen"
      :tipo="activeNode?.tipo"
      :id="activeNode?.id"
      @navigate="(t, i) => { activeNode = { tipo: t, id: i }; modalOpen = true; }"
    />
  </div>
</template>
