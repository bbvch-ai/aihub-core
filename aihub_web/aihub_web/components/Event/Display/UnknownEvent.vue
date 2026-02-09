<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="mage:question-mark-circle"
  />
</template>

<script setup lang="ts">
import type { ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent
  thread: ThreadDto
}>()
</script>
