<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { marked } from "marked";
import {
  Sparkles,
  X,
  Send,
  Square,
  RotateCcw,
  Bot,
  User,
  Search,
  PlusCircle,
  RefreshCw,
  FileCheck,
  AlertTriangle,
} from "lucide-vue-next";
import { useCopilot } from "~/composables/useCopilot";
import ToolCallCard from "~/components/copilot/ToolCallCard.vue";

const { isOpen, close, messages, status, error, sendMessage, stop, clearError } = useCopilot();

const inputText = ref("");
const messagesContainer = ref<HTMLElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const isBusy = computed(() => status.value === "streaming" || status.value === "submitted");

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
}

watch(
  () => messages.value,
  () => {
    scrollToBottom();
  },
  { deep: true }
);

watch(
  () => isOpen.value,
  (open) => {
    if (open) {
      scrollToBottom();
      nextTick(() => {
        textareaRef.value?.focus();
      });
    }
  }
);

function handleSend() {
  const text = inputText.value.trim();
  if (!text || isBusy.value) return;

  inputText.value = "";
  if (clearError) clearError();

  sendMessage({ text });
  scrollToBottom();
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}

function sendSuggestion(promptText: string) {
  inputText.value = promptText;
  handleSend();
}

function handleReset() {
  messages.value = [];
  if (clearError) clearError();
}

// Global escape key to close drawer
function handleGlobalKey(e: KeyboardEvent) {
  if (e.key === "Escape" && isOpen.value) {
    close();
  }
}

onMounted(() => {
  window.addEventListener("keydown", handleGlobalKey);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleGlobalKey);
});

// Safe Markdown render helper
function renderMarkdown(content: string): string {
  try {
    return marked.parse(content, { breaks: true, gfm: true }) as string;
  } catch {
    return content;
  }
}

// Filter tool parts from message parts
function getToolParts(message: any) {
  if (!message.parts || !Array.isArray(message.parts)) return [];
  return message.parts.filter(
    (p: any) =>
      p &&
      (p.type === "dynamic-tool" ||
        (typeof p.type === "string" && p.type.startsWith("tool-")))
  );
}

