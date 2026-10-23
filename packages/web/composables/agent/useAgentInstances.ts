import { type FullAgentInstanceDto, getAllAgentInstances } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useAgentInstances = defineQuery(() => {
  const { tenantId } = useTenant()
  // The search lives in the URL, not in this app-wide query's state, so it cannot filter agent lists on other pages.
  const searchQuery = useRouteQuery<string>('agent_search', '')
  const agentClass = useRouteQuery<string | null>('agent_type', null)
  const status = useRouteQuery<string | null>('agent_status', null)

  const debouncedSearch = refDebounced(searchQuery, 300)
  // Leaving the page empties the search at once; waiting out the debounce would serve the next page the filtered list.
  const activeSearch = computed(() => (searchQuery.value ? debouncedSearch.value : ''))

  const getOnlineStatus = () => {
    if (status.value === 'enabled') return true
    if (status.value === 'disabled') return false
    return undefined
  }

  const { data: agentInstances, isPending: agentInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['tenant', tenantId.value, 'agent-instances', status.value, agentClass.value, activeSearch.value],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    placeholderData: previousData => previousData,
    query: async () => {
      return await getAllAgentInstances({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
        query: {
          online: getOnlineStatus(),
          agent_class: agentClass.value || undefined,
          search: activeSearch.value || undefined,
        },
      })
    },
  })

  return {
    agentInstances,
    agentInstancesAreLoading,
    searchQuery,
    agentClass,
    status,
  }
})
