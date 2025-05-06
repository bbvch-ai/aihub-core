import {
  getThreadEventTimeseries,
  type ThreadEventTimeseries,
} from '@core/sdk/client'
import { useRouteQuery } from '@vueuse/router'
import { useRoute } from 'vue-router'

export const useThreadEventTimeseries = defineQuery(() => {
  const route = useRoute()
  const timeRange = useRouteQuery<'1h' | '24h' | '30d' | '365d'>('range', '24h')

  const { data: threadEventTimeseries, isPending: threadEventTimeseriesIsLoading } = useQuery<ThreadEventTimeseries>({
    key: () => ['threads', route.params.thread_id as string, 'statistics', timeRange.value],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getThreadEventTimeseries({
        composable: '$fetch',
        path: {
          thread_id: route.params.thread_id as string,
        },
        query: {
          time_range: timeRange.value,
        },
      })
    },
  })
  return {
    threadEventTimeseries,
    threadEventTimeseriesIsLoading,
    timeRange,
  }
})
