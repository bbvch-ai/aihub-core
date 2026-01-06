import { type AgentClassDtoReadable, getAgentClasses } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export type AgentClassDto = AgentClassDtoReadable

export const useAgentClasses = defineQuery(() => {
  const { data: agentClasses, isPending: agentClassesAreLoading } = useQuery<AgentClassDto[]>({
    key: () => ['agent-classes'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getAgentClasses({
        composable: '$fetch',
      })
    },
  })
  return {
    agentClasses,
    agentClassesAreLoading,
  }
})
