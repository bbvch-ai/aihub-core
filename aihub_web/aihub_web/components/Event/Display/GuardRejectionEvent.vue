<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:shield"
  >
    <Message
      severity="error"
      icon="pi pi-times-circle"
      variant="simple"
      size="small"
    >
      {{ event.event.reason }}
    </Message>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { GuardRejectionEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: GuardRejectionEvent }
  thread: ThreadDto
}>()
</script>
