<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mynaui:tool"
  >
    <EventDisplayPartToolLoopState :state="event.event.state" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ThreadDto, ToolLoopIterationEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: ToolLoopIterationEvent }
  thread: ThreadDto
}>()
</script>
