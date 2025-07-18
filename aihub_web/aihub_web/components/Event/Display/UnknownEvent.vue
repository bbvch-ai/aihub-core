<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="line-md:question"
  />
</template>

<script setup lang="ts">
import type { ThreadDto, WsServerAgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: WsServerAgentEventReadable
  thread: ThreadDto
}>()
</script>
