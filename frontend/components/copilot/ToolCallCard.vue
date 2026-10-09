<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import {
  Search,
  PlusCircle,
  FileEdit,
  Trash2,
  Tag,
  Link,
  Unlink,
  MessageSquare,
  RefreshCw,
  Activity,
  FileText,
  Gauge,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  CheckCircle2,
  Loader2,
  AlertCircle,
} from "lucide-vue-next";

const props = defineProps<{
  part: any;
}>();

const router = useRouter();
const expanded = ref(false);

const toolName = computed(() => {
  const type = props.part?.type || "";
  return type.startsWith("tool-") ? type.replace(/^tool-/, "") : props.part?.toolName || type;
});

const isComplete = computed(() => {
  return props.part?.state === "output-available" || !!props.part?.output;
});

const isError = computed(() => {
  return props.part?.state === "output-error" || props.part?.output?.success === false;
});

const toolMeta = computed(() => {
  switch (toolName.value) {
    case "search_evidence":
      return {
        label: "Búsqueda de Evidencias",
        icon: Search,
        color: "text-info bg-info/10 border-info/20",
      };
    case "search_leads":
      return {
        label: "Búsqueda de Leads",
        icon: Search,
        color: "text-primary bg-primary/10 border-primary/20",
      };
    case "get_lead_details":
      return {
        label: "Consulta de Lead",
        icon: FileText,
        color: "text-primary bg-primary/10 border-primary/20",
      };
    case "create_lead":
      return {
        label: "Crear Nuevo Lead",
        icon: PlusCircle,
        color: "text-success bg-success/10 border-success/20",
      };
    case "update_lead":
      return {
        label: "Actualizar Lead",
        icon: FileEdit,
        color: "text-warning bg-warning/10 border-warning/20",
      };
    case "delete_lead":
      return {
        label: "Eliminar Lead",
        icon: Trash2,
        color: "text-error bg-error/10 border-error/20",
      };
    case "add_lead_flag":
    case "remove_lead_flag":
      return {
        label: "Etiquetado de Flags",
        icon: Tag,
        color: "text-accent bg-accent/10 border-accent/20",
      };
    case "add_lead_evidence":
      return {
        label: "Vincular Evidencia",
        icon: Link,
        color: "text-success bg-success/10 border-success/20",
      };
    case "remove_lead_evidence":
      return {
        label: "Desvincular Evidencia",
        icon: Unlink,
        color: "text-error bg-error/10 border-error/20",
      };
    case "add_lead_note":
      return {
        label: "Nota de Verificación",
        icon: MessageSquare,
        color: "text-primary bg-primary/10 border-primary/20",
      };
    case "rerun_ingestion":
      return {
        label: "Reejecutar Ingesta",
        icon: RefreshCw,
        color: "text-accent bg-accent/10 border-accent/20",
      };
    case "get_ingestion_status":
      return {
        label: "Estado de Ingesta",
        icon: Activity,
        color: "text-info bg-info/10 border-info/20",
      };
    case "generate_lead_brief":
      return {
        label: "Generar Brief Editorial",
        icon: FileText,
        color: "text-primary bg-primary/10 border-primary/20",
      };
    case "get_lead_score":
      return {
        label: "Score de Evidencia",
        icon: Gauge,
        color: "text-primary bg-primary/10 border-primary/20",
      };
    default:
      return {
        label: toolName.value,
        icon: Activity,
        color: "text-ink-muted bg-surface-sunken border-hairline",
      };
  }
});

// Extract actionable lead ID if present
const linkedLeadId = computed(() => {
  const out = props.part?.output;
  const inp = props.part?.input;
  if (out?.lead?.id) return out.lead.id;
  if (inp?.id && typeof inp.id === "number") return inp.id;
  return null;
});

const toolSummary = computed(() => {
  const out = props.part?.output;
  if (!out) return null;
  if (toolName.value === "get_ingestion_status" && out.report?.families) {
    const f = out.report.families;
    const n = f["noticias.csv"]?.valid ?? 0;
    const i = f["indicadores.csv"]?.valid ?? 0;
    const e = f["eventos.geojson"]?.valid ?? 0;
    return `${n} noticias · ${i} indicadores · ${e} eventos procesados`;
  }
  if (toolName.value === "create_lead" && out.lead?.id) {
    return `Lead #${out.lead.id} creado (${out.lead.modalidad?.toUpperCase() || "TVN"})`;
  }
  if (toolName.value === "update_lead" && out.lead?.id) {
    return `Lead #${out.lead.id} actualizado`;
  }
  if (toolName.value === "search_leads" && typeof out.total === "number") {
    return `${out.total} leads encontrados`;
  }
  if (toolName.value === "search_evidence" && typeof out.count === "number") {
    return `${out.count} evidencias encontradas`;
  }
  if (toolName.value === "rerun_ingestion") {
    return "Ingesta ejecutada correctamente";
  }
  return null;
});

