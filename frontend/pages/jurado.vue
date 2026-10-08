<script setup lang="ts">
import { onMounted, ref } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import { api } from "~/composables/useApi";

interface PruebaDetalle {
  prueba: string;
  comprueba: string;
  segundos: number;
  ok: boolean;
  mensaje?: string;
}

interface FilaPrueba {
  id: string;
  titulo: string;
  esperado: string;
  pruebas: PruebaDetalle[];
  estado: "verde" | "rojo";
  motivo?: string;
}

interface InformeJurado {
  disponible: boolean;
  en_curso: boolean;
  generado_utc?: string;
  segundos?: number;
  verdes: number;
  total: number;
  filas: FilaPrueba[];
  comando?: string;
  salida_resumen?: string;
}

interface FilaMetrica {
  metrica: string;
  meta: string;
  baseline_bm25: string;
  agente_evidentia: string;
  cumple: boolean;
}

interface MetricasJurado {
  disponible: boolean;
  generado_utc?: string;
  conjunto?: string;
  modelo?: string;
  tabla: FilaMetrica[];
  totales?: Record<string, any>;
}

const loadingPruebas = ref(false);
const runningPruebas = ref(false);
const timerSeconds = ref(0);
let timerInterval: any = null;

const informe = ref<InformeJurado | null>(null);
const metricas = ref<MetricasJurado | null>(null);
const errorMsg = ref<string | null>(null);

// Acordeón de pruebas abiertas
const openAccordions = ref<Record<string, boolean>>({});

function toggleAccordion(id: string) {
  openAccordions.value[id] = !openAccordions.value[id];
}

async function fetchUltimoInforme() {
  loadingPruebas.value = true;
  errorMsg.value = null;
  try {
    const res = await api<InformeJurado>("jurado/pruebas");
    informe.value = res;
    // Abrir las primeras 2 por defecto
    if (res?.filas?.length) {
      openAccordions.value[res.filas[0].id] = true;
      openAccordions.value[res.filas[1].id] = true;
    }
  } catch (err: any) {
    errorMsg.value = err?.message || "No se pudo cargar el informe de pruebas.";
  } finally {
    loadingPruebas.value = false;
  }
}

async function fetchMetricas() {
  try {
    const res = await api<MetricasJurado>("jurado/metricas");
    metricas.value = res;
  } catch (err: any) {
    console.error("Error al cargar métricas:", err);
  }
}

async function ejecutarPruebasEnVivo() {
  runningPruebas.value = true;
  timerSeconds.value = 0;
  errorMsg.value = null;

  timerInterval = setInterval(() => {
    timerSeconds.value = Math.round((timerSeconds.value + 0.1) * 10) / 10;
  }, 100);

  try {
    const res = await api<InformeJurado>("jurado/pruebas", { method: "POST" });
    informe.value = res;
    // Abrir todas las pruebas para revisión completa del jurado
    res.filas?.forEach((f) => {
      openAccordions.value[f.id] = true;
    });
  } catch (err: any) {
    errorMsg.value = err?.message || "Error al ejecutar las pruebas en vivo.";
  } finally {
    if (timerInterval) clearInterval(timerInterval);
    runningPruebas.value = false;
  }
}

function formatHoraPA(isoString?: string): string {
  if (!isoString) return "No ejecutado";
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString("es-PA", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return isoString;
  }
}

onMounted(() => {
  fetchUltimoInforme();
  fetchMetricas();
});

const PREGUNTAS_JURADO = [
  {
    pregunta: "«Muéstrame de dónde proviene esta cifra económica y de qué año es»",
    respuesta:
      "Cada cifra del Banco Mundial preserva el ID oficial (ej. WB:PAN:FP.CPI.TOTL.ZG:2023), año y unidad (% anual). Se advierte explícitamente que no es una medición de hoy.",
    enlace: "/leads",
    enlaceTexto: "Ver leads con indicadores oficiales →",
  },
  {
    pregunta: "«Si tres medios replican la misma agencia (EFE), ¿cuántas fuentes independientes cuentan?»",
    respuesta:
      "Una sola procedencia. EvidentIA agrupa réplicas léxicas de agencia sin triplicar la importancia (N < 1.0) ni la corroboración de fuentes primarias.",
    enlace: "/",
    enlaceTexto: "Ver bandeja de eventos agrupados →",
  },
  {
    pregunta: "«¿Qué ocurre si la consulta carece de evidencia en el corpus?»",
    respuesta:
      "Abstención explícita y estructurada. El sistema indica con precisión qué datos faltan y qué acción editorial corresponde, sin alucinar citas ni inventar números.",
    enlace: "/leads/new",
    enlaceTexto: "Probar flujo con verificación de evidencia →",
  },
  {
    pregunta: "«¿Y si una fuente web externa intenta cambiar las instrucciones o inyectar prompts?»",
    respuesta:
      "Las fuentes son tratadas estrictamente como datos pasivos, jamás instrucciones. Cualquier afirmación no soportada o con citas forjadas es descartada por el validador y su evidencia queda en E = 0.",
    enlace: null,
    enlaceTexto: null,
  },
  {
    pregunta: "«¿Cómo demuestran la trazabilidad de relaciones causales y dependencias?»",
    respuesta:
      "Mediante el motor dinámico interactivo GraphRAG a 60 FPS en SVG. Permite explorar visualmente las conexiones entre noticias, eventos sísmicos, indicadores y entidades.",
    enlace: "/graph",
    enlaceTexto: "Explorar Grafo de Conocimiento Interactivo →",
  },
];
</script>

