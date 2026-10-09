<script setup lang="ts">
import { ref } from "vue";
import LeadWizard from "~/components/leads/LeadWizard.vue";
import { api } from "~/composables/useApi";
import { seedFromDetail, type ScoreResponse, type SeedDetail, type WizardSeed } from "~/lib/leadWizard";

// Edit lead — loads an existing case and runs the shared Lead Workspace wizard
// pre-filled with its data. Step 1 PATCHes the case; later steps self-persist as
// in the create flow. Reached from the read-only ficha's "Editar" button.

const route = useRoute();
const id = route.params.id as string;

const seed = ref<WizardSeed | null>(null);

onMounted(async () => {
  const detail = await api<SeedDetail>(`cases/${id}`);
  let score: ScoreResponse | null = null;
  try {
    score = await api<ScoreResponse>(`cases/${id}/score`);
  } catch {
    score = null;
  }
  seed.value = seedFromDetail(detail, score);
});
</script>

<template>
  <LeadWizard v-if="seed" mode="edit" :lead-id="seed.leadId" :seed="seed" />
  <div v-else class="py-12 text-center text-body-sm text-ink-muted">Cargando ficha del lead…</div>
</template>
