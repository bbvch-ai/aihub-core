import {
  type AgentEventTimeseries, getAgentEventTimeseries,
} from '@core/sdk/client'
import { useRouteQuery } from '@vueuse/router'
import { useRoute } from 'vue-router'

export const useAgentEventTimeseries = defineQuery(() => {
  const route = useRoute()
  const timeRange = useRouteQuery<'1h' | '24h' | '30d' | '365d'>('range', '24h')

  const { data: agentEventTimeseries, isPending: agentEventTimeseriesIsLoading } = useQuery<AgentEventTimeseries>({
    key: () => ['agent', route.params.agent_class as string, route.params.agent_id as string, 'statistics', timeRange.value],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getAgentEventTimeseries({
        composable: '$fetch',
        path: {
          agent_id: route.params.agent_id as string,
          agent_class: route.params.agent_class as string,
        },
        query: {
          time_range: timeRange.value,
        },
      })
    },
  })
  return {
    agentEventTimeseries,
    agentEventTimeseriesIsLoading,
    timeRange,
  }
})
