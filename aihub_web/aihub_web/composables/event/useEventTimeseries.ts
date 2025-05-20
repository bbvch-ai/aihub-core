import {
  type EventTimeseries, getEventTimeseries,
} from '@core/sdk/client'
import { useRoute } from 'vue-router'

export const useEventTimeseries = ({ eventName, timeRange, agentClass, agentId }: { eventName?: string, timeRange: Ref<string>, agentClass?: string, agentId?: string }) => {
  const route = useRoute()

  const query = {
    agent_class: agentClass ?? route?.params?.agent_class,
    agent_id: agentId ?? route?.params?.agent_id,
    thread_id: route?.params?.thread_id,
    event_name: eventName,
  }
  const { data: timeseries, isPending: timeseriesIsLoading } = useQuery<EventTimeseries>({
    key: () => ['events', 'timeseries', timeRange.value, query],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getEventTimeseries({
        composable: '$fetch',
        path: {
          time_range: timeRange.value,
        },
        query,
      })
    },
  })

  return {
    timeseries,
    timeseriesIsLoading,
    timeRange,
  }
}
