<script setup lang="ts">
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";

export interface RankItem {
  id: string;
  titulo: string;
  P: number;
  band: string;
  components: Record<string, number>;
  evidence_state: string;
  group_size: number;
  dedup: { label: string; primary_sources: number; agency: string | null };
  ids_fuente: string[];
}

defineProps<{ items: RankItem[]; loading: boolean }>();
const emit = defineEmits<{ open: [item: RankItem] }>();

function bandVariant(band: string) {
  return band === "alto" ? "destructive" : band === "medio" ? "default" : "secondary";
}
</script>

<template>
  <Card>
    <template #header>Bandeja priorizada</template>
    <p v-if="loading" class="text-sm text-muted-foreground">Cargando ranking…</p>
    <p v-else-if="!items.length" class="text-sm text-muted-foreground">
      Sin temas. Ejecuta una ingesta primero.
    </p>
    <ul v-else class="divide-y">
      <li v-for="item in items" :key="item.id" class="flex items-start justify-between gap-4 py-3">
        <div>
          <p class="font-medium">{{ item.titulo }}</p>
          <p class="mt-1 text-xs text-muted-foreground">
            P={{ item.P }} (R={{ item.components.R }} I={{ item.components.I }} U={{
              item.components.U
            }} N={{ item.components.N }} E={{ item.components.E }}) · {{ item.group_size }} notas ·
            {{ item.dedup.primary_sources }} fuente(s) · {{ item.dedup.label }}
          </p>
          <div class="mt-1 flex gap-1">
            <Badge :variant="bandVariant(item.band)">{{ item.band }}</Badge>
            <Badge variant="outline">evidencia: {{ item.evidence_state }}</Badge>
          </div>
        </div>
        <Button variant="outline" @click="emit('open', item)">Abrir Lead</Button>
      </li>
    </ul>
  </Card>
</template>
