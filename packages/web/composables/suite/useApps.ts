import type { ServiceDto } from '@core/sdk/client'
import type { MenuItem } from 'primevue/menuitem'

export const useApps = () => {
  const { suite, suiteError, suiteIsLoading } = useSuite()
  const router = useRouter()
  const tenantPath = useTenantPath()

  const apps = computed<MenuItem>(() => {
    // `services` is non-optional on SuiteDto, so the type system cannot catch a
    // cached value that is not actually a SuiteDto. It used to be reachable: a
    // proxy answering 200 text/html for a downed API landed here as a raw HTML
    // string and `.services.map` threw inside this computed, taking down every
    // page on the default layout. The SDK guard now rejects that response; this
    // stays as the last line of defence.
    const services = Array.isArray(suite.value?.services) ? suite.value.services : []

    const suiteApps = services.map((service: ServiceDto) => ({
      label: service.name,
      description: service.description,
      icon: service.icon,
      path: service.path,
      isAdmin: service.user_is_admin ?? false,
    } satisfies MenuItem
    ))
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
    appsError: suiteError,
  }
}
