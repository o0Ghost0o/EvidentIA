// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2024-08-01",
  devtools: { enabled: false },
  modules: ["@nuxtjs/tailwindcss"],
  css: ["~/assets/css/tailwind.css"],
  // Auto-register only .vue components so shadcn-vue barrel files (ui/*/index.ts)
  // don't collide with their same-named Dialog.vue / Sheet.vue entrypoints.
  components: [{ path: "~/components", extensions: ["vue"] }],
  app: {
    head: {
      link: [
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap",
        },
      ],
    },
  },
  runtimeConfig: {
    // Server-only: the browser talks to the Nuxt BFF, the BFF talks here.
    backendUrl: process.env.NUXT_BACKEND_URL || "http://localhost:8000",
    togetherApiKey: process.env.TOGETHER_API_KEY || "",
    togetherBaseUrl: process.env.TOGETHER_BASE_URL || "https://api.together.xyz/v1",
    openaiApiKey: process.env.OPENAI_API_KEY || "",
    llmModel: process.env.LLM_MODEL || "meta-llama/Llama-3.3-70B-Instruct-Turbo",
  },
  nitro: {
    preset: "node-server",
  },
});
