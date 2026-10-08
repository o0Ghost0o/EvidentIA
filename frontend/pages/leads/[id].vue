<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ContextStep from "~/components/leads/ContextStep.vue";
import DraftStep from "~/components/leads/DraftStep.vue";
import EvidenceStep from "~/components/leads/EvidenceStep.vue";
import FichaStep from "~/components/leads/FichaStep.vue";
import ReviewStep from "~/components/leads/ReviewStep.vue";
import StateChip from "~/components/ui/StateChip.vue";
import { api } from "~/composables/useApi";
import { EVIDENCE_STATES, type EvidenceLevel } from "~/lib/leadEvidence";
import { BAND_LABEL, type ScoreResponse, evidenceLevelFrom } from "~/lib/leadWizard";
import { modalidadLabel, reviewMeta } from "~/lib/leadList";

// Lead detail — the read-only ficha. It renders the finished artifact the New-lead
// workspace produces, in the same design language, by reusing the wizard step
// components in their `readonly` mode. Nothing here mutates the lead; editing lives
// in the wizard.

const route = useRoute();
const id = route.params.id as string;

interface EvidenceItem {
  id: number;
  fuente_tipo: string;
  fuente_id: string;
  rol: string;
  nota: string | null;
  marcado_manual: boolean;
}
interface NoteItem {
  id: number;
  autor: string;
  estado_revision: string;
  texto: string;
  created_at: string;
}
interface CaseDetail {
  id: number;
  titulo: string;
  modalidad: string;
  estado: string;
  queries: string[];
  flags: string[];
  evidence: EvidenceItem[];
  notes: NoteItem[];
}

const detail = ref<CaseDetail | null>(null);
const score = ref<ScoreResponse | null>(null);

onMounted(async () => {
  detail.value = await api<CaseDetail>(`cases/${id}`);
  try {
    score.value = await api<ScoreResponse>(`cases/${id}/score`);
  } catch {
    score.value = null;
  }
});

// --- Derived props for the reused steps ------------------------------------
// All linked evidence is real; the steps fetch their own backend data from the
// case id, so this only feeds the hero summary and the stale-on-change watchers.
const linkedIds = computed(() => (detail.value?.evidence ?? []).map((e) => e.fuente_id));
// Real linked evidence, mapped onto the EvidenceStep view model.
const evidenceItems = computed(() =>
  (detail.value?.evidence ?? []).map((e) => ({
    rowId: e.id,
    fuenteId: e.fuente_id,
    fuenteTipo: e.fuente_tipo,
    rol: e.rol,
    titulo: e.nota || e.fuente_id,
  }))
);
const evidenceLevel = computed<EvidenceLevel>(() =>
  evidenceLevelFrom(score.value?.evidence_state, linkedIds.value.length)
);
const evidenceState = computed(() => EVIDENCE_STATES[evidenceLevel.value]);

// "Alcance: …" and the modalidad live in the case flags the wizard writes.
const alcance = computed(() => {
  const f = (detail.value?.flags ?? []).find((x) => x.toLowerCase().startsWith("alcance:"));
  return f ? f.slice(f.indexOf(":") + 1).trim() : "";
});
const modalidadFlag = computed(() => {
  const f = (detail.value?.flags ?? []).find((x) => !x.toLowerCase().startsWith("alcance:"));
  return f ?? "";
});
const modalidad = computed(() => modalidadFlag.value || modalidadLabel(detail.value?.modalidad ?? ""));
const pregunta = computed(() => detail.value?.queries?.[0] ?? "");

const review = computed(() => reviewMeta(detail.value?.estado ?? "nuevo"));
// With no primary source the workspace treats the lead as an abstention.
const abstained = computed(() => evidenceLevel.value === "insuficiente");

const priorityTotal = computed(() => score.value?.P ?? 0);
const priorityBandKey = computed(() => score.value?.band ?? "bajo");
const priorityBand = computed(() => BAND_LABEL[priorityBandKey.value]);

// Static step copy, mirroring the New-lead workspace rail.
const STEPS = [
  { title: "Definir", desc: "Qué se investiga, con qué alcance y con qué pregunta." },
  { title: "Evidencia", desc: "Fuentes vinculadas, ordenadas según respalden, contradigan o den contexto." },
  { title: "Contexto & Priorización", desc: "Cuánto importa ahora y cuánto respalda la evidencia disponible." },
  { title: "Ficha", desc: "Qué se reporta, quién, qué lo respalda, qué falta y la acción sugerida." },
  { title: "Borrador", desc: "Texto compuesto solo a partir de la evidencia vinculada, con citas verificables." },
  { title: "Revisión", desc: "La decisión editorial registrada y su bitácora de trazabilidad." },
];

