/**
 * Authentication and session management composable:
 * Dual JWT tokens (15-minute access token, 7-day refresh token) with automatic rotation,
 * cookie persistence for SSR/middleware guard, and RBAC hierarchy.
 */

import { computed, ref } from "vue";

export interface AuthUser {
  id: number;
  email: string;
  nombre: string;
  role: "Super Admin" | "Owner" | "Admin" | "Member" | string;
  org_id: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  refresh_expires_in: number;
  user: AuthUser;
}

const accessToken = ref<string | null>(null);
const refreshToken = ref<string | null>(null);
const user = ref<AuthUser | null>(null);
const isRefreshing = ref(false);

const STORAGE_KEY_ACCESS = "evidentia_access_token";
const STORAGE_KEY_REFRESH = "evidentia_refresh_token";
const STORAGE_KEY_USER = "evidentia_user";

export function useAuth() {
  const accessCookie = useCookie<string | null>("evidentia_access_token", { maxAge: 900 });
  const refreshCookie = useCookie<string | null>("evidentia_refresh_token", { maxAge: 604800 });
  const userCookie = useCookie<AuthUser | null>("evidentia_user", { maxAge: 604800 });

  // Sync memory state with cookies if not set
  if (accessCookie.value && !accessToken.value) accessToken.value = accessCookie.value;
  if (refreshCookie.value && !refreshToken.value) refreshToken.value = refreshCookie.value;
  if (userCookie.value && !user.value) user.value = userCookie.value;

  const isAuthenticated = computed(() => {
    const hasToken = !!(accessToken.value || accessCookie.value);
    const hasUser = !!(user.value || userCookie.value);
    return hasToken && hasUser;
  });

  function saveSession(tokens: TokenResponse) {
    accessToken.value = tokens.access_token;
    refreshToken.value = tokens.refresh_token;
    user.value = tokens.user;

    accessCookie.value = tokens.access_token;
    refreshCookie.value = tokens.refresh_token;
    userCookie.value = tokens.user;

    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY_ACCESS, tokens.access_token);
      localStorage.setItem(STORAGE_KEY_REFRESH, tokens.refresh_token);
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(tokens.user));
    }
  }

  function clearSession() {
    accessToken.value = null;
    refreshToken.value = null;
    user.value = null;

    accessCookie.value = null;
    refreshCookie.value = null;
    userCookie.value = null;

    if (import.meta.client) {
      localStorage.removeItem(STORAGE_KEY_ACCESS);
      localStorage.removeItem(STORAGE_KEY_REFRESH);
      localStorage.removeItem(STORAGE_KEY_USER);
    }
  }

  async function login(email: string, password: string): Promise<TokenResponse> {
    const res = await $fetch<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: { email, password },
    });
    saveSession(res);
    return res;
  }

  async function refreshSession(): Promise<boolean> {
    const currentRefresh = refreshToken.value || refreshCookie.value;
    if (!currentRefresh || isRefreshing.value) return false;
    isRefreshing.value = true;
    try {
      const res = await $fetch<TokenResponse>("/api/auth/refresh", {
        method: "POST",
        body: { refresh_token: currentRefresh },
      });
      saveSession(res);
      return true;
    } catch {
      clearSession();
      return false;
    } finally {
      isRefreshing.value = false;
    }
  }

  async function logout(): Promise<void> {
    const token = refreshToken.value || refreshCookie.value;
    clearSession();
    if (token) {
      await $fetch("/api/auth/logout", {
        method: "POST",
        body: { refresh_token: token },
      }).catch(() => {});
    }
  }

  function initAuth() {
    if (accessCookie.value) accessToken.value = accessCookie.value;
    if (refreshCookie.value) refreshToken.value = refreshCookie.value;
    if (userCookie.value) user.value = userCookie.value;

    if (import.meta.client && (!accessToken.value || !user.value)) {
      const storedAccess = localStorage.getItem(STORAGE_KEY_ACCESS);
      const storedRefresh = localStorage.getItem(STORAGE_KEY_REFRESH);
      const storedUser = localStorage.getItem(STORAGE_KEY_USER);

      if (storedAccess) {
        accessToken.value = storedAccess;
        accessCookie.value = storedAccess;
      }
      if (storedRefresh) {
        refreshToken.value = storedRefresh;
        refreshCookie.value = storedRefresh;
      }
      if (storedUser) {
        try {
          const parsed = JSON.parse(storedUser);
          user.value = parsed;
          userCookie.value = parsed;
        } catch {
          user.value = null;
        }
      }
    }
  }

  function hasRole(requiredRole: string): boolean {
    const currentUser = user.value || userCookie.value;
    if (!currentUser) return false;
    const hierarchy: Record<string, number> = {
      Member: 1,
      Admin: 2,
      Owner: 3,
      "Super Admin": 4,
    };
    const userWeight = hierarchy[currentUser.role] || 0;
    const requiredWeight = hierarchy[requiredRole] || 0;
    return userWeight >= requiredWeight;
  }

  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    login,
    logout,
    refreshSession,
    initAuth,
    hasRole,
  };
}
