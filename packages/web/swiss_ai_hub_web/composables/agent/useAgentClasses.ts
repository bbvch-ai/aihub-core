import { type AgentClassDtoReadable, getAgentClasses } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export type AgentClassDto = AgentClassDtoReadable

export const useAgentClasses = defineQuery((options?: { online?: boolean }) => {
  const { tenantName } = useTenant()

  const { data: agentClasses, isPending: agentClassesAreLoading } = useQuery<AgentClassDto[]>({
    key: () => ['agent-classes', tenantName.value, options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getAgentClasses({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
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
