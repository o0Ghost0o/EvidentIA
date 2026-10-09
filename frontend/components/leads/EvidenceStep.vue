<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import Button from "~/components/ui/Button.vue";
import Input from "~/components/ui/Input.vue";
import { api } from "~/composables/useApi";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "~/components/ui/sheet";
import EvidenceDetailModal from "~/components/EvidenceDetailModal.vue";
import ChainNode, { type ChainTreeNode } from "~/components/leads/ChainNode.vue";
import type { EvidenceLevel, CatalogSource } from "~/lib/leadEvidence";
import {
  BAND_LABEL,
  type LinkedItem,
  type RankItem,
  type RankingResponse,
  type Rol,
  ROL_META,
  ROL_ORDER,
  type ScoreResponse,
  evidenceLevelFrom,
  normaliseRol,
} from "~/lib/leadWizard";

// Step 2 "Evidencia" of the new-lead workspace. Sources are linked from the real
// ranking catalog (GET /ranking) and persisted to the evidence API. The evidence
// state, role lanes and requirement checklist are derived from the linked set and
// the deterministic score endpoint (GET /cases/{id}/score) — no local fixtures.
interface InitialItem {
  rowId: number | null;
  fuenteId: string;
  fuenteTipo: string;
  rol: string;
  titulo: string;
}
const props = withDefaults(
  defineProps<{
    leadId: number;
    modalidad?: string;
    readonly?: boolean;
    initialItems?: InitialItem[];
    initialLinkedIds?: string[];
    customCatalog?: CatalogSource[];
  }>(),
  {
    modalidad: "tvn",
    readonly: false,
    initialItems: () => [],
    initialLinkedIds: () => [],
    customCatalog: () => [],
  }
);
const emit = defineEmits<{
  (e: "back"): void;
  (e: "continue"): void;
  (e: "change", payload: { count: number; label: string; tone: string; key: EvidenceLevel; linkedIds: string[]; items: LinkedItem[] }): void;
}>();

// Linked set, seeded from any already-saved evidence (lead detail / resume).
const linked = ref<LinkedItem[]>(
  props.initialItems.length
    ? props.initialItems.map((it) => ({
        rowId: it.rowId,
        fuenteId: it.fuenteId,
        fuenteTipo: it.fuenteTipo,
        rol: normaliseRol(it.rol),
        titulo: it.titulo,
      }))
    : (props.initialLinkedIds || []).map((id) => ({
        rowId: null,
        fuenteId: id,
        fuenteTipo: "news",
        rol: "respaldo",
        titulo: id,
      }))
);
const persistError = ref("");

// Backend score for the current linked set; drives the evidence state label/tone.
const score = ref<ScoreResponse | null>(null);
const scoreLoading = ref(false);

interface CatalogItem extends RankItem {
  tipo?: string;
  similarity_score?: number;
  suggested_role?: Rol;
  is_contradiction?: boolean;
  contra_reason?: string | null;
  graph_connection?: string | null;
}

// Catalog drawer with RAG & GraphRAG suggestions
const catOpen = ref(false);
const catalog = ref<CatalogItem[]>([]);
const catalogLoading = ref(false);
const catalogError = ref("");
const query = ref("");

const activeCatalogTab = ref<"suggested" | "all" | "linked">("suggested");
const suggestions = ref<CatalogItem[]>([]);
const suggestionsLoading = ref(false);
const suggestionsError = ref("");

// Role chosen for the next link, per catalog row.
const pendingRol = reactive<Record<string, Rol>>({});

// Source-detail modal (real GET /evidence/item).
const modalOpen = ref(false);
const inspected = ref<{ tipo: string; id: string } | null>(null);

const linkedIds = computed(() => linked.value.map((l) => l.fuenteId));
const isLinked = (fuenteId: string) => linked.value.some((l) => l.fuenteId === fuenteId);

