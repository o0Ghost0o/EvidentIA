<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import Button from "~/components/ui/Button.vue";
import { Alert, AlertDescription } from "~/components/ui/alert";
import { deriveEvidence } from "~/lib/leadEvidence";
import { type DraftClass, type DraftMode, draftGaps, draftSents, words } from "~/lib/leadDraft";

// Step 5 "Borrador" of the new-lead workspace. The draft is written only from the
// linked evidence, each sentence with a verifiable citation; what is not backed is
// flagged, never filled in. If no primary source backs the central claim the step
// is blocked — the reporter can link more evidence or register an abstention. A
// generated draft (or an abstention) is what unlocks the Revisión step.
const props = withDefaults(
  defineProps<{ linkedIds: string[]; title: string; genDelay?: number }>(),
  { genDelay: 1800 }
);
const emit = defineEmits<{
  (e: "back"): void;
  (e: "continue"): void;
  (e: "goEvidence"): void;
  (e: "change", payload: { draft: boolean; abstained: boolean }): void;
}>();

// --- Generation state machine ---------------------------------------------
const gen = ref(false); // generating
const draft = ref(false); // a draft has been produced
const abstained = ref(false);
const tr = ref(0); // reasoning-trace step, 0..5
const typed = ref(0); // characters revealed while "Redactando"
const dMode = reactive<DraftMode>({ short: false, cautious: false });
const flags = ref<Record<string, boolean>>({}); // sentences marked "sin respaldo"
const asks = ref<Record<string, boolean>>({}); // sentences with a 2nd-source request
const pick = ref<"flag" | "second" | null>(null); // which controlled action is armed

let genTimer: ReturnType<typeof setTimeout> | null = null;
function clearGen() {
  if (genTimer) {
    clearTimeout(genTimer);
    genTimer = null;
  }
}

// --- Derived evidence & draft ----------------------------------------------
const derived = computed(() => deriveEvidence(props.linkedIds));
const ev = computed(() => derived.value.state.key);
const insuf = computed(() => ev.value === "insuficiente");
const isParcial = computed(() => ev.value === "parcial");
const linked = computed(() => derived.value.linked);
// Sources that feed the draft: those that support or contradict (context aside).
const draftSrcCount = computed(
  () => linked.value.filter((s) => s.rel === "Respalda" || s.rel === "Contradice").length
);

const dList = computed(() => draftSents(props.linkedIds, dMode, props.title.trim()));
const dGaps = computed(() => draftGaps(props.linkedIds, ev.value));
const dWords = computed(() => words(props.title) + dList.value.reduce((a, s) => a + words(s.text), 0));
const dCites = computed(() => dList.value.filter((s) => !flags.value[s.key]).length);
const modeLabel = computed(
  () => [dMode.short && "≤250 palabras", dMode.cautious && "cauto"].filter(Boolean).join(" · ") || "completo"
);
const dMeta = computed(
  () => `brf-0128 · ${dCites.value} citas · ${tr.value >= 4 ? dWords.value : "—"} palabras · ${modeLabel.value}`
);

// Progressive reveal of the draft while the trace is in its "Redactando" step.
const dShown = computed(() => {
  const list = dList.value;
  const shown: { s: (typeof list)[number]; n: number; full: boolean }[] = [];
  let off = 0;
  for (const s of list) {
    const len = s.text.length;
    const n = tr.value > 3 ? len : tr.value === 3 ? Math.max(0, Math.min(len, typed.value - off)) : 0;
    off += len;
    if (n) shown.push({ s, n, full: n >= len });
  }
  return shown;
});
const lastFull = computed(() => dShown.value.map((x) => x.full).lastIndexOf(true));

const CLS_COLOR: Record<DraftClass, string> = {
  hecho: "text-success",
  "declaración": "text-[#0369A1]",
  inferencia: "text-[#6B4FA0]",
  "hipótesis": "text-warning",
};

