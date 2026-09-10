import { getHealth } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

// Surfaces the running version of both services. When both name the same release
// a single version is shown, otherwise both are shown as `UI / API` so a genuine
// skew — one service rolled, the other not — stays visible.
//
// Neither container can know its own version at build time: a release is promoted
// by retagging the exact `-rc.N` build that was tested, so anything baked into an
// image keeps the candidate's name even though the artifact IS the final release.
// The deployment is the only party that knows the tag it pulled, so both sides
// take their version from it — the UI through APP_VERSION in /config.js (see
// plugins/0.runtime-config.client.ts), the API through its AIHUB_VERSION env var.
// Each falls back to its build-time value when the deployment injects nothing,
// which is why a promoted build can still report `-rc.N` on one side only.
//
// docker-compose is the one flavour that pins a rolling channel tag instead of an
// exact version, so it reports the channel name (`latest`) rather than a number.
//
// Versions are compared with the leading `v` normalised away, because one side is
// a git tag (`v0.319.0`) and the other can be Python package metadata (`0.319.0`)
// — the same version, and rendering it as `UI / API` would read as skew.
const RELEASE_CHANNEL = 'latest'
const RC_SUFFIX = /-rc\.\d+$/
const toReleaseVersion = (version: string): string => version.replace(RC_SUFFIX, '')
const toComparable = (version: string): string => toReleaseVersion(version.replace(/^v/, ''))

export const useAppVersion = defineQuery(() => {
  const declaredUiVersion = useRuntimeConfig().public.appVersion as string

  const { data: apiVersion } = useQuery<string>({
    key: () => ['app-version', 'api'],
    staleTime: minutesToMilliseconds(60),
    query: async () => {
      const health = await getHealth({ composable: '$fetch' })
      return health.version
    },
  })

  // The one version both services agree on, or null when they genuinely differ.
  const agreedVersion = computed(() => {
    const api = apiVersion.value
    if (!api) return declaredUiVersion
    if (api === RELEASE_CHANNEL) return toReleaseVersion(declaredUiVersion)
    if (toComparable(api) !== toComparable(declaredUiVersion)) return null
    // Same release. If either side reports the promoted, suffix-free name then
    // that is what this deployment is; if both still carry `-rc.N` it really is a
    // candidate build and the suffix stays to keep it identifiable.
    return RC_SUFFIX.test(declaredUiVersion) ? api : declaredUiVersion
  })

  const uiVersion = computed(() => agreedVersion.value ?? declaredUiVersion)

  const versionDisplay = computed(
    () => agreedVersion.value ?? `${declaredUiVersion} / ${apiVersion.value}`,
  )

  return { uiVersion, apiVersion, versionDisplay }
})
