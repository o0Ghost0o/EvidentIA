/** Typed fetch against the BFF (/api/* → FastAPI) with automatic JWT bearer attachment and refresh rotation. */
import { useAuth } from "~/composables/useAuth";

export async function api<T>(
  path: string,
  opts: { method?: string; body?: unknown; query?: Record<string, string>; headers?: Record<string, string> } = {}
): Promise<T> {
  const auth = useAuth();
  const headers: Record<string, string> = { ...(opts.headers || {}) };

  if (auth.accessToken.value) {
    headers["authorization"] = `Bearer ${auth.accessToken.value}`;
  }

  const cleanPath = path.replace(/^\//, "");

  try {
    return await $fetch<T>(`/api/${cleanPath}`, {
      method: (opts.method || "GET") as "GET",
      body: opts.body,
      query: opts.query,
      headers,
    });
  } catch (error: any) {
    // If access token expired (15m elapsed) and refresh token exists, attempt rotation and retry once
    if (error?.status === 401 && auth.refreshToken.value && !cleanPath.startsWith("auth/")) {
      const refreshed = await auth.refreshSession();
      if (refreshed && auth.accessToken.value) {
        headers["authorization"] = `Bearer ${auth.accessToken.value}`;
        return await $fetch<T>(`/api/${cleanPath}`, {
          method: (opts.method || "GET") as "GET",
          body: opts.body,
          query: opts.query,
          headers,
        });
      }
    }
    throw error;
  }
}