const level = computed<EvidenceLevel>(() =>
  evidenceLevelFrom(score.value?.evidence_state, linked.value.length)
);
const STATE: Record<EvidenceLevel, { label: string; short: string; tone: "neutral" | "error" | "warning" | "success" }> = {
  none: { label: "sin fuentes", short: "Aún no hay fuentes vinculadas.", tone: "neutral" },
  insuficiente: { label: "insuficiente", short: "Ninguna fuente primaria respalda la afirmación.", tone: "error" },
  parcial: { label: "parcial", short: "Una fuente primaria respalda; falta corroborar.", tone: "warning" },
  suficiente: { label: "suficiente", short: "La afirmación está respaldada por fuentes primarias.", tone: "success" },
};
const state = computed(() => STATE[level.value]);

// --- Score refresh --------------------------------------------------------
async function refreshScore() {
  scoreLoading.value = true;
  try {
    score.value = await api<ScoreResponse>(`cases/${props.leadId}/score`);
  } catch {
    score.value = null;
  } finally {
    scoreLoading.value = false;
  }
}

watch(
  [level, linked],
  () => {
    emit("change", {
      count: linked.value.length,
      label: state.value.label,
      tone: state.value.tone,
      key: level.value,
      linkedIds: [...linkedIds.value],
      items: linked.value.map((l) => ({ ...l })),
    });
  },
  { immediate: true, deep: true }
);

// --- Persistence (optimistic) --------------------------------------------
async function persistLink(item: LinkedItem) {
  try {
    const res = await api<{ id: number }>(`cases/${props.leadId}/evidence`, {
      method: "POST",
      body: {
        fuente_tipo: item.fuenteTipo,
        fuente_id: item.fuenteId,
        rol: item.rol,
        nota: item.titulo,
        marcado_manual: true,
      },
    });
    if (res?.id != null) item.rowId = res.id;
  } catch (err: any) {
    persistError.value = err?.data?.detail || "No se pudo guardar el vínculo; se mantiene localmente.";
  }
  await refreshScore();
}
async function persistUnlink(item: LinkedItem) {
  if (item.rowId == null) return;
  try {
    await api(`cases/${props.leadId}/evidence/${item.rowId}`, { method: "DELETE" });
  } catch (err: any) {
    persistError.value = err?.data?.detail || "No se pudo quitar el vínculo en el servidor.";
  }
  await refreshScore();
}

function linkRow(row: CatalogItem) {
  const fuenteId = row.ids_fuente[0] ?? row.id;
  if (isLinked(fuenteId)) return;
  const assignedRole = pendingRol[row.id] ?? row.suggested_role ?? "respaldo";
  const item: LinkedItem = {
    rowId: null,
    fuenteId,
    fuenteTipo: row.tipo || (fuenteId.startsWith("geo:") || fuenteId.startsWith("evt:") ? "event" : (fuenteId.includes(":") && !fuenteId.startsWith("http")) ? "indicator" : "news"),
    rol: assignedRole,
    titulo: row.titulo,
  };
  // Key the linked item by the ranking id so toggles line up with the drawer.
  (item as LinkedItem & { catId?: string }).catId = row.id;
  linked.value = [...linked.value, item];
  persistError.value = "";
  void persistLink(item);
}
function unlinkByFuente(fuenteId: string) {
  const item = linked.value.find((l) => l.fuenteId === fuenteId);
  if (!item) return;
  linked.value = linked.value.filter((l) => l.fuenteId !== fuenteId);
  persistError.value = "";
  void persistUnlink(item);
}
function toggleRow(row: CatalogItem) {
  const fuenteId = row.ids_fuente[0] ?? row.id;
  isLinked(fuenteId) ? unlinkByFuente(fuenteId) : linkRow(row);
}
function rowLinked(row: CatalogItem) {
  return isLinked(row.ids_fuente[0] ?? row.id);
}

function setRol(item: LinkedItem, rol: Rol) {
  item.rol = rol;
  if (item.rowId != null) {
    // rol is only captured at link time by the API; a change relinks the row.
    void api(`cases/${props.leadId}/evidence/${item.rowId}`, { method: "DELETE" })
      .then(() => {
        item.rowId = null;
        return persistLink(item);
      })
      .catch(() => {});
  }
}

