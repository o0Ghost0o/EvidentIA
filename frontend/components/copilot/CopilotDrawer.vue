<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
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
  Copy,
  Check,
} from "lucide-vue-next";
import { useCopilot } from "~/composables/useCopilot";
import ToolCallCard from "~/components/copilot/ToolCallCard.vue";

const { isOpen, close, messages, status, error, sendMessage, stop, clearError } = useCopilot();
const router = useRouter();

const inputText = ref("");
const messagesContainer = ref<HTMLElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const copiedMessageId = ref<string | number | null>(null);

const isBusy = computed(() => status.value === "streaming" || status.value === "submitted");

// Configure marked with GFM, breaks and custom link rendering
marked.use({
  gfm: true,
  breaks: true,
  renderer: {
    link({ href, title, text }) {
      const isInternal = href.startsWith("/");
      const targetAttr = isInternal ? "" : ` target="_blank" rel="noopener noreferrer"`;
      const titleAttr = title ? ` title="${title}"` : "";
      return `<a href="${href}"${targetAttr}${titleAttr} class="copilot-link font-medium">${text}</a>`;
    },
  },
});

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
    return marked.parse(content) as string;
  } catch {
    return content;
  }
}

// Copy assistant markdown text to clipboard
async function copyResponse(text: string, id: string | number) {
  try {
    await navigator.clipboard.writeText(text);
    copiedMessageId.value = id;
    setTimeout(() => {
      if (copiedMessageId.value === id) {
        copiedMessageId.value = null;
      }
    }, 2000);
  } catch (err) {
    console.error("Error al copiar texto:", err);
  }
}

