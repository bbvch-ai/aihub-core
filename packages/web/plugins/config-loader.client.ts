// Loads runtime configuration from /config.json in the production container.
//
// This plugin ships in the @swiss-ai-hub/web Nuxt layer and therefore also
// runs in any app that EXTENDS the layer (e.g. @swiss-ai-hub/sysadmin-web, or
// a customer UI). Downstream apps may declare only the subset of
// runtimeConfig.public keys they actually use — so this loader must write
// defensively: only into config groups the consuming app declared, and only
// from config.json keys that are present. It must never assume its own host
// app's full runtimeConfig shape, or it breaks every extender.
export default defineNuxtPlugin(async () => {
  const isConfigLoaded = useState('isConfigLoaded', () => false)
  const publicConfig = useRuntimeConfig().public as Record<string, Record<string, unknown>>

  // In dev, config is already loaded from .env. We just set loading to complete.
  if (publicConfig.env === 'dev') {
    isConfigLoaded.value = true
    return
  }

  // Assigns `value` to `group[key]` only if the consuming app declared `group`
  // and `value` is defined. A missing group simply means this extender does
  // not use that part of the config.
  const assignIfPresent = (
    group: Record<string, unknown> | undefined,
    key: string,
    value: unknown,
  ): void => {
    if (group && value !== undefined) group[key] = value
  }

  try {
    const appConfig = (await $fetch('/config.json')) as Record<string, unknown>

    assignIfPresent(publicConfig.oidc, 'clientId', appConfig.OAUTH_CLIENT_ID)
    assignIfPresent(publicConfig.oidc, 'authorityUrl', appConfig.OAUTH_AUTHORITY_URL)
    assignIfPresent(publicConfig.webui, 'url', appConfig.WEBUI_URL)
    assignIfPresent(publicConfig.ws, 'endpoint', appConfig.WS_ENDPOINT)
  }
  catch (error) {
    console.error('Could not load runtime configuration:', error)
  }
  finally {
    isConfigLoaded.value = true
  }
})
