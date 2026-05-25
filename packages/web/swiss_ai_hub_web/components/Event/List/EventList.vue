<template>
  <div class="flex flex-col gap-12 pt-4">
    <Panel
      v-if="showChat"
      :header="t('event.list.chat')"
      toggleable
    >
      <div class="flex flex-col gap-8">
        <ChatThread
          :events="eventsInRuns"
          :thread="thread"
        />
      </div>
    </Panel>
    <div class="flex flex-col gap-8">
      <div class="grid grid-cols-2 gap-4 px-4 xl:grid-cols-4">
        <div class="flex flex-col items-start gap-2">
          <span class="font-semibold">{{ t('event.list.firstInteraction') }}</span>
          <Tag
            :value="firstInteraction"
            severity="secondary"
          />
        </div>
        <div class="flex flex-col items-start gap-2">
          <span class="font-semibold">{{ t('event.list.lastInteraction') }}</span>
          <Tag
            :value="lastInteraction"
            severity="secondary"
          />
        </div>
        <div class="flex flex-col items-start gap-2">
          <span class="font-semibold">{{ t('event.list.duration') }}</span>
          <Tag
            :value="runDuration"
            severity="secondary"
          />
        </div>
        <div class="flex flex-col items-start gap-2">
          <span class="font-semibold">{{ t('event.list.costs') }}</span>
          <Tag
            :value="totalCost"
            severity="secondary"
          />
        </div>
      </div>
      <MeterGroup
        :value="eventMeterValues"
        class="px-4"
      />
      <div class="flex w-full items-center justify-end gap-2 pr-4">
        <MultiSelect
          v-model="activeRuns"
          display="chip"
          input-id="agents"
          :options="display.runs"
          :option-label="runNameFn"
        />
      </div>
      <Timeline
        :value="eventsInRuns"
        data-key="event_id"
        align="left"
        class="customized-timeline w-full"
      >
        <template #opposite="{ item: event }">
          <div class="flex w-full flex-row justify-end">
            <div class="flex flex-col text-xs text-surface-500 dark:text-surface-400">
              <div class="font-semibold">
                {{ useDateFormat(event.event.created_at / 1_000_000, 'DD.MM.YYYY') }}
              </div>
              <div>{{ useDateFormat(event.event.created_at / 1_000_000, 'hh:mm:ss') }}</div>
            </div>
          </div>
        </template>
        <template #content="{ item: event }">
          <div class="w-full pb-12">
            <component
              :is="resolveComponentForEvent(event)"
              :event="event"
              :thread="thread"
            />
          </div>
        </template>
        <template #marker>
          <span
            class="z-10 flex size-5 items-center justify-center rounded-full border border-surface-100 bg-white text-white shadow-md shadow-surface-200 dark:border-surface-800 dark:bg-surface-700 dark:shadow-surface-950"
          >
            <Icon
              class="text-green-700"
              name="mage:check"
              size="xs"
            />
          </span>
        </template>
      </Timeline>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatDuration, intervalToDuration } from 'date-fns'
import { de } from 'date-fns/locale/de'
import { enUS } from 'date-fns/locale/en-US'
import { frCH } from 'date-fns/locale/fr-CH'
import { itCH } from 'date-fns/locale/it-CH'

import type {
  DisplayStatistics, RunStatistics,
  ThreadDto,
  ContextualizedAgentEvent,
} from '@core/sdk/client'

const props = withDefaults(defineProps<{
  events: ContextualizedAgentEvent[]
  thread: ThreadDto
  displayId?: string
  showChat?: boolean
}>(), {
  showChat: false,
})

const route = useRoute()
const { locale, t } = useI18n()

const localeMap = { de, en: enUS, fr: frCH, it: itCH } as const

const activeRuns = ref<RunStatistics[]>([])

const display = computed(() => {
  const displayId = props.displayId ?? route.params.display_id
  return props.thread.displays?.find((display: DisplayStatistics) => display.display_id === displayId)
})

watch(display, () => {
  activeRuns.value = display.value?.runs ?? []
}, { immediate: true })

const eventsInRuns = computed<ContextualizedAgentEvent[]>(() => {
  const runIds = new Set(activeRuns.value.map((run: RunStatistics) => run.run_id))
  return props.events.filter((event: ContextualizedAgentEvent) => runIds.has(event.run_id))
})

