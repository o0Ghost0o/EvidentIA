<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import Input from "~/components/ui/Input.vue";
import Select from "~/components/ui/Select.vue";
import StateChip from "~/components/ui/StateChip.vue";
import ScoreBreakdown from "~/components/ScoreBreakdown.vue";
import EvidenceDetailModal from "~/components/EvidenceDetailModal.vue";
import { api } from "~/composables/useApi";

const modalOpen = ref(false);
const activeSource = ref<{ tipo: string; id: string } | null>(null);

function inspectSource(sourceId: string) {
  activeSource.value = { tipo: "news", id: sourceId };
  modalOpen.value = true;
}

// Bandeja de temas — the prioritised inbox. Deterministic P ranking with traceable
// evidence; every row can be opened as a Lead (ficha de evidencia). Layout and
// behaviour follow the Bandeja design: summary tiles + band bar, a filter bar, and
// a dense row list whose score-breakdown is explainable on demand.
type Band = "alto" | "medio" | "bajo";
type Evidence = "suficiente" | "parcial" | "insuficiente";
type Modalidad = "tvn" | "banca";

interface RankItem {
  id: string;
  titulo: string;
  modalidad: Modalidad;
  ids_fuente: string[];
  group_size: number;
  dedup: { label: string; primary_sources: number; agency: string | null };
  P: number;
  components: Record<string, number>;
  weights: Record<string, number>;
  rules_version: string;
  band: Band;
  evidence_state: Evidence;
}

const BAND_TONE: Record<Band, "error" | "warning" | "neutral"> = {
  alto: "error",
  medio: "warning",
  bajo: "neutral",
};
const BAND_BAR: Record<Band, string> = {
  alto: "bg-error",
  medio: "bg-warning",
  bajo: "bg-ink-muted",
};
const EV_TONE: Record<Evidence, "success" | "warning" | "error"> = {
  suficiente: "success",
  parcial: "warning",
  insuficiente: "error",
};

const items = ref<RankItem[]>([]);
const loading = ref(true);
const error = ref("");
const rulesVersion = ref("v1.2");

// Filters. Modalidad is the scoring lens (server re-scores groups under it), so it
// drives a refetch; band / evidence / search are client-side over the loaded set.
const mod = ref<Modalidad>("tvn");
const q = ref("");
const fBand = ref<"all" | Band>("all");
const fEv = ref<"all" | Evidence>("all");
const sort = ref<"p" | "u" | "n">("p");

async function refresh() {
  loading.value = true;
  error.value = "";
  try {
    const res = await api<{ items: RankItem[]; rules_version: string }>("ranking", {
      query: { modalidad: mod.value },
    });
    items.value = res.items;
    if (res.rules_version) rulesVersion.value = res.rules_version;
  } catch {
    error.value = "No se pudo cargar el ranking. ¿Está corriendo el backend?";
    items.value = [];
  } finally {
    loading.value = false;
  }
}

watch(mod, refresh);
onMounted(refresh);

const hasAny = computed(() => items.value.length > 0);
const total = computed(() => items.value.length);

const bandCount = (b: Band) => items.value.filter((t) => t.band === b).length;
const insItems = computed(() => items.value.filter((t) => t.evidence_state === "insuficiente"));
const insAlto = computed(() => insItems.value.filter((t) => t.band === "alto").length);

const bar = computed(() =>
  (["alto", "medio", "bajo"] as Band[]).map((b) => ({ label: `Banda ${b}`, n: bandCount(b), c: BAND_BAR[b] }))
);

function toggleBand(b: Band) {
  fBand.value = fBand.value === b ? "all" : b;
}
function toggleEvInsuf() {
  fEv.value = fEv.value === "insuficiente" ? "all" : "insuficiente";
}

