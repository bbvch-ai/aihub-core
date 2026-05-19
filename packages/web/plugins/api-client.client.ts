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
// Where the AI-Hub API lives is the layer's extension point:
//   - dev: `runtimeConfig.public.apiBaseUrl` (defaults to same-origin /api/v1)
//   - prod container: `API_BASE_URL` in /config.json (envsubst'd at startup)
// web leaves it at the same-origin default; sysadmin-web (and customers whose
// UI is on a different origin than the API) point it at the API instance.
//
// Self-contained on purpose: it resolves its own base URL (incl. reading
// /config.json itself in prod) so it does not depend on plugin ordering
// relative to config-loader.client.ts.
export default defineNuxtPlugin(async (nuxtApp) => {
  const publicConfig = useRuntimeConfig().public as Record<string, unknown>
  const { getToken } = useAuth()

  let baseURL = (publicConfig.apiBaseUrl as string) || '/api/v1'
  if (publicConfig.env !== 'dev') {
    try {
      const appConfig = (await $fetch('/config.json')) as { API_BASE_URL?: string }
      if (appConfig?.API_BASE_URL) baseURL = appConfig.API_BASE_URL
    }
    catch (error) {
      console.error('api-client: could not load /config.json for API_BASE_URL; using', baseURL, error)
    }
  }

  client.setConfig({
    baseURL,
    // Identical to the layer's app.vue contract: getToken() throws when the
    // user is not logged in; auth-optional endpoints (e.g. auth providers on
    // the login page) still resolve. Behaviour unchanged from web's app.vue.
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
