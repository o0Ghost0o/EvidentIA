<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";
import AuthModal from "~/components/AuthModal.vue";
import Popover from "~/components/ui/Popover.vue";
import CopilotDrawer from "~/components/copilot/CopilotDrawer.vue";
import CopilotFab from "~/components/copilot/CopilotFab.vue";
import { Lock, LogOut, Moon, Sun } from "lucide-vue-next";
import { useAuth } from "~/composables/useAuth";
import { useCopilot } from "~/composables/useCopilot";

const route = useRoute();
const auth = useAuth();
const copilot = useCopilot();
const showAuthModal = ref(false);
const sessionMenuOpen = ref(false);
const loggingOut = ref(false);

async function handleLogout() {
  if (loggingOut.value) return;
  loggingOut.value = true;
  try {
    await auth.logout();
  } finally {
    loggingOut.value = false;
    sessionMenuOpen.value = false;
    await navigateTo("/login");
  }
}

const nav = [
  { label: "Bandeja", to: "/" },
  { label: "Leads", to: "/leads" },
  { label: "Grafo", to: "/graph" },
  { label: "Ingesta", to: "/ingest" },
  { label: "Corrida de Evaluación", to: "/jurado", isJurado: true },
];

function isActive(to: string): boolean {
  return to === "/" ? route.path === "/" : route.path.startsWith(to);
}

// Session chip initials from the authenticated user's email.
const initials = computed(() => {
  const email = auth.user.value?.email ?? "";
  const name = email.split("@")[0] ?? "";
  return name.slice(0, 2).toUpperCase() || "··";
});

// Theme toggle — DESIGN app-bar carries the light/dark switch; tokens are class-based.
const isDark = ref(false);
function applyTheme(dark: boolean) {
  isDark.value = dark;
  document.documentElement.classList.toggle("dark", dark);
  try {
    localStorage.setItem("ev-theme", dark ? "dark" : "light");
  } catch {
    /* storage may be unavailable */
  }
}
function toggleTheme() {
  applyTheme(!isDark.value);
}

function handleKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    copilot.toggle();
  }
}

onMounted(() => {
  auth.initAuth();
  let stored: string | null = null;
  try {
    stored = localStorage.getItem("ev-theme");
  } catch {
    /* ignore */
  }
  applyTheme(stored === "dark");
  window.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
});
</script>

<template>
  <div class="min-h-screen bg-canvas text-ink">
    <!-- app-bar: surface fill, bottom hairline, 56px tall -->
    <header class="h-14 border-b border-hairline bg-surface px-4">
      <div class="mx-auto flex h-full w-full max-w-container items-center gap-8">
        <!-- Serif wordmark (logo placeholder per DESIGN Known Gaps) -->
        <NuxtLink
          to="/"
          class="font-serif text-xl font-semibold tracking-[-0.2px] text-ink no-underline"
        >
          Evident<span class="text-primary">IA</span>
        </NuxtLink>

        <!-- Primary nav: uppercase label links, active route in primary -->
        <nav class="flex items-center gap-6">
          <NuxtLink
            v-for="item in nav"
            :key="item.to"
            :to="item.to"
            class="flex items-center gap-1.5 border-b-2 py-[18px] text-label uppercase no-underline transition-colors"
            :class="
              isActive(item.to)
                ? 'border-primary text-primary font-semibold'
                : 'border-transparent text-ink-muted hover:text-ink'
            "
          >
            <span>{{ item.label }}</span>
            <span
              v-if="item.isJurado"
              class="rounded bg-primary/10 px-1.5 py-0.5 text-[9px] font-bold text-primary border border-primary/20"
            >
              T01–T10
            </span>
          </NuxtLink>
        </nav>

        <!-- Session + theme controls -->
        <div class="ml-auto flex items-center gap-2">
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-surface-sunken hover:text-ink"
            :aria-label="isDark ? 'Activar modo claro' : 'Activar modo oscuro'"
            @click="toggleTheme"
          >
            <Sun v-if="isDark" class="h-4 w-4" aria-hidden="true" />
            <Moon v-else class="h-4 w-4" aria-hidden="true" />
          </button>

          <!-- Authenticated: session chip opens a menu with the logout action -->
          <Popover
            v-if="auth.isAuthenticated.value && auth.user.value"
            v-model:open="sessionMenuOpen"
            align="end"
            content-class="w-64 p-0"
          >
            <template #trigger>
              <button
                type="button"
                class="flex items-center gap-2 rounded-full border border-hairline py-1 pl-1 pr-3 text-body-sm transition-colors hover:bg-surface-sunken"
                aria-label="Abrir menú de sesión"
              >
                <span
                  class="flex h-7 w-7 items-center justify-center rounded-full bg-primary-soft text-caption font-semibold text-primary"
                >
                  {{ initials }}
                </span>
                <span class="whitespace-nowrap text-ink">{{ auth.user.value.email }}</span>
                <span
                  class="rounded-full border border-hairline px-2 py-px text-[10px] font-semibold uppercase tracking-wide text-ink-muted"
                >
                  {{ auth.user.value.role }}
                </span>
              </button>
            </template>

            <div class="flex flex-col gap-0.5 border-b border-hairline px-3 py-2.5">
              <span class="truncate text-body-sm font-semibold text-ink">
                {{ auth.user.value.email }}
              </span>
              <span class="text-caption uppercase tracking-wide text-ink-muted">
                {{ auth.user.value.role }}
              </span>
            </div>
            <div class="p-1">
              <button
                type="button"
                :disabled="loggingOut"
                class="flex w-full items-center gap-2 rounded-sm px-2.5 py-2 text-left text-body-sm text-ink transition-colors hover:bg-surface-sunken disabled:opacity-50"
                @click="handleLogout"
              >
                <LogOut class="h-4 w-4 text-ink-muted" aria-hidden="true" />
                <span>{{ loggingOut ? "Cerrando sesión…" : "Cerrar sesión" }}</span>
              </button>
            </div>
          </Popover>

          <!-- Unauthenticated: outline login action -->
          <button
            v-else
            type="button"
            class="flex h-9 items-center gap-1.5 rounded-md border border-hairline bg-transparent px-3 text-body-sm font-semibold text-ink transition-colors hover:bg-surface-sunken"
            @click="showAuthModal = true"
          >
            <Lock class="h-4 w-4" aria-hidden="true" />
            <span>Seguridad &amp; Login</span>
          </button>
        </div>
      </div>
    </header>

    <main class="mx-auto w-full max-w-container px-4 py-6">
      <slot />
    </main>

    <AuthModal v-model="showAuthModal" />
    <CopilotDrawer />
    <CopilotFab />
  </div>
</template>
