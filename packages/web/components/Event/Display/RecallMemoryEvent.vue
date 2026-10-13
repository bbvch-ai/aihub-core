<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:brain"
  >
    <EventDisplayPartFacts :facts="facts" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, RecallMemoryEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: RecallMemoryEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.query'), value: props.event.event.query },
  { label: t('event.capability.namespaces'), value: props.event.event.org_memory_namespaces ?? [] },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
