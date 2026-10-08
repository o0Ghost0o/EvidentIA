<script setup lang="ts">
import { onMounted, ref } from "vue";
import BriefView from "~/components/BriefView.vue";
import EvidenceTree, { type EvidenceTreeData } from "~/components/EvidenceTree.vue";
import FlagBadges, { type ActivityFlag } from "~/components/FlagBadges.vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Input from "~/components/ui/Input.vue";
import EvidenceDetailModal from "~/components/EvidenceDetailModal.vue";
import { api } from "~/composables/useApi";

const route = useRoute();
const id = route.params.id as string;

const activeEvidenceModal = ref(false);
const activeEvidenceTarget = ref<{ tipo: string; id: string } | null>(null);

function inspectEvidence(tipo: string, idVal: string) {
  activeEvidenceTarget.value = { tipo, id: idVal };
  activeEvidenceModal.value = true;
}

interface EvidenceItem {
  id: number;
  fuente_tipo: string;
  fuente_id: string;
  rol: string;
  nota: string | null;
  marcado_manual: boolean;
}

interface CaseDetail {
  id: number;
  titulo: string;
  modalidad: string;
  estado: string;
  queries: string[];
  flags: string[];
  activity_flags: ActivityFlag[];
  evidence: EvidenceItem[];
  notes: { id: number; autor: string; estado_revision: string; texto: string; created_at: string }[];
}

const detail = ref<CaseDetail | null>(null);
const tree = ref<EvidenceTreeData | null>(null);
const brief = ref<Record<string, unknown> | null>(null);
const generating = ref(false);
const treeLoading = ref(false);

// Default hierarchy depth: 5 levels
const currentDepth = ref(5);

const evTipo = ref("news");
const evId = ref("");
const evNota = ref("");
const noteAutor = ref("");
const noteEstado = ref("en_revision");
const noteTexto = ref("");

async function refreshDetail() {
  detail.value = await api<CaseDetail>(`cases/${id}`);
}

async function refreshTree(depth: number = currentDepth.value) {
  treeLoading.value = true;
  try {
    currentDepth.value = depth;
    tree.value = await api<EvidenceTreeData>(`cases/${id}/tree`, {
      query: { depth: String(depth) },
    });
  } finally {
    treeLoading.value = false;
  }
}

async function refresh() {
  await Promise.all([refreshDetail(), refreshTree(currentDepth.value)]);
}

async function onDepthChange(newDepth: number) {
  await refreshTree(newDepth);
}

async function addEvidence() {
  if (!evId.value.trim()) return;
  await api(`cases/${id}/evidence`, {
    method: "POST",
    body: {
      fuente_tipo: evTipo.value,
      fuente_id: evId.value.trim(),
      nota: evNota.value || null,
      marcado_manual: true,
    },
  });
  evId.value = "";
  evNota.value = "";
  await refresh();
}

async function removeEvidence(evidenceId: number) {
  await api(`cases/${id}/evidence/${evidenceId}`, { method: "DELETE" });
  await refresh();
}

async function addCustomFlag(flagName: string) {
  const updated = await api<CaseDetail>(`cases/${id}/flags`, {
    method: "POST",
    body: { flag: flagName },
  });
  detail.value = updated;
}

async function removeCustomFlag(flagName: string) {
  const updated = await api<CaseDetail>(`cases/${id}/flags/${encodeURIComponent(flagName)}`, {
    method: "DELETE",
  });
  detail.value = updated;
}

async function updateStatus(newStatus: string) {
  if (!detail.value) return;
  const updated = await api<CaseDetail>(`cases/${id}`, {
    method: "PATCH",
    body: { estado: newStatus },
  });
  detail.value = updated;
}

async function addNote() {
  if (!noteAutor.value.trim() || !noteTexto.value.trim()) return;
  await api(`cases/${id}/notes`, {
    method: "POST",
    body: { autor: noteAutor.value, estado_revision: noteEstado.value, texto: noteTexto.value },
  });
  noteTexto.value = "";
  await refresh();
}

async function generateBrief() {
  generating.value = true;
  try {
    brief.value = await api(`cases/${id}/brief`, { method: "POST" });
  } finally {
    generating.value = false;
  }
}

