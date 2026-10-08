<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Popover from "~/components/ui/Popover.vue";
import { cn } from "~/lib/utils";

// score-breakdown — the signature component from DESIGN.md. Makes P explainable:
// five mini bars (R/I/U/N/E) as the trigger, and a popover with the formula,
// per-component weight × value = contribution, and the honest reminder that a high
// P with insufficient evidence means "investigate", never "publish".
type Key = "R" | "I" | "U" | "N" | "E";

const COMP: Record<Key, { name: string; desc: string }> = {
  R: { name: "Relevancia", desc: "Alcance territorial y de audiencia del tema." },
  I: { name: "Impacto", desc: "Consecuencia sobre servicios, dinero o derechos de las personas." },
  U: { name: "Urgencia", desc: "Ventana de tiempo antes de que el hecho ocurra o escale." },
  N: { name: "Novedad", desc: "Distancia frente a lo ya publicado en las últimas 72 h." },
  E: { name: "Evidencia", desc: "Corroboración por procedencias independientes." },
};
const ORDER: Key[] = ["R", "I", "U", "N", "E"];

const props = withDefaults(
  defineProps<{
    components: Record<string, number>;
    weights: Record<string, number>;
    p: number;
    bandLabel: string;
    rulesVersion?: string;
    flag?: boolean;
  }>(),
  { rulesVersion: "v1.2", flag: false }
);

const fmt2 = (v: number) => v.toFixed(2);
const fmt1 = (v: number) => v.toFixed(1);

const rows = computed(() =>
  ORDER.map((k) => {
    const value = props.components[k] ?? 0;
    const weight = props.weights[k] ?? 0;
    return {
      k,
      name: COMP[k].name,
      desc: COMP[k].desc,
      weight,
      value,
      vs: fmt2(value),
      pct: `${Math.round(value * 100)}%`,
      contrib: fmt1(value * weight),
    };
  })
);

const sumExpr = computed(() => rows.value.map((r) => r.contrib).join(" + "));

// Hover previews the panel; click pins it open (desktop affordance from DESIGN).
const open = ref(false);
const pinned = ref(false);
watch(open, (v) => {
  if (!v) pinned.value = false;
});
function toggle() {
  open.value = !open.value;
  pinned.value = open.value;
}
function onEnter() {
  if (!pinned.value) open.value = true;
}
function onLeave() {
  if (!pinned.value) open.value = false;
}
</script>

<template>
  <div class="relative" @mouseenter="onEnter" @mouseleave="onLeave">
    <Popover v-model:open="open" align="end" :side-offset="8">
      <template #trigger>
        <button
          type="button"
          :aria-expanded="open"
          title="Ver desglose del puntaje"
          :class="
            cn(
              'flex w-full items-end gap-1 rounded-md border px-2 py-1.5 transition-colors',
              open ? 'border-primary bg-primary-soft' : 'border-hairline bg-transparent hover:border-ink-muted'
            )
          "
          @click="toggle"
        >
          <span
            v-for="r in rows"
            :key="r.k"
            class="flex min-w-0 flex-1 flex-col items-center gap-0.5"
          >
            <span class="flex h-6 w-2.5 items-end overflow-hidden rounded-[2px] bg-surface-sunken">
              <span class="w-full bg-primary" :style="{ height: r.pct }" />
            </span>
            <span class="text-[11px] font-semibold text-ink-muted">{{ r.k }}</span>
            <span class="font-mono text-[11px] tabular-nums text-ink">{{ r.vs }}</span>
          </span>
        </button>
      </template>

      <!-- score-breakdown panel -->
      <div class="flex flex-col gap-3">
        <div class="flex items-center justify-between gap-2">
          <span class="text-label uppercase text-ink-muted">Desglose de prioridad</span>
          <span
            class="rounded-md bg-surface-sunken px-1.5 font-mono text-caption text-ink-muted"
          >
            reglas {{ rulesVersion }}
          </span>
        </div>

        <div
          class="rounded-md bg-surface-sunken px-3 py-2 font-mono text-[13px] tabular-nums text-ink"
        >
          P = 30R + 25I + 20U + 15N + 10E
        </div>

        <div class="flex flex-col gap-2.5">
          <div
            v-for="r in rows"
            :key="r.k"
            class="grid grid-cols-[20px_minmax(0,1fr)_auto] items-baseline gap-x-2 gap-y-0.5"
          >
            <span class="font-mono text-[13px] font-medium text-primary">{{ r.k }}</span>
            <span class="text-[13px] font-semibold text-ink">{{ r.name }}</span>
            <span class="whitespace-nowrap font-mono text-caption tabular-nums text-ink-muted">
              {{ r.weight }} × {{ r.vs }} =
              <span class="font-medium text-ink">{{ r.contrib }}</span>
            </span>
            <span class="col-start-2 col-end-4 text-caption leading-snug text-ink-muted">
              {{ r.desc }}
            </span>
            <span
              class="col-start-2 col-end-4 mt-0.5 h-1 overflow-hidden rounded-full bg-surface-sunken"
            >
              <span class="block h-full bg-primary" :style="{ width: r.pct }" />
            </span>
          </div>
        </div>

        <div class="flex flex-col gap-1.5 border-t border-hairline pt-2.5">
          <span class="font-mono text-caption tabular-nums text-ink">
            P = {{ sumExpr }} = <span class="font-medium">{{ p }}</span> → {{ bandLabel }}
          </span>
          <span class="text-caption leading-snug text-ink-muted">
            Mismas entradas, mismo P. Bandas: alto ≥ 70 · medio 40–69 · bajo &lt; 40.
          </span>
          <span v-if="flag" class="text-caption leading-snug text-error">
            P alto no equivale a publicable: la suficiencia de evidencia se evalúa aparte y hoy es
            insuficiente.
          </span>
        </div>
      </div>
    </Popover>
  </div>
</template>
