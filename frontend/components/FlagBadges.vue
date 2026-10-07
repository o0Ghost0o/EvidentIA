<script setup lang="ts">
import { ref } from "vue";
import Badge from "~/components/ui/Badge.vue";
import Button from "~/components/ui/Button.vue";
import Input from "~/components/ui/Input.vue";

export interface ActivityFlag {
  id: string;
  label: string;
  category?: string;
  variant?: "default" | "secondary" | "outline" | "destructive" | "success" | "warning" | "info" | "purple" | "teal";
  description?: string;
}

const props = withDefaults(
  defineProps<{
    flags: ActivityFlag[];
    customFlags?: string[];
    editable?: boolean;
    compact?: boolean;
  }>(),
  {
    customFlags: () => [],
    editable: false,
    compact: false,
  }
);

const emit = defineEmits<{
  (e: "addFlag", flagName: string): void;
  (e: "removeFlag", flagName: string): void;
}>();

const showAddInput = ref(false);
const newFlagText = ref("");

const PRESET_SUGGESTIONS = [
  "Prioridad Alta",
  "Riesgo Crítico",
  "Investigación Especial",
  "Banca Corporativa",
  "Auditoría Externa",
  "Cliente VIP",
  "Alerta de Fraude",
];

function submitAdd(flagName: string) {
  const val = flagName.trim();
  if (!val) return;
  emit("addFlag", val);
  newFlagText.value = "";
  showAddInput.value = false;
}

function removeCustom(flagName: string) {
  emit("removeFlag", flagName);
}
</script>

<template>
  <div class="space-y-2">
    <div class="flex flex-wrap items-center gap-1.5">
      <template v-for="flag in flags" :key="flag.id">
        <span
          class="group relative inline-flex items-center"
          :title="flag.description || flag.label"
        >
          <Badge :variant="flag.variant || 'secondary'" class="flex items-center gap-1 cursor-default">
            <span>{{ flag.label }}</span>
            <button
              v-if="editable && flag.category === 'custom'"
              type="button"
              class="ml-1 text-xs opacity-60 hover:opacity-100 hover:text-destructive"
              title="Quitar flag"
              @click.stop="removeCustom(flag.label)"
            >
              ×
            </button>
          </Badge>
        </span>
      </template>

      <!-- Button to add new flag if editable -->
      <div v-if="editable" class="inline-flex items-center">
        <button
          v-if="!showAddInput"
          type="button"
          class="inline-flex items-center rounded-full border border-dashed border-muted-foreground/40 px-2 py-0.5 text-xs text-muted-foreground hover:border-foreground hover:text-foreground transition-colors"
          @click="showAddInput = true"
        >
          + Agregar Flag
        </button>

        <div v-else class="flex items-center gap-1.5 animate-in fade-in">
          <Input
            v-model="newFlagText"
            placeholder="Nueva flag…"
            class="h-7 w-36 text-xs px-2"
            @keyup.enter="submitAdd(newFlagText)"
          />
          <Button size="sm" class="h-7 px-2 text-xs" @click="submitAdd(newFlagText)">
            Añadir
          </Button>
          <button
            type="button"
            class="text-xs text-muted-foreground hover:text-foreground px-1"
            @click="showAddInput = false"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>

    <!-- Preset chips dropdown/suggestions if adding -->
    <div v-if="editable && showAddInput" class="flex flex-wrap items-center gap-1 text-xs text-muted-foreground pt-1">
      <span class="mr-1">Sugerencias:</span>
      <button
        v-for="preset in PRESET_SUGGESTIONS"
        :key="preset"
        type="button"
        class="rounded-md border bg-muted/40 px-1.5 py-0.5 text-[11px] hover:bg-accent hover:text-accent-foreground"
        @click="submitAdd(preset)"
      >
        + {{ preset }}
      </button>
    </div>
  </div>
</template>
