<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import Button from "~/components/ui/Button.vue";
import Textarea from "~/components/ui/Textarea.vue";
import { ToggleGroup, ToggleGroupItem } from "~/components/ui/toggle-group";
import { api } from "~/composables/useApi";
import { useAuth } from "~/composables/useAuth";

// Step 6 "Revisión" of the new-lead workspace. The editorial decision over the
// generated draft (or the abstention) is the last gate: a review state is chosen,
// an optional note is added, and saving persists both — POST /cases/{id}/notes
// records the audit note and moves the case's `estado` to the chosen state, exactly
// the five states the backend accepts. The lead then lives in the bandeja with its
// trail. Nothing here invents content; it only files the human decision.
interface PersistedNote {
  autor: string;
  estado_revision?: string;
  texto: string;
  created_at?: string | null;
}
const props = withDefaults(
  defineProps<{
    leadId: number;
    abstained: boolean;
    linkedIds: string[];
    title: string;
    readonly?: boolean;
    // Lead detail: the case's current estado and its recorded review notes.
    decision?: string;
    auditNotes?: PersistedNote[];
    // Wizard: seed the pick and note so a back-then-forward keeps them.
    initialReview?: string;
    initialNote?: string;
    // Label for the finish button after a decision is saved (edit vs create).
    restartLabel?: string;
  }>(),
  { readonly: false, decision: "", auditNotes: () => [], initialReview: "", initialNote: "", restartLabel: "Crear otro lead" }
);
const emit = defineEmits<{
  (e: "back"): void;
  (e: "restart"): void;
  (e: "change", payload: { saved: boolean; estado: string; label: string }): void;
  (e: "draft", payload: { review: string; note: string }): void;
}>();

// The five editorial states, in the design's order. Keys match the backend's
// REVIEW_STATES; each carries the chip colours its selected state uses.
const REVIEW_OPTIONS = [
  { key: "nuevo", label: "Nuevo", on: "data-[state=on]:border-info data-[state=on]:bg-info/10 data-[state=on]:text-info" },
  { key: "en_revision", label: "En revisión", on: "data-[state=on]:border-primary data-[state=on]:bg-primary-soft data-[state=on]:text-primary" },
  { key: "requiere_evidencia", label: "Requiere evidencia", on: "data-[state=on]:border-warning data-[state=on]:bg-warning/10 data-[state=on]:text-warning" },
  { key: "aprobado_borrador", label: "Borrador aprobado", on: "data-[state=on]:border-success data-[state=on]:bg-success/10 data-[state=on]:text-success" },
  { key: "descartado", label: "Descartado", on: "data-[state=on]:border-ink-muted data-[state=on]:bg-surface-sunken data-[state=on]:text-ink" },
] as const;
const LABEL: Record<string, string> = Object.fromEntries(REVIEW_OPTIONS.map((o) => [o.key, o.label]));

const review = ref<string>(props.readonly ? props.decision : props.initialReview);
const note = ref(props.readonly ? "" : props.initialNote);
const saved = ref(false);
const saving = ref(false);
const saveError = ref("");

// Keep the parent's draft of the editorial decision in sync so it survives a
// back-then-forward through the wizard.
watch([review, note], () => {
  if (!props.readonly) emit("draft", { review: review.value, note: note.value });
});

// What is under review: the abstention, or the generated draft.
const reviewSubject = computed(() =>
  props.abstained ? "abstención registrada" : "borrador generado"
);

// A small, honest audit trail: the review opening, then the filed decision.
interface AuditEntry {
  t: string;
  msg: string;
}
const hhmm = () =>
  new Date().toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit", hour12: false });
const audit = reactive<AuditEntry[]>([{ t: hhmm(), msg: `revisión abierta · ${reviewSubject.value}` }]);

function stamp(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? "—"
    : d.toLocaleString("es", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false });
}

// Read-only (lead detail): the trail is the case's persisted review notes, oldest
// first; interactively it is the live open/decision trail above.
const auditEntries = computed<AuditEntry[]>(() => {
  if (!props.readonly) return audit;
  return props.auditNotes.map((n) => ({
    t: stamp(n.created_at),
    msg: `${n.estado_revision ? `${LABEL[n.estado_revision] ?? n.estado_revision} · ` : ""}${n.autor}: ${n.texto}`,
  }));
});

