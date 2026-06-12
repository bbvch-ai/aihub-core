import { type FullAgentInstanceDto, getAllAgentInstances } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useAgentInstances = defineQuery(() => {
  const { tenantId } = useTenant()
  const searchQuery = ref<string | null>(null)
  const agentClass = useRouteQuery<string | null>('agent_type', null)
  const status = useRouteQuery<string | null>('agent_status', null)

  const debouncedSearch = refDebounced(searchQuery, 300)

  const getOnlineStatus = () => {
    if (status.value === 'enabled') return true
    if (status.value === 'disabled') return false
    return undefined
  }

  const { data: agentInstances, isPending: agentInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['tenant', tenantId.value, 'agent-instances', status.value, agentClass.value, debouncedSearch.value],
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
          search: debouncedSearch.value || undefined,
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
