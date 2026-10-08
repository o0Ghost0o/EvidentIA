<script setup lang="ts">
import { computed, reactive, ref } from "vue";
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
import type { EvidenceLevel } from "~/lib/leadEvidence";

// New lead — the Lead Workspace wizard. Step 1 "Definir" captures the minimum that
// makes a lead exist (título + modalidad); once created, the flow advances in place
// to step 2 "Evidencia" where sources are linked. The backend case model
// (titulo / queries[] / flags[]) is the persistence target.

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

const form = reactive({ title: "", mod: "", modalidad: "tvn", alc: "", q: "" });
const tried = ref(false);
const submitting = ref(false);
const submitError = ref("");

// Wizard state. step is 1-based; leadId is set once the case is created.
const step = ref(1);
const leadId = ref<number | null>(null);
const evidence = reactive({ count: 0, label: "sin fuentes", tone: "neutral", key: "none" as EvidenceLevel });
const linkedIds = ref<string[]>([]);
const priority = reactive({ scored: false, total: 0, band: "", bandLabel: "" });
const ficha = reactive({ confirmed: false });
const draftState = reactive({ generated: false, abstained: false });
const reviewState = reactive({ saved: false, label: "" });

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
const stepsDone = computed(() => (reviewState.saved ? 6 : step.value - 1));
const progressPct = computed(() => `${(stepsDone.value / 6) * 100}%`);
const cur = computed(() => STEPS[step.value - 1]);

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
function railState(i: number): "done" | "active" | "locked" {
  if (i < step.value - 1) return "done";
  if (i === step.value - 1) return "active";
  return "locked";
}

function fillExample() {
  Object.assign(form, EXAMPLE);
}

async function createLead() {
  tried.value = true;
  submitError.value = "";
  if (!titleOk.value || !modOk.value) return;

  const flags = [form.mod, form.alc.trim() ? `Alcance: ${form.alc.trim()}` : ""].filter(Boolean);
  submitting.value = true;
  try {
    const res = await api<{ id: number }>("cases", {
      method: "POST",
      body: {
        titulo: titleTrimmed.value,
        modalidad: form.modalidad,
        queries: form.q.trim() ? [form.q.trim()] : [],
        flags,
      },
    });
    leadId.value = res.id;
    step.value = 2;
    window.scrollTo({ top: 0 });
  } catch (err: any) {
    submitError.value =
      err?.data?.detail || err?.message || "No se pudo crear el lead. Inténtalo de nuevo.";
  } finally {
    submitting.value = false;
  }
}

function onEvidenceChange(p: { count: number; label: string; tone: string; key: EvidenceLevel; linkedIds: string[] }) {
  evidence.count = p.count;
  evidence.label = p.label;
  evidence.tone = p.tone;
  evidence.key = p.key;
  linkedIds.value = p.linkedIds;
}

// Step 2 → step 3, in place. The wizard keeps advancing inside the page.
function continueToContext() {
  step.value = 3;
  window.scrollTo({ top: 0 });
}

