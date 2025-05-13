<template>
  <div>
    <p>Chart {{ widgetData.agent?.agentId }}</p>
  </div>
</template>

<script setup lang="ts">
import type { EventTimeseries } from '@core/sdk/client'
import type { DashboardWidget } from '@core/types/DashboardWidget'

defineProps<{
  timeseries: EventTimeseries
  widgetData: DashboardWidget
}>()
</script>

<style scoped>

</style>
