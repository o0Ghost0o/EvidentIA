<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import ContextStep from "~/components/leads/ContextStep.vue";
import DraftStep from "~/components/leads/DraftStep.vue";
import EvidenceStep from "~/components/leads/EvidenceStep.vue";
import FichaStep from "~/components/leads/FichaStep.vue";
import ReviewStep from "~/components/leads/ReviewStep.vue";
import Button from "~/components/ui/Button.vue";
import Input from "~/components/ui/Input.vue";
import Label from "~/components/ui/Label.vue";
import Select from "~/components/ui/Select.vue";
import Textarea from "~/components/ui/Textarea.vue";
import { api } from "~/composables/useApi";
import { EVIDENCE_STATES, type EvidenceLevel } from "~/lib/leadEvidence";
import { deriveProgress } from "~/lib/leadList";
import {
  BAND_LABEL,
  evidenceLevelFrom,
  mergeStep1Flags,
  type LinkedItem,
  type ScoreResponse,
  type WizardSeed,
} from "~/lib/leadWizard";
import type { BriefPackage } from "~/components/leads/DraftStep.vue";

// Lead Workspace wizard, shared by the New-lead page (`mode: "create"`) and the
// Edit-lead page (`mode: "edit"`). In create mode step 1 "Definir" POSTs a new
// case; in edit mode the wizard is seeded from an existing lead and step 1
// PATCHes it. Every later step self-persists via its own backend calls, exactly
// as before — this component only orchestrates the flow.

const props = withDefaults(
  defineProps<{
    mode?: "create" | "edit";
    /** Edit mode: the existing case id. */
    leadId?: number | null;
    /** Edit mode: the lead's data, pre-mapped onto the wizard shape. */
    seed?: WizardSeed | null;
  }>(),
  { mode: "create", leadId: null, seed: null },
);

const isEdit = computed(() => props.mode === "edit");

// "Tipo" is an editorial flag on the lead; it is descriptive and does not change
// how the backend scores or drafts.
const MODALIDAD_OPTIONS = [
  { value: "Investigación", label: "Investigación" },
  { value: "Verificación", label: "Verificación" },
  { value: "Seguimiento", label: "Seguimiento" },
];

// "Modalidad" is the backend lens (tvn | banca): it drives the ranking catalog,
// the priority scoring and the brief generation, so it is stored on the case.
const LENS_OPTIONS = [
  { value: "tvn", label: "TVN (editorial)" },
  { value: "banca", label: "Banca (económico)" },
];

// Mirrors the design's "Usar ejemplo" seed so the flow can be walked quickly.
const EXAMPLE = {
  title: "Alza en tarifas eléctricas residenciales en Colón tras la revisión de septiembre",
  mod: "Investigación",
  modalidad: "tvn",
  alc: "Provincia de Colón",
  q: "¿Cuánto aumentó la factura residencial promedio y qué parte del alza se explica por la resolución tarifaria frente a lecturas estimadas?",
};

const STEPS = [
  { title: "Definir", guide: "Empieza por el título y la modalidad: son lo mínimo para que el lead exista. Usa «Usar ejemplo» si quieres recorrer el flujo rápido.", desc: "Qué se investiga, con qué alcance y con qué pregunta.", lockReason: "" },
  { title: "Evidencia", guide: "Prueba «Vincular ejemplo»: tres réplicas del mismo cable cuentan como 1 fuente. Toca una tarjeta para ver su cadena de evidencia.", desc: "Vincula fuentes del catálogo: cada una se ordena según respalde, contradiga o dé contexto a la afirmación.", lockReason: "Crea el lead primero" },
  { title: "Contexto & Priorización", guide: "La prioridad se calcula con reglas versionadas, no a criterio del modelo. Cada componente es explicable.", desc: "Cuánto importa ahora y cuánto respalda la evidencia disponible.", lockReason: "Vincula ≥1 fuente" },
  { title: "Ficha", guide: "La ficha se compone solo con lo vinculado. «Qué falta» es tan importante como lo que hay.", desc: "Qué se reporta, quién, qué lo respalda, qué falta y la acción sugerida.", lockReason: "Calcula la prioridad" },
  { title: "Borrador", guide: "Si la evidencia es insuficiente, este paso se bloquea: puedes volver a vincular fuentes o registrar una abstención.", desc: "Texto generado únicamente a partir de evidencia vinculada, con citas verificables.", lockReason: "Confirma la ficha" },
  { title: "Revisión", guide: "", desc: "", lockReason: "Requiere borrador o abstención" },
];

