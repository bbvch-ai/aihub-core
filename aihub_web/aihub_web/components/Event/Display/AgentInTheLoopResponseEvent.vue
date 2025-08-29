<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="mdi:robot-happy"
  />
</template>

<script setup lang="ts">
import type { AgentInTheLoopResponseEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: AgentInTheLoopResponseEventReadable }
  thread: ThreadDto
}>()
</script>
