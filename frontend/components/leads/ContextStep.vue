<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import Button from "~/components/ui/Button.vue";
import { api } from "~/composables/useApi";
import { EVIDENCE_STATES, type EvidenceLevel } from "~/lib/leadEvidence";
import {
  BAND_LABEL,
  COMPONENT_LABEL,
  SCORE_FORMULA,
  type ScoreResponse,
  evidenceLevelFrom,
} from "~/lib/leadWizard";

// Step 3 "Contexto & Priorización" of the new-lead workspace. Priority is read
// from the deterministic rules endpoint (GET /cases/{id}/score): every component
// is explainable and reproducible. A high priority with insufficient evidence
// never unlocks the draft — it is surfaced as a warning; the score alone never
// authorises publication.
const props = withDefaults(
  defineProps<{ leadId: number; evidenceLevel?: EvidenceLevel; readonly?: boolean }>(),
  { evidenceLevel: "none", readonly: false }
);
const emit = defineEmits<{
  (e: "back"): void;
  (e: "continue"): void;
  (e: "change", payload: { total: number; band: string; bandLabel: string }): void;
}>();

const scoring = ref(false);
const scored = ref(false);
const score = ref<ScoreResponse | null>(null);
const error = ref("");

// Weight display order follows the formula P = 30R + 25I + 20U + 15N + 10E.
const COMPONENT_ORDER = ["R", "I", "U", "N", "E"] as const;

// Evidence level comes from the score when present, falling back to the prop.
const evLevel = computed<EvidenceLevel>(() =>
  score.value ? evidenceLevelFrom(score.value.evidence_state, 1) : props.evidenceLevel
);
const evState = computed(() => EVIDENCE_STATES[evLevel.value]);
const highInsuf = computed(
  () => scored.value && score.value?.band === "alto" && evLevel.value === "insuficiente"
);

const pDisplay = computed(() => (scored.value && score.value ? String(score.value.P) : "—"));
const bandLabel = computed(() => (scored.value && score.value ? BAND_LABEL[score.value.band] : ""));

const rows = computed(() =>
  COMPONENT_ORDER.map((key) => {
    const value = score.value?.components?.[key] ?? 0;
    const weight = score.value?.weights?.[key] ?? 0;
    return {
      key,
      label: COMPONENT_LABEL[key] ?? key,
      weight,
      value: scored.value ? value.toFixed(2) : "—",
      pct: scored.value ? `${Math.round(value * 100)}%` : "0%",
    };
  })
);

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
const BAND_CHIP: Record<string, string> = {
  alto: "border-destructive/40 bg-destructive/10 text-destructive",
  medio: "border-warning/40 bg-warning/10 text-warning",
  bajo: "border-border bg-surface-sunken text-ink-muted",
};

async function fetchScore() {
  error.value = "";
  try {
    score.value = await api<ScoreResponse>(`cases/${props.leadId}/score`);
    scored.value = true;
    emit("change", {
      total: score.value.P,
      band: score.value.band,
      bandLabel: BAND_LABEL[score.value.band],
    });
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "No se pudo calcular la prioridad.";
  }
}

async function score_() {
  if (scoring.value || scored.value) return;
  scoring.value = true;
  await fetchScore();
  scoring.value = false;
}

// Read-only (lead detail): the priority is already settled, so fetch it at once.
onMounted(() => {
  if (props.readonly) void fetchScore();
});
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
      <!-- Priority panel -->
      <div class="flex flex-col gap-4 rounded-md bg-surface-sunken p-4">
        <div class="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
          <span class="text-label uppercase text-ink-muted">Prioridad</span>
          <span class="font-mono text-caption text-ink-muted">{{ SCORE_FORMULA }}</span>
        </div>

        <div class="flex min-h-10 items-baseline gap-3">
          <span class="font-mono text-display-lg font-medium leading-none [font-variant-numeric:tabular-nums]">
            {{ pDisplay }}
          </span>
          <span
            v-if="scored && score"
            class="whitespace-nowrap rounded-full border px-2.5 py-0.5 text-caption font-semibold"
            :class="BAND_CHIP[score.band]"
          >
            Banda {{ bandLabel }}
          </span>
          <span v-else-if="scoring" class="text-caption font-medium text-ink-muted">Calculando…</span>
        </div>

        <div class="flex flex-col gap-3">
          <div
            v-for="row in rows"
            :key="row.key"
            class="grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-1"
          >
            <span class="text-body-sm">
              {{ row.label }}
              <span class="font-mono text-caption text-ink-muted">×{{ row.weight }}</span>
            </span>
            <span class="font-mono text-mono [font-variant-numeric:tabular-nums]">{{ row.value }}</span>
            <div class="col-span-full h-1.5 overflow-hidden rounded-full bg-border">
              <div
                class="h-full rounded-full bg-primary transition-[width] duration-700 ease-out"
                :style="{ width: row.pct }"
              />
            </div>
          </div>
        </div>

        <span class="self-start rounded-sm bg-surface px-1 font-mono text-caption text-ink-muted">
          reglas {{ score?.rules_version ?? "v1.2" }}
        </span>
      </div>

      <!-- Evidence state + high-priority / insufficient warning -->
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2 rounded-md border p-4" :class="STATE_CARD[evState.tone]">
          <span class="text-label uppercase" :class="STATE_TEXT[evState.tone]">
            Estado de evidencia · {{ evState.label }}
          </span>
          <p class="text-balance text-body-sm leading-relaxed text-ink">{{ evState.explain }}</p>
        </div>

        <div
          v-if="highInsuf"
          class="rounded-md bg-warning/10 px-4 py-3 text-body-sm leading-relaxed text-ink"
        >
          <strong class="font-semibold text-warning">Atención:</strong>
          prioridad alta con evidencia insuficiente. El paso Borrador permanecerá bloqueado.
        </div>
      </div>
    </div>

    <p v-if="error" class="text-body-sm text-destructive">{{ error }}</p>

    <!-- Footer nav -->
    <div v-if="!readonly" class="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
      <Button variant="outline" @click="emit('back')">← Atrás</Button>
      <Button v-if="scored" @click="emit('continue')">Continuar · Ficha →</Button>
      <Button v-else :disabled="scoring" @click="score_">
        {{ scoring ? "Calculando…" : "Calcular prioridad" }}
      </Button>
    </div>
  </div>
</template>
