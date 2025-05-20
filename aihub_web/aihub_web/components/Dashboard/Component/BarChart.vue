<template>
  <div class="relative">
    <div class="flex flex-col gap-1">
      <div class="flex items-baseline gap-4">
        <p class="text-lg font-medium">
          {{ title }}
        </p>
        <p
          class="text-surface-500"
        >
          {{ agentName }}
        </p>
        <DashboardTrend :timeseries="timeseries" />
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
