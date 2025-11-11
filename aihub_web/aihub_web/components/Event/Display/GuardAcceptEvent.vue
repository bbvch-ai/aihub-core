<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:shield"
  >
    <Message
      severity="success"
      icon="pi pi-check-circle"
      variant="simple"
      size="small"
    >
      {{ event.event.reason }}
    </Message>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { GuardAcceptEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: GuardAcceptEventReadable }
  thread: ThreadDto
}>()
</script>
