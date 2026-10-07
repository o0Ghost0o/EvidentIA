<script setup lang="ts">
// Backward compatibility: redirect /projects to /leads
await navigateTo("/leads", { redirectCode: 301 });
</script>

<template>
  <div>Redirigiendo a Leads…</div>
</template>
