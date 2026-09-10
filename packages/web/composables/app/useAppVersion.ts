import { getHealth } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

// Surfaces the running version of both services. The UI service version is baked
// into the static bundle at build time (runtimeConfig.public.appVersion); the API
// version is read from the health endpoint. When both agree a single number is
// shown, otherwise both are shown as `UI / API`.
//
// A release is promoted by retagging the exact `-rc.N` build that was tested, so
// the baked UI version keeps its release-candidate suffix (e.g. `v0.317.0-rc.3`)
// even though the artifact IS the final release. A container cannot read its own
// image tag, so the release has to be inferred from what the API reports, and the
// two deployment flavours report it differently: docker-compose pins the channel
// tag (`latest`), while Helm pins an exact `vX.Y.Z` per instance and leaves the
// API on its package metadata (`0.319.0`). Both are release signals; on either
// one the suffix is dropped so a promoted build shows its release version.
//
// Versions are compared with the leading `v` normalised away, because one side is
// a git tag (`v0.319.0`) and the other Python package metadata (`0.319.0`) — the
// same version, and rendering it as `UI / API` would read as skew.
//
// Every other case is genuinely a candidate or a rolling build (another channel
// such as `staging`, an API pinned to an explicit `-rc.N`, a nightly), so the
// suffix stays to keep the build identifiable.
const RELEASE_CHANNEL = 'latest'
const RC_SUFFIX = /-rc\.\d+$/
const toReleaseVersion = (version: string): string => version.replace(RC_SUFFIX, '')
const toComparable = (version: string): string => version.replace(/^v/, '')

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

  // An API version that still carries `-rc.N` can never equal the stripped UI
  // version, so a candidate deployment fails this check without a separate guard.
  const isReleaseDeployment = computed(() => {
    const api = apiVersion.value
    if (!api) return false
    return api === RELEASE_CHANNEL || toComparable(api) === toComparable(toReleaseVersion(bakedUiVersion))
  })

  const uiVersion = computed(() =>
    isReleaseDeployment.value ? toReleaseVersion(bakedUiVersion) : bakedUiVersion,
  )

  const versionDisplay = computed(() => {
    const api = apiVersion.value
    if (!api || toComparable(api) === toComparable(uiVersion.value)) return uiVersion.value
    return `${uiVersion.value} / ${api}`
  })

  return { uiVersion, apiVersion, versionDisplay }
})
