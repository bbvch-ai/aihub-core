import { type FullAgentInstanceDto, getAgentClassInstances } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useAgentClassInstances = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('agent_class')

  const { data: agentClassInstances, isPending: agentClassInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['agent-class-instances', route.params.agent_class as string],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
    query: async () => {
      return await getAgentClassInstances({
        composable: '$fetch',
        path: {
          agent_class: route.params.agent_class as string,
        },
      })
    },
  })
  return {
    agentClassInstances,
    agentClassInstancesAreLoading,
  }
})
