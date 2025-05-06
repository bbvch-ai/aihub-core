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
      v-if="!threadStatisticsAreLoading && threadStatistics"
      class="flex flex-col gap-3"
    >
      <div
        v-for="bar in bars"
        :key="bar.key"
      >
        <h3 class="font-bold">
          {{ bar.title }}
        </h3>
        <ThreadChart
          :thread="thread"
          :statistics="threadStatistics"
          :bars="bar.bars"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useThreadStatistics } from '@core/composables/thread/useThreadStatistics'

import type { EventBucket, ThreadDto } from '@core/sdk/client'

defineProps<{
  thread: ThreadDto
}>()

const options = ref<string[]>(['1h', '24h', '30d', '365d'])

const { threadStatistics, threadStatisticsAreLoading, timeRange } = useThreadStatistics()

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