const seed = props.seed;
const form = reactive({
  title: seed?.title ?? "",
  mod: seed?.mod ?? "",
  modalidad: seed?.modalidad ?? "tvn",
  alc: seed?.alcance ?? "",
  q: seed?.pregunta ?? "",
});
const tried = ref(false);
const submitting = ref(false);
const submitError = ref("");

// Wizard state. step is 1-based; caseId is set once the case exists (created in
// create mode, seeded in edit mode).
const step = ref(1);
const caseId = ref<number | null>(isEdit.value ? (props.leadId ?? seed?.leadId ?? null) : null);

// Evidence summary, seeded in edit mode from the lead's linked sources.
const seedEvidenceKey: EvidenceLevel = seed
  ? evidenceLevelFrom(seed.score?.evidence_state, seed.evidenceItems.length)
  : "none";
const evidence = reactive({
  count: seed?.evidenceItems.length ?? 0,
  label: EVIDENCE_STATES[seedEvidenceKey].label,
  tone: EVIDENCE_STATES[seedEvidenceKey].tone as string,
  key: seedEvidenceKey,
});
// Full linked set lives here so each step re-seeds from the parent after a
// back-then-forward; linkedIds is the id-only view the later steps consume.
const evidenceItems = ref<LinkedItem[]>(seed?.evidenceItems ?? []);
const linkedIds = computed(() => evidenceItems.value.map((i) => i.fuenteId));
const priority = reactive({
  scored: !!seed?.score,
  total: seed?.score?.P ?? 0,
  band: seed?.score?.band ?? "",
  bandLabel: seed?.score ? (BAND_LABEL[seed.score.band] ?? seed.score.band) : "",
});
const priorityScore = ref<ScoreResponse | null>(seed?.score ?? null);
const ficha = reactive({ confirmed: false });
const draftState = reactive({ generated: false, abstained: false });
const draftPkg = ref<BriefPackage | null>(null);
const reviewState = reactive({ saved: false, label: "", estado: seed?.estado ?? "" });
const reviewDraft = reactive({ review: seed?.estado ?? "", note: "" });

// Data-driven step completion, shared with the read-only ficha: the furthest step
// a lead's real data supports (deriveProgress over estado + linked evidence). In
// edit mode this lets completed steps be revisited directly; create grows it as
// the wizard advances.
const currentEstado = computed(() => reviewState.estado || seed?.estado || "nuevo");
const doneCount = computed(() =>
  caseId.value == null ? 0 : deriveProgress(currentEstado.value, evidenceItems.value.length).done,
);
// Furthest step visited this session, so forward progress stays reachable too.
const visitedMax = ref(1);
watch(step, (v) => {
  if (v > visitedMax.value) visitedMax.value = v;
});

// A step is reachable (clickable) in edit mode when it is already complete, the
// next step to fill, or one already visited this session.
function canJump(n: number): boolean {
  return isEdit.value && caseId.value != null && (n <= doneCount.value + 1 || n <= visitedMax.value);
}
function goStep(i: number) {
  const n = i + 1;
  if (n !== step.value && canJump(n)) {
    step.value = n;
    window.scrollTo({ top: 0 });
  }
}

const BAND_CHIP: Record<string, string> = {
  alto: "bg-destructive/10 text-destructive",
  medio: "bg-warning/10 text-warning",
  bajo: "bg-surface-sunken text-ink-muted",
};

const titleTrimmed = computed(() => form.title.trim());
const titleOk = computed(() => titleTrimmed.value.length >= 10);
const modOk = computed(() => !!form.mod);

const titleInvalid = computed(() => tried.value && !titleOk.value);
const modInvalid = computed(() => tried.value && !modOk.value);

const titleHelp = computed(() => {
  if (titleInvalid.value) {
    return titleTrimmed.value ? "Mínimo 10 caracteres" : "El título es obligatorio";
  }
  return `${form.title.length} caracteres · mínimo 10`;
});