function onPriorityChange(p: { total: number; band: string; bandLabel: string }) {
  priority.scored = true;
  priority.total = p.total;
  priority.band = p.band;
  priority.bandLabel = p.bandLabel;
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

function onDraftChange(p: { draft: boolean; abstained: boolean }) {
  draftState.generated = p.draft;
  draftState.abstained = p.abstained;
}

// Step 5 → step 6 "Revisión", in place.
function continueToReview() {
  step.value = 6;
  window.scrollTo({ top: 0 });
}

function onReviewChange(p: { saved: boolean; estado: string; label: string }) {
  reviewState.saved = p.saved;
  reviewState.label = p.label;
}

// "Crear otro lead" — reset the wizard to a blank step 1.
function restartWizard() {
  Object.assign(form, { title: "", mod: "", modalidad: "tvn", alc: "", q: "" });
  tried.value = false;
  submitError.value = "";
  leadId.value = null;
  Object.assign(evidence, { count: 0, label: "sin fuentes", tone: "neutral", key: "none" as EvidenceLevel });
  linkedIds.value = [];
  Object.assign(priority, { scored: false, total: 0, band: "", bandLabel: "" });
  ficha.confirmed = false;
  Object.assign(draftState, { generated: false, abstained: false });
  Object.assign(reviewState, { saved: false, label: "" });
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
      <span>{{ step > 1 ? "Ficha" : "Nuevo lead" }}</span>
    </nav>

    <!-- Hero -->
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div class="min-w-0 flex-1 basis-[520px]">
        <h1
          class="mb-3 text-balance font-serif text-display-xl"
          :class="titleTrimmed ? 'text-ink' : 'text-ink-muted'"
        >
          {{ titleTrimmed || "Nuevo lead" }}
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
          <div
            v-for="(s, i) in STEPS"
            :key="s.title"
            class="flex min-h-11 items-start gap-3 rounded-md border-l-[3px] px-3 py-2.5 transition-colors"
            :class="
              railState(i) === 'active'
                ? 'border-primary bg-surface'
                : railState(i) === 'done'
                  ? 'border-success bg-surface'
                  : 'cursor-not-allowed border-transparent opacity-50'
            "
          >
            <div
              class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-[1.5px] font-mono text-caption"
              :class="
                railState(i) === 'active'
                  ? 'border-primary bg-primary text-on-primary'
                  : railState(i) === 'done'
                    ? 'border-success bg-success text-white'
                    : 'border-dashed border-ink-muted text-ink-muted'
              "
            >
              <span v-if="railState(i) === 'done'">✓</span>
              <span v-else>{{ i + 1 }}</span>
            </div>
            <div class="flex min-w-0 flex-col gap-0.5">
              <span
                class="font-semibold leading-tight"
                :class="railState(i) === 'active' ? 'font-serif text-heading-md text-ink' : 'text-body-sm text-ink-muted'"
              >
                {{ s.title }}
              </span>
              <span class="text-caption font-medium leading-snug text-ink-muted">
                {{ railSub(i) }}
              </span>
            </div>
          </div>
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
          <form v-if="step === 1" class="flex flex-col gap-4" novalidate @submit.prevent="createLead">
            <div class="flex justify-end">
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
                {{ submitting ? "Creando…" : "Crear lead" }}
              </Button>
            </div>
          </form>

          <!-- Step 2 · Evidencia -->
          <EvidenceStep
            v-else-if="step === 2 && leadId != null"
            :lead-id="leadId"
            :modalidad="form.modalidad"
            @back="step = 1"
            @continue="continueToContext"
            @change="onEvidenceChange"
          />

          <!-- Step 3 · Contexto & Priorización -->
          <ContextStep
            v-else-if="step === 3 && leadId != null"
            :lead-id="leadId"
            :evidence-level="evidence.key"
            @back="step = 2"
            @continue="continueToFicha"
            @change="onPriorityChange"
          />

          <!-- Step 4 · Ficha -->
          <FichaStep
            v-else-if="step === 4 && leadId != null"
            :lead-id="leadId"
            :linked-ids="linkedIds"
            :alcance="form.alc"
            @back="step = 3"
            @continue="continueToDraft"
            @change="onFichaChange"
          />

          <!-- Step 5 · Borrador -->
          <DraftStep
            v-else-if="step === 5 && leadId != null"
            :lead-id="leadId"
            :linked-ids="linkedIds"
            :title="form.title"
            @back="step = 4"
            @go-evidence="step = 2"
            @continue="continueToReview"
            @change="onDraftChange"
          />

          <!-- Step 6 · Revisión -->
          <ReviewStep
            v-else-if="step === 6 && leadId != null"
            :lead-id="leadId"
            :abstained="draftState.abstained"
            :linked-ids="linkedIds"
            :title="form.title"
            @back="step = 5"
            @restart="restartWizard"
            @change="onReviewChange"
          />
        </div>
      </section>
    </div>
  </div>
</template>