// --- Catalog & AI Suggestions (RAG + GraphRAG) -----------------------------
async function loadSuggestions(searchQuery?: string) {
  suggestionsLoading.value = true;
  suggestionsError.value = "";
  try {
    const qParam = searchQuery !== undefined ? searchQuery : query.value.trim();
    let res: CatalogItem[] = [];
    if (props.leadId != null) {
      res = await api<CatalogItem[]>(`cases/${props.leadId}/suggested-evidence`, {
        query: { q: qParam || undefined, limit: "20" },
      });
    } else {
      res = await api<CatalogItem[]>("cases/suggested-evidence", {
        query: { q: qParam || undefined, modalidad: props.modalidad, limit: "20" },
      });
    }
    suggestions.value = res;
    // Pre-assign suggested role if provided (e.g. "contradiccion")
    for (const item of res) {
      if (item.suggested_role && !pendingRol[item.id]) {
        pendingRol[item.id] = item.suggested_role;
      }
    }
  } catch (err: any) {
    suggestionsError.value = "No se pudieron cargar sugerencias de IA.";
  } finally {
    suggestionsLoading.value = false;
  }
}

async function loadCatalog() {
  if (catalog.value.length || catalogLoading.value) return;
  catalogLoading.value = true;
  catalogError.value = "";
  try {
    const res = await api<RankingResponse>("ranking", { query: { modalidad: props.modalidad } });
    catalog.value = res.items;
  } catch {
    catalogError.value = "No se pudo cargar el catálogo de fuentes. ¿Está corriendo el backend?";
  } finally {
    catalogLoading.value = false;
  }
}

function openCatalog() {
  catOpen.value = true;
  activeCatalogTab.value = "suggested";
  void loadSuggestions();
  void loadCatalog();
}

let searchTimer: any = null;
watch(query, (val) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    if (activeCatalogTab.value === "suggested" || val.trim().length >= 2) {
      void loadSuggestions(val.trim());
    }
  }, 300);
});

const catalogFiltered = computed<CatalogItem[]>(() => {
  if (activeCatalogTab.value === "linked") {
    const allKnown = [...suggestions.value, ...catalog.value];
    const seen = new Set<string>();
    return allKnown.filter((row) => {
      const fid = row.ids_fuente[0] ?? row.id;
      if (seen.has(fid)) return false;
      seen.add(fid);
      return isLinked(fid);
    });
  }

  if (activeCatalogTab.value === "suggested") {
    return suggestions.value;
  }

  // "all" tab
  const q = query.value.trim().toLowerCase();
  return catalog.value.filter((row) => {
    if (!q) return true;
    return row.titulo.toLowerCase().includes(q) || row.id.toLowerCase().includes(q);
  });
});

// --- Lanes & checklist ----------------------------------------------------
const lanes = computed(() =>
  ROL_ORDER.map((rol) => ({
    rol,
    label: ROL_META[rol].laneLabel,
    empty: ROL_META[rol].empty,
    cards: linked.value.filter((l) => l.rol === rol),
  }))
);
const contraCount = computed(() => linked.value.filter((l) => l.rol === "contradiccion").length);
const checks = computed(() => [
  {
    label: "Al menos una fuente vinculada",
    note: "Requerido para continuar a Contexto",
    detail: String(linked.value.length),
    status: linked.value.length ? "ok" : "todo",
  },
  {
    label: "Evidencia suficiente",
    note:
      level.value === "suficiente"
        ? "Respaldo primario confirmado por las reglas"
        : "Dos fuentes primarias independientes · la prensa replicada cuenta como una",
    detail: level.value === "suficiente" ? "✓" : level.value === "parcial" ? "parcial" : "falta",
    status: level.value === "suficiente" ? "ok" : level.value === "parcial" ? "warn" : "todo",
  },
  {
    label: "Versión contraria identificada",
    note: contraCount.value ? "El borrador presentará ambas versiones" : "Recomendado · p. ej. la versión de la distribuidora",
    detail: String(contraCount.value),
    status: contraCount.value ? "ok" : "todo",
  },
]);