async function downloadMarkdown() {
  const res = await fetch(`/api/cases/${id}/brief?formato=markdown`, { method: "POST" });
  const text = await res.text();
  const blob = new Blob([text], { type: "text/markdown" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `lead-${id}-ficha.md`;
  a.click();
  URL.revokeObjectURL(a.href);
}

onMounted(refresh);
</script>

<template>
  <div v-if="detail" class="space-y-6">
    <!-- Header -->
    <div class="space-y-2">
      <div class="flex items-center gap-2 text-xs text-muted-foreground">
        <NuxtLink to="/leads" class="hover:underline flex items-center gap-1">
          <span>← Volver a Leads</span>
        </NuxtLink>
        <span>/</span>
        <span class="font-mono">Ficha #{{ detail.id }}</span>
      </div>

      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-foreground">{{ detail.titulo }}</h1>
          <div class="mt-2 flex flex-wrap items-center gap-2">
            <Badge variant="secondary" class="uppercase font-mono text-xs">
              Modalidad: {{ detail.modalidad }}
            </Badge>

            <!-- Quick Status Select -->
            <div class="flex items-center gap-1.5 text-xs">
              <span class="text-muted-foreground">Estado:</span>
              <select
                :value="detail.estado"
                class="h-7 rounded border bg-background px-2 text-xs font-medium focus:outline-hidden"
                @change="updateStatus(($event.target as HTMLSelectElement).value)"
              >
                <option value="nuevo">nuevo</option>
                <option value="en_revision">en revisión</option>
                <option value="requiere_evidencia">requiere evidencia</option>
                <option value="aprobado_borrador">aprobado como borrador</option>
                <option value="descartado">descartado</option>
              </select>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <Button variant="outline" size="sm" @click="downloadMarkdown">
            Exportar Ficha (.md)
          </Button>
        </div>
      </div>
    </div>

    <!-- Flags & Client Activity Badges Card -->
    <Card>
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="font-semibold text-sm">Flags y Actividades del Lead / Cliente</span>
            <Badge variant="outline" class="text-xs">Trazabilidad</Badge>
          </div>
          <span class="text-xs text-muted-foreground">
            Badges asociados a las acciones del cliente y el estado del lead
          </span>
        </div>
      </template>

      <div class="space-y-3">
        <FlagBadges
          :flags="detail.activity_flags || []"
          :custom-flags="detail.flags || []"
          :editable="true"
          @add-flag="addCustomFlag"
          @remove-flag="removeCustomFlag"
        />
      </div>
    </Card>

    <!-- Hierarchical Evidence Tree (5 default levels with user controls) -->
    <EvidenceTree
      :tree="tree"
      :depth="currentDepth"
      :loading="treeLoading"
      @change-depth="onDepthChange"
    />

    <!-- Linked Evidence Items (Fichas vinculadas) -->
    <Card>
      <template #header>
        <div class="flex items-center justify-between">
          <span>Fichas de Evidencia vinculadas ({{ detail.evidence.length }})</span>
          <span class="text-xs text-muted-foreground">Fuentes primarias y secundarias</span>
        </div>
      </template>

      <div class="space-y-4">
        <div v-if="!detail.evidence.length" class="text-sm text-muted-foreground py-2">
          No hay fichas de evidencia vinculadas directamente a este lead aún. Agrega una abajo.
        </div>

        <ul v-else class="divide-y text-sm">
          <li
            v-for="e in detail.evidence"
            :key="e.id"
            class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 py-2.5"
          >
            <div class="flex flex-wrap items-center gap-2">
              <Badge
                :variant="e.fuente_tipo === 'news' ? 'info' : e.fuente_tipo === 'indicator' ? 'teal' : 'warning'"
                class="text-xs"
              >
                {{ e.fuente_tipo }}
              </Badge>
              <button
                type="button"
                class="font-mono text-xs font-semibold bg-muted/60 hover:bg-primary/10 hover:text-primary px-1.5 py-0.5 rounded transition-colors text-left cursor-pointer"
                :title="`Inspeccionar contenido de ${e.fuente_id}`"
                @click="inspectEvidence(e.fuente_tipo, e.fuente_id)"
              >
                {{ e.fuente_id }}
              </button>
              <span v-if="e.nota" class="text-muted-foreground text-xs italic">
                — {{ e.nota }}
              </span>
              <Badge v-if="e.marcado_manual" variant="purple" class="text-[10px] px-1 py-0">
                manual
              </Badge>
            </div>
            <div class="flex items-center gap-1.5 self-end sm:self-auto">
              <Button
                variant="outline"
                size="sm"
                class="h-7 text-xs gap-1"
                @click="inspectEvidence(e.fuente_tipo, e.fuente_id)"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <span>Ver contenido</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                class="h-7 text-xs text-destructive hover:text-destructive"
                @click="removeEvidence(e.id)"
              >
                Quitar
              </Button>
            </div>
          </li>
        </ul>

        <!-- Form to link new evidence -->
        <div class="border-t pt-4">
          <h4 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
            Vincular nueva ficha de evidencia
          </h4>
          <div class="flex flex-wrap gap-2">
            <select
              v-model="evTipo"
              class="h-9 rounded-md border bg-background px-3 text-sm focus:outline-hidden"
            >
              <option value="news">news (noticia)</option>
              <option value="indicator">indicator (banco mundial)</option>
              <option value="event">event (sismo USGS)</option>
            </select>
            <Input
              v-model="evId"
              placeholder="id_noticia / PAIS:IND:AÑO / event_id"
              class="flex-1 min-w-[200px]"
              @keyup.enter="addEvidence"
            />
            <Input
              v-model="evNota"
              placeholder="nota o rol analítico (opcional)"
              class="flex-1 min-w-[180px]"
              @keyup.enter="addEvidence"
            />
            <Button size="sm" @click="addEvidence">Vincular</Button>
          </div>
        </div>
      </div>
    </Card>

    <!-- Synthesis Draft Brief -->
    <Card>
      <template #header>
        <div class="flex items-center justify-between">
          <span>Borrador de Síntesis ({{ detail.modalidad }})</span>
          <span class="text-xs text-muted-foreground">Generación controlada con trazabilidad</span>
        </div>
      </template>

      <div class="mb-4 flex flex-wrap gap-2">
        <Button :disabled="generating" @click="generateBrief">
          {{ generating ? "Generando borrador…" : "Generar borrador de ficha" }}
        </Button>
        <Button variant="outline" @click="downloadMarkdown">
          Descargar Markdown
        </Button>
      </div>

      <BriefView :brief="brief" />
    </Card>

    <!-- Human Review Notes & Traceability -->
    <Card>
      <template #header>
        <div class="flex items-center justify-between">
          <span>Revisión humana y trazabilidad ({{ detail.notes.length }})</span>
          <span class="text-xs text-muted-foreground">Bitácora auditable de decisiones</span>
        </div>
      </template>

      <div class="space-y-4">
        <ul v-if="detail.notes.length" class="space-y-2 text-sm">
          <li
            v-for="n in detail.notes"
            :key="n.id"
            class="rounded border bg-muted/20 p-2.5 space-y-1"
          >
            <div class="flex items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <Badge variant="outline" class="text-xs">{{ n.estado_revision }}</Badge>
                <span class="font-semibold text-xs">{{ n.autor }}</span>
              </div>
              <span v-if="n.created_at" class="text-[11px] text-muted-foreground">
                {{ new Date(n.created_at).toLocaleString() }}
              </span>
            </div>
            <p class="text-xs text-muted-foreground pl-1">{{ n.texto }}</p>
          </li>
        </ul>
        <p v-else class="text-xs text-muted-foreground">
          Sin revisiones registradas. Registra la primera evaluación del analista abajo.
        </p>

        <!-- Form to add audit note -->
        <div class="border-t pt-3 flex flex-wrap gap-2">
          <Input v-model="noteAutor" placeholder="Tu nombre / rol" class="w-40 text-sm" />
          <select
            v-model="noteEstado"
            class="h-9 rounded-md border bg-background px-3 text-sm focus:outline-hidden"
          >
            <option value="en_revision">en revisión</option>
            <option value="requiere_evidencia">requiere evidencia</option>
            <option value="aprobado_borrador">aprobado como borrador</option>
            <option value="descartado">descartado</option>
          </select>
          <Input
            v-model="noteTexto"
            placeholder="Nota de revisión analítica…"
            class="flex-1 min-w-[220px] text-sm"
            @keyup.enter="addNote"
          />
          <Button size="sm" @click="addNote">Registrar</Button>
        </div>
      </div>
    </Card>

    <!-- Evidence detail interactive modal -->
    <EvidenceDetailModal
      v-model:open="activeEvidenceModal"
      :tipo="activeEvidenceTarget?.tipo"
      :id="activeEvidenceTarget?.id"
      @navigate="(t, i) => { activeEvidenceTarget = { tipo: t, id: i }; activeEvidenceModal = true; }"
    />
  </div>
  <div v-else class="py-12 text-center text-sm text-muted-foreground">
    Cargando ficha del lead…
  </div>
</template>
