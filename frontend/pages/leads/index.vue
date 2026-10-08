<script setup lang="ts">
import { onMounted, ref } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Input from "~/components/ui/Input.vue";
import FlagBadges, { type ActivityFlag } from "~/components/FlagBadges.vue";
import { api } from "~/composables/useApi";

interface CaseItem {
  id: number;
  titulo: string;
  modalidad: string;
  estado: string;
  flags: string[];
  activity_flags: ActivityFlag[];
  evidence: unknown[];
}

const cases = ref<CaseItem[]>([]);
const titulo = ref("");
const modalidad = ref("tvn");
const initialFlag = ref("");
const loading = ref(true);

async function refresh() {
  loading.value = true;
  try {
    const res = await api<{ items: CaseItem[] }>("cases");
    cases.value = res.items;
  } finally {
    loading.value = false;
  }
}

async function createLead() {
  if (!titulo.value.trim()) return;
  const flags = initialFlag.value.trim() ? [initialFlag.value.trim()] : [];
  const res = await api<CaseItem>("cases", {
    method: "POST",
    body: { titulo: titulo.value, modalidad: modalidad.value, flags },
  });
  titulo.value = "";
  initialFlag.value = "";
  await navigateTo(`/leads/${res.id}`);
}

onMounted(refresh);
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Leads — Fichas de Evidencia</h1>
        <p class="text-sm text-muted-foreground mt-0.5">
          Gestión jerárquica de fichas de investigación, correlación de fuentes y trazabilidad determinista.
        </p>
      </div>
      <NuxtLink to="/leads/new">
        <Button variant="outline">+ Nuevo lead</Button>
      </NuxtLink>
    </div>

    <!-- Create Lead Card -->
    <Card>
      <template #header>
        <div class="flex items-center gap-2">
          <span>Crear nuevo lead</span>
          <Badge variant="outline" class="text-xs">Nueva ficha</Badge>
        </div>
      </template>
      <div class="space-y-3">
        <div class="flex flex-wrap gap-2">
          <Input
            v-model="titulo"
            placeholder="Título del lead o tema a investigar (ej. Expansión Puerto de Colón)"
            class="flex-1 min-w-[240px]"
            @keyup.enter="createLead"
          />
          <select
            v-model="modalidad"
            class="h-9 rounded-md border bg-background px-3 text-sm focus:outline-hidden"
          >
            <option value="tvn">TVN (Editorial)</option>
            <option value="banca">Banca (Entorno)</option>
          </select>
          <Input
            v-model="initialFlag"
            placeholder="Flag opcional (ej. Prioritario)"
            class="w-44 text-sm"
            @keyup.enter="createLead"
          />
          <Button @click="createLead">Crear Lead</Button>
        </div>
        <p class="text-xs text-muted-foreground">
          Cada lead crea una ficha de evidencia que agrupa noticias, indicadores, eventos y su grafo jerárquico.
        </p>
      </div>
    </Card>

    <!-- Leads List -->
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Fichas registradas ({{ cases.length }})
        </h2>
      </div>

      <p v-if="loading" class="text-sm text-muted-foreground py-4 text-center">
        Cargando leads…
      </p>
      <p v-else-if="!cases.length" class="text-sm text-muted-foreground py-6 text-center border rounded-md">
        No hay leads creados aún. Crea el primero arriba o ábrelo desde la Bandeja.
      </p>

      <div v-else class="grid gap-3">
        <Card v-for="c in cases" :key="c.id" class="transition-shadow hover:shadow-xs">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <NuxtLink :to="`/leads/${c.id}`" class="font-semibold text-base hover:underline text-foreground">
                  {{ c.titulo }}
                </NuxtLink>
                <span class="text-xs font-mono text-muted-foreground">#{{ c.id }}</span>
              </div>

              <!-- Base badges -->
              <div class="flex flex-wrap items-center gap-1.5">
                <Badge variant="secondary" class="uppercase text-[11px] font-mono">
                  {{ c.modalidad }}
                </Badge>
                <Badge variant="outline" class="text-[11px]">
                  {{ c.estado }}
                </Badge>
                <Badge variant="outline" class="text-[11px]">
                  {{ c.evidence.length }} ficha(s) de evidencia
                </Badge>
              </div>

              <!-- Activity & Custom Flag Badges -->
              <div v-if="c.activity_flags && c.activity_flags.length" class="pt-1">
                <FlagBadges :flags="c.activity_flags" compact />
              </div>
            </div>

            <div class="flex items-center gap-2 self-start md:self-center">
              <NuxtLink :to="`/leads/${c.id}`">
                <Button variant="outline" size="sm">Abrir Lead</Button>
              </NuxtLink>
            </div>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>
