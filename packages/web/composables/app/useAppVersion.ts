import { getHealth } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

// Surfaces the running version of both services. The UI service version is baked
// into the static bundle at build time (runtimeConfig.public.appVersion); the API
// version is read from the health endpoint. When both match a single number is
// shown, otherwise both are shown as `UI / API`.
//
// A release is promoted by retagging the exact `-rc.N` build that was tested, so
// the baked version keeps its release-candidate suffix (e.g. `v0.317.0-rc.3`)
// even though the artifact IS the final release. Strip that suffix so a promoted
// build shows its release version (`v0.317.0`). Rolling-channel builds
// (`-nightly.N` / `-staging.N`) keep their suffix so they stay identifiable.
const toReleaseVersion = (version: string): string => version.replace(/-rc\.\d+$/, '')

export const useAppVersion = defineQuery(() => {
  const uiVersion = toReleaseVersion(useRuntimeConfig().public.appVersion as string)

  const { data: apiVersion } = useQuery<string>({
    key: () => ['app-version', 'api'],
    staleTime: minutesToMilliseconds(60),
    query: async () => {
      const health = await getHealth({ composable: '$fetch' })
      return toReleaseVersion(health.version)
    },
  })

  const versionDisplay = computed(() => {
    const api = apiVersion.value
    if (!api || api === uiVersion) return uiVersion
    return `${uiVersion} / ${api}`
  })

  return { uiVersion, apiVersion, versionDisplay }
})
