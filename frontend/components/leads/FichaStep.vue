<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Button from "~/components/ui/Button.vue";
import Badge from "~/components/ui/Badge.vue";
import Card from "~/components/ui/Card.vue";
import { Alert, AlertDescription } from "~/components/ui/alert";
import ForceGraph, { type GraphNode, type GraphLink } from "~/components/ForceGraph.vue";
import EvidenceDetailModal from "~/components/EvidenceDetailModal.vue";
import {
  deriveEvidence,
  CLAIM,
  PROVENANCE,
  PROV_REL,
  SUB,
  NODES,
  CATALOG,
} from "~/lib/leadEvidence";

// Step 4 "Ficha" of the new-lead workspace. The ficha is composed only from what
// has been linked: "Qué falta" matters as much as what is there. Confirming the
// ficha is the gate that unlocks the Borrador step. If the evidence changes after
// a confirmation, the ficha goes stale and must be confirmed again.
const props = withDefaults(
  defineProps<{ linkedIds: string[]; alcance: string; readonly?: boolean }>(),
  { readonly: false }
);
const emit = defineEmits<{
  (e: "back"): void;
  (e: "continue"): void;
  (e: "change", payload: { confirmed: boolean }): void;
}>();

const confirmed = ref(false);
const stale = ref(false);

const derived = computed(() => deriveEvidence(props.linkedIds));

// Ficha rows, derived from the linked set exactly as the Lead Workspace design
// composes them. Only "Qué falta" carries the amber label; the rest stay muted.
const rows = computed(() => {
  const linked = derived.value.linked;
  const sup = linked.filter((s) => s.rel === "Respalda");
  const con = linked.filter((s) => s.rel === "Contradice");
  const primaries = linked.filter((s) => s.rel === "Respalda" && s.type !== "Noticia");
  const primN = derived.value.primN;
  const ev = derived.value.state.key;
  const insuf = ev === "insuficiente";
  const alc = props.alcance.trim();

  return [
    {
      label: "Qué se reporta",
      text: sup[0] ? sup[0].s : "Sin afirmación respaldada.",
      cite: sup[0] ? `[${sup[0].id}:${sup[0].c}]` : "—",
      amber: false,
    },
    {
      label: "Quién",
      text: `Hogares y comercios de ${alc || "la zona"}; distribuidora; ente regulador.`,
      cite: "—",
      amber: false,
    },
    {
      label: "Qué respalda",
      text: primN
        ? `${primN} ${primN === 1 ? "fuente primaria" : "fuentes primarias"}: ${primaries.map((s) => s.id).join(", ")}.`
        : "Solo testimonios en prensa; sin fuente primaria.",
      cite: "—",
      amber: false,
    },
    {
      label: "Qué falta",
      text:
        ev === "suficiente"
          ? con.length
            ? "Respuesta formal del ente regulador a la versión contraria."
            : "Versión de la distribuidora: no hay fuente contraria vinculada."
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
        : `Redactar nota explicativa${con.length ? " con ambas versiones." : "."}`,
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

// The ficha is built from the linked set: if that set changes after a
// confirmation, the ficha no longer reflects the evidence and must be re-confirmed.
// Interactive Graph state & computation for the Ficha
const showGraph = ref(true);
const modalOpen = ref(false);
const inspectedNode = ref<{ tipo: string; id: string } | null>(null);

function onGraphNodeClick(node: GraphNode) {
  let tipo = node.tipo || "news";
  if (tipo === "caso") tipo = "case";
  else if (tipo === "noticia") tipo = "news";
  else if (tipo === "indicador") tipo = "indicator";
  else if (tipo === "evento") tipo = "event";
  else if (tipo === "entidad" || tipo === "procedencia" || tipo === "correlación") tipo = "entity";

  inspectedNode.value = { tipo, id: node.id };
  modalOpen.value = true;
}

const fichaGraph = computed(() => {
  const nodesMap = new Map<string, GraphNode>();
  const links: GraphLink[] = [];
  const addedLinks = new Set<string>();

  const rootId = "lead-claim";
  nodesMap.set(rootId, {
    id: rootId,
    label: CLAIM,
    tipo: "caso",
  });

  const linked = derived.value.linked;
  for (const src of linked) {
    nodesMap.set(src.id, {
      id: src.id,
      label: src.title,
      tipo: src.type.toLowerCase(),
    });

    const linkKey1 = `${rootId}->${src.id}`;
    if (!addedLinks.has(linkKey1)) {
      links.push({ source: rootId, target: src.id, tipo: src.rel });
      addedLinks.add(linkKey1);
    }

    const provId = src.p;
    const prov = PROVENANCE[provId];
    if (prov) {
      nodesMap.set(provId, {
        id: provId,
        label: prov.t,
        tipo: "procedencia",
      });
      const linkKey2 = `${src.id}->${provId}`;
      if (!addedLinks.has(linkKey2)) {
        links.push({ source: src.id, target: provId, tipo: PROV_REL[provId] || "Contexto" });
        addedLinks.add(linkKey2);
      }

      const walk = (entries: any[], parentId: string) => {
        for (const [subId, subRel, kids] of entries) {
          const nodeInfo =
            NODES[subId] ||
            (CATALOG.find((c) => c.id === subId)
              ? { k: "noticia", t: CATALOG.find((c) => c.id === subId)!.title }
              : { k: "entidad", t: subId });
          if (!nodesMap.has(subId)) {
            nodesMap.set(subId, {
              id: subId,
              label: nodeInfo.t,
              tipo: nodeInfo.k,
            });
          }
          const linkKeySub = `${parentId}->${subId}`;
          if (!addedLinks.has(linkKeySub)) {
            links.push({ source: parentId, target: subId, tipo: subRel });
            addedLinks.add(linkKeySub);
          }
          if (kids && kids.length) {
            walk(kids, subId);
          }
        }
      };
      walk(SUB[provId] ?? [], provId);
    }
  }

  return {
    nodes: Array.from(nodesMap.values()),
    links,
  };
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
  },
  { deep: true }
);
</script>

<template>
  <div class="flex flex-col gap-3">
    <Alert v-if="stale && !readonly" variant="warning">
      <AlertDescription class="text-body-sm leading-relaxed text-ink">
        <strong class="font-semibold text-warning">La evidencia cambió.</strong>
        Revisa y confirma la ficha de nuevo.
      </AlertDescription>
    </Alert>

    <!-- Ficha · composed only from linked evidence -->
    <div class="overflow-hidden rounded-md border border-border">
      <div
        v-for="row in rows"
        :key="row.label"
        class="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-x-4 gap-y-1 border-b border-border px-4 py-3.5 last:border-b-0"
      >
        <span
          class="text-label uppercase"
          :class="row.amber ? 'text-warning' : 'text-ink-muted'"
        >
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

    <!-- Módulo de Grafo de Relaciones de la Ficha -->
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
            <Button
              variant="outline"
              size="sm"
              class="h-7 text-xs"
              @click="showGraph = !showGraph"
            >
              {{ showGraph ? "Ocultar grafo" : "Mostrar grafo" }}
            </Button>
          </div>
        </div>
      </template>

      <div v-show="showGraph" class="space-y-3">
        <div
          v-if="!fichaGraph.nodes.length || fichaGraph.nodes.length <= 1"
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

    <!-- Modal interactivo para inspeccionar evidencia desde el grafo -->
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
