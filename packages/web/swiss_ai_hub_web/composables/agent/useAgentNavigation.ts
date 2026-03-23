import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

export function useAgentNavigation() {
  const router = useRouter()
  const route = useRoute()
  const localePath = useLocalePath()
  const { t } = useI18n()

  const navItems = computed<NavItem[]>(() => [
    {
      name: t('agent.tabs.myAgents'),
      key: 'agents',
      path: '/service/agents',
      isActive: () => route.path.startsWith(localePath('/service/agents')) && !route.path.includes('/service/agents/templates'),
    },
    {
      name: t('agent.tabs.templates'),
      key: 'templates',
      path: '/service/agents/templates',
      isActive: () => route.path.includes('/service/agents/templates'),
    },
  ])

  const activeNavItem = computed<NavItem | undefined>(() => {
    return navItems.value.filter(navItem => navItem.isActive())[0]
  })

  const toNavItem = (navItem: NavItem | null) => {
    if (navItem) {
      router.push(localePath(navItem.path))
    }
  }

  return { navItems, activeNavItem, toNavItem }
}
