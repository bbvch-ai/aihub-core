// LiteLLM v1.106.4 keeps the usage view and its customer filter in component
// state, so no URL opens Customer Usage already filtered to a tenant: every
// link lands on the usage page and the sysadmin picks the tenant there.
const USAGE_PATH = '/ui/usage/'

export function useLiteLlmUsage() {
  const config = useRuntimeConfig()

  const usageUrl = computed(() => {
    const adminUrl = (config.public.litellm as { url?: string } | undefined)?.url ?? ''
    if (!adminUrl) return ''
    const origin = adminUrl.endsWith('/') ? adminUrl.slice(0, -1) : adminUrl
    return `${origin}${USAGE_PATH}`
  })

  const isAvailable = computed(() => usageUrl.value !== '')

  return { usageUrl, isAvailable }
}
