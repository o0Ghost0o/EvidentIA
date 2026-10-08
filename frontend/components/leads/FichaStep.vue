<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import Button from "~/components/ui/Button.vue";
import Badge from "~/components/ui/Badge.vue";
import Card from "~/components/ui/Card.vue";
import { Alert, AlertDescription } from "~/components/ui/alert";
import ForceGraph, { type GraphNode, type GraphLink } from "~/components/ForceGraph.vue";
import EvidenceDetailModal from "~/components/EvidenceDetailModal.vue";
import { api } from "~/composables/useApi";
import { type ScoreResponse, evidenceLevelFrom, normaliseRol } from "~/lib/leadWizard";

// Step 4 "Ficha" of the new-lead workspace. The ficha is composed only from what
// has been linked: the relations graph is the real evidence tree (GET
// /cases/{id}/tree), and the rows are derived from the linked items, their roles,
// the entities in the tree and the deterministic score. "Qué falta" matters as
// much as what is there. Confirming the ficha unlocks the Borrador step; if the
// evidence changes after a confirmation, the ficha goes stale and must be
// confirmed again.
const props = withDefaults(
  defineProps<{ leadId: number; linkedIds: string[]; alcance: string; readonly?: boolean }>(),
  { readonly: false }
);
const emit = defineEmits<{
  (e: "back"): void;
  (e: "continue"): void;
  (e: "change", payload: { confirmed: boolean }): void;
}>();

const confirmed = ref(false);
const stale = ref(false);

interface CaseEvidence {
  id: number;
  fuente_tipo: string;
  fuente_id: string;
  rol: string;
  nota: string | null;
}
interface TreeNode { tipo: string; id: string; label: string }
interface TreeEdge {
  origen_tipo: string; origen_id: string;
  destino_tipo: string; destino_id: string;
  tipo: string; peso?: number;
}

const items = ref<CaseEvidence[]>([]);
const tree = ref<{ nodes: TreeNode[]; edges: TreeEdge[] } | null>(null);
const score = ref<ScoreResponse | null>(null);
const loading = ref(false);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [detail, treeRes, scoreRes] = await Promise.all([
      api<{ evidence: CaseEvidence[] }>(`cases/${props.leadId}`),
      api<{ nodes: TreeNode[]; edges: TreeEdge[] }>(`cases/${props.leadId}/tree`),
      api<ScoreResponse>(`cases/${props.leadId}/score`),
    ]);
    items.value = detail.evidence ?? [];
    tree.value = treeRes;
    score.value = scoreRes;
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "No se pudo componer la ficha.";
  } finally {
    loading.value = false;
  }
}

// --- Derived signals ------------------------------------------------------
const evLevel = computed(() => evidenceLevelFrom(score.value?.evidence_state, items.value.length));
const respaldo = computed(() => items.value.filter((e) => normaliseRol(e.rol) === "respaldo"));
const contra = computed(() => items.value.filter((e) => normaliseRol(e.rol) === "contradiccion"));
const primaries = computed(() => respaldo.value.filter((e) => e.fuente_tipo !== "news"));
const entityLabels = computed(() =>
  (tree.value?.nodes ?? []).filter((n) => n.tipo === "entity").map((n) => n.label)
);

const rows = computed(() => {
  const ev = evLevel.value;
  const insuf = ev === "insuficiente";
  const alc = props.alcance.trim();
  const sup = respaldo.value[0];
  const primList = primaries.value.length
    ? primaries.value.map((e) => e.fuente_id).join(", ")
    : respaldo.value.map((e) => e.fuente_id).slice(0, 3).join(", ");

  return [
    {
      label: "Qué se reporta",
      text: sup ? (sup.nota || sup.fuente_id) : "Sin afirmación respaldada.",
      cite: sup ? `[${sup.fuente_id}]` : "—",
      amber: false,
    },
    {
      label: "Quién",
      text: entityLabels.value.length
        ? entityLabels.value.slice(0, 4).join("; ")
        : alc
          ? `Actores de ${alc}.`
          : "Sin entidades resueltas en la evidencia vinculada.",
      cite: "—",
      amber: false,
    },
    {
      label: "Qué respalda",
      text: respaldo.value.length
        ? `${respaldo.value.length} fuente(s) respaldan${primList ? `: ${primList}` : ""}.`
        : "Sin fuentes que respalden la afirmación.",
      cite: "—",
      amber: false,
    },
    {
      label: "Qué falta",
      text:
        ev === "suficiente"
          ? contra.value.length
            ? "Respuesta formal a la versión contraria."
            : "Versión contraria: no hay fuente que contradiga vinculada."
          : ev === "parcial"
            ? "Una segunda fuente primaria que corrobore la cifra central."
            : "Fuente primaria (documento o indicador) para la cifra central.",
      cite: "—",
      amber: true,
    },
    {
      label: "Acción",
      text: insuf
        ? "Solicitar documentación antes de redactar, o abstenerse."
        : `Redactar nota explicativa${contra.value.length ? " con ambas versiones." : "."}`,
      cite: "—",
      amber: false,
    },
  ];
});

