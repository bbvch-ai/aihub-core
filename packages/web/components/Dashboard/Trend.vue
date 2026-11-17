<template>
  <Tag
    v-if="isTrendingUp"
    :severity="reverseLogic ? 'danger' : 'success'"
    size="small"
    icon="pi pi-arrow-up-right"
    rounded
    class="max-w-full"
  >
    <DashboardTruncatedText
      :text="t('chart.trending_up')"
      class="min-w-0"
    />
  </Tag>
  <Tag
    v-else
    :severity="reverseLogic ? 'success' : 'danger'"
    icon="pi pi-arrow-down-right"
    rounded
    class="max-w-full"
  >
    <DashboardTruncatedText
      :text="t('chart.trending_down')"
      class="min-w-0"
    />
  </Tag>
</template>

<script setup lang="ts">
import type { EventTimeseries } from '@core/sdk/client'

const props = defineProps<{
  timeseries: EventTimeseries
}>()

const { t } = useI18n()
const { isTrendingUp } = useEventTimeseriesStats(props.timeseries)

const EXCEPTION_EVENT = 'ExceptionEvent'

const reverseLogic = computed(() => {
  return props.timeseries.event_name === EXCEPTION_EVENT
})
</script>
