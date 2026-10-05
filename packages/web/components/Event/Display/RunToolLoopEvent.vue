<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mynaui:tool"
  >
    <EventDisplayPartFacts :facts="facts" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, RunToolLoopEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: RunToolLoopEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.toolLoop.loop'), value: props.event.event.loop },
  { label: t('event.toolLoop.mode'), value: t(`event.toolLoop.modes.${props.event.event.mode ?? 'answer'}`) },
  { label: t('event.toolLoop.narrowedTools'), value: props.event.event.tools ?? null },
  { label: t('event.toolLoop.maxIterations'), value: props.event.event.max_iterations },
  { label: t('event.capability.historyMessages'), value: (props.event.event.history ?? []).length },
  { label: t('event.capability.files'), value: (props.event.event.files ?? []).map(file => file.filename) },
  {
    label: t('event.capability.references'),
    value: (props.event.event.knowledge_references ?? []).map(reference => `${reference.database} / ${reference.namespace}`),
  },
])
</script>
