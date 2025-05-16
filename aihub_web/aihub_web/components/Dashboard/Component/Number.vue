<template>
  <div class="pointer-events-none relative w-full">
    <p class="pointer-events-none -mt-8 w-full text-center text-[12rem] font-medium opacity-70">
      {{ sum }}
    </p>
    <span class="absolute bottom-8 w-full text-center text-lg font-bold opacity-80">{{ title }}</span>
    <span
      class="absolute bottom-2 w-full text-center text-surface-500"
    >
      {{ agentName }}
    </span>
    <div class="absolute -bottom-6 flex w-full justify-center">
      <DashboardTrend :timeseries="timeseries" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { EventTimeseries } from '@core/sdk/client'
import type { DashboardWidget } from '@core/types/DashboardWidget'

const props = defineProps<{
  title: string
  timeseries: EventTimeseries
  widgetData: DashboardWidget
}>()

const { sum } = useEventTimeseriesStats(props.timeseries)

const { agentName } = useAgentNameFromDashboardWidget(props.widgetData)
</script>
