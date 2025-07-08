<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="line-md:question"
  />
</template>

<script setup lang="ts">
import type { ThreadDto, WsServerEventReadable } from '@core/sdk/client'

defineProps<{
  event: WsServerEventReadable
  thread: ThreadDto
}>()
</script>
