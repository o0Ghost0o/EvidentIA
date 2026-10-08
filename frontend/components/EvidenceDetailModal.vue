<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import { api } from "~/composables/useApi";
import { CATALOG, NODES, PROVENANCE } from "~/lib/leadEvidence";

export interface EvidenceItemDetail {
  tipo: string;
  id: string;
  titulo: string;
  descripcion?: string | null;
  url?: string | null;
  fuente_nombre?: string | null;
  fecha?: string | null;
  cita_codigo?: string | null;
  cita_texto?: string | null;
  detalles: Record<string, any>;
  relaciones: {
    origen_tipo: string;
    origen_id: string;
    destino_tipo: string;
    destino_id: string;
    tipo: string;
    peso?: number;
  }[];
}

const props = defineProps<{
  open: boolean;
  tipo?: string;
  id?: string;
  initialItem?: EvidenceItemDetail | null;
}>();

const emit = defineEmits<{
  (e: "update:open", value: boolean): void;
  (e: "close"): void;
  (e: "navigate", tipo: string, id: string): void;
}>();

const loading = ref(false);
const error = ref<string | null>(null);
const item = ref<EvidenceItemDetail | null>(null);
const copiedId = ref(false);
const copiedFull = ref(false);

async function fetchItem(tipo: string, idVal: string) {
  loading.value = true;
  error.value = null;
  item.value = null;

  try {
    const res = await api<EvidenceItemDetail>("evidence/item", {
      query: { tipo, id: idVal },
    });
    item.value = res;
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || "No se pudo cargar el detalle de la fuente.";
  } finally {
    loading.value = false;
  }
}

watch(
  () => [props.open, props.tipo, props.id],
  ([isOpen, newTipo, newId]) => {
    if (isOpen) {
      copiedId.value = false;
      copiedFull.value = false;
      if (props.initialItem) {
        item.value = props.initialItem;
        loading.value = false;
        error.value = null;
      } else if (newTipo && newId) {
        fetchItem(String(newTipo), String(newId));
      }
    } else {
      item.value = null;
      error.value = null;
    }
  },
  { immediate: true }
);

function closeModal() {
  emit("update:open", false);
  emit("close");
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Escape" && props.open) {
    closeModal();
  }
}

onMounted(() => {
  window.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
});

const computedCitaCodigo = computed(() => {
  if (!item.value) return "";
  if (item.value.cita_codigo) return item.value.cita_codigo;
  const idVal = item.value.id;
  const cat = CATALOG.find((c) => c.id === idVal);
  if (cat) return `[${cat.id}:${cat.c}]`;
  const node = NODES[idVal];
  if (node) return `[${idVal}:${node.f || "mención"}]`;
  if (item.value.tipo === "news") return `[${idVal}:titulo]`;
  if (item.value.tipo === "indicator") return `[${idVal}:valor]`;
  if (item.value.tipo === "event") return `[${idVal}:registro]`;
  return `[${item.value.tipo}:${idVal}]`;
});

const computedCitaTexto = computed(() => {
  if (!item.value) return "";
  if (item.value.cita_texto) return item.value.cita_texto;
  const idVal = item.value.id;
  const cat = CATALOG.find((c) => c.id === idVal);
  if (cat && cat.x) return cat.x;
  const node = NODES[idVal];
  if (node && node.x) return node.x;
  const prov = PROVENANCE[idVal];
  if (prov && prov.x) return prov.x;
  if (item.value.tipo === "news") return `«${item.value.titulo}»`;
  if (item.value.tipo === "indicator") {
    const val = item.value.detalles?.valor !== null && item.value.detalles?.valor !== undefined
      ? `${item.value.detalles.valor} ${item.value.detalles.unidad || ""}`.trim()
      : "Sin dato publicado";
    return `«${item.value.detalles?.indicador_nombre || item.value.titulo}: ${val} (${item.value.detalles?.anio || ""})»`;
  }
  if (item.value.tipo === "event") {
    const mag = item.value.detalles?.magnitude ? `M${item.value.detalles.magnitude}` : "";
    const place = item.value.detalles?.place || "Ubicación registrada";
    const depth = item.value.detalles?.depth ? `${item.value.detalles.depth} km profundidad` : "";
    return `«Sismo ${mag} en ${place}${depth ? " (" + depth + ")" : ""}»`;
  }
  return item.value.descripcion || `«${item.value.titulo}»`;
});