const bandLabel = computed(() => (score.value ? BAND_LABEL[score.value.band] : ""));

// --- Presentation helpers -------------------------------------------------
const STATE_CARD: Record<string, string> = {
  neutral: "border-border bg-surface",
  error: "border-destructive bg-surface",
  warning: "border-warning/50 bg-warning/5",
  success: "border-success/50 bg-success/5",
};
const STATE_TEXT: Record<string, string> = {
  neutral: "text-ink-muted",
  error: "text-destructive",
  warning: "text-warning",
  success: "text-success",
};
const CHECK_GLYPH: Record<string, string> = { ok: "✓", warn: "!", todo: "", info: "·" };
const CHECK_CIRCLE: Record<string, string> = {
  ok: "bg-success text-white border-success",
  warn: "bg-warning text-white border-warning",
  todo: "border-ink-muted/50 text-ink-muted",
  info: "border-ink-muted/50 text-ink-muted",
};
const REL_ACCENT: Record<Rol, string> = {
  respaldo: "border-t-success",
  contradiccion: "border-t-destructive",
  contexto: "border-t-ink-muted",
};
const REL_LABEL_COLOR: Record<Rol, string> = {
  respaldo: "text-success",
  contradiccion: "text-destructive",
  contexto: "text-ink-muted",
};

function inspect(fuenteId: string, fuenteTipo: string) {
  inspected.value = { tipo: fuenteTipo, id: fuenteId };
  modalOpen.value = true;
}

// --- Evidence-chain drawer (real /evidence/tree) --------------------------
interface TreeNode { tipo: string; id: string; label: string }
interface TreeEdge {
  origen_tipo: string; origen_id: string;
  destino_tipo: string; destino_id: string;
  tipo: string; peso?: number;
}
const chainCard = ref<LinkedItem | null>(null);
const chainTree = ref<{ nodes: TreeNode[]; edges: TreeEdge[] } | null>(null);
const chainLoading = ref(false);
const chainError = ref("");

// Relation code → human label (relations: mentions | same_event | source_of |
// contradicts | corroborates | has_evidence | measures | geolocated_in).
const REL_LABEL: Record<string, string> = {
  contradicts: "Contradice",
  corroborates: "Corrobora",
  mentions: "Menciona",
  same_event: "Mismo evento",
  source_of: "Fuente de",
  has_evidence: "Evidencia",
  measures: "Mide",
  geolocated_in: "Ubicado en",
};
async function openChain(card: LinkedItem) {
  chainCard.value = card;
  chainTree.value = null;
  chainError.value = "";
  chainLoading.value = true;
  try {
    chainTree.value = await api<{ nodes: TreeNode[]; edges: TreeEdge[] }>("evidence/tree", {
      query: { tipo: card.fuenteTipo, id: card.fuenteId, depth: "3" },
    });
  } catch (err: any) {
    chainError.value = err?.data?.detail || "No se pudo cargar la cadena de evidencia.";
  } finally {
    chainLoading.value = false;
  }
}

