<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="mdi:robot-happy"
  />
</template>

<script setup lang="ts">
import type { AgentInTheLoopResponseEvent, ThreadDto, WsServerEventReadable } from '@core/sdk/client'

defineProps<{
  event: WsServerEventReadable & { event: AgentInTheLoopResponseEvent }
  thread: ThreadDto
}>()
</script>
