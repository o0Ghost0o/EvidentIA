/**
 * Composable for EvidentIA Copilot Agent.
 *
 * Provides shared drawer state (open/close/toggle) and wraps @ai-sdk/vue's useChat
 * with automatic JWT authorization header injection and page context.
 */
import { ref, computed } from "vue";
import { useChat } from "@ai-sdk/vue";
import { DefaultChatTransport } from "ai";
import { useRoute } from "vue-router";
import { useAuth } from "~/composables/useAuth";

const isOpen = ref(false);

function isTokenExpired(token: string | null): boolean {
  if (!token) return true;
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return false;
    const payload = JSON.parse(atob(parts[1]));
    if (payload.exp) {
      // Treat as expired if less than 30s remaining
      return Date.now() >= payload.exp * 1000 - 30000;
    }
  } catch {
    return false;
  }
  return false;
}

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
    transport: new DefaultChatTransport({
      api: "/api/copilot",
      headers: async () => {
        // Proactively refresh JWT session if access token is missing or expiring
        if (isTokenExpired(auth.accessToken.value) && auth.refreshToken.value) {
          await auth.refreshSession();
        }
        return auth.accessToken.value ? { authorization: `Bearer ${auth.accessToken.value}` } : {};
      },
      body: () => ({
        context: currentContext.value,
      }),
    }),
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
