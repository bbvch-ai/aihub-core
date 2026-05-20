// The ONE place runtime configuration enters the app.
//
// In a production container, nginx envsubst's config.template.js into
// /config.js, which index.html loads as a classic <script> in <head> — so
// `window.__AIHUB_CONFIG__` is already populated, synchronously, before any
// Nuxt plugin runs. This plugin maps it into `runtimeConfig.public` so every
// existing downstream reader (oidc-client, api-client, composables) keeps
// working unchanged. No $fetch, no async, no plugin-ordering concerns — which
// is why it replaced three separate config.json-fetching plugins.
//
// The numeric `0.` filename prefix makes this the first plugin in the layer
// so api-client.client.ts (and any extender plugin) sees a fully-populated
// runtimeConfig.
//
// Ships in the @swiss-ai-hub/web layer, so it also runs in extenders
// (@swiss-ai-hub/sysadmin-web, customer UIs). It writes defensively: only into
// config groups the consuming app declared, and only from injected keys that
// are present, so an extender that uses a subset of the config is unaffected.
export default defineNuxtPlugin(() => {
  const isConfigLoaded = useState('isConfigLoaded', () => false)
  const publicConfig = useRuntimeConfig().public as Record<string, unknown>

  // Dev: values are already injected from .env via .app/nuxt.config.ts and
  // there is no nginx to produce /config.js — nothing to map.
  if (publicConfig.env === 'dev') {
    isConfigLoaded.value = true
    return
  }

  const injected
    = (window as unknown as { __AIHUB_CONFIG__?: Record<string, string> }).__AIHUB_CONFIG__ ?? {}

  const group = (name: string): Record<string, unknown> | undefined =>
    publicConfig[name] as Record<string, unknown> | undefined

  // Assigns only when the consuming app declared `target` and the injected
  // value is a non-empty string (envsubst leaves unset vars as '').
  const assign = (
    target: Record<string, unknown> | undefined,
    key: string,
    value: string | undefined,
  ): void => {
    if (target && value) target[key] = value
  }

  assign(group('oidc'), 'clientId', injected.OAUTH_CLIENT_ID)
  assign(group('oidc'), 'authorityUrl', injected.OAUTH_AUTHORITY_URL)
  assign(group('webui'), 'url', injected.WEBUI_URL)
  assign(group('ws'), 'endpoint', injected.WS_ENDPOINT)
  assign(group('sysadmin'), 'url', injected.SYSADMIN_URL)
  assign(group('mainApp'), 'url', injected.MAIN_APP_URL)
  if (injected.API_BASE_URL) publicConfig.apiBaseUrl = injected.API_BASE_URL

  isConfigLoaded.value = true
})
