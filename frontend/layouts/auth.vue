<script setup lang="ts">
import { onMounted } from "vue";
import { useAuth } from "~/composables/useAuth";

// Minimal full-screen shell for authentication pages — no app bar.
// Mirrors default.vue startup: restore session + persisted theme on mount.
const auth = useAuth();

onMounted(() => {
  auth.initAuth();
  let stored: string | null = null;
  try {
    stored = localStorage.getItem("ev-theme");
  } catch {
    /* storage may be unavailable */
  }
  document.documentElement.classList.toggle("dark", stored === "dark");
});
</script>

<template>
  <div class="min-h-screen bg-surface text-ink">
    <slot />
  </div>
</template>