const dSents = computed(() =>
  dShown.value.map(({ s, n, full }, i) => {
    const flagged = !!flags.value[s.key];
    const lit = gen.value && i === lastFull.value; // the line being written right now
    const clickable = !!pick.value && !gen.value;
    return {
      key: s.key,
      text: s.text.slice(0, n),
      caret: full ? "" : "▍",
      flagged,
      showCite: full && !flagged,
      cite: s.cite,
      cls: s.cls,
      clsColor: CLS_COLOR[s.cls],
      asked: !!asks.value[s.key],
      lit,
      clickable,
      onPick: clickable ? () => pickSent(s.key) : undefined,
    };
  })
);

// --- Reasoning trace --------------------------------------------------------
const pl = (n: number, a: string, b: string) => `${n} ${n === 1 ? a : b}`;
const cnt = (k: DraftClass) => dList.value.filter((s) => s.cls === k).length;

const trace = computed(() => {
  const list = dList.value;
  const indepN = new Set(linked.value.map((s) => s.p)).size;
  const aggN = derived.value.replicaGroups.map((g) => g.size);
  const nFull = dShown.value.filter((x) => x.full).length;
  const rows: [string, string][] = [
    [
      `Recuperando ${linked.value.length} fuentes vinculadas`,
      `${indepN} procedencias independientes` + (aggN.length ? ` · ${aggN[0]} réplicas = 1 fuente` : ""),
    ],
    [
      "Verificando respaldo por afirmación",
      `${pl(list.length, "afirmación", "afirmaciones")} · ${cnt("hecho")} con respaldo documental`,
    ],
    [
      "Separando hecho / declaración / inferencia / hipótesis",
      `${pl(cnt("hecho"), "hecho", "hechos")} · ${pl(cnt("declaración"), "declaración", "declaraciones")} · ${pl(cnt("inferencia"), "inferencia", "inferencias")} · ${pl(cnt("hipótesis"), "hipótesis", "hipótesis")}`,
    ],
    [
      "Redactando con citas",
      tr.value === 3 ? `${nFull}/${list.length} oraciones` : `${pl(list.length, "oración", "oraciones")} · ${pl(list.length, "cita", "citas")} [id:campo]`,
    ],
    ["Marcando lo no respaldado", dGaps.value.length ? pl(dGaps.value.length, "vacío marcado", "vacíos marcados") : "sin vacíos"],
  ];
  return {
    status: gen.value ? `En curso · ${tr.value}/5` : "Completado · 5/5",
    rows: rows.map(([label, detail], i) => {
      const ok = tr.value > i;
      const on = gen.value && tr.value === i;
      return {
        label,
        detail: ok || (on && i === 3) ? detail : "",
        glyph: ok ? "✓" : on ? "→" : "",
        done: ok,
        active: on,
      };
    }),
  };
});

// --- Controlled actions -----------------------------------------------------
interface DraftAction {
  label: string;
  active: boolean;
  onClick: () => void;
}
const dActs = computed<DraftAction[]>(() => [
  { label: "↻ Regenerar", active: false, onClick: () => startGen({ short: false, cautious: false }, true) },
  {
    label: dMode.short ? "Acortado ✓ · restaurar" : "Acortar a 250 palabras",
    active: dMode.short,
    onClick: () => startGen({ short: !dMode.short }),
  },
  {
    label: dMode.cautious ? "Más cauto ✓ · restaurar" : "Más cauto",
    active: dMode.cautious,
    onClick: () => startGen({ cautious: !dMode.cautious }),
  },
  {
    label: "Marcar afirmación como sin respaldo",
    active: pick.value === "flag",
    onClick: () => togglePick("flag"),
  },
  { label: "Pedir una segunda fuente", active: pick.value === "second", onClick: () => togglePick("second") },
]);

