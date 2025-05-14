import type { EventBucket, EventTimeseries } from '@core/sdk/client'

export const useEventTimeseriesStats = (timeseries: EventTimeseries) => {
  const sum = computed(() => {
    return timeseries.buckets.reduce((sum, bucket: EventBucket) => sum + bucket.total_events, 0)
  })

  const isTrendingUp = computed<boolean>(() => {
    const localBuckets = timeseries.buckets
    if (!localBuckets || localBuckets.length < 2) return false

    const halfwayIndex = Math.floor(localBuckets.length / 2)
    const firstHalfBuckets = localBuckets.slice(0, halfwayIndex)
    const secondHalfBuckets = localBuckets.slice(halfwayIndex)

    const sum1 = firstHalfBuckets.reduce((sum, bucket: EventBucket) => sum + (bucket.total_events || 0), 0)
    const sum2 = secondHalfBuckets.reduce((sum, bucket: EventBucket) => sum + (bucket.total_events || 0), 0)

    return sum2 > sum1
  })

  return {
    sum,
    isTrendingUp,
  }
}
