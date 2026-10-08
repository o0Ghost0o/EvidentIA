<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import Button from "~/components/ui/Button.vue";
import Input from "~/components/ui/Input.vue";
import Label from "~/components/ui/Label.vue";
import Select from "~/components/ui/Select.vue";
import Textarea from "~/components/ui/Textarea.vue";
import { api } from "~/composables/useApi";

// New lead — step 1 "Definir" of the Lead Workspace. Captures the minimum that makes
// a lead exist (título + modalidad), plus optional alcance and research question.
// The backend case model (titulo / queries[] / flags[]) is the persistence target:
// pregunta → queries[0]; modalidad label + alcance are carried as flags.

const MODALIDAD_OPTIONS = [
  { value: "Investigación", label: "Investigación" },
  { value: "Verificación", label: "Verificación" },
  { value: "Seguimiento", label: "Seguimiento" },
];

// Mirrors the design's "Usar ejemplo" seed so the flow can be walked quickly.
const EXAMPLE = {
  title: "Alza en tarifas eléctricas residenciales en Colón tras la revisión de septiembre",
  mod: "Investigación",
  alc: "Provincia de Colón",
  q: "¿Cuánto aumentó la factura residencial promedio y qué parte del alza se explica por la resolución tarifaria frente a lecturas estimadas?",
};

// Step rail — step 1 is active; the rest unlock later in the workspace.
const STEPS = [
  { title: "Definir", lockReason: "", activeSub: "Título y modalidad" },
  { title: "Evidencia", lockReason: "Crea el lead primero" },
  { title: "Contexto & Priorización", lockReason: "Vincula ≥1 fuente" },
  { title: "Ficha", lockReason: "Calcula la prioridad" },
  { title: "Borrador", lockReason: "Confirma la ficha" },
  { title: "Revisión", lockReason: "Requiere borrador o abstención" },
];

const form = reactive({ title: "", mod: "", alc: "", q: "" });
const tried = ref(false);
const submitting = ref(false);
const submitError = ref("");

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
        queries: form.q.trim() ? [form.q.trim()] : [],
        flags,
      },
    });
    await navigateTo(`/leads/${res.id}`);
  } catch (err: any) {
    submitError.value =
      err?.data?.detail || err?.message || "No se pudo crear el lead. Inténtalo de nuevo.";
    submitting.value = false;
  }
}
</script>

<template>
  <div>
    <!-- Breadcrumb -->
    <nav class="mb-3 flex items-center gap-1.5 text-caption font-medium text-ink-muted">
      <NuxtLink to="/leads" class="text-ink-muted no-underline hover:text-ink">← Leads</NuxtLink>
      <span>/</span>
      <span>Nuevo lead</span>
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
        <!-- Chips appear as the lead progresses; empty at creation -->
        <div class="flex min-h-6 flex-wrap items-center gap-2" />
      </div>
      <div class="font-mono text-caption text-ink-muted">0/6 pasos completos</div>
    </div>

    <div class="flex flex-wrap items-start gap-6">
      <!-- Aside: summary + step rail -->
      <aside class="sticky top-4 flex basis-[280px] flex-col gap-4" style="flex: 0 1 280px; min-width: 260px">
        <div class="flex flex-col gap-3 rounded-md border border-border bg-surface p-4 shadow-ev-1">
          <div class="text-label uppercase text-ink-muted">Resumen del lead</div>
          <div class="grid grid-cols-[auto_1fr] gap-x-3 gap-y-2 text-body-sm">
            <span class="text-ink-muted">Modalidad</span><span>{{ form.mod || "—" }}</span>
            <span class="text-ink-muted">Alcance</span><span>{{ form.alc.trim() || "—" }}</span>
            <span class="text-ink-muted">Fuentes</span><span class="font-mono">—</span>
            <span class="text-ink-muted">Prioridad</span><span class="font-mono">—</span>
          </div>
          <div class="h-1 overflow-hidden rounded-full bg-surface-sunken">
            <div class="h-full bg-success transition-[width] duration-500" style="width: 0%" />
          </div>
        </div>

        <nav class="flex flex-col gap-0.5 rounded-lg bg-surface-sunken p-2">
          <div
            v-for="(s, i) in STEPS"
            :key="s.title"
            class="flex min-h-11 items-start gap-3 rounded-md border-l-[3px] px-3 py-2.5 transition-colors"
            :class="
              i === 0
                ? 'border-primary bg-surface'
                : 'cursor-not-allowed border-transparent opacity-50'
            "
          >
            <div
              class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-[1.5px] font-mono text-caption"
              :class="
                i === 0
                  ? 'border-primary bg-primary text-on-primary'
                  : 'border-dashed border-ink-muted text-ink-muted'
              "
            >
              {{ i + 1 }}
            </div>
            <div class="flex min-w-0 flex-col gap-0.5">
              <span
                class="font-semibold leading-tight"
                :class="i === 0 ? 'font-serif text-heading-md text-ink' : 'text-body-sm text-ink-muted'"
              >
                {{ s.title }}
              </span>
              <span class="text-caption font-medium leading-snug text-ink-muted">
                {{ i === 0 ? s.activeSub : s.lockReason }}
              </span>
            </div>
          </div>
        </nav>
      </aside>

      <!-- Main form card -->
      <section class="flex min-w-0 flex-1 basis-[560px] flex-col gap-6">
        <div class="flex flex-col gap-6 rounded-md border border-border bg-surface p-6 shadow-ev-1">
          <div class="flex flex-col gap-1.5 border-b border-border pb-4">
            <span class="text-label uppercase text-ink-muted">Paso 1 de 6</span>
            <h2 class="font-serif text-display-lg">Definir</h2>
            <p class="max-w-[60ch] text-balance text-body-sm text-ink-muted">
              Qué se investiga, con qué alcance y con qué pregunta.
            </p>
          </div>

          <!-- Guía -->
          <div class="flex items-start gap-3 rounded-md bg-primary-soft px-4 py-3">
            <span class="whitespace-nowrap pt-0.5 text-label uppercase text-primary">Guía</span>
            <p class="text-balance text-body-sm text-ink">
              Empieza por el título y la modalidad: son lo mínimo para que el lead exista. Usa
              «Usar ejemplo» si quieres recorrer el flujo rápido.
            </p>
          </div>

          <form class="flex flex-col gap-4" novalidate @submit.prevent="createLead">
            <div class="flex justify-end">
              <Button type="button" variant="outline" @click="fillExample">Usar ejemplo</Button>
            </div>

            <div class="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4">
              <div class="col-span-full flex flex-col gap-1.5">
                <Label for="lead-title">Título *</Label>
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
                <Label>Modalidad *</Label>
                <Select
                  v-model="form.mod"
                  :options="MODALIDAD_OPTIONS"
                  placeholder="Selecciona…"
                  :invalid="modInvalid"
                />
                <span class="text-caption font-medium text-destructive">
                  {{ modInvalid ? "Elige una modalidad" : "" }}
                </span>
              </div>

              <div class="flex flex-col gap-1.5">
                <Label for="lead-alcance">Alcance</Label>
                <Input id="lead-alcance" v-model="form.alc" placeholder="Región o ámbito" />
              </div>

              <div class="col-span-full flex flex-col gap-1.5">
                <Label for="lead-q">Pregunta de investigación</Label>
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

            <!-- Footer action bar -->
            <div class="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
              <!-- Atrás is hidden on step 1 but reserves layout, matching the design -->
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
        </div>
      </section>
    </div>
  </div>
</template>
