// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2024-08-01",
  devtools: { enabled: false },
  modules: ["@nuxtjs/tailwindcss"],
  css: ["~/assets/css/tailwind.css"],
  runtimeConfig: {
    // Server-only: the browser talks to the Nuxt BFF, the BFF talks here.
    backendUrl: process.env.NUXT_BACKEND_URL || "http://localhost:8000",
  },
  nitro: {
    preset: "node-server",
  },
});
