<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:web"
  >
    <EventDisplayPartFacts :facts="facts" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, FetchWebPagesEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: FetchWebPagesEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.links'), value: props.event.event.urls ?? [] },
  { label: t('event.capability.citeSources'), value: t(props.event.event.cite_sources ? 'event.parts.yes' : 'event.parts.no') },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
