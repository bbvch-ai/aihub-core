// Loads sysadmin-web-specific runtime config (MAIN_API_URL) from /config.json
// in the production container. The inherited @swiss-ai-hub/web
// `config-loader.client.ts` only knows OAUTH_*/WEBUI_URL/WS_ENDPOINT, so it
// populates `oidc` for us but never `mainApi.url`. This additive plugin fills
// that gap. It runs after the layer's config-loader (Nuxt runs layer plugins
// before the app's own plugins), so `oidc` is already loaded by then.
export default defineNuxtPlugin(async () => {
  const publicConfig = useRuntimeConfig().public

  // In dev, mainApi.url is already set from process.env via .app/nuxt.config.ts.
  if (publicConfig.env === 'dev') return

  try {
    const appConfig = await $fetch<{ MAIN_API_URL?: string }>('/config.json')
    if (appConfig?.MAIN_API_URL) {
      publicConfig.mainApi.url = appConfig.MAIN_API_URL
    }
  }
  catch (error) {
    console.error('sysadmin-config: could not load /config.json for MAIN_API_URL', error)
  }
})