const pickMsg = computed(() =>
  pick.value === "flag"
    ? "Toca la afirmación que quieres marcar como sin respaldo: perderá su cita y quedará como pendiente. Tócala de nuevo luego para retirar la marca."
    : "Toca la afirmación que necesita una segunda fuente independiente. La solicitud queda en la auditoría."
);

// --- View states (design is5*) ---------------------------------------------
const is5Ready = computed(() => !insuf.value && !draft.value && !gen.value);
const is5Work = computed(() => gen.value || draft.value);
const is5Blocked = computed(() => insuf.value && !abstained.value);
const is5Abstained = computed(() => abstained.value);
const dGapsOn = computed(() => tr.value >= 5 && dGaps.value.length > 0);
const dDone = computed(() => draft.value && !gen.value);
const dWaiting = computed(() => tr.value < 3);
const pickOn = computed(() => !!pick.value && draft.value);
const draftHead = computed(() => props.title.trim() || "Borrador");

// --- Methods ----------------------------------------------------------------
function startGen(opts: Partial<DraftMode>, fresh = false) {
  clearGen();
  Object.assign(dMode, opts);
  gen.value = true;
  draft.value = false;
  tr.value = 0;
  typed.value = 0;
  pick.value = null;
  if (fresh) {
    flags.value = {};
    asks.value = {};
  }
  const ms = props.genDelay / 5;
  const tick = () => {
    if (tr.value < 3) {
      const next = tr.value + 1;
      tr.value = next;
      genTimer = setTimeout(tick, next === 3 ? 60 : ms);
      return;
    }
    if (tr.value === 3) {
      const total = dList.value.reduce((a, s) => a + s.text.length, 0);
      if (typed.value < total) {
        typed.value += Math.max(3, Math.ceil(total / 120));
        genTimer = setTimeout(tick, 22);
        return;
      }
      tr.value = 4;
      genTimer = setTimeout(tick, ms);
      return;
    }
    tr.value = 5;
    gen.value = false;
    draft.value = true;
  };
  genTimer = setTimeout(tick, ms);
}

function generate() {
  startGen({ short: false, cautious: false }, true);
}

function togglePick(p: "flag" | "second") {
  pick.value = pick.value === p ? null : p;
}

function pickSent(key: string) {
  if (pick.value === "flag") {
    const on = !flags.value[key];
    const next = { ...flags.value };
    if (on) next[key] = true;
    else delete next[key];
    flags.value = next;
    pick.value = null;
  } else if (pick.value === "second") {
    pick.value = null;
    if (asks.value[key]) return;
    asks.value = { ...asks.value, [key]: true };
  }
}

function abstain() {
  abstained.value = true;
}
function undoAbstain() {
  abstained.value = false;
}

// The draft is built from the linked set: if that set changes upstream, any draft
// or abstention no longer reflects the evidence and is cleared.
watch(
  () => props.linkedIds,
  () => {
    clearGen();
    gen.value = false;
    draft.value = false;
    abstained.value = false;
    tr.value = 0;
    typed.value = 0;
  },
  { deep: true }
);

watch([draft, abstained], () => emit("change", { draft: draft.value, abstained: abstained.value }));