const { resolveComponentForEvent } = useEventComponent()

const runNameFn = (run: RunStatistics) => run.agent.agent_config.name

const getEventTimestamp = (event: AgentEventReadable): number =>
  (event.event as { created_at?: number }).created_at ?? 0

const sortedEvents = computed(() =>
  [...eventsInRuns.value].sort((a, b) => getEventTimestamp(a) - getEventTimestamp(b)),
)

const firstInteraction = computed<string>(() => {
  if (!sortedEvents.value.length) return '-'
  const ts = getEventTimestamp(sortedEvents.value[0])
  if (!ts) return '-'
  return useDateFormat(ts / 1_000_000, 'DD.MM.YYYY HH:mm:ss').value
})

const lastInteraction = computed<string>(() => {
  if (!sortedEvents.value.length) return '-'
  const ts = getEventTimestamp(sortedEvents.value[sortedEvents.value.length - 1])
  if (!ts) return '-'
  return useDateFormat(ts / 1_000_000, 'DD.MM.YYYY HH:mm:ss').value
})

const runDuration = computed<string>(() => {
  const events = sortedEvents.value
  if (events.length < 2) return '-'
  const startNs = getEventTimestamp(events[0])
  const endNs = getEventTimestamp(events[events.length - 1])
  const startMs = startNs / 1_000_000
  const endMs = endNs / 1_000_000
  const dur = intervalToDuration({ start: new Date(startMs), end: new Date(endMs) })
  if (dur.minutes || dur.hours || dur.days) dur.seconds = 0
  if (dur.days || dur.weeks) dur.minutes = 0
  return formatDuration(dur, { locale: localeMap[locale.value as keyof typeof localeMap] }) || '< 1s'
})

const totalCost = computed<string>(() => {
  let cost = 0
  for (const event of eventsInRuns.value) {
    if (event._event_name !== 'LLMCostEvent' && !(event._parent_event_names as string[])?.includes('LLMCostEvent')) continue
    const e = event.event as { prompt_tokens_costs?: number, completion_tokens_costs?: number, embedding_tokens_costs?: number }
    cost += (e.prompt_tokens_costs ?? 0) + (e.completion_tokens_costs ?? 0) + (e.embedding_tokens_costs ?? 0)
  }
  return `${cost.toFixed(6)} CHF`
})

const { getEventColor } = useEventColor()

const eventMeterValues = computed(() => {
  const sorted = sortedEvents.value
  if (sorted.length < 2) return []

  const durations = new Map<string, { label: string, duration: number }>()
  for (let i = 1; i < sorted.length; i++) {
    const curr = sorted[i]
    const prev = sorted[i - 1]
    const delta = getEventTimestamp(curr) - getEventTimestamp(prev)
    const name = curr.event_display_name as string ?? curr._event_name

    const existing = durations.get(name)
    if (existing) {
      existing.duration += delta
    }
    else {
      durations.set(name, { label: name, duration: delta })
    }
  }

  const totalDuration = Array.from(durations.values()).reduce((sum, e) => sum + e.duration, 0)
  if (totalDuration === 0) return []

  const MIN_DURATION_NS = 100_000_000 // 0.1s in nanoseconds
  const insertionOrder = Array.from(durations.keys())
  const entries = Array.from(durations.values())
    .filter(e => e.duration >= MIN_DURATION_NS)
    .sort((a, b) => insertionOrder.indexOf(a.label) - insertionOrder.indexOf(b.label))

  const rawValues = entries.map(e => (e.duration / totalDuration) * 100)
  const floored = rawValues.map(v => Math.floor(v))
  let remainder = 100 - floored.reduce((sum, v) => sum + v, 0)
  const fractionals = rawValues.map((v, i) => ({ i, frac: v - floored[i] }))
    .sort((a, b) => b.frac - a.frac)
  for (const { i } of fractionals) {
    if (remainder <= 0) break
    floored[i]++
    remainder--
  }

  return entries.map((entry, index) => ({
    label: entry.label,
    value: floored[index],
    color: getEventColor(entry.label),
  }))
})
</script>

<style scoped>
.customized-timeline :deep(.p-timeline-event-opposite) {
  width: 60px;
  max-width: 60px;
}
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