// Extract plain text parts
function getTextContent(message: any): string {
  if (!message.parts || !Array.isArray(message.parts)) {
    return typeof message.content === "string" ? message.content : "";
  }
  return message.parts
    .filter((p: any) => p && p.type === "text")
    .map((p: any) => p.text || "")
    .join("");
}
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-40 bg-ink/20 backdrop-blur-[2px] transition-opacity"
      @click="close"
    />

    <!-- Slide-over Drawer Panel -->
    <div
      class="fixed inset-y-0 right-0 z-50 flex w-full flex-col border-l border-hairline bg-surface shadow-2xl transition-transform duration-300 ease-in-out sm:w-[480px] lg:w-[520px]"
      :class="isOpen ? 'translate-x-0' : 'translate-x-full'"
    >
      <!-- Header -->
      <div class="flex h-14 items-center justify-between border-b border-hairline px-4 bg-surface">
        <div class="flex items-center gap-2.5">
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary border border-primary/20">
            <Sparkles class="h-4 w-4" />
          </div>
          <div>
            <h2 class="font-serif text-base font-semibold text-ink leading-tight">
              Copiloto Editorial
            </h2>
            <div class="flex items-center gap-1.5 font-mono text-[10px] text-ink-muted">
              <span>EvidentIA AI Agent</span>
              <span>·</span>
              <span class="rounded bg-surface-sunken px-1 border border-hairline">Server Tools</span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-1">
          <button
            v-if="messages.length > 0"
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-surface-sunken hover:text-ink"
            title="Reiniciar conversación"
            @click="handleReset"
          >
            <RotateCcw class="h-4 w-4" />
          </button>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-surface-sunken hover:text-ink"
            title="Cerrar copiloto (Esc)"
            @click="close"
          >
            <X class="h-4 w-4" />
          </button>
        </div>
      </div>

      <!-- Messages Stream Feed -->
      <div
        ref="messagesContainer"
        class="flex-1 overflow-y-auto p-4 space-y-4 bg-canvas/40"
      >
        <!-- Welcome empty state -->
        <div
          v-if="messages.length === 0"
          class="flex flex-col items-center justify-center py-8 text-center"
        >
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary border border-primary/20 mb-3">
            <Bot class="h-6 w-6" />
          </div>
          <h3 class="font-serif text-lg font-semibold text-ink">
            ¿En qué puedo ayudarte hoy?
          </h3>
          <p class="mt-1 text-xs text-ink-muted max-w-[340px]">
            Puedo buscar evidencias en el catálogo, crear y actualizar leads, asociar fuentes, registrar notas y reejecutar la ingesta de datos.
          </p>

          <!-- Quick Prompts suggestions -->
          <div class="mt-6 flex flex-col gap-2 w-full max-w-[380px]">
            <button
              type="button"
              class="flex items-center gap-2.5 rounded-lg border border-hairline bg-surface p-2.5 text-left text-xs text-ink transition-all hover:border-primary/40 hover:bg-surface-sunken shadow-xs"
              @click="sendSuggestion('Busca en el catálogo las últimas evidencias y noticias disponibles')"
            >
              <Search class="h-4 w-4 text-primary shrink-0" />
              <span>Buscar evidencias y noticias recientes</span>
            </button>

            <button
              type="button"
              class="flex items-center gap-2.5 rounded-lg border border-hairline bg-surface p-2.5 text-left text-xs text-ink transition-all hover:border-primary/40 hover:bg-surface-sunken shadow-xs"
              @click="sendSuggestion('¿Cuáles son los leads de investigación que están en revisión?')"
            >
              <FileCheck class="h-4 w-4 text-warning shrink-0" />
              <span>Ver leads que requieren revisión</span>
            </button>

            <button
              type="button"
              class="flex items-center gap-2.5 rounded-lg border border-hairline bg-surface p-2.5 text-left text-xs text-ink transition-all hover:border-primary/40 hover:bg-surface-sunken shadow-xs"
              @click="sendSuggestion('Crea un nuevo lead para TVN con título: Investigación de Contratos Públicos')"
            >
              <PlusCircle class="h-4 w-4 text-success shrink-0" />
              <span>Crear nuevo lead de investigación</span>
            </button>

            <button
              type="button"
              class="flex items-center gap-2.5 rounded-lg border border-hairline bg-surface p-2.5 text-left text-xs text-ink transition-all hover:border-primary/40 hover:bg-surface-sunken shadow-xs"
              @click="sendSuggestion('Cuál es el estado de la ingesta y cuántos registros hay procesados?')"
            >
              <RefreshCw class="h-4 w-4 text-accent shrink-0" />
              <span>Consultar reporte de calidad de ingesta</span>
            </button>
          </div>
        </div>

        <!-- Chat messages loop -->
        <div
          v-for="(msg, idx) in messages"
          :key="msg.id || idx"
          class="flex flex-col space-y-1.5"
        >
          <!-- User message -->
          <div
            v-if="msg.role === 'user'"
            class="flex items-start justify-end gap-2"
          >
            <div class="max-w-[85%] rounded-lg bg-primary px-3.5 py-2.5 text-xs text-on-primary shadow-xs">
              <p class="whitespace-pre-wrap leading-relaxed">{{ getTextContent(msg) }}</p>
            </div>
            <div class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/20 text-primary border border-primary/30 mt-0.5">
              <User class="h-3.5 w-3.5" />
            </div>
          </div>

          <!-- Assistant message -->
          <div
            v-else
            class="flex items-start justify-start gap-2"
          >
            <div class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-surface-sunken text-primary border border-hairline mt-0.5">
              <Sparkles class="h-3.5 w-3.5" />
            </div>
            <div class="max-w-[90%] flex-1">
              <!-- Render Tool Calls first or alongside -->
              <div v-if="getToolParts(msg).length > 0" class="space-y-1.5">
                <ToolCallCard
                  v-for="(part, pIdx) in getToolParts(msg)"
                  :key="pIdx"
                  :part="part"
                />
              </div>

              <!-- Render Text Response with Markdown -->
              <div
                v-if="getTextContent(msg)"
                class="rounded-lg border border-hairline bg-surface px-3.5 py-2.5 text-xs text-ink shadow-xs prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-li:my-0.5"
                v-html="renderMarkdown(getTextContent(msg))"
              />
            </div>
          </div>
        </div>

        <!-- Thinking indicator -->
        <div
          v-if="isBusy && messages[messages.length - 1]?.role === 'user'"
          class="flex items-center gap-2 text-ink-muted text-xs pl-8"
        >
          <div class="flex gap-1">
            <span class="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
            <span class="h-1.5 w-1.5 rounded-full bg-primary animate-pulse delay-150" />
            <span class="h-1.5 w-1.5 rounded-full bg-primary animate-pulse delay-300" />
          </div>
          <span class="font-mono text-[11px]">Procesando herramientas del servidor...</span>
        </div>

        <!-- Error banner -->
        <div
          v-if="error"
          class="flex items-center gap-2 rounded-md border border-error/20 bg-error/10 p-3 text-xs text-error"
        >
          <AlertTriangle class="h-4 w-4 shrink-0" />
          <span class="flex-1">{{ error?.message || error || 'Ocurrió un error inesperado al procesar la solicitud.' }}</span>
        </div>
      </div>

      <!-- Composer / Input Bar -->
      <div class="border-t border-hairline bg-surface p-3">
        <div class="relative flex items-end gap-2 rounded-lg border border-hairline bg-surface-sunken p-1.5 focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/20 transition-all">
          <textarea
            ref="textareaRef"
            v-model="inputText"
            rows="2"
            placeholder="Escribe una instrucción al Copiloto (ej: 'Crea un lead sobre finanzas')..."
            class="flex-1 resize-none bg-transparent px-2 py-1 text-xs text-ink placeholder:text-ink-muted focus:outline-none leading-relaxed"
            :disabled="isBusy"
            @keydown="handleKeydown"
          />

          <div class="flex items-center gap-1 pb-0.5">
            <button
              v-if="isBusy"
              type="button"
              class="flex h-7 w-7 items-center justify-center rounded-md bg-error/10 text-error hover:bg-error/20 transition-colors"
              title="Detener respuesta"
              @click="stop"
            >
              <Square class="h-3.5 w-3.5 fill-current" />
            </button>

            <button
              v-else
              type="button"
              class="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-on-primary hover:bg-primary-deep disabled:opacity-40 transition-colors shadow-xs"
              :disabled="!inputText.trim()"
              title="Enviar mensaje (Enter)"
              @click="handleSend"
            >
              <Send class="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        <div class="mt-1.5 flex items-center justify-between px-1 text-[10px] text-ink-muted font-mono">
          <span>Enter para enviar · Shift+Enter para salto</span>
          <span>Esc para cerrar</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>
