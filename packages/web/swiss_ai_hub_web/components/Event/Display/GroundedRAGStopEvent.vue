<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:success"
  />
</template>

<script setup lang="ts">
import type { ThreadDto, GroundedRagStopEvent, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: GroundedRagStopEvent }
  thread: ThreadDto
}>()
</script>
