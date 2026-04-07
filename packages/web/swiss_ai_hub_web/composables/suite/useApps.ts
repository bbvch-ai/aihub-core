import type { ServiceDto } from '@core/sdk/client'
import type { MenuItem } from 'primevue/menuitem'

export const useApps = () => {
  const { suite, suiteIsLoading } = useSuite()
  const router = useRouter()
  const tenantPath = useTenantPath()

  const apps = computed<MenuItem>(() => {
    const suiteApps = suite.value?.services.map((service: ServiceDto) => ({
      label: service.name,
      description: service.description,
      icon: service.icon,
      path: service.path,
      isAdmin: service.user_is_admin ?? false,
    } satisfies MenuItem
    )) ?? []
    return [
      { icon: 'material-symbols:home', label: 'Home', path: '/' },
      ...suiteApps,
    ].filter((app: MenuItem) => {
      const resolved = app.path === '/' ? tenantPath('/') : tenantPath(app.path)
      return router.resolve(resolved).matched.length > 0
    })
  })

  return {
    apps,
    appsLoading: suiteIsLoading,
  }
}
