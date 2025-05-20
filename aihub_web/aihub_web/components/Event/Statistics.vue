<template>
  <div
    class="flex w-full flex-col gap-8"
  >
    <div class="flex w-full justify-end">
      <SelectButton
        :model-value="modelValue"
        size="small"
        :options="options"
        :allow-empty="false"
        @update:model-value="emit('update:modelValue', $event)"
      />
    </div>
    <div
      class="grid w-full grid-cols-1 lg:grid-cols-2"
    >
      <div
        v-for="(chart, index) in charts"
        :key="index"
        class="flex h-[350px] w-full items-center justify-center"
      >
        <EventTimeseries
          v-if="!chart.isLoading"
          :title="chart.title"
          :series-inputs="chart.timeseriesInputs"
        />
        <ProgressSpinner
          v-else
          class="size-12"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { EventChartInput } from '@core/types/EventChartInput'

defineProps<{
  modelValue: string
  charts: EventChartInput[]
}>()

const emit = defineEmits<{
  'update:modelValue': [string]
}>()

const options = ref<string[]>(['1h', '24h', '30d', '365d'])
</script>
