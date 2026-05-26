import { type FullAgentInstanceDto, getAgentClassInstances } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useAgentClassInstances = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const { data: agentClassInstances, isPending: agentClassInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['tenant', tenantId.value, 'agent-class-instances', route.params.agent_class as string],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('agent_class'),
    query: async () => {
      return await getAgentClassInstances({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
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
