import type { ServiceDto } from '@core/sdk/client'
import type { MenuItem } from 'primevue/menuitem'

import { useLocalePath } from '#i18n'

export const useApps = () => {
  const { suite, suiteIsLoading } = useSuite()
  const router = useRouter()
  const localePath = useLocalePath()

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
    ].filter((app: MenuItem) => router.resolve(localePath(app.path)).matched.length > 0)
  })

  return {
    apps,
    appsLoading: suiteIsLoading,
  }
}
