<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:content-save-cog"
  >
    <EventDisplayPartFacts :facts="facts" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, MemoryStorageRequestedEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: MemoryStorageRequestedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  {
    label: t('event.capability.targetAgent'),
    value: `${props.event.event.target_agent_class} / ${props.event.event.target_agent_id}`,
  },
  { label: t('event.capability.historyMessages'), value: props.event.event.start_event.messages.length },
])
</script>
