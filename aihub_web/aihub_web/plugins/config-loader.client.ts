// plugins/config-loader.client.ts
export default defineNuxtPlugin(async () => {
  const isConfigLoaded = useState('isConfigLoaded', () => false)

  // In dev, config is already loaded from .env. We just set loading to complete.
  if (process.env.DEV) {
    isConfigLoaded.value = true
    return
  }

  // This part now only runs in the production container
  try {
    const appConfig = await $fetch('/config.json')
    const publicConfig = useRuntimeConfig().public

    // Merge the fetched config into the runtimeConfig
    publicConfig.oidc.clientId = appConfig.AZURE_AD_CLIENT_ID
    publicConfig.oidc.tenantId = appConfig.AZURE_AD_TENANT_ID
    publicConfig.webui.url = appConfig.WEBUI_URL
    publicConfig.ws.endpoint = appConfig.WS_ENDPOINT
  }
  catch (error) {
    console.error('Could not load runtime configuration:', error)
  }
  finally {
    isConfigLoaded.value = true
  }
})
