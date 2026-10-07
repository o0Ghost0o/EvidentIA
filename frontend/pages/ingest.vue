<script setup lang="ts">
import { onMounted, ref } from "vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import { api } from "~/composables/useApi";

const report = ref<Record<string, unknown> | null>(null);
const running = ref(false);
const useSeed = ref(true);
const error = ref("");

async function loadReport() {
  try {
    report.value = await api("ingest/quality-report");
  } catch {
    report.value = null;
  }
}

async function runIngest() {
  running.value = true;
  error.value = "";
  try {
    const res = await api<{ status: string; report?: Record<string, unknown> }>("ingest/run", {
      method: "POST",
      query: { sync: "true", use_seed: String(useSeed.value) },
    });
    if (res.report) report.value = res.report;
    else await loadReport();
  } catch (e) {
    error.value = "Falló la ingesta. Revisa el backend y los logs del worker.";
  } finally {
    running.value = false;
  }
}

onMounted(loadReport);
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-2xl font-bold">Ingesta y calidad</h1>
    <Card>
      <template #header>Ejecutar carga</template>
      <div class="flex items-center gap-3">
        <label class="flex items-center gap-2 text-sm">
          <input v-model="useSeed" type="checkbox" class="h-4 w-4" />
          Usar snapshot local (demo sin internet)
        </label>
        <Button :disabled="running" @click="runIngest">
          {{ running ? "Cargando…" : "Ejecutar ingesta" }}
        </Button>
      </div>
      <p v-if="error" class="mt-2 text-sm text-destructive">{{ error }}</p>
    </Card>
    <Card v-if="report">
      <template #header>Reporte de calidad</template>
      <div class="space-y-2 text-sm">
        <p>Fuente: <strong>{{ report.source }}</strong> · corte: {{ (report.manifest as Record<string,string>).fecha_corte_UTC }}</p>
        <ul class="list-disc pl-5">
          <li v-for="(fam, name) in (report.families as Record<string, Record<string, number>>)" :key="name">
            {{ name }}: {{ fam.valid }} válidas, {{ fam.dropped }} descartadas ({{ fam.error_count }} observaciones)
          </li>
        </ul>
        <div v-if="(report.warnings as string[]).length">
          <p class="font-medium">Advertencias:</p>
          <ul class="list-disc pl-5 text-muted-foreground">
            <li v-for="(w, i) in (report.warnings as string[])" :key="i">{{ w }}</li>
          </ul>
        </div>
      </div>
    </Card>
    <p v-else class="text-sm text-muted-foreground">Aún no hay reportes. Ejecuta una ingesta.</p>
  </div>
</template>
