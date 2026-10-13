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
import type { ContextualizedAgentEvent, ThreadDto, ToolCallApprovedEvent } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: ToolCallApprovedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.toolLoop.tool'), value: props.event.event.name },
  { label: t('event.toolLoop.kind'), value: t(`event.toolLoop.kinds.${props.event.event.kind}`) },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
