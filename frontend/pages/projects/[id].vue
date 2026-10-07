<script setup lang="ts">
import { onMounted, ref } from "vue";
import BriefView from "~/components/BriefView.vue";
import EvidenceTree, { type EvidenceTreeData } from "~/components/EvidenceTree.vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Input from "~/components/ui/Input.vue";
import Textarea from "~/components/ui/Textarea.vue";
import { api } from "~/composables/useApi";

const route = useRoute();
const id = route.params.id as string;

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
  evidence: EvidenceItem[];
  notes: { id: number; autor: string; estado_revision: string; texto: string }[];
}

const detail = ref<CaseDetail | null>(null);
const tree = ref<EvidenceTreeData | null>(null);
const brief = ref<Record<string, unknown> | null>(null);
const generating = ref(false);

const evTipo = ref("news");
const evId = ref("");
const evNota = ref("");
const noteAutor = ref("");
const noteEstado = ref("en_revision");
const noteTexto = ref("");

async function refresh() {
  detail.value = await api<CaseDetail>(`cases/${id}`);
  tree.value = await api<EvidenceTreeData>(`cases/${id}/tree`);
}

async function addEvidence() {
  if (!evId.value.trim()) return;
  await api(`cases/${id}/evidence`, {
    method: "POST",
    body: { fuente_tipo: evTipo.value, fuente_id: evId.value.trim(), nota: evNota.value || null },
  });
  evId.value = "";
  evNota.value = "";
  await refresh();
}

async function removeEvidence(evidenceId: number) {
  await api(`cases/${id}/evidence/${evidenceId}`, { method: "DELETE" });
  await refresh();
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
  a.download = `caso-${id}-brief.md`;
  a.click();
  URL.revokeObjectURL(a.href);
}

onMounted(refresh);
</script>

<template>
  <div v-if="detail" class="space-y-4">
    <div>
      <h1 class="text-2xl font-bold">{{ detail.titulo }}</h1>
      <div class="mt-1 flex gap-1">
        <Badge variant="secondary">{{ detail.modalidad }}</Badge>
        <Badge variant="outline">{{ detail.estado }}</Badge>
      </div>
    </div>

    <EvidenceTree :tree="tree" />

    <Card>
      <template #header>Evidencia vinculada ({{ detail.evidence.length }})</template>
      <ul class="space-y-2 text-sm">
        <li v-for="e in detail.evidence" :key="e.id" class="flex items-center justify-between gap-2">
          <span>
            <Badge variant="outline">{{ e.fuente_tipo }}</Badge>
            <span class="ml-2 font-mono text-xs">{{ e.fuente_id }}</span>
            <span v-if="e.nota" class="ml-2 text-muted-foreground">— {{ e.nota }}</span>
            <span v-if="e.marcado_manual" class="ml-2 text-xs text-muted-foreground">(manual)</span>
          </span>
          <Button variant="outline" @click="removeEvidence(e.id)">Quitar</Button>
        </li>
      </ul>
      <div class="mt-3 flex gap-2">
        <select v-model="evTipo" class="h-9 rounded-md border bg-background px-3 text-sm">
          <option value="news">news</option>
          <option value="indicator">indicator</option>
          <option value="event">event</option>
        </select>
        <Input v-model="evId" placeholder="id_noticia / PAIS:IND:AÑO / event_id" class="flex-1" />
        <Input v-model="evNota" placeholder="nota (opcional)" class="flex-1" />
        <Button @click="addEvidence">Vincular</Button>
      </div>
    </Card>

    <Card>
      <template #header>Borrador ({{ detail.modalidad }})</template>
      <div class="mb-3 flex gap-2">
        <Button :disabled="generating" @click="generateBrief">
          {{ generating ? "Generando…" : "Generar borrador" }}
        </Button>
        <Button variant="outline" @click="downloadMarkdown">Descargar Markdown</Button>
      </div>
      <BriefView :brief="brief" />
    </Card>

    <Card>
      <template #header>Revisión humana ({{ detail.notes.length }})</template>
      <ul class="mb-3 space-y-2 text-sm">
        <li v-for="n in detail.notes" :key="n.id">
          <Badge variant="outline">{{ n.estado_revision }}</Badge>
          <span class="ml-2 font-medium">{{ n.autor }}</span>
          <span class="ml-2 text-muted-foreground">{{ n.texto }}</span>
        </li>
      </ul>
      <div class="flex gap-2">
        <Input v-model="noteAutor" placeholder="tu nombre" class="w-40" />
        <select v-model="noteEstado" class="h-9 rounded-md border bg-background px-3 text-sm">
          <option value="en_revision">en revisión</option>
          <option value="requiere_evidencia">requiere evidencia</option>
          <option value="aprobado_borrador">aprobado como borrador</option>
          <option value="descartado">descartado</option>
        </select>
        <Input v-model="noteTexto" placeholder="nota de revisión" class="flex-1" />
        <Button @click="addNote">Registrar</Button>
      </div>
    </Card>
  </div>
  <p v-else class="text-sm text-muted-foreground">Cargando proyecto…</p>
</template>
