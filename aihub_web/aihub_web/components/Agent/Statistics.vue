<template>
  <div class="w-full">
    <div class="flex w-full justify-end">
      <SelectButton
        v-model="timeRange"
        size="small"
        :options="options"
        :allow-empty="false"
      />
    </div>
    <div
      v-if="!agentEventTimeseriesIsLoading && agentEventTimeseries"
      class="grid grid-cols-1 lg:grid-cols-2"
    >
      <div
        v-for="bar in bars"
        :key="bar.key"
      >
        <h3 class="font-bold">
          {{ bar.title }}
        </h3>
        <EventTimeseries
          :statistics="agentEventTimeseries"
          :bars="bar.bars"
          :title="bar.title"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentDto, EventBucket } from '@core/sdk/client'

defineProps<{
  agent: AgentDto
}>()

const options = ref<string[]>(['1h', '24h', '30d', '365d'])

const { agentEventTimeseries, agentEventTimeseriesIsLoading, timeRange } = useAgentEventTimeseries()

const bars = computed<{ title: string, key: string, bars: { key: keyof EventBucket, name: string, color?: string }[] }[]>(() => [
  {
    title: 'Interactions',
    key: 'interactions',
    bars: [{ key: 'stop_events', name: 'Interactions', color: 'var(--p-surface-500)' }],
  },
  {
    title: 'Errors',
    key: 'errors',
    bars: [{ key: 'exception_events', name: 'Errors', color: 'var(--p-red-500)' }],
  },
],
)
</script>

<style scoped>

</style>
