<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="line-md:question"
  />
</template>

<script setup lang="ts">
import type { ThreadResponse, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent
  thread: ThreadResponse
}>()
</script>
