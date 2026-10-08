<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import Button from "~/components/ui/Button.vue";
import { EVIDENCE_STATES, type EvidenceLevel } from "~/lib/leadEvidence";
import {
  BAND_LABEL,
  SCORE_FORMULA,
  computePriority,
  type Priority,
} from "~/lib/leadPriority";

// Step 3 "Contexto & Priorización" of the new-lead workspace. Priority is computed
// with versioned rules (not model judgement): every component is explainable. A
// high priority with insufficient evidence never unlocks the draft — it is
// surfaced as a warning, the score alone never authorises publication.
const props = withDefaults(defineProps<{ evidenceLevel: EvidenceLevel; readonly?: boolean }>(), {
  readonly: false,
});
const emit = defineEmits<{
  (e: "back"): void;
  (e: "continue"): void;
  (e: "change", payload: { total: number; band: string; bandLabel: string }): void;
}>();

const scoring = ref(false);
const scored = ref(false);
const priority = ref<Priority | null>(null);
let timer: ReturnType<typeof setTimeout> | null = null;

const evState = computed(() => EVIDENCE_STATES[props.evidenceLevel]);
// A high priority on evidence that no primary source backs: the draft stays locked.
const highInsuf = computed(() => scored.value && props.evidenceLevel === "insuficiente");

const pDisplay = computed(() => (scored.value && priority.value ? String(priority.value.total) : "—"));
const bandLabel = computed(() =>
  scored.value && priority.value ? BAND_LABEL[priority.value.band] : ""
);

// Score rows: before calculating, show the weights with placeholder values.
const rows = computed(() =>
  computePriority().components.map((c) => ({
    key: c.key,
    label: c.label,
    weight: c.weight,
    value: scored.value ? c.value.toFixed(2) : "—",
    pct: scored.value ? `${c.value * 100}%` : "0%",
  }))
);

// Evidence-state tone → card and text colors (shared with step 2's palette).
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

function applyScore() {
  const p = computePriority();
  priority.value = p;
  scoring.value = false;
  scored.value = true;
  emit("change", { total: p.total, band: p.band, bandLabel: BAND_LABEL[p.band] });
}

function score() {
  if (scoring.value || scored.value) return;
  scoring.value = true;
  timer = setTimeout(applyScore, 900);
}

// Read-only (lead detail): the priority is already settled, so show it at once
// without the calculate step.
onMounted(() => {
  if (props.readonly) applyScore();
});

onBeforeUnmount(() => {
  if (timer) clearTimeout(timer);
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
            v-if="scored && priority"
            class="whitespace-nowrap rounded-full border px-2.5 py-0.5 text-caption font-semibold"
            :class="BAND_CHIP[priority.band]"
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
          reglas {{ priority?.rulesVersion ?? "v1.2" }}
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

    <!-- Footer nav -->
    <div v-if="!readonly" class="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
      <Button variant="outline" @click="emit('back')">← Atrás</Button>
      <Button v-if="scored" @click="emit('continue')">Continuar · Ficha →</Button>
      <Button v-else :disabled="scoring" @click="score">
        {{ scoring ? "Calculando…" : "Calcular prioridad" }}
      </Button>
    </div>
  </div>
</template>
