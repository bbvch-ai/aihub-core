<template>
  <Tag
    v-if="isTrendingUp"
    :severity="reverseLogic ? 'danger' : 'success'"
    :value="t('chart.trending_up')"
    size="small"
    icon="pi pi-arrow-up-right"
    rounded
  />
  <Tag
    v-else
    :severity="reverseLogic ? 'success' : 'danger'"
    :value="t('chart.trending_down')"
    icon="pi pi-arrow-down-right"
    rounded
  />
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