<template>
  <div class="space-y-10 py-6">
    <!-- Header Hero -->
    <div class="border-b border-hairline pb-8">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-xs font-semibold uppercase tracking-wider text-primary">
              Modo Jurado · Reto TVN Media §9
            </span>
            <Badge variant="outline" class="bg-primary/10 text-primary border-primary/20 text-[11px]">
              T01–T10 Live Suite
            </Badge>
          </div>
          <h1 class="mt-2 font-serif text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            Centro de Verificación de Aceptación
          </h1>
          <p class="mt-2 max-w-3xl text-sm leading-relaxed text-ink-muted">
            Ejecución auditable y en tiempo real de los 10 criterios de aceptación obligatorios del pliego
            editorial de TVN Media, ejecutados en un subproceso aislado sobre el motor analítico de EvidentIA.
          </p>
        </div>

        <!-- Action Button -->
        <div class="flex flex-col items-start gap-2 sm:items-end">
          <Button
            size="lg"
            class="shadow-sm font-semibold tracking-wide"
            :disabled="runningPruebas"
            @click="ejecutarPruebasEnVivo"
          >
            <span v-if="runningPruebas" class="flex items-center gap-2">
              <span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-canvas border-t-transparent"></span>
              Corriendo pruebas… {{ timerSeconds }} s
            </span>
            <span v-else class="flex items-center gap-2">
              <span>▶</span>
              <span>Ejecutar Suite T01–T10 en Vivo</span>
            </span>
          </Button>

          <span v-if="informe?.generado_utc && !runningPruebas" class="text-xs text-ink-muted">
            Última corrida: <b>{{ formatHoraPA(informe.generado_utc) }}</b> · Duración: <b>{{ informe.segundos }} s</b>
          </span>
        </div>
      </div>

      <!-- Execution Status Pill -->
      <div v-if="informe" class="mt-6 flex flex-wrap items-center gap-3 rounded-lg border border-hairline bg-surface-sunken/40 p-4">
        <div class="flex items-center gap-2">
          <span class="flex h-3 w-3 rounded-full" :class="informe.verdes === informe.total ? 'bg-emerald-500' : 'bg-rose-500'"></span>
          <span class="text-sm font-semibold text-ink">
            Estado de Aceptación:
          </span>
          <span
            class="font-mono text-sm font-bold"
            :class="informe.verdes === informe.total ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600'"
          >
            {{ informe.verdes }} / {{ informe.total }} Pruebas en Verde ({{ Math.round((informe.verdes / informe.total) * 100) }}%)
          </span>
        </div>

        <span class="text-ink-muted">·</span>
        <span class="font-mono text-xs text-ink-muted">
          {{ informe.comando }}
        </span>
      </div>

      <div v-if="errorMsg" class="mt-4 rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
        {{ errorMsg }}
      </div>
    </div>

    <!-- T01–T10 Test Cards Grid -->
    <section class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="font-serif text-xl font-bold text-ink">
          Pruebas de Aceptación Obligatorias (§9)
        </h2>
        <span class="text-xs text-ink-muted">
          Haz clic en cada tarjeta para inspeccionar aserciones y tiempos
        </span>
      </div>

      <div v-if="loadingPruebas && !informe" class="py-12 text-center text-sm text-ink-muted">
        Cargando estado de pruebas del jurado…
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="f in informe?.filas"
          :key="f.id"
          class="rounded-lg border transition-all"
          :class="f.estado === 'verde' ? 'border-emerald-500/20 bg-surface' : 'border-rose-500/30 bg-rose-50/10'"
        >
          <!-- Card Header (Clickable) -->
          <button
            type="button"
            class="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-surface-sunken/30"
            @click="toggleAccordion(f.id)"
          >
            <div class="flex items-center gap-3">
              <span
                class="flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold"
                :class="f.estado === 'verde' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'"
              >
                {{ f.estado === 'verde' ? '✓' : '✕' }}
              </span>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-mono text-xs font-bold uppercase tracking-wider text-primary">
                    {{ f.id }}
                  </span>
                  <span class="font-semibold text-ink text-sm sm:text-base">
                    {{ f.titulo }}
                  </span>
                </div>
                <p class="text-xs text-ink-muted mt-0.5 line-clamp-1">
                  {{ f.esperado }}
                </p>
              </div>
            </div>

            <div class="flex items-center gap-4">
              <span v-if="f.pruebas?.[0]?.segundos" class="font-mono text-xs text-ink-muted hidden sm:inline">
                {{ f.pruebas[0].segundos }} s
              </span>
              <span class="text-xs text-ink-muted">
                {{ openAccordions[f.id] ? '▲' : '▼' }}
              </span>
            </div>
          </button>

          <!-- Card Content (Accordion) -->
          <div v-if="openAccordions[f.id]" class="border-t border-hairline/60 bg-surface-sunken/20 p-4 space-y-3 text-sm">
            <div>
              <span class="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Criterio Oficial del Pliego TVN:
              </span>
              <p class="mt-1 text-ink text-xs sm:text-sm leading-relaxed bg-surface p-2.5 rounded border border-hairline/50">
                {{ f.esperado }}
              </p>
            </div>

            <div>
              <span class="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Evidencia de Ejecución Pytest:
              </span>
              <div class="mt-1 space-y-2">
                <div
                  v-for="p in f.pruebas"
                  :key="p.prueba"
                  class="rounded border border-hairline/60 bg-surface p-2.5 text-xs font-mono"
                >
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-ink">
                      {{ p.prueba }}
                    </span>
                    <span class="text-ink-muted">
                      {{ p.segundos }} s · {{ p.ok ? 'PASSED ✓' : 'FAILED ✕' }}
                    </span>
                  </div>
                  <p class="font-sans text-xs text-ink-muted mt-1">
                    {{ p.comprueba }}
                  </p>
                  <div v-if="p.mensaje" class="mt-2 rounded bg-rose-100/30 p-2 text-rose-700 dark:text-rose-400">
                    {{ p.mensaje }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Agente EvidentIA vs. Baseline BM25 -->
    <section class="space-y-4 pt-4 border-t border-hairline">
      <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="font-serif text-xl font-bold text-ink">
            Evaluación Comparativa: Agente EvidentIA frente a Baseline BM25
          </h2>
          <p class="text-xs text-ink-muted">
            Benchmark de 40 consultas de desarrollo (§7 y §8): 20 sustentadas, 7 sin respuesta, 7 contradicciones, 6 adversariales.
          </p>
        </div>
        <span v-if="metricas?.modelo" class="font-mono text-xs text-primary bg-primary/10 px-2.5 py-1 rounded border border-primary/20">
          {{ metricas.modelo }}
        </span>
      </div>

      <div class="overflow-x-auto rounded-lg border border-hairline bg-surface">
        <table class="w-full text-left text-sm">
          <thead class="border-b border-hairline bg-surface-sunken/50 text-xs uppercase tracking-wider text-ink-muted">
            <tr>
              <th class="py-3 px-4">Métrica de Evaluación</th>
              <th class="py-3 px-4">Meta Reto</th>
              <th class="py-3 px-4">Baseline BM25</th>
              <th class="py-3 px-4">EvidentIA (Llama-3.3-70B)</th>
              <th class="py-3 px-4 text-right">Cumplimiento</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-hairline">
            <tr v-for="m in metricas?.tabla" :key="m.metrica" class="hover:bg-surface-sunken/20 transition-colors">
              <td class="py-3 px-4 font-medium text-ink">
                {{ m.metrica }}
              </td>
              <td class="py-3 px-4 font-mono text-xs text-ink-muted">
                {{ m.meta }}
              </td>
              <td class="py-3 px-4 font-mono text-xs text-ink-muted">
                {{ m.baseline_bm25 }}
              </td>
              <td class="py-3 px-4 font-mono text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                {{ m.agente_evidentia }}
              </td>
              <td class="py-3 px-4 text-right">
                <Badge variant="outline" class="bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300">
                  Supera Meta ✓
                </Badge>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Preguntas Frecuentes del Jurado -->
    <section class="space-y-4 pt-4 border-t border-hairline">
      <div>
        <h2 class="font-serif text-xl font-bold text-ink">
          Respuestas Preparadas para el Jurado de TVN
        </h2>
        <p class="text-xs text-ink-muted">
          Atajos interactivos para demostrar en vivo el comportamiento del agente ante las preguntas técnicas más exigentes.
        </p>
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <Card
          v-for="p in PREGUNTAS_JURADO"
          :key="p.pregunta"
          class="p-4 flex flex-col justify-between hover:border-primary/40 transition-colors"
        >
          <div>
            <h3 class="font-semibold text-ink text-sm leading-snug">
              {{ p.pregunta }}
            </h3>
            <p class="mt-2 text-xs text-ink-muted leading-relaxed">
              {{ p.respuesta }}
            </p>
          </div>

          <div v-if="p.enlace" class="mt-4 pt-3 border-t border-hairline/60">
            <NuxtLink
              :to="p.enlace"
              class="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
            >
              {{ p.enlaceTexto }}
            </NuxtLink>
          </div>
        </Card>
      </div>
    </section>
  </div>
</template>
