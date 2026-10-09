<script setup lang="ts">
import { ref } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Input from "~/components/ui/Input.vue";
import { useAuth } from "~/composables/useAuth";

definePageMeta({
  layout: "default",
});

const route = useRoute();
const auth = useAuth();

const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

function fillCreds(demoEmail: string, demoPass: string) {
  email.value = demoEmail;
  password.value = demoPass;
  error.value = "";
}

async function onSubmit() {
  if (!email.value.trim() || !password.value.trim()) {
    error.value = "Por favor ingresa tanto tu correo como tu contraseña.";
    return;
  }

  error.value = "";
  loading.value = true;

  try {
    await auth.login(email.value.trim(), password.value);
    const target = (route.query.redirect as string) || "/";
    await navigateTo(target);
  } catch (err: any) {
    error.value = err?.data?.detail || "Credenciales incorrectas o usuario inactivo.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-[75vh] items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="w-full max-w-md space-y-8 animate-in fade-in zoom-in-95 duration-200">
      <div class="text-center space-y-2">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border bg-muted/30 text-xs font-medium">
          <span>🛡️</span>
          <span>Acceso Restringido</span>
          <Badge variant="outline" class="text-[10px]">Dual JWT</Badge>
        </div>
        <h1 class="text-3xl font-extrabold tracking-tight">EvidentIA</h1>
        <p class="text-sm text-muted-foreground">
          Plataforma de inteligencia informativa y verificación trazable. Inicia sesión con tus credenciales institucionales.
        </p>
      </div>

      <Card class="shadow-lg border-border/80">
        <template #header>
          <div class="text-sm font-semibold text-center text-foreground">
            Iniciar Sesión
          </div>
        </template>

        <form class="space-y-4" @submit.prevent="onSubmit">
          <div class="space-y-1">
            <label class="text-xs font-semibold text-foreground/90">Correo Electrónico</label>
            <Input
              v-model="email"
              type="email"
              placeholder="admin@tvn.com"
              required
              autocomplete="email"
              class="h-10"
            />
          </div>

          <div class="space-y-1">
            <div class="flex items-center justify-between">
              <label class="text-xs font-semibold text-foreground/90">Contraseña</label>
            </div>
            <Input
              v-model="password"
              type="password"
              placeholder="••••••••••••"
              required
              autocomplete="current-password"
              class="h-10"
            />
          </div>

          <!-- Acceso Rápido para Auditoría de Jurado (RBAC) -->
          <div class="rounded-lg border border-border/70 bg-muted/20 p-3 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-semibold text-foreground flex items-center gap-1.5">
                <span>🔑</span> Cuentas Demo Oficiales (Jurado / RBAC)
              </span>
              <Badge variant="outline" class="text-[9px]">1-Click</Badge>
            </div>
            <div class="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                @click="fillCreds('admin@tvn.com', 'EvidentIA2026!')"
                class="flex flex-col items-center justify-center p-2 rounded-md border text-center transition-all hover:bg-muted/60 active:scale-95"
                :class="email === 'admin@tvn.com' ? 'border-primary bg-primary/10 text-primary font-medium ring-1 ring-primary/40' : 'border-border/60 text-muted-foreground'"
              >
                <span class="text-[11px] font-semibold leading-tight">Super Admin</span>
                <span class="text-[9px] opacity-75">Jurado (T01-T10)</span>
              </button>
              <button
                type="button"
                @click="fillCreds('editor@tvn.com', 'EvidentIA2026!')"
                class="flex flex-col items-center justify-center p-2 rounded-md border text-center transition-all hover:bg-muted/60 active:scale-95"
                :class="email === 'editor@tvn.com' ? 'border-primary bg-primary/10 text-primary font-medium ring-1 ring-primary/40' : 'border-border/60 text-muted-foreground'"
              >
                <span class="text-[11px] font-semibold leading-tight">Editor Jefe</span>
                <span class="text-[9px] opacity-75">Owner (Inbox/Aprob.)</span>
              </button>
              <button
                type="button"
                @click="fillCreds('periodista@tvn.com', 'EvidentIA2026!')"
                class="flex flex-col items-center justify-center p-2 rounded-md border text-center transition-all hover:bg-muted/60 active:scale-95"
                :class="email === 'periodista@tvn.com' ? 'border-primary bg-primary/10 text-primary font-medium ring-1 ring-primary/40' : 'border-border/60 text-muted-foreground'"
              >
                <span class="text-[11px] font-semibold leading-tight">Periodista</span>
                <span class="text-[9px] opacity-75">Member (Leads/Grafo)</span>
              </button>
            </div>
          </div>

          <div v-if="error" class="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-start gap-2">
            <span>⚠️</span>
            <span>{{ error }}</span>
          </div>

          <Button type="submit" class="w-full h-10 font-semibold" :disabled="loading">
            {{ loading ? "Verificando credenciales…" : "Acceder a EvidentIA" }}
          </Button>

          <p class="text-[11px] text-center text-muted-foreground pt-2">
            Sesión segura protegida con tokens criptográficos de rotación anti-replay.
          </p>
        </form>
      </Card>
    </div>
  </div>
</template>
