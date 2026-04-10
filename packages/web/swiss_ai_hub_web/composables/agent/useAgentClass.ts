import { type AgentClassDtoReadable, getAgentClass } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useAgentClass = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const { data: agentClass, isPending: agentClassIsLoading } = useQuery<AgentClassDtoReadable>({
    key: () => ['tenant', tenantId.value, 'agent-classes', route.params.agent_class as string],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('agent_class'),
    query: async () => {
      return await getAgentClass({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
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
