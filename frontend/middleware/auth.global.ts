/**
 * Global navigation guard: enforces authentication across all routes.
 * Redirects unauthenticated visitors to /login.
 */
import { useAuth } from "~/composables/useAuth";

export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuth();
  auth.initAuth();

  const isLoginRoute = to.path === "/login";

  if (!auth.isAuthenticated.value) {
    if (!isLoginRoute) {
      const redirectQuery = to.fullPath && to.fullPath !== "/" ? `?redirect=${encodeURIComponent(to.fullPath)}` : "";
      return navigateTo(`/login${redirectQuery}`);
    }
  } else {
    if (isLoginRoute) {
      const redirectTarget = (to.query.redirect as string) || "/";
      return navigateTo(redirectTarget);
    }
  }
});
