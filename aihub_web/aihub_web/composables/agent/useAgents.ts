import { type AgentDto, getAgents } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useAgents = defineQuery(() => {
  const { data: agents, isPending: agentsAreLoading } = useQuery<AgentDto[]>({
    key: () => ['agents'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getAgents({
        composable: '$fetch',
      })
    },
  })
  return {
    agents,
    agentsAreLoading,
  }
})
