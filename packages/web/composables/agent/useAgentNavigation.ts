import type { NavItem } from '@core/types/NavItem'

export function useAgentNavigation() {
  const router = useRouter()
  const route = useRoute()
  const tenantPath = useTenantPath()
  const { t } = useI18n()

  const navItems = computed<NavItem[]>(() => [
    {
      name: t('agent.tabs.myAgents'),
      key: 'agents',
      path: '/service/agents',
      isActive: () => route.path.startsWith(tenantPath('/service/agents')) && !route.path.includes('/service/agents/templates'),
    },
    {
      name: t('agent.tabs.templates'),
      key: 'templates',
      path: '/service/agents/templates',
      isActive: () => route.path.includes('/service/agents/templates'),
    },
  ])

  const activeNavItem = computed<NavItem | undefined>(() => {
    return navItems.value.find((navItem: NavItem) => navItem.isActive())
  })

  const toNavItem = (navItem: NavItem | null) => {
    if (navItem) {
      router.push(tenantPath(navItem.path))
    }
  }

  return { navItems, activeNavItem, toNavItem }
}
