import { getSuite, type ServiceDto, type SuiteDto } from '@core/sdk/client'
import type { MenuItem } from 'primevue/menuitem'
import { useLocalePath } from '#i18n'

export const useSuiteStore = defineStore('suite', () => {
  const router = useRouter()
  const localePath = useLocalePath()

  const {
    data: suite,
    status: loadingSuite,
    refresh: refreshSuite,
    refetch: refetchSuite,
  } = useQuery<SuiteDto>({
    key: ['suite'],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getSuite({
        composable: '$fetch',
      })
    },
  })

  const apps = computed<MenuItem>(() => {
    const suiteApps = suite.value?.services.map((service: ServiceDto) => ({
      label: service.name,
      description: service.description,
      icon: service.icon,
      path: service.path,
    } satisfies MenuItem
    )) ?? []
    return [
      { icon: 'material-symbols:home', label: 'Home', path: '/' },
      ...suiteApps,
    ].filter((app: MenuItem) => router.resolve(localePath(app.path)).matched.length > 0)
  })

  return {
    suite,
    loadingSuite,
    refreshSuite,
    refetchSuite,
    apps,
  }
})
