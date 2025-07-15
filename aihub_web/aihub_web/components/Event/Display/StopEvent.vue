<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:success"
  />
</template>

<script setup lang="ts">
import type { StopEvent, ThreadDto, WsServerAgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: WsServerAgentEventReadable & { event: StopEvent }
  thread: ThreadDto
}>()
</script>
