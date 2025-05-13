<template>
  <div
    ref="gridItemRoot"
    class="grid-stack-item"
  >
    <div class="h-full justify-start rounded-lg border border-surface-500 bg-white p-4 shadow-lg dark:bg-surface-800">
      <h2
        class="text-xl"
      >
        {{ title }}
      </h2>
      <button @click="handleRemove">
        Remove
      </button>
      <p v-if="timeseriesIsLoading">
        Loading
      </p>
      <div v-else>
        <component
          :is="vueComponent"
          :timeseries="timeseries"
          :widget-data="data"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDashboardComponent } from '@core/composables/dasoboard/useDashboardComponent'

import type { DashboardWidget } from '@core/types/DashboardWidget'

const props = defineProps<{
  component: string
  title: string
  data: DashboardWidget
}>()

const emit = defineEmits<{
  remove: [HTMLElement]
}>()

const timeRange = computed(() => props.data.timeRange)

const { timeseries, timeseriesIsLoading } = useEventTimeseries({
  eventName: props.data.event,
  timeRange: timeRange,
  agentId: props.data?.agent?.agentId,
  agentClass: props.data?.agent?.agentClass,
})

const gridItemRoot = ref<HTMLElement | null>(null)
const { resolveComponent } = useDashboardComponent()

const vueComponent = computed(() => {
  return resolveComponent(props.component)
})

const handleRemove = () => {
  if (gridItemRoot.value) {
    emit('remove', gridItemRoot.value)
  }
}
</script>