const summary = computed(() => [
  { key: "alto", label: "Alto", dot: BAND_BAR.alto, n: bandCount("alto"), cap: "P ≥ 70", active: fBand.value === "alto", red: false, onClick: () => toggleBand("alto"), title: "Filtrar banda alta" },
  { key: "medio", label: "Medio", dot: BAND_BAR.medio, n: bandCount("medio"), cap: "P 40–69", active: fBand.value === "medio", red: false, onClick: () => toggleBand("medio"), title: "Filtrar banda media" },
  { key: "bajo", label: "Bajo", dot: BAND_BAR.bajo, n: bandCount("bajo"), cap: "P < 40", active: fBand.value === "bajo", red: false, onClick: () => toggleBand("bajo"), title: "Filtrar banda baja" },
  { key: "ins", label: "Evid. insuficiente", dot: "bg-error", n: insItems.value.length, cap: `${insAlto.value} en banda alta`, active: fEv.value === "insuficiente", red: insItems.value.length > 0, onClick: toggleEvInsuf, title: "Filtrar evidencia insuficiente" },
]);

const hasFilters = computed(
  () => !!q.value.trim() || fBand.value !== "all" || fEv.value !== "all"
);
function clearFilters() {
  q.value = "";
  fBand.value = "all";
  fEv.value = "all";
}

const sortKey: Record<"p" | "u" | "n", (t: RankItem) => number> = {
  p: (t) => t.P,
  u: (t) => t.components.U ?? 0,
  n: (t) => t.components.N ?? 0,
};
const sortLabel = computed(
  () => ({ p: "orden P desc", u: "orden urgencia desc", n: "orden novedad desc" })[sort.value]
);

const filtered = computed(() => {
  const term = q.value.trim().toLowerCase();
  const list = items.value.filter(
    (t) =>
      (fBand.value === "all" || t.band === fBand.value) &&
      (fEv.value === "all" || t.evidence_state === fEv.value) &&
      (!term || t.titulo.toLowerCase().includes(term) || t.id.toLowerCase().includes(term))
  );
  const key = sortKey[sort.value];
  return [...list].sort((a, b) => key(b) - key(a) || b.P - a.P);
});

const shown = computed(() => filtered.value.length);
const noResults = computed(() => hasAny.value && filtered.value.length === 0);

interface Row {
  item: RankItem;
  rank: string;
  shortId: string;
  flag: boolean;
  dedupText: string;
  dedupReplica: boolean;
  dedupTitle: string;
  bandLabel: string;
  bandTone: "error" | "warning" | "neutral";
  evTone: "success" | "warning" | "error";
  evVariant: "soft" | "outline";
}

const rows = computed<Row[]>(() =>
  filtered.value.map((item, i) => {
    const proc = item.dedup.primary_sources;
    const replica = item.dedup.label === "repetition" || (proc === 1 && item.group_size > 1);
    return {
      item,
      rank: String(i + 1).padStart(2, "0"),
      shortId: item.id.replace(/^solo:/, ""),
      flag: item.evidence_state === "insuficiente" && item.band === "alto",
      dedupText: proc === 1 ? "1 procedencia" : `${proc} procedencias`,
      dedupReplica: replica,
      dedupTitle: replica
        ? `${item.group_size} notas replican ${item.dedup.agency || "una sola fuente"} · cuentan como 1 procedencia`
        : "Procedencias independientes tras deduplicar",
      bandLabel: item.band,
      bandTone: BAND_TONE[item.band],
      evTone: EV_TONE[item.evidence_state],
      evVariant: item.evidence_state === "insuficiente" ? "outline" : "soft",
    };
  })
);

const modOptions = [
  { value: "tvn", label: "TVN" },
  { value: "banca", label: "Banca" },
];
const bandOptions = [
  { value: "all", label: "Todas las bandas" },
  { value: "alto", label: "Banda alta" },
  { value: "medio", label: "Banda media" },
  { value: "bajo", label: "Banda baja" },
];
const evOptions = [
  { value: "all", label: "Toda la evidencia" },
  { value: "suficiente", label: "Evidencia suficiente" },
  { value: "parcial", label: "Evidencia parcial" },
  { value: "insuficiente", label: "Evidencia insuficiente" },
];
const sortOptions = [
  { value: "p", label: "Orden: P ↓" },
  { value: "u", label: "Orden: Urgencia ↓" },
  { value: "n", label: "Orden: Novedad ↓" },
];

