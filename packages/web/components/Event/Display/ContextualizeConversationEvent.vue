<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:edit"
  >
    <EventDisplayPartFacts :facts="facts" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizeConversationEvent, ContextualizedAgentEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: ContextualizeConversationEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.userQuery'), value: props.event.event.user_query },
  { label: t('event.capability.historyMessages'), value: props.event.event.history.length },
])
</script>
