<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import {
  RefreshCw,
  Download,
  Upload,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  X,
} from "lucide-vue-next";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import StateChip from "~/components/ui/StateChip.vue";
import Pagination from "~/components/ui/Pagination.vue";
import { api } from "~/composables/useApi";
import { usePagination } from "~/composables/usePagination";

interface AutoScheduleStatus {
  enabled: boolean;
  interval_minutes: number;
  is_running: boolean;
  last_status: string;
  last_error: string | null;
  last_run: string | null;
  next_run: string | null;
  items_ingested_last_run: number;
}

const report = ref<Record<string, unknown> | null>(null);
const runningManual = ref(false);
const runningLive = ref(false);
const useSeed = ref(true);
const error = ref("");
const liveSuccessMsg = ref("");

// Auto-ingest scheduler state
const scheduleStatus = ref<AutoScheduleStatus>({
  enabled: false,
  interval_minutes: 15,
  is_running: false,
  last_status: "idle",
  last_error: null,
  last_run: null,
  next_run: null,
  items_ingested_last_run: 0,
});
const savingSchedule = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;

async function loadReport() {
  try {
    report.value = await api("ingest/quality-report");
  } catch {
    report.value = null;
  }
}

async function loadScheduleStatus() {
  try {
    const data = await api<AutoScheduleStatus>("ingest/auto-schedule");
    scheduleStatus.value = data;
  } catch (e) {
    console.error("Error loading auto-schedule status:", e);
  }
}

async function toggleAutoSchedule(newVal?: boolean) {
  savingSchedule.value = true;
  const targetEnabled = newVal !== undefined ? newVal : !scheduleStatus.value.enabled;
  try {
    const res = await api<AutoScheduleStatus>("ingest/auto-schedule", {
      method: "POST",
      body: {
        enabled: targetEnabled,
        interval_minutes: scheduleStatus.value.interval_minutes,
      },
    });
    scheduleStatus.value = res;
  } catch (e) {
    error.value = "No se pudo actualizar la configuración del programador.";
  } finally {
    savingSchedule.value = false;
  }
}

async function changeInterval(e: Event) {
  const target = e.target as HTMLSelectElement;
  const mins = parseInt(target.value, 10);
  savingSchedule.value = true;
  try {
    const res = await api<AutoScheduleStatus>("ingest/auto-schedule", {
      method: "POST",
      body: {
        enabled: scheduleStatus.value.enabled,
        interval_minutes: mins,
      },
    });
    scheduleStatus.value = res;
  } catch (e) {
    error.value = "No se pudo actualizar el intervalo.";
  } finally {
    savingSchedule.value = false;
  }
}

async function runLiveNow() {
  runningLive.value = true;
  error.value = "";
  liveSuccessMsg.value = "";
  try {
    const res = await api<{ status: string; report?: Record<string, unknown>; error?: string }>(
      "ingest/live-now",
      { method: "POST" }
    );
    if (res.status === "success") {
      liveSuccessMsg.value = "Noticias en vivo sincronizadas exitosamente.";
      if (res.report) report.value = res.report;
      else await loadReport();
      await loadScheduleStatus();
    } else {
      error.value = res.error || "Error al sincronizar noticias en vivo.";
    }
  } catch (e) {
    error.value = "Falló la ingesta en vivo. Verifica conectividad a los feeds RSS de TVN y Panamá.";
  } finally {
    runningLive.value = false;
  }
}

async function runManualIngest() {
  runningManual.value = true;
  error.value = "";
  liveSuccessMsg.value = "";
  try {
    const res = await api<{ status: string; report?: Record<string, unknown> }>("ingest/run", {
      method: "POST",
      query: { sync: "true", use_seed: String(useSeed.value) },
    });
    if (res.report) report.value = res.report;
    else await loadReport();
  } catch (e) {
    error.value = "Falló la ingesta manual. Revisa los logs del backend.";
  } finally {
    runningManual.value = false;
  }
}

function formatDate(isoStr: string | null) {
  if (!isoStr) return "Nunca";
  try {
    const d = new Date(isoStr);
    return (
      d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) +
      " (" +
      d.toLocaleDateString() +
      ")"
    );
  } catch {
    return isoStr;
  }
}