// Progress & rail.
const sessionDone = computed(() => (reviewState.saved ? 6 : step.value - 1));
// In edit, reflect the lead's real completion too, so the counter matches the ficha.
const stepsDone = computed(() =>
  isEdit.value ? Math.max(sessionDone.value, doneCount.value) : sessionDone.value,
);
const progressPct = computed(() => `${(stepsDone.value / 6) * 100}%`);
const cur = computed(() => STEPS[step.value - 1]);

// Copy that differs between creating and editing.
const breadcrumbTail = computed(() => (isEdit.value ? "Editar ficha" : step.value > 1 ? "Ficha" : "Nuevo lead"));
const heroTitle = computed(() => titleTrimmed.value || (isEdit.value ? "Editar ficha" : "Nuevo lead"));
const step1Cta = computed(() => {
  if (submitting.value) return isEdit.value ? "Guardando…" : "Creando…";
  return isEdit.value ? "Guardar y continuar" : "Crear lead";
});

function railSub(i: number): string {
  // Locked steps show why; done and active steps show their positive status.
  if (railState(i) === "locked") return STEPS[i].lockReason;
  if (i === 0) return form.mod || "Título y modalidad";
  if (i === 1) return evidence.count ? `${evidence.count} ${evidence.count === 1 ? "fuente" : "fuentes"} · ${evidence.label}` : "Sin fuentes";
  if (i === 2) return priority.scored ? `P ${priority.total} · ${priority.bandLabel}` : "Por calcular";
  if (i === 3) return ficha.confirmed ? "Confirmada" : "Por confirmar";
  if (i === 4) {
    if (draftState.abstained) return "Abstención registrada";
    if (draftState.generated) return "Borrador listo";
    return evidence.key === "insuficiente" ? "Evidencia insuficiente" : "Listo para generar";
  }
  if (i === 5) return reviewState.saved ? reviewState.label : "Pendiente de decisión";
  return STEPS[i].desc;
}
function railState(i: number): "done" | "active" | "todo" | "locked" {
  const n = i + 1;
  if (isEdit.value) {
    // Data-driven: completed steps are "done", the current is "active", a reachable
    // step is "todo" (clickable), the rest stay locked.
    if (n === step.value) return "active";
    if (n <= doneCount.value) return "done";
    if (canJump(n)) return "todo";
    return "locked";
  }
  if (i < step.value - 1) return "done";
  if (i === step.value - 1) return "active";
  return "locked";
}

// Rail rows with their state and whether they can be jumped to (edit only).
const railItems = computed(() =>
  STEPS.map((s, i) => {
    const state = railState(i);
    return { ...s, i, state, check: state === "done", clickable: state !== "active" && canJump(i + 1) };
  }),
);

function fillExample() {
  Object.assign(form, EXAMPLE);
}

// Step 1 "Definir": create POSTs a new case; edit PATCHes the existing one,
// preserving the scoring/source metadata flags.
async function submitStep1() {
  tried.value = true;
  submitError.value = "";
  if (!titleOk.value || !modOk.value) return;

  submitting.value = true;
  try {
    if (isEdit.value && caseId.value != null) {
      const flags = mergeStep1Flags(seed?.flags ?? [], form.mod, form.alc);
      await api(`cases/${caseId.value}`, {
        method: "PATCH",
        body: {
          titulo: titleTrimmed.value,
          modalidad: form.modalidad,
          queries: form.q.trim() ? [form.q.trim()] : [],
          flags,
        },
      });
    } else {
      const flags = [form.mod, form.alc.trim() ? `Alcance: ${form.alc.trim()}` : ""].filter(Boolean);
      const res = await api<{ id: number }>("cases", {
        method: "POST",
        body: {
          titulo: titleTrimmed.value,
          modalidad: form.modalidad,
          queries: form.q.trim() ? [form.q.trim()] : [],
          flags,
        },
      });
      caseId.value = res.id;
    }
    step.value = 2;
    window.scrollTo({ top: 0 });
  } catch (err: any) {
    submitError.value =
      err?.data?.detail || err?.message ||
      (isEdit.value ? "No se pudo guardar el lead. Inténtalo de nuevo." : "No se pudo crear el lead. Inténtalo de nuevo.");
  } finally {
    submitting.value = false;
  }
}