function scrollToStep(i: number) {
  document.getElementById(`step-${i + 1}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}
</script>

<template>
  <div v-if="detail">
    <!-- Breadcrumb -->
    <nav class="mb-3 flex items-center gap-1.5 text-caption font-medium text-ink-muted">
      <NuxtLink to="/leads" class="text-ink-muted no-underline hover:text-ink">← Leads</NuxtLink>
      <span>/</span>
      <span class="font-mono">Ficha #{{ detail.id }}</span>
    </nav>

    <!-- Hero -->
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div class="min-w-0 flex-1 basis-[520px]">
        <h1 class="mb-3 text-balance font-serif text-display-xl text-ink">{{ detail.titulo }}</h1>
        <div class="flex min-h-6 flex-wrap items-center gap-2">
          <span
            v-if="modalidad"
            class="rounded-full bg-surface-sunken px-2.5 py-0.5 font-mono text-caption uppercase text-ink-muted"
          >
            {{ modalidad }}
          </span>
          <StateChip :tone="review.tone">{{ review.label }}</StateChip>
          <StateChip :tone="evidenceState.tone" dot>
            {{ linkedIds.length ? `Evidencia ${evidenceState.label}` : "Sin fuentes" }}
          </StateChip>
          <span
            class="rounded-full px-2.5 py-0.5 text-caption font-semibold"
            :class="
              priorityBandKey === 'alto'
                ? 'bg-destructive/10 text-destructive'
                : priorityBandKey === 'medio'
                  ? 'bg-warning/10 text-warning'
                  : 'bg-surface-sunken text-ink-muted'
            "
          >
            Prioridad {{ priorityBand }} · P {{ priorityTotal }}
          </span>
        </div>
      </div>
      <div class="font-mono text-caption text-ink-muted">Ficha completa · 6/6 pasos</div>
    </div>

    <div class="flex flex-wrap items-start gap-6">
      <!-- Aside: summary + step rail -->
      <aside class="sticky top-4 flex basis-[280px] flex-col gap-4" style="flex: 0 1 280px; min-width: 260px">
        <div class="flex flex-col gap-3 rounded-md border border-border bg-surface p-4 shadow-ev-1">
          <div class="text-label uppercase text-ink-muted">Resumen del lead</div>
          <div class="grid grid-cols-[auto_1fr] gap-x-3 gap-y-2 text-body-sm">
            <span class="text-ink-muted">Modalidad</span><span>{{ modalidad || "—" }}</span>
            <span class="text-ink-muted">Alcance</span><span>{{ alcance || "—" }}</span>
            <span class="text-ink-muted">Fuentes</span>
            <span class="font-mono">{{ linkedIds.length ? `${linkedIds.length} · ${evidenceState.label}` : "—" }}</span>
            <span class="text-ink-muted">Prioridad</span>
            <span class="font-mono">{{ priorityTotal }} · {{ priorityBand }}</span>
          </div>
        </div>

        <nav class="flex flex-col gap-0.5 rounded-lg bg-surface-sunken p-2">
          <button
            v-for="(s, i) in STEPS"
            :key="s.title"
            type="button"
            class="flex min-h-11 items-start gap-3 rounded-md border-l-[3px] border-success bg-surface px-3 py-2.5 text-left transition-colors hover:bg-primary-soft/40"
            @click="scrollToStep(i)"
          >
            <span
              class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-[1.5px] border-success bg-success font-mono text-caption text-white"
            >
              ✓
            </span>
            <div class="flex min-w-0 flex-col gap-0.5">
              <span class="text-body-sm font-semibold leading-tight text-ink">{{ s.title }}</span>
            </div>
          </button>
        </nav>
      </aside>

      <!-- Main column: the reused steps, read-only -->
      <section class="flex min-w-0 flex-1 basis-[560px] flex-col gap-6">
        <!-- Step 1 · Definir (no wizard component — saved fields) -->
        <div id="step-1" class="flex flex-col gap-6 rounded-md border border-border bg-surface p-6 shadow-ev-1 scroll-mt-4">
          <div class="flex flex-col gap-1.5 border-b border-border pb-4">
            <span class="text-label uppercase text-ink-muted">Paso 1 de 6</span>
            <h2 class="font-serif text-display-lg">{{ STEPS[0].title }}</h2>
            <p class="max-w-[60ch] text-balance text-body-sm text-ink-muted">{{ STEPS[0].desc }}</p>
          </div>
          <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-3 text-body-sm">
            <dt class="text-ink-muted">Título</dt>
            <dd class="text-ink">{{ detail.titulo }}</dd>
            <dt class="text-ink-muted">Modalidad</dt>
            <dd>{{ modalidad || "—" }}</dd>
            <dt class="text-ink-muted">Alcance</dt>
            <dd>{{ alcance || "—" }}</dd>
            <dt class="text-ink-muted">Pregunta</dt>
            <dd class="text-pretty leading-relaxed">{{ pregunta || "—" }}</dd>
          </dl>
        </div>

        <!-- Steps 2–6 · reused wizard components in read-only mode -->
        <div
          v-for="(s, i) in STEPS.slice(1)"
          :key="s.title"
          :id="`step-${i + 2}`"
          class="flex flex-col gap-6 rounded-md border border-border bg-surface p-6 shadow-ev-1 scroll-mt-4"
        >
          <div class="flex flex-col gap-1.5 border-b border-border pb-4">
            <span class="text-label uppercase text-ink-muted">Paso {{ i + 2 }} de 6</span>
            <h2 class="font-serif text-display-lg">{{ s.title }}</h2>
            <p class="max-w-[60ch] text-balance text-body-sm text-ink-muted">{{ s.desc }}</p>
          </div>

          <EvidenceStep
            v-if="i === 0"
            readonly
            :lead-id="detail.id"
            :modalidad="detail.modalidad"
            :initial-items="evidenceItems"
          />
          <ContextStep v-else-if="i === 1" readonly :lead-id="detail.id" :evidence-level="evidenceLevel" />
          <FichaStep v-else-if="i === 2" readonly :lead-id="detail.id" :linked-ids="linkedIds" :alcance="alcance" />
          <DraftStep v-else-if="i === 3" readonly :lead-id="detail.id" :linked-ids="linkedIds" :title="detail.titulo" />
          <ReviewStep
            v-else-if="i === 4"
            readonly
            :lead-id="detail.id"
            :abstained="abstained"
            :linked-ids="linkedIds"
            :title="detail.titulo"
            :decision="detail.estado"
            :audit-notes="detail.notes"
          />
        </div>
      </section>
    </div>
  </div>

  <div v-else class="py-12 text-center text-body-sm text-ink-muted">Cargando ficha del lead…</div>
</template>
