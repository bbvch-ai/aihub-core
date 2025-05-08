import {
  type EventTimeseries, getEventTimeseries,
} from '@core/sdk/client'
import { useRoute } from 'vue-router'

export const useEventTimeseries = ({ eventName, timeRange }: { eventName: string, timeRange: Ref<string> }) => {
  const route = useRoute()

  const query = {
    agent_class: route.params.agent_class as string,
    agent_id: route.params.agent_id as string,
    thread_id: route.params.thread_id as string,
    event_name: eventName,
  }

  const { data: timeseries, isPending: timeseriesIsLoading } = useQuery<EventTimeseries>({
    key: () => ['events', 'timeseries', timeRange.value, query],
    staleTime: 1000, // 5 minutes
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