async function copyCitationId() {
  if (!computedCitaCodigo.value) return;
  try {
    await navigator.clipboard.writeText(computedCitaCodigo.value);
    copiedId.value = true;
    setTimeout(() => {
      copiedId.value = false;
    }, 2000);
  } catch {
    // Fallback if clipboard api not available
  }
}

async function copyFullCitation() {
  if (!computedCitaTexto.value || !computedCitaCodigo.value) return;
  const full = `${computedCitaTexto.value} ${computedCitaCodigo.value}`;
  try {
    await navigator.clipboard.writeText(full);
    copiedFull.value = true;
    setTimeout(() => {
      copiedFull.value = false;
    }, 2000);
  } catch {
    // Fallback if clipboard api not available
  }
}

function typeBadgeProps(tipo: string): { label: string; variant: "default" | "secondary" | "outline" | "destructive" | "success" | "warning" | "info" } {
  switch (tipo) {
    case "news":
      return { label: "Noticia de Prensa", variant: "info" };
    case "indicator":
      return { label: "Indicador Oficial WB", variant: "info" };
    case "event":
      return { label: "Evento Sísmico USGS", variant: "warning" };
    case "entity":
      return { label: "Entidad del Grafo", variant: "secondary" };
    case "case":
      return { label: "Lead Editorial", variant: "default" };
    default:
      return { label: tipo, variant: "secondary" };
  }
}

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return "Fecha no registrada";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleString("es-PA", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return dateStr;
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
    >
      <!-- Backdrop (DESIGN.md: 40% ink backdrop with subtle blur) -->
      <div
        class="fixed inset-0 bg-ink/50 backdrop-blur-xs transition-opacity"
        @click="closeModal"
      ></div>

      <!-- Modal Card (DESIGN.md: surface, hairline, elevation 3 for modals, rounded-lg) -->
      <div
        class="relative z-10 w-full max-w-2xl max-h-[90vh] flex flex-col rounded-lg border border-hairline bg-surface text-ink shadow-ev-3 overflow-hidden animate-in fade-in zoom-in-95 duration-150"
      >
        <!-- Modal Header -->
        <div class="flex items-start justify-between border-b border-hairline px-6 py-4 bg-surface-sunken/40">
          <div class="space-y-1.5 pr-6">
            <div class="flex flex-wrap items-center gap-2">
              <Badge
                v-if="item || tipo"
                :variant="typeBadgeProps(item?.tipo || tipo || '').variant"
                class="text-caption font-medium"
              >
                {{ typeBadgeProps(item?.tipo || tipo || "").label }}
              </Badge>
              <span class="font-mono text-mono text-caption text-ink-muted bg-surface-sunken border border-hairline px-2 py-0.5 rounded-sm tabular-nums">
                {{ item?.id || id }}
              </span>
            </div>
            <h3 class="font-serif text-heading-md font-semibold text-ink leading-snug">
              {{ item?.titulo || (loading ? "Cargando contenido de la evidencia..." : "Detalle de Evidencia") }}
            </h3>
          </div>

          <!-- Close button -->
          <button
            type="button"
            class="rounded-md p-1.5 text-ink-muted hover:bg-surface-sunken hover:text-ink transition-colors shrink-0"
            title="Cerrar modal (Esc)"
            @click="closeModal"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Modal Body -->
        <div class="flex-1 overflow-y-auto p-6 space-y-5">
          <!-- Loading state -->
          <div v-if="loading" class="space-y-4 py-8">
            <div class="flex items-center justify-center gap-3 text-body-sm text-ink-muted">
              <svg class="animate-spin h-5 w-5 text-primary" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
              </svg>
              <span>Consultando repositorio de evidencia y relaciones...</span>
            </div>
          </div>

          <!-- Error state -->
          <div v-else-if="error" class="p-4 rounded-md border border-error/30 bg-error/10 text-error text-body-sm space-y-2">
            <div class="font-semibold flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>Fuente no encontrada</span>
            </div>
            <p>{{ error }}</p>
          </div>

          <!-- Content display -->
          <template v-else-if="item">
            <!-- Source & Date Strip -->
            <div class="flex flex-wrap items-center justify-between gap-3 p-3 rounded-md bg-surface-sunken/60 border border-hairline text-caption font-sans">
              <div class="flex items-center gap-2">
                <span class="text-ink-muted font-medium">Fuente:</span>
                <span class="font-semibold text-ink">{{ item.fuente_nombre || "Oficial" }}</span>
              </div>
              <div class="flex items-center gap-2 text-ink-muted font-mono tabular-nums">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span>{{ formatDate(item.fecha) }}</span>
              </div>
            </div>

            <!-- Description / Extract -->
            <div class="space-y-1.5">
              <h4 class="text-caption font-semibold uppercase tracking-wider text-ink-muted">
                Contenido / Registro
              </h4>
              <div class="p-4 rounded-md border border-hairline bg-surface-sunken/30 text-body-sm leading-relaxed text-ink whitespace-pre-line font-sans">
                {{ item.descripcion || "Sin texto adicional registrado para este nodo." }}
              </div>
            </div>

            <!-- News specific details -->
            <div v-if="item.tipo === 'news'" class="grid grid-cols-2 sm:grid-cols-3 gap-3 text-caption">
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Medio emisor</div>
                <div class="font-semibold text-ink text-body-sm mt-0.5">{{ item.detalles.medio }}</div>
              </div>
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Alcance textual</div>
                <div class="font-semibold capitalize text-ink text-body-sm mt-0.5">{{ item.detalles.alcance_texto }}</div>
              </div>
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Agencia primaria</div>
                <div class="font-semibold text-ink text-body-sm mt-0.5">{{ item.detalles.agencia_primaria || "Producción propia" }}</div>
              </div>
              <div v-if="item.detalles.tema" class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Categoría / Tema</div>
                <div class="font-semibold text-ink text-body-sm mt-0.5">{{ item.detalles.tema }}</div>
              </div>
              <div v-if="item.detalles.grupo_evento_id" class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Grupo de evento</div>
                <div class="font-mono text-mono tabular-nums text-caption text-ink mt-0.5 truncate">{{ item.detalles.grupo_evento_id }}</div>
              </div>
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Idioma</div>
                <div class="font-semibold uppercase text-ink text-body-sm mt-0.5">{{ item.detalles.idioma }}</div>
              </div>
            </div>

            <!-- Indicator specific details -->
            <div v-else-if="item.tipo === 'indicator'" class="grid grid-cols-2 sm:grid-cols-3 gap-3 text-caption">
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">País</div>
                <div class="font-semibold text-ink text-body-sm mt-0.5">{{ item.detalles.pais_nombre }} ({{ item.detalles.pais_iso3 }})</div>
              </div>
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Valor Medido</div>
                <div class="font-mono tabular-nums font-semibold text-info text-body-sm mt-0.5">
                  {{ item.detalles.valor !== null ? `${item.detalles.valor} ${item.detalles.unidad || ''}` : 'Sin dato' }}
                </div>
              </div>
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Año de observación</div>
                <div class="font-mono tabular-nums font-semibold text-ink text-body-sm mt-0.5">{{ item.detalles.anio }}</div>
              </div>
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Indicador ID</div>
                <div class="font-mono text-mono tabular-nums text-caption text-ink mt-0.5 truncate">{{ item.detalles.indicador_id }}</div>
              </div>
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Licencia de datos</div>
                <div class="font-semibold text-ink text-body-sm mt-0.5">{{ item.detalles.licencia }}</div>
              </div>
            </div>

            <!-- Event specific details -->
            <div v-else-if="item.tipo === 'event'" class="grid grid-cols-2 sm:grid-cols-3 gap-3 text-caption">
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Magnitud</div>
                <div class="font-mono tabular-nums font-semibold text-warning text-body-sm mt-0.5">M{{ item.detalles.magnitude }}</div>
              </div>
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Profundidad</div>
                <div class="font-mono tabular-nums font-semibold text-ink text-body-sm mt-0.5">{{ item.detalles.depth }} km</div>
              </div>
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40">
                <div class="text-ink-muted">Estado</div>
                <div class="font-semibold capitalize text-ink text-body-sm mt-0.5">{{ item.detalles.status }}</div>
              </div>
              <div class="p-2.5 rounded-md border border-hairline bg-surface-sunken/40 col-span-2">
                <div class="text-ink-muted">Lugar / Epicentro</div>
                <div class="font-semibold text-ink text-body-sm mt-0.5 truncate">{{ item.detalles.place }}</div>
              </div>
            </div>

            <!-- Graph relations -->
            <div v-if="item.relaciones && item.relaciones.length" class="space-y-2">
              <h4 class="text-caption font-semibold uppercase tracking-wider text-ink-muted">
                Conexiones en Grafo ({{ item.relaciones.length }})
              </h4>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="(rel, idx) in item.relaciones"
                  :key="idx"
                  type="button"
                  class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-caption border border-hairline bg-surface hover:bg-surface-sunken text-ink transition-colors shadow-ev-1 cursor-pointer"
                  @click="emit('navigate', rel.destino_tipo === item.tipo ? rel.origen_tipo : rel.destino_tipo, rel.destino_tipo === item.tipo ? rel.origen_id : rel.destino_id)"
                >
                  <span class="text-ink-muted font-mono text-[10px]">{{ rel.tipo }}:</span>
                  <span class="font-mono tabular-nums font-medium text-ink">
                    {{ rel.destino_tipo === item.tipo ? `${rel.origen_tipo}:${rel.origen_id}` : `${rel.destino_tipo}:${rel.destino_id}` }}
                  </span>
                </button>
              </div>
            </div>

            <!-- Citation helper with actual Quote & ID -->
            <div class="p-3.5 rounded-md bg-surface-sunken/60 border border-hairline space-y-2.5">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <span class="text-caption text-ink-muted font-medium">Cita para borrador:</span>
                  <code class="font-mono text-mono tabular-nums bg-surface border border-hairline px-2 py-0.5 rounded-sm text-ink font-semibold text-caption">
                    {{ computedCitaCodigo }}
                  </code>
                </div>
                <div class="flex items-center gap-1.5">
                  <Button
                    variant="outline"
                    size="sm"
                    class="h-7 text-caption gap-1.5 cursor-pointer"
                    title="Copiar solo el identificador [id:campo]"
                    @click="copyCitationId"
                  >
                    <svg v-if="!copiedId" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                    </svg>
                    <svg v-else class="w-3.5 h-3.5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>{{ copiedId ? "¡ID Copiado!" : "Copiar ID" }}</span>
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    class="h-7 text-caption gap-1.5 cursor-pointer font-medium"
                    title="Copiar cita textual completa con su identificador"
                    @click="copyFullCitation"
                  >
                    <svg v-if="!copiedFull" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <svg v-else class="w-3.5 h-3.5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>{{ copiedFull ? "¡Cita Copiada!" : "Copiar Cita Textual" }}</span>
                  </Button>
                </div>
              </div>

              <!-- Visual Quote Callout -->
              <blockquote class="rounded-md border-l-[3px] border-primary bg-surface p-3 text-body-sm text-ink font-serif italic leading-relaxed shadow-ev-1">
                {{ computedCitaTexto }}
                <span class="mt-1.5 block font-mono text-mono text-caption not-italic text-ink-muted tabular-nums">
                  — {{ computedCitaCodigo }}
                </span>
              </blockquote>
            </div>
          </template>
        </div>

        <!-- Modal Footer -->
        <div class="border-t border-hairline px-6 py-3.5 bg-surface-sunken/40 flex items-center justify-between gap-3">
          <div>
            <a
              v-if="item?.url"
              :href="item.url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1.5 text-body-sm font-semibold text-primary hover:underline"
            >
              <span>Abrir fuente original</span>
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          </div>

          <Button variant="default" size="sm" @click="closeModal">
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