function navigateToLead(id: number) {
  router.push(`/leads/${id}`);
}

function navigateToIngest() {
  router.push("/ingest");
}
</script>

<template>
  <div
    class="my-2 overflow-hidden rounded-md border border-hairline bg-surface-sunken text-xs font-sans shadow-sm transition-all"
  >
    <!-- Header bar -->
    <div
      class="flex items-center justify-between px-3 py-2 cursor-pointer select-none hover:bg-surface/50"
      @click="expanded = !expanded"
    >
      <div class="flex items-center gap-2">
        <div
          class="flex h-5 w-5 items-center justify-center rounded border"
          :class="toolMeta.color"
        >
          <component :is="toolMeta.icon" class="h-3 w-3" />
        </div>
        <span class="font-medium text-ink">{{ toolMeta.label }}</span>
        <span class="font-mono text-[10px] text-ink-muted">({{ toolName }})</span>
      </div>

      <div class="flex items-center gap-2">
        <span
          v-if="!isComplete && !isError"
          class="flex items-center gap-1 font-mono text-[10px] text-accent"
        >
          <Loader2 class="h-3 w-3 animate-spin" />
          Ejecutando
        </span>
        <span
          v-else-if="isError"
          class="flex items-center gap-1 font-mono text-[10px] text-error"
        >
          <AlertCircle class="h-3 w-3" />
          Error
        </span>
        <span
          v-else
          class="flex items-center gap-1 font-mono text-[10px] text-success"
        >
          <CheckCircle2 class="h-3 w-3" />
          Completado
        </span>

        <button
          type="button"
          class="text-ink-muted hover:text-ink p-0.5 rounded"
          :aria-label="expanded ? 'Colapsar detalles' : 'Expandir detalles'"
        >
          <ChevronUp v-if="expanded" class="h-3.5 w-3.5" />
          <ChevronDown v-else class="h-3.5 w-3.5" />
        </button>
      </div>
    </div>

    <!-- Summary snippet when completed and collapsed -->
    <div
      v-if="toolSummary && !expanded"
      class="flex items-center justify-between border-t border-hairline/60 bg-surface/40 px-3 py-1 font-mono text-[11px] text-ink"
    >
      <span class="font-medium text-ink-muted">{{ toolSummary }}</span>
      <span class="text-[10px] text-ink-muted/60">Detalles ▾</span>
    </div>

    <!-- Quick action buttons -->
    <div
      v-if="linkedLeadId || toolName === 'rerun_ingestion'"
      class="flex items-center gap-2 border-t border-hairline/60 bg-surface/30 px-3 py-1.5"
    >
      <button
        v-if="linkedLeadId"
        type="button"
        class="flex items-center gap-1 rounded bg-primary/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-primary transition-colors hover:bg-primary/20"
        @click.stop="navigateToLead(linkedLeadId)"
      >
        <span>Ver Lead #{{ linkedLeadId }}</span>
        <ExternalLink class="h-2.5 w-2.5" />
      </button>

      <button
        v-if="toolName === 'rerun_ingestion'"
        type="button"
        class="flex items-center gap-1 rounded bg-accent/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-accent transition-colors hover:bg-accent/20"
        @click.stop="navigateToIngest"
      >
        <span>Ir a Bandeja de Ingesta</span>
        <ExternalLink class="h-2.5 w-2.5" />
      </button>
    </div>

    <!-- Collapsible payload details -->
    <div
      v-if="expanded"
      class="border-t border-hairline bg-surface p-2.5 font-mono text-[11px] text-ink-muted space-y-2 overflow-x-auto"
    >
      <div v-if="part.input">
        <span class="font-bold text-ink">Entrada:</span>
        <pre class="mt-1 rounded bg-surface-sunken p-2 overflow-x-auto text-[10px] text-ink">{{ JSON.stringify(part.input, null, 2) }}</pre>
      </div>
      <div v-if="part.output">
        <span class="font-bold text-ink">Resultado del Servidor:</span>
        <pre class="mt-1 rounded bg-surface-sunken p-2 overflow-x-auto text-[10px] text-ink">{{ JSON.stringify(part.output, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>
