import { type FullAgentInstanceDto, getAllAgentInstances } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useAgentInstances = defineQuery((options?: { online?: boolean }) => {
  const { tenantName } = useTenantFromRoute()

  const { data: agentInstances, isPending: agentInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['agent-instances', tenantName.value, options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getAllAgentInstances({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
        query: {
          online: options?.online,
        },
      })
    },
  })
  return {
    agentInstances,
    agentInstancesAreLoading,
  }
})
