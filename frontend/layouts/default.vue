<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import AuthModal from "~/components/AuthModal.vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import { useAuth } from "~/composables/useAuth";

const route = useRoute();
const auth = useAuth();
const showAuthModal = ref(false);

const isLoginPage = computed(() => route.path === "/login");

onMounted(() => {
  auth.initAuth();
});

async function handleLogout() {
  await auth.logout();
  await navigateTo("/login");
}
</script>

<template>
  <div class="min-h-screen">
    <header class="border-b">
      <nav class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <div class="flex items-center gap-6">
          <NuxtLink to="/" class="text-lg font-bold">EvidentIA</NuxtLink>
          <template v-if="!isLoginPage && auth.isAuthenticated.value">
            <NuxtLink to="/" class="text-sm text-muted-foreground hover:text-foreground">Bandeja</NuxtLink>
            <NuxtLink to="/leads" class="text-sm text-muted-foreground hover:text-foreground">Leads</NuxtLink>
            <NuxtLink to="/ingest" class="text-sm text-muted-foreground hover:text-foreground">Ingesta</NuxtLink>
          </template>
        </div>

        <!-- Security / Auth session status -->
        <div class="flex items-center gap-3">
          <template v-if="!isLoginPage && auth.isAuthenticated.value && auth.user.value">
            <div
              class="flex items-center gap-2 cursor-pointer rounded-full border bg-muted/40 px-3 py-1 hover:bg-muted transition-colors"
              title="Ver detalles de sesión"
              @click="showAuthModal = true"
            >
              <span class="text-xs font-medium">{{ auth.user.value.email }}</span>
              <Badge variant="outline" class="text-[10px] font-semibold py-0">
                {{ auth.user.value.role }}
              </Badge>
            </div>
            <Button
              variant="outline"
              size="sm"
              class="h-8 text-xs text-muted-foreground hover:text-destructive hover:bg-destructive/10"
              @click="handleLogout"
            >
              <span>Cerrar Sesión</span>
            </Button>
          </template>
          <NuxtLink
            v-else-if="!isLoginPage"
            to="/login"
            class="text-xs font-semibold text-primary hover:underline"
          >
            Iniciar Sesión →
          </NuxtLink>
        </div>
      </nav>
    </header>
    <main class="mx-auto max-w-5xl px-4 py-6">
      <slot />
    </main>

    <AuthModal v-model="showAuthModal" />
  </div>
</template>