async function openAsLead(item: RankItem) {
  const created = await api<{ id: number }>("cases", {
    method: "POST",
    body: { titulo: item.titulo, modalidad: item.modalidad, queries: [item.titulo] },
  });
  await navigateTo(`/leads/${created.id}`);
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <!-- Page header -->
    <div class="flex flex-col gap-2">
      <h1 class="font-serif text-display-xl text-ink">Bandeja de temas</h1>
      <p class="max-w-[64ch] text-body-sm text-ink-muted">
        Priorización determinista con evidencia trazable
      </p>
    </div>

    <p v-if="error" class="rounded-md border border-error/50 bg-error/5 p-3 text-body-sm text-ink">
      {{ error }}
    </p>

    <p v-if="loading" class="py-10 text-center text-body-sm text-ink-muted">Cargando bandeja…</p>

    <!-- Populated state -->
    <template v-else-if="hasAny">
      <!-- Summary: band bar + stat tiles -->
      <div class="flex flex-col gap-3 rounded-md border border-hairline bg-surface p-4 shadow-ev-1">
        <div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <span class="text-label uppercase text-ink-muted">Resumen</span>
          <span class="font-mono text-caption tabular-nums text-ink-muted">
            {{ total }} temas · reglas {{ rulesVersion }}
          </span>
        </div>
        <div class="flex h-2 gap-0.5 overflow-hidden rounded-full bg-surface-sunken">
          <div
            v-for="b in bar"
            :key="b.label"
            :title="`${b.label} · ${b.n}`"
            class="h-full"
            :class="b.c"
            :style="{ flex: `${b.n} 1 0` }"
          />
        </div>
        <div class="grid grid-cols-[repeat(auto-fit,minmax(150px,1fr))] gap-2">
          <button
            v-for="s in summary"
            :key="s.key"
            type="button"
            :title="s.title"
            class="flex min-h-[44px] flex-col items-start gap-1 rounded-md border px-3 py-2.5 text-left transition-colors hover:border-ink-muted"
            :class="s.active ? 'border-primary/40 bg-primary-soft' : 'border-hairline bg-surface'"
            @click="s.onClick"
          >
            <span class="flex items-center gap-2 text-label uppercase text-ink-muted">
              <span class="h-2 w-2 rounded-full" :class="s.dot" />{{ s.label }}
            </span>
            <span
              class="font-mono text-[28px] font-medium leading-none tabular-nums"
              :class="s.red ? 'text-error' : 'text-ink'"
            >
              {{ s.n }}
            </span>
            <span class="font-mono text-caption text-ink-muted">{{ s.cap }}</span>
          </button>
        </div>
      </div>

      <!-- Filter bar -->
      <div class="flex flex-wrap items-center gap-x-3 gap-y-2">
        <Input
          v-model="q"
          placeholder="Buscar tema o #id"
          class="min-w-0 flex-1 basis-[220px] font-mono"
        />
        <!-- Modalidad segmented control (scoring lens) -->
        <div class="flex gap-0.5 rounded-md bg-surface-sunken p-0.5">
          <button
            v-for="m in modOptions"
            :key="m.value"
            type="button"
            class="h-8 rounded-sm px-3 text-body-sm font-semibold transition-colors"
            :class="
              mod === m.value
                ? 'bg-surface text-ink shadow-ev-1'
                : 'bg-transparent text-ink-muted hover:text-ink'
            "
            @click="mod = m.value as Modalidad"
          >
            {{ m.label }}
          </button>
        </div>
        <Select v-model="fBand" :options="bandOptions" class="w-auto min-w-[160px]" />
        <Select v-model="fEv" :options="evOptions" class="w-auto min-w-[180px]" />
        <div class="ml-auto flex items-center gap-2">
          <Select v-model="sort" :options="sortOptions" class="w-auto min-w-[150px]" />
          <span
            title="Reglas de priorización · pesos 30 / 25 / 20 / 15 / 10"
            class="whitespace-nowrap rounded-md border border-hairline bg-surface-sunken px-1.5 py-0.5 font-mono text-caption text-ink-muted"
          >
            reglas {{ rulesVersion }}
          </span>
          <button
            v-if="hasFilters"
            type="button"
            class="h-9 whitespace-nowrap px-2 text-body-sm font-semibold text-ink-muted transition-colors hover:text-ink"
            @click="clearFilters"
          >
            Limpiar filtros
          </button>
        </div>
      </div>

      <!-- Rows -->
      <template v-if="shown">
        <div class="overflow-hidden rounded-md border border-hairline bg-surface shadow-ev-1">
          <!-- Column header (md+) -->
          <div
            class="hidden items-center gap-6 bg-surface-sunken px-4 py-2.5 pl-[19px] text-label uppercase text-ink-muted md:flex"
          >
            <span class="min-w-0 flex-[1_1_340px]">Tema</span>
            <span class="flex-[0_0_96px]">Prioridad</span>
            <span class="flex-[0_0_188px]">R · I · U · N · E</span>
            <span class="flex-[0_0_184px]">Evidencia · acción</span>
          </div>

          <div
            v-for="(r, i) in rows"
            :key="r.item.id"
            class="relative flex flex-wrap items-center gap-x-6 gap-y-3 bg-surface py-4 pl-[19px] pr-4"
            :class="i > 0 ? 'border-t border-hairline' : ''"
            :style="{ boxShadow: `inset 3px 0 0 var(--row-band)` }"
            :data-band="r.item.band"
          >
            <!-- Tema -->
            <div class="flex min-w-0 flex-[1_1_340px] flex-col gap-2">
              <div class="flex flex-wrap items-center gap-x-2.5 gap-y-1">
                <span class="font-mono text-caption tabular-nums text-ink-muted">{{ r.rank }}</span>
                <span
                  class="truncate rounded-sm bg-surface-sunken px-1 font-mono text-[13px] text-ink-muted"
                  :title="r.item.id"
                >#{{ r.shortId }}</span>
                <span
                  class="rounded-full border border-hairline bg-surface-sunken px-2.5 py-0.5 text-caption font-semibold uppercase text-ink"
                >{{ r.item.modalidad }}</span>
              </div>
              <span class="font-serif text-heading-md text-ink">{{ r.item.titulo }}</span>
              <div
                class="flex flex-wrap items-center gap-x-2 gap-y-0.5 font-mono text-caption tabular-nums text-ink-muted"
              >
                <span>{{ r.item.group_size }} notas</span>
                <span aria-hidden="true">·</span>
                <span :title="r.dedupTitle" :class="r.dedupReplica ? 'text-warning' : ''">
                  {{ r.dedupText }}
                </span>
              </div>

              <!-- Sources 1-click preview -->
              <div v-if="r.item.ids_fuente && r.item.ids_fuente.length" class="flex flex-wrap items-center gap-1.5 pt-0.5">
                <span class="text-[11px] font-mono text-ink-muted">Fuentes:</span>
                <button
                  v-for="srcId in r.item.ids_fuente.slice(0, 3)"
                  :key="srcId"
                  type="button"
                  class="inline-flex items-center gap-1 rounded bg-surface-sunken px-1.5 py-0.5 font-mono text-[11px] text-ink-muted border border-hairline transition-colors hover:border-primary hover:text-primary cursor-pointer"
                  :title="`Inspeccionar contenido de la noticia ${srcId}`"
                  @click.stop="inspectSource(srcId)"
                >
                  <svg class="h-3 w-3 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  <span>{{ srcId }}</span>
                </button>
                <span v-if="r.item.ids_fuente.length > 3" class="text-caption font-mono text-ink-muted">
                  +{{ r.item.ids_fuente.length - 3 }} más
                </span>
              </div>
            </div>

            <!-- Prioridad -->
            <div class="flex flex-[0_0_96px] flex-col items-start gap-1.5">
              <span
                class="font-mono text-[32px] font-medium leading-none tabular-nums tracking-[-0.5px] text-ink"
                :title="`P = ${r.item.P}`"
              >{{ r.item.P }}</span>
              <StateChip :tone="r.bandTone">{{ r.bandLabel }}</StateChip>
            </div>

            <!-- R · I · U · N · E breakdown -->
            <div class="flex-[0_0_188px]">
              <ScoreBreakdown
                :components="r.item.components"
                :weights="r.item.weights"
                :p="r.item.P"
                :band-label="r.bandLabel"
                :rules-version="rulesVersion"
                :flag="r.flag"
              />
            </div>

            <!-- Evidencia · acción -->
            <div class="flex flex-[0_0_184px] flex-col items-stretch gap-2">
              <div class="flex flex-wrap items-center gap-1.5">
                <StateChip :tone="r.evTone" :variant="r.evVariant" dot>
                  Evidencia {{ r.item.evidence_state }}
                </StateChip>
              </div>
              <span
                v-if="r.flag"
                title="Prioridad alta con evidencia insuficiente: el borrador quedará bloqueado en el Lead"
                class="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.4px] text-error"
              >
                <span class="h-2 w-2 rotate-45 border-[1.5px] border-error" aria-hidden="true" />
                Investigar, no publicar
              </span>
              <button
                type="button"
                title="Crea un Lead en el paso 1 · Definir con este tema"
                class="h-9 whitespace-nowrap rounded-md border border-primary/40 bg-primary-soft px-3 text-body-sm font-semibold text-primary transition-colors hover:border-primary"
                @click="openAsLead(r.item)"
              >
                Abrir como Lead
              </button>
            </div>
          </div>
        </div>
        <span class="font-mono text-caption text-ink-muted">
          {{ shown }} de {{ total }} temas · {{ sortLabel }} · desempate por P
        </span>
      </template>

      <!-- No results for current filters -->
      <div
        v-else
        class="flex flex-col items-center gap-3 rounded-md border-[1.5px] border-dashed border-hairline px-6 py-8 text-center"
      >
        <span class="font-serif text-heading-md text-ink">Ningún tema coincide</span>
        <span class="max-w-[48ch] text-body-sm text-ink-muted">
          Prueba con otra banda, estado de evidencia o modalidad.
        </span>
        <button
          type="button"
          class="h-9 whitespace-nowrap rounded-md border border-hairline px-3 text-body-sm font-semibold text-ink transition-colors hover:bg-surface-sunken"
          @click="clearFilters"
        >
          Limpiar filtros
        </button>
      </div>
    </template>

    <!-- Empty state (no topics at all) -->
    <div
      v-else
      class="flex flex-col items-center gap-3 rounded-lg border-[1.5px] border-dashed border-hairline bg-surface px-6 py-12 text-center"
    >
      <span class="rounded-md bg-surface-sunken px-1.5 font-mono text-caption text-ink-muted">
        0 temas · reglas {{ rulesVersion }}
      </span>
      <span class="font-serif text-display-lg text-ink">Sin temas · ejecuta una ingesta</span>
      <span class="max-w-[46ch] text-body-sm text-ink-muted">
        La bandeja se llena al procesar fuentes: cada tema llega agrupado, deduplicado y con su
        prioridad P calculada con las mismas reglas.
      </span>
      <NuxtLink
        to="/ingest"
        class="mt-1 flex h-9 items-center rounded-md border border-hairline px-3 text-body-sm font-semibold text-ink no-underline transition-colors hover:bg-surface-sunken"
      >
        Ir a Ingesta →
      </NuxtLink>
    </div>

    <!-- Evidence detail interactive modal -->
    <EvidenceDetailModal
      v-model:open="modalOpen"
      :tipo="activeSource?.tipo"
      :id="activeSource?.id"
      @navigate="(t, i) => { activeSource = { tipo: t, id: i }; modalOpen = true; }"
    />
  </div>
</template>

<style scoped>
/* Priority band accent on the left edge of each row (DESIGN: inset band marker). */
[data-band="alto"] {
  --row-band: hsl(var(--error));
}
[data-band="medio"] {
  --row-band: hsl(var(--warning));
}
[data-band="bajo"] {
  --row-band: hsl(var(--ink-muted));
}
</style>
