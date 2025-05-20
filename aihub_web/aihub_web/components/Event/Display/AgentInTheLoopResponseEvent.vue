<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="mdi:robot-happy"
  />
</template>

<script setup lang="ts">
import type { AgentInTheLoopResponseEvent, ThreadDto, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: AgentInTheLoopResponseEvent }
  thread: ThreadDto
}>()
</script>
