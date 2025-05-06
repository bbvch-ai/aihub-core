import { type EventBucket, getThreadTimeStatistics, type ThreadTimeStatisticsDto } from '@core/sdk/client'
import { useRouteQuery } from '@vueuse/router'
import { useRoute } from 'vue-router'

const generateMockBuckets = (startTime: Date, numBuckets: number, resolutionMinutes: number): EventBucket[] => {
  const buckets: EventBucket[] = []
  let currentStartTime = new Date(startTime.getTime())

  for (let i = 0; i < numBuckets; i++) {
    const endTime = new Date(currentStartTime.getTime() + resolutionMinutes * 60 * 1000)
    const exception_events = Math.random() > 0.7 ? Math.floor(Math.random() * 5) : 0
    const hitl_events = Math.random() > 0.5 ? Math.floor(Math.random() * 10) + 1 : 0
    const start_events = Math.random() > 0.5 ? Math.floor(Math.random() * 10) + 1 : 0
    const stop_events = Math.random() > 0.5 ? Math.floor(Math.random() * 10) + 1 : 0
    const bitl_events = Math.random() > 0.6 ? Math.floor(Math.random() * 8) : 0
    const aitl_events = Math.random() > 0.8 ? Math.floor(Math.random() * 3) : 0
    const other_events = Math.floor(Math.random() * 15) + (i % 5 === 0 ? 5 : 0) // Add some base and spikes
    const total_events = exception_events + hitl_events + bitl_events + aitl_events + other_events

    buckets.push({
      start_time: currentStartTime.toISOString() as unknown as Date, // Casting for type compatibility
      end_time: endTime.toISOString() as unknown as Date, // Casting for type compatibility
      total_events,
      start_events,
      stop_events,
      exception_events,
      hitl_events,
      bitl_events,
      aitl_events,
      other_events,
    })
    currentStartTime = endTime
  }
  return buckets
}

const createMockData = (range: '1h' | '24h' | '30d' | '365d'): ThreadTimeStatisticsDto => {
  const now = new Date('2025-05-06T09:42:07.173730Z') // Fixed date for consistent mock data
  let startTime: Date
  let numBuckets: number
  let resolution: '1m' | '1h' | '1d' | '1w'
  let resolutionMinutes: number // Helper for bucket generation

  switch (range) {
    case '24h':
      startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000)
      numBuckets = 24
      resolution = '1h'
      resolutionMinutes = 60
      break
    case '30d':
      startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      numBuckets = 30
      resolution = '1d'
      resolutionMinutes = 24 * 60
      break
    case '365d':
      startTime = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000)
      numBuckets = 52 // Approx 52 weeks
      resolution = '1w'
      resolutionMinutes = 7 * 24 * 60
      break
    case '1h':
    default:
      startTime = new Date(now.getTime() - 60 * 60 * 1000)
      numBuckets = 60
      resolution = '1m'
      resolutionMinutes = 1
      break
  }

  return {
    thread_id: 'mock_thread_id_123',
    time_range: range,
    resolution: resolution,
    start_time: startTime.toISOString() as unknown as Date, // Casting for type compatibility
    end_time: now.toISOString() as unknown as Date, // Casting for type compatibility
    buckets: generateMockBuckets(startTime, numBuckets, resolutionMinutes),
  }
}

export const useThreadStatisticsMock = () => {
  const timeRange = useRouteQuery<'1h' | '24h' | '30d' | '365d'>('range', '1h')
  const mockDataRef: Ref<ThreadTimeStatisticsDto> = ref(createMockData(timeRange.value))

  watch(timeRange, (newRange) => {
    mockDataRef.value = createMockData(newRange)
  }, { immediate: true })

  const threadStatisticsAreLoading = ref(false)

  return {
    threadStatistics: mockDataRef,
    threadStatisticsAreLoading,
    timeRange,
  }
}

export const useThreadStatistics = defineQuery(() => {
  const route = useRoute()
  const timeRange = useRouteQuery<'1h' | '24h' | '30d' | '365d'>('range', '24h')

  const { data: threadStatistics, isPending: threadStatisticsAreLoading } = useQuery<ThreadTimeStatisticsDto>({
    key: () => ['threads', route.params.thread_id as string, 'statistics', timeRange.value],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getThreadTimeStatistics({
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
    threadStatistics,
    threadStatisticsAreLoading,
    timeRange,
  }
})
