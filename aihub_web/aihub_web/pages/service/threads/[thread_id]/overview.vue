<template>
  <StructuralColumn
    :title="thread?.name"
    close-route="/service/threads"
    :loading="threadIsLoading"
    size="large"
  >
    <div class="flex flex-col gap-12">
      <Panel
        class="panel pt-5"
      >
        <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('event.list.firstInteraction') }}
            </span>
            <Tag
              :value="firstInteraction"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('event.list.lastInteraction') }}
            </span>
            <Tag
              :value="lastInteraction"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('event.list.duration') }}
            </span>
            <Tag
              :value="duration"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('event.list.costs') }}
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
  </StructuralColumn>
</template>

<script setup lang="ts">
import { formatDuration, intervalToDuration } from 'date-fns'
import { de } from 'date-fns/locale/de'
import { enUS } from 'date-fns/locale/en-US'
import { frCH } from 'date-fns/locale/fr-CH'
import { itCH } from 'date-fns/locale/it-CH'

const { thread, threadIsLoading } = useThread()
const { timeRange, charts } = useBasicEventStatistics()
const { locale, t } = useI18n()

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
  return formatDuration(duration, { locale: { de, en: enUS, fr: frCH, it: itCH }[locale.value as 'de' | 'en' | 'fr' | 'it'] })
})
</script>

<style scoped>
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
