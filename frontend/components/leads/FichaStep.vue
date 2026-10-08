<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Button from "~/components/ui/Button.vue";
import { Alert, AlertDescription } from "~/components/ui/alert";
import { deriveEvidence } from "~/lib/leadEvidence";

// Step 4 "Ficha" of the new-lead workspace. The ficha is composed only from what
// has been linked: "Qué falta" matters as much as what is there. Confirming the
// ficha is the gate that unlocks the Borrador step. If the evidence changes after
// a confirmation, the ficha goes stale and must be confirmed again.
const props = defineProps<{ linkedIds: string[]; alcance: string }>();
const emit = defineEmits<{
  (e: "back"): void;
  (e: "continue"): void;
  (e: "change", payload: { confirmed: boolean }): void;
}>();

const confirmed = ref(false);
const stale = ref(false);

const derived = computed(() => deriveEvidence(props.linkedIds));

// Ficha rows, derived from the linked set exactly as the Lead Workspace design
// composes them. Only "Qué falta" carries the amber label; the rest stay muted.
const rows = computed(() => {
  const linked = derived.value.linked;
  const sup = linked.filter((s) => s.rel === "Respalda");
  const con = linked.filter((s) => s.rel === "Contradice");
  const primaries = linked.filter((s) => s.rel === "Respalda" && s.type !== "Noticia");
  const primN = derived.value.primN;
  const ev = derived.value.state.key;
  const insuf = ev === "insuficiente";
  const alc = props.alcance.trim();

  return [
    {
      label: "Qué se reporta",
      text: sup[0] ? sup[0].s : "Sin afirmación respaldada.",
      cite: sup[0] ? `[${sup[0].id}:${sup[0].c}]` : "—",
      amber: false,
    },
    {
      label: "Quién",
      text: `Hogares y comercios de ${alc || "la zona"}; distribuidora; ente regulador.`,
      cite: "—",
      amber: false,
    },
    {
      label: "Qué respalda",
      text: primN
        ? `${primN} ${primN === 1 ? "fuente primaria" : "fuentes primarias"}: ${primaries.map((s) => s.id).join(", ")}.`
        : "Solo testimonios en prensa; sin fuente primaria.",
      cite: "—",
      amber: false,
    },
    {
      label: "Qué falta",
      text:
        ev === "suficiente"
          ? con.length
            ? "Respuesta formal del ente regulador a la versión contraria."
            : "Versión de la distribuidora: no hay fuente contraria vinculada."
          : ev === "parcial"
            ? "Una segunda fuente primaria que corrobore la cifra central."
            : "Fuente primaria (documento o indicador) para la cifra central.",
      cite: "—",
      amber: true,
    },
    {
      label: "Acción",
      text: insuf
        ? "Solicitar documentación antes de redactar, o abstenerse."
        : `Redactar nota explicativa${con.length ? " con ambas versiones." : "."}`,
      cite: "—",
      amber: false,
    },
  ];
});

function confirm() {
  confirmed.value = true;
  stale.value = false;
  emit("change", { confirmed: true });
}

// The ficha is built from the linked set: if that set changes after a
// confirmation, the ficha no longer reflects the evidence and must be re-confirmed.
watch(
  () => props.linkedIds,
  () => {
    if (confirmed.value) {
      confirmed.value = false;
      stale.value = true;
      emit("change", { confirmed: false });
    }
  },
  { deep: true }
);
</script>

<template>
  <div class="flex flex-col gap-3">
    <Alert v-if="stale" variant="warning">
      <AlertDescription class="text-body-sm leading-relaxed text-ink">
        <strong class="font-semibold text-warning">La evidencia cambió.</strong>
        Revisa y confirma la ficha de nuevo.
      </AlertDescription>
    </Alert>

    <!-- Ficha · composed only from linked evidence -->
    <div class="overflow-hidden rounded-md border border-border">
      <div
        v-for="row in rows"
        :key="row.label"
        class="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-x-4 gap-y-1 border-b border-border px-4 py-3.5 last:border-b-0"
      >
        <span
          class="text-label uppercase"
          :class="row.amber ? 'text-warning' : 'text-ink-muted'"
        >
          {{ row.label }}
        </span>
        <span class="text-pretty text-body-sm leading-relaxed [grid-column:span_2]">
          {{ row.text }}
          <span
            v-if="row.cite !== '—'"
            class="ml-0.5 whitespace-nowrap rounded-sm bg-surface-sunken px-1 font-mono text-caption text-ink-muted"
          >
            {{ row.cite }}
          </span>
        </span>
      </div>
    </div>

    <!-- Footer nav -->
    <div class="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
      <Button variant="outline" @click="emit('back')">← Atrás</Button>
      <Button v-if="confirmed" @click="emit('continue')">Continuar · Borrador →</Button>
      <Button v-else @click="confirm">Confirmar ficha</Button>
    </div>
  </div>
</template>
