import { type FullAgentInstanceDto, getAgentInstance } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useAgentInstance = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const { data: agentInstance, isPending: agentInstanceIsLoading } = useQuery<FullAgentInstanceDto>({
    key: () => ['tenant', tenantId.value as string, 'agent-instances', route.params.agent_class as string, route.params.agent_id as string],
    staleTime: minutesToMilliseconds(5),
    // A focus refetch after leaving the tab would flip the loading/enabled state and remount
    // the configuration form, discarding unsaved edits (issue #38). Keep the cached value.
    refetchOnWindowFocus: false,
    enabled: useTenantReady('agent_id', 'agent_class'),
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
