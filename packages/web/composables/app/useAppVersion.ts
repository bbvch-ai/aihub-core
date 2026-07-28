import { getHealth } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

// Surfaces the running version of both services. The UI service version is baked
// into the static bundle at build time (runtimeConfig.public.appVersion); the API
// version is read from the health endpoint, which reports the channel tag (e.g.
// `latest`) the running image was pulled as. When both match a single number is
// shown, otherwise both are shown as `UI / API`.
//
// A release is promoted onto the `latest` channel by retagging the exact `-rc.N`
// build that was tested, so the baked version keeps its release-candidate suffix
// (e.g. `v0.317.0-rc.3`) even though the artifact IS the final release. Strip that
// suffix only on the `latest` channel, so a promoted build shows its release
// version (`v0.317.0`). On any other channel the build is genuinely a candidate or
// rolling build, so keep the suffix to stay identifiable.
const RELEASE_CHANNEL = 'latest'
const toReleaseVersion = (version: string): string => version.replace(/-rc\.\d+$/, '')

export const useAppVersion = defineQuery(() => {
  const bakedUiVersion = useRuntimeConfig().public.appVersion as string

  const { data: apiVersion } = useQuery<string>({
    key: () => ['app-version', 'api'],
    staleTime: minutesToMilliseconds(60),
    query: async () => {
      const health = await getHealth({ composable: '$fetch' })
      return health.version
    },
  })

  const uiVersion = computed(() =>
    apiVersion.value === RELEASE_CHANNEL ? toReleaseVersion(bakedUiVersion) : bakedUiVersion,
  )

  const versionDisplay = computed(() => {
    const api = apiVersion.value
    if (!api || api === uiVersion.value) return uiVersion.value
    return `${uiVersion.value} / ${api}`
  })

  return { uiVersion, apiVersion, versionDisplay }
})
