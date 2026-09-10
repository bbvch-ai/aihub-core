import { type AgentClassDtoReadable, getAgentClasses } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export type AgentClassDto = AgentClassDtoReadable

export const useAgentClasses = defineQuery((options?: { online?: boolean }) => {
  const { tenantId } = useTenant()

  const { data: agentClasses, isPending: agentClassesAreLoading } = useQuery<AgentClassDto[]>({
    key: () => ['tenant', tenantId.value, 'agent-classes', options?.online],
    staleTime: minutesToMilliseconds(5),
    // A focus refetch replaces the classes array with new object references, which would
    // reset an in-progress create form (issue #38). Keep the cached value until invalidated.
    refetchOnWindowFocus: false,
    enabled: useTenantReady(),
    query: async () => {
      return await getAgentClasses({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
        query: {
          online: options?.online,
        },
      })
    },
  })
  return {
    agentClasses,
    agentClassesAreLoading,
  }
})
