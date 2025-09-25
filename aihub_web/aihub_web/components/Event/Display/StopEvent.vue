<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:success"
  />
</template>

<script setup lang="ts">
import type { StopEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: StopEventReadable }
  thread: ThreadDto
}>()
</script>
