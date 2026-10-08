<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import Button from "~/components/ui/Button.vue";
import Input from "~/components/ui/Input.vue";
import { api } from "~/composables/useApi";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "~/components/ui/sheet";
import EvidenceDetailModal from "~/components/EvidenceDetailModal.vue";
import type { EvidenceLevel } from "~/lib/leadEvidence";
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
  defineProps<{ leadId: number; modalidad?: string; readonly?: boolean; initialItems?: InitialItem[] }>(),
  { modalidad: "tvn", readonly: false, initialItems: () => [] }
);
const emit = defineEmits<{
  (e: "back"): void;
  (e: "continue"): void;
  (e: "change", payload: { count: number; label: string; tone: string; key: EvidenceLevel; linkedIds: string[] }): void;
}>();

// Linked set, seeded from any already-saved evidence (lead detail / resume).
const linked = ref<LinkedItem[]>(
  props.initialItems.map((it) => ({
    rowId: it.rowId,
    fuenteId: it.fuenteId,
    fuenteTipo: it.fuenteTipo,
    rol: normaliseRol(it.rol),
    titulo: it.titulo,
  }))
);
const persistError = ref("");

// Backend score for the current linked set; drives the evidence state label/tone.
const score = ref<ScoreResponse | null>(null);
const scoreLoading = ref(false);

// Catalog drawer (ranking).
const catOpen = ref(false);
const catalog = ref<RankItem[]>([]);
const catalogLoading = ref(false);
const catalogError = ref("");
const query = ref("");
const onlyLinked = ref(false);
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
  [level, linkedIds],
  () => {
    emit("change", {
      count: linked.value.length,
      label: state.value.label,
      tone: state.value.tone,
      key: level.value,
      linkedIds: [...linkedIds.value],
    });
  },
  { immediate: true }
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