onBeforeUnmount(clearGen);
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Ready · evidence is sufficient/partial, draft not yet generated -->
    <template v-if="is5Ready">
      <Alert v-if="isParcial" variant="warning">
        <AlertDescription class="text-body-sm leading-relaxed text-ink">
          <strong class="font-semibold text-warning">Evidencia parcial.</strong>
          El borrador marcará como pendiente lo que no está respaldado.
        </AlertDescription>
      </Alert>

      <div class="flex flex-col gap-2 rounded-md bg-surface-sunken p-4">
        <span class="text-label uppercase text-ink-muted">
          Se usarán {{ draftSrcCount }} fuentes vinculadas
        </span>
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="l in linked"
            :key="l.id"
            class="rounded-sm bg-surface px-1 font-mono text-caption text-ink-muted"
          >
            {{ l.id }}
          </span>
        </div>
      </div>
    </template>

    <!-- Work · generation trace + the draft itself -->
    <template v-else-if="is5Work">
      <!-- Reasoning over the linked evidence -->
      <div class="flex flex-col gap-2.5 rounded-md border border-border bg-canvas p-4">
        <div class="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
          <span class="text-label uppercase text-primary">Razonamiento sobre evidencia vinculada</span>
          <span class="font-mono text-caption text-ink-muted [font-variant-numeric:tabular-nums]">
            {{ trace.status }}
          </span>
        </div>
        <div
          v-for="(r, i) in trace.rows"
          :key="i"
          class="flex items-start gap-2.5 transition-opacity"
          :class="r.done || r.active ? 'opacity-100' : 'opacity-60'"
        >
          <span
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-[1.5px] text-[11px] font-semibold transition-colors"
            :class="
              r.done
                ? 'border-success bg-success text-white'
                : r.active
                  ? 'border-primary bg-transparent text-primary'
                  : 'border-ink-muted bg-transparent text-primary'
            "
          >
            {{ r.glyph }}
          </span>
          <div class="flex min-w-0 flex-wrap items-baseline gap-x-2.5 gap-y-0.5">
            <span
              class="text-body-sm leading-5"
              :class="[r.done || r.active ? 'text-ink' : 'text-ink-muted', r.active ? 'font-semibold' : 'font-normal']"
            >
              {{ r.label }}
            </span>
            <span class="font-mono text-caption text-ink-muted [font-variant-numeric:tabular-nums]">
              {{ r.detail }}
            </span>
          </div>
        </div>
        <span class="border-t border-border pt-2.5 font-mono text-[11px] leading-relaxed text-ink-muted">
          Solo fuentes vinculadas · ninguna cifra fuera de ellas · lo no respaldado se marca, no se completa
        </span>
      </div>

      <!-- The draft -->
      <article class="flex flex-col gap-3 rounded-md border border-border p-6">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <span class="text-caption font-semibold uppercase tracking-[0.6px] text-ink-muted">
            Borrador · no publicado
          </span>
          <span class="font-mono text-caption text-ink-muted [font-variant-numeric:tabular-nums]">
            {{ dMeta }}
          </span>
        </div>
        <h3 class="text-balance font-serif text-display-lg leading-tight">{{ draftHead }}</h3>

        <p v-if="dWaiting" class="text-body-sm text-ink-muted">
          El texto se redactará cuando termine la verificación.
        </p>

        <p
          v-for="s in dSents"
          :key="s.key"
          class="-ml-2 max-w-[68ch] text-pretty rounded-md px-2 py-1 text-body-md leading-relaxed outline-1 transition-colors"
          :class="[
            s.flagged ? 'bg-warning/10 text-warning' : 'bg-transparent text-ink',
            s.clickable ? 'cursor-pointer outline-dashed outline-[#9DB5D3]' : 'outline-transparent',
          ]"
          @click="s.onPick?.()"
        >
          <strong v-if="s.flagged" class="font-semibold">[Sin respaldo] </strong>{{ s.text }}<span class="text-primary">{{ s.caret }}</span>
          <template v-if="s.showCite">
            <span
              class="ml-0.5 whitespace-nowrap rounded-sm px-1 font-mono text-caption transition-colors"
              :class="s.lit ? 'bg-primary text-on-primary' : 'bg-primary-soft text-primary'"
            >
              {{ s.cite }}
            </span>
            <span class="ml-0.5 whitespace-nowrap text-[10px] font-semibold uppercase tracking-[0.6px]" :class="s.clsColor">
              {{ s.cls }}
            </span>
          </template>
          <span
            v-if="s.asked"
            class="ml-1 whitespace-nowrap rounded-full border border-primary/40 bg-surface px-2 py-px text-[11px] font-semibold text-primary"
          >
            2ª fuente solicitada
          </span>
        </p>

        <div v-if="dGapsOn" class="flex flex-col gap-1.5 border-t border-border pt-3">
          <p v-for="(g, i) in dGaps" :key="i" class="text-pretty text-body-sm leading-relaxed text-warning">
            [Sin respaldo] {{ g }}
          </p>
        </div>
      </article>

      <!-- Controlled actions, available once the draft is settled -->
      <div v-if="dDone" class="flex flex-col gap-2.5">
        <span class="text-label uppercase text-ink-muted">Acciones controladas</span>
        <div class="flex flex-wrap gap-2">
          <Button
            v-for="a in dActs"
            :key="a.label"
            variant="outline"
            class="h-9 text-caption font-semibold"
            :class="a.active ? 'border-primary bg-primary-soft text-primary' : ''"
            @click="a.onClick"
          >
            {{ a.label }}
          </Button>
        </div>
        <div
          v-if="pickOn"
          class="flex flex-wrap items-center gap-3 rounded-md bg-primary-soft px-4 py-2.5"
        >
          <span class="flex-1 basis-60 text-pretty text-body-sm leading-relaxed text-ink">{{ pickMsg }}</span>
          <Button variant="outline" class="h-8 border-none bg-transparent text-caption text-primary hover:bg-transparent" @click="pick = null">
            Cancelar
          </Button>
        </div>
      </div>
    </template>

    <!-- Blocked · no primary source backs the claim -->
    <template v-else-if="is5Blocked">
      <div class="flex flex-col gap-2 rounded-md border-[1.5px] border-destructive p-4">
        <span class="text-label uppercase text-destructive">Paso bloqueado</span>
        <p class="font-serif text-heading-md leading-tight">Evidencia insuficiente para generar un borrador</p>
        <p class="text-pretty text-body-sm leading-relaxed text-ink-muted">
          Ninguna fuente primaria (documento o indicador) respalda la afirmación central. Prioridad alta con
          evidencia insuficiente nunca habilita publicación.
        </p>
        <div class="mt-1 flex flex-wrap items-center gap-3">
          <Button disabled>Generar borrador</Button>
          <span class="text-caption font-medium text-ink-muted">Requiere evidencia parcial o suficiente</span>
        </div>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button variant="outline" @click="emit('goEvidence')">← Vincular más evidencia</Button>
        <Button
          variant="outline"
          class="border-destructive bg-surface text-destructive hover:bg-destructive/5"
          @click="abstain"
        >
          Registrar abstención
        </Button>
      </div>
    </template>

    <!-- Abstained -->
    <div
      v-else-if="is5Abstained"
      class="flex flex-col gap-3 rounded-md border-[1.5px] border-destructive bg-destructive/5 p-6"
    >
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h3 class="font-serif text-heading-md leading-tight">Abstención</h3>
        <span class="font-mono text-caption text-ink-muted">abs-0128</span>
      </div>
      <p class="text-pretty text-body-sm leading-relaxed text-ink">
        No se generó borrador. Las fuentes vinculadas no incluyen respaldo documental ni indicadores para la
        afirmación central.
      </p>
      <p class="text-body-sm font-semibold text-success">Ninguna cifra o cita fue inventada.</p>
      <div>
        <Button variant="outline" class="h-9 border-none bg-transparent text-ink-muted hover:bg-transparent hover:text-ink" @click="undoAbstain">
          Deshacer abstención
        </Button>
      </div>
    </div>

    <!-- Footer nav -->
    <div class="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
      <Button variant="outline" @click="emit('back')">← Atrás</Button>
      <Button v-if="draft || abstained" @click="emit('continue')">Continuar · Revisión →</Button>
      <Button v-else-if="!insuf" :disabled="gen" @click="generate">
        {{ gen ? "Generando…" : "Generar borrador" }}
      </Button>
    </div>
  </div>
</template>
