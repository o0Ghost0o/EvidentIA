<script setup lang="ts">
import { onMounted, ref } from "vue";
import AuthModal from "~/components/AuthModal.vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import { useAuth } from "~/composables/useAuth";

const auth = useAuth();
const showAuthModal = ref(false);

onMounted(() => {
  auth.initAuth();
});
</script>

<template>
  <div class="min-h-screen">
    <header class="border-b">
      <nav class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <div class="flex items-center gap-6">
          <NuxtLink to="/" class="text-lg font-bold">EvidentIA</NuxtLink>
          <NuxtLink to="/" class="text-sm text-muted-foreground hover:text-foreground">Bandeja</NuxtLink>
          <NuxtLink to="/leads" class="text-sm text-muted-foreground hover:text-foreground">Leads</NuxtLink>
          <NuxtLink to="/ingest" class="text-sm text-muted-foreground hover:text-foreground">Ingesta</NuxtLink>
        </div>

        <!-- Security / Auth session status -->
        <div class="flex items-center gap-3">
          <div
            v-if="auth.isAuthenticated.value && auth.user.value"
            class="flex items-center gap-2 cursor-pointer rounded-full border bg-muted/40 px-3 py-1 hover:bg-muted transition-colors"
            @click="showAuthModal = true"
          >
            <span class="text-xs font-medium">{{ auth.user.value.email }}</span>
            <Badge variant="outline" class="text-[10px] font-semibold py-0">
              {{ auth.user.value.role }}
            </Badge>
          </div>
          <Button
            v-else
            variant="outline"
            size="sm"
            class="h-8 text-xs flex items-center gap-1.5"
            @click="showAuthModal = true"
          >
            <span>🔒</span>
            <span>Seguridad & Login</span>
          </Button>
        </div>
      </nav>
    </header>
    <main class="mx-auto max-w-5xl px-4 py-6">
      <slot />
    </main>

    <AuthModal v-model="showAuthModal" />
  </div>
</template>
