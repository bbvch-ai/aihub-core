import { type AgentDto, getAgents } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useAgents = defineQuery(() => {
  const { data: agents, isPending: agentsAreLoading } = useQuery<AgentDto[]>({
    key: () => ['agents'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      try {
        return await getAgents({
          composable: '$fetch',
        })
      }
      catch (error: any) {
        // If user doesn't have permission to view agents, return empty array
        // This prevents 403 errors from breaking the dashboard UI
        if (error?.status === 403 || error?.statusCode === 403) {
          return []
        }
        throw error
      }
    },
  })
  return {
    agents,
    agentsAreLoading,
  }
})
