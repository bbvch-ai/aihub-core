import { type AgentDto, getAgents } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useAgents = defineQuery(() => {
  const { suite } = useSuite()

  const hasAgentAccess = computed(() => {
    return suite.value?.services?.some(service => service.path === '/service/agents') ?? false
  })

  const { data: agents, isPending: agentsAreLoading } = useQuery<AgentDto[]>({
    key: () => ['agents'],
    staleTime: minutesToMilliseconds(5),
    enabled: hasAgentAccess,
    query: async () => {
      return await getAgents({
        composable: '$fetch',
      })
    },
  })
  return {
    agents,
    agentsAreLoading,
    hasAgentAccess,
  }
})
