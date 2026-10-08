<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Badge from "~/components/ui/Badge.vue";
import { api } from "~/composables/useApi";

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
      liveSuccessMsg.value = "¡Noticias en vivo de hoy sincronizadas exitosamente!";
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
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) +
      " (" + d.toLocaleDateString() + ")";
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

    uploadResultMsg.value[familyKey] = `✓ ${record.valid_rows} filas válidas procesadas (${record.upload_id})${record.duplicates_found ? ` · ${record.duplicate_count} duplicados detectados` : ''}`;
    await Promise.all([loadUploadHistory(), loadReport()]);
  } catch (err: any) {
    uploadErrorMsg.value[familyKey] = err?.data?.detail || err?.message || "Error al procesar el archivo.";
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
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-3xl font-extrabold tracking-tight">Ingesta y Flujo de Noticias</h1>
        <p class="text-sm text-muted-foreground mt-1">
          Monitoreo continuo de feeds RSS de TVN-2 y Panamá, extracción de entidades y actualización de señales.
        </p>
      </div>

      <!-- Live badge -->
      <div class="flex items-center gap-2">
        <Badge v-if="report?.source === 'live'" class="bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 text-xs px-2.5 py-1">
          🔴 Corpus: Noticias en Vivo (TVN RSS)
        </Badge>
        <Badge v-else class="bg-amber-600/20 text-amber-300 border border-amber-500/30 text-xs px-2.5 py-1">
          🟡 Corpus: Snapshot Local (T10 Demo Offline)
        </Badge>
      </div>
    </div>

    <!-- Alert feedback -->
    <div v-if="liveSuccessMsg" class="p-4 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-200 text-sm flex items-center justify-between">
      <span>{{ liveSuccessMsg }}</span>
      <button class="text-xs text-emerald-400 hover:underline" @click="liveSuccessMsg = ''">Cerrar</button>
    </div>
    <div v-if="error" class="p-4 rounded-lg bg-destructive/20 border border-destructive/40 text-destructive text-sm flex items-center justify-between">
      <span>{{ error }}</span>
      <button class="text-xs text-destructive hover:underline" @click="error = ''">Cerrar</button>
    </div>

    <!-- Auto-Ingest Pitch Control Card -->
    <Card class="border-border/60 bg-gradient-to-br from-card to-secondary/10">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="inline-block w-2.5 h-2.5 rounded-full" :class="scheduleStatus.enabled ? 'bg-emerald-500 animate-pulse' : 'bg-muted-foreground'"></span>
            <span class="font-semibold text-base">Ingesta Automática en Segundo Plano (Pitch Mode)</span>
          </div>
          <Badge :class="scheduleStatus.enabled ? 'bg-emerald-900/60 text-emerald-300 border-emerald-700' : 'bg-muted/60 text-muted-foreground'">
            {{ scheduleStatus.enabled ? 'ACTIVO' : 'PAUSADO' }}
          </Badge>
        </div>
      </template>

      <div class="space-y-4">
        <p class="text-sm text-muted-foreground">
          Activa el copiloto para escanear periódicamente el feed RSS de TVN-2 y medios de Panamá, extrayendo entidades,
          actualizando el grafo de eventos y recalculando el ranking de atención en tiempo real.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <!-- Toggle Box -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-secondary/20">
            <div>
              <div class="font-medium text-sm">Monitoreo Automático</div>
              <div class="text-xs text-muted-foreground">Feature flag global</div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                class="sr-only peer"
                :checked="scheduleStatus.enabled"
                :disabled="savingSchedule"
                @change="toggleAutoSchedule(!scheduleStatus.enabled)"
              />
              <div class="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
            </label>
          </div>

          <!-- Interval Selector -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-secondary/20">
            <div>
              <div class="font-medium text-sm">Frecuencia de Escaneo</div>
              <div class="text-xs text-muted-foreground">Intervalo en minutos</div>
            </div>
            <select
              :value="scheduleStatus.interval_minutes"
              :disabled="savingSchedule"
              class="bg-background border border-input text-foreground text-sm rounded-md px-2.5 py-1 focus:ring-1 focus:ring-ring"
              @change="changeInterval"
            >
              <option :value="5">Cada 5 min</option>
              <option :value="15">Cada 15 min</option>
              <option :value="30">Cada 30 min</option>
              <option :value="60">Cada 60 min</option>
            </select>
          </div>

          <!-- Action: Force Live Ingest Now -->
          <div class="flex items-center justify-center p-3 rounded-lg border border-emerald-900/40 bg-emerald-950/20">
            <Button
              class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-sm transition-all text-xs sm:text-sm py-2"
              :disabled="runningLive || scheduleStatus.is_running"
              @click="runLiveNow"
            >
              {{ (runningLive || scheduleStatus.is_running) ? 'Sincronizando Noticias…' : '⚡ Sincronizar Noticias de Hoy en Vivo' }}
            </Button>
          </div>
        </div>

        <!-- Schedule Diagnostics -->
        <div class="pt-2 text-xs text-muted-foreground flex flex-wrap gap-4 border-t border-border/40">
          <div>Última ejecución: <span class="font-mono text-foreground">{{ formatDate(scheduleStatus.last_run) }}</span></div>
          <div v-if="scheduleStatus.enabled">Próximo ciclo: <span class="font-mono text-foreground">{{ formatDate(scheduleStatus.next_run) }}</span></div>
          <div>Estado: <span class="font-medium capitalize" :class="scheduleStatus.is_running ? 'text-amber-400' : 'text-emerald-400'">{{ scheduleStatus.is_running ? 'Ejecutando…' : scheduleStatus.last_status }}</span></div>
          <div v-if="scheduleStatus.items_ingested_last_run > 0">
            Titulares procesados: <span class="font-mono text-foreground font-semibold">{{ scheduleStatus.items_ingested_last_run }}</span>
          </div>
        </div>
      </div>
    </Card>

    <!-- Schema File Upload with Downloadable Templates -->
    <Card>
      <template #header>
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-semibold text-base">Carga de Archivos por Esquema (Upload & Validación)</h3>
            <p class="text-xs text-muted-foreground mt-0.5">
              Carga manual de datos con validación determinista, detección automática de duplicados y plantillas descargables.
            </p>
          </div>
        </div>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- 1. Noticias CSV -->
        <div class="p-4 rounded-lg border border-border/50 bg-secondary/15 flex flex-col justify-between space-y-3">
          <div>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-sm text-foreground flex items-center gap-1.5">
                📰 Noticias de Prensa
              </span>
              <Badge variant="outline" class="text-[11px] font-mono">noticias.csv</Badge>
            </div>
            <p class="text-xs text-muted-foreground mt-1">
              Titulares de medios locales y GDELT. Detección automática de duplicados por URL y títulos repetidos (Jaccard > 0.85).
            </p>
            <div class="mt-2 text-[11px] text-muted-foreground font-mono bg-background/50 p-2 rounded border border-border/40">
              id_noticia, titulo, url, medio, idioma, fecha_publicacion, tema, origen, alcance_texto
            </div>
          </div>

          <div class="space-y-2 pt-2 border-t border-border/40">
            <div class="flex items-center justify-between gap-2">
              <Button
                variant="ghost"
                size="sm"
                class="text-xs h-8 text-primary hover:text-primary-deep"
                @click="downloadTemplate('noticias')"
              >
                📥 Descargar Plantilla
              </Button>
              <label class="cursor-pointer">
                <input
                  type="file"
                  accept=".csv"
                  class="sr-only"
                  :disabled="uploading['noticias']"
                  @change="uploadFamilyFile($event, 'noticias')"
                />
                <span class="inline-flex items-center justify-center rounded-md text-xs font-medium h-8 px-3 bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs">
                  {{ uploading['noticias'] ? 'Validando…' : 'Subir Archivo CSV' }}
                </span>
              </label>
            </div>
            <p v-if="uploadResultMsg['noticias']" class="text-xs text-emerald-400 font-medium">{{ uploadResultMsg['noticias'] }}</p>
            <p v-if="uploadErrorMsg['noticias']" class="text-xs text-destructive font-medium">{{ uploadErrorMsg['noticias'] }}</p>
          </div>
        </div>

        <!-- 2. Indicadores CSV -->
        <div class="p-4 rounded-lg border border-border/50 bg-secondary/15 flex flex-col justify-between space-y-3">
          <div>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-sm text-foreground flex items-center gap-1.5">
                📊 Indicadores Banco Mundial
              </span>
              <Badge variant="outline" class="text-[11px] font-mono">indicadores.csv</Badge>
            </div>
            <p class="text-xs text-muted-foreground mt-1">
              Series macroeconómicas oficiales. Clave de unicidad: (pais_iso3, indicador_id, anio).
            </p>
            <div class="mt-2 text-[11px] text-muted-foreground font-mono bg-background/50 p-2 rounded border border-border/40">
              pais_iso3, indicador_id, anio, valor, unidad, fuente_url, licencia, fecha_extraccion
            </div>
          </div>

          <div class="space-y-2 pt-2 border-t border-border/40">
            <div class="flex items-center justify-between gap-2">
              <Button
                variant="ghost"
                size="sm"
                class="text-xs h-8 text-primary hover:text-primary-deep"
                @click="downloadTemplate('indicadores')"
              >
                📥 Descargar Plantilla
              </Button>
              <label class="cursor-pointer">
                <input
                  type="file"
                  accept=".csv"
                  class="sr-only"
                  :disabled="uploading['indicadores']"
                  @change="uploadFamilyFile($event, 'indicadores')"
                />
                <span class="inline-flex items-center justify-center rounded-md text-xs font-medium h-8 px-3 bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs">
                  {{ uploading['indicadores'] ? 'Validando…' : 'Subir Archivo CSV' }}
                </span>
              </label>
            </div>
            <p v-if="uploadResultMsg['indicadores']" class="text-xs text-emerald-400 font-medium">{{ uploadResultMsg['indicadores'] }}</p>
            <p v-if="uploadErrorMsg['indicadores']" class="text-xs text-destructive font-medium">{{ uploadErrorMsg['indicadores'] }}</p>
          </div>
        </div>

        <!-- 3. Eventos GeoJSON -->
        <div class="p-4 rounded-lg border border-border/50 bg-secondary/15 flex flex-col justify-between space-y-3">
          <div>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-sm text-foreground flex items-center gap-1.5">
                🌍 Eventos Geofísicos USGS
              </span>
              <Badge variant="outline" class="text-[11px] font-mono">eventos.geojson</Badge>
            </div>
            <p class="text-xs text-muted-foreground mt-1">
              Sismicidad regional en formato FeatureCollection. Clave de unicidad: id de evento USGS.
            </p>
            <div class="mt-2 text-[11px] text-muted-foreground font-mono bg-background/50 p-2 rounded border border-border/40">
              FeatureCollection -> features: [id, geometry.coordinates, properties: mag, place, time]
            </div>
          </div>

          <div class="space-y-2 pt-2 border-t border-border/40">
            <div class="flex items-center justify-between gap-2">
              <Button
                variant="ghost"
                size="sm"
                class="text-xs h-8 text-primary hover:text-primary-deep"
                @click="downloadTemplate('eventos')"
              >
                📥 Descargar Plantilla
              </Button>
              <label class="cursor-pointer">
                <input
                  type="file"
                  accept=".geojson,.json"
                  class="sr-only"
                  :disabled="uploading['eventos']"
                  @change="uploadFamilyFile($event, 'eventos')"
                />
                <span class="inline-flex items-center justify-center rounded-md text-xs font-medium h-8 px-3 bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs">
                  {{ uploading['eventos'] ? 'Validando…' : 'Subir GeoJSON' }}
                </span>
              </label>
            </div>
            <p v-if="uploadResultMsg['eventos']" class="text-xs text-emerald-400 font-medium">{{ uploadResultMsg['eventos'] }}</p>
            <p v-if="uploadErrorMsg['eventos']" class="text-xs text-destructive font-medium">{{ uploadErrorMsg['eventos'] }}</p>
          </div>
        </div>

        <!-- 4. Fichas JSONL -->
        <div class="p-4 rounded-lg border border-border/50 bg-secondary/15 flex flex-col justify-between space-y-3">
          <div>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-sm text-foreground flex items-center gap-1.5">
                📋 Fichas Editoriales
              </span>
              <Badge variant="outline" class="text-[11px] font-mono">fichas.jsonl</Badge>
            </div>
            <p class="text-xs text-muted-foreground mt-1">
              Casos investigativos con fuentes vinculadas, afirmaciones y puntajes. Clave de unicidad: id_caso.
            </p>
            <div class="mt-2 text-[11px] text-muted-foreground font-mono bg-background/50 p-2 rounded border border-border/40">
              {"id_caso": "...", "modalidad": "tvn", "ids_fuente": [...], "puntaje": ...}
            </div>
          </div>

          <div class="space-y-2 pt-2 border-t border-border/40">
            <div class="flex items-center justify-between gap-2">
              <Button
                variant="ghost"
                size="sm"
                class="text-xs h-8 text-primary hover:text-primary-deep"
                @click="downloadTemplate('fichas')"
              >
                📥 Descargar Plantilla
              </Button>
              <label class="cursor-pointer">
                <input
                  type="file"
                  accept=".jsonl,.json"
                  class="sr-only"
                  :disabled="uploading['fichas']"
                  @change="uploadFamilyFile($event, 'fichas')"
                />
                <span class="inline-flex items-center justify-center rounded-md text-xs font-medium h-8 px-3 bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs">
                  {{ uploading['fichas'] ? 'Validando…' : 'Subir JSONL' }}
                </span>
              </label>
            </div>
            <p v-if="uploadResultMsg['fichas']" class="text-xs text-emerald-400 font-medium">{{ uploadResultMsg['fichas'] }}</p>
            <p v-if="uploadErrorMsg['fichas']" class="text-xs text-destructive font-medium">{{ uploadErrorMsg['fichas'] }}</p>
          </div>
        </div>
      </div>
    </Card>

    <!-- Upload History & Duplicate Audit Table -->
    <Card v-if="uploadHistory.length > 0">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="font-semibold text-base">Historial de Cargas y Trazabilidad de Duplicados</span>
            <Badge variant="outline" class="text-xs">{{ uploadHistory.length }} registradas</Badge>
          </div>
        </div>
      </template>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="border-b border-border/50 bg-secondary/30 text-muted-foreground uppercase tracking-wider font-semibold">
            <tr>
              <th class="py-2.5 px-3">Upload ID</th>
              <th class="py-2.5 px-3">Fecha / Hora</th>
              <th class="py-2.5 px-3">Archivo / Familia</th>
              <th class="py-2.5 px-3">Filas Procesadas</th>
              <th class="py-2.5 px-3">Detección de Duplicados</th>
              <th class="py-2.5 px-3 text-right">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border/30">
            <tr v-for="item in uploadHistory" :key="item.upload_id" class="hover:bg-secondary/15 transition-colors">
              <td class="py-2.5 px-3 font-mono font-medium text-primary">
                {{ item.upload_id }}
              </td>
              <td class="py-2.5 px-3 text-muted-foreground whitespace-nowrap">
                {{ formatDate(item.timestamp) }}
              </td>
              <td class="py-2.5 px-3">
                <span class="font-medium text-foreground">{{ item.filename }}</span>
                <span class="block text-[11px] text-muted-foreground font-mono">{{ item.family }}</span>
              </td>
              <td class="py-2.5 px-3 whitespace-nowrap">
                <span class="text-emerald-400 font-semibold">{{ item.valid_rows }} válidas</span>
                <span v-if="item.dropped_rows > 0" class="text-muted-foreground"> / {{ item.dropped_rows }} descartadas</span>
                <span class="text-[11px] text-muted-foreground block">Total: {{ item.total_rows }}</span>
              </td>
              <td class="py-2.5 px-3">
                <div v-if="item.duplicates_found" class="flex items-center gap-2">
                  <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-amber-500/15 text-amber-300 border border-amber-500/30">
                    ⚠️ {{ item.duplicate_count }} duplicados detectados
                  </span>
                  <button
                    type="button"
                    class="text-[11px] text-primary hover:underline"
                    @click="selectedDuplicates = item"
                  >
                    Ver detalle
                  </button>
                </div>
                <span v-else class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  ✓ Sin duplicados
                </span>
              </td>
              <td class="py-2.5 px-3 text-right whitespace-nowrap">
                <Badge
                  :class="{
                    'bg-emerald-950/60 text-emerald-300 border-emerald-700': item.status === 'completed',
                    'bg-amber-950/60 text-amber-300 border-amber-700': item.status === 'completed_with_warnings',
                    'bg-destructive/20 text-destructive border-destructive/40': item.status === 'failed',
                  }"
                >
                  {{ item.status === 'completed' ? 'Completado' : item.status === 'completed_with_warnings' ? 'Advertencias' : 'Error' }}
                </Badge>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Modal de Detalle de Duplicados -->
    <div
      v-if="selectedDuplicates"
      class="fixed inset-0 z-50 bg-background/80 backdrop-blur-xs flex items-center justify-center p-4"
      @click.self="selectedDuplicates = null"
    >
      <div class="rounded-lg border border-border bg-card p-6 shadow-xl max-w-lg w-full space-y-4">
        <div class="flex items-center justify-between border-b border-border/50 pb-3">
          <div>
            <h4 class="font-semibold text-base">Duplicados Detectados en Carga</h4>
            <p class="text-xs font-mono text-muted-foreground">{{ selectedDuplicates.upload_id }} · {{ selectedDuplicates.filename }}</p>
          </div>
          <button class="text-muted-foreground hover:text-foreground text-sm" @click="selectedDuplicates = null">✕</button>
        </div>

        <p class="text-xs text-muted-foreground">
          Los siguientes registros duplicados fueron detectados por el validador y consolidados para no duplicar volumen ni adulterar el cálculo de precedencia:
        </p>

        <div class="max-h-60 overflow-y-auto space-y-2 font-mono text-xs">
          <div
            v-for="(dup, idx) in selectedDuplicates.duplicate_details"
            :key="idx"
            class="p-2.5 rounded bg-secondary/30 border border-border/40 text-[11px]"
          >
            <div class="text-amber-400 font-semibold">{{ dup.reason }} (fila {{ dup.row }})</div>
            <div v-if="dup.url" class="truncate text-muted-foreground mt-0.5">{{ dup.url }}</div>
            <div v-if="dup.titulo" class="text-muted-foreground mt-0.5">«{{ dup.titulo }}»</div>
            <div v-if="dup.id_caso" class="text-muted-foreground mt-0.5">Caso ID: {{ dup.id_caso }}</div>
          </div>
        </div>

        <div class="flex justify-end pt-2 border-t border-border/50">
          <Button size="sm" variant="outline" @click="selectedDuplicates = null">Cerrar</Button>
        </div>
      </div>
    </div>

    <!-- Manual Seed / Offline Mode (T10 Requirement) -->
    <Card>
      <template #header>Carga Manual / Modo Contingencia Offline (T10)</template>
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <label class="flex items-center gap-2 text-sm cursor-pointer select-none">
          <input v-model="useSeed" type="checkbox" class="h-4 w-4 rounded border-border text-primary focus:ring-primary" />
          <span>Usar snapshot local congelado (Simulación demo sin internet / offline T10)</span>
        </label>
        <Button variant="outline" :disabled="runningManual || runningLive" @click="runManualIngest">
          {{ runningManual ? "Cargando…" : "Ejecutar Ingesta Manual" }}
        </Button>
      </div>
    </Card>


    <!-- Quality Report -->
    <Card v-if="report">
      <template #header>Reporte de Calidad y Procedencia de Datos</template>
      <div class="space-y-4 text-sm">
        <div class="flex flex-wrap gap-4 text-xs text-muted-foreground pb-2 border-b border-border/40">
          <div>Origen: <strong class="text-foreground uppercase">{{ report.source }}</strong></div>
          <div v-if="(report.manifest as Record<string,string>)?.fecha_corte_UTC">
            Corte UTC: <span class="font-mono text-foreground">{{ (report.manifest as Record<string,string>).fecha_corte_UTC }}</span>
          </div>
          <div v-if="report.finished_at">
            Finalizado: <span class="font-mono text-foreground">{{ formatDate(report.finished_at as string) }}</span>
          </div>
        </div>

        <div>
          <h4 class="font-medium mb-2">Familias de Datos:</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div
              v-for="(fam, name) in (report.families as Record<string, Record<string, number>>)"
              :key="name"
              class="p-3 rounded-lg border border-border/40 bg-secondary/15"
            >
              <div class="font-mono font-medium text-xs text-primary truncate">{{ name }}</div>
              <div class="mt-2 flex items-baseline justify-between text-xs">
                <span class="text-emerald-400 font-bold text-sm">{{ fam.valid }} válidas</span>
                <span class="text-muted-foreground">{{ fam.dropped }} descartadas</span>
              </div>
              <div class="text-[11px] text-muted-foreground mt-1">
                Total leídas: {{ fam.raw }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="(report.warnings as string[])?.length">
          <p class="font-medium text-xs text-amber-400">Observaciones / Advertencias registradas:</p>
          <ul class="list-disc pl-5 text-xs text-muted-foreground space-y-0.5 mt-1">
            <li v-for="(w, i) in (report.warnings as string[])" :key="i">{{ w }}</li>
          </ul>
        </div>
      </div>
    </Card>

    <div v-else class="text-center py-10 border border-dashed rounded-lg text-muted-foreground text-sm">
      No hay reporte de calidad generado todavía. Sincroniza noticias o ejecuta una ingesta.
    </div>
  </div>
</template>
