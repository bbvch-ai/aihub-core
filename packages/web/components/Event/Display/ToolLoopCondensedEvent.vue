<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="lucide:layers"
  >
    <EventDisplayPartFacts :facts="facts" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ThreadDto, ToolLoopCondensedEvent } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: ToolLoopCondensedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.toolLoop.loop'), value: props.event.event.loop },
  {
    label: t('event.toolLoop.tokens'),
    value: `${props.event.event.tokens_before} → ${props.event.event.tokens_after}`,
  },
  { label: t('event.toolLoop.condensedResults'), value: props.event.event.condensed_results ?? 0 },
  { label: t('event.toolLoop.condensedTurns'), value: props.event.event.condensed_turns ?? 0 },
])
</script>
