<script setup lang="ts">
import { ref } from "vue";
import Button from "~/components/ui/Button.vue";
import Input from "~/components/ui/Input.vue";
import { useAuth } from "~/composables/useAuth";

definePageMeta({
  layout: "auth",
});

const route = useRoute();
const auth = useAuth();

const email = ref("");
const password = ref("");
const showPassword = ref(false);
const loading = ref(false);
const error = ref("");

const demoAccounts = [
  { label: "Admin", email: "admin@tvn.com" },
  { label: "Editor", email: "editor@tvn.com" },
  { label: "Periodista", email: "periodista@tvn.com" },
  { label: "Vertex", email: "admin@vertexdc.com" },
];

function fillCreds(demoEmail: string) {
  email.value = demoEmail;
  password.value = "EvidentIA2026!";
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
  <div class="flex min-h-screen flex-col-reverse lg:flex-row">
    <!-- Columna principal: formulario -->
    <main
      class="flex flex-1 flex-col items-center justify-center gap-7 bg-surface px-5 py-10 sm:px-12 lg:px-24 lg:py-16"
    >
      <!-- Encabezado -->
      <div class="flex w-full max-w-[440px] flex-col gap-2.5">
        <span class="text-label uppercase tracking-wider text-primary">
          Consola editorial
        </span>
        <h1
          class="font-serif text-[32px] font-semibold leading-tight tracking-tight text-ink sm:text-[40px]"
        >
          Hola de nuevo
        </h1>
        <p class="text-body-md text-ink-muted">
          Verificación de fuentes, citación estructurada y priorización explicable
          — en una sola consola.
        </p>
      </div>

      <!-- Formulario -->
      <form class="flex w-full max-w-[440px] flex-col gap-4" @submit.prevent="onSubmit">
        <label class="flex flex-col gap-1.5">
          <span class="text-label uppercase tracking-wider text-ink-muted">
            Correo electrónico
          </span>
          <Input
            v-model="email"
            type="email"
            placeholder="admin@tvn.com"
            autocomplete="username"
            class="h-11 border-hairline text-body-sm"
          />
        </label>

        <label class="flex flex-col gap-1.5">
          <span class="text-label uppercase tracking-wider text-ink-muted">
            Contraseña
          </span>
          <div class="relative flex">
            <Input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••••••"
              autocomplete="current-password"
              class="h-11 min-w-0 flex-1 border-hairline pr-20 text-body-sm"
            />
            <button
              type="button"
              class="absolute right-1.5 top-1.5 h-8 rounded-sm px-2 text-caption font-semibold text-primary transition-colors hover:bg-primary-soft"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? "Ocultar" : "Mostrar" }}
            </button>
          </div>
        </label>

        <span v-if="error" class="text-body-sm text-error">{{ error }}</span>

        <div class="flex flex-wrap items-center gap-4">
          <Button
            type="submit"
            class="h-11 min-w-[120px] flex-1 px-7 font-semibold sm:flex-none"
            :disabled="loading"
          >
            {{ loading ? "Accediendo…" : "Acceder" }}
          </Button>
          <a href="#" class="text-caption font-medium text-primary hover:underline">
            ¿Olvidaste tu contraseña?
          </a>
        </div>
      </form>

      <!-- Acceso rápido demo (jurado / RBAC) -->
      <div
        class="flex w-full max-w-[440px] flex-wrap items-center gap-2 border-t border-hairline pt-4"
      >
        <span class="text-caption text-ink-muted">Demo:</span>
        <button
          v-for="acc in demoAccounts"
          :key="acc.email"
          type="button"
          class="h-8 rounded-sm border px-3 text-caption font-medium text-ink transition-colors"
          :class="
            email === acc.email
              ? 'border-primary bg-primary-soft'
              : 'border-hairline hover:border-primary/40'
          "
          @click="fillCreds(acc.email)"
        >
          {{ acc.label }}
        </button>
      </div>
    </main>

    <!-- Banda de marca: tira lateral (desktop) / cabecera (móvil) -->
    <aside
      class="relative flex flex-col justify-end overflow-hidden bg-primary p-8 lg:w-[520px] lg:flex-shrink-0 lg:p-10"
    >
      <!-- Wordmark vertical gigante (solo desktop) -->
      <div
        aria-label="EvidentIA"
        class="pointer-events-none absolute left-1/2 top-1/2 hidden -translate-x-1/2 -translate-y-1/2 -rotate-90 whitespace-nowrap font-serif text-[226px] font-semibold leading-none tracking-tight text-on-primary lg:block"
      >
        Evident<span class="text-on-primary/70">IA</span>
      </div>

      <!-- Wordmark horizontal (móvil / tablet) -->
      <div
        aria-label="EvidentIA"
        class="whitespace-nowrap font-serif font-semibold leading-none tracking-tight text-on-primary lg:hidden"
        style="font-size: clamp(70px, 20vw, 174px)"
      >
        Evident<span class="text-on-primary/70">IA</span>
      </div>

      <p
        class="relative z-10 mt-3 max-w-[32ch] font-serif text-body-sm font-medium leading-snug text-on-primary lg:mt-0 lg:max-w-[16ch] lg:self-end lg:text-right"
      >
        Inteligencia periodística con trazabilidad auditable.
      </p>
    </aside>
  </div>
</template>
