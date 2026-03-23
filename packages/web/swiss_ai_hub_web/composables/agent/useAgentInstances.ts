import { type FullAgentInstanceDto, getAllAgentInstances } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useAgentInstances = defineQuery((options?: { online?: boolean }) => {
  const { data: agentInstances, isPending: agentInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['agent-instances', options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getAllAgentInstances({
        composable: '$fetch',
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
