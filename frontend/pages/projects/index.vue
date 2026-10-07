<script setup lang="ts">
import { onMounted, ref } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Input from "~/components/ui/Input.vue";
import { api } from "~/composables/useApi";

interface CaseItem {
  id: number;
  titulo: string;
  modalidad: string;
  estado: string;
  evidence: unknown[];
}

const cases = ref<CaseItem[]>([]);
const titulo = ref("");
const modalidad = ref("tvn");

async function refresh() {
  const res = await api<{ items: CaseItem[] }>("cases");
  cases.value = res.items;
}

async function createCase() {
  if (!titulo.value.trim()) return;
  await api("cases", { method: "POST", body: { titulo: titulo.value, modalidad: modalidad.value } });
  titulo.value = "";
  await refresh();
}

onMounted(refresh);
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-2xl font-bold">Proyectos de investigación</h1>
    <Card>
      <template #header>Nuevo proyecto</template>
      <div class="flex gap-2">
        <Input v-model="titulo" placeholder="Título del caso o tema" class="flex-1" />
        <select v-model="modalidad" class="h-9 rounded-md border bg-background px-3 text-sm">
          <option value="tvn">TVN</option>
          <option value="banca">Banca</option>
        </select>
        <Button @click="createCase">Crear</Button>
      </div>
    </Card>
    <div class="grid gap-3">
      <Card v-for="c in cases" :key="c.id">
        <div class="flex items-center justify-between">
          <div>
            <NuxtLink :to="`/projects/${c.id}`" class="font-medium hover:underline">
              {{ c.titulo }}
            </NuxtLink>
            <div class="mt-1 flex gap-1">
              <Badge variant="secondary">{{ c.modalidad }}</Badge>
              <Badge variant="outline">{{ c.estado }}</Badge>
              <Badge variant="outline">{{ c.evidence.length }} evidencia(s)</Badge>
            </div>
          </div>
          <NuxtLink :to="`/projects/${c.id}`">
            <Button variant="outline">Abrir</Button>
          </NuxtLink>
        </div>
      </Card>
    </div>
  </div>
</template>
