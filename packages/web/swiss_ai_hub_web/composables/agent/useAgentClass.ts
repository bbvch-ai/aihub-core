import { type AgentClassDtoReadable, getAgentClass } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useAgentClass = defineQuery(() => {
  const route = useRoute()
  const { tenantName } = useTenant()
  const isRouteReady = useRouteReady('agent_class')

  const { data: agentClass, isPending: agentClassIsLoading } = useQuery<AgentClassDtoReadable>({
    key: () => ['agent-classes', tenantName.value, route.params.agent_class as string],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => isRouteReady.value && !!tenantName.value),
    query: async () => {
      return await getAgentClass({
        composable: '$fetch',
        path: {
          tenant_id: tenantName.value!,
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
