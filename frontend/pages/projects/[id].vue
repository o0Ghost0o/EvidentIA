<script setup lang="ts">
// Backward compatibility: redirect /projects/:id to /leads/:id
const route = useRoute();
await navigateTo(`/leads/${route.params.id}`, { redirectCode: 301 });
</script>

<template>
  <div>Redirigiendo a Ficha de Lead…</div>
</template>
