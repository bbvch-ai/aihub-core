<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="mage:robot-happy"
  />
</template>

<script setup lang="ts">
import type { AgentInTheLoopResponseEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: AgentInTheLoopResponseEvent }
  thread: ThreadDto
}>()
</script>
