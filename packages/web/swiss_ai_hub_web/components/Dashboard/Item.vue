<template>
  <div
    ref="gridItemRoot"
    class="grid-stack-item"
  >
    <div class="size-full p-4">
      <div class="flex size-full flex-col justify-start gap-2 rounded-xl border border-surface-200 bg-white p-4 shadow-lg dark:border-surface-800 dark:bg-surface-900">
        <div class="flex w-full justify-between">
          <Tag
            severity="secondary"
            :value="timeRangeName"
          />
          <button @click="handleRemove">
            <Icon
              name="oui:cross"
              size="xl"
            />
          </button>
        </div>
        <ProgressSpinner
          v-if="timeseriesIsLoading"
          class="mt-24 size-12"
        />
        <div v-else>
          <component
            :is="vueComponent"
            :title="title"
            :timeseries="timeseries"
            :widget-data="data"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DashboardWidget } from '@core/types/DashboardWidget'

const props = defineProps<{
  component: string
  data: DashboardWidget
}>()

const { t } = useI18n()

const emit = defineEmits<{
  remove: [HTMLElement]
}>()

const title = computed(() => t(`dashboard.events.${props.data.event}.label`))

const timeRange = computed(() => props.data.timeRange)
const timeRangeName = computed(() => t(`timerange.${timeRange.value}`))

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
