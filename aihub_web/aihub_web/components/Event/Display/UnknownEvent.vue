<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="line-md:question"
  />
</template>

<script setup lang="ts">
import type { ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable
  thread: ThreadDto
}>()
</script>
