import { type FullAgentInstanceDto, getAllAgentInstances } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useAgentInstances = defineQuery((options?: { online?: boolean }) => {
  const { tenantId } = useTenant()

  const { data: agentInstances, isPending: agentInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['agent-instances', tenantId.value, options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantId.value),
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
