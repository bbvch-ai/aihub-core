<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:success"
    :is-warning="true"
  >
    <Message
      severity="warn"
      icon="pi pi-exclamation-triangle"
      variant="simple"
      size="small"
    >
      {{ t(`event.rag_stop.ungrounded_reason.${event.event.reason}`) }}
    </Message>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ThreadDto, UngroundedRagStopEvent, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: UngroundedRagStopEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
</script>
