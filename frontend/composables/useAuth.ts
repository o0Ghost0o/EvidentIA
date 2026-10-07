/**
 * Authentication and session management composable:
 * Dual JWT tokens (15-minute access token, 7-day refresh token) with automatic rotation and RBAC.
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
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value);

  function saveSession(tokens: TokenResponse) {
    accessToken.value = tokens.access_token;
    refreshToken.value = tokens.refresh_token;
    user.value = tokens.user;

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
    if (!refreshToken.value || isRefreshing.value) return false;
    isRefreshing.value = true;
    try {
      const res = await $fetch<TokenResponse>("/api/auth/refresh", {
        method: "POST",
        body: { refresh_token: refreshToken.value },
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
    const token = refreshToken.value;
    clearSession();
    if (token) {
      await $fetch("/api/auth/logout", {
        method: "POST",
        body: { refresh_token: token },
      }).catch(() => {});
    }
  }

  function initAuth() {
    if (!import.meta.client) return;
    const storedAccess = localStorage.getItem(STORAGE_KEY_ACCESS);
    const storedRefresh = localStorage.getItem(STORAGE_KEY_REFRESH);
    const storedUser = localStorage.getItem(STORAGE_KEY_USER);

    if (storedAccess) accessToken.value = storedAccess;
    if (storedRefresh) refreshToken.value = storedRefresh;
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser);
      } catch {
        user.value = null;
      }
    }
  }

  function hasRole(requiredRole: string): boolean {
    if (!user.value) return false;
    const hierarchy: Record<string, number> = {
      Member: 1,
      Admin: 2,
      Owner: 3,
      "Super Admin": 4,
    };
    const userWeight = hierarchy[user.value.role] || 0;
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
