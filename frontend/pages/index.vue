<script setup lang="ts">
import { onMounted, ref } from "vue";
import RankingTable, { type RankItem } from "~/components/RankingTable.vue";
import { api } from "~/composables/useApi";

const items = ref<RankItem[]>([]);
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  try {
    const res = await api<{ items: RankItem[] }>("ranking", { query: { modalidad: "tvn" } });
    items.value = res.items;
  } catch (e) {
    error.value = "No se pudo cargar el ranking. ¿Está corriendo el backend?";
  } finally {
    loading.value = false;
  }
});

async function openProject(item: RankItem) {
  const created = await api<{ id: number }>("cases", {
    method: "POST",
    body: { titulo: item.titulo, modalidad: "tvn", queries: [item.titulo] },
  });
  await navigateTo(`/projects/${created.id}`);
}
</script>

<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-2xl font-bold">Bandeja de temas</h1>
      <p class="text-sm text-muted-foreground">
        Priorización determinista con evidencia trazable. Cada fila puede abrirse como proyecto.
      </p>
    </div>
    <p v-if="error" class="rounded-md border border-destructive/50 p-3 text-sm">{{ error }}</p>
    <RankingTable :items="items" :loading="loading" @open="openProject" />
  </div>
</template>
