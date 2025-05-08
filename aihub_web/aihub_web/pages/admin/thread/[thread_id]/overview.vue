<template>
  <ProgressBar
    v-if="threadIsLoading || !thread"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    class="flex flex-col gap-16 p-3"
  >
    <Panel
      class="panel pt-5"
    >
      <div class="grid grid-cols-2 gap-4 2xl:grid-cols-4">
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ $t('eventList.firstInteraction') }}
          </span>
          <Tag
            :value="firstInteraction"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ $t('eventList.lastInteraction') }}
          </span>
          <Tag
            :value="lastInteraction"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ $t('eventList.duration') }}
          </span>
          <Tag
            :value="duration"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ $t('eventList.costs') }}
          </span>
          <Tag
            :value="thread.llm_cost.toFixed(6) + 'CHF'"
            severity="secondary"
          />
        </div>
      </div>
    </Panel>
    <ThreadInfo
      :thread="thread"
    />
    <EventStatistics
      v-model="timeRange"
      :charts="charts"
    />
  </div>
</template>

<script setup lang="ts">
import { formatDuration, intervalToDuration } from 'date-fns'
import { de } from 'date-fns/locale/de'

const { thread, threadIsLoading } = useThread()
const { timeRange, charts } = useBasicEventStatistics()

const firstInteraction = computed<string>(() => {
  return useDateFormat(new Date(thread.value?.first_interaction), 'DD.MM.YYYY HH:mm:ss')
})

const lastInteraction = computed<string>(() => {
  return useDateFormat(new Date(thread.value?.latest_interaction), 'DD.MM.YYYY HH:mm:ss')
})

const duration = computed<string>(() => {
  const duration = intervalToDuration({
    start: new Date(thread.value?.first_interaction),
    end: new Date(thread.value?.latest_interaction),
  })
  if (duration.minutes || duration.hours || duration.days) {
    duration.seconds = 0
  }
  if (duration.days || duration.weeks) {
    duration.minutes = 0
  }
  return formatDuration(duration, { locale: de })
})
</script>

<style scoped>
::v-deep(.panel) {
  .p-panel-header {
    padding: 0 !important;
  }
}
</style>