function onEvidenceChange(p: { count: number; label: string; tone: string; key: EvidenceLevel; linkedIds: string[]; items: LinkedItem[] }) {
  evidence.count = p.count;
  evidence.label = p.label;
  evidence.tone = p.tone;
  evidence.key = p.key;
  evidenceItems.value = p.items;
}

// Step 2 → step 3, in place. The wizard keeps advancing inside the page.
function continueToContext() {
  step.value = 3;
  window.scrollTo({ top: 0 });
}

function onPriorityChange(p: { total: number; band: string; bandLabel: string; score: ScoreResponse | null }) {
  priority.scored = true;
  priority.total = p.total;
  priority.band = p.band;
  priority.bandLabel = p.bandLabel;
  priorityScore.value = p.score;
}

// Step 3 → step 4 "Ficha", in place.
function continueToFicha() {
  step.value = 4;
  window.scrollTo({ top: 0 });
}

function onFichaChange(p: { confirmed: boolean }) {
  ficha.confirmed = p.confirmed;
}

// Step 4 → step 5 "Borrador", in place.
function continueToDraft() {
  step.value = 5;
  window.scrollTo({ top: 0 });
}

function onDraftChange(p: { draft: boolean; abstained: boolean; pkg: BriefPackage | null }) {
  draftState.generated = p.draft;
  draftState.abstained = p.abstained;
  draftPkg.value = p.pkg;
}

// Step 5 → step 6 "Revisión", in place.
function continueToReview() {
  step.value = 6;
  window.scrollTo({ top: 0 });
}

function onReviewChange(p: { saved: boolean; estado: string; label: string }) {
  reviewState.saved = p.saved;
  reviewState.label = p.label;
  reviewState.estado = p.estado;
}

function onReviewDraft(p: { review: string; note: string }) {
  reviewDraft.review = p.review;
  reviewDraft.note = p.note;
}

// Finish: create resets to a blank step 1; edit returns to the lead's ficha.
function onFinish() {
  if (isEdit.value && caseId.value != null) {
    navigateTo(`/leads/${caseId.value}`);
    return;
  }
  Object.assign(form, { title: "", mod: "", modalidad: "tvn", alc: "", q: "" });
  tried.value = false;
  submitError.value = "";
  caseId.value = null;
  Object.assign(evidence, { count: 0, label: "sin fuentes", tone: "neutral", key: "none" as EvidenceLevel });
  evidenceItems.value = [];
  Object.assign(priority, { scored: false, total: 0, band: "", bandLabel: "" });
  priorityScore.value = null;
  ficha.confirmed = false;
  Object.assign(draftState, { generated: false, abstained: false });
  draftPkg.value = null;
  Object.assign(reviewState, { saved: false, label: "", estado: "" });
  Object.assign(reviewDraft, { review: "", note: "" });
  step.value = 1;
  window.scrollTo({ top: 0 });
}
</script>

