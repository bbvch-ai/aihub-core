export default defineNuxtPlugin(async () => {
  const isConfigLoaded = useState('isConfigLoaded', () => false)
  const publicConfig = useRuntimeConfig().public

  // In dev, config is already loaded from .env. We just set loading to complete.
  if (publicConfig.env === 'dev') {
    isConfigLoaded.value = true
    return
  }

  // This part now only runs in the production container
  try {
    const appConfig = await $fetch('/config.json')

    console.log('Loaded runtime configuration:', appConfig, publicConfig)

    // Merge the fetched config into the runtimeConfig
    publicConfig.oidc.clientId = appConfig.OAUTH_CLIENT_ID
    publicConfig.oidc.authorityUrl = appConfig.OAUTH_AUTHORITY_URL
    publicConfig.webui.url = appConfig.WEBUI_URL
    publicConfig.langfuse.url = appConfig.LANGFUSE_BASEURL
    publicConfig.langfuse.projectId = appConfig.LANGFUSE_INIT_PROJECT_ID
    publicConfig.ws.endpoint = appConfig.WS_ENDPOINT
  }
  catch (error) {
    console.error('Could not load runtime configuration:', error)
  }
  finally {
    isConfigLoaded.value = true
  }
})
