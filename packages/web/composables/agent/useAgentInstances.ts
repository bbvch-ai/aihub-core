import { type FullAgentInstanceDto, getAllAgentInstances } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useAgentInstances = defineQuery((options?: { online?: boolean }) => {
  const { tenantId } = useTenant()

  const { data: agentInstances, isPending: agentInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['tenant', tenantId.value, 'agent-instances', options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getAllAgentInstances({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
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
