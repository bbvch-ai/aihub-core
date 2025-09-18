<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:shield"
    is-empty
  />
</template>

<script setup lang="ts">
import type { AgentInTheLoopResponseEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: AgentInTheLoopResponseEventReadable }
  thread: ThreadDto
}>()
</script>
