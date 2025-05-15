<template>
  <Tag
    v-if="isTrendingUp"
    severity="success"
    value="Trending Up"
    size="small"
    icon="pi pi-arrow-up-right"
    rounded
  />
  <Tag
    v-else
    severity="danger"
    value="Trending Down"
    icon="pi pi-arrow-down-right"
    rounded
  />
</template>

<script setup lang="ts">
import type { EventTimeseries } from '@core/sdk/client'

const props = defineProps<{
  timeseries: EventTimeseries
}>()

const { isTrendingUp } = useEventTimeseriesStats(props.timeseries)
</script>
