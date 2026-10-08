<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { marked } from "marked";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import StateChip from "~/components/ui/StateChip.vue";
import { api } from "~/composables/useApi";

const mdViewMode = ref<"render" | "raw">("render");

const renderedMarkdown = computed(() => {
  const md = informe.value?.markdown;
  if (!md) return "<p class='text-ink-muted italic'>Generando reporte Markdown oficial...</p>";
  return marked.parse(md, { gfm: true, breaks: true });
});

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
  markdown?: string;
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
const activeTab = ref<"tarjetas" | "markdown">("tarjetas");
const copiadoMd = ref(false);

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

async function copiarMarkdown() {
  if (!informe.value?.markdown) return;
  try {
    await navigator.clipboard.writeText(informe.value.markdown);
    copiadoMd.value = true;
    setTimeout(() => {
      copiadoMd.value = false;
    }, 2000);
  } catch (e) {
    console.error("Error al copiar Markdown:", e);
  }
}

function descargarReporteMarkdown() {
  if (!informe.value?.markdown) return;
  const blob = new Blob([informe.value.markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `reporte_jurado_evidentia_${new Date().toISOString().slice(0, 10)}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
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
  <div class="mx-auto max-w-container px-4 py-6 space-y-8">
    <!-- Header Hero -->
    <div class="border-b border-hairline pb-8">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div class="space-y-1.5">
          <div class="flex items-center gap-2">
            <span class="text-label uppercase tracking-wider text-primary font-semibold">
              Corrida de Evaluación · Reto TVN Media §9
            </span>
            <StateChip tone="primary" variant="soft" class="text-caption">
              T01–T10 Live Suite
            </StateChip>
            <span class="text-caption text-ink-muted">· Reporte Markdown (.md)</span>
          </div>
          <h1 class="font-serif text-display-xl font-semibold tracking-tight text-ink">
            Centro de Verificación de Aceptación
          </h1>
          <p class="max-w-[72ch] text-body-sm leading-relaxed text-ink-muted">
            Ejecución auditable y en tiempo real de los 10 criterios de aceptación obligatorios del pliego
            editorial de TVN Media, ejecutados en un subproceso aislado sobre el motor analítico de EvidentIA.
          </p>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-col items-start gap-2 sm:items-end">
          <div class="flex flex-wrap items-center gap-2">
            <Button
              v-if="informe?.markdown"
              variant="secondary"
              class="h-9 px-3 text-body-sm font-medium"
              @click="copiarMarkdown"
            >
              <span v-if="copiadoMd" class="text-success flex items-center gap-1.5">
                <span>✓</span>
                <span>¡Copiado!</span>
              </span>
              <span v-else class="flex items-center gap-1.5">
                <span>📋</span>
                <span>Copiar MD</span>
              </span>
            </Button>

            <Button
              v-if="informe?.markdown"
              variant="secondary"
              class="h-9 px-3 text-body-sm font-medium"
              @click="descargarReporteMarkdown"
            >
              <span class="flex items-center gap-1.5">
                <span>⬇</span>
                <span>Descargar (.md)</span>
              </span>
            </Button>

            <Button
              :disabled="runningPruebas"
              class="h-9 px-4 text-body-sm font-semibold"
              @click="ejecutarPruebasEnVivo"
            >
              <span v-if="runningPruebas" class="flex items-center gap-2 font-mono tabular-nums">
                <span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-canvas border-t-transparent"></span>
                Corriendo… {{ timerSeconds }} s
              </span>
              <span v-else class="flex items-center gap-2">
                <span>▶</span>
                <span>Ejecutar Suite en Vivo</span>
              </span>
            </Button>
          </div>

          <span v-if="informe?.generado_utc && !runningPruebas" class="text-caption text-ink-muted font-mono tabular-nums">
            Última corrida: <b>{{ formatHoraPA(informe.generado_utc) }}</b> · Duración: <b>{{ informe.segundos }} s</b>
          </span>
        </div>
      </div>

      <!-- Execution Status Pill -->
      <div v-if="informe" class="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-md border border-hairline bg-surface-sunken p-3.5">
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2">
            <span
              class="flex h-2.5 w-2.5 rounded-full"
              :class="informe.verdes === informe.total ? 'bg-success' : 'bg-error'"
            ></span>
            <span class="text-body-sm font-semibold text-ink">
              Estado de Aceptación:
            </span>
            <span
              class="font-mono text-mono font-bold tabular-nums"
              :class="informe.verdes === informe.total ? 'text-success' : 'text-error'"
            >
              {{ informe.verdes }} / {{ informe.total }} Pruebas en Verde ({{ Math.round((informe.verdes / informe.total) * 100) }}%)
            </span>
          </div>

          <span class="text-ink-muted">·</span>
          <span class="font-mono text-caption text-ink-muted">
            {{ informe.comando }}
          </span>
        </div>

        <!-- View Switcher Tabs -->
        <div class="flex items-center rounded-sm bg-surface p-0.5 border border-hairline text-caption font-semibold">
          <button
            type="button"
            class="px-3 py-1 rounded-sm transition-colors cursor-pointer"
            :class="activeTab === 'tarjetas' ? 'bg-primary text-canvas shadow-xs' : 'text-ink-muted hover:text-ink'"
            @click="activeTab = 'tarjetas'"
          >
            Vista Interactiva (§9)
          </button>
          <button
            type="button"
            class="px-3 py-1 rounded-sm transition-colors cursor-pointer flex items-center gap-1.5"
            :class="activeTab === 'markdown' ? 'bg-primary text-canvas shadow-xs' : 'text-ink-muted hover:text-ink'"
            @click="activeTab = 'markdown'"
          >
            <span>Reporte Markdown</span>
            <span class="text-[10px] px-1 py-0.2 rounded bg-surface-sunken/40">.md</span>
          </button>
        </div>
      </div>

      <div v-if="errorMsg" class="mt-4 rounded-md border border-error/30 bg-error/10 p-4 text-body-sm text-error">
        {{ errorMsg }}
      </div>
    </div>

    <!-- TAB 1: INTERACTIVE CARDS -->
    <section v-if="activeTab === 'tarjetas'" class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="font-serif text-heading-md font-semibold text-ink">
          Pruebas de Aceptación Obligatorias (§9)
        </h2>
        <span class="text-caption text-ink-muted">
          Haz clic en cada tarjeta para inspeccionar aserciones y tiempos
        </span>
      </div>

      <div v-if="loadingPruebas && !informe" class="py-12 text-center text-body-sm text-ink-muted">
        Cargando estado de pruebas del jurado…
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="f in informe?.filas"
          :key="f.id"
          class="rounded-md border border-hairline bg-surface shadow-ev-1 overflow-hidden transition-colors"
          :class="f.estado === 'rojo' ? 'border-error/40 bg-error/5' : ''"
        >
          <!-- Card Header (Clickable) -->
          <button
            type="button"
            class="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-surface-sunken/40 cursor-pointer"
            @click="toggleAccordion(f.id)"
          >
            <div class="flex items-center gap-3">
              <StateChip
                :tone="f.estado === 'verde' ? 'success' : 'error'"
                variant="soft"
                :dot="true"
              >
                {{ f.estado === 'verde' ? 'Aprobada ✓' : 'Fallida ✕' }}
              </StateChip>

              <div>
                <div class="flex items-center gap-2">
                  <span class="font-mono text-mono font-bold uppercase tracking-wider text-primary">
                    {{ f.id }}
                  </span>
                  <span class="font-semibold text-ink text-body-sm sm:text-body-md">
                    {{ f.titulo }}
                  </span>
                </div>
                <p class="text-caption text-ink-muted mt-0.5 line-clamp-1">
                  {{ f.esperado }}
                </p>
              </div>
            </div>

            <div class="flex items-center gap-4">
              <span v-if="f.pruebas?.[0]?.segundos !== undefined" class="font-mono text-caption text-ink-muted tabular-nums hidden sm:inline">
                {{ f.pruebas[0].segundos }} s
              </span>
              <span class="text-caption text-ink-muted">
                {{ openAccordions[f.id] ? '▲' : '▼' }}
              </span>
            </div>
          </button>

          <!-- Card Content (Accordion Panel) -->
          <div v-if="openAccordions[f.id]" class="border-t border-hairline bg-surface-sunken p-4 space-y-3 text-body-sm">
            <div>
              <span class="text-label uppercase tracking-wider text-ink-muted">
                Criterio Oficial del Pliego TVN:
              </span>
              <p class="mt-1 bg-surface rounded-md border border-hairline p-3 text-body-sm text-ink leading-relaxed">
                {{ f.esperado }}
              </p>
            </div>

            <div>
              <span class="text-label uppercase tracking-wider text-ink-muted">
                Evidencia de Ejecución Pytest / Test Engine:
              </span>
              <div class="mt-1 space-y-2">
                <div
                  v-for="p in f.pruebas"
                  :key="p.prueba"
                  class="rounded-md border border-hairline bg-surface p-3 text-mono font-mono text-ink"
                >
                  <div class="flex items-center justify-between">
                    <span class="font-semibold text-ink">
                      {{ p.prueba }}
                    </span>
                    <span class="text-ink-muted tabular-nums">
                      {{ p.segundos }} s · {{ p.ok ? 'PASSED ✓' : 'FAILED ✕' }}
                    </span>
                  </div>
                  <p class="font-sans text-caption text-ink-muted mt-1">
                    {{ p.comprueba }}
                  </p>
                  <div v-if="p.mensaje" class="mt-2 rounded-sm border border-error/20 bg-error/10 p-2.5 text-error text-caption">
                    {{ p.mensaje }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 2: MARKDOWN REPORT VIEW -->
    <section v-else-if="activeTab === 'markdown'" class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="font-serif text-heading-md font-semibold text-ink">
            Reporte Oficial en Formato Markdown (.md)
          </h2>
          <p class="text-caption text-ink-muted">
            Documento estructurado en formato Markdown estándar GitHub/CommonMark, sin dependencias de XML.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <Button
            variant="secondary"
            class="h-8 px-3 text-caption font-semibold"
            @click="copiarMarkdown"
          >
            {{ copiadoMd ? '✓ Copiado' : 'Copiar Texto' }}
          </Button>
          <Button
            class="h-8 px-3 text-caption font-semibold"
            @click="descargarReporteMarkdown"
          >
            Descargar archivo .md
          </Button>
        </div>
      </div>

      <div class="rounded-md border border-hairline bg-surface shadow-ev-1 overflow-hidden">
        <div class="border-b border-hairline bg-surface-sunken px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-caption font-mono text-ink-muted">
          <div class="flex items-center gap-2">
            <span class="inline-block h-2 w-2 rounded-full bg-success"></span>
            <span class="font-semibold text-ink">reporte_jurado_evidentia.md</span>
          </div>

          <div class="flex items-center gap-3">
            <span class="text-caption font-mono hidden sm:inline">{{ (informe?.markdown?.length || 0).toLocaleString() }} caracteres</span>

            <!-- Single view toggle (Explicitly NO split view) -->
            <div class="inline-flex rounded-md border border-hairline bg-surface p-0.5 text-caption font-sans">
              <button
                type="button"
                class="px-2.5 py-1 rounded text-caption font-medium transition-colors"
                :class="mdViewMode === 'render' ? 'bg-primary text-white shadow-xs font-semibold' : 'text-ink-muted hover:text-ink'"
                @click="mdViewMode = 'render'"
              >
                Vista Renderizada
              </button>
              <button
                type="button"
                class="px-2.5 py-1 rounded text-caption font-medium transition-colors"
                :class="mdViewMode === 'raw' ? 'bg-primary text-white shadow-xs font-semibold' : 'text-ink-muted hover:text-ink'"
                @click="mdViewMode = 'raw'"
              >
                Código Markdown (.md)
              </button>
            </div>
          </div>
        </div>

        <!-- Vista Renderizada (Default, single view a ancho completo) -->
        <div
          v-if="mdViewMode === 'render'"
          class="p-6 md:p-8 overflow-y-auto max-h-[750px] bg-surface"
        >
          <div
            class="evidentia-markdown-content max-w-none text-ink leading-relaxed"
            v-html="renderedMarkdown"
          ></div>
        </div>

        <!-- Vista Código Markdown Crudo -->
        <pre
          v-else
          class="p-6 font-mono text-mono text-ink bg-surface overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-[750px]"
        >{{ informe?.markdown || "Generando reporte Markdown..." }}</pre>
      </div>
    </section>


    <!-- Agente EvidentIA vs. Baseline BM25 -->
    <section class="space-y-4 pt-4 border-t border-hairline">
      <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="font-serif text-heading-md font-semibold text-ink">
            Evaluación Comparativa: Agente EvidentIA frente a Baseline BM25
          </h2>
          <p class="text-caption text-ink-muted">
            Benchmark de 40 consultas de desarrollo (§7 y §8): 20 sustentadas, 7 sin respuesta, 7 contradicciones, 6 adversariales.
          </p>
        </div>
        <span v-if="metricas?.modelo" class="font-mono text-mono text-primary bg-primary-soft px-2.5 py-1 rounded-sm border border-primary/20">
          {{ metricas.modelo }}
        </span>
      </div>

      <div class="overflow-x-auto rounded-md border border-hairline bg-surface shadow-ev-1">
        <table class="w-full text-left text-body-sm">
          <thead class="border-b border-hairline bg-surface-sunken text-label uppercase tracking-wider text-ink-muted">
            <tr>
              <th class="py-3 px-4 font-semibold">Métrica de Evaluación</th>
              <th class="py-3 px-4 font-semibold">Meta Reto</th>
              <th class="py-3 px-4 font-semibold">Baseline BM25</th>
              <th class="py-3 px-4 font-semibold">EvidentIA (Llama-3.3-70B)</th>
              <th class="py-3 px-4 font-semibold text-right">Cumplimiento</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-hairline">
            <tr v-for="m in metricas?.tabla" :key="m.metrica" class="hover:bg-surface-sunken/30 transition-colors">
              <td class="py-3 px-4 font-medium text-ink">
                {{ m.metrica }}
              </td>
              <td class="py-3 px-4 font-mono text-mono text-ink-muted tabular-nums">
                {{ m.meta }}
              </td>
              <td class="py-3 px-4 font-mono text-mono text-ink-muted tabular-nums">
                {{ m.baseline_bm25 }}
              </td>
              <td class="py-3 px-4 font-mono text-mono font-semibold text-success tabular-nums">
                {{ m.agente_evidentia }}
              </td>
              <td class="py-3 px-4 text-right">
                <StateChip tone="success" variant="soft">
                  Supera Meta ✓
                </StateChip>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Preguntas Frecuentes del Jurado -->
    <section class="space-y-4 pt-4 border-t border-hairline">
      <div>
        <h2 class="font-serif text-heading-md font-semibold text-ink">
          Respuestas Preparadas para el Jurado de TVN
        </h2>
        <p class="text-caption text-ink-muted">
          Atajos interactivos para demostrar en vivo el comportamiento del agente ante las preguntas técnicas más exigentes.
        </p>
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <div
          v-for="p in PREGUNTAS_JURADO"
          :key="p.pregunta"
          class="rounded-md border border-hairline bg-surface p-5 shadow-ev-1 flex flex-col justify-between hover:border-primary/50 transition-colors"
        >
          <div>
            <h3 class="font-serif text-heading-md font-semibold text-ink leading-snug">
              {{ p.pregunta }}
            </h3>
            <p class="mt-2 text-body-sm text-ink-muted leading-relaxed">
              {{ p.respuesta }}
            </p>
          </div>

          <div v-if="p.enlace" class="mt-4 pt-3 border-t border-hairline">
            <NuxtLink
              :to="p.enlace"
              class="text-caption font-semibold text-primary hover:text-primary-deep flex items-center gap-1 transition-colors"
            >
              {{ p.enlaceTexto }}
            </NuxtLink>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.evidentia-markdown-content :deep(h1) {
  font-family: var(--font-serif, serif);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-ink, #0f172a);
  margin-top: 1rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
}

.evidentia-markdown-content :deep(h2) {
  font-family: var(--font-serif, serif);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-ink, #0f172a);
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--color-hairline, #f1f5f9);
}

.evidentia-markdown-content :deep(h3) {
  font-family: var(--font-serif, serif);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-ink, #0f172a);
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}

.evidentia-markdown-content :deep(h4) {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-ink, #0f172a);
  margin-top: 1rem;
  margin-bottom: 0.25rem;
}

.evidentia-markdown-content :deep(p) {
  margin-bottom: 0.75rem;
  line-height: 1.6;
  font-size: 0.875rem;
  color: var(--color-ink, #1e293b);
}

.evidentia-markdown-content :deep(strong) {
  font-weight: 600;
  color: var(--color-ink, #0f172a);
}

.evidentia-markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  margin-bottom: 1.25rem;
  font-size: 0.8125rem;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 0.375rem;
  overflow: hidden;
}

.evidentia-markdown-content :deep(th) {
  background-color: var(--color-surface-sunken, #f8fafc);
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--color-border, #e2e8f0);
  font-weight: 600;
  text-align: left;
  color: var(--color-ink, #0f172a);
}

.evidentia-markdown-content :deep(td) {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border, #e2e8f0);
  color: var(--color-ink, #1e293b);
}

.evidentia-markdown-content :deep(tr:nth-child(even)) {
  background-color: rgba(248, 250, 252, 0.5);
}

.evidentia-markdown-content :deep(ul) {
  list-style-type: disc;
  padding-left: 1.5rem;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
}

.evidentia-markdown-content :deep(ol) {
  list-style-type: decimal;
  padding-left: 1.5rem;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
}

.evidentia-markdown-content :deep(li) {
  margin-bottom: 0.25rem;
  line-height: 1.5;
}

.evidentia-markdown-content :deep(code) {
  font-family: var(--font-mono, monospace);
  font-size: 0.8125rem;
  background-color: var(--color-surface-sunken, #f1f5f9);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  border: 1px solid var(--color-border, #e2e8f0);
  color: var(--color-primary, #0284c7);
}

.evidentia-markdown-content :deep(pre) {
  background-color: var(--color-surface-sunken, #f8fafc);
  border: 1px solid var(--color-border, #e2e8f0);
  padding: 0.75rem 1rem;
  border-radius: 0.375rem;
  overflow-x: auto;
  margin: 0.75rem 0;
  font-family: var(--font-mono, monospace);
  font-size: 0.8125rem;
}

.evidentia-markdown-content :deep(pre code) {
  background: transparent;
  padding: 0;
  border: none;
  color: inherit;
}

.evidentia-markdown-content :deep(blockquote) {
  border-left: 4px solid var(--color-primary, #0284c7);
  padding-left: 1rem;
  margin: 0.75rem 0;
  font-style: italic;
  color: var(--color-ink-muted, #64748b);
}

.evidentia-markdown-content :deep(hr) {
  border: 0;
  border-top: 1px solid var(--color-border, #e2e8f0);
  margin: 1.5rem 0;
}
</style>