function confirm() {
  confirmed.value = true;
  stale.value = false;
  emit("change", { confirmed: true });
}

// --- Graph from the real evidence tree ------------------------------------
const showGraph = ref(true);
const modalOpen = ref(false);
const inspectedNode = ref<{ tipo: string; id: string } | null>(null);

function onGraphNodeClick(node: GraphNode) {
  // Tree node ids are "${tipo}:${id}"; recover the type and id for the modal.
  const [tipo, ...rest] = node.id.split(":");
  inspectedNode.value = { tipo: tipo || node.tipo || "news", id: rest.join(":") };
  modalOpen.value = true;
}

const fichaGraph = computed<{ nodes: GraphNode[]; links: GraphLink[] }>(() => {
  if (!tree.value) return { nodes: [], links: [] };
  const nodes: GraphNode[] = tree.value.nodes.map((n) => ({
    id: `${n.tipo}:${n.id}`,
    label: n.label,
    tipo: n.tipo,
  }));
  const links: GraphLink[] = tree.value.edges.map((e) => ({
    source: `${e.origen_tipo}:${e.origen_id}`,
    target: `${e.destino_tipo}:${e.destino_id}`,
    tipo: e.tipo,
  }));
  return { nodes, links };
});

// The ficha is built from the linked set: if that set changes after a
// confirmation, the ficha no longer reflects the evidence and must be re-confirmed.
watch(
  () => props.linkedIds,
  () => {
    if (confirmed.value) {
      confirmed.value = false;
      stale.value = true;
      emit("change", { confirmed: false });
    }
    void load();
  },
  { deep: true }
);

onMounted(load);
</script>

<template>
  <div class="flex flex-col gap-3">
    <Alert v-if="stale && !readonly" variant="warning">
      <AlertDescription class="text-body-sm leading-relaxed text-ink">
        <strong class="font-semibold text-warning">La evidencia cambió.</strong>
        Revisa y confirma la ficha de nuevo.
      </AlertDescription>
    </Alert>

    <p v-if="error" class="text-body-sm text-destructive">{{ error }}</p>

    <!-- Ficha · composed only from linked evidence -->
    <div class="overflow-hidden rounded-md border border-border">
      <div
        v-for="row in rows"
        :key="row.label"
        class="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-x-4 gap-y-1 border-b border-border px-4 py-3.5 last:border-b-0"
      >
        <span class="text-label uppercase" :class="row.amber ? 'text-warning' : 'text-ink-muted'">
          {{ row.label }}
        </span>
        <span class="text-pretty text-body-sm leading-relaxed [grid-column:span_2]">
          {{ row.text }}
          <span
            v-if="row.cite !== '—'"
            class="ml-0.5 whitespace-nowrap rounded-sm bg-surface-sunken px-1 font-mono text-caption text-ink-muted"
          >
            {{ row.cite }}
          </span>
        </span>
      </div>
    </div>

    <!-- Relations graph · the real evidence tree -->
    <Card class="mt-2">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <span class="font-serif text-sm font-semibold text-ink">Grafo de Relaciones de la Ficha</span>
            <Badge variant="outline" class="font-mono text-[11px] tabular-nums">
              {{ fichaGraph.nodes.length }} nodos · {{ fichaGraph.links.length }} conexiones
            </Badge>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-caption text-ink-muted hidden sm:inline">
              Haz clic en cualquier nodo para ver evidencia y citas
            </span>
            <Button variant="outline" size="sm" class="h-7 text-xs" @click="showGraph = !showGraph">
              {{ showGraph ? "Ocultar grafo" : "Mostrar grafo" }}
            </Button>
          </div>
        </div>
      </template>

      <div v-show="showGraph" class="space-y-3">
        <div v-if="loading" class="py-6 text-center text-body-sm text-ink-muted">Componiendo la ficha…</div>
        <div
          v-else-if="fichaGraph.nodes.length <= 1"
          class="py-6 text-center text-body-sm text-ink-muted"
        >
          No hay suficientes evidencias vinculadas para visualizar el grafo. Vincula fuentes en el paso anterior.
        </div>
        <div v-else class="space-y-2">
          <ForceGraph
            :nodes="fichaGraph.nodes"
            :links="fichaGraph.links"
            :show-controls="true"
            :show-legend="true"
            :initial-height="420"
            @node-click="onGraphNodeClick"
          />
        </div>
      </div>
    </Card>

    <!-- Modal to inspect evidence from the graph (real /evidence/item) -->
    <EvidenceDetailModal
      v-model:open="modalOpen"
      :tipo="inspectedNode?.tipo"
      :id="inspectedNode?.id"
      @navigate="(t, i) => { inspectedNode = { tipo: t, id: i }; modalOpen = true; }"
    />

    <!-- Footer nav -->
    <div v-if="!readonly" class="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
      <Button variant="outline" @click="emit('back')">← Atrás</Button>
      <Button v-if="confirmed" @click="emit('continue')">Continuar · Borrador →</Button>
      <Button v-else @click="confirm">Confirmar ficha</Button>
    </div>
  </div>
</template>