interface UploadRecord {
  upload_id: string;
  timestamp: string;
  filename: string;
  family: string;
  status: "completed" | "completed_with_warnings" | "failed";
  total_rows: number;
  valid_rows: number;
  dropped_rows: number;
  duplicates_found: boolean;
  duplicate_count: number;
  duplicate_details: { row?: number; reason: string; [key: string]: any }[];
  warnings: string[];
}

const uploadHistory = ref<UploadRecord[]>([]);
const {
  page: historyPage,
  pageCount: historyPageCount,
  total: historyTotal,
  rangeStart: historyRangeStart,
  rangeEnd: historyRangeEnd,
  paged: pagedHistory,
} = usePagination(uploadHistory, { pageSize: 10 });
const uploading = ref<Record<string, boolean>>({});
const uploadResultMsg = ref<Record<string, string>>({});
const uploadErrorMsg = ref<Record<string, string>>({});
const selectedDuplicates = ref<UploadRecord | null>(null);

async function loadUploadHistory() {
  try {
    uploadHistory.value = await api<UploadRecord[]>("ingest/uploads");
  } catch (e) {
    console.error("Error cargando historial de cargas:", e);
  }
}

async function uploadFamilyFile(event: Event, familyKey: string) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  uploading.value[familyKey] = true;
  uploadResultMsg.value[familyKey] = "";
  uploadErrorMsg.value[familyKey] = "";

  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("family", familyKey);

    const record = await api<UploadRecord>(`ingest/upload?family=${familyKey}`, {
      method: "POST",
      body: formData,
    });

    uploadResultMsg.value[familyKey] = `${record.valid_rows} filas válidas procesadas (${record.upload_id})${
      record.duplicates_found ? ` · ${record.duplicate_count} duplicados detectados` : ""
    }`;
    await Promise.all([loadUploadHistory(), loadReport()]);
  } catch (err: any) {
    uploadErrorMsg.value[familyKey] =
      err?.data?.detail || err?.message || "Error al procesar el archivo.";
  } finally {
    uploading.value[familyKey] = false;
    input.value = "";
  }
}

