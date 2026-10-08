<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import Button from "~/components/ui/Button.vue";
import Input from "~/components/ui/Input.vue";
import { api } from "~/composables/useApi";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "~/components/ui/dialog";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "~/components/ui/sheet";
import {
  CATALOG,
  EXAMPLE_LINK,
  type CatalogSource,
  type ChainNode,
  type EvidenceLevel,
  type LaneCard,
  type Relation,
  buildSourceChain,
  deriveEvidence,
  evidencePayload,
  registerDynamicSources,
} from "~/lib/leadEvidence";

// Step 2 "Evidencia" of the new-lead workspace. Links sources from the ingest
// catalog; the evidence state, role lanes and requirement checklist are derived
// from the linked set. Links persist to the real evidence API, optimistically.
const props = withDefaults(
  defineProps<{
    leadId: number;
    readonly?: boolean;
    initialLinkedIds?: string[];
    customCatalog?: CatalogSource[];
  }>(),
  { readonly: false, initialLinkedIds: () => [], customCatalog: () => [] }
);
const emit = defineEmits<{
  (e: "back"): void;
  (e: "continue"): void;
  (e: "change", payload: { count: number; label: string; tone: string; key: EvidenceLevel; linkedIds: string[] }): void;
}>();

// Seed from already-linked sources (lead detail) so the lanes, checklist and
// chains render the saved evidence without any catalog interaction.
const linkedIds = ref<string[]>([...props.initialLinkedIds]);

watch(
  () => props.initialLinkedIds,
  (ids) => {
    if (ids) linkedIds.value = [...ids];
  },
  { deep: true }
);

// Catalog id → backend evidence row id, so unlinks can DELETE the right row.
const evidenceRowId = reactive<Record<string, number>>({});
const persistError = ref("");

const catOpen = ref(false);
const query = ref("");
const onlyLinked = ref(false);
const chainSource = ref<CatalogSource | null>(null);

// Combined catalog: props.customCatalog if provided, merged with CATALOG + dynamic backend items
const backendCatalog = ref<CatalogSource[]>([]);
const catalog = computed(() => {
  const base = props.customCatalog?.length ? props.customCatalog : CATALOG;
  if (!backendCatalog.value.length) return base;
  const map = new Map<string, CatalogSource>();
  for (const s of base) map.set(s.id, s);
  for (const s of backendCatalog.value) map.set(s.id, s);
  return Array.from(map.values());
});

async function loadBackendCatalog() {
  try {
    const res = await api<CatalogSource[]>("cases/catalog", { query: { limit: 150 } });
    if (res && Array.isArray(res)) {
      backendCatalog.value = res;
      registerDynamicSources(res);
    }
  } catch {
    // fallback
  }
}

watch(catOpen, (open) => {
  if (open && backendCatalog.value.length === 0) {
    void loadBackendCatalog();
  }
});

const derived = computed(() => deriveEvidence(linkedIds.value, catalog.value));
const isLinked = (id: string) => linkedIds.value.includes(id);

watch(
  derived,
  (d) => emit("change", { count: d.linked.length, label: d.state.label, tone: d.state.tone, key: d.state.key, linkedIds: [...linkedIds.value] }),
  { immediate: true, deep: false }
);

// --- Persistence (optimistic) --------------------------------------------
async function persistLink(src: CatalogSource) {
  try {
    const res = await api<{ id: number }>(`cases/${props.leadId}/evidence`, {
      method: "POST",
      body: evidencePayload(src),
    });
    if (res?.id != null) evidenceRowId[src.id] = res.id;
  } catch (err: any) {
    persistError.value = err?.data?.detail || "No se pudo guardar el vínculo; se mantiene localmente.";
  }
}
async function persistUnlink(id: string) {
  const rowId = evidenceRowId[id];
  if (rowId == null) return;
  try {
    await api(`cases/${props.leadId}/evidence/${rowId}`, { method: "DELETE" });
    delete evidenceRowId[id];
  } catch (err: any) {
    persistError.value = err?.data?.detail || "No se pudo quitar el vínculo en el servidor.";
  }
}

