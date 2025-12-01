import { type AgentDto, getAgent } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useAgent = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('agent_id', 'agent_class')

  const { data: agent, isPending: agentIsLoading } = useQuery<AgentDto>({
    key: () => ['agents', route.params.agent_class as string, route.params.agent_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
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
