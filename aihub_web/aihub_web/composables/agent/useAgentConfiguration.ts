import { getAgentConfiguration } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

import type { AgentConfigurationDataDto } from '@core/sdk/client'

export const useAgentConfiguration = defineQuery(() => {
  const route = useRoute()
  const { data: agentConfiguration, isPending: agentConfigurationIsLoading } = useQuery<AgentConfigurationDataDto>({
    key: () => ['agents', route.params.agent_class as string, route.params.agent_id as string, 'configuration'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getAgentConfiguration({
        composable: '$fetch',
        path: {
          agent_id: route.params.agent_id as string,
          agent_class: route.params.agent_class as string,
        },
      })
    },
  })
  return {
    agentConfiguration,
    agentConfigurationIsLoading,
  }
})
