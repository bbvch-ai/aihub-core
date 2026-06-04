import { getHealth } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

// Surfaces the running version of both services. The UI service version is baked
// into the static bundle at build time (runtimeConfig.public.appVersion); the API
// version is read from the health endpoint. When both match a single number is
// shown, otherwise both are shown as `UI / API`.
export const useAppVersion = defineQuery(() => {
  const uiVersion = useRuntimeConfig().public.appVersion as string

  const { data: apiVersion } = useQuery<string | undefined>({
    key: () => ['app-version', 'api'],
    staleTime: minutesToMilliseconds(60),
    query: async () => {
      const health = await getHealth({ composable: '$fetch', baseURL: '/api/v1' })
      return health.version ?? undefined
    },
  })

  const versionDisplay = computed(() => {
    const api = apiVersion.value
    if (!api || api === uiVersion) return uiVersion
    return `${uiVersion} / ${api}`
  })

  return { uiVersion, apiVersion, versionDisplay }
})
