import { client } from '@core/sdk/client/client.gen'

// Configures the @swiss-ai-hub/web SDK client (`@core/sdk/client`) that every
// composable shipped in this layer uses.
//
// This MUST live in a plugin, not in app.vue: app.vue is app-singular, so any
// app that EXTENDS this layer (@swiss-ai-hub/sysadmin-web, or a customer UI)
// supplies its own app.vue and the layer's app.vue never runs — leaving the
// SDK client unconfigured and every inherited layer composable firing against
// an unconfigured client. Plugins, by contrast, run in every extender.
//
// Where the AI-Hub API lives is the layer's extension point. The base URL is
// resolved once by 0.runtime-config.client.ts (which runs first — numeric
// filename prefix) into `runtimeConfig.public.apiBaseUrl`:
//   - dev: from .env via .app/nuxt.config.ts (defaults to same-origin /api/v1)
//   - prod container: from API_BASE_URL in window.__AIHUB_CONFIG__ (/config.js)
// web leaves it at the same-origin default; sysadmin-web (and customers whose
// UI is on a different origin than the API) point it at the API instance.
export default defineNuxtPlugin((nuxtApp) => {
  const publicConfig = useRuntimeConfig().public as Record<string, unknown>
  const { getToken } = useAuth()

  const baseURL = (publicConfig.apiBaseUrl as string) || '/api/v1'

  client.setConfig({
    baseURL,
    // getToken() throws when the user is not logged in; auth-optional
    // endpoints (e.g. auth providers on the login page) still resolve.
    auth: async () => await getToken(),
    onRequest: ({ options }) => {
      const locale = (nuxtApp.$i18n as { locale?: { value?: string } } | undefined)?.locale?.value
      if (locale) options.headers.set('lang', locale)
    },
    onResponseError: ({ response }) => {
      console.error('AI-Hub API error', response.status, response._data?.detail)
    },
  })
})
