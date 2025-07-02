<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:shield"
    is-empty
  />
</template>

<script setup lang="ts">
import type { AgentInTheLoopResponseEvent, ThreadDto, WsServerEventReadable } from '@core/sdk/client'

defineProps<{
  event: WsServerEventReadable & { event: AgentInTheLoopResponseEvent }
  thread: ThreadDto
}>()
</script>
