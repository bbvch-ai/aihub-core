<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:search"
  >
    <EventDisplayPartFacts :facts="facts" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, SearchKnowledgeEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: SearchKnowledgeEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.query'), value: props.event.event.query },
  {
    label: t('event.capability.references'),
    value: (props.event.event.references ?? []).map(reference => `${reference.database} / ${reference.namespace}`),
  },
  { label: t('event.capability.citeSources'), value: t(props.event.event.cite_sources ? 'event.parts.yes' : 'event.parts.no') },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
