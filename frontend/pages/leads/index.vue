<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import Button from "~/components/ui/Button.vue";
import Input from "~/components/ui/Input.vue";
import Select from "~/components/ui/Select.vue";
import StateChip, { type StateTone } from "~/components/ui/StateChip.vue";
import { Tabs, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { ToggleGroup, ToggleGroupItem } from "~/components/ui/toggle-group";
import { api } from "~/composables/useApi";
import {
  deriveEvidenceState,
  deriveProgress,
  deriveReviewer,
  evidenceTone,
  formatUpdated,
  modalidadLabel,
  reviewMeta,
  REVIEW_ORDER,
  STEP_TOTAL,
  type ReviewState,
} from "~/lib/leadList";

interface EvidenceRef {
  fuente_tipo: string;
  rol?: string | null;
}
interface NoteRef {
  autor: string;
  created_at?: string | null;
}
interface CaseItem {
  id: number;
  titulo: string;
  modalidad: string;
  estado: string;
  flags: string[];
  evidence: EvidenceRef[];
  notes: NoteRef[];
  created_at?: string | null;
  updated_at?: string | null;
}

const cases = ref<CaseItem[]>([]);
const loading = ref(true);

// Filters — the controls from the design (tabs + search + modalidad + evidence + sort).
const reviewFilter = ref<"all" | ReviewState>("all");
const query = ref("");
const modalidadFilter = ref<"all" | "tvn" | "banca">("all");
const evidenceFilter = ref<"all" | "suficiente" | "parcial" | "insuficiente" | "none">("all");
const sortOrder = ref<"recent" | "oldest">("recent");

// A single-select toggle lets you click the active item off; keep "Todas" as the
// floor so the modalidad filter is never left blank.
watch(modalidadFilter, (v) => {
  if (!v) modalidadFilter.value = "all";
});

const evidenceOptions = [
  { value: "all", label: "Toda la evidencia" },
  { value: "suficiente", label: "Evidencia suficiente" },
  { value: "parcial", label: "Evidencia parcial" },
  { value: "insuficiente", label: "Evidencia insuficiente" },
  { value: "none", label: "Sin fuentes" },
];

const sortOptions = [
  { value: "recent", label: "Más reciente primero" },
  { value: "oldest", label: "Más antiguo primero" },
];

async function refresh() {
  loading.value = true;
  try {
    const res = await api<{ items: CaseItem[] }>("cases");
    cases.value = res.items;
  } finally {
    loading.value = false;
  }
}
onMounted(refresh);

// A lead row with every datum the list renders, all derived from real fields.
interface LeadRow {
  raw: CaseItem;
  review: ReturnType<typeof reviewMeta>;
  evidence: ReturnType<typeof deriveEvidenceState>;
  progress: ReturnType<typeof deriveProgress>;
  reviewer: ReturnType<typeof deriveReviewer>;
  sources: number;
  updated: string;
}

function toRow(c: CaseItem): LeadRow {
  const sources = c.evidence?.length ?? 0;
  return {
    raw: c,
    review: reviewMeta(c.estado),
    evidence: deriveEvidenceState(c.evidence ?? []),
    progress: deriveProgress(c.estado, sources),
    reviewer: deriveReviewer(c.notes ?? []),
    sources,
    updated: formatUpdated(c.updated_at),
  };
}

const allRows = computed<LeadRow[]>(() => cases.value.map(toRow));

// Counts per review state, over the whole set — drives the summary bar + tabs.
const reviewCounts = computed<Record<string, number>>(() => {
  const acc: Record<string, number> = {};
  for (const r of allRows.value) acc[r.review.key] = (acc[r.review.key] ?? 0) + 1;
  return acc;
});

const total = computed(() => allRows.value.length);
const lastActivity = computed(() => {
  const stamps = cases.value
    .map((c) => c.updated_at)
    .filter(Boolean)
    .sort((a, b) => String(b).localeCompare(String(a)));
  return formatUpdated(stamps[0] ?? null);
});

// Review states actually present, in lifecycle order — for the bar and the tabs.
const presentStates = computed(() => REVIEW_ORDER.filter((s) => (reviewCounts.value[s] ?? 0) > 0));

const hasFilters = computed(
  () =>
    reviewFilter.value !== "all" ||
    modalidadFilter.value !== "all" ||
    evidenceFilter.value !== "all" ||
    sortOrder.value !== "recent" ||
    query.value.trim() !== "",
);

function clearFilters() {
  reviewFilter.value = "all";
  modalidadFilter.value = "all";
  evidenceFilter.value = "all";
  sortOrder.value = "recent";
  query.value = "";
}

const rows = computed<LeadRow[]>(() => {
  const q = query.value.trim().toLowerCase();
  const filtered = allRows.value.filter((r) => {
    if (reviewFilter.value !== "all" && r.review.key !== reviewFilter.value) return false;
    if (modalidadFilter.value !== "all" && r.raw.modalidad !== modalidadFilter.value) return false;
    if (evidenceFilter.value !== "all" && r.evidence.key !== evidenceFilter.value) return false;
    if (q) {
      const hay = `${r.raw.titulo} #${r.raw.id}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  return filtered.sort((a, b) => {
    const timeA = a.raw.created_at ? new Date(a.raw.created_at).getTime() : 0;
    const timeB = b.raw.created_at ? new Date(b.raw.created_at).getTime() : 0;
    if (timeA && timeB && timeA !== timeB) {
      return sortOrder.value === "recent" ? timeB - timeA : timeA - timeB;
    }
    return sortOrder.value === "recent" ? b.raw.id - a.raw.id : a.raw.id - b.raw.id;
  });
});

const isEmpty = computed(() => !loading.value && total.value === 0);
const noResults = computed(() => !loading.value && total.value > 0 && rows.value.length === 0);

// Map a status tone onto its semantic color token (bar segments, step dots, accent).
const TONE_VAR: Record<StateTone, string> = {
  success: "hsl(var(--success))",
  warning: "hsl(var(--warning))",
  error: "hsl(var(--error))",
  info: "hsl(var(--info))",
  primary: "hsl(var(--primary))",
  neutral: "hsl(var(--ink-muted))",
};

function openLead(id: number) {
  navigateTo(`/leads/${id}`);
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <!-- Page header -->
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div class="flex min-w-0 flex-1 basis-[480px] flex-col gap-2">
        <h1 class="font-serif text-display-xl text-ink">Leads — Fichas de Evidencia</h1>
        <p class="max-w-[64ch] text-body-sm text-ink-muted">
          Registro de las investigaciones que el equipo trabaja o ha cerrado. Cada ficha conserva su
          paso en el flujo, su evidencia y su estado de revisión.
        </p>
      </div>
      <NuxtLink to="/leads/new">
        <Button>+ Nuevo lead</Button>
      </NuxtLink>
    </div>

    <p v-if="loading" class="py-10 text-center text-body-sm text-ink-muted">Cargando leads…</p>

    <!-- Empty: no leads at all -->
    <div
      v-else-if="isEmpty"
      class="flex flex-col items-center gap-3 rounded-lg border border-dashed border-ink-muted/40 bg-surface px-6 py-12 text-center"
    >
      <span class="rounded-md bg-surface-sunken px-1.5 font-mono text-caption text-ink-muted">0 fichas</span>
      <span class="font-serif text-display-lg text-ink">No hay leads</span>
      <span class="max-w-[44ch] text-body-sm text-ink-muted">
        Crea el primero o ábrelo desde la Bandeja: cada señal que conviertas en lead aparecerá aquí
        con su evidencia y su estado de revisión.
      </span>
      <div class="mt-1 flex flex-wrap justify-center gap-2">
        <NuxtLink to="/leads/new"><Button variant="outline">Crear lead</Button></NuxtLink>
        <NuxtLink to="/" class="flex h-9 items-center px-3 text-body-sm font-semibold text-primary">
          Ir a la Bandeja →
        </NuxtLink>
      </div>
    </div>

    <template v-else>
      <!-- Summary: review-state distribution -->
      <div
        class="flex flex-col gap-3 rounded-md border border-hairline bg-surface p-4 shadow-ev-1"
      >
        <div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <span class="text-label uppercase text-ink-muted">Estado de revisión</span>
          <span class="font-mono text-caption tabular-nums text-ink-muted">
            {{ total }} leads · última actividad {{ lastActivity }}
          </span>
        </div>
        <div class="flex h-2 gap-0.5 overflow-hidden rounded-full bg-surface-sunken">
          <div
            v-for="s in presentStates"
            :key="s"
            :title="`${reviewMeta(s).label} · ${reviewCounts[s]}`"
            class="h-full"
            :style="{ flex: `${reviewCounts[s]} 1 0`, background: reviewMeta(s).barVar }"
          />
        </div>
        <div class="flex flex-wrap gap-x-6 gap-y-1">
          <button
            v-for="s in presentStates"
            :key="s"
            type="button"
            class="flex min-h-8 items-center gap-2 text-body-sm text-ink transition-colors hover:text-primary"
            @click="reviewFilter = reviewFilter === s ? 'all' : s"
          >
            <span class="h-2 w-2 rounded-full" :style="{ background: reviewMeta(s).barVar }" />
            <span>{{ reviewMeta(s).label }}</span>
            <span class="font-mono font-medium tabular-nums">{{ reviewCounts[s] }}</span>
          </button>
        </div>
      </div>

      <!-- Tabs (review-state filter) + filters -->
      <div class="flex flex-col gap-3">
        <Tabs v-model="reviewFilter">
          <TabsList
            class="h-auto w-full justify-start gap-1 overflow-x-auto rounded-none border-b border-hairline bg-transparent p-0 text-ink-muted"
          >
            <TabsTrigger
              value="all"
              class="h-11 gap-2 rounded-none border-b-2 border-transparent px-3 text-ink-muted data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-primary data-[state=active]:shadow-none"
            >
              Todos
              <span class="rounded-full bg-surface-sunken px-2 py-px font-mono text-caption font-medium">
                {{ total }}
              </span>
            </TabsTrigger>
            <TabsTrigger
              v-for="s in presentStates"
              :key="s"
              :value="s"
              class="h-11 gap-2 rounded-none border-b-2 border-transparent px-3 text-ink-muted data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-primary data-[state=active]:shadow-none"
            >
              {{ reviewMeta(s).label }}
              <span class="rounded-full bg-surface-sunken px-2 py-px font-mono text-caption font-medium">
                {{ reviewCounts[s] }}
              </span>
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <div class="flex flex-wrap items-center gap-x-3 gap-y-2">
          <Input
            v-model="query"
            placeholder="Buscar por título o #L-0000"
            class="min-w-0 flex-1 basis-60 font-mono"
          />
          <ToggleGroup
            v-model="modalidadFilter"
            type="single"
            class="gap-0.5 rounded-md bg-surface-sunken p-0.5"
          >
            <ToggleGroupItem
              v-for="m in [
                { v: 'all', label: 'Todas' },
                { v: 'tvn', label: 'TVN' },
                { v: 'banca', label: 'Banca' },
              ]"
              :key="m.v"
              :value="m.v"
              class="h-8 rounded-md px-3 text-body-sm font-semibold text-ink-muted hover:bg-transparent data-[state=on]:bg-surface data-[state=on]:text-ink data-[state=on]:shadow-ev-1"
            >
              {{ m.label }}
            </ToggleGroupItem>
          </ToggleGroup>
          <Select v-model="evidenceFilter" :options="evidenceOptions" class="w-56" />
          <Select v-model="sortOrder" :options="sortOptions" class="w-52" />
          <button
            v-if="hasFilters"
            type="button"
            class="h-9 px-2 text-body-sm font-semibold text-ink-muted transition-colors hover:text-ink"
            @click="clearFilters"
          >
            Limpiar filtros
          </button>
        </div>
      </div>

      <!-- Rows -->
      <template v-if="rows.length">
        <div class="overflow-hidden rounded-lg border border-hairline bg-surface shadow-ev-1">
          <!-- Column header -->
          <div
            class="hidden items-center gap-6 bg-surface-sunken px-4 py-2.5 text-label uppercase text-ink-muted md:flex"
          >
            <span class="min-w-0 flex-1 basis-[400px]">Lead</span>
            <span class="flex-[0_0_150px]">Progreso</span>
            <span class="min-w-[180px] flex-[0_1_210px]">Revisor · actividad</span>
            <span class="flex-[0_0_12px]" />
          </div>

          <div
            v-for="l in rows"
            :key="l.raw.id"
            role="link"
            tabindex="0"
            :title="`Abrir #${l.raw.id} · ${l.progress.label}`"
            class="flex cursor-pointer flex-wrap items-center gap-x-6 gap-y-3 border-t border-hairline px-4 py-3.5 pl-[19px] transition-colors first:border-t-0 hover:bg-primary-soft/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
            :style="{ boxShadow: `inset 3px 0 0 ${l.review.barVar}` }"
            @click="openLead(l.raw.id)"
            @keydown.enter="openLead(l.raw.id)"
          >
            <!-- Lead -->
            <div class="flex min-w-0 flex-1 basis-[400px] flex-col gap-2">
              <div class="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
                <span class="shrink-0 rounded-md bg-surface-sunken px-1 font-mono text-mono text-ink-muted">
                  #{{ l.raw.id }}
                </span>
                <span class="min-w-0 flex-1 basis-60 font-serif text-heading-md text-ink">
                  {{ l.raw.titulo }}
                </span>
              </div>
              <div class="flex flex-wrap items-center gap-1.5">
                <span
                  class="rounded-full border border-hairline bg-surface-sunken px-2.5 py-0.5 text-caption font-semibold text-ink"
                >
                  {{ modalidadLabel(l.raw.modalidad) }}
                </span>
                <StateChip :tone="l.review.tone">{{ l.review.label }}</StateChip>
                <StateChip :tone="evidenceTone(l.evidence)" dot>
                  {{ l.evidence.key === "none" ? "Sin fuentes" : `Evidencia ${l.evidence.label}` }}
                </StateChip>
                <span
                  v-for="f in l.raw.flags"
                  :key="f"
                  class="whitespace-nowrap px-0.5 text-[11px] font-semibold uppercase tracking-wide text-accent"
                >
                  {{ f }}
                </span>
              </div>
            </div>

            <!-- Progreso -->
            <div class="flex flex-[0_0_150px] flex-col gap-1.5">
              <div class="flex items-center gap-[3px]">
                <span
                  v-for="n in STEP_TOTAL"
                  :key="n"
                  class="h-1.5 w-5 rounded-full"
                  :style="{
                    background:
                      !l.progress.closed && n <= l.progress.done
                        ? TONE_VAR[l.progress.tone]
                        : 'hsl(var(--surface-sunken))',
                    border: '1px solid hsl(var(--hairline))',
                  }"
                />
              </div>
              <span class="font-mono text-caption" :style="{ color: TONE_VAR[l.progress.tone] }">
                {{ l.progress.label }}
              </span>
            </div>

            <!-- Revisor · actividad -->
            <div class="flex min-w-[180px] flex-[0_1_210px] flex-col gap-1.5">
              <div class="flex min-w-0 items-center gap-2">
                <span
                  class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold"
                  :class="
                    l.reviewer.assigned
                      ? 'bg-primary-soft text-primary'
                      : 'border border-dashed border-hairline text-ink-muted'
                  "
                >
                  {{ l.reviewer.initials }}
                </span>
                <span
                  class="truncate text-body-sm"
                  :class="l.reviewer.assigned ? 'text-ink' : 'text-ink-muted'"
                >
                  {{ l.reviewer.name }}
                </span>
              </div>
              <div class="flex flex-wrap gap-x-3 gap-y-0.5 font-mono text-caption tabular-nums text-ink-muted">
                <span>{{ l.sources }} {{ l.sources === 1 ? "fuente" : "fuentes" }}</span>
                <span title="Hora de Panamá (UTC−5)">{{ l.updated }}</span>
              </div>
            </div>

            <span class="hidden flex-[0_0_12px] text-xl leading-none text-ink-muted md:block">›</span>
          </div>
        </div>
        <span class="font-mono text-caption text-ink-muted">
          {{ rows.length }} de {{ total }} leads · horas en hora de Panamá (UTC−5)
        </span>
      </template>

      <!-- No results under active filters -->
      <div
        v-else
        class="flex flex-col items-center gap-3 rounded-md border border-dashed border-ink-muted/40 px-6 py-8 text-center"
      >
        <span class="font-serif text-heading-md text-ink">Ningún lead coincide</span>
        <span class="max-w-[48ch] text-body-sm text-ink-muted">
          Prueba con otro estado de revisión, modalidad o evidencia.
        </span>
        <Button variant="outline" @click="clearFilters">Limpiar filtros</Button>
      </div>
    </template>
  </div>
</template>
