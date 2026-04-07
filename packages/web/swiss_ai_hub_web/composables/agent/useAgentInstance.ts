import { type FullAgentInstanceDto, getAgentInstance } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useAgentInstance = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()
  const isRouteReady = useRouteReady('agent_id', 'agent_class')

  const { data: agentInstance, isPending: agentInstanceIsLoading } = useQuery<FullAgentInstanceDto>({
    key: () => ['agent-instances', tenantId.value, route.params.agent_class as string, route.params.agent_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => isRouteReady.value && !!tenantId.value),
    query: async () => {
      return await getAgentInstance({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          agent_id: route.params.agent_id as string,
          agent_class: route.params.agent_class as string,
        },
      })
    },
  })
  return {
    agentInstance,
    agentInstanceIsLoading,
  }
})