// Intercept clicks on internal markdown links for Nuxt SPA routing
function handleMessageClick(e: MouseEvent) {
  const target = (e.target as HTMLElement)?.closest("a");
  if (!target) return;
  const href = target.getAttribute("href");
  if (href && href.startsWith("/") && !href.startsWith("//")) {
    e.preventDefault();
    router.push(href);
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
        @click="handleMessageClick"
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

              <!-- Render Text Response with Markdown and Copy Action -->
              <div
                v-if="getTextContent(msg)"
                class="group relative rounded-lg border border-hairline bg-surface p-3.5 text-xs text-ink shadow-xs"
                :class="{ 'mt-2.5': getToolParts(msg).length > 0 }"
              >
                <div
                  class="copilot-prose"
                  v-html="renderMarkdown(getTextContent(msg))"
                />

                <!-- Footer with Copy Action -->
                <div class="mt-2.5 flex items-center justify-between border-t border-hairline/60 pt-2 text-[10px] text-ink-muted select-none">
                  <span class="font-mono">EvidentIA Copilot</span>
                  <button
                    type="button"
                    class="flex items-center gap-1 rounded px-1.5 py-0.5 text-ink-muted transition-colors hover:bg-surface-sunken hover:text-ink font-mono"
                    :title="copiedMessageId === (msg.id || idx) ? 'Copiado al portapapeles' : 'Copiar respuesta'"
                    @click="copyResponse(getTextContent(msg), msg.id || idx)"
                  >
                    <Check v-if="copiedMessageId === (msg.id || idx)" class="h-3 w-3 text-success" />
                    <Copy v-else class="h-3 w-3" />
                    <span>{{ copiedMessageId === (msg.id || idx) ? 'Copiado' : 'Copiar' }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Thinking / Generation indicator -->
        <div
          v-if="isBusy && (!messages.length || !getTextContent(messages[messages.length - 1]))"
          class="flex items-center gap-2 text-ink-muted text-xs pl-8"
        >
          <div class="flex gap-1">
            <span class="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
            <span class="h-1.5 w-1.5 rounded-full bg-primary animate-pulse delay-150" />
            <span class="h-1.5 w-1.5 rounded-full bg-primary animate-pulse delay-300" />
          </div>
          <span class="font-mono text-[11px]">
            {{ getToolParts(messages[messages.length - 1] || {}).length > 0 ? 'Analizando datos y redactando respuesta...' : 'Procesando consulta...' }}
          </span>
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

<style>
/* Scoped typography & markdown rules for Copilot chat responses */
.copilot-prose {
  font-size: 0.8125rem; /* 13px */
  line-height: 1.55;
  color: hsl(var(--ink));
  word-break: break-word;
}

.copilot-prose h1,
.copilot-prose h2,
.copilot-prose h3,
.copilot-prose h4 {
  font-family: 'Source Serif 4', Lora, Georgia, serif;
  font-weight: 600;
  color: hsl(var(--ink));
  margin-top: 0.75rem;
  margin-bottom: 0.35rem;
  line-height: 1.25;
}

.copilot-prose h1 { font-size: 1.1rem; }
.copilot-prose h2 { font-size: 1rem; }
.copilot-prose h3 { font-size: 0.9375rem; }
.copilot-prose h4 { font-size: 0.875rem; }

.copilot-prose p {
  margin-top: 0.35rem;
  margin-bottom: 0.35rem;
}

.copilot-prose ul {
  list-style-type: disc;
  padding-left: 1.25rem;
  margin-top: 0.35rem;
  margin-bottom: 0.35rem;
}

.copilot-prose ol {
  list-style-type: decimal;
  padding-left: 1.25rem;
  margin-top: 0.35rem;
  margin-bottom: 0.35rem;
}

.copilot-prose li {
  margin-top: 0.2rem;
  margin-bottom: 0.2rem;
}

.copilot-prose strong {
  font-weight: 600;
  color: hsl(var(--ink));
}

.copilot-prose .copilot-link,
.copilot-prose a {
  color: hsl(var(--primary));
  font-weight: 500;
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
  transition: color 0.15s ease;
}

.copilot-prose .copilot-link:hover,
.copilot-prose a:hover {
  color: hsl(var(--primary-deep));
}

.copilot-prose blockquote {
  border-left: 3px solid hsl(var(--primary) / 0.5);
  background: hsl(var(--surface-sunken) / 0.6);
  padding: 0.4rem 0.75rem;
  margin: 0.5rem 0;
  border-radius: 0 4px 4px 0;
  font-style: italic;
  color: hsl(var(--ink-muted));
}

.copilot-prose table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.6rem 0;
  font-size: 0.75rem;
  border: 1px solid hsl(var(--hairline));
  border-radius: 6px;
  overflow: hidden;
  display: table;
}

.copilot-prose thead {
  background: hsl(var(--surface-sunken));
}

.copilot-prose th {
  color: hsl(var(--ink));
  font-weight: 600;
  padding: 0.4rem 0.6rem;
  border-bottom: 1px solid hsl(var(--hairline));
  text-align: left;
}

.copilot-prose td {
  padding: 0.35rem 0.6rem;
  border-bottom: 1px solid hsl(var(--hairline) / 0.7);
  color: hsl(var(--ink));
}

.copilot-prose tr:last-child td {
  border-bottom: none;
}

.copilot-prose tbody tr:nth-child(even) {
  background: hsl(var(--surface-sunken) / 0.25);
}

.copilot-prose code {
  font-family: 'IBM Plex Mono', 'JetBrains Mono', monospace;
  font-size: 0.6875rem;
  background: hsl(var(--surface-sunken));
  color: hsl(var(--primary));
  padding: 0.15rem 0.35rem;
  border-radius: 4px;
  border: 1px solid hsl(var(--hairline) / 0.7);
}

.copilot-prose pre {
  background: hsl(var(--canvas));
  border: 1px solid hsl(var(--hairline));
  border-radius: 6px;
  padding: 0.6rem 0.8rem;
  margin: 0.5rem 0;
  overflow-x: auto;
}

.copilot-prose pre code {
  background: transparent;
  border: none;
  padding: 0;
  color: hsl(var(--ink));
  font-size: 0.75rem;
}

.copilot-prose hr {
  border: none;
  border-top: 1px solid hsl(var(--hairline));
  margin: 0.75rem 0;
}
</style>
