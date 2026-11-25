<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:search-web"
  >
    <EventDisplayPartFacts :facts="facts" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, SearchWebEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: SearchWebEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.searchQueries'), value: props.event.event.queries ?? [] },
  { label: t('event.capability.citeSources'), value: t(props.event.event.cite_sources ? 'event.parts.yes' : 'event.parts.no') },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
