<script setup lang="ts">
import Badge from "~/components/ui/Badge.vue";
import Card from "~/components/ui/Card.vue";

defineProps<{
  brief: Record<string, unknown> | null;
}>();

const ORDER_TVN = [
  ["titulo_propuesto", "Título propuesto"],
  ["brief", "Brief"],
  ["enfoque", "Enfoque"],
  ["preguntas", "Preguntas"],
  ["fuentes_y_verificaciones", "Fuentes y pendientes"],
  ["guion", "Guion"],
  ["copy_digital", "Copy digital"],
] as const;

const ORDER_BANCA = [
  ["resumen", "Resumen"],
  ["sectores", "Sectores"],
  ["horizonte", "Horizonte"],
  ["evidencia", "Evidencia"],
  ["preguntas", "Preguntas"],
] as const;
</script>

<template>
  <Card>
    <template #header>Borrador</template>
    <p v-if="!brief" class="text-sm text-muted-foreground">Aún no se ha generado un borrador.</p>
    <div v-else-if="brief.abstained" class="rounded-md border border-destructive/50 bg-destructive/5 p-3 text-sm">
      <Badge variant="destructive">Abstención</Badge>
      <p class="mt-2">{{ brief.text }}</p>
    </div>
    <div v-else class="space-y-4 text-sm">
      <p class="rounded-md border bg-muted/50 p-2 text-xs">
        BORRADOR PARA REVISIÓN HUMANA — no publicar sin verificación.
        <span v-if="brief.titular_only">AVISO: basado únicamente en titular/metadatos.</span>
      </p>
      <div
        v-for="[key, label] in brief.modalidad === 'banca' ? ORDER_BANCA : ORDER_TVN"
        :key="key"
      >
        <h4 class="font-semibold">{{ label }}</h4>
        <p class="whitespace-pre-wrap text-muted-foreground">{{ brief[key] }}</p>
      </div>
      <p class="text-xs text-muted-foreground">
        Citas válidas: {{ brief.citations_valid }} · removidas: {{ (brief.citations_dropped as string[]).length }}
      </p>
    </div>
  </Card>
</template>
