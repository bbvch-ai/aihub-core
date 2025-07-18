<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="mdi:robot-happy"
  />
</template>

<script setup lang="ts">
import type { AgentInTheLoopResponseEventReadable, ThreadDto, WsServerAgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: WsServerAgentEventReadable & { event: AgentInTheLoopResponseEventReadable }
  thread: ThreadDto
}>()
</script>