function linkRow(row: RankItem) {
  if (isLinked(row.id)) return;
  const fuenteId = row.ids_fuente[0] ?? row.id;
  const item: LinkedItem = {
    rowId: null,
    fuenteId,
    fuenteTipo: "news",
    rol: pendingRol[row.id] ?? "respaldo",
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
function toggleRow(row: RankItem) {
  const fuenteId = row.ids_fuente[0] ?? row.id;
  isLinked(fuenteId) ? unlinkByFuente(fuenteId) : linkRow(row);
}
function rowLinked(row: RankItem) {
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

// --- Catalog --------------------------------------------------------------
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
  void loadCatalog();
}

const catalogFiltered = computed(() => {
  const q = query.value.trim().toLowerCase();
  return catalog.value.filter((row) => {
    if (onlyLinked.value && !rowLinked(row)) return false;
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
const KIND_LABEL: Record<string, string> = {
  news: "Noticia",
  indicator: "Indicador",
  event: "Evento",
  entity: "Entidad",
  case: "Caso",
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

// Kind → colored chip (mirrors the design's evidence-chain palette).
const KIND_TONE: Record<string, string> = {
  news: "text-info bg-info/10",
  indicator: "text-teal-700 dark:text-teal-300 bg-teal-500/15",
  event: "text-warning bg-warning/10",
  entity: "text-purple-700 dark:text-purple-300 bg-purple-500/15",
  case: "text-primary bg-primary-soft",
};
function kindTone(tipo: string) {
  return KIND_TONE[tipo] ?? "text-ink-muted bg-surface-sunken";
}
// Relation → accent for the node's relation badge and left border.
function relClass(rel: string) {
  if (rel === "contradicts") return "text-destructive border-destructive/40 bg-destructive/10";
  if (rel === "corroborates") return "text-success border-success/40 bg-success/10";
  return "text-ink-muted border-border bg-surface";
}

// Build the hierarchical chain the design shows: the source is N0, and each ring
// of neighbours in the graph is the next level (N1, N2, …), indented, with each
// node carrying its relation to its parent. Levels come from a breadth-first walk
// of the real /evidence/tree neighbourhood.
const chainLevels = computed(() => {
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

  const depth = new Map<string, number>([[rootKey, 0]]);
  const parentRel = new Map<string, string>();
  const queue = [rootKey];
  while (queue.length) {
    const cur = queue.shift()!;
    const d = depth.get(cur)!;
    for (const { to, rel } of adj.get(cur) ?? []) {
      if (!depth.has(to)) {
        depth.set(to, d + 1);
        parentRel.set(to, rel);
        queue.push(to);
      }
    }
  }

  const byDepth = new Map<number, { node: TreeNode; rel: string; relLabel: string }[]>();
  for (const [k, d] of depth) {
    if (d === 0) continue;
    const node = nodeByKey.get(k);
    if (!node) continue;
    const rel = parentRel.get(k) ?? "";
    (byDepth.get(d) ?? byDepth.set(d, []).get(d)!).push({
      node,
      rel,
      relLabel: REL_LABEL[rel] ?? rel,
    });
  }
  return [...byDepth.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([level, nodes]) => ({ level, nodes }));
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
          <div class="flex flex-wrap items-center gap-2 border-b border-border px-5 py-3">
            <Input v-model="query" placeholder="Buscar por título o ID" class="h-8 flex-1 font-mono text-caption" />
            <div class="flex gap-1.5">
              <button
                type="button"
                class="h-8 rounded-full border px-3 text-caption font-semibold transition-colors"
                :class="!onlyLinked ? 'border-ink bg-ink text-on-primary' : 'border-border bg-surface text-ink'"
                @click="onlyLinked = false"
              >
                Todas · {{ catalog.length }}
              </button>
              <button
                type="button"
                class="h-8 rounded-full border px-3 text-caption font-semibold transition-colors"
                :class="onlyLinked ? 'border-ink bg-ink text-on-primary' : 'border-border bg-surface text-ink'"
                @click="onlyLinked = true"
              >
                Vinculadas · {{ linked.length }}
              </button>
            </div>
          </div>

          <p v-if="catalogLoading" class="px-5 py-4 text-body-sm text-ink-muted">Cargando catálogo…</p>
          <p v-else-if="catalogError" class="px-5 py-4 text-body-sm text-destructive">{{ catalogError }}</p>

          <div
            v-for="row in catalogFiltered"
            :key="row.id"
            class="flex flex-col gap-2 border-b border-border px-5 py-3 transition-colors"
            :class="rowLinked(row) ? 'bg-primary-soft/40' : ''"
          >
            <div class="flex flex-wrap items-center gap-2">
              <span class="shrink-0 rounded-sm bg-surface-sunken px-1 font-mono text-caption text-ink-muted">
                P {{ row.P }}
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
            <div class="flex flex-wrap items-center gap-2 font-mono text-[11px] text-ink-muted">
              <span>{{ row.group_size }} {{ row.group_size === 1 ? "nota" : "notas" }}</span>
              <span>· {{ row.dedup.primary_sources }} primaria(s)</span>
              <span>· evidencia {{ row.evidence_state }}</span>
              <template v-if="!rowLinked(row)">
                <span class="ml-auto">papel:</span>
                <button
                  v-for="rol in ROL_ORDER"
                  :key="rol"
                  type="button"
                  class="rounded-full border px-2 py-0.5 font-semibold transition-colors"
                  :class="(pendingRol[row.id] ?? 'respaldo') === rol ? 'border-ink bg-ink text-on-primary' : 'border-border bg-surface'"
                  @click="pendingRol[row.id] = rol"
                >
                  {{ ROL_META[rol].label }}
                </button>
              </template>
            </div>
          </div>

          <p v-if="!catalogLoading && !catalogError && !catalogFiltered.length" class="px-5 py-4 text-body-sm text-ink-muted">
            Sin resultados.
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
          <p v-else-if="!chainLevels.length" class="text-body-sm text-ink-muted">
            Esta fuente aún no tiene relaciones en el grafo de evidencia.
          </p>

          <!-- N1..N · each ring of neighbours, indented by level -->
          <div
            v-for="lvl in chainLevels"
            :key="lvl.level"
            class="flex flex-col gap-1.5 border-l border-border pl-3"
            :style="{ marginLeft: (lvl.level - 1) * 10 + 'px' }"
          >
            <span class="font-mono text-[11px] uppercase tracking-wide text-ink-muted">Nivel {{ lvl.level }}</span>
            <button
              v-for="entry in lvl.nodes"
              :key="`${entry.node.tipo}:${entry.node.id}`"
              type="button"
              class="flex flex-col gap-1 rounded-md border bg-surface px-3 py-2 text-left transition-shadow hover:shadow-ev-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/25"
              :class="entry.rel === 'contradicts' ? 'border-destructive/50' : 'border-border'"
              @click="inspect(entry.node.id, entry.node.tipo)"
            >
              <div class="flex flex-wrap items-center gap-1.5">
                <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="kindTone(entry.node.tipo)">
                  {{ KIND_LABEL[entry.node.tipo] ?? entry.node.tipo }}
                </span>
                <span class="font-mono text-caption text-ink-muted">{{ entry.node.id }}</span>
                <span
                  v-if="entry.relLabel"
                  class="rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase"
                  :class="relClass(entry.rel)"
                >
                  {{ entry.relLabel }}
                </span>
              </div>
              <span class="text-caption leading-snug">{{ entry.node.label }}</span>
            </button>
          </div>
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