// Build the hierarchical chain the design shows: the clicked source is the root,
// and each node expands to its children — the next ring of related nodes. The
// parent/child structure comes from a breadth-first walk of the real
// /evidence/tree neighbourhood, so every node is reached once, through its nearest
// parent, with the edge relation that connects them.
const chainRoots = computed<ChainTreeNode[]>(() => {
  const card = chainCard.value;
  const tree = chainTree.value;
  if (!card || !tree) return [];
  const key = (t: string, i: string) => `${t}:${i}`;
  const rootKey = key(card.fuenteTipo, card.fuenteId);
  const nodeByKey = new Map(tree.nodes.map((n) => [key(n.tipo, n.id), n]));

  const adj = new Map<string, { to: string; rel: string }[]>();
  for (const e of tree.edges) {
    const a = key(e.origen_tipo, e.origen_id);
    const b = key(e.destino_tipo, e.destino_id);
    (adj.get(a) ?? adj.set(a, []).get(a)!).push({ to: b, rel: e.tipo });
    (adj.get(b) ?? adj.set(b, []).get(b)!).push({ to: a, rel: e.tipo });
  }

  // BFS from the source: record each node's parent and the relation that reached it.
  const seen = new Set<string>([rootKey]);
  const childrenOf = new Map<string, { k: string; rel: string }[]>();
  const queue = [rootKey];
  while (queue.length) {
    const cur = queue.shift()!;
    for (const { to, rel } of adj.get(cur) ?? []) {
      if (seen.has(to)) continue;
      seen.add(to);
      (childrenOf.get(cur) ?? childrenOf.set(cur, []).get(cur)!).push({ k: to, rel });
      queue.push(to);
    }
  }

  const build = (k: string, rel: string): ChainTreeNode | null => {
    const node = nodeByKey.get(k);
    if (!node) return null;
    return {
      tipo: node.tipo,
      id: node.id,
      label: node.label,
      rel,
      relLabel: REL_LABEL[rel] ?? rel,
      children: (childrenOf.get(k) ?? [])
        .map((c) => build(c.k, c.rel))
        .filter((n): n is ChainTreeNode => n !== null),
    };
  };

  return (childrenOf.get(rootKey) ?? [])
    .map((c) => build(c.k, c.rel))
    .filter((n): n is ChainTreeNode => n !== null);
});

