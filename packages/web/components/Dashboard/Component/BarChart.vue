<template>
  <div class="relative">
    <div class="relative z-10 flex w-fit max-w-full flex-col gap-1">
      <div class="flex min-w-0 items-baseline gap-4">
        <DashboardTruncatedText
          tag="p"
          :text="title"
          class="min-w-0 text-lg font-medium"
        />
        <DashboardTruncatedText
          tag="p"
          :text="agentName"
          class="min-w-0 text-surface-500"
        />
        <DashboardTrend
          class="shrink-0"
          :timeseries="timeseries"
        />
      </div>
    </div>
    <div class="absolute inset-x-0 top-0">
      <EventTimeseries
        :title="title"
        :series-inputs="seriesInput"
        :height="250"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { EventTimeseries as EventTimeseriesType } from '@core/sdk/client'
import type { DashboardWidget } from '@core/types/DashboardWidget'
import type { TimeseriesInput } from '@core/types/TimeseriesInput'

const props = defineProps<{
  title: string
  timeseries: EventTimeseriesType
  widgetData: DashboardWidget
}>()

const seriesInput = computed<TimeseriesInput[]>(() => [{
  name: props.title,
  color: 'var(--p-surface-600)',
  timeseries: props.timeseries,
}])

const { agentName } = useAgentNameFromDashboardWidget(props.widgetData)
</script>