<template>
  <div>
    <!-- Breadcrumb -->
    <nav class="mb-3 flex items-center gap-1.5 text-caption font-medium text-ink-muted">
      <NuxtLink to="/leads" class="text-ink-muted no-underline hover:text-ink">← Leads</NuxtLink>
      <span>/</span>
      <span>{{ breadcrumbTail }}</span>
    </nav>

    <!-- Hero -->
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div class="min-w-0 flex-1 basis-[520px]">
        <h1
          class="mb-3 text-balance font-serif text-display-xl"
          :class="titleTrimmed ? 'text-ink' : 'text-ink-muted'"
        >
          {{ heroTitle }}
        </h1>
        <!-- Chips appear as the lead progresses -->
        <div class="flex min-h-6 flex-wrap items-center gap-2">
          <template v-if="step > 1">
            <span class="rounded-full bg-surface-sunken px-2.5 py-0.5 font-mono text-caption uppercase text-ink-muted">
              {{ form.mod }}
            </span>
            <span class="rounded-full bg-surface-sunken px-2.5 py-0.5 text-caption font-medium text-ink-muted">
              Evidencia {{ evidence.label }}
            </span>
            <span
              v-if="priority.scored"
              class="rounded-full px-2.5 py-0.5 text-caption font-semibold"
              :class="BAND_CHIP[priority.band]"
            >
              Prioridad {{ priority.bandLabel }} · P {{ priority.total }}
            </span>
          </template>
        </div>
      </div>
      <div class="font-mono text-caption text-ink-muted">{{ stepsDone }}/6 pasos completos</div>
    </div>

    <div class="flex flex-wrap items-start gap-6">
      <!-- Aside: summary + step rail -->
      <aside class="sticky top-4 flex basis-[280px] flex-col gap-4" style="flex: 0 1 280px; min-width: 260px">
        <div class="flex flex-col gap-3 rounded-md border border-border bg-surface p-4 shadow-ev-1">
          <div class="text-label uppercase text-ink-muted">Resumen del lead</div>
          <div class="grid grid-cols-[auto_1fr] gap-x-3 gap-y-2 text-body-sm">
            <span class="text-ink-muted">Modalidad</span><span>{{ form.mod || "—" }}</span>
            <span class="text-ink-muted">Alcance</span><span>{{ form.alc.trim() || "—" }}</span>
            <span class="text-ink-muted">Fuentes</span>
            <span class="font-mono">{{ evidence.count ? `${evidence.count} · ${evidence.label}` : "—" }}</span>
            <span class="text-ink-muted">Prioridad</span>
            <span class="font-mono">{{ priority.scored ? `${priority.total} · ${priority.bandLabel}` : "—" }}</span>
          </div>
          <div class="h-1 overflow-hidden rounded-full bg-surface-sunken">
            <div class="h-full bg-success transition-[width] duration-500" :style="{ width: progressPct }" />
          </div>
        </div>

        <nav class="flex flex-col gap-0.5 rounded-lg bg-surface-sunken p-2">
          <component
            :is="r.clickable ? 'button' : 'div'"
            v-for="r in railItems"
            :key="r.title"
            :type="r.clickable ? 'button' : undefined"
            class="flex min-h-11 items-start gap-3 rounded-md border-l-[3px] px-3 py-2.5 text-left transition-colors"
            :class="[
              r.state === 'active'
                ? 'border-primary bg-surface'
                : r.state === 'done'
                  ? 'border-success bg-surface'
                  : r.state === 'todo'
                    ? 'border-hairline bg-surface'
                    : 'cursor-not-allowed border-transparent opacity-50',
              r.clickable ? 'cursor-pointer hover:bg-primary-soft/40' : '',
            ]"
            @click="r.clickable && goStep(r.i)"
          >
            <div
              class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-[1.5px] font-mono text-caption"
              :class="
                r.state === 'active'
                  ? 'border-primary bg-primary text-on-primary'
                  : r.state === 'done'
                    ? 'border-success bg-success text-white'
                    : 'border-dashed border-ink-muted text-ink-muted'
              "
            >
              <span v-if="r.check">✓</span>
              <span v-else>{{ r.i + 1 }}</span>
            </div>
            <div class="flex min-w-0 flex-col gap-0.5">
              <span
                class="font-semibold leading-tight"
                :class="r.state === 'active' ? 'font-serif text-heading-md text-ink' : 'text-body-sm text-ink-muted'"
              >
                {{ r.title }}
              </span>
              <span class="text-caption font-medium leading-snug text-ink-muted">
                {{ railSub(r.i) }}
              </span>
            </div>
          </component>
        </nav>
      </aside>

      <!-- Main card -->
      <section class="flex min-w-0 flex-1 basis-[560px] flex-col gap-6">
        <div class="flex flex-col gap-6 rounded-md border border-border bg-surface p-6 shadow-ev-1">
          <div class="flex flex-col gap-1.5 border-b border-border pb-4">
            <span class="text-label uppercase text-ink-muted">Paso {{ step }} de 6</span>
            <h2 class="font-serif text-display-lg">{{ cur.title }}</h2>
            <p class="max-w-[60ch] text-balance text-body-sm text-ink-muted">{{ cur.desc }}</p>
          </div>

          <!-- Guía -->
          <div class="flex items-start gap-3 rounded-md bg-primary-soft px-4 py-3">
            <span class="whitespace-nowrap pt-0.5 text-label uppercase text-primary">Guía</span>
            <p class="text-balance text-body-sm text-ink">{{ cur.guide }}</p>
          </div>

          <!-- Step 1 · Definir -->
          <form v-if="step === 1" class="flex flex-col gap-4" novalidate @submit.prevent="submitStep1">
            <div v-if="!isEdit" class="flex justify-end">
              <Button type="button" variant="outline" @click="fillExample">Usar ejemplo</Button>
            </div>

            <div class="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4">
              <div class="col-span-full flex flex-col gap-1.5">
                <Label for="lead-title" class="normal-case">Título *</Label>
                <Input
                  id="lead-title"
                  v-model="form.title"
                  placeholder="Qué se investiga, en una frase"
                  :class="titleInvalid ? 'border-destructive' : ''"
                />
                <span class="text-caption font-medium" :class="titleInvalid ? 'text-destructive' : 'text-ink-muted'">
                  {{ titleHelp }}
                </span>
              </div>

              <div class="flex flex-col gap-1.5">
                <Label class="normal-case">Tipo *</Label>
                <Select
                  v-model="form.mod"
                  :options="MODALIDAD_OPTIONS"
                  placeholder="Selecciona…"
                  :invalid="modInvalid"
                />
                <span class="text-caption font-medium text-destructive">
                  {{ modInvalid ? "Elige un tipo" : "" }}
                </span>
              </div>

              <div class="flex flex-col gap-1.5">
                <Label class="normal-case">Modalidad *</Label>
                <Select
                  v-model="form.modalidad"
                  :options="LENS_OPTIONS"
                  placeholder="Selecciona…"
                />
                <span class="text-caption font-medium text-ink-muted">
                  Lente de priorización y borrador
                </span>
              </div>

              <div class="flex flex-col gap-1.5">
                <Label for="lead-alcance" class="normal-case">Alcance</Label>
                <Input id="lead-alcance" v-model="form.alc" placeholder="Región o ámbito" />
              </div>

              <div class="col-span-full flex flex-col gap-1.5">
                <Label for="lead-q" class="normal-case">Pregunta de investigación</Label>
                <Textarea
                  id="lead-q"
                  v-model="form.q"
                  :rows="3"
                  placeholder="¿Qué debe poder responder este lead?"
                  class="resize-y"
                />
              </div>
            </div>

            <p v-if="submitError" class="text-body-sm text-destructive">{{ submitError }}</p>

            <div class="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
              <button
                type="button"
                class="invisible h-11 px-3 font-semibold text-ink-muted"
                aria-hidden="true"
                tabindex="-1"
              >
                ← Atrás
              </button>
              <Button type="submit" :disabled="submitting">
                {{ step1Cta }}
              </Button>
            </div>
          </form>

          <!-- Step 2 · Evidencia -->
          <EvidenceStep
            v-else-if="step === 2 && caseId != null"
            :lead-id="caseId"
            :modalidad="form.modalidad"
            :initial-items="evidenceItems"
            @back="step = 1"
            @continue="continueToContext"
            @change="onEvidenceChange"
          />

          <!-- Step 3 · Contexto & Priorización -->
          <ContextStep
            v-else-if="step === 3 && caseId != null"
            :lead-id="caseId"
            :evidence-level="evidence.key"
            :initial-scored="priority.scored"
            :initial-score="priorityScore"
            @back="step = 2"
            @continue="continueToFicha"
            @change="onPriorityChange"
          />

          <!-- Step 4 · Ficha -->
          <FichaStep
            v-else-if="step === 4 && caseId != null"
            :lead-id="caseId"
            :linked-ids="linkedIds"
            :alcance="form.alc"
            @back="step = 3"
            @continue="continueToDraft"
            @change="onFichaChange"
          />

          <!-- Step 5 · Borrador -->
          <DraftStep
            v-else-if="step === 5 && caseId != null"
            :lead-id="caseId"
            :linked-ids="linkedIds"
            :title="form.title"
            :initial-pkg="draftPkg"
            @back="step = 4"
            @go-evidence="step = 2"
            @continue="continueToReview"
            @change="onDraftChange"
          />

          <!-- Step 6 · Revisión -->
          <ReviewStep
            v-else-if="step === 6 && caseId != null"
            :lead-id="caseId"
            :abstained="draftState.abstained"
            :linked-ids="linkedIds"
            :title="form.title"
            :initial-review="reviewDraft.review"
            :initial-note="reviewDraft.note"
            :restart-label="isEdit ? 'Volver a la ficha' : 'Crear otro lead'"
            @back="step = 5"
            @restart="onFinish"
            @change="onReviewChange"
            @draft="onReviewDraft"
          />
        </div>
      </section>
    </div>
  </div>
</template>
