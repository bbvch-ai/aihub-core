import { type FullAgentInstanceDto, getAgentClassInstances } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useAgentClassInstances = defineQuery(() => {
  const route = useRoute()
  const { tenantName } = useTenant()
  const isRouteReady = useRouteReady('agent_class')

  const { data: agentClassInstances, isPending: agentClassInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['agent-class-instances', tenantName.value, route.params.agent_class as string],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => isRouteReady.value && !!tenantName.value),
    query: async () => {
      return await getAgentClassInstances({
        composable: '$fetch',
        path: {
          tenant_id: tenantName.value!,
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