// A review state must be picked before the decision can be saved. Approving the
// draft is impossible when the reporter abstained — there is no draft to approve.
const canApprove = (key: string) => !(props.abstained && key === "aprobado_borrador");

function onPick(value: string | string[] | undefined) {
  // Single ToggleGroup: ignore the deselect (empty) the group emits when the active
  // pill is clicked — the design always keeps a choice once made.
  const next = Array.isArray(value) ? value[0] : value;
  if (!next || !canApprove(next)) return;
  review.value = next;
  saved.value = false;
}

async function save() {
  if (!review.value || saving.value) return;
  saveError.value = "";
  saving.value = true;
  const auth = useAuth();
  const autor = auth.user.value?.nombre || auth.user.value?.email || "Equipo editorial";
  // The note body is required by the API; fall back to the decision itself.
  const texto = note.value.trim() || `Decisión: ${LABEL[review.value]}`;
  try {
    await api(`cases/${props.leadId}/notes`, {
      method: "POST",
      body: { autor, estado_revision: review.value, texto },
    });
    saved.value = true;
    audit.push({ t: hhmm(), msg: `decisión ${LABEL[review.value]} registrada · ${autor}` });
    emit("change", { saved: true, estado: review.value, label: LABEL[review.value] });
  } catch (err: any) {
    saveError.value =
      err?.data?.detail || err?.message || "No se pudo guardar la decisión. Inténtalo de nuevo.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- What is being reviewed -->
    <div class="rounded-md bg-surface-sunken px-4 py-3 text-body-sm leading-normal">
      Revisando: <strong class="font-semibold">{{ reviewSubject }}</strong>
    </div>

    <!-- Editorial decision · single-select pill group (static in read-only) -->
    <span class="text-label uppercase text-ink-muted">Decisión editorial</span>
    <ToggleGroup
      type="single"
      :model-value="review"
      class="flex-wrap justify-start gap-2"
      @update:model-value="onPick"
    >
      <ToggleGroupItem
        v-for="o in REVIEW_OPTIONS"
        :key="o.key"
        :value="o.key"
        :disabled="readonly || !canApprove(o.key)"
        :aria-label="o.label"
        class="h-auto min-h-11 gap-2 rounded-full border-[1.5px] border-border bg-surface px-4 text-caption font-semibold text-ink-muted hover:bg-surface-sunken hover:text-ink"
        :class="o.on"
      >
        <span class="h-2 w-2 shrink-0 rounded-full bg-current" />
        {{ o.label }}
      </ToggleGroupItem>
    </ToggleGroup>

    <!-- Optional note for the team -->
    <Textarea v-if="!readonly" v-model="note" :rows="3" placeholder="Nota para el equipo (opcional)" class="resize-y" />

    <!-- Audit trail -->
    <div class="flex flex-col gap-1.5 rounded-md bg-surface-sunken p-3 font-mono text-caption leading-normal text-ink-muted">
      <span v-if="readonly && !auditEntries.length">Sin notas de revisión registradas.</span>
      <span v-for="(a, i) in auditEntries" :key="i">{{ a.t }} · {{ a.msg }}</span>
    </div>

    <p v-if="saveError" class="text-body-sm text-destructive">{{ saveError }}</p>

    <!-- Saved confirmation -->
    <div
      v-if="saved && !readonly"
      class="flex flex-col gap-1 rounded-md border border-success/50 bg-success/5 p-4"
    >
      <span class="font-serif text-heading-md text-success">Lead registrado en la bandeja</span>
      <span class="text-body-sm leading-normal text-ink">
        Estado <strong class="font-semibold">{{ LABEL[review] }}</strong>. Todas las afirmaciones
        quedan trazadas a sus fuentes.
      </span>
    </div>

    <!-- Footer nav -->
    <div v-if="!readonly" class="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
      <Button variant="outline" @click="emit('back')">← Atrás</Button>
      <Button v-if="saved" variant="outline" @click="emit('restart')">{{ restartLabel }}</Button>
      <div v-else class="flex items-center gap-3">
        <span v-if="!review" class="text-caption font-medium text-ink-muted">Elige un estado</span>
        <Button :disabled="!review || saving" @click="save">
          {{ saving ? "Guardando…" : "Guardar decisión" }}
        </Button>
      </div>
    </div>
  </div>
</template>