function link(src: CatalogSource) {
  if (isLinked(src.id)) return;
  linkedIds.value = [...linkedIds.value, src.id];
  persistError.value = "";
  void persistLink(src);
}
function unlink(id: string) {
  if (!isLinked(id)) return;
  linkedIds.value = linkedIds.value.filter((x) => x !== id);
  persistError.value = "";
  void persistUnlink(id);
}
function toggle(src: CatalogSource) {
  isLinked(src.id) ? unlink(src.id) : link(src);
}
function linkExample() {
  for (const id of EXAMPLE_LINK) {
    const src = CATALOG.find((s) => s.id === id);
    if (src) link(src);
  }
}

// --- Catalog drawer filtering --------------------------------------------
const catalogFiltered = computed(() => {
  const q = query.value.trim().toLowerCase();
  return catalog.value.filter((s) => {
    if (onlyLinked.value && !isLinked(s.id)) return false;
    if (!q) return true;
    return s.title.toLowerCase().includes(q) || s.id.toLowerCase().includes(q);
  });
});

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
const REL_ACCENT: Record<Relation, string> = {
  Respalda: "border-t-success",
  Contradice: "border-t-destructive",
  Contexto: "border-t-ink-muted",
};
const REL_LABEL_COLOR: Record<Relation, string> = {
  Respalda: "text-success",
  Contradice: "text-destructive",
  Contexto: "text-ink-muted",
};
function kindClass(type: string) {
  switch (type) {
    case "Noticia": return "text-info bg-info/10";
    case "Documento": return "text-primary bg-primary-soft";
    case "Indicador": return "text-teal-700 dark:text-teal-300 bg-teal-500/15";
    case "Evento": return "text-warning bg-warning/10";
    default: return "text-ink-muted bg-surface-sunken";
  }
}
function kindTone(kind: string) {
  switch (kind) {
    case "noticia": return "text-info bg-info/10";
    case "documento": return "text-primary bg-primary-soft";
    case "indicador": return "text-teal-700 dark:text-teal-300 bg-teal-500/15";
    case "evento": return "text-warning bg-warning/10";
    case "entidad": return "text-purple-700 dark:text-purple-300 bg-purple-500/15";
    case "correlación": return "text-ink bg-surface-sunken";
    default: return "text-ink-muted bg-surface-sunken"; // procedencia
  }
}
const meter = computed(() => {
  const n = Math.min(derived.value.primN, 2);
  return { n, a: n >= 1, b: n >= 2 };
});
function cardVia(card: LaneCard) {
  return card.head.m;
}
function replicaNote(card: LaneCard) {
  return card.members.length > 1 ? `+${card.members.length - 1} réplicas · cuentan como 1` : "";
}

const chain = computed(() => (chainSource.value ? buildSourceChain(chainSource.value.id) : null));
function nodeRelClass(rel: string) {
  if (rel === "Respalda" || rel === "Corrobora") return "text-success border-success/40 bg-success/10";
  if (rel === "Contradice") return "text-destructive border-destructive/40 bg-destructive/10";
  return "text-ink-muted border-border bg-surface";
}
function openChain(card: LaneCard) {
  chainSource.value = card.head;
  selectedNode.value = null;
}

