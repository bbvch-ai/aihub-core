<template>
  <div
    class="w-full"
  >
    <div class="flex w-full justify-end">
      <SelectButton
        v-model="timeRange"
        size="small"
        :options="options"
        :allow-empty="false"
      />
    </div>
    <div
      class="grid w-full grid-cols-1 lg:grid-cols-2"
    >
      <div
        v-for="(chart, index) in chartsMap"
        :key="index"
      >
        {{ chart.seriesInputs }}
        <EventTimeseries
          v-if="!chart.seriesInputs.some(series => series.isLoading)"
          :title="chart.title"
          :series-inputs="chart.seriesInputs"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useEventTimeseries } from '@core/composables/event/useEventTimeseries'
import { useRouteQuery } from '@vueuse/router'

import type { TimeseriesInput } from '@core/types/TimeseriesInput'

const props = defineProps<{
  charts: { title: string, display: { eventName: string, name: string, color: string }[] }[]
}>()

const options = ref<string[]>(['1h', '24h', '30d', '365d'])
const timeRange = useRouteQuery<'1h' | '24h' | '30d' | '365d'>('range', '24h')

const chartsMap = computed<{ title: string, seriesInputs: TimeseriesInput[] }[]>(() => {
  return props.charts.map(({ title, display }) => {
    return {
      title,
      seriesInputs: display.map(({ eventName, name, color }) => {
        const { timeseries, timeseriesIsLoading } = useEventTimeseries({
          eventName,
          timeRange,
        })
        return {
          name,
          color,
          timeseries,
          timeseriesIsLoading,
        }
      }),
    }
  })
})
</script>

<style scoped>

</style>
