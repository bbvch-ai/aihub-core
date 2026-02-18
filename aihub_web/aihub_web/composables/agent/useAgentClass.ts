import { type AgentClassDtoReadable, getAgentClass } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useAgentClass = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('agent_class')

  const { data: agentClass, isPending: agentClassIsLoading } = useQuery<AgentClassDtoReadable>({
    key: () => ['agent-classes', route.params.agent_class as string],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
    query: async () => {
      return await getAgentClass({
        composable: '$fetch',
        path: {
          agent_class: route.params.agent_class as string,
        },
      })
    },
  })
  return {
    agentClass,
    agentClassIsLoading,
  }
})