// Node detail modal — opened by clicking a node inside the chain tree.
const selectedNode = ref<ChainNode | null>(null);
function openNode(node: ChainNode) {
  selectedNode.value = node;
}
function nodeLinked(node: ChainNode) {
  return node.catId != null && isLinked(node.catId);
}
function toggleNode(node: ChainNode) {
  if (!node.catId) return;
  const src = CATALOG.find((s) => s.id === node.catId);
  if (src) toggle(src);
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Evidence state + requirement checklist -->
    <div class="flex flex-col gap-3 rounded-md border p-4 transition-colors" :class="STATE_CARD[derived.state.tone]">
      <div class="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span class="font-serif text-heading-md" :class="STATE_TEXT[derived.state.tone]">
          Evidencia {{ derived.state.label }}
        </span>
        <span class="text-body-sm text-ink">{{ derived.state.short }}</span>
      </div>

      <!-- Primaries meter -->
      <div class="flex items-center gap-1.5">
        <span class="h-1.5 w-6 rounded-full transition-colors" :class="meter.a ? (meter.b ? 'bg-success' : 'bg-warning') : 'bg-border'" />
        <span class="h-1.5 w-6 rounded-full transition-colors" :class="meter.b ? 'bg-success' : 'bg-border'" />
        <span class="ml-1 font-mono text-caption text-ink-muted">{{ meter.n }}/2 primarias</span>
      </div>

      <div class="flex flex-col overflow-hidden rounded-md border border-border bg-surface">
        <div
          v-for="(ck, i) in derived.checks"
          :key="ck.label"
          class="grid grid-cols-[22px_minmax(0,1fr)_auto] items-center gap-3 px-3.5 py-2.5"
          :class="i < derived.checks.length - 1 ? 'border-b border-surface-sunken' : ''"
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
        <span class="text-caption text-ink-muted">Toca una fuente para ver su cadena de evidencia.</span>
      </div>
      <div v-if="!readonly" class="flex flex-wrap gap-2">
        <Button variant="outline" @click="linkExample">Vincular ejemplo</Button>
        <Button @click="catOpen = true">+ Vincular fuentes</Button>
      </div>
    </div>

    <p v-if="persistError" class="text-caption text-destructive">{{ persistError }}</p>

    <!-- Role lanes -->
    <div class="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] items-start gap-3">
      <div
        v-for="lane in derived.lanes"
        :key="lane.rel"
        class="flex flex-col gap-2 rounded-md border-t-[3px] bg-surface-sunken p-3"
        :class="REL_ACCENT[lane.rel]"
      >
        <div class="flex items-center justify-between">
          <span class="text-label uppercase" :class="REL_LABEL_COLOR[lane.rel]">{{ lane.label }}</span>
          <span class="font-mono text-caption text-ink-muted">{{ lane.cards.length }}</span>
        </div>

        <p v-if="!lane.cards.length" class="text-caption leading-relaxed text-ink-muted">
          {{ lane.empty }}
        </p>

        <button
          v-for="card in lane.cards"
          :key="card.key"
          type="button"
          class="flex flex-col gap-1.5 rounded-md border border-border bg-surface p-3 text-left transition-shadow hover:shadow-ev-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/25"
          @click="openChain(card)"
        >
          <div class="flex flex-wrap items-center gap-1.5">
            <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="kindClass(card.head.type)">
              {{ card.head.type.toLowerCase() }}
            </span>
            <span class="font-mono text-caption text-ink-muted">{{ card.head.id }}</span>
            <span
              v-if="card.primary"
              class="rounded-full border border-success/40 bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success"
            >
              primaria
            </span>
          </div>
          <span class="text-body-sm leading-snug">{{ card.head.title }}</span>
          <div class="flex flex-wrap items-center gap-x-2.5 gap-y-1 font-mono text-[11px] text-ink-muted">
            <span>vía {{ cardVia(card) }}</span>
            <span v-if="card.members.length > 1">{{ replicaNote(card) }}</span>
          </div>
          <div v-if="card.chain.levels.length" class="flex flex-wrap items-center gap-x-2.5 gap-y-1">
            <span class="font-mono text-[11px] text-ink-muted">
              {{ card.chain.counts.ent }} ent · {{ card.chain.counts.datos }} datos · {{ card.chain.counts.corr }} corr
            </span>
            <span
              v-if="card.chain.contradictions"
              class="rounded-full bg-destructive px-2 py-0.5 text-[10px] font-semibold uppercase text-white"
            >
              ▲ {{ card.chain.contradictions }} {{ card.chain.contradictions === 1 ? "contradicción" : "contradicciones" }}
            </span>
          </div>
        </button>
      </div>
    </div>

    <!-- Footer nav -->
    <div v-if="!readonly" class="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
      <Button variant="outline" @click="emit('back')">← Atrás</Button>
      <Button :disabled="!derived.linked.length" @click="emit('continue')">
        Continuar · Contexto →
      </Button>
    </div>

    <!-- Catalog drawer -->
    <Sheet v-model:open="catOpen">
      <SheetContent side="right" class="flex w-full flex-col gap-0 p-0 sm:max-w-[560px]">
        <div class="flex flex-col gap-1 border-b border-border px-5 py-4 pr-12">
          <SheetTitle class="font-serif text-heading-md text-ink">Vincular fuentes</SheetTitle>
          <SheetDescription class="text-caption text-ink-muted">
            Catálogo de ingesta · cada fuente vinculada se agrega al árbol como nodo N1
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
              Todas · {{ CATALOG.length }}
            </button>
            <button
              type="button"
              class="h-8 rounded-full border px-3 text-caption font-semibold transition-colors"
              :class="onlyLinked ? 'border-ink bg-ink text-on-primary' : 'border-border bg-surface text-ink'"
              @click="onlyLinked = true"
            >
              Vinculadas · {{ linkedIds.length }}
            </button>
          </div>
        </div>

        <div
          v-for="src in catalogFiltered"
          :key="src.id"
          class="flex flex-wrap items-center gap-2 border-b border-border px-5 py-3 transition-colors"
          :class="isLinked(src.id) ? 'bg-primary-soft/40' : ''"
        >
          <span class="shrink-0 rounded-sm bg-surface-sunken px-1 font-mono text-caption text-ink-muted">{{ src.id }}</span>
          <span class="min-w-0 flex-1 basis-[200px] text-body-sm leading-snug">{{ src.title }}</span>
          <span class="flex items-center gap-1.5 whitespace-nowrap text-caption font-semibold" :class="REL_LABEL_COLOR[src.rel]">
            <span class="h-2 w-2 rounded-full" :class="REL_ACCENT[src.rel].replace('border-t-', 'bg-')" />
            {{ src.rel }}
          </span>
          <button
            type="button"
            class="ml-auto h-8 min-w-[96px] rounded-md border px-3 text-caption font-semibold transition-colors"
            :class="isLinked(src.id)
              ? 'border-border bg-surface text-ink hover:bg-surface-sunken'
              : 'border-transparent bg-primary text-on-primary hover:bg-primary-deep'"
            @click="toggle(src)"
          >
            {{ isLinked(src.id) ? "Quitar" : "Vincular" }}
          </button>
        </div>

        <p v-if="!catalogFiltered.length" class="px-5 py-4 text-body-sm text-ink-muted">Sin resultados.</p>
        </div>

        <div class="flex items-center justify-between gap-3 border-t border-border px-5 py-4">
          <span class="text-caption text-ink-muted">{{ linkedIds.length }} fuentes vinculadas</span>
          <Button variant="outline" @click="catOpen = false">Listo</Button>
        </div>
      </SheetContent>
    </Sheet>

    <!-- Evidence-chain drawer — the source's hierarchical tree only.
         Clicking a node opens its detail modal. -->
    <Sheet :open="!!chainSource" @update:open="(v) => { if (!v) chainSource = null; }">
      <SheetContent side="right" class="flex w-full flex-col gap-0 p-0 sm:max-w-[480px]">
        <div class="flex flex-col gap-1 border-b border-border px-5 py-4 pr-12">
          <SheetTitle class="font-serif text-heading-md text-ink">
            {{ chainSource ? `Cadena de evidencia · ${chainSource.id}` : "" }}
          </SheetTitle>
          <SheetDescription class="text-caption text-ink-muted">
            Toca un nodo para ver su ficha completa.
          </SheetDescription>
        </div>
      <div v-if="chain" class="min-h-0 flex-1 overflow-y-auto flex flex-col gap-3 px-5 py-4">
        <!-- N0 · central claim (tree root) -->
        <button
          type="button"
          class="flex flex-col gap-1.5 rounded-md border border-primary/40 bg-primary-soft/40 p-3 text-left transition-shadow hover:shadow-ev-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/25"
          @click="openNode(chain.claim)"
        >
          <span class="font-mono text-[11px] uppercase tracking-wide text-ink-muted">N0 · Afirmación central</span>
          <span class="text-body-sm italic leading-snug text-ink">{{ chain.claim.title }}</span>
        </button>

        <!-- N1..N5, grouped by level and indented -->
        <div
          v-for="lvl in chain.levels"
          :key="lvl.level"
          class="flex flex-col gap-1.5 border-l border-border pl-3"
          :style="{ marginLeft: (lvl.level - 1) * 10 + 'px' }"
        >
          <span class="font-mono text-[11px] uppercase tracking-wide text-ink-muted">N{{ lvl.level }} · {{ lvl.name }}</span>
          <button
            v-for="node in lvl.nodes"
            :key="node.id"
            type="button"
            class="flex flex-col gap-1 rounded-md border bg-surface px-3 py-2 text-left transition-shadow hover:shadow-ev-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/25"
            :class="node.rel === 'Contradice' ? 'border-destructive/50' : 'border-border'"
            @click="openNode(node)"
          >
            <div class="flex flex-wrap items-center gap-1.5">
              <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="kindTone(node.kind)">
                {{ node.kind }}
              </span>
              <span class="font-mono text-caption text-ink-muted">{{ node.id }}</span>
              <span
                v-if="node.rel"
                class="rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase"
                :class="nodeRelClass(node.rel)"
              >
                {{ node.rel }}
              </span>
            </div>
            <span class="text-caption leading-snug">{{ node.title }}</span>
          </button>
        </div>
      </div>
      </SheetContent>
    </Sheet>

    <!-- Node detail modal — the complete evidence information. -->
    <Dialog :open="!!selectedNode" @update:open="(v) => { if (!v) selectedNode = null; }">
      <DialogContent class="flex max-h-[calc(100vh-48px)] flex-col gap-0 overflow-hidden p-0 sm:max-w-[640px]">
        <div v-if="selectedNode" class="flex min-h-0 flex-1 flex-col">
        <div class="flex flex-col gap-1 border-b border-border px-5 py-4 pr-12">
          <DialogTitle class="font-serif text-heading-md text-ink">{{ selectedNode.title }}</DialogTitle>
          <DialogDescription class="font-mono text-caption text-ink-muted">
            N{{ selectedNode.depth }} · {{ selectedNode.levelName }}
          </DialogDescription>
        </div>
        <div class="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-5 py-4">
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold" :class="kindTone(selectedNode.kind)">
            {{ selectedNode.kind }}
          </span>
          <span class="font-mono text-caption text-ink-muted">{{ selectedNode.id }}</span>
          <span
            v-if="selectedNode.rel"
            class="rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase"
            :class="nodeRelClass(selectedNode.rel)"
          >
            {{ selectedNode.rel }} · {{ selectedNode.parentTitle }}
          </span>
        </div>

        <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-body-sm">
          <dt class="text-ink-muted">Fuente / medio</dt><dd>{{ selectedNode.medio }}</dd>
          <dt class="text-ink-muted">Fecha</dt><dd class="font-mono">{{ selectedNode.fecha }}</dd>
          <dt class="text-ink-muted">Alcance</dt><dd>{{ selectedNode.alcance }}</dd>
          <dt class="text-ink-muted">Rol en el caso</dt><dd>{{ selectedNode.role }}</dd>
        </dl>

        <blockquote class="rounded-md border-l-[3px] border-primary bg-primary-soft/40 px-3 py-2 text-body-sm italic text-ink">
          {{ selectedNode.excerpt }}
          <span class="mt-1 block font-mono text-caption not-italic text-ink-muted">{{ selectedNode.cite }}</span>
        </blockquote>

        <a
          :href="`https://ingesta.evidentia.app/f/${selectedNode.id}`"
          target="_blank"
          rel="noopener noreferrer"
          class="font-mono text-caption text-primary hover:underline"
        >
          Abrir en ingesta ↗
        </a>
        </div>

        <div
          v-if="selectedNode.catId && !readonly"
          class="flex items-center justify-between gap-3 border-t border-border px-5 py-4"
        >
          <span
            class="rounded-full border px-2 py-0.5 text-caption font-semibold"
            :class="nodeLinked(selectedNode) ? 'border-success/40 bg-success/10 text-success' : 'border-border bg-surface text-ink-muted'"
          >
            {{ nodeLinked(selectedNode) ? "Vinculada al caso" : "No vinculada" }}
          </span>
          <Button
            :variant="nodeLinked(selectedNode) ? 'outline' : 'default'"
            @click="toggleNode(selectedNode)"
          >
            {{ nodeLinked(selectedNode) ? "Desvincular" : "Vincular al caso" }}
          </Button>
        </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>
