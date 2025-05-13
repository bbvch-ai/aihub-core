<template>
  <div>
    <p>Number {{ sum }}</p>
  </div>
</template>

<script setup lang="ts">
import type { EventBucket, EventTimeseries } from '@core/sdk/client'
import type { DashboardWidget } from '@core/types/DashboardWidget'

const props = defineProps<{
  timeseries: EventTimeseries
  widgetData: DashboardWidget
}>()

const sum = computed(() => {
  return props.timeseries.buckets.reduce((sum, bucket: EventBucket) => sum + bucket.total_events, 0)
})
</script>

<style scoped>

</style>
