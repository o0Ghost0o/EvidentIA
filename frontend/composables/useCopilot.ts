/**
 * Composable for EvidentIA Copilot Agent.
 *
 * Provides shared drawer state (open/close/toggle) and wraps @ai-sdk/vue's useChat
 * with automatic JWT authorization header injection and page context.
 */
import { ref, computed } from "vue";
import { useChat } from "@ai-sdk/vue";
import { useRoute } from "vue-router";
import { useAuth } from "~/composables/useAuth";

const isOpen = ref(false);

export function useCopilot() {
  const auth = useAuth();
  const route = useRoute();

  function toggle() {
    isOpen.value = !isOpen.value;
  }

  function open() {
    isOpen.value = true;
  }

  function close() {
    isOpen.value = false;
  }

  // Active page context passed along with user prompts
  const currentContext = computed(() => ({
    currentPath: route.path,
    leadId: route.params.id || null,
    userEmail: auth.user.value?.email || null,
    userRole: auth.user.value?.role || null,
  }));

  const chat = useChat({
    api: "/api/copilot",
    headers: computed(() => ({
      ...(auth.accessToken.value ? { authorization: `Bearer ${auth.accessToken.value}` } : {}),
    })),
    body: computed(() => ({
      context: currentContext.value,
    })),
  });

  return {
    isOpen,
    toggle,
    open,
    close,
    chat,
    messages: chat.messages,
    status: chat.status,
    error: chat.error,
    sendMessage: chat.sendMessage,
    stop: chat.stop,
    clearError: chat.clearError,
  };
}
