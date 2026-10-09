<script setup lang="ts">
import { ref } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Card from "~/components/ui/Card.vue";
import Input from "~/components/ui/Input.vue";
import { useAuth } from "~/composables/useAuth";

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ (e: "update:modelValue", val: boolean): void }>();

const email = ref("");
const password = ref("");
const error = ref("");
const successMsg = ref("");
const loading = ref(false);

function fillCreds(demoEmail: string, demoPass: string) {
  email.value = demoEmail;
  password.value = demoPass;
  error.value = "";
  successMsg.value = "";
}

async function handleLogin() {
  error.value = "";
  successMsg.value = "";
  loading.value = true;
  try {
    await auth.login(email.value, password.value);
    successMsg.value = "Sesión iniciada exitosamente con tokens duales (15m / 7d).";
  } catch (err: any) {
    error.value = err?.data?.detail || "Error al iniciar sesión. Revisa las credenciales.";
  } finally {
    loading.value = false;
  }
}

async function handleRefresh() {
  error.value = "";
  successMsg.value = "";
  loading.value = true;
  try {
    const ok = await auth.refreshSession();
    if (ok) {
      successMsg.value = "¡Token rotado exitosamente! Nuevo access token (15m) y refresh token (7d) emitidos.";
    } else {
      error.value = "No se pudo rotar el token.";
    }
  } catch (err: any) {
    error.value = err?.data?.detail || "Error al rotar token.";
  } finally {
    loading.value = false;
  }
}

async function handleLogout() {
  await auth.logout();
  successMsg.value = "Sesión cerrada.";
}

function close() {
  emit("update:modelValue", false);
}
</script>

<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
    @click.self="close"
  >
    <div class="w-full max-w-md animate-in fade-in zoom-in-95 duration-150">
      <Card>
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="font-bold text-base">Capa de Seguridad & Sesión</span>
              <Badge variant="outline" class="text-xs">Dual JWT</Badge>
            </div>
            <button
              type="button"
              class="text-muted-foreground hover:text-foreground text-sm font-bold"
              @click="close"
            >
              ✕
            </button>
          </div>
        </template>

        <div class="space-y-4">
          <!-- Active Session View -->
          <div v-if="auth.isAuthenticated.value && auth.user.value" class="space-y-3">
            <div class="rounded-md border bg-muted/30 p-3 space-y-2">
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-semibold text-sm">{{ auth.user.value.nombre || 'Usuario' }}</p>
                  <p class="text-xs text-muted-foreground font-mono">{{ auth.user.value.email }}</p>
                </div>
                <Badge variant="default" class="text-xs font-semibold">
                  {{ auth.user.value.role }}
                </Badge>
              </div>

              <div class="text-[11px] text-muted-foreground border-t pt-2 space-y-1">
                <p>Organización: <strong class="text-foreground">{{ auth.user.value.org_id }}</strong></p>
                <div class="flex flex-wrap gap-2 pt-1">
                  <Badge variant="success" class="text-[10px]">
                    Access Token: 15 min
                  </Badge>
                  <Badge variant="info" class="text-[10px]">
                    Refresh Token: 7 días
                  </Badge>
                  <Badge variant="outline" class="text-[10px]">
                    Rotación con anti-replay
                  </Badge>
                </div>
              </div>
            </div>

            <p v-if="successMsg" class="text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 p-2 rounded border border-emerald-500/20">
              {{ successMsg }}
            </p>
            <p v-if="error" class="text-xs text-destructive bg-destructive/10 p-2 rounded border border-destructive/20">
              {{ error }}
            </p>

            <div class="flex flex-wrap gap-2 pt-1">
              <Button size="sm" variant="outline" :disabled="loading" @click="handleRefresh">
                Probar rotación de token
              </Button>
              <Button size="sm" variant="destructive" @click="handleLogout">
                Cerrar Sesión
              </Button>
            </div>
          </div>

          <!-- Login Form -->
          <div v-else class="space-y-3">
            <p class="text-xs text-muted-foreground">
              Autenticación con tokens duales: <strong>15 minutos</strong> para acceso inmediato y <strong>7 días</strong> para sesión extendida con rotación segura.
            </p>

            <div class="space-y-2">
              <div>
                <label class="text-xs font-medium text-muted-foreground">Correo electrónico</label>
                <Input v-model="email" placeholder="admin@tvn.com" class="mt-1" />
              </div>
              <div>
                <label class="text-xs font-medium text-muted-foreground">Contraseña</label>
                <Input
                  v-model="password"
                  type="password"
                  placeholder="••••••••"
                  class="mt-1"
                  @keyup.enter="handleLogin"
                />
              </div>
            </div>

            <!-- Acceso Rápido Demo Jurado / RBAC -->
            <div class="rounded-md border bg-muted/20 p-2.5 space-y-1.5">
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-semibold text-foreground flex items-center gap-1">
                  <span>🔑</span> Cuentas Demo Jurado (RBAC)
                </span>
                <span class="text-[9px] text-muted-foreground">1-Click</span>
              </div>
              <div class="grid grid-cols-3 gap-1">
                <button
                  type="button"
                  @click="fillCreds('admin@tvn.com', 'EvidentIA2026!')"
                  class="flex flex-col items-center justify-center p-1.5 rounded border text-center transition-all hover:bg-muted/50"
                  :class="email === 'admin@tvn.com' ? 'border-primary bg-primary/10 text-primary font-semibold' : 'border-border/60 text-muted-foreground'"
                >
                  <span class="text-[10px] font-semibold">Super Admin</span>
                  <span class="text-[8px] opacity-75">T01-T10</span>
                </button>
                <button
                  type="button"
                  @click="fillCreds('editor@tvn.com', 'EvidentIA2026!')"
                  class="flex flex-col items-center justify-center p-1.5 rounded border text-center transition-all hover:bg-muted/50"
                  :class="email === 'editor@tvn.com' ? 'border-primary bg-primary/10 text-primary font-semibold' : 'border-border/60 text-muted-foreground'"
                >
                  <span class="text-[10px] font-semibold">Editor Jefe</span>
                  <span class="text-[8px] opacity-75">Owner</span>
                </button>
                <button
                  type="button"
                  @click="fillCreds('periodista@tvn.com', 'EvidentIA2026!')"
                  class="flex flex-col items-center justify-center p-1.5 rounded border text-center transition-all hover:bg-muted/50"
                  :class="email === 'periodista@tvn.com' ? 'border-primary bg-primary/10 text-primary font-semibold' : 'border-border/60 text-muted-foreground'"
                >
                  <span class="text-[10px] font-semibold">Periodista</span>
                  <span class="text-[8px] opacity-75">Member</span>
                </button>
              </div>
            </div>

            <p v-if="error" class="text-xs text-destructive bg-destructive/10 p-2 rounded border border-destructive/20">
              {{ error }}
            </p>
            <p v-if="successMsg" class="text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 p-2 rounded border border-emerald-500/20">
              {{ successMsg }}
            </p>

            <div class="flex items-center justify-end gap-2 pt-2">
              <Button size="sm" :disabled="loading" @click="handleLogin">
                {{ loading ? "Ingresando…" : "Iniciar Sesión" }}
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>