onMounted(() => {
  if (props.leadId != null) void refreshScore();
});
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Evidence state + requirement checklist -->
    <div class="flex flex-col gap-3 rounded-md border p-4 transition-colors" :class="STATE_CARD[state.tone]">
      <div class="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span class="font-serif text-heading-md" :class="STATE_TEXT[state.tone]">
          Evidencia {{ state.label }}
        </span>
        <span class="text-body-sm text-ink">{{ state.short }}</span>
      </div>

      <div v-if="score" class="flex flex-wrap items-center gap-2 font-mono text-caption text-ink-muted">
        <span>P {{ score.P }} · banda {{ bandLabel }}</span>
        <span class="rounded-sm bg-surface-sunken px-1">reglas {{ score.rules_version }}</span>
        <span v-if="scoreLoading">· actualizando…</span>
      </div>

      <div class="flex flex-col overflow-hidden rounded-md border border-border bg-surface">
        <div
          v-for="(ck, i) in checks"
          :key="ck.label"
          class="grid grid-cols-[22px_minmax(0,1fr)_auto] items-center gap-3 px-3.5 py-2.5"
          :class="i < checks.length - 1 ? 'border-b border-surface-sunken' : ''"
        >
          <span
            class="flex h-[22px] w-[22px] items-center justify-center rounded-full border-[1.5px] text-caption font-semibold transition-colors"
            :class="CHECK_CIRCLE[ck.status]"
          >
            {{ CHECK_GLYPH[ck.status] }}
          </span>
          <div class="flex min-w-0 flex-col gap-0.5">
            <span class="text-body-sm font-semibold">{{ ck.label }}</span>
            <span class="text-caption text-ink-muted">{{ ck.note }}</span>
          </div>
          <span class="whitespace-nowrap font-mono text-mono">{{ ck.detail }}</span>
        </div>
      </div>
    </div>

    <!-- Fuentes por papel header + actions -->
    <div class="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
      <div class="flex min-w-0 flex-col gap-0.5">
        <span class="text-label uppercase text-ink-muted">Fuentes por papel</span>
        <span class="text-caption text-ink-muted">Toca una fuente para ver su detalle y citas.</span>
      </div>
      <div v-if="!readonly" class="flex flex-wrap gap-2">
        <Button @click="openCatalog">+ Vincular fuentes</Button>
      </div>
    </div>

    <p v-if="persistError" class="text-caption text-destructive">{{ persistError }}</p>

    <!-- Role lanes -->
    <div class="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] items-start gap-3">
      <div
        v-for="lane in lanes"
        :key="lane.rol"
        class="flex flex-col gap-2 rounded-md border-t-[3px] bg-surface-sunken p-3"
        :class="REL_ACCENT[lane.rol]"
      >
        <div class="flex items-center justify-between">
          <span class="text-label uppercase" :class="REL_LABEL_COLOR[lane.rol]">{{ lane.label }}</span>
          <span class="font-mono text-caption text-ink-muted">{{ lane.cards.length }}</span>
        </div>

        <p v-if="!lane.cards.length" class="text-caption leading-relaxed text-ink-muted">
          {{ lane.empty }}
        </p>

        <div
          v-for="card in lane.cards"
          :key="card.fuenteId"
          class="flex flex-col gap-1.5 rounded-md border border-border bg-surface p-3"
        >
          <button
            type="button"
            class="flex flex-col gap-1.5 text-left transition-shadow hover:shadow-ev-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/25"
            @click="openChain(card)"
          >
            <div class="flex flex-wrap items-center gap-1.5">
              <span class="rounded-full bg-info/10 px-2 py-0.5 text-[11px] font-semibold text-info">
                {{ card.fuenteTipo }}
              </span>
              <span class="font-mono text-caption text-ink-muted">{{ card.fuenteId }}</span>
            </div>
            <span class="text-body-sm leading-snug">{{ card.titulo }}</span>
          </button>

          <div v-if="!readonly" class="flex flex-wrap items-center gap-1.5 border-t border-surface-sunken pt-2">
            <button
              v-for="rol in ROL_ORDER"
              :key="rol"
              type="button"
              class="h-6 rounded-full border px-2 text-[11px] font-semibold transition-colors"
              :class="card.rol === rol ? 'border-ink bg-ink text-on-primary' : 'border-border bg-surface text-ink-muted'"
              @click="setRol(card, rol)"
            >
              {{ ROL_META[rol].label }}
            </button>
            <button
              type="button"
              class="ml-auto h-6 rounded-md px-2 text-[11px] font-semibold text-destructive hover:bg-destructive/5"
              @click="unlinkByFuente(card.fuenteId)"
            >
              Quitar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer nav -->
    <div v-if="!readonly" class="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
      <Button variant="outline" @click="emit('back')">← Atrás</Button>
      <Button :disabled="!linked.length" @click="emit('continue')">
        Continuar · Contexto →
      </Button>
    </div>

    <!-- Catalog drawer (ranking) -->
    <Sheet v-model:open="catOpen">
      <SheetContent side="right" class="flex w-full flex-col gap-0 p-0 sm:max-w-[560px]">
        <div class="flex flex-col gap-1 border-b border-border px-5 py-4 pr-12">
          <SheetTitle class="font-serif text-heading-md text-ink">Vincular fuentes</SheetTitle>
          <SheetDescription class="text-caption text-ink-muted">
            Catálogo priorizado · modalidad {{ modalidad }} · cada grupo cuenta como una fuente
          </SheetDescription>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto">
          <div class="flex flex-col gap-2 border-b border-border px-5 py-3">
            <Input
              v-model="query"
              placeholder="🔍 Buscar por semántica RAG, GraphRAG o ID…"
              class="h-8 w-full font-mono text-caption"
            />
            <div class="flex flex-wrap items-center gap-1.5">
              <button
                type="button"
                class="flex h-7 items-center gap-1 rounded-full border px-2.5 text-caption font-semibold transition-colors"
                :class="activeCatalogTab === 'suggested' ? 'border-primary bg-primary text-on-primary shadow-sm' : 'border-border bg-surface text-ink hover:bg-surface-sunken'"
                @click="activeCatalogTab = 'suggested'"
              >
                <span>✨ Sugerencias IA · {{ suggestions.length }}</span>
              </button>
              <button
                type="button"
                class="h-7 rounded-full border px-2.5 text-caption font-semibold transition-colors"
                :class="activeCatalogTab === 'all' ? 'border-ink bg-ink text-on-primary' : 'border-border bg-surface text-ink hover:bg-surface-sunken'"
                @click="activeCatalogTab = 'all'"
              >
                Todas · {{ catalog.length }}
              </button>
              <button
                type="button"
                class="h-7 rounded-full border px-2.5 text-caption font-semibold transition-colors"
                :class="activeCatalogTab === 'linked' ? 'border-ink bg-ink text-on-primary' : 'border-border bg-surface text-ink hover:bg-surface-sunken'"
                @click="activeCatalogTab = 'linked'"
              >
                Vinculadas · {{ linked.length }}
              </button>
            </div>
          </div>

          <!-- Banner de estado para Sugerencias IA -->
          <div
            v-if="activeCatalogTab === 'suggested'"
            class="flex items-center justify-between border-b border-primary/20 bg-primary/5 px-5 py-2 text-[11px] font-medium text-primary"
          >
            <span>✨ Top 20 evidencias recomendadas mediante RAG semántico y GraphRAG</span>
            <span v-if="suggestionsLoading" class="animate-pulse font-mono">Consultando motor IA…</span>
          </div>

          <p v-if="catalogLoading || suggestionsLoading" class="px-5 py-4 text-body-sm text-ink-muted">
            {{ suggestionsLoading ? "Analizando semántica y causalidad en el grafo…" : "Cargando catálogo…" }}
          </p>
          <p v-else-if="catalogError || suggestionsError" class="px-5 py-4 text-body-sm text-destructive">
            {{ catalogError || suggestionsError }}
          </p>

          <div
            v-for="row in catalogFiltered"
            :key="row.id"
            class="flex flex-col gap-2 border-b border-border px-5 py-3 transition-colors"
            :class="rowLinked(row) ? 'bg-primary-soft/40' : row.is_contradiction ? 'bg-destructive/5' : ''"
          >
            <div class="flex flex-wrap items-center gap-2">
              <span class="shrink-0 rounded-sm bg-surface-sunken px-1 font-mono text-caption text-ink-muted">
                P {{ row.P }}
              </span>
              <span
                v-if="row.is_contradiction"
                class="inline-flex items-center gap-1 rounded border border-destructive/30 bg-destructive/10 px-1.5 py-0.5 font-sans text-[10px] font-bold tracking-wide text-destructive"
              >
                ⚡ Versión contraria / Anti-patrón
              </span>
              <span
                v-if="row.graph_connection"
                class="inline-flex items-center gap-1 rounded border border-primary/20 bg-primary/10 px-1.5 py-0.5 font-sans text-[10px] font-medium text-primary"
              >
                🕸️ {{ row.graph_connection }}
              </span>
              <span class="min-w-0 flex-1 basis-[200px] text-body-sm leading-snug">{{ row.titulo }}</span>
              <button
                type="button"
                class="ml-auto h-8 min-w-[96px] rounded-md border px-3 text-caption font-semibold transition-colors"
                :class="rowLinked(row)
                  ? 'border-border bg-surface text-ink hover:bg-surface-sunken'
                  : 'border-transparent bg-primary text-on-primary hover:bg-primary-deep'"
                @click="toggleRow(row)"
              >
                {{ rowLinked(row) ? "Quitar" : "Vincular" }}
              </button>
            </div>

            <!-- Razón de anti-patrón de contradicción -->
            <p v-if="row.contra_reason" class="text-[11px] italic text-destructive/90">
              ℹ️ {{ row.contra_reason }}
            </p>

            <div class="flex flex-wrap items-center gap-2 font-mono text-[11px] text-ink-muted">
              <span>{{ row.group_size }} {{ row.group_size === 1 ? "nota" : "notas" }}</span>
              <span>· {{ row.dedup?.primary_sources ?? 1 }} primaria(s)</span>
              <span>· evidencia {{ row.evidence_state }}</span>
              <span v-if="row.similarity_score != null">· afinidad {{ Math.round(row.similarity_score * 100) }}%</span>
              <template v-if="!rowLinked(row)">
                <span class="ml-auto">papel:</span>
                <button
                  v-for="rol in ROL_ORDER"
                  :key="rol"
                  type="button"
                  class="rounded-full border px-2 py-0.5 font-semibold transition-colors"
                  :class="(pendingRol[row.id] ?? row.suggested_role ?? 'respaldo') === rol
                    ? (rol === 'contradiccion' ? 'border-destructive bg-destructive text-white' : 'border-ink bg-ink text-on-primary')
                    : 'border-border bg-surface'"
                  @click="pendingRol[row.id] = rol"
                >
                  {{ ROL_META[rol].label }}
                </button>
              </template>
            </div>
          </div>

          <p v-if="!catalogLoading && !suggestionsLoading && !catalogFiltered.length" class="px-5 py-4 text-body-sm text-ink-muted">
            Sin resultados para la búsqueda.
          </p>
        </div>

        <div class="flex items-center justify-between gap-3 border-t border-border px-5 py-4">
          <span class="text-caption text-ink-muted">{{ linked.length }} fuentes vinculadas</span>
          <Button variant="outline" @click="catOpen = false">Listo</Button>
        </div>
      </SheetContent>
    </Sheet>

    <!-- Evidence-chain drawer (real /evidence/tree). A node opens its full detail. -->
    <Sheet :open="!!chainCard" @update:open="(v) => { if (!v) chainCard = null; }">
      <SheetContent side="right" class="flex w-full flex-col gap-0 p-0 sm:max-w-[480px]">
        <div class="flex flex-col gap-1 border-b border-border px-5 py-4 pr-12">
          <SheetTitle class="font-serif text-heading-md text-ink">
            {{ chainCard ? `Cadena de evidencia · ${chainCard.fuenteId}` : "" }}
          </SheetTitle>
          <SheetDescription class="text-caption text-ink-muted">
            Vecindario en el grafo. Toca un nodo para ver su ficha completa.
          </SheetDescription>
        </div>
        <div class="min-h-0 flex-1 overflow-y-auto flex flex-col gap-3 px-5 py-4">
          <!-- N0 · the source itself -->
          <button
            v-if="chainCard"
            type="button"
            class="flex flex-col gap-1.5 rounded-md border border-primary/40 bg-primary-soft/40 p-3 text-left transition-shadow hover:shadow-ev-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/25"
            @click="inspect(chainCard.fuenteId, chainCard.fuenteTipo)"
          >
            <span class="font-mono text-[11px] uppercase tracking-wide text-ink-muted">Fuente · {{ chainCard.fuenteId }}</span>
            <span class="text-body-sm leading-snug text-ink">{{ chainCard.titulo }}</span>
          </button>

          <p v-if="chainLoading" class="text-body-sm text-ink-muted">Cargando cadena…</p>
          <p v-else-if="chainError" class="text-body-sm text-destructive">{{ chainError }}</p>
          <p v-else-if="!chainRoots.length" class="text-body-sm text-ink-muted">
            Esta fuente aún no tiene relaciones en el grafo de evidencia.
          </p>

          <!-- Nested tree: each node toggles open to reveal its sublevel. -->
          <ChainNode
            v-for="root in chainRoots"
            :key="`${root.tipo}:${root.id}`"
            :node="root"
            :depth="1"
            @inspect="(t, i) => inspect(i, t)"
          />
        </div>
      </SheetContent>
    </Sheet>

    <!-- Source detail (real /evidence/item) -->
    <EvidenceDetailModal
      v-model:open="modalOpen"
      :tipo="inspected?.tipo"
      :id="inspected?.id"
      @navigate="(t, i) => { inspected = { tipo: t, id: i }; modalOpen = true; }"
    />
  </div>
</template>