function downloadTemplate(family: string) {
  const url = `/api/ingest/templates/${family}`;
  const a = document.createElement("a");
  a.href = url;
  a.download = `plantilla_${family}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

onMounted(() => {
  loadReport();
  loadScheduleStatus();
  loadUploadHistory();
  pollTimer = setInterval(() => {
    loadScheduleStatus();
  }, 10000);
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header (Editorial Serif + StateChips) -->
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 border-b border-hairline pb-5">
      <div class="space-y-1">
        <h1 class="font-serif text-display-xl text-ink font-semibold tracking-tight">
          Ingesta y Calidad de Datos
        </h1>
        <p class="text-body-sm text-ink-muted max-w-[72ch]">
          Monitoreo continuo de fuentes primarias, escaneo periódico de feeds RSS, validación determinista por esquemas y auditoría de duplicados.
        </p>
      </div>

      <!-- Corpus and Pipeline Status Chips -->
      <div class="flex flex-wrap items-center gap-2">
        <StateChip
          :tone="report?.source === 'live' ? 'success' : 'warning'"
          dot
        >
          {{ report?.source === 'live' ? 'Corpus: Noticias en Vivo (TVN RSS)' : 'Corpus: Snapshot Local (Demo T10)' }}
        </StateChip>
        <StateChip
          :tone="scheduleStatus.enabled ? 'success' : 'neutral'"
          dot
        >
          {{ scheduleStatus.enabled ? 'Autoprogramador Activo' : 'Autoprogramador Pausado' }}
        </StateChip>
      </div>
    </div>

    <!-- Alert Notifications (System Tone Colors + Crisp SVG Icons) -->
    <div
      v-if="liveSuccessMsg"
      class="flex items-center justify-between rounded-md border border-success/30 bg-success/10 px-4 py-3 text-body-sm text-success"
    >
      <div class="flex items-center gap-2">
        <CheckCircle2 class="h-4 w-4 shrink-0 text-success" />
        <span>{{ liveSuccessMsg }}</span>
      </div>
      <button
        type="button"
        class="text-caption font-semibold text-success hover:underline ml-4 cursor-pointer"
        @click="liveSuccessMsg = ''"
      >
        Cerrar
      </button>
    </div>

    <div
      v-if="error"
      class="flex items-center justify-between rounded-md border border-error/30 bg-error/10 px-4 py-3 text-body-sm text-error"
    >
      <div class="flex items-center gap-2">
        <AlertCircle class="h-4 w-4 shrink-0 text-error" />
        <span>{{ error }}</span>
      </div>
      <button
        type="button"
        class="text-caption font-semibold text-error hover:underline ml-4 cursor-pointer"
        @click="error = ''"
      >
        Cerrar
      </button>
    </div>

    <!-- Card 1: Auto-Ingest Scheduler & Pitch Mode -->
    <Card>
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center gap-2.5">
            <span
              class="h-2.5 w-2.5 rounded-full"
              :class="scheduleStatus.enabled ? 'bg-success animate-pulse' : 'bg-ink-muted'"
            />
            <h2 class="font-serif text-heading-md text-ink">
              Monitoreo Automático en Segundo Plano (Pitch Mode)
            </h2>
          </div>
          <StateChip :tone="scheduleStatus.enabled ? 'success' : 'neutral'">
            {{ scheduleStatus.enabled ? 'ACTIVO' : 'PAUSADO' }}
          </StateChip>
        </div>
      </template>

      <div class="space-y-5">
        <p class="text-body-sm text-ink-muted max-w-[76ch]">
          Activa el copiloto para escanear periódicamente los feeds RSS de TVN-2 y medios de Panamá, extrayendo entidades, actualizando el grafo de conocimiento interactivo y recalculando el ranking de atención en tiempo real.
        </p>

        <!-- Scheduler Configuration Settings (2 Columns) -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <!-- Col 1: Toggle Feature Flag -->
          <div class="flex items-center justify-between rounded-md border border-hairline bg-surface-sunken p-3.5">
            <div class="space-y-0.5 pr-3">
              <div class="text-body-sm font-semibold text-ink">Monitoreo Automático</div>
              <div class="text-caption text-ink-muted">Copiloto en segundo plano</div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                type="checkbox"
                class="sr-only peer"
                :checked="scheduleStatus.enabled"
                :disabled="savingSchedule"
                @change="toggleAutoSchedule(!scheduleStatus.enabled)"
              />
              <div class="w-11 h-6 bg-hairline peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-hairline after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>

          <!-- Col 2: Interval Selector -->
          <div class="flex items-center justify-between rounded-md border border-hairline bg-surface-sunken p-3.5">
            <div class="space-y-0.5 pr-3">
              <div class="text-body-sm font-semibold text-ink">Frecuencia de Escaneo</div>
              <div class="text-caption text-ink-muted">Intervalo en minutos</div>
            </div>
            <select
              :value="scheduleStatus.interval_minutes"
              :disabled="savingSchedule"
              class="h-9 rounded-sm border border-hairline bg-surface px-3 py-1 text-body-sm text-ink focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/25 cursor-pointer shrink-0"
              @change="changeInterval"
            >
              <option :value="5">Cada 5 min</option>
              <option :value="15">Cada 15 min</option>
              <option :value="30">Cada 30 min</option>
              <option :value="60">Cada 60 min</option>
            </select>
          </div>
        </div>

        <!-- Dedicated Live Sync Action Panel (Wrap-safe, full-width) -->
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3.5 rounded-md border border-hairline bg-surface-sunken p-4">
          <div class="space-y-0.5">
            <div class="text-body-sm font-semibold text-ink">Sincronización en Vivo</div>
            <p class="text-caption text-ink-muted">
              Forzar escaneo inmediato de feeds RSS de TVN-2 y medios de Panamá sin esperar el siguiente ciclo automático.
            </p>
          </div>
          <Button
            variant="default"
            class="h-9 px-4 text-xs font-semibold shrink-0 gap-2 self-start sm:self-auto cursor-pointer whitespace-nowrap"
            :disabled="runningLive || scheduleStatus.is_running"
            @click="runLiveNow"
          >
            <RefreshCw
              class="h-3.5 w-3.5 shrink-0"
              :class="{ 'animate-spin': runningLive || scheduleStatus.is_running }"
            />
            <span>{{ (runningLive || scheduleStatus.is_running) ? 'Sincronizando noticias…' : 'Sincronizar ahora' }}</span>
          </Button>
        </div>

        <!-- Schedule Diagnostics Bar -->
        <div class="rounded-md border border-hairline bg-surface-sunken p-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-caption text-ink-muted">
          <div>
            Última ejecución: <span class="font-mono tabular-nums text-ink font-medium">{{ formatDate(scheduleStatus.last_run) }}</span>
          </div>
          <div v-if="scheduleStatus.enabled">
            Próximo ciclo: <span class="font-mono tabular-nums text-ink font-medium">{{ formatDate(scheduleStatus.next_run) }}</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span>Estado:</span>
            <span
              class="font-mono font-medium capitalize"
              :class="scheduleStatus.is_running ? 'text-warning' : 'text-success'"
            >
              {{ scheduleStatus.is_running ? 'Ejecutando…' : scheduleStatus.last_status }}
            </span>
          </div>
          <div v-if="scheduleStatus.items_ingested_last_run > 0">
            Titulares procesados: <span class="font-mono tabular-nums text-ink font-semibold">{{ scheduleStatus.items_ingested_last_run }}</span>
          </div>
        </div>
      </div>
    </Card>

    <!-- Card 2: Manual Seed / Offline Mode (T10 Requirement - preserves E2E test locator) -->
    <Card>
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="font-serif text-heading-md text-ink">
            Ejecutar carga / Modo Contingencia Offline (T10)
          </h2>
          <span class="font-mono text-caption text-ink-muted bg-surface-sunken px-2 py-0.5 rounded-sm border border-hairline">
            Snapshot Local
          </span>
        </div>
      </template>

      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <label class="flex items-center gap-3 text-body-sm text-ink cursor-pointer select-none">
          <input
            v-model="useSeed"
            type="checkbox"
            class="h-4 w-4 rounded border-hairline text-primary focus:ring-primary"
          />
          <span>Usar snapshot local congelado (Simulación demo sin internet / offline T10)</span>
        </label>

        <Button
          variant="outline"
          class="h-9 px-4 text-xs font-semibold cursor-pointer"
          :disabled="runningManual || runningLive"
          @click="runManualIngest"
        >
          {{ runningManual ? "Cargando…" : "Ejecutar ingesta manual" }}
        </Button>
      </div>
    </Card>

    <!-- Card 3: Schema File Upload with Downloadable Templates -->
    <Card>
      <template #header>
        <div class="space-y-1">
          <h2 class="font-serif text-heading-md text-ink">
            Carga de Archivos por Esquema (Upload &amp; Validación)
          </h2>
          <p class="text-body-sm text-ink-muted">
            Carga manual de datos con validación determinista, detección automática de duplicados y plantillas descargables oficiales.
          </p>
        </div>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- 1. Noticias CSV -->
        <div class="rounded-md border border-hairline bg-surface p-4 flex flex-col justify-between space-y-4 hover:border-ink-muted/30 transition-colors">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-body-sm text-ink">
                Noticias de Prensa
              </span>
              <span class="font-mono text-caption text-ink-muted bg-surface-sunken px-2 py-0.5 rounded-sm border border-hairline">
                noticias.csv
              </span>
            </div>
            <p class="text-caption text-ink-muted">
              Titulares de medios locales y GDELT. Detección automática de duplicados por URL y similitud léxica Jaccard &gt; 0.85.
            </p>
            <div class="font-mono text-[11px] text-ink-muted bg-surface-sunken p-2.5 rounded-sm border border-hairline break-all select-all">
              id_noticia, titulo, url, medio, idioma, fecha_publicacion, tema, origen, alcance_texto
            </div>
          </div>

          <div class="space-y-2 pt-3 border-t border-hairline">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <Button
                variant="ghost"
                class="h-8 px-2.5 text-caption font-semibold text-primary hover:text-primary-deep gap-1.5 cursor-pointer"
                @click="downloadTemplate('noticias')"
              >
                <Download class="h-3.5 w-3.5 shrink-0" />
                <span>Descargar plantilla</span>
              </Button>
              <label class="cursor-pointer">
                <input
                  type="file"
                  accept=".csv"
                  class="sr-only"
                  :disabled="uploading['noticias']"
                  @change="uploadFamilyFile($event, 'noticias')"
                />
                <span class="inline-flex items-center justify-center gap-1.5 rounded-md text-caption font-semibold h-8 px-3 border border-hairline bg-transparent hover:bg-surface-sunken text-ink transition-colors cursor-pointer">
                  <Upload class="h-3.5 w-3.5 shrink-0 text-ink-muted" />
                  <span>{{ uploading['noticias'] ? 'Validando…' : 'Subir archivo CSV' }}</span>
                </span>
              </label>
            </div>
            <p v-if="uploadResultMsg['noticias']" class="text-caption font-mono text-success font-medium">{{ uploadResultMsg['noticias'] }}</p>
            <p v-if="uploadErrorMsg['noticias']" class="text-caption font-mono text-error font-medium">{{ uploadErrorMsg['noticias'] }}</p>
          </div>
        </div>

        <!-- 2. Indicadores CSV -->
        <div class="rounded-md border border-hairline bg-surface p-4 flex flex-col justify-between space-y-4 hover:border-ink-muted/30 transition-colors">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-body-sm text-ink">
                Indicadores Banco Mundial
              </span>
              <span class="font-mono text-caption text-ink-muted bg-surface-sunken px-2 py-0.5 rounded-sm border border-hairline">
                indicadores.csv
              </span>
            </div>
            <p class="text-caption text-ink-muted">
              Series macroeconómicas oficiales. Clave de unicidad: (pais_iso3, indicador_id, anio).
            </p>
            <div class="font-mono text-[11px] text-ink-muted bg-surface-sunken p-2.5 rounded-sm border border-hairline break-all select-all">
              pais_iso3, indicador_id, anio, valor, unidad, fuente_url, licencia, fecha_extraccion
            </div>
          </div>

          <div class="space-y-2 pt-3 border-t border-hairline">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <Button
                variant="ghost"
                class="h-8 px-2.5 text-caption font-semibold text-primary hover:text-primary-deep gap-1.5 cursor-pointer"
                @click="downloadTemplate('indicadores')"
              >
                <Download class="h-3.5 w-3.5 shrink-0" />
                <span>Descargar plantilla</span>
              </Button>
              <label class="cursor-pointer">
                <input
                  type="file"
                  accept=".csv"
                  class="sr-only"
                  :disabled="uploading['indicadores']"
                  @change="uploadFamilyFile($event, 'indicadores')"
                />
                <span class="inline-flex items-center justify-center gap-1.5 rounded-md text-caption font-semibold h-8 px-3 border border-hairline bg-transparent hover:bg-surface-sunken text-ink transition-colors cursor-pointer">
                  <Upload class="h-3.5 w-3.5 shrink-0 text-ink-muted" />
                  <span>{{ uploading['indicadores'] ? 'Validando…' : 'Subir archivo CSV' }}</span>
                </span>
              </label>
            </div>
            <p v-if="uploadResultMsg['indicadores']" class="text-caption font-mono text-success font-medium">{{ uploadResultMsg['indicadores'] }}</p>
            <p v-if="uploadErrorMsg['indicadores']" class="text-caption font-mono text-error font-medium">{{ uploadErrorMsg['indicadores'] }}</p>
          </div>
        </div>

        <!-- 3. Eventos GeoJSON -->
        <div class="rounded-md border border-hairline bg-surface p-4 flex flex-col justify-between space-y-4 hover:border-ink-muted/30 transition-colors">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-body-sm text-ink">
                Eventos Geofísicos USGS
              </span>
              <span class="font-mono text-caption text-ink-muted bg-surface-sunken px-2 py-0.5 rounded-sm border border-hairline">
                eventos.geojson
              </span>
            </div>
            <p class="text-caption text-ink-muted">
              Sismicidad regional en formato FeatureCollection. Clave de unicidad: ID de evento sísmico USGS.
            </p>
            <div class="font-mono text-[11px] text-ink-muted bg-surface-sunken p-2.5 rounded-sm border border-hairline break-all select-all">
              FeatureCollection -&gt; features: [id, geometry.coordinates, properties: mag, place, time]
            </div>
          </div>

          <div class="space-y-2 pt-3 border-t border-hairline">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <Button
                variant="ghost"
                class="h-8 px-2.5 text-caption font-semibold text-primary hover:text-primary-deep gap-1.5 cursor-pointer"
                @click="downloadTemplate('eventos')"
              >
                <Download class="h-3.5 w-3.5 shrink-0" />
                <span>Descargar plantilla</span>
              </Button>
              <label class="cursor-pointer">
                <input
                  type="file"
                  accept=".geojson,.json"
                  class="sr-only"
                  :disabled="uploading['eventos']"
                  @change="uploadFamilyFile($event, 'eventos')"
                />
                <span class="inline-flex items-center justify-center gap-1.5 rounded-md text-caption font-semibold h-8 px-3 border border-hairline bg-transparent hover:bg-surface-sunken text-ink transition-colors cursor-pointer">
                  <Upload class="h-3.5 w-3.5 shrink-0 text-ink-muted" />
                  <span>{{ uploading['eventos'] ? 'Validando…' : 'Subir GeoJSON' }}</span>
                </span>
              </label>
            </div>
            <p v-if="uploadResultMsg['eventos']" class="text-caption font-mono text-success font-medium">{{ uploadResultMsg['eventos'] }}</p>
            <p v-if="uploadErrorMsg['eventos']" class="text-caption font-mono text-error font-medium">{{ uploadErrorMsg['eventos'] }}</p>
          </div>
        </div>

        <!-- 4. Fichas JSONL -->
        <div class="rounded-md border border-hairline bg-surface p-4 flex flex-col justify-between space-y-4 hover:border-ink-muted/30 transition-colors">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-body-sm text-ink">
                Fichas Editoriales
              </span>
              <span class="font-mono text-caption text-ink-muted bg-surface-sunken px-2 py-0.5 rounded-sm border border-hairline">
                fichas.jsonl
              </span>
            </div>
            <p class="text-caption text-ink-muted">
              Casos investigativos con fuentes vinculadas, afirmaciones y puntajes. Clave de unicidad: id_caso.
            </p>
            <div class="font-mono text-[11px] text-ink-muted bg-surface-sunken p-2.5 rounded-sm border border-hairline break-all select-all">
              {"id_caso": "...", "modalidad": "tvn", "ids_fuente": [...], "puntaje": ...}
            </div>
          </div>

          <div class="space-y-2 pt-3 border-t border-hairline">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <Button
                variant="ghost"
                class="h-8 px-2.5 text-caption font-semibold text-primary hover:text-primary-deep gap-1.5 cursor-pointer"
                @click="downloadTemplate('fichas')"
              >
                <Download class="h-3.5 w-3.5 shrink-0" />
                <span>Descargar plantilla</span>
              </Button>
              <label class="cursor-pointer">
                <input
                  type="file"
                  accept=".jsonl,.json"
                  class="sr-only"
                  :disabled="uploading['fichas']"
                  @change="uploadFamilyFile($event, 'fichas')"
                />
                <span class="inline-flex items-center justify-center gap-1.5 rounded-md text-caption font-semibold h-8 px-3 border border-hairline bg-transparent hover:bg-surface-sunken text-ink transition-colors cursor-pointer">
                  <Upload class="h-3.5 w-3.5 shrink-0 text-ink-muted" />
                  <span>{{ uploading['fichas'] ? 'Validando…' : 'Subir JSONL' }}</span>
                </span>
              </label>
            </div>
            <p v-if="uploadResultMsg['fichas']" class="text-caption font-mono text-success font-medium">{{ uploadResultMsg['fichas'] }}</p>
            <p v-if="uploadErrorMsg['fichas']" class="text-caption font-mono text-error font-medium">{{ uploadErrorMsg['fichas'] }}</p>
          </div>
        </div>
      </div>
    </Card>

    <!-- Card 4: Upload History & Duplicate Audit Table -->
    <Card v-if="uploadHistory.length > 0">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <h2 class="font-serif text-heading-md text-ink">
              Historial de Cargas y Trazabilidad de Duplicados
            </h2>
            <span class="font-mono text-caption text-ink-muted bg-surface-sunken px-2 py-0.5 rounded-sm border border-hairline">
              {{ uploadHistory.length }} registradas
            </span>
          </div>
        </div>
      </template>

      <div class="overflow-x-auto -mx-4 md:-mx-6">
        <table class="w-full text-left text-body-sm">
          <thead class="border-b border-hairline bg-surface-sunken text-label uppercase tracking-wider text-ink-muted">
            <tr>
              <th class="py-2.5 px-4 font-semibold">Upload ID</th>
              <th class="py-2.5 px-4 font-semibold">Fecha / Hora</th>
              <th class="py-2.5 px-4 font-semibold">Archivo / Familia</th>
              <th class="py-2.5 px-4 font-semibold">Filas Procesadas</th>
              <th class="py-2.5 px-4 font-semibold">Detección de Duplicados</th>
              <th class="py-2.5 px-4 text-right font-semibold">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-hairline">
            <tr
              v-for="item in pagedHistory"
              :key="item.upload_id"
              class="hover:bg-surface-sunken/60 transition-colors"
            >
              <td class="py-3 px-4 font-mono text-caption font-medium text-primary">
                {{ item.upload_id }}
              </td>
              <td class="py-3 px-4 font-mono text-caption text-ink-muted tabular-nums whitespace-nowrap">
                {{ formatDate(item.timestamp) }}
              </td>
              <td class="py-3 px-4">
                <span class="font-medium text-ink block">{{ item.filename }}</span>
                <span class="font-mono text-[11px] text-ink-muted">{{ item.family }}</span>
              </td>
              <td class="py-3 px-4 whitespace-nowrap font-mono tabular-nums text-caption">
                <span class="text-success font-semibold">{{ item.valid_rows }} válidas</span>
                <span v-if="item.dropped_rows > 0" class="text-ink-muted"> / {{ item.dropped_rows }} descartadas</span>
                <span class="text-[11px] text-ink-muted block">Total: {{ item.total_rows }}</span>
              </td>
              <td class="py-3 px-4">
                <div v-if="item.duplicates_found" class="flex items-center gap-2">
                  <StateChip tone="warning" dot>
                    {{ item.duplicate_count }} duplicados
                  </StateChip>
                  <button
                    type="button"
                    class="text-caption font-medium text-primary hover:underline cursor-pointer"
                    @click="selectedDuplicates = item"
                  >
                    Ver detalle
                  </button>
                </div>
                <StateChip v-else tone="success" dot>
                  Sin duplicados
                </StateChip>
              </td>
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <StateChip
                  :tone="item.status === 'completed' ? 'success' : item.status === 'completed_with_warnings' ? 'warning' : 'error'"
                >
                  {{ item.status === 'completed' ? 'Completado' : item.status === 'completed_with_warnings' ? 'Advertencias' : 'Error' }}
                </StateChip>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pagination
        v-model:page="historyPage"
        :page-count="historyPageCount"
        :total="historyTotal"
        :range-start="historyRangeStart"
        :range-end="historyRangeEnd"
        class="mt-3"
      />
    </Card>

    <!-- Modal de Detalle de Duplicados (Elevación Nivel 3) -->
    <div
      v-if="selectedDuplicates"
      class="fixed inset-0 z-50 flex items-center justify-center bg-ink/50 backdrop-blur-xs p-4"
      @click.self="selectedDuplicates = null"
    >
      <div class="rounded-lg border border-hairline bg-surface p-6 shadow-ev-3 max-w-lg w-full space-y-4 text-ink animate-in fade-in zoom-in-95 duration-150">
        <div class="flex items-center justify-between border-b border-hairline pb-3">
          <div>
            <h3 class="font-serif text-heading-md text-ink">Duplicados Detectados en Carga</h3>
            <p class="font-mono text-caption text-ink-muted mt-0.5">
              {{ selectedDuplicates.upload_id }} · {{ selectedDuplicates.filename }}
            </p>
          </div>
          <button
            type="button"
            class="text-ink-muted hover:text-ink p-1 rounded-sm cursor-pointer"
            @click="selectedDuplicates = null"
          >
            <X class="h-4 w-4" />
          </button>
        </div>

        <p class="text-body-sm text-ink-muted">
          Los siguientes registros duplicados fueron detectados por el validador y consolidados para preservar la unicidad del corpus sin adulterar el cálculo de precedencia:
        </p>

        <div class="max-h-60 overflow-y-auto space-y-2 font-mono text-caption">
          <div
            v-for="(dup, idx) in selectedDuplicates.duplicate_details"
            :key="idx"
            class="p-2.5 rounded-sm bg-surface-sunken border border-hairline text-[11px]"
          >
            <div class="text-warning font-semibold">{{ dup.reason }} (fila {{ dup.row }})</div>
            <div v-if="dup.url" class="truncate text-ink-muted mt-0.5">{{ dup.url }}</div>
            <div v-if="dup.titulo" class="text-ink mt-0.5">«{{ dup.titulo }}»</div>
            <div v-if="dup.id_caso" class="text-ink-muted mt-0.5">Caso ID: {{ dup.id_caso }}</div>
          </div>
        </div>

        <div class="flex justify-end pt-3 border-t border-hairline">
          <Button variant="outline" class="h-8 px-3 text-caption cursor-pointer" @click="selectedDuplicates = null">
            Cerrar
          </Button>
        </div>
      </div>
    </div>

    <!-- Card 5: Quality Report & Data Provenance -->
    <Card v-if="report">
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="font-serif text-heading-md text-ink">
            Reporte de Calidad y Procedencia de Datos
          </h2>
          <span class="font-mono text-caption text-ink-muted bg-surface-sunken px-2 py-0.5 rounded-sm border border-hairline uppercase">
            {{ report.source }}
          </span>
        </div>
      </template>

      <div class="space-y-5 text-body-sm">
        <!-- Metadata Strip -->
        <div class="rounded-md border border-hairline bg-surface-sunken p-3 flex flex-wrap gap-x-6 gap-y-2 text-caption text-ink-muted">
          <div>Origen: <strong class="text-ink uppercase font-semibold">{{ report.source }}</strong></div>
          <div v-if="(report.manifest as Record<string,string>)?.fecha_corte_UTC">
            Corte UTC: <span class="font-mono tabular-nums text-ink font-medium">{{ (report.manifest as Record<string,string>).fecha_corte_UTC }}</span>
          </div>
          <div v-if="report.finished_at">
            Finalizado: <span class="font-mono tabular-nums text-ink font-medium">{{ formatDate(report.finished_at as string) }}</span>
          </div>
        </div>

        <!-- Families Grid -->
        <div>
          <h3 class="text-label uppercase tracking-wider text-ink-muted mb-3 font-semibold">
            Familias de Datos Ingestadas
          </h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div
              v-for="(fam, name) in (report.families as Record<string, Record<string, number>>)"
              :key="name"
              class="p-3.5 rounded-md border border-hairline bg-surface-sunken flex flex-col justify-between"
            >
              <div class="font-mono font-semibold text-caption text-primary truncate">{{ name }}</div>
              <div class="mt-2 flex items-baseline justify-between">
                <span class="font-mono text-heading-md font-bold text-success tabular-nums">{{ fam.valid }}</span>
                <span class="font-mono text-caption text-ink-muted tabular-nums">{{ fam.dropped }} descartadas</span>
              </div>
              <div class="font-mono text-[11px] text-ink-muted mt-1 tabular-nums">
                Total leídas: {{ fam.raw }}
              </div>
            </div>
          </div>
        </div>

        <!-- Warnings / Observations -->
        <div v-if="(report.warnings as string[])?.length" class="rounded-md border border-warning/30 bg-warning/10 p-4 space-y-1.5">
          <p class="font-semibold text-caption text-warning flex items-center gap-1.5">
            <AlertTriangle class="h-4 w-4 shrink-0 text-warning" />
            <span>Observaciones / Advertencias registradas:</span>
          </p>
          <ul class="list-disc pl-5 text-caption text-ink space-y-1">
            <li v-for="(w, i) in (report.warnings as string[])" :key="i">{{ w }}</li>
          </ul>
        </div>
      </div>
    </Card>

    <!-- Empty State for Quality Report -->
    <div
      v-else
      class="flex flex-col items-center gap-3 rounded-lg border border-dashed border-hairline bg-surface px-6 py-12 text-center"
    >
      <span class="rounded-md bg-surface-sunken px-2 py-0.5 font-mono text-caption text-ink-muted">Sin reporte</span>
      <h3 class="font-serif text-display-lg text-ink">No hay reporte de calidad generado todavía</h3>
      <p class="max-w-[46ch] text-body-sm text-ink-muted">
        Sincroniza noticias en vivo desde los feeds RSS de TVN o ejecuta una ingesta manual para inspeccionar la procedencia del corpus.
      </p>
    </div>
  </div>
</template>
