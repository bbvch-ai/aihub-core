import { type AgentDto, getAgent } from '@core/sdk/client'
import { useRoute } from 'vue-router'

export const useAgent = defineQuery(() => {
  const route = useRoute()
  const { data: agent, isPending: agentIsLoading } = useQuery<AgentDto>({
    key: () => ['agent', route.params.agent_class as string, route.params.agent_id as string],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getAgent({
        composable: '$fetch',
        path: {
          agent_id: route.params.agent_id as string,
          agent_class: route.params.agent_class as string,
        },
      })
    },
  })
  return {
    agent,
    agentIsLoading,
  }
})
