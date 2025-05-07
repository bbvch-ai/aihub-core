import { type AgentDto, getAgents } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'

export const useAgents = defineQuery(() => {
  const { data: agents, isLoading: agentsAreLoading } = useQuery<AgentDto[]>({
    key: () => ['agents'],
    staleTime: 1000 * 60 * 5, // 5 minutes
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
