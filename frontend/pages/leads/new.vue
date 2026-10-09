<script setup lang="ts">
import LeadWizard from "~/components/leads/LeadWizard.vue";

// New lead — the Lead Workspace wizard in create mode. All orchestration lives in
// LeadWizard, shared with the edit flow (pages/leads/[id]/edit.vue).
</script>

<template>
  <LeadWizard mode="create" />
</template>
