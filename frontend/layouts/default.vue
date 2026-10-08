<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import AuthModal from "~/components/AuthModal.vue";
import { useAuth } from "~/composables/useAuth";

const auth = useAuth();
const route = useRoute();
const showAuthModal = ref(false);

const nav = [
  { label: "Bandeja", to: "/" },
  { label: "Leads", to: "/leads" },
  { label: "Ingesta", to: "/ingest" },
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

onMounted(() => {
  auth.initAuth();
  let stored: string | null = null;
  try {
    stored = localStorage.getItem("ev-theme");
  } catch {
    /* ignore */
  }
  applyTheme(stored === "dark");
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
            class="border-b-2 py-[18px] text-label uppercase no-underline transition-colors"
            :class="
              isActive(item.to)
                ? 'border-primary text-primary'
                : 'border-transparent text-ink-muted hover:text-ink'
            "
          >
            {{ item.label }}
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
            <span aria-hidden="true">{{ isDark ? "☀" : "☾" }}</span>
          </button>

          <!-- Authenticated: session chip (avatar + name · role) -->
          <button
            v-if="auth.isAuthenticated.value && auth.user.value"
            type="button"
            class="flex items-center gap-2 rounded-full border border-hairline py-1 pl-1 pr-3 text-body-sm transition-colors hover:bg-surface-sunken"
            @click="showAuthModal = true"
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

          <!-- Unauthenticated: outline login action -->
          <button
            v-else
            type="button"
            class="flex h-9 items-center gap-1.5 rounded-md border border-hairline bg-transparent px-3 text-body-sm font-semibold text-ink transition-colors hover:bg-surface-sunken"
            @click="showAuthModal = true"
          >
            <span aria-hidden="true">🔒</span>
            <span>Seguridad &amp; Login</span>
          </button>
        </div>
      </div>
    </header>

    <main class="mx-auto w-full max-w-container px-4 py-6">
      <slot />
    </main>

    <AuthModal v-model="showAuthModal" />
  </div>
</template>
